# Quick Start Guide for CMU Babel (Singularity)

This guide explains how to run mini-swe-agent with Qwen/Qwen2.5-Coder-7B-Instruct on 100 SWE-bench Pro instances on CMU Babel using Singularity.

## Prerequisites

- Access to CMU Babel cluster
- Already in a screen or tmux session
- Python 3.10+

## Directory Structure

```
mini-swe-agent/
├── configs/
│   ├── qwen2.5_coder_7b.yaml          # Model configuration
│   └── litellm_model_registry.json     # Model registry (updated)
├── data/
│   └── swebench_pro_sample_100.jsonl   # 100 SWE-bench Pro instances
├── scripts/
│   ├── setup_and_run.sh                # Setup venv and run
│   └── run_model.sh                    # Run model on dataset
└── swe-agent-mini/                     # Python utility scripts
```

## Quick Start

**Single command to run everything:**
```bash
bash scripts/run.sh
```

Or adjust workers based on available RAM:
```bash
WORKERS=32 bash scripts/run.sh
```

This script will:
- Create Python 3.12 virtual environment
- Install all dependencies (vLLM, torch, transformers, mini-swe-agent)
- Start vLLM server in background
- Run evaluation on 100 instances with Singularity

## Adjusting Worker Count

```bash
# Recommended for Babel (128GB+ RAM): 16-50 workers
WORKERS=32 bash scripts/run.sh

# For systems with less RAM
WORKERS=16 bash scripts/run.sh
```

## Resuming After Failure

If the script fails, you can resume:

```bash
# Skip venv setup (if already done)
SKIP_SETUP=1 bash scripts/run.sh

# Skip venv + vLLM check (if vLLM already running)
SKIP_SETUP=1 SKIP_VLLM=1 bash scripts/run.sh
```

The evaluation **automatically skips completed instances** - just re-run the script.

## Configuration Details

### Model Configuration (`configs/qwen2.5_coder_7b.yaml`)
- **Model**: Qwen/Qwen2.5-Coder-7B-Instruct
- **Max Tokens**: 32,768
- **Temperature**: 0.0
- **Step Limit**: 75 commands per instance
- **Environment**: Docker containers (via Singularity)

### Execution Settings
- **Dataset**: 100 SWE-bench Pro instances from `data/swebench_pro_sample_100.jsonl`
- **Workers**: 8 by default (adjustable via `WORKERS` environment variable)
  - Recommended: 16-50 workers on Babel (depending on available RAM)
  - Rule of thumb: ~6-8GB RAM per worker
- **Environment**: Singularity (auto-detected)
- **Docker Images**: Auto-pulled from `jefzda/sweap-images` and converted by Singularity
- **No Quantization**: Full model precision

## Output

Results will be saved to:
```
results/swebench_pro_100_qwen2.5_coder_7b/
```

The run log will be saved to:
```
results/swebench_pro_100_qwen2.5_coder_7b/run.log
```

## Notes

- The model will be downloaded from HuggingFace on first run
- Docker images for each instance will be pulled automatically
- Singularity will handle Docker image conversion
- All 100 instances will run in parallel (adjust `WORKERS` in `scripts/run_model.sh` if needed)
- Each instance has a 60-second timeout per command
- The model runs without quantization (full precision)

## Troubleshooting

If you encounter issues:

1. **Out of Memory**: Reduce `WORKERS` in `scripts/run_model.sh`
2. **Docker/Singularity Issues**: Check Babel's Singularity documentation
3. **Model Download Fails**: Check HuggingFace access and network
4. **Dataset Not Found**: Verify `data/swebench_pro_sample_100.jsonl` exists

## Monitoring Progress

To monitor the run:
```bash
tail -f results/swebench_pro_100_qwen2.5_coder_7b/run.log
```
