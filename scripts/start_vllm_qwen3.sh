#!/bin/bash

# Start vLLM server for Qwen3-Coder-30B-A3B-Instruct

echo "========================================================================"
echo "Starting vLLM Server - Qwen3-Coder-30B-A3B-Instruct"
echo "========================================================================"
echo ""
echo "Model will be served at: http://localhost:8000"
echo "This may take 10-30 minutes for first-time model download"
echo ""
echo "To run in background with tmux:"
echo "  tmux new -s vllm"
echo "  ./scripts/start_vllm_qwen3.sh"
echo "  # Press Ctrl+B, then D to detach"
echo ""
echo "========================================================================"
echo ""

vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --dtype auto
