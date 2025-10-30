#!/usr/bin/env python3

"""Sample 100 instances from SWE-bench_Pro that don't overlap with SWE-Bench Verified."""

import json
import random
from datetime import datetime
from pathlib import Path

from datasets import load_dataset

# Set random seed for reproducibility
RANDOM_SEED = 42
SAMPLE_SIZE = 100

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_JSONL = OUTPUT_DIR / "swebench_pro_sample_100.jsonl"
OUTPUT_IDS = OUTPUT_DIR / "swebench_pro_sample_100_ids.txt"
OUTPUT_METADATA = OUTPUT_DIR / "swebench_pro_sample_100_metadata.json"


def main():
    print("=" * 80)
    print("SWE-bench_Pro Sampling Script")
    print("=" * 80)
    print()

    # Load SWE-bench_Pro
    print("Loading SWE-bench_Pro dataset...")
    swebench_pro = load_dataset("ScaleAI/SWE-bench_Pro", split="test")
    print(f"✓ Loaded {len(swebench_pro)} instances from SWE-bench_Pro")
    print()

    # Load SWE-Bench Verified
    print("Loading SWE-Bench Verified dataset...")
    swebench_verified = load_dataset("princeton-nlp/SWE-Bench_Verified", split="test")
    print(f"✓ Loaded {len(swebench_verified)} instances from SWE-Bench Verified")
    print()

    # Get instance IDs from Verified dataset
    verified_ids = set(instance["instance_id"] for instance in swebench_verified)
    print(f"Identified {len(verified_ids)} instance IDs in SWE-Bench Verified")
    print()

    # Filter out overlapping instances
    print("Filtering out instances that overlap with SWE-Bench Verified...")
    non_overlapping = [
        instance for instance in swebench_pro if instance["instance_id"] not in verified_ids
    ]
    print(f"✓ Found {len(non_overlapping)} non-overlapping instances")
    print()

    # Check if we have enough instances
    if len(non_overlapping) < SAMPLE_SIZE:
        raise ValueError(
            f"Not enough non-overlapping instances! Found {len(non_overlapping)}, need {SAMPLE_SIZE}"
        )

    # Sample 100 instances
    print(f"Sampling {SAMPLE_SIZE} instances with random seed {RANDOM_SEED}...")
    random.seed(RANDOM_SEED)
    sampled_instances = random.sample(non_overlapping, SAMPLE_SIZE)
    print(f"✓ Sampled {len(sampled_instances)} instances")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as JSONL (one JSON object per line)
    print(f"Saving sampled instances to {OUTPUT_JSONL}...")
    with open(OUTPUT_JSONL, "w") as f:
        for instance in sampled_instances:
            f.write(json.dumps(instance) + "\n")
    print(f"✓ Saved {len(sampled_instances)} instances")
    print()

    # Save instance IDs only
    print(f"Saving instance IDs to {OUTPUT_IDS}...")
    instance_ids = [instance["instance_id"] for instance in sampled_instances]
    with open(OUTPUT_IDS, "w") as f:
        for instance_id in sorted(instance_ids):
            f.write(instance_id + "\n")
    print(f"✓ Saved {len(instance_ids)} instance IDs")
    print()

    # Save metadata
    metadata = {
        "sampling_date": datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "sample_size": SAMPLE_SIZE,
        "swebench_pro_total": len(swebench_pro),
        "swebench_verified_total": len(swebench_verified),
        "non_overlapping_total": len(non_overlapping),
        "overlap_count": len(swebench_pro) - len(non_overlapping),
        "instance_ids": sorted(instance_ids),
    }
    print(f"Saving metadata to {OUTPUT_METADATA}...")
    with open(OUTPUT_METADATA, "w") as f:
        f.write(json.dumps(metadata, indent=2))
    print(f"✓ Saved metadata")
    print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"SWE-bench_Pro instances:     {len(swebench_pro)}")
    print(f"SWE-Bench Verified instances: {len(swebench_verified)}")
    print(f"Overlapping instances:        {len(swebench_pro) - len(non_overlapping)}")
    print(f"Non-overlapping instances:    {len(non_overlapping)}")
    print(f"Sampled instances:            {len(sampled_instances)}")
    print()
    print("Output files:")
    print(f"  - {OUTPUT_JSONL}")
    print(f"  - {OUTPUT_IDS}")
    print(f"  - {OUTPUT_METADATA}")
    print()
    print("✓ Done!")


if __name__ == "__main__":
    main()
