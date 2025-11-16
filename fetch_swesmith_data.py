#!/usr/bin/env python3
"""
Fetch first 10 samples from SWE-bench/SWE-smith-trajectories dataset
and save them in the same format as data/swesmith/
"""

import json
from datetime import datetime
from datasets import load_dataset

def main():
    print("Loading SWE-smith-trajectories dataset from Hugging Face (streaming mode)...")

    # Load the dataset in streaming mode (using 'tool' split)
    dataset = load_dataset("SWE-bench/SWE-smith-trajectories", split="tool", streaming=True)

    print("Dataset loaded in streaming mode. Fetching first 10 samples where resolved=true...")

    # Get first 10 samples where resolved is true
    first_10 = []
    total_checked = 0
    for item in dataset:
        total_checked += 1
        if item.get('resolved', False):
            first_10.append(item)
            print(f"  Fetched sample {len(first_10)}/10: {item.get('instance_id', 'unknown')} (checked {total_checked} samples)")
            if len(first_10) >= 10:
                break

    # Prepare output files
    output_dir = "/Users/user-jiseung/Documents/CMU/GitHub/mini-swe-agent/data/swesmith_true"
    jsonl_file = f"{output_dir}/swesmith_sample_10.jsonl"
    ids_file = f"{output_dir}/swesmith_sample_10_ids.txt"
    metadata_file = f"{output_dir}/swesmith_sample_10_metadata.json"

    # Extract instance IDs and write JSONL
    instance_ids = []

    print(f"Writing {len(first_10)} samples to {jsonl_file}...")
    with open(jsonl_file, 'w') as f:
        for item in first_10:
            # Write the item as a JSON line
            json.dump(dict(item), f)
            f.write('\n')

            # Collect instance ID
            if 'instance_id' in item:
                instance_ids.append(item['instance_id'])

    # Write instance IDs
    print(f"Writing instance IDs to {ids_file}...")
    with open(ids_file, 'w') as f:
        for instance_id in instance_ids:
            f.write(f"{instance_id}\n")

    # Create metadata
    metadata = {
        "sampling_date": datetime.now().isoformat(),
        "source": "SWE-bench/SWE-smith-trajectories",
        "samples_fetched": len(first_10),
        "instance_ids": instance_ids
    }

    print(f"Writing metadata to {metadata_file}...")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print("\nDone!")
    print(f"Created files:")
    print(f"  - {jsonl_file}")
    print(f"  - {ids_file}")
    print(f"  - {metadata_file}")
    print(f"\nFirst 10 instance IDs:")
    for i, instance_id in enumerate(instance_ids, 1):
        print(f"  {i}. {instance_id}")

if __name__ == "__main__":
    main()
