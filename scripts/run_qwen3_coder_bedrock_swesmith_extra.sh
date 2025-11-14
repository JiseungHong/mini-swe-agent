#!/bin/bash

# Script to run mini-swe-agent with Qwen3-Coder on SWE-Smith via Amazon Bedrock (EXTRA SERVER)
# This script starts from row 800 by default (for parallel execution on another server)
# Features:
# - Starts from configurable row number (default: 800)
# - Cost tracking with configurable limit
# - N inferences per instance (parallel per instance, sequential across instances)
# - Proper trajectory saving
# - Robust skip mechanism based on instance_id

set -e

echo "========================================================================"
echo "Mini-SWE-Agent with Qwen3-Coder (Amazon Bedrock) - EXTRA SERVER"
echo "========================================================================"
echo ""

# Configuration
N_RUNS=${N_RUNS:-5}  # Default to 5 runs per instance
COST_LIMIT=${COST_LIMIT:-100.0}  # Default to $100 cost limit
MAX_INSTANCES=${MAX_INSTANCES:-}  # Default to all instances (empty = no limit)
START_ROW=${START_ROW:-800}  # Default to row 800 (for extra server)
CONFIG="configs/qwen3_coder_bedrock.yaml"
DATASET_JSONL="data/swesmith/swesmith_sample_1k.jsonl"
OUTPUT_DIR="results/swe_smith/qwen3_coder_bedrock"

# Check for AWS credentials
if [ -z "${AWS_ACCESS_KEY_ID}" ]; then
    echo "ERROR: AWS_ACCESS_KEY_ID environment variable not set"
    echo ""
    echo "Usage:"
    echo "  export AWS_ACCESS_KEY_ID='your_access_key'"
    echo "  export AWS_SECRET_ACCESS_KEY='your_secret_key'"
    echo "  export AWS_REGION_NAME='us-east-1'  # Optional, defaults to us-east-1"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith.sh"
    exit 1
fi

if [ -z "${AWS_SECRET_ACCESS_KEY}" ]; then
    echo "ERROR: AWS_SECRET_ACCESS_KEY environment variable not set"
    echo ""
    echo "Usage:"
    echo "  export AWS_ACCESS_KEY_ID='your_access_key'"
    echo "  export AWS_SECRET_ACCESS_KEY='your_secret_key'"
    echo "  export AWS_REGION_NAME='us-east-1'  # Optional, defaults to us-east-1"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith.sh"
    exit 1
fi

# Set default AWS region if not specified
export AWS_REGION_NAME="${AWS_REGION_NAME:-us-east-1}"

echo "Configuration:"
echo "  - Model: Qwen3-Coder-480B via Amazon Bedrock"
echo "  - Model ID: qwen.qwen3-coder-480b-a35b-v1:0"
echo "  - Region: ${AWS_REGION_NAME}"
echo "  - Runs per instance: ${N_RUNS}"
echo "  - Cost limit: \$${COST_LIMIT}"
echo "  - Start from row: ${START_ROW}"
if [ -n "${MAX_INSTANCES}" ]; then
    echo "  - Max instances: ${MAX_INSTANCES}"
else
    echo "  - Max instances: all (from row ${START_ROW})"
fi
echo "  - Dataset: ${DATASET_JSONL}"
echo "  - Output: ${OUTPUT_DIR}"
echo ""

# Check if dataset exists
if [ ! -f "${DATASET_JSONL}" ]; then
    echo "ERROR: Dataset not found at ${DATASET_JSONL}"
    echo ""
    echo "Please run the sampling script first:"
    echo "  source venv/bin/activate"
    echo "  python swe-agent-mini/sample_swesmith.py"
    exit 1
fi

# Count instances in dataset
INSTANCE_COUNT=$(wc -l < "${DATASET_JSONL}")
INSTANCES_TO_PROCESS=$((INSTANCE_COUNT - START_ROW + 1))
echo "Found ${INSTANCE_COUNT} instances in dataset"
echo "Starting from row ${START_ROW}, will process ${INSTANCES_TO_PROCESS} instances"
echo "Total planned runs: $((INSTANCES_TO_PROCESS * N_RUNS))"
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
    python3 swe-agent-mini/run_swesmith_bedrock_extra.py \
        "${DATASET_JSONL}" \
        "${OUTPUT_DIR}" \
        "${CONFIG}" \
        --n-runs "${N_RUNS}" \
        --cost-limit "${COST_LIMIT}" \
        --max-instances "${MAX_INSTANCES}" \
        --start-row "${START_ROW}"
else
    python3 swe-agent-mini/run_swesmith_bedrock_extra.py \
        "${DATASET_JSONL}" \
        "${OUTPUT_DIR}" \
        "${CONFIG}" \
        --n-runs "${N_RUNS}" \
        --cost-limit "${COST_LIMIT}" \
        --start-row "${START_ROW}"
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
