#!/usr/bin/env python3

"""
Run mini-SWE-agent on SWE-Smith instances with Qwen3-Coder via Amazon Bedrock.
Features:
- Cost tracking with configurable limit
- N inferences per instance (parallel per instance, sequential across instances)
- Proper trajectory saving with naming {instance_id}_{n}
"""

import concurrent.futures
import json
import sys
import threading
import time
import traceback
from pathlib import Path

import yaml
from jinja2 import StrictUndefined, Template
from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from minisweagent.agents.default import DefaultAgent
from minisweagent.config import get_config_path
from minisweagent.environments import get_environment
from minisweagent.models import get_model
from minisweagent.run.extra.utils.swebench_pro_utils import get_swebench_pro_docker_image
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import add_file_handler, logger

# Qwen3-Coder-30B pricing (per 1K tokens)
INPUT_COST_PER_1K = 0.00022
OUTPUT_COST_PER_1K = 0.0018

_OUTPUT_FILE_LOCK = threading.Lock()
console = Console()


class CostTracker:
    """Thread-safe cost tracker."""

    def __init__(self, cost_limit: float):
        self.cost_limit = cost_limit
        self.total_cost = 0.0
        self.lock = threading.Lock()

    def add_cost(self, cost: float) -> bool:
        """Add cost and return True if under limit."""
        with self.lock:
            self.total_cost += cost
            return self.total_cost < self.cost_limit

    def get_total_cost(self) -> float:
        """Get current total cost."""
        with self.lock:
            return self.total_cost

    def is_under_limit(self) -> bool:
        """Check if still under cost limit."""
        with self.lock:
            return self.total_cost < self.cost_limit


def get_swebench_docker_image_name(instance: dict) -> str:
    """Get the image name for a SWEBench instance."""
    image_name = instance.get("image_name", None)
    if image_name is None:
        # Check if this is a SWE-Smith instance (has 'repo' field)
        if "repo" in instance:
            image_name = get_swebench_pro_docker_image(instance)
        else:
            # Docker doesn't allow double underscore, so we replace them with a magic token
            iid = instance["instance_id"]
            id_docker_compatible = iid.replace("__", "_1776_")
            image_name = f"docker.io/swebench/sweb.eval.x86_64.{id_docker_compatible}:latest".lower()
    return image_name


def get_sb_environment(config: dict, instance: dict):
    """Get environment for SWEBench instance."""
    env_config = config.setdefault("environment", {})
    env_config["environment_class"] = env_config.get("environment_class", "docker")
    image_name = get_swebench_docker_image_name(instance)
    if env_config["environment_class"] == "docker":
        env_config["image"] = image_name
    elif env_config["environment_class"] == "singularity":
        env_config["image"] = "docker://" + image_name
    env = get_environment(env_config)
    if startup_command := config.get("run", {}).get("env_startup_command"):
        startup_command = Template(startup_command, undefined=StrictUndefined).render(**instance)
        out = env.execute(startup_command)
        if out["returncode"] != 0:
            raise RuntimeError(f"Error executing startup command: {out}")
    return env


def update_preds_file(output_path: Path, instance_id: str, run_id: int, model_name: str, result: str):
    """Update the output JSON file with results from a single instance run."""
    with _OUTPUT_FILE_LOCK:
        output_data = {}
        if output_path.exists():
            output_data = json.loads(output_path.read_text())

        key = f"{instance_id}_{run_id}"
        output_data[key] = {
            "model_name_or_path": model_name,
            "instance_id": instance_id,
            "run_id": run_id,
            "model_patch": result,
        }
        output_path.write_text(json.dumps(output_data, indent=2))


