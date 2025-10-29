#!/bin/bash

# Start vLLM server for Devstral-Small-2507

echo "========================================================================"
echo "Starting vLLM Server - Devstral-Small-2507"
echo "========================================================================"
echo ""
echo "Model will be served at: http://localhost:8001"
echo "This may take 10-30 minutes for first-time model download"
echo ""
echo "To run in background with tmux:"
echo "  tmux new -s vllm"
echo "  ./scripts/start_vllm_devstral.sh"
echo "  # Press Ctrl+B, then D to detach"
echo ""
echo "========================================================================"
echo ""

vllm serve mistralai/Devstral-Small-2507 \
    --port 8001 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --dtype auto
