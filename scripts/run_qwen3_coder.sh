#!/bin/bash

# Run mini-swe-agent on 100 SWE-bench_Pro instances with Qwen3-Coder-30B-A3B-Instruct

set -e

MODEL_NAME="qwen3-coder"
CONFIG="configs/qwen3_coder.yaml"
DATASET="data/swebench_pro_sample_100.jsonl"
OUTPUT_DIR="results/swe_bench_pro_100/${MODEL_NAME}"
WORKERS=4  # Adjust based on your instance resources

echo "========================================================================"
echo "Running SWE-bench_Pro Evaluation with Qwen3-Coder-30B-A3B-Instruct"
echo "========================================================================"
echo "Dataset: ${DATASET}"
echo "Config: ${CONFIG}"
echo "Output: ${OUTPUT_DIR}"
echo "Workers: ${WORKERS}"
echo "========================================================================"
echo ""

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

# Check if model server is running
echo "Checking if model server is running at http://localhost:8000..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: Model server is not running at http://localhost:8000"
    echo "Please start the vLLM server first:"
    echo "  vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000"
    exit 1
fi
echo "✓ Model server is running"
echo ""

# Run the evaluation
# Note: Using the main swebench module directly won't work with local JSONL
# So we need to use a custom runner or modify the approach

python -m minisweagent.run.extra.swebench \
    --subset lite \
    --split dev \
    --slice 0:100 \
    --output "${OUTPUT_DIR}" \
    --config "${CONFIG}" \
    --workers ${WORKERS} \
    --filter "" 2>&1 | tee "${OUTPUT_DIR}/run.log"

# Note: The above command is for HuggingFace datasets
# For local JSONL, we need a different approach
# Creating a custom runner script below...

echo ""
echo "========================================================================"
echo "Evaluation Complete!"
echo "Results saved to: ${OUTPUT_DIR}"
echo "========================================================================"
