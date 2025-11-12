#!/bin/bash

# Script to evaluate SWE-Smith predictions using SWE-Bench harness
# Automatically skips already evaluated instances

set -e

echo "========================================================================"
echo "SWE-Smith Evaluation with SWE-Bench Harness"
echo "========================================================================"
echo ""

# Configuration
NUM_WORKERS=${NUM_WORKERS:-4}  # Default to 4 workers
TIMEOUT=${TIMEOUT:-900}  # Default to 900 seconds (15 min) per instance
RESULTS_DIR="results/swe_smith/qwen3_coder_bedrock"
DATASET_FILE="data/swesmith/swesmith_sample_1k.jsonl"

echo "Configuration:"
echo "  - Results directory: ${RESULTS_DIR}"
echo "  - Dataset file: ${DATASET_FILE}"
echo "  - Workers: ${NUM_WORKERS}"
echo "  - Timeout: ${TIMEOUT}s per instance"
echo ""

# Check if results directory exists
if [ ! -d "${RESULTS_DIR}" ]; then
    echo "ERROR: Results directory not found: ${RESULTS_DIR}"
    echo ""
    echo "Please run inference first:"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith.sh"
    exit 1
fi

# Check if preds.json exists
if [ ! -f "${RESULTS_DIR}/preds.json" ]; then
    echo "ERROR: preds.json not found in ${RESULTS_DIR}"
    echo ""
    echo "Please run inference first:"
    echo "  bash scripts/run_qwen3_coder_bedrock_swesmith.sh"
    exit 1
fi

# Count predictions
PRED_COUNT=$(python3 -c "import json; print(len(json.load(open('${RESULTS_DIR}/preds.json'))))")
echo "Found ${PRED_COUNT} predictions to evaluate"
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

# Check if SWE-Bench is installed
echo "Checking for SWE-Bench harness..."
if ! python3 -c "import swebench" 2>/dev/null; then
    echo "SWE-Bench not found. Installing..."
    pip install swebench
    echo "✓ SWE-Bench installed"
else
    echo "✓ SWE-Bench already installed"
fi
echo ""

echo "========================================================================"
echo "Starting Evaluation"
echo "========================================================================"
echo ""

# Run evaluation
python3 swe-agent-mini/evaluate_swesmith.py \
    "${RESULTS_DIR}" \
    --dataset-file "${DATASET_FILE}" \
    --num-workers "${NUM_WORKERS}" \
    --timeout "${TIMEOUT}"

echo ""
echo "========================================================================"
echo "Evaluation Complete!"
echo "========================================================================"
echo ""
echo "Results saved to: ${RESULTS_DIR}/evaluation/"
echo ""
echo "Key files:"
echo "  - ${RESULTS_DIR}/evaluation/results.json        # Detailed test results"
echo "  - ${RESULTS_DIR}/evaluation/report.json         # Summary metrics"
echo "  - ${RESULTS_DIR}/evaluation_info.json           # Evaluation metadata"
echo ""
echo "To view results:"
echo "  python3 -c \"import json; r=json.load(open('${RESULTS_DIR}/evaluation/report.json')); print(f'Resolved: {r.get(\\\"resolved\\\", 0)} / {r.get(\\\"total\\\", 0)} = {r.get(\\\"resolved\\\", 0)/r.get(\\\"total\\\", 1)*100:.1f}%')\""
