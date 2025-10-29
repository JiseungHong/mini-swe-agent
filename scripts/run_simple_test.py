#!/usr/bin/env python3

"""Simple test runner for SWE-bench Pro - no progress display."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minisweagent import Environment
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments import get_environment
from minisweagent.models import get_model
from minisweagent.run.extra.swebench import get_sb_environment, update_preds_file
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import add_file_handler, logger
import yaml
import traceback


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Paths
    dataset_path = Path("data/swebench_pro_sample_100.jsonl")
    output_dir = Path("results/swe_bench_pro_100/gpt-4.1-mini")
    config_path = Path("configs/swebench_pro_gpt4mini.yaml")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Simple SWE-bench Pro Test")
    print("=" * 80)

    # Load instances
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, 'r') as f:
        test_instance = json.loads(f.readline())

    instance_id = test_instance["instance_id"]
    instance_dir = output_dir / instance_id
    instance_dir.mkdir(parents=True, exist_ok=True)

    print(f"Testing instance: {instance_id}")

    # Set up logging
    add_file_handler(output_dir / "minisweagent.log")

    # Load config
    print(f"Loading config from {config_path}...")
    config = yaml.safe_load(config_path.read_text())

    print(f"Creating model...")
    model = get_model(config=config.get("model", {}))

    print(f"Creating environment...")
    env = get_sb_environment(config, test_instance)

    print(f"Creating agent...")
    agent = DefaultAgent(model, env, **config.get("agent", {}))

    print(f"Running agent on task...")
    task = test_instance["problem_statement"]

    try:
        exit_status, result = agent.run(task)
        print(f"Agent completed with status: {exit_status}")
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    else:
        extra_info = None

    # Save results
    print(f"Saving trajectory...")
    traj_file = instance_dir / f"{instance_id}.traj.json"
    save_traj(
        agent,
        traj_file,
        exit_status=exit_status,
        result=result,
        extra_info=extra_info,
        instance_id=instance_id,
        print_fct=print,
    )

    print(f"Updating predictions file...")
    update_preds_file(output_dir / "preds.json", instance_id, model.config.model_name, result)

    print()
    print("=" * 80)
    print("Test Complete!")
    print(f"Trajectory: {traj_file}")
    print(f"Predictions: {output_dir}/preds.json")
    print(f"Model cost: ${model.cost:.2f}")
    print(f"API calls: {model.n_calls}")
    print("=" * 80)


if __name__ == "__main__":
    main()
