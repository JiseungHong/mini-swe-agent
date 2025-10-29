#!/bin/bash

# Script to run 1 SWE-bench Pro instance as a test with gpt-4.1-mini
# Usage: OPENAI_API_KEY=your_key ./scripts/run_swebench_pro_test.sh

set -e

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable not set"
    echo "Usage: OPENAI_API_KEY='your_key' $0"
    exit 1
fi

# Configuration
DATASET_PATH="data/swebench_pro_sample_100.jsonl"
OUTPUT_DIR="results/swe_bench_pro_100/gpt-4.1-mini"
CONFIG_PATH="configs/swebench_pro_gpt4mini.yaml"
MODEL_NAME="gpt-4.1-mini"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "================================================================================"
echo "Running SWE-bench Pro Test Instance"
echo "================================================================================"
echo "Dataset: $DATASET_PATH"
echo "Output:  $OUTPUT_DIR"
echo "Config:  $CONFIG_PATH"
echo "Model:   $MODEL_NAME"
echo "================================================================================"
echo ""

# Run mini-swe-agent with swebench module
# Using python -m to run the swebench module directly
# Note: For local JSONL files, HuggingFace datasets loads them as "train" split by default
python -m minisweagent.run.extra.swebench \
    --subset "json" \
    --split "train" \
    --slice "0:1" \
    --output "$OUTPUT_DIR" \
    --config "$CONFIG_PATH" \
    --model "$MODEL_NAME" \
    --model-class "litellm_model"

echo ""
echo "================================================================================"
echo "Test run completed!"
echo "================================================================================"
echo "Check results in: $OUTPUT_DIR"
