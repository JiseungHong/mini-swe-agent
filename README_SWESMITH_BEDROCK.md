# SWE-Smith Inference with Qwen3-Coder via Amazon Bedrock

This guide explains how to run inference on SWE-Smith instances using Qwen3-Coder-30B via Amazon Bedrock.

## Overview

The system provides:
- **Repository-diverse sampling**: Sample ~1k instances from SWE-Smith (50k+) while maintaining diversity across 222 repositories
- **Cost tracking**: Monitor costs and stop when exceeding a configurable limit
- **Multiple runs per instance**: Run N inferences per instance in parallel
- **Proper trajectory saving**: Save all trajectories with naming `{instance_id}_{n}`
- **Complete trajectory information**: Each trajectory includes all necessary information for evaluation

## Files Created

1. **`swe-agent-mini/sample_swesmith.py`**: Samples diverse instances from SWE-Smith
2. **`swe-agent-mini/run_swesmith_bedrock.py`**: Main inference script with cost tracking
3. **`configs/qwen3_coder_bedrock.yaml`**: Configuration for Qwen3-Coder with Bedrock
4. **`scripts/run_qwen3_coder_bedrock_swesmith.sh`**: Convenience bash script

## Prerequisites

1. **AWS Credentials**: You need AWS access credentials with Bedrock permissions
2. **Virtual Environment**: Python virtual environment with required packages
3. **Docker**: Docker must be installed and running (used for SWE-Bench containers)
4. **SWE-Smith Dataset**: Sampled dataset (created in Step 1)

## Step 1: Sample SWE-Smith Instances

First, create a diverse sample of ~1k instances from SWE-Smith:

```bash
# Activate virtual environment
source venv/bin/activate

# Run sampling script
python swe-agent-mini/sample_swesmith.py
```

This will create:
- `data/swesmith/swesmith_sample_1k.jsonl` - 1,092 instances (5 per repository)
- `data/swesmith/swesmith_sample_1k_ids.txt` - List of instance IDs
- `data/swesmith/swesmith_sample_1k_metadata.json` - Sampling metadata

**Key Statistics:**
- Total instances sampled: 1,092
- Repositories covered: 222
- Samples per repository: 5 (or all available if < 5)
- All columns preserved for inference

## Step 2: Set Up AWS Credentials

Export your AWS credentials as environment variables:

```bash
export AWS_ACCESS_KEY_ID='your_access_key_id'
export AWS_SECRET_ACCESS_KEY='your_secret_access_key'
export AWS_REGION_NAME='us-east-1'  # Optional, defaults to us-east-1
```

## Step 3: Run Inference

### Option A: Using the Bash Script (Recommended)

```bash
# Run with default settings (5 runs per instance, $100 cost limit)
bash scripts/run_qwen3_coder_bedrock_swesmith.sh

# Or customize with environment variables
N_RUNS=3 COST_LIMIT=50.0 bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

### Option B: Using Python Directly

```bash
source venv/bin/activate

python swe-agent-mini/run_swesmith_bedrock.py \
    data/swesmith/swesmith_sample_1k.jsonl \
    results/swe_smith/qwen3_coder_bedrock \
    configs/qwen3_coder_bedrock.yaml \
    --n-runs 5 \
    --cost-limit 100.0
```

## Configuration Options

### Bash Script Environment Variables

- `N_RUNS`: Number of inference runs per instance (default: 5)
- `COST_LIMIT`: Maximum cost in USD before stopping (default: 100.0)
- `MAX_INSTANCES`: Maximum number of instances to process (default: all)

### Python Script Arguments

```bash
python swe-agent-mini/run_swesmith_bedrock.py \
    <jsonl_path>      # Path to JSONL with instances
    <output_dir>      # Output directory for results
    <config_path>     # Path to config YAML
    --n-runs <int>    # Number of runs per instance (default: 5)
    --cost-limit <float>  # Cost limit in USD (default: 100.0)
    --max-instances <int>  # Maximum number of instances to process (default: all)
