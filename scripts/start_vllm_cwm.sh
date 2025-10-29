#!/bin/bash

# Start vLLM server for CWM

echo "========================================================================"
echo "Starting vLLM Server - CWM (Code Wrangler Model)"
echo "========================================================================"
echo ""
echo "Model will be served at: http://localhost:8002"
echo "This may take 10-30 minutes for first-time model download"
echo ""
echo "To run in background with tmux:"
echo "  tmux new -s vllm"
echo "  ./scripts/start_vllm_cwm.sh"
echo "  # Press Ctrl+B, then D to detach"
echo ""
echo "========================================================================"
echo ""

vllm serve facebook/cwm \
    --port 8002 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --dtype auto
