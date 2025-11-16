#!/usr/bin/env python3
"""
Check if the 10 resolved instances exist in SWE-bench/SWE-smith
and create files with that data (which includes docker image info)
"""

import json
from datasets import load_dataset

# The 10 instance IDs we found in SWE-smith-trajectories with resolved=true
target_instance_ids = [
    "django-money__django-money.835c1ab8.func_pm_ctrl_shuffle__viqnyl9u",
    "marshmallow-code__apispec.8b421526.func_pm_remove_assign__kdkrbg6a",
    "mozillazg__python-pinyin.e42dede5.func_pm_remove_assign__vn346ybe",
    "marshmallow-code__marshmallow.9716fc62.func_pm_class_rm_funcs__e35a2bbx",
    "luozhouyang__python-string-similarity.115acaac.func_pm_remove_cond__gch4emzr",
    "tkrajina__gpxpy.09fc46b3.func_pm_ctrl_shuffle__grix6fbc",
    "sloria__environs.73c372df.func_pm_remove_assign__l35izs7k",
    "amueller__word_cloud.ec24191c.func_pm_ctrl_shuffle__3gl981ew",
    "pallets__jinja.ada0a9a6.func_pm_ctrl_invert_if__ik1ndo54",
    "google__textfsm.c31b6007.func_pm_ctrl_shuffle__hjtsbxdc"
]

def main():
    print("Loading SWE-bench/SWE-smith dataset from Hugging Face (streaming mode)...")

    # Load the dataset in streaming mode
    dataset = load_dataset("SWE-bench/SWE-smith", split="train", streaming=True)

    print(f"Searching for {len(target_instance_ids)} instance IDs in SWE-smith...")

    found_instances = []
    found_ids = set()
    checked_count = 0

    for item in dataset:
        checked_count += 1
        instance_id = item.get('instance_id')

        if instance_id in target_instance_ids and instance_id not in found_ids:
            found_instances.append(item)
            found_ids.add(instance_id)
            print(f"  Found {len(found_instances)}/{len(target_instance_ids)}: {instance_id}")

            # Check if it has image_name
            if 'image_name' in item:
                print(f"    -> Has image_name: {item['image_name']}")

            if len(found_instances) >= len(target_instance_ids):
                print(f"\nFound all {len(target_instance_ids)} instances after checking {checked_count} samples!")
                break

        if checked_count % 1000 == 0:
            print(f"  Checked {checked_count} samples, found {len(found_instances)} so far...")

    print(f"\nSearch complete. Checked {checked_count} samples.")
    print(f"Found {len(found_instances)}/{len(target_instance_ids)} instances in SWE-smith.")

    if len(found_instances) == 0:
        print("\nNo instances found in SWE-smith. The instances might not exist in this dataset.")
        return

    # Prepare output files
    output_dir = "/Users/user-jiseung/Documents/CMU/GitHub/mini-swe-agent/data/swesmith_true"
    jsonl_file = f"{output_dir}/swesmith_sample_10.jsonl"
    ids_file = f"{output_dir}/swesmith_sample_10_ids.txt"
    metadata_file = f"{output_dir}/swesmith_sample_10_metadata.json"

    # Write JSONL file
    print(f"\nWriting {len(found_instances)} samples to {jsonl_file}...")
    with open(jsonl_file, 'w') as f:
        for item in found_instances:
            json.dump(dict(item), f)
            f.write('\n')

    # Write instance IDs
    print(f"Writing instance IDs to {ids_file}...")
    with open(ids_file, 'w') as f:
        for item in found_instances:
            f.write(f"{item['instance_id']}\n")

    # Create metadata
    from datetime import datetime
    metadata = {
        "sampling_date": datetime.now().isoformat(),
        "source": "SWE-bench/SWE-smith",
        "samples_fetched": len(found_instances),
        "instance_ids": [item['instance_id'] for item in found_instances],
        "note": "These instances were selected based on resolved=true from SWE-smith-trajectories"
    }

    print(f"Writing metadata to {metadata_file}...")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print("\nDone!")
    print(f"Created files:")
    print(f"  - {jsonl_file}")
    print(f"  - {ids_file}")
    print(f"  - {metadata_file}")

    print(f"\nFound instance IDs:")
    for i, item in enumerate(found_instances, 1):
        print(f"  {i}. {item['instance_id']}")
        if 'image_name' in item:
            print(f"     Image: {item['image_name']}")

    # Show what's missing
    missing_ids = set(target_instance_ids) - found_ids
    if missing_ids:
        print(f"\nMissing {len(missing_ids)} instances (not found in SWE-smith):")
        for instance_id in missing_ids:
            print(f"  - {instance_id}")

if __name__ == "__main__":
    main()