```

### Smart Resume Feature

The script automatically **skips instances that already have sufficient trajectories**:
- Checks the output directory for existing trajectory files
- Skips instances with ≥ `n_runs` completed trajectories
- Only processes instances that need more runs
- Perfect for resuming interrupted runs or adding more iterations

## Model Configuration

The configuration file `configs/qwen3_coder_bedrock.yaml` specifies:

```yaml
environment:
  cwd: "/testbed"              # SWE-Smith uses /testbed
  environment_class: docker    # Use Docker (not Singularity)

model:
  model_name: "bedrock/qwen.qwen3-coder-30b-a3b-v1:0"
  model_kwargs:
    temperature: 0.7           # Temperature for generation
    max_tokens: 2048
    aws_region_name: "us-east-1"
```

## Cost Tracking

The system uses Qwen3-Coder-30B pricing:
- **Input tokens**: $0.00022 per 1,000 tokens
- **Output tokens**: $0.0018 per 1,000 tokens

Cost tracking features:
- Real-time cost monitoring
- Automatic stop when exceeding limit
- Per-instance cost reporting
- Total cost summary

## Output Structure

```
results/swe_smith/qwen3_coder_bedrock/
├── cost_summary.json              # Clear cost breakdown per instance
├── preds.json                      # All predictions
├── progress.json                   # Detailed progress tracking
├── minisweagent.log               # Detailed logs
└── <instance_id>/
    ├── <instance_id>_0.traj.json  # Run 0 trajectory
    ├── <instance_id>_1.traj.json  # Run 1 trajectory
    ├── <instance_id>_2.traj.json  # Run 2 trajectory
    ├── <instance_id>_3.traj.json  # Run 3 trajectory
    └── <instance_id>_4.traj.json  # Run 4 trajectory
```

### Cost Summary Format

The `cost_summary.json` file provides a clear, concise cost breakdown:
```json
{
  "total_cost": 1.234567,
  "cost_limit": 100.0,
  "completed_instances": 10,
  "instances": [
    {
      "instance_id": "instance_1",
      "total_cost": 0.123456,
      "num_runs_completed": 5
    },
    {
      "instance_id": "instance_2",
      "total_cost": 0.098765,
      "num_runs_completed": 5
    }
  ]
}
```

**Fields:**
- `total_cost`: Total accumulated cost across all completed instances
- `cost_limit`: Configured cost limit
- `completed_instances`: Number of instances that have been processed
- `instances`: Array of per-instance cost data
  - `instance_id`: Unique identifier for the instance
  - `total_cost`: Total cost for this instance across all runs
  - `num_runs_completed`: Number of inference runs completed for this instance

### Trajectory Format

Each trajectory JSON file contains:
```json
{
  "info": {
    "exit_status": "Submitted",
    "submission": "...",
    "model_stats": {
      "instance_cost": 0.01544195,
      "api_calls": 7
    },
    "mini_version": "1.7.0"
  },
  "messages": [...],  # Full conversation history
  "trajectory_format": "mini-swe-agent-1",
  "instance_id": "instance_id"
}
```

### Progress Tracking

The `progress.json` file tracks:
- Completed instances
- Total cost
- Results for each run
- Stopping status

## Execution Flow

1. **Sequential across instances**: Process one instance at a time
2. **Parallel runs per instance**: For each instance, run N inferences in parallel
3. **Cost checking**: Before each instance, check if under cost limit
4. **Trajectory saving**: Save each trajectory immediately after completion
5. **Progress tracking**: Update progress file after each instance

## Example Usage

### Example 1: Quick Test (3 runs, $10 limit)
```bash
N_RUNS=3 COST_LIMIT=10.0 bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

### Example 2: Full Run (5 runs, $100 limit)
```bash
bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

### Example 3: Extensive Run (10 runs, $500 limit)
```bash
N_RUNS=10 COST_LIMIT=500.0 bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

### Example 4: Limited Instance Run (First 10 instances only)
```bash
MAX_INSTANCES=10 bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

### Example 5: Resume Interrupted Run
```bash
# Simply re-run the same command - already completed instances are automatically skipped
bash scripts/run_qwen3_coder_bedrock_swesmith.sh
```

## Step 4: Evaluate Generated Patches

After inference completes, evaluate the generated patches using the SWE-Bench harness:

### Option A: Using the Bash Script (Recommended)

```bash
# Evaluate with default settings (4 workers, 900s timeout)
bash scripts/evaluate_qwen3_coder_bedrock.sh

