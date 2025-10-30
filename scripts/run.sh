#!/bin/bash

# Script to run mini-swe-agent on 100 SWE-bench Pro instances with 3 models sequentially
# Models: Qwen3-Coder-30B-A3B, Devstral-Small-2507, facebook/cwm
#
# Usage:
#   bash scripts/run.sh                    # Full setup and run all 3 models
#   SKIP_SETUP=1 bash scripts/run.sh       # Skip venv setup
#   WORKERS=4 bash scripts/run.sh          # Custom worker count
#   MODEL=qwen3 bash scripts/run.sh        # Run only qwen3 model
#   MODEL=devstral bash scripts/run.sh     # Run only devstral model
#   MODEL=cwm bash scripts/run.sh          # Run only facebook/cwm model

set -e

echo "========================================================================"
echo "Mini-SWE-Agent - Sequential 3-Model Execution"
echo "========================================================================"
echo ""

# Configuration
WORKERS=${WORKERS:-8}  # Adjust: 4-8 for g5.4xlarge, 16-50 for Babel
DATASET_JSONL="data/swebench_pro_sample_100.jsonl"
VLLM_PORT=8000

# Define the 3 models to run sequentially
ALL_MODELS=(
    "Qwen/Qwen3-Coder-30B-A3B-Instruct"
    "mistralai/Devstral-Small-2507"
    "facebook/cwm"
)

ALL_CONFIGS=(
    "configs/qwen3_coder_30b.yaml"
    "configs/devstral_small.yaml"
    "configs/facebook_cwm.yaml"
)

ALL_OUTPUT_DIRS=(
    "results/swebench_pro_100_qwen3_coder_30b"
    "results/swebench_pro_100_devstral_small"
    "results/swebench_pro_100_facebook_cwm"
)

# Select which models to run based on MODEL env variable
if [ -n "${MODEL}" ]; then
    case "${MODEL}" in
        qwen3)
            MODELS=("${ALL_MODELS[0]}")
            CONFIGS=("${ALL_CONFIGS[0]}")
            OUTPUT_DIRS=("${ALL_OUTPUT_DIRS[0]}")
            ;;
        devstral)
            MODELS=("${ALL_MODELS[1]}")
            CONFIGS=("${ALL_CONFIGS[1]}")
            OUTPUT_DIRS=("${ALL_OUTPUT_DIRS[1]}")
            ;;
        cwm)
            MODELS=("${ALL_MODELS[2]}")
            CONFIGS=("${ALL_CONFIGS[2]}")
            OUTPUT_DIRS=("${ALL_OUTPUT_DIRS[2]}")
            ;;
        *)
            echo "ERROR: Unknown model '${MODEL}'"
            echo "Valid options: qwen3, devstral, cwm"
            exit 1
            ;;
    esac
else
    # Run all models
    MODELS=("${ALL_MODELS[@]}")
    CONFIGS=("${ALL_CONFIGS[@]}")
    OUTPUT_DIRS=("${ALL_OUTPUT_DIRS[@]}")
fi

# Check Python 3.12 (required for vLLM)
PYTHON_CMD="python3.12"
if ! command -v ${PYTHON_CMD} &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "Using: $(${PYTHON_CMD} --version)"
echo "Workers: ${WORKERS}"
echo "Models to run: ${#MODELS[@]}"
for model in "${MODELS[@]}"; do
    echo "  - $model"
done
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

# Set dummy API key for litellm (vLLM doesn't need authentication)
export OPENAI_API_KEY="dummy-key-for-local-vllm"

# Function to stop vLLM server
stop_vllm() {
    echo "Stopping vLLM server..."
    pkill -f "vllm serve" || true
    sleep 5
    echo "✓ vLLM server stopped"
}

# Function to check if vLLM is running with the correct model
check_vllm_model() {
    local expected_model=$1
    if ! curl -s http://localhost:${VLLM_PORT}/v1/models > /dev/null 2>&1; then
        return 1  # vLLM not running
    fi

    # Get current model from vLLM API
    local current_model=$(curl -s http://localhost:${VLLM_PORT}/v1/models | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', [{}])[0].get('id', ''))" 2>/dev/null)

    if [ "$current_model" = "$expected_model" ]; then
        return 0  # Correct model running
    else
        return 1  # Different model or error
    fi
}

# Function to start vLLM server with a specific model
start_vllm() {
    local model=$1
    local max_model_len=$2

    # Check if vLLM is already running with this model
    if check_vllm_model "$model"; then
        echo "✓ vLLM server already running with $model"
        return 0
    fi

    echo "Starting vLLM server with $model..."
    nohup vllm serve "$model" \
        --host 0.0.0.0 \
        --port ${VLLM_PORT} \
        --dtype auto \
        --gpu-memory-utilization 0.9 \
        --max-model-len ${max_model_len} \
        > vllm_${model//\//_}.log 2>&1 &

    echo "Waiting for vLLM to start (this may take 2-5 minutes)..."
    for i in {1..60}; do
        if curl -s http://localhost:${VLLM_PORT}/v1/models > /dev/null 2>&1; then
            echo "✓ vLLM server ready with $model"
            return 0
        fi
        sleep 5
        echo -n "."
    done
    echo ""
    echo "ERROR: vLLM failed to start"
    return 1
}

# Loop through each model and run evaluation
for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    CONFIG="${CONFIGS[$i]}"
    OUTPUT_DIR="${OUTPUT_DIRS[$i]}"

    echo ""
    echo "========================================================================"
    echo "Model $((i+1))/${#MODELS[@]}: $MODEL"
    echo "========================================================================"
    echo ""

    # Determine max_model_len based on model
    case "$MODEL" in
        "Qwen/Qwen3-Coder-30B-A3B-Instruct")
            MAX_MODEL_LEN=128000
            ;;
        "mistralai/Devstral-Small-2507")
            MAX_MODEL_LEN=128000
            ;;
        "facebook/cwm")
            MAX_MODEL_LEN=128000
            ;;
        *)
            MAX_MODEL_LEN=32768
            ;;
    esac

    # Stop any existing vLLM server
    if [ $i -gt 0 ]; then
        stop_vllm
    fi

    # Start vLLM with the current model
    start_vllm "$MODEL" "$MAX_MODEL_LEN"

    # Create output directory
    mkdir -p "${OUTPUT_DIR}"

    echo ""
    echo "Running evaluation on 100 instances with ${WORKERS} workers"
    echo "Using Singularity (auto-converts Docker images)"
    echo ""

    # Run evaluation
    python3 swe-agent-mini/prepare_dataset.py \
        "${DATASET_JSONL}" \
        "${OUTPUT_DIR}" \
        "${CONFIG}" \
        "${WORKERS}"

    echo ""
    echo "✓ Model $((i+1))/${#MODELS[@]} complete! Results saved to: ${OUTPUT_DIR}"
    echo ""
done

# Stop vLLM server after all models are done
stop_vllm

echo ""
echo "========================================================================"
echo "All 3 models complete!"
echo "========================================================================"
echo ""
echo "Results saved to:"
for output_dir in "${OUTPUT_DIRS[@]}"; do
    echo "  - $output_dir"
done
echo ""
