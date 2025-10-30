#!/bin/bash

# Single script to setup and run mini-swe-agent on 100 SWE-bench Pro instances
#
# Usage:
#   bash scripts/run.sh                    # Full setup and run
#   SKIP_SETUP=1 bash scripts/run.sh       # Skip venv setup, only run evaluation
#   SKIP_VLLM=1 bash scripts/run.sh        # Skip vLLM start, only run evaluation
#   WORKERS=4 bash scripts/run.sh          # Custom worker count

set -e

echo "========================================================================"
echo "Mini-SWE-Agent Setup and Execution"
echo "========================================================================"
echo ""

# Configuration
WORKERS=${WORKERS:-8}  # Adjust: 4-8 for g5.4xlarge, 16-50 for Babel
CONFIG="configs/qwen2.5_coder_7b.yaml"
DATASET_JSONL="data/swebench_pro_sample_100.jsonl"
OUTPUT_DIR="results/swebench_pro_100_qwen2.5_coder_7b"
VLLM_PORT=8000

# Check Python 3.12 (required for vLLM)
PYTHON_CMD="python3.12"
if ! command -v ${PYTHON_CMD} &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "Using: $(${PYTHON_CMD} --version)"
echo "Workers: ${WORKERS}"
echo ""

# Check if we should skip setup
if [ "${SKIP_SETUP}" = "1" ]; then
    echo "⏭️  Skipping venv setup (SKIP_SETUP=1)"
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✓ Using existing venv"
    else
        echo "ERROR: No venv found. Run without SKIP_SETUP=1 first."
        exit 1
    fi
    echo ""
else
    # Create and activate venv
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        ${PYTHON_CMD} -m venv venv
    fi

    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo ""

    # Install dependencies
    echo "Installing dependencies..."
    pip install --upgrade pip -q
    pip install -e ".[full]" -q
    pip install vllm torch transformers accelerate datasets -q
    echo "✓ Dependencies installed"
    echo ""
fi

# Start vLLM server in background if not running
if [ "${SKIP_VLLM}" = "1" ]; then
    echo "⏭️  Skipping vLLM check (SKIP_VLLM=1)"
    echo "⚠️  Make sure vLLM is running at http://localhost:${VLLM_PORT}"
    echo ""
else
    echo "Checking vLLM server..."
    if ! curl -s http://localhost:${VLLM_PORT}/v1/models > /dev/null 2>&1; then
        echo "Starting vLLM server..."
        nohup vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
            --host 0.0.0.0 \
            --port ${VLLM_PORT} \
            --dtype auto \
            --gpu-memory-utilization 0.9 \
            --max-model-len 32768 \
            > vllm.log 2>&1 &

        echo "Waiting for vLLM to start (this may take 2-5 minutes)..."
        for i in {1..60}; do
            if curl -s http://localhost:${VLLM_PORT}/v1/models > /dev/null 2>&1; then
                echo "✓ vLLM server ready"
                break
            fi
            sleep 5
            echo -n "."
        done
        echo ""
    else
        echo "✓ vLLM server already running"
    fi
    echo ""
fi

# Run evaluation with Singularity
mkdir -p "${OUTPUT_DIR}"

echo "========================================================================"
echo "Running evaluation on 100 instances with ${WORKERS} workers"
echo "Using Singularity (auto-converts Docker images)"
echo "========================================================================"
echo ""

# Run evaluation directly (bypasses datasets library issues)
# Set dummy API key for litellm (vLLM doesn't need authentication)
export OPENAI_API_KEY="dummy-key-for-local-vllm"

python3 swe-agent-mini/prepare_dataset.py \
    "${DATASET_JSONL}" \
    "${OUTPUT_DIR}" \
    "${CONFIG}" \
    "${WORKERS}"

echo ""
echo "========================================================================"
echo "Complete! Results saved to: ${OUTPUT_DIR}"
echo "========================================================================"
