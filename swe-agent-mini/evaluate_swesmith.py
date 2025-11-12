#!/usr/bin/env python3

"""
Evaluate SWE-Smith predictions using the official SWE-Bench evaluation harness.
Features:
- Skips already evaluated instances
- Handles multiple runs per instance
- Provides clear progress tracking
"""

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def load_predictions(preds_file: Path) -> dict:
    """Load predictions from preds.json."""
    if not preds_file.exists():
        console.print(f"[red]Error: Predictions file not found: {preds_file}[/red]")
        sys.exit(1)

    with open(preds_file, 'r') as f:
        preds = json.load(f)

    return preds


def load_existing_results(results_file: Path) -> set:
    """Load already evaluated instance IDs from results file."""
    if not results_file.exists():
        return set()

    try:
        with open(results_file, 'r') as f:
            results = json.load(f)

        # Handle both list and dict formats
        if isinstance(results, list):
            return {r['instance_id'] for r in results if 'instance_id' in r}
        elif isinstance(results, dict):
            return set(results.keys())
        else:
            return set()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load existing results: {e}[/yellow]")
        return set()


def group_predictions_by_instance(preds: dict) -> dict:
    """Group predictions by base instance_id (without run_id suffix)."""
    grouped = {}

    for key, pred in preds.items():
        instance_id = pred.get('instance_id')
        if not instance_id:
            console.print(f"[yellow]Warning: Skipping prediction with no instance_id: {key}[/yellow]")
            continue

        if instance_id not in grouped:
            grouped[instance_id] = []

        grouped[instance_id].append({
            'key': key,
            'run_id': pred.get('run_id', 0),
            'patch': pred.get('model_patch', '')
        })

    return grouped


def select_best_prediction(runs: list) -> dict:
    """Select the best prediction from multiple runs.

    Currently selects run_id=0, but could be extended with voting or other strategies.
    """
    # Sort by run_id and take the first one
    runs.sort(key=lambda x: x['run_id'])
    return runs[0]


def prepare_evaluation_preds(preds: dict, skip_instances: set) -> tuple[dict, dict]:
    """Prepare predictions for evaluation harness and track what was included."""
    grouped = group_predictions_by_instance(preds)

    eval_preds = {}
    included_info = {}
    skipped_count = 0

    for instance_id, runs in grouped.items():
        if instance_id in skip_instances:
            skipped_count += 1
            continue

        # Select best prediction from multiple runs
        best_run = select_best_prediction(runs)

        # Format for evaluation harness (it expects instance_id as key)
        eval_preds[instance_id] = {
            'instance_id': instance_id,
            'model_patch': best_run['patch'],
            'model_name_or_path': preds[best_run['key']].get('model_name_or_path', 'unknown')
        }

        included_info[instance_id] = {
            'total_runs': len(runs),
            'selected_run_id': best_run['run_id'],
        }

    console.print(f"\n[bold]Prediction Summary:[/bold]")
    console.print(f"  - Total unique instances: {len(grouped)}")
    console.print(f"  - Already evaluated (skipped): {skipped_count}")
    console.print(f"  - To be evaluated: {len(eval_preds)}")

    return eval_preds, included_info


