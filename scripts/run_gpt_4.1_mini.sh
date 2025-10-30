#!/bin/bash

# Script to test mini-swe-agent with GPT-4.1-mini on first 8 instances
# Uses CMU AI Gateway API

set -e

echo "========================================================================"
echo "Mini-SWE-Agent with GPT-4.1-mini (CMU AI Gateway)"
echo "========================================================================"
echo ""

# Configuration
WORKERS=${WORKERS:-4}  # Use 4 workers for 8 instances
CONFIG="configs/gpt-4.1-mini.yaml"
DATASET_JSONL="data/swebench_pro_sample_100.jsonl"
OUTPUT_DIR="results/swebench_pro_gpt4.1_mini_test"
INSTANCE_SLICE="0:8"  # Only run first 8 instances

# Check for API key
if [ -z "${OPENAI_API_KEY}" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable not set"
    echo ""
    echo "Usage:"
    echo "  export OPENAI_API_KEY='your_api_key'"
    echo "  bash scripts/run_gpt_4.1_mini.sh"
    exit 1
fi

echo "Using GPT-4.1-mini via CMU AI Gateway"
echo "Workers: ${WORKERS}"
echo "Instances: 0-7 (8 total)"
echo ""

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Using existing venv"
else
    echo "ERROR: No venv found. Run setup first:"
    echo "  bash scripts/run.sh"
    exit 1
fi
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Create a temporary JSONL with only first 8 instances
echo "Extracting first 8 instances..."
head -n 8 "${DATASET_JSONL}" > "${OUTPUT_DIR}/test_8_instances.jsonl"
echo "✓ Created ${OUTPUT_DIR}/test_8_instances.jsonl with 8 instances"
echo ""

echo "========================================================================"
echo "Running evaluation on 8 instances with ${WORKERS} workers"
echo "Using Singularity (auto-converts Docker images)"
echo "========================================================================"
echo ""

# Run evaluation directly (bypasses datasets library issues)
python3 swe-agent-mini/prepare_dataset.py \
    "${OUTPUT_DIR}/test_8_instances.jsonl" \
    "${OUTPUT_DIR}" \
    "${CONFIG}" \
    "${WORKERS}"

echo ""
echo "========================================================================"
echo "Complete! Results saved to: ${OUTPUT_DIR}"
echo "========================================================================"
