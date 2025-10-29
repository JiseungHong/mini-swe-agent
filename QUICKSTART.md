# Quick Start Guide - EC2 Setup to Running Evaluation

This is a streamlined guide to go from a fresh EC2 instance to running your first model evaluation in ~30 minutes.

## Prerequisites

- AWS EC2 `g5.4xlarge` instance launched with Ubuntu 22.04
- SSH key to access the instance

---

## Step 1: SSH into EC2 Instance

```bash
# From your local machine
ssh -i your-key.pem ubuntu@<your-ec2-ip>
```

---

## Step 2: Install System Dependencies

Copy and paste this entire block:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker ubuntu

# Install Python and tools
sudo apt install -y python3-pip python3-venv git tmux curl

# Install NVIDIA Container Toolkit (for GPU support in Docker)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Log out and back in for docker group to take effect
exit
```

**Now SSH back in:**
```bash
ssh -i your-key.pem ubuntu@<your-ec2-ip>
```

---

## Step 3: Verify GPU Setup

```bash
# Should show your GPU
nvidia-smi

# Should work without sudo
docker ps
```

---

## Step 4: Clone Repository and Setup Python Environment

```bash
# Clone your repository
git clone https://github.com/<your-username>/mini-swe-agent.git
cd mini-swe-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (this takes 5-10 minutes)
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
- vLLM and dependencies installed
- No errors

---

## Step 5: Test vLLM Installation

Quick sanity check:

```bash
python -c "import vllm; print('vLLM installed:', vllm.__version__)"
python -c "import litellm; print('LiteLLM installed:', litellm.__version__)"
```

---

## Step 6: Start vLLM Server for Qwen3-Coder

Start the model server in tmux (runs in background):

```bash
# Create tmux session
tmux new -s vllm

# Start vLLM server (this downloads model on first run - takes 10-30 min)
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# Press Ctrl+B, then D to detach from tmux
# (Server keeps running in background)
```

**Monitor progress:**
```bash
# Reattach to see logs
tmux attach -t vllm

# Look for this line:
# "INFO:     Application startup complete."

# Detach again: Ctrl+B, then D
```

---

## Step 7: Test Model Inference (Simple Test)

Once the server shows "Application startup complete", test it:

```bash
# Should return model info
curl http://localhost:8000/v1/models

# Simple inference test
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "prompt": "def add(a, b):",
    "max_tokens": 50
  }'
```

**Expected output:**
- JSON response with generated code
- No errors

---

## Step 8: Run SWE-bench Evaluation on All 100 Instances

Now run the full evaluation:

```bash
# Make sure you're in the repo directory
cd ~/mini-swe-agent
source venv/bin/activate

# Run evaluation (takes 3-4 hours)
./scripts/run_qwen3.sh
```

**What happens:**
- Processes all 100 instances
- Uses 8 parallel workers
- Saves results to `results/swe_bench_pro_100/qwen3-coder/`

**Monitor progress:**
```bash
# In another terminal/tmux window
tail -f results/swe_bench_pro_100/qwen3-coder/minisweagent.log

# Count completed instances
ls results/swe_bench_pro_100/qwen3-coder/instance_* | wc -l
```

---

## Step 9: When Qwen3 Finishes, Switch to Devstral

```bash
# Stop vLLM server
tmux kill-session -t vllm

# Start Devstral server
tmux new -s vllm
vllm serve mistralai/Devstral-Small-2507 \
    --port 8001 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
# Ctrl+B, D

# Run evaluation
./scripts/run_devstral.sh
```

---

## Step 10: Finally, Run CWM

```bash
# Stop vLLM server
tmux kill-session -t vllm

# Start CWM server
tmux new -s vllm
vllm serve facebook/cwm \
    --port 8002 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
# Ctrl+B, D

# Run evaluation
./scripts/run_cwm.sh
```

---

## Step 11: Download Results

Once all 3 models complete:

```bash
# From your local machine
scp -i your-key.pem -r ubuntu@<ec2-ip>:~/mini-swe-agent/results/swe_bench_pro_100 .
```

---

## Summary Timeline

| Task | Time | Notes |
|------|------|-------|
| System setup | 10 min | One-time |
| Python/vLLM install | 10 min | One-time |
| Model download (first time) | 15-30 min | Per model |
| Qwen3 evaluation | 3-4 hours | 100 instances |
| Devstral evaluation | 3-4 hours | 100 instances |
| CWM evaluation | 3-4 hours | 100 instances |
| **Total** | **10-13 hours** | **$16-21** |

---

## Quick Reference Commands

```bash
# Check vLLM server status
curl http://localhost:8000/v1/models

# View vLLM logs
tmux attach -t vllm

# Check evaluation progress
tail -f results/swe_bench_pro_100/qwen3-coder/minisweagent.log

# Count completed instances
ls results/swe_bench_pro_100/qwen3-coder/instance_* | wc -l

# List tmux sessions
tmux ls

# Kill tmux session
tmux kill-session -t vllm
```

---

## Troubleshooting

### GPU not detected
```bash
nvidia-smi
# If it fails, instance may not have GPU drivers
```

### vLLM server won't start
```bash
# Check GPU memory
nvidia-smi

# View full error logs
tmux attach -t vllm
```

### Docker permission denied
```bash
# Log out and back in after adding user to docker group
exit
ssh -i your-key.pem ubuntu@<ec2-ip>
```

### Evaluation seems stuck
```bash
# Check if containers are running
docker ps

# Check logs
tail -f results/swe_bench_pro_100/qwen3-coder/minisweagent.log
```

---

## When You're Done

```bash
# From your local machine, download results
scp -i your-key.pem -r ubuntu@<ec2-ip>:~/mini-swe-agent/results/swe_bench_pro_100 .

# Then terminate EC2 instance via AWS Console to stop billing
```

---

## Complete Copy-Paste Workflow

For the impatient, here's everything in order:

```bash
# === ON EC2 (after SSH) ===

# 1. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io python3-pip python3-venv git tmux curl
sudo usermod -aG docker ubuntu

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# 2. Log out and back in
exit
# ssh back in...

# 3. Setup repo
git clone https://github.com/<your-username>/mini-swe-agent.git
cd mini-swe-agent
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Start vLLM server
tmux new -s vllm
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000 --max-model-len 4096 --gpu-memory-utilization 0.9
# Ctrl+B, D

# 5. Wait for "Application startup complete", then run evaluation
./scripts/run_qwen3.sh
```