def run_evaluation(
    dataset_file: Path,
    eval_preds: dict,
    output_dir: Path,
    num_workers: int = 4,
    timeout: int = 900,
):
    """Run the SWE-Bench evaluation harness."""

    if len(eval_preds) == 0:
        console.print("\n[yellow]No instances to evaluate. All done![/yellow]")
        return

    # Create temporary predictions file for harness
    temp_preds_file = output_dir / "temp_eval_preds.json"
    with open(temp_preds_file, 'w') as f:
        json.dump(eval_preds, f, indent=2)

    console.print(f"\n[bold green]Starting Evaluation[/bold green]")
    console.print(f"  - Instances: {len(eval_preds)}")
    console.print(f"  - Workers: {num_workers}")
    console.print(f"  - Timeout: {timeout}s per instance")
    console.print(f"  - Temp predictions: {temp_preds_file}")
    console.print()

    # Prepare evaluation command
    eval_dir = output_dir / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python", "-m", "swebench.harness.run_evaluation",
        "--dataset_name", "princeton-nlp/SWE-bench",
        "--predictions_path", str(temp_preds_file),
        "--max_workers", str(num_workers),
        "--timeout", str(timeout),
        "--run_id", "evaluation",
        "--cache_level", "env",
    ]

    # Check if dataset file is provided
    if dataset_file and dataset_file.exists():
        # If we have a local dataset file, we might need to use it differently
        console.print(f"[yellow]Note: Using dataset from Hugging Face. Local file provided: {dataset_file}[/yellow]")

    console.print(f"[bold cyan]Running command:[/bold cyan]")
    console.print(f"  {' '.join(cmd)}")
    console.print()

    try:
        # Run the evaluation
        result = subprocess.run(
            cmd,
            cwd=output_dir,
            check=True,
            text=True,
            capture_output=False  # Show output in real-time
        )

        console.print(f"\n[bold green]✓ Evaluation completed successfully![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"\n[bold red]✗ Evaluation failed with exit code {e.returncode}[/bold red]")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        console.print("\n[bold red]✗ SWE-Bench evaluation harness not found![/bold red]")
        console.print("\n[yellow]Please install it:[/yellow]")
        console.print("  pip install swebench")
        console.print("\n[yellow]Or from source:[/yellow]")
        console.print("  git clone https://github.com/princeton-nlp/SWE-bench.git")
        console.print("  cd SWE-bench")
        console.print("  pip install -e .")
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate SWE-Smith predictions with smart skipping"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Output directory containing preds.json"
    )
    parser.add_argument(
        "--dataset-file",
        type=Path,
        default=None,
        help="Path to dataset JSONL file (for reference)"
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=None,
        help="Path to existing results file to skip (default: output_dir/evaluation/results.json)"
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout per instance in seconds (default: 900)"
    )

    args = parser.parse_args()

    # Validate paths
    preds_file = args.output_dir / "preds.json"
    if not preds_file.exists():
        console.print(f"[red]Error: preds.json not found in {args.output_dir}[/red]")
        sys.exit(1)

    # Determine results file location
    if args.results_file:
        results_file = args.results_file
    else:
        results_file = args.output_dir / "evaluation" / "results.json"

    console.print("[bold]SWE-Smith Evaluation Script[/bold]")
    console.print(f"  - Output directory: {args.output_dir}")
    console.print(f"  - Predictions file: {preds_file}")
    console.print(f"  - Results file: {results_file}")
    console.print()

    # Load predictions
    console.print("[bold]Loading predictions...[/bold]")
    preds = load_predictions(preds_file)
    console.print(f"  ✓ Loaded {len(preds)} predictions")

    # Load existing results to skip
    console.print("\n[bold]Checking for existing results...[/bold]")
    skip_instances = load_existing_results(results_file)
    if skip_instances:
        console.print(f"  ✓ Found {len(skip_instances)} already evaluated instances")
    else:
        console.print("  - No existing results found (will evaluate all)")

    # Prepare predictions for evaluation
    eval_preds, included_info = prepare_evaluation_preds(preds, skip_instances)

    # Save info about what was included
    info_file = args.output_dir / "evaluation_info.json"
    with open(info_file, 'w') as f:
        json.dump({
            'total_predictions': len(preds),
            'unique_instances': len(group_predictions_by_instance(preds)),
            'skipped_instances': len(skip_instances),
            'evaluated_instances': len(eval_preds),
            'included_details': included_info,
        }, f, indent=2)
    console.print(f"\n  ✓ Saved evaluation info to {info_file}")

    # Run evaluation
    if len(eval_preds) > 0:
        run_evaluation(
            args.dataset_file,
            eval_preds,
            args.output_dir,
            args.num_workers,
            args.timeout,
        )
    else:
        console.print("\n[bold green]✓ All instances already evaluated![/bold green]")

    console.print(f"\n[bold]Evaluation results will be in:[/bold]")
    console.print(f"  {args.output_dir / 'evaluation'}")


if __name__ == "__main__":
    main()
