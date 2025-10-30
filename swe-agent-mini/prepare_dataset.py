"""
Prepare JSONL dataset for mini-swe-agent by running evaluation directly.
This bypasses the datasets library issues and runs evaluation with loaded instances.
"""
import concurrent.futures
import json
import sys
import time
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from rich.live import Live
from minisweagent.run.extra.swebench import process_instance
from minisweagent.run.extra.utils.batch_progress import RunBatchProgressManager
from minisweagent.config import get_config_path
from minisweagent.utils.log import add_file_handler, logger


def run_evaluation(jsonl_path: str, output_dir: str, config_path: str, workers: int = 8):
    """Load instances from JSONL and run evaluation directly."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to {output_path}")
    add_file_handler(output_path / "minisweagent.log")

    # Load instances from JSONL
    logger.info(f"Loading instances from {jsonl_path}...")
    instances = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                instances.append(json.loads(line))

    logger.info(f"✓ Loaded {len(instances)} instances from {jsonl_path}")

    # Skip already completed instances
    if (output_path / "preds.json").exists():
        existing_instances = list(json.loads((output_path / "preds.json").read_text()).keys())
        logger.info(f"Skipping {len(existing_instances)} existing instances")
        instances = [instance for instance in instances if instance["instance_id"] not in existing_instances]

    logger.info(f"Running on {len(instances)} instances with {workers} workers...")

    # Load config
    config_path = get_config_path(Path(config_path))
    logger.info(f"Loading agent config from '{config_path}'")
    config = yaml.safe_load(config_path.read_text())

    # Create progress manager
    progress_manager = RunBatchProgressManager(len(instances), output_path / f"exit_statuses_{time.time()}.yaml")

    def process_futures(futures: dict[concurrent.futures.Future, str]):
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except concurrent.futures.CancelledError:
                pass
            except Exception as e:
                instance_id = futures[future]
                logger.error(f"Error in future for instance {instance_id}: {e}", exc_info=True)
                progress_manager.on_uncaught_exception(instance_id, e)

    # Run instances in parallel
    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_instance, instance, output_path, config, progress_manager): instance[
                    "instance_id"
                ]
                for instance in instances
            }
            try:
                process_futures(futures)
            except KeyboardInterrupt:
                logger.info("Cancelling all pending jobs. Press ^C again to exit immediately.")
                for future in futures:
                    if not future.running() and not future.done():
                        future.cancel()
                process_futures(futures)

    logger.info(f"✓ Evaluation complete! Results saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python prepare_dataset.py <jsonl_path> <output_dir> <config_path> <workers>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    output_dir = sys.argv[2]
    config_path = sys.argv[3]
    workers = int(sys.argv[4])

    run_evaluation(jsonl_path, output_dir, config_path, workers)
