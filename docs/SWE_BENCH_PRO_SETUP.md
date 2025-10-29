# SWE-bench Pro 100 Instance Setup

This document describes the setup for running inference on 100 sampled instances from SWE-bench_Pro.

## Dataset Sampling

We randomly sampled 100 instances from `ScaleAI/SWE-bench_Pro` that do not overlap with SWE-Bench Verified.

### Sampling Results

- **SWE-bench_Pro total**: 731 instances
- **SWE-Bench Verified total**: 500 instances
- **Overlap**: 0 instances (datasets are completely disjoint)
- **Sampled**: 100 instances (random seed: 42)

### Generated Files

- `data/swebench_pro_sample_100.jsonl` - Full instance data (JSONL format)
- `data/swebench_pro_sample_100_ids.txt` - Instance IDs only (one per line)
- `data/swebench_pro_sample_100_metadata.json` - Sampling metadata

## Directory Structure

```
results/swe_bench_pro_100/
└── {model_name}/           # e.g., gpt-4.1-mini
    ├── preds.json          # Predictions file (consolidated)
    ├── minisweagent.log    # Agent log
    └── {instance_id}/      # One directory per instance
        └── {instance_id}.traj.json  # Trajectory file
```

## Running Inference

### Prerequisites

1. Set up virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set your API key:
```bash
export OPENAI_API_KEY='your_api_key_here'
```

### Test with 1 Instance

To test with a single instance (recommended first step):

```bash
# Using the Python script
OPENAI_API_KEY='your_key' python scripts/run_swebench_pro_test.py

# Or using venv
OPENAI_API_KEY='your_key' ./venv/bin/python scripts/run_swebench_pro_test.py
```

This will:
- Load the first instance from `data/swebench_pro_sample_100.jsonl`
- Run inference using `gpt-4.1-mini` via CMU AI Gateway
- Save results to `results/swe_bench_pro_100/gpt-4.1-mini/`

### Run All 100 Instances

**⚠️ WARNING: This is expensive! Estimated cost ~$100-300 depending on model.**

To run all 100 instances, you would need to modify the test script or use the main swebench runner:

```bash
# This would run all instances - USE WITH CAUTION
# (Script modification needed - not implemented yet)
```

## Configuration

The configuration file `configs/swebench_pro_gpt4mini.yaml` contains:

- **Agent settings**: System prompts, templates, step limits
- **Environment settings**: Docker environment, timeouts
- **Model settings**:
  - Model: `gpt-4.1-mini`
  - API Base: `https://ai-gateway.andrew.cmu.edu/`
  - Temperature: 0.0
  - Cost limit: $3 per instance

## Output Format

Each trajectory file (`{instance_id}.traj.json`) contains:

```json
{
  "info": {
    "exit_status": "Submitted",
    "submission": "diff --git ...",
    "model_stats": {
      "instance_cost": 0.01544195,
      "api_calls": 7
    },
    "mini_version": "1.7.0"
  },
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "trajectory_format": "mini-swe-agent-1",
  "instance_id": "instance_..."
}
```

## Sampling Script

To re-run the sampling or create a different sample:

```bash
./venv/bin/python scripts/sample_swebench_pro.py
```

This will regenerate the sample with the same random seed (42) for reproducibility.

## API Testing

To test the CMU AI Gateway connection:

```bash
OPENAI_API_KEY='your_key' python scripts/api_key_reference.py
```

This will make a simple API call to verify your credentials are working.
