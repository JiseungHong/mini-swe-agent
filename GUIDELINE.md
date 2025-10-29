# SWE-bench_Pro Evaluation Guide for AWS EC2

This guide explains how to run the mini-swe-agent evaluation on 100 SWE-bench_Pro instances using three different models: Qwen3-Coder-30B-A3B-Instruct, Devstral-Small-2507, and CWM.

## Table of Contents

1. [AWS EC2 Instance Setup](#aws-ec2-instance-setup)
2. [Model Server Setup](#model-server-setup)
3. [Testing Models](#testing-models)
4. [Running Evaluation](#running-evaluation)
5. [Cost Estimates](#cost-estimates)
6. [Troubleshooting](#troubleshooting)

---

## AWS EC2 Instance Setup

### Recommended Instance Types

**⭐ RECOMMENDED: g5.4xlarge** (Best cost/performance ratio)
- **1x A10G GPU** (24GB VRAM)
- **16 vCPUs, 64GB RAM**
- **Cost: ~$1.62/hour**
- Run models sequentially, process 100 instances with 8 parallel workers
- **Total cost for all 3 models: $15-18**

| Instance | vCPUs | RAM | GPU | Workers | Time/Model | Total Cost |
|----------|-------|-----|-----|---------|------------|------------|
| **g5.4xlarge** ⭐ | 16 | 64GB | 1x A10G | 8 | 3-4h | **$15-18** |
| g5.2xlarge | 8 | 32GB | 1x A10G | 4 | 6-8h | $21-30 |
| g5.12xlarge | 48 | 192GB | 4x A10G | 16 (parallel) | 2-4h | $11-23 |

**Alternative Options:**

**Option 1: g5.4xlarge Sequential (RECOMMENDED)**
- Instance: `g5.4xlarge` (1x A10G GPU, 16 vCPUs, 64GB RAM)
- Cost: ~$1.62/hour
- Run one model at a time, all 100 instances per model
- Fastest sequential option, lowest total cost

**Option 2: g5.12xlarge Parallel (If Speed is Priority)**
- Instance: `g5.12xlarge` (4x A10G GPUs, 48 vCPUs, 192GB RAM)
- Cost: ~$5.67/hour
- Can run all 3 models simultaneously on different GPUs
- Faster but more expensive

**Option 3: g5.2xlarge Budget (If Cost is Critical)**
- Instance: `g5.2xlarge` (1x A10G GPU, 8 vCPUs, 32GB RAM)
- Cost: ~$1.21/hour
- Slower but cheapest per hour (higher total cost due to longer runtime)

### Launch EC2 Instance

1. **Go to EC2 Console** → Launch Instance

2. **Select AMI:**
   - Ubuntu 22.04 LTS (64-bit x86)
   - Or: Deep Learning AMI (Ubuntu 22.04) - comes with CUDA pre-installed

3. **Instance Type:**
   - Choose based on table above (e.g., `g5.12xlarge`)

4. **Storage:**
   - At least **200GB** EBS gp3 volume (models + Docker images are large)

5. **Security Group:**
   - Allow SSH (port 22) from your IP
   - Optionally allow ports 8000-8002 if you want to access model APIs externally

6. **Launch** and save your private key

### Initial Setup on EC2

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@<instance-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker ubuntu
# Log out and back in for docker group to take effect
exit
ssh -i your-key.pem ubuntu@<instance-ip>

# Install Python and dependencies
sudo apt install -y python3-pip python3-venv git

# Verify GPU access
nvidia-smi  # Should show your GPUs

# Install NVIDIA Container Toolkit (for GPU support in Docker)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Clone repository
git clone https://github.com/<your-username>/mini-swe-agent.git
cd mini-swe-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install vllm  # For serving models
```

---

## Model Server Setup

We'll use vLLM to serve the models via OpenAI-compatible API.

### Start Model Servers

**For g5.4xlarge (1 GPU - run models sequentially):**

You'll start one model at a time, run all 100 instances, then switch to the next model.

```bash
# Start Qwen3-Coder
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

**For g5.12xlarge (4 GPUs - run all models in parallel):**

```bash
# Terminal 1: Start Qwen3-Coder on GPU 0
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --port 8000 \
    --max-model-len 4096

# Terminal 2: Start Devstral on GPU 1
CUDA_VISIBLE_DEVICES=1 vllm serve mistralai/Devstral-Small-2507 \
    --port 8001 \
    --max-model-len 4096

# Terminal 3: Start CWM on GPU 2
CUDA_VISIBLE_DEVICES=2 vllm serve facebook/cwm \
    --port 8002 \
    --max-model-len 4096
```

**Tips:**
- Use `tmux` or `screen` to keep servers running in background
- First-time downloads may take 10-30 minutes per model
- Check logs for "Application startup complete" message

**Using tmux (recommended for g5.4xlarge):**

For sequential model execution (run in background with tmux):

```bash
# Install tmux
sudo apt install -y tmux

# Start first model in tmux
tmux new -s vllm
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000 --gpu-memory-utilization 0.9
# Press Ctrl+B, then D to detach

# Check it's running
tmux ls
tmux attach -t vllm  # to view logs

# When switching models, kill and restart:
tmux kill-session -t vllm
tmux new -s vllm
vllm serve mistralai/Devstral-Small-2507 --port 8001 --gpu-memory-utilization 0.9
```

**Using tmux for g5.12xlarge (parallel):**

```bash
# Create sessions for each model
tmux new -s qwen3
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000
# Press Ctrl+B, then D to detach

tmux new -s devstral
CUDA_VISIBLE_DEVICES=1 vllm serve mistralai/Devstral-Small-2507 --port 8001
# Press Ctrl+B, then D to detach

tmux new -s cwm
CUDA_VISIBLE_DEVICES=2 vllm serve facebook/cwm --port 8002
# Press Ctrl+B, then D to detach
```

---

## Testing Models

Before running the full evaluation, test that all models are working:

```bash
cd ~/mini-swe-agent
source venv/bin/activate

# Test all three models
python scripts/test_models.py
```

Expected output:
```
================================================================================
Testing: qwen3-coder
================================================================================
Sending request to openai/qwen3-coder...

✅ SUCCESS - Model responded:
--------------------------------------------------------------------------------
def add_numbers(a, b):
    return a + b
...
```

If any model fails:
1. Check if the vLLM server is running (`tmux ls` and reattach)
2. Check server logs for errors
3. Verify port numbers match config files

---

## Running Evaluation

### Pull Docker Images First (Recommended)

Pre-pull all Docker images to avoid delays during evaluation:

```bash
# Create script to pull all images
python3 -c "
import json
from minisweagent.run.extra.utils.swebench_pro_utils import get_swebench_pro_docker_image

with open('data/swebench_pro_sample_100.jsonl') as f:
    for line in f:
        inst = json.loads(line)
        image = get_swebench_pro_docker_image(inst)
        print(f'docker pull {image}')
" > pull_images.sh

chmod +x pull_images.sh

# Pull all images (this will take a while - run in tmux)
tmux new -s docker-pull
./pull_images.sh
# Press Ctrl+B, then D to detach
```

### Run Evaluation for Each Model

**For g5.4xlarge (Sequential - RECOMMENDED):**

```bash
cd ~/mini-swe-agent
source venv/bin/activate

# Start Qwen3-Coder server in tmux (already running from previous step)

# Run evaluation on all 100 instances (uses 8 workers by default)
python scripts/run_all_100.py --model qwen3-coder

# When complete, stop server and switch models
tmux kill-session -t vllm

# Start Devstral
tmux new -s vllm
vllm serve mistralai/Devstral-Small-2507 --port 8001 --gpu-memory-utilization 0.9
# Ctrl+B, D

# Run Devstral evaluation
python scripts/run_all_100.py --model devstral

# Repeat for CWM
tmux kill-session -t vllm
tmux new -s vllm
vllm serve facebook/cwm --port 8002 --gpu-memory-utilization 0.9
# Ctrl+B, D

python scripts/run_all_100.py --model cwm
```

**For g5.12xlarge (Parallel - all models at once):**

```bash
# All model servers already running on different GPUs

# Terminal 1 (or tmux session)
tmux new -s eval-qwen3
cd ~/mini-swe-agent && source venv/bin/activate
python scripts/run_all_100.py --model qwen3-coder --workers 5
# Ctrl+B, D

# Terminal 2
tmux new -s eval-devstral
cd ~/mini-swe-agent && source venv/bin/activate
python scripts/run_all_100.py --model devstral --workers 5
# Ctrl+B, D

# Terminal 3
tmux new -s eval-cwm
cd ~/mini-swe-agent && source venv/bin/activate
python scripts/run_all_100.py --model cwm --workers 6
# Ctrl+B, D

# Monitor progress
tmux attach -t eval-qwen3  # See progress
```

### Test with Subset First

Before running all 100 instances, test with a small subset:

```bash
# Run on first 5 instances (use fewer workers for testing)
python scripts/run_all_100.py --model qwen3-coder --workers 4 --slice 0:5

# Check results
ls results/swe_bench_pro_100/qwen3-coder/
cat results/swe_bench_pro_100/qwen3-coder/preds.json
```

### Monitoring Progress

```bash
# Watch progress in real-time
tmux attach -t eval-qwen3

# Check logs
tail -f results/swe_bench_pro_100/qwen3-coder/minisweagent.log

# Count completed instances
ls results/swe_bench_pro_100/qwen3-coder/ | grep ".traj.json" | wc -l
```

---

## Cost Estimates

### Compute Costs

**Using g5.4xlarge (RECOMMENDED - Sequential):**
- Instance cost: $1.62/hour
- Estimated time per instance: 3-5 minutes (with step_limit=75, 8 workers)
- 100 instances with 8 workers: ~3-4 hours per model
- Running all 3 models sequentially: 9-12 hours total
- **Total cost: $15-20**

**Using g5.12xlarge (Parallel - Faster):**
- Instance cost: $5.67/hour
- 100 instances with 16 workers total: ~2-4 hours (all 3 models in parallel)
- **Total cost: $11-23**

**Using g5.2xlarge (Budget - Slower):**
- Instance cost: $1.21/hour
- 100 instances with 4 workers: ~6-8 hours per model
- Running all 3 models sequentially: 18-24 hours total
- **Total cost: $22-30**

### Summary

| Instance | Hourly | Runtime | Total Cost |
|----------|--------|---------|------------|
| **g5.4xlarge** ⭐ | $1.62 | 9-12h | **$15-20** |
| g5.12xlarge | $5.67 | 2-4h | $11-23 |
| g5.2xlarge | $1.21 | 18-24h | $22-30 |

### Storage Costs
- 200GB EBS gp3: ~$16/month (~$0.022/hour)
- Negligible for short evaluation runs

### Network Costs
- Minimal (< $1) for model downloads and results upload

### **Total Estimated Cost: $15-25 (g5.4xlarge recommended)**

---

## Results

After evaluation completes, results will be in:

```
results/swe_bench_pro_100/
├── qwen3-coder/
│   ├── preds.json              # Model predictions
│   ├── minisweagent.log        # Execution log
│   ├── exit_statuses.yaml      # Summary of results
│   └── instance_*/             # Per-instance trajectory files
│       └── *.traj.json
├── devstral/
│   └── ...
└── cwm/
    └── ...
```

### Download Results to Local Machine

```bash
# On your local machine
scp -i your-key.pem -r ubuntu@<instance-ip>:~/mini-swe-agent/results/swe_bench_pro_100 .
```

### Analyze Results

```python
import json

# Load predictions
with open('results/swe_bench_pro_100/qwen3-coder/preds.json') as f:
    preds = json.load(f)

print(f"Completed instances: {len(preds)}")

# Load exit statuses
import yaml
with open('results/swe_bench_pro_100/qwen3-coder/exit_statuses.yaml') as f:
    statuses = yaml.safe_load(f)

print(statuses)
```

---

## Troubleshooting

### GPU Out of Memory

If you see OOM errors:

```bash
# Reduce tensor parallel size or max_model_len
CUDA_VISIBLE_DEVICES=0,1 vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --port 8000 \
    --tensor-parallel-size 2 \
    --max-model-len 2048 \
    --dtype float16
```

### Docker Container Fails to Start

```bash
# Check Docker is running
sudo systemctl status docker

# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Verify image was pulled
docker images | grep sweap-images
```

### Model Server Not Responding

```bash
# Check if server is running
curl http://localhost:8000/health

# Check vLLM logs
tmux attach -t qwen3

# Restart server if needed
# Kill the process and restart
```

### Slow Inference

- Reduce `--workers` to 1 or 2
- Increase `--tensor-parallel-size` for larger models
- Use smaller `--max-model-len`

### Resuming After Interruption

The evaluation automatically skips instances that already have results in `preds.json`. Just run the same command again:

```bash
python scripts/run_all_100.py --model qwen3-coder --workers 4
# Will automatically resume from where it left off
```

---

## Cleanup

When evaluation is complete:

```bash
# Stop model servers
tmux kill-session -t qwen3
tmux kill-session -t devstral
tmux kill-session -t cwm

# Download results
scp -i your-key.pem -r ubuntu@<ip>:~/mini-swe-agent/results .

# Terminate EC2 instance via AWS Console
# This stops billing
```

---

## Quick Reference Commands

**For g5.4xlarge (Sequential):**

```bash
# Start model server (one at a time)
tmux new -s vllm
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000 --gpu-memory-utilization 0.9
# Ctrl+B, D to detach

# Test models (update port in test_models.py first)
python scripts/test_models.py

# Run evaluation (uses 8 workers by default)
python scripts/run_all_100.py --model qwen3-coder

# Switch models
tmux kill-session -t vllm
tmux new -s vllm
vllm serve mistralai/Devstral-Small-2507 --port 8001 --gpu-memory-utilization 0.9

python scripts/run_all_100.py --model devstral

# Repeat for CWM...

# Monitor
tail -f results/swe_bench_pro_100/qwen3-coder/minisweagent.log

# Download results
scp -i key.pem -r ubuntu@<ip>:~/mini-swe-agent/results/swe_bench_pro_100 .
```

**For g5.12xlarge (Parallel):**

```bash
# Start all model servers on different GPUs
tmux new -s qwen3 "CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000"
tmux new -s devstral "CUDA_VISIBLE_DEVICES=1 vllm serve mistralai/Devstral-Small-2507 --port 8001"
tmux new -s cwm "CUDA_VISIBLE_DEVICES=2 vllm serve facebook/cwm --port 8002"

# Run evaluations in parallel
python scripts/run_all_100.py --model qwen3-coder --workers 5 &
python scripts/run_all_100.py --model devstral --workers 5 &
python scripts/run_all_100.py --model cwm --workers 6 &
```

---

## Support

For issues:
1. Check logs in `results/*/minisweagent.log`
2. Verify model servers are running (`tmux ls`)
3. Test models individually (`scripts/test_models.py`)
4. Check GitHub issues: https://github.com/anthropics/mini-swe-agent/issues
