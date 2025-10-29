#!/bin/bash

# Run evaluation with CWM on all 100 instances

set -e

echo "========================================================================"
echo "SWE-bench_Pro Evaluation - CWM (Code Wrangler Model)"
echo "========================================================================"
echo ""

# Check if vLLM server is running
echo "Checking if vLLM server is running at http://localhost:8002..."
if ! curl -s http://localhost:8002/v1/models > /dev/null 2>&1; then
    echo "❌ ERROR: vLLM server is not running at http://localhost:8002"
    echo ""
    echo "Please start the vLLM server first:"
    echo "  tmux new -s vllm"
    echo "  vllm serve facebook/cwm --port 8002 --gpu-memory-utilization 0.9"
    echo "  # Press Ctrl+B, then D to detach"
    echo ""
    exit 1
fi
echo "✓ vLLM server is running"
echo ""

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run evaluation
echo "Starting evaluation with 8 workers..."
echo ""

python scripts/run_all_100.py \
    --model cwm \
    --workers 8

echo ""
echo "========================================================================"
echo "✓ CWM evaluation complete!"
echo "Results saved to: results/swe_bench_pro_100/cwm/"
echo "========================================================================"
