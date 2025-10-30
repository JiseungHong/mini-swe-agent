# Quick Start Guide for CMU Babel (Singularity)

This guide explains how to run mini-swe-agent on 100 SWE-bench Pro instances on CMU Babel using Singularity with 3 different models.

## Prerequisites

- Access to CMU Babel cluster
- Already in a screen or tmux session
- Python 3.12+
- Singularity installed

## Directory Structure

```
mini-swe-agent/
├── configs/
│   ├── qwen3_coder_30b.yaml            # Qwen3-Coder-30B config
│   ├── devstral_small.yaml             # Devstral-Small config
│   ├── facebook_cwm.yaml               # Facebook CWM config
│   ├── qwen2.5_coder_7b.yaml          # Legacy Qwen2.5 config
│   └── litellm_model_registry.json     # Model registry
├── data/
│   └── swebench_pro_sample_100.jsonl   # 100 SWE-bench Pro instances
├── scripts/
│   ├── run.sh                          # Main script (runs 3 models)
│   ├── run_qwen2.5_coder_7b.sh        # Legacy single model script
│   └── install_singularity.sh          # Singularity installation
└── swe-agent-mini/                     # Python utility scripts
```

## Models Available

The script supports 3 models:
1. **Qwen/Qwen3-Coder-30B-A3B-Instruct** - 30B parameter coding model
2. **mistralai/Devstral-Small-2507** - Mistral's coding model
3. **facebook/cwm** - Facebook's Code World Model

## Quick Start

### Run All 3 Models Sequentially

```bash
bash scripts/run.sh
```

### Run a Specific Model

```bash
# Run only Qwen3-Coder-30B
MODEL=qwen3 bash scripts/run.sh

# Run only Devstral-Small
MODEL=devstral bash scripts/run.sh

# Run only Facebook CWM
MODEL=cwm bash scripts/run.sh
```

### Adjust Workers Based on RAM

```bash
# For Babel with 256GB RAM
WORKERS=32 bash scripts/run.sh

# For Babel with 128GB RAM
WORKERS=16 bash scripts/run.sh

# Run specific model with custom workers
MODEL=qwen3 WORKERS=24 bash scripts/run.sh
```

The script will:
- Create Python 3.12 virtual environment
- Install all dependencies (vLLM, torch, transformers, mini-swe-agent)
- Start vLLM server in background for each model
- Run evaluation on 100 instances with Singularity
- Stop and restart vLLM between models (if running multiple)

## Resuming After Failure

If the script fails, you can resume:

```bash
# Skip venv setup (if already done)
SKIP_SETUP=1 bash scripts/run.sh

# Resume specific model
MODEL=devstral SKIP_SETUP=1 bash scripts/run.sh
```

The evaluation **automatically skips completed instances** - just re-run the script.

## Configuration Details

### Model Configurations
All models use the following settings:
- **Max Tokens**: 2048 per response
- **Temperature**: 0.0 (deterministic)
- **Step Limit**: 75 commands per instance
- **Environment**: Singularity containers (auto-converts Docker images)
- **Working Directory**: `/app` (where repository is located)

### Model-Specific Settings

**Qwen3-Coder-30B (`configs/qwen3_coder_30b.yaml`)**
- Model: Qwen/Qwen3-Coder-30B-A3B-Instruct
- Context: 128K tokens
- VRAM: ~60GB

**Devstral-Small (`configs/devstral_small.yaml`)**
- Model: mistralai/Devstral-Small-2507
- Context: 128K tokens
- VRAM: ~40GB

**Facebook CWM (`configs/facebook_cwm.yaml`)**
- Model: facebook/cwm
- Context: 128K tokens
- VRAM: ~50GB

### Execution Settings
- **Dataset**: 100 SWE-bench Pro instances from `data/swebench_pro_sample_100.jsonl`
- **Workers**: 8 by default (adjustable via `WORKERS` environment variable)
  - Recommended: 16-32 workers on Babel (depending on available RAM)
  - Rule of thumb: ~6-8GB RAM per worker
- **Environment**: Singularity (auto-converts Docker images with `docker://` prefix)
- **Docker Images**: Auto-pulled from `jefzda/sweap-images` based on instance
- **No Quantization**: Full model precision (FP16/BF16 auto-selected)

## Output

Results will be saved to separate directories per model:
```
results/swebench_pro_100_qwen3_coder_30b/
results/swebench_pro_100_devstral_small/
results/swebench_pro_100_facebook_cwm/
```

Each directory contains:
- `minisweagent.log` - Main execution log
- `preds.json` - Model predictions
- `[instance_id]/` - Individual instance trajectories and results

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