def process_single_run(
    instance: dict,
    run_id: int,
    output_dir: Path,
    config: dict,
    cost_tracker: CostTracker,
    progress: Progress,
    task_id,
) -> dict:
    """Process a single run of an instance."""
    instance_id = instance["instance_id"]
    instance_dir = output_dir / instance_id
    instance_dir.mkdir(parents=True, exist_ok=True)

    traj_path = instance_dir / f"{instance_id}_{run_id}.traj.json"

    model = get_model(config=config.get("model", {}))
    task = instance["problem_statement"]

    agent = None
    extra_info = None

    try:
        progress.update(task_id, description=f"[cyan]Run {run_id}: Pulling/starting docker")
        env = get_sb_environment(config, instance)

        progress.update(task_id, description=f"[cyan]Run {run_id}: Running agent")
        agent = DefaultAgent(model, env, **config.get("agent", {}))
        exit_status, result = agent.run(task)

    except Exception as e:
        logger.error(f"Error processing {instance_id} run {run_id}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}

    finally:
        # Save trajectory
        save_traj(
            agent,
            traj_path,
            exit_status=exit_status,
            result=result,
            extra_info=extra_info,
            instance_id=instance_id,
            print_fct=logger.info,
        )

        # Update predictions file
        update_preds_file(
            output_dir / "preds.json",
            instance_id,
            run_id,
            model.config.model_name,
            result
        )

        # Track cost
        run_cost = model.cost if agent else 0.0
        cost_tracker.add_cost(run_cost)

        progress.update(task_id, description=f"[green]Run {run_id}: Complete (${run_cost:.4f})")

        return {
            "instance_id": instance_id,
            "run_id": run_id,
            "exit_status": exit_status,
            "cost": run_cost,
        }


def process_instance_n_times(
    instance: dict,
    n_runs: int,
    output_dir: Path,
    config: dict,
    cost_tracker: CostTracker,
    start_run_id: int = 0,
) -> list[dict]:
    """Process an instance N times in parallel, starting from start_run_id."""
    instance_id = instance["instance_id"]

    # Calculate how many runs we actually need
    runs_to_do = n_runs - start_run_id

    if runs_to_do <= 0:
        console.print(f"\n[yellow]⊘ Skipping {instance_id}: already has {start_run_id} trajectories (need {n_runs})[/yellow]")
        return []

    console.print(f"\n[bold blue]Processing instance: {instance_id}[/bold blue]")
    console.print(f"Running {runs_to_do} inferences in parallel (run_ids {start_run_id} to {n_runs-1})...")

    # Create progress bar for this instance
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    )

    results = []

    with progress:
        with concurrent.futures.ThreadPoolExecutor(max_workers=runs_to_do) as executor:
            futures = {}

            for run_id in range(start_run_id, n_runs):
                task_id = progress.add_task(f"[cyan]Run {run_id}: Starting...", total=None)
                future = executor.submit(
                    process_single_run,
                    instance,
                    run_id,
                    output_dir,
                    config,
                    cost_tracker,
                    progress,
                    task_id,
                )
                futures[future] = run_id

            # Wait for all runs to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    run_id = futures[future]
                    logger.error(f"Error in run {run_id}: {e}", exc_info=True)
                    results.append({
                        "instance_id": instance_id,
                        "run_id": run_id,
                        "exit_status": "Error",
                        "cost": 0.0,
                        "error": str(e),
                    })

    total_instance_cost = sum(r["cost"] for r in results)
    console.print(f"[green]✓ Completed {instance_id}: ${total_instance_cost:.4f}[/green]")

    return results


def count_existing_trajectories(instance_id: str, output_path: Path) -> int:
    """Count existing trajectory files for an instance."""
    instance_dir = output_path / instance_id
    if not instance_dir.exists():
        return 0

    # Count trajectory files matching pattern: {instance_id}_*.traj.json
    traj_files = list(instance_dir.glob(f"{instance_id}_*.traj.json"))
    return len(traj_files)


