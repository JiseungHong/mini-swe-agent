#!/usr/bin/env python3

"""Run 1 test instance from SWE-bench Pro sample with gpt-4.1-mini."""

import json
import os
import sys
from pathlib import Path

from datasets import Dataset

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minisweagent.run.extra.swebench import main as swebench_main, process_instance, RunBatchProgressManager
from minisweagent.config import get_config_path
from minisweagent.utils.log import add_file_handler, logger
import yaml


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Usage: OPENAI_API_KEY='your_key' python scripts/run_swebench_pro_test.py", file=sys.stderr)
        sys.exit(1)

    # Paths
    dataset_path = Path("data/swebench_pro_sample_100.jsonl")
    output_dir = Path("results/swe_bench_pro_100/gpt-4.1-mini")
    config_path = Path("configs/swebench_pro_gpt4mini.yaml")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load instances from JSONL
    print("=" * 80)
    print("Running SWE-bench Pro Test Instance")
    print("=" * 80)
    print(f"Dataset: {dataset_path}")
    print(f"Output:  {output_dir}")
    print(f"Config:  {config_path}")
    print("=" * 80)
    print()

    print(f"Loading dataset from {dataset_path}...")
    instances = []
    with open(dataset_path, 'r') as f:
        for line in f:
            instances.append(json.loads(line))

    print(f"Loaded {len(instances)} instances")

    # Take only the first instance for testing
    test_instance = instances[0]
    instance_id = test_instance["instance_id"]

    print(f"Testing with instance: {instance_id}")
    print()

    # Set up logging
    add_file_handler(output_dir / "minisweagent.log")

    # Load config
    print(f"Loading config from {config_path}...")
    config = yaml.safe_load(config_path.read_text())

    # Override model settings to use CMU gateway
    config["model"]["model_class"] = "litellm"
    config["model"]["model_name"] = "gpt-4.1-mini"
    config["model"]["model_kwargs"] = {
        "temperature": 0.0,
        "api_base": "https://ai-gateway.andrew.cmu.edu/"
    }

    print("Config loaded and updated for gpt-4.1-mini")
    print()

    # Create progress manager
    progress_manager = RunBatchProgressManager(1, output_dir / "exit_statuses.yaml")

    # Process the instance
    print(f"Processing instance {instance_id}...")
    print()

    try:
        from rich.live import Live
        with Live(progress_manager.render_group, refresh_per_second=4):
            process_instance(test_instance, output_dir, config, progress_manager)
    except Exception as e:
        logger.error(f"Error processing instance: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=" * 80)
    print("Test run completed!")
    print("=" * 80)
    print(f"Results saved to: {output_dir}/{instance_id}/")
    print(f"Trajectory: {output_dir}/{instance_id}/{instance_id}.traj.json")
    print(f"Predictions: {output_dir}/preds.json")
    print()


if __name__ == "__main__":
    main()
