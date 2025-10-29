#!/usr/bin/env python3

"""Run all 100 SWE-bench_Pro instances with a specified model."""

import argparse
import concurrent.futures
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from rich.live import Live

from minisweagent.run.extra.swebench import process_instance, RunBatchProgressManager
from minisweagent.utils.log import add_file_handler, logger


def main():
    parser = argparse.ArgumentParser(description="Run SWE-bench_Pro evaluation")
    parser.add_argument(
        "--model",
        required=True,
        choices=["qwen3-coder", "devstral", "cwm"],
        help="Model to use for evaluation"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel workers (default: 8, recommended for g5.4xlarge)"
    )
    parser.add_argument(
        "--slice",
        type=str,
        default="",
        help="Slice specification (e.g., '0:10' for first 10 instances)"
    )

    args = parser.parse_args()

    # Paths
    dataset_path = Path("data/swebench_pro_sample_100.jsonl")
    config_path = Path(f"configs/{args.model}.yaml")
    output_dir = Path(f"results/swe_bench_pro_100/{args.model}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    add_file_handler(output_dir / "minisweagent.log")

    print("=" * 80)
    print(f"SWE-bench_Pro Evaluation - {args.model.upper()}")
    print("=" * 80)
    print(f"Dataset: {dataset_path}")
    print(f"Config: {config_path}")
    print(f"Output: {output_dir}")
    print(f"Workers: {args.workers}")
    print("=" * 80)
    print()

    # Load instances
    logger.info(f"Loading dataset from {dataset_path}...")
    instances = []
    with open(dataset_path, 'r') as f:
        for line in f:
            instances.append(json.loads(line))

    logger.info(f"Loaded {len(instances)} instances")

    # Apply slice if specified
    if args.slice:
        values = [int(x) if x else None for x in args.slice.split(":")]
        instances = instances[slice(*values)]
        logger.info(f"Using slice {args.slice}: {len(instances)} instances")

    # Load config
    logger.info(f"Loading config from {config_path}...")
    config = yaml.safe_load(config_path.read_text())

    # Skip instances that already have results
    preds_file = output_dir / "preds.json"
    if preds_file.exists():
        existing = set(json.loads(preds_file.read_text()).keys())
        logger.info(f"Found {len(existing)} existing results, skipping them")
        instances = [inst for inst in instances if inst["instance_id"] not in existing]
        logger.info(f"Remaining instances to process: {len(instances)}")

    if not instances:
        logger.info("No instances to process!")
        return

    # Create progress manager
    progress_manager = RunBatchProgressManager(
        len(instances),
        output_dir / f"exit_statuses.yaml"
    )

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

    # Run evaluation with progress display
    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_instance, instance, output_dir, config, progress_manager): instance["instance_id"]
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

    print()
    print("=" * 80)
    print("Evaluation Complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