def run_evaluation(
    jsonl_path: str,
    output_dir: str,
    config_path: str,
    n_runs: int = 5,
    cost_limit: float = 100.0,
    max_instances: int | None = None,
):
    """Load instances from JSONL and run evaluation with cost tracking."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to {output_path}")
    add_file_handler(output_path / "minisweagent.log")

    # Load instances from JSONL
    console.print(f"\n[bold]Loading instances from {jsonl_path}...[/bold]")
    instances = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                instances.append(json.loads(line))

    console.print(f"[green]✓ Loaded {len(instances)} instances[/green]")

    # Check existing trajectories and track how many runs are needed per instance
    console.print(f"\n[bold]Checking for existing trajectories...[/bold]")
    instances_with_runs = []  # List of (instance, start_run_id) tuples
    skipped_count = 0

    for instance in instances:
        instance_id = instance["instance_id"]
        existing_count = count_existing_trajectories(instance_id, output_path)

        if existing_count >= n_runs:
            skipped_count += 1
            logger.info(f"Skipping {instance_id}: already has {existing_count} trajectories (need {n_runs})")
        else:
            # Store instance with the run_id to start from
            instances_with_runs.append((instance, existing_count))
            if existing_count > 0:
                logger.info(f"{instance_id}: has {existing_count} trajectories, will run {n_runs - existing_count} more")

    if skipped_count > 0:
        console.print(f"[yellow]⊘ Skipped {skipped_count} instances with sufficient trajectories[/yellow]")

    console.print(f"[green]✓ {len(instances_with_runs)} instances need processing[/green]")

    # Limit to max_instances if specified
    if max_instances is not None and max_instances > 0:
        original_count = len(instances_with_runs)
        instances_with_runs = instances_with_runs[:max_instances]
        if len(instances_with_runs) < original_count:
            console.print(f"[yellow]⊘ Limited to first {max_instances} instances (from {original_count})[/yellow]")

    # Load config
    config_path = get_config_path(Path(config_path))
    console.print(f"[bold]Loading agent config from '{config_path}'[/bold]")
    config = yaml.safe_load(config_path.read_text())

    # Initialize cost tracker
    cost_tracker = CostTracker(cost_limit)

    console.print(f"\n[bold yellow]Configuration:[/bold yellow]")
    console.print(f"  - Instances to process: {len(instances_with_runs)}")
    if max_instances is not None:
        console.print(f"  - Max instances limit: {max_instances}")
    console.print(f"  - Runs per instance: {n_runs}")
    console.print(f"  - Cost limit: ${cost_limit:.2f}")
    console.print(f"  - Model: {config.get('model', {}).get('model_name', 'N/A')}")
    console.print(f"  - Environment: {config.get('environment', {}).get('environment_class', 'docker')}")

    # Track overall statistics
    all_results = []
    completed_instances = 0
    cost_summary = []  # Simple cost tracking per instance

    # Process instances sequentially
    for idx, (instance, start_run_id) in enumerate(instances_with_runs, 1):
        # Check cost limit before starting
        if not cost_tracker.is_under_limit():
            console.print(f"\n[bold red]Cost limit (${cost_limit:.2f}) exceeded![/bold red]")
            console.print(f"Total cost so far: ${cost_tracker.get_total_cost():.2f}")
            console.print(f"Stopping after {completed_instances} instances")
            break

        console.print(f"\n[bold]Instance {idx}/{len(instances_with_runs)}[/bold]")
        console.print(f"Current total cost: ${cost_tracker.get_total_cost():.2f} / ${cost_limit:.2f}")

        # Process this instance N times in parallel, starting from where we left off
        instance_results = process_instance_n_times(
            instance,
            n_runs,
            output_path,
            config,
            cost_tracker,
            start_run_id,  # Start from existing trajectory count
        )

        all_results.extend(instance_results)
        completed_instances += 1

        # Add to cost summary
        instance_total_cost = sum(r["cost"] for r in instance_results)
        cost_summary.append({
            "instance_id": instance["instance_id"],
            "total_cost": round(instance_total_cost, 6),
            "num_runs_completed": len(instance_results),
        })

        # Save cost summary after each instance
        cost_summary_file = output_path / "cost_summary.json"
        with open(cost_summary_file, 'w') as f:
            json.dump({
                "total_cost": round(cost_tracker.get_total_cost(), 6),
                "cost_limit": cost_limit,
                "completed_instances": completed_instances,
                "instances": cost_summary,
            }, f, indent=2)

        # Save progress after each instance
        progress_file = output_path / "progress.json"
        with open(progress_file, 'w') as f:
            json.dump({
                "completed_instances": completed_instances,
                "total_instances": len(instances),
                "total_cost": cost_tracker.get_total_cost(),
                "cost_limit": cost_limit,
                "n_runs": n_runs,
                "results": all_results,
            }, f, indent=2)

    # Final summary
    console.print(f"\n[bold green]{'='*80}[/bold green]")
    console.print(f"[bold green]Evaluation Complete![/bold green]")
    console.print(f"[bold green]{'='*80}[/bold green]")
    console.print(f"  - Completed instances: {completed_instances} / {len(instances)}")
    console.print(f"  - Total runs: {len(all_results)}")
    console.print(f"  - Total cost: ${cost_tracker.get_total_cost():.6f}")
    console.print(f"  - Results saved to: {output_path}")
    console.print(f"\n[bold cyan]Output files:[/bold cyan]")
    console.print(f"  - cost_summary.json    # Clear cost breakdown per instance")
    console.print(f"  - preds.json          # All predictions")
    console.print(f"  - progress.json       # Detailed progress tracking")
    console.print(f"  - <instance_id>/      # Trajectory files")

    logger.info(f"✓ Evaluation complete! Results saved to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run SWE-Smith evaluation with Qwen3-Coder via Amazon Bedrock"
    )
    parser.add_argument("jsonl_path", help="Path to JSONL file with instances")
    parser.add_argument("output_dir", help="Output directory for results")
    parser.add_argument("config_path", help="Path to config YAML file")
    parser.add_argument(
        "--n-runs",
        type=int,
        default=5,
        help="Number of inference runs per instance (default: 5)"
    )
    parser.add_argument(
        "--cost-limit",
        type=float,
        default=100.0,
        help="Maximum cost in USD before stopping (default: $100)"
    )
    parser.add_argument(
        "--max-instances",
        type=int,
        default=None,
        help="Maximum number of instances to process (default: all instances)"
    )

    args = parser.parse_args()

    run_evaluation(
        args.jsonl_path,
        args.output_dir,
        args.config_path,
        args.n_runs,
        args.cost_limit,
        args.max_instances,
    )