# Or customize with environment variables
NUM_WORKERS=8 TIMEOUT=1200 bash scripts/evaluate_qwen3_coder_bedrock.sh
```

### Option B: Using Python Directly

```bash
source venv/bin/activate

python swe-agent-mini/evaluate_swesmith.py \
    results/swe_smith/qwen3_coder_bedrock \
    --dataset-file data/swesmith/swesmith_sample_1k.jsonl \
    --num-workers 4 \
    --timeout 900
```

### Evaluation Features

**Smart Skipping:**
- Automatically detects already-evaluated instances
- Only evaluates new or incomplete instances
- Perfect for resuming interrupted evaluations

**Multi-Run Handling:**
- Automatically selects best prediction from N runs per instance
- Currently uses run_id=0, but extensible for voting strategies

**Progress Tracking:**
- Real-time progress updates
- Clear error reporting
- Detailed evaluation logs

### Evaluation Output

```
results/swe_smith/qwen3_coder_bedrock/
├── evaluation/
│   ├── results.json           # Detailed test results per instance
│   ├── report.json            # Summary metrics (resolve rate, etc.)
│   ├── logs/                  # Evaluation logs per instance
│   └── testbed/               # Temporary test environments
├── evaluation_info.json       # Evaluation metadata
└── temp_eval_preds.json       # Processed predictions for harness
```

### Evaluation Results Format

**results.json:**
```json
{
  "instance_id": {
    "instance_id": "instance_id",
    "status": "resolved",  // "resolved", "partial", "failed"
    "fail_to_pass": {
      "success": ["test1", "test2"],
      "failure": []
    },
    "pass_to_pass": {
      "success": ["test3", "test4"],
      "failure": []
    },
    "test_timeout": false,
    "patch_applied": true
  }
}
```

**report.json (Summary):**
```json
{
  "total": 1092,
  "resolved": 250,
  "partial": 100,
  "failed": 742,
  "resolve_rate": 0.229,  // 22.9%
  "partial_rate": 0.092   // 9.2%
}
```

### Viewing Results

```bash
# Quick summary
python3 -c "import json; r=json.load(open('results/swe_smith/qwen3_coder_bedrock/evaluation/report.json')); print(f'Resolved: {r[\"resolved\"]} / {r[\"total\"]} = {r[\"resolved\"]/r[\"total\"]*100:.1f}%')"

# Detailed analysis
cat results/swe_smith/qwen3_coder_bedrock/evaluation/results.json | jq '.[] | select(.status=="resolved") | .instance_id'
```

## Monitoring

The system provides real-time monitoring:
- Progress bars for each run
- Cost tracking per instance
- Overall progress across instances
- Docker container status

## Troubleshooting

### Issue: AWS Credentials Not Set
**Solution**: Export AWS credentials as shown in Step 2

### Issue: Dataset Not Found
**Solution**: Run the sampling script first (Step 1)

### Issue: Docker Connection Error
**Solution**: Ensure Docker is running: `docker ps`

### Issue: Cost Limit Exceeded
**Solution**: Increase cost limit or reduce number of runs

## Advanced Usage

### Resume from Checkpoint

The system saves progress after each instance. To resume:
1. Check `progress.json` for last completed instance
2. Manually remove completed instances from input JSONL
3. Re-run with adjusted JSONL file

### Custom Sampling

Modify `swe-agent-mini/sample_swesmith.py` to:
- Change number of samples per repository
- Filter specific repositories
- Use different random seed

### Custom Configuration

Edit `configs/qwen3_coder_bedrock.yaml` to:
- Adjust temperature
- Change max_tokens
- Modify agent prompts
- Add custom environment variables

## Notes

- **Parallel execution**: Runs for the same instance execute in parallel, but instances are processed sequentially to manage resources
- **Trajectory completeness**: All trajectories include full conversation history and model statistics
- **Cost safety**: System stops automatically when cost limit is exceeded
- **Data preservation**: All original dataset columns are preserved for evaluation

## Support

For issues or questions:
1. Check `results/swesmith_qwen3_coder_bedrock/minisweagent.log` for detailed logs
2. Review `progress.json` for execution status
3. Verify AWS credentials and Docker status
