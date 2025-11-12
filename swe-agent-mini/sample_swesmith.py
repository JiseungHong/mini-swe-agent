#!/usr/bin/env python3

"""Sample ~1k instances from SWE-Smith while maintaining repository diversity.

This script samples 5 instances from each repository in SWE-Smith
to create a diverse subset of approximately 1k instances.
"""

import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from datasets import load_dataset

# Set random seed for reproducibility
RANDOM_SEED = 42
SAMPLES_PER_REPO = 5

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "swesmith"
OUTPUT_JSONL = OUTPUT_DIR / "swesmith_sample_1k.jsonl"
OUTPUT_IDS = OUTPUT_DIR / "swesmith_sample_1k_ids.txt"
OUTPUT_METADATA = OUTPUT_DIR / "swesmith_sample_1k_metadata.json"


def main():
    print("=" * 80)
    print("SWE-Smith Sampling Script")
    print("=" * 80)
    print()

    # Load SWE-Smith dataset
    print("Loading SWE-Smith dataset...")
    swesmith = load_dataset("SWE-bench/SWE-smith", split="train")
    print(f"✓ Loaded {len(swesmith)} instances from SWE-Smith")

    # Print available columns
    if len(swesmith) > 0:
        sample_instance = swesmith[0]
        print(f"Available columns: {list(sample_instance.keys())}")
    print()

    # Group instances by repository
    print("Grouping instances by repository...")
    repo_instances = defaultdict(list)
    for instance in swesmith:
        repo = instance["repo"]
        repo_instances[repo].append(instance)

    print(f"✓ Found {len(repo_instances)} unique repositories")
    print()

    # Print repository statistics
    print("Repository statistics:")
    repo_counts = {repo: len(instances) for repo, instances in repo_instances.items()}
    print(f"  - Total repositories: {len(repo_counts)}")
    print(f"  - Min instances per repo: {min(repo_counts.values())}")
    print(f"  - Max instances per repo: {max(repo_counts.values())}")
    print(f"  - Avg instances per repo: {sum(repo_counts.values()) / len(repo_counts):.1f}")
    print()

    # Check if all repositories have at least SAMPLES_PER_REPO instances
    repos_with_insufficient_instances = {
        repo: count for repo, count in repo_counts.items() if count < SAMPLES_PER_REPO
    }

    if repos_with_insufficient_instances:
        print(f"⚠ Warning: {len(repos_with_insufficient_instances)} repositories have fewer than {SAMPLES_PER_REPO} instances:")
        for repo, count in sorted(repos_with_insufficient_instances.items(), key=lambda x: x[1]):
            print(f"  - {repo}: {count} instances")
        print()

    # Sample instances from each repository
    print(f"Sampling {SAMPLES_PER_REPO} instances from each repository (seed={RANDOM_SEED})...")
    random.seed(RANDOM_SEED)
    sampled_instances = []

    for repo in sorted(repo_instances.keys()):
        instances = repo_instances[repo]
        # If repo has fewer instances than requested, take all of them
        sample_size = min(SAMPLES_PER_REPO, len(instances))
        sampled = random.sample(instances, sample_size)
        sampled_instances.extend(sampled)

    print(f"✓ Sampled {len(sampled_instances)} instances from {len(repo_instances)} repositories")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as JSONL (one JSON object per line)
    # Note: All columns from the original dataset are preserved
    print(f"Saving sampled instances to {OUTPUT_JSONL}...")
    with open(OUTPUT_JSONL, "w") as f:
        for instance in sampled_instances:
            # Convert dataset instance to dict to ensure all columns are included
            instance_dict = dict(instance)
            f.write(json.dumps(instance_dict) + "\n")
    print(f"✓ Saved {len(sampled_instances)} instances with all original columns")

    # Verify columns are preserved
    with open(OUTPUT_JSONL, "r") as f:
        first_line = f.readline()
        saved_instance = json.loads(first_line)
        print(f"✓ Verified: {len(saved_instance)} columns preserved in output")
    print()

    # Save instance IDs only
    print(f"Saving instance IDs to {OUTPUT_IDS}...")
    instance_ids = [instance["instance_id"] for instance in sampled_instances]
    with open(OUTPUT_IDS, "w") as f:
        for instance_id in sorted(instance_ids):
            f.write(instance_id + "\n")
    print(f"✓ Saved {len(instance_ids)} instance IDs")
    print()

    # Calculate per-repository statistics for sampled data
    sampled_repo_counts = defaultdict(int)
    for instance in sampled_instances:
        sampled_repo_counts[instance["repo"]] += 1

    # Save metadata
    metadata = {
        "sampling_date": datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "samples_per_repo": SAMPLES_PER_REPO,
        "total_instances": len(swesmith),
        "total_repositories": len(repo_instances),
        "sampled_instances": len(sampled_instances),
        "repository_counts": dict(repo_counts),
        "sampled_repository_counts": dict(sampled_repo_counts),
        "repositories_with_insufficient_instances": len(repos_with_insufficient_instances),
        "instance_ids": sorted(instance_ids),
    }
    print(f"Saving metadata to {OUTPUT_METADATA}...")
    with open(OUTPUT_METADATA, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata")
    print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total SWE-Smith instances:        {len(swesmith)}")
    print(f"Total repositories:               {len(repo_instances)}")
    print(f"Target samples per repository:    {SAMPLES_PER_REPO}")
    print(f"Total sampled instances:          {len(sampled_instances)}")
    print(f"Repositories with <{SAMPLES_PER_REPO} instances:  {len(repos_with_insufficient_instances)}")
    print()
    print("Output files:")
    print(f"  - {OUTPUT_JSONL}")
    print(f"  - {OUTPUT_IDS}")
    print(f"  - {OUTPUT_METADATA}")
    print()
    print("✓ Done!")


if __name__ == "__main__":
    main()
