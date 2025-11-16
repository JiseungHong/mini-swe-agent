#!/bin/bash

# Script to run mini-swe-agent with Qwen3-Coder-30B on SWE-Smith-True via Amazon Bedrock
# Features:
# - Cost tracking with configurable limit
# - N inferences per instance (parallel per instance, sequential across instances)
# - Proper trajectory saving

set -e

echo "========================================================================"
echo "Mini-SWE-Agent with Qwen3-Coder-30B (Amazon Bedrock) on SWE-Smith-True"
echo "========================================================================"
echo ""

# Configuration
N_RUNS=${N_RUNS:-5}  # Default to 5 runs per instance
COST_LIMIT=${COST_LIMIT:-100.0}  # Default to $100 cost limit
MAX_INSTANCES=${MAX_INSTANCES:-}  # Default to all instances (empty = no limit)
CONFIG="configs/qwen3_coder_bedrock.yaml"
DATASET_JSONL="data/swesmith_true/swesmith_sample_10.jsonl"
OUTPUT_DIR="results/swe_smith_true/qwen3_coder_bedrock"

# Check for AWS credentials
if [ -z "${AWS_ACCESS_KEY_ID}" ]; then
    echo "ERROR: AWS_ACCESS_KEY_ID environment variable not set"
    echo ""
    echo "Usage:"
    echo "  export AWS_ACCESS_KEY_ID='your_access_key'"
    echo "  export AWS_SECRET_ACCESS_KEY='your_secret_key'"
    echo "  export AWS_REGION_NAME='us-east-1'  # Optional, defaults to us-east-1"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith_true.sh"
    exit 1
fi

if [ -z "${AWS_SECRET_ACCESS_KEY}" ]; then
    echo "ERROR: AWS_SECRET_ACCESS_KEY environment variable not set"
    echo ""
    echo "Usage:"
    echo "  export AWS_ACCESS_KEY_ID='your_access_key'"
    echo "  export AWS_SECRET_ACCESS_KEY='your_secret_key'"
    echo "  export AWS_REGION_NAME='us-east-1'  # Optional, defaults to us-east-1"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith_true.sh"
    exit 1
fi

# Set default AWS region if not specified
export AWS_REGION_NAME="${AWS_REGION_NAME:-us-east-1}"

echo "Configuration:"
echo "  - Model: Qwen3-Coder-30B via Amazon Bedrock"
echo "  - Model ID: qwen.qwen3-coder-30b-a3b-v1:0"
echo "  - Region: ${AWS_REGION_NAME}"
echo "  - Runs per instance: ${N_RUNS}"
echo "  - Cost limit: \$${COST_LIMIT}"
if [ -n "${MAX_INSTANCES}" ]; then
    echo "  - Max instances: ${MAX_INSTANCES}"
else
    echo "  - Max instances: all"
fi
echo "  - Dataset: ${DATASET_JSONL}"
echo "  - Output: ${OUTPUT_DIR}"
echo ""

# Check if dataset exists
if [ ! -f "${DATASET_JSONL}" ]; then
    echo "ERROR: Dataset not found at ${DATASET_JSONL}"
    echo ""
    echo "Please ensure the swesmith_true dataset exists."
    exit 1
fi

# Count instances in dataset
INSTANCE_COUNT=$(wc -l < "${DATASET_JSONL}")
echo "Found ${INSTANCE_COUNT} instances in dataset"
echo "Total planned runs: $((INSTANCE_COUNT * N_RUNS))"
echo ""

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Using existing venv"
else
    echo "ERROR: No venv found. Please set up venv first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi
echo ""

# Install boto3 if not already installed (required for Bedrock)
echo "Checking for boto3..."
if ! python -c "import boto3" 2>/dev/null; then
    echo "Installing boto3 for Amazon Bedrock..."
    pip install boto3
    echo "✓ boto3 installed"
else
    echo "✓ boto3 already installed"
fi
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "========================================================================"
echo "Starting evaluation"
echo "========================================================================"
echo ""

# Run evaluation
if [ -n "${MAX_INSTANCES}" ]; then
    python3 swe-agent-mini/run_swesmith_true_bedrock.py \
        "${DATASET_JSONL}" \
        "${OUTPUT_DIR}" \
        "${CONFIG}" \
        --n-runs "${N_RUNS}" \
        --cost-limit "${COST_LIMIT}" \
        --max-instances "${MAX_INSTANCES}"
else
    python3 swe-agent-mini/run_swesmith_true_bedrock.py \
        "${DATASET_JSONL}" \
        "${OUTPUT_DIR}" \
        "${CONFIG}" \
        --n-runs "${N_RUNS}" \
        --cost-limit "${COST_LIMIT}"
fi

echo ""
echo "========================================================================"
echo "Complete! Results saved to: ${OUTPUT_DIR}"
echo "========================================================================"
echo ""
echo "Output files:"
echo "  - ${OUTPUT_DIR}/cost_summary.json   # Clear cost breakdown per instance"
echo "  - ${OUTPUT_DIR}/preds.json          # All predictions"
echo "  - ${OUTPUT_DIR}/progress.json       # Detailed progress tracking"
echo "  - ${OUTPUT_DIR}/<instance_id>/      # Individual trajectories"
echo "  - ${OUTPUT_DIR}/minisweagent.log    # Detailed logs"
