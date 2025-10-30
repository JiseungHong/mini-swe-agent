# Quick Start Guide for AWS EC2 g5.4xlarge

This guide explains how to run mini-swe-agent with Qwen/Qwen2.5-Coder-7B-Instruct on 100 SWE-bench Pro instances on AWS EC2 g5.4xlarge.

## Instance Specifications

**g5.4xlarge:**
- 16 vCPUs
- 64GB RAM
- 1x NVIDIA A10G GPU (24GB VRAM)
- 600GB NVMe SSD

## Recommended Configuration

### OS: Ubuntu 22.04 LTS

**Why Ubuntu?**
- Better Singularity support than Amazon Linux
- Easier PyTorch/CUDA installation
- Most mini-swe-agent testing done on Ubuntu
- Better ML/AI ecosystem support

### Worker Count: 4-8 (NOT 100)

**Memory per worker:** ~6-8GB RAM
- **Safe (recommended): 4 workers** → ~24-32GB RAM (50% utilization)
- **Moderate: 8 workers** → ~48-64GB RAM (75-100% utilization)
- **Maximum: 10 workers** → Risk of OOM (Out of Memory)

**Why not 100 workers?**
- 100 × 6GB = 600GB RAM required (you only have 64GB)
- Disk I/O bottleneck with parallel Singularity containers
- Model inference is GPU-bound (sequential on single GPU)

## Setup Instructions

### 1. Launch EC2 Instance

```bash
# AMI: Ubuntu 22.04 LTS (ami-0c7217cdde317cfec or latest)
# Instance Type: g5.4xlarge
# Storage: 200GB+ EBS GP3 (for Docker images + results)
```

### 2. Install Singularity and System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install NVIDIA drivers
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers install

# Install Singularity dependencies
sudo apt install -y \
    build-essential \
    libseccomp-dev \
    pkg-config \
    squashfs-tools \
    cryptsetup \
    wget

# Install Go (required for Singularity)
export VERSION=1.21.5 OS=linux ARCH=amd64
wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz
sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz
rm go$VERSION.$OS-$ARCH.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install SingularityCE
export VERSION=4.1.0
wget https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-ce-${VERSION}.tar.gz
tar -xzf singularity-ce-${VERSION}.tar.gz
cd singularity-ce-${VERSION}
./mconfig
make -C builddir
sudo make -C builddir install
cd ..
rm -rf singularity-ce-${VERSION}*

# Verify installations
nvidia-smi
singularity --version

# Reboot (required for driver changes)
sudo reboot
```

### 3. Run Mini-SWE-Agent

```bash
# Start screen/tmux session (recommended)
screen -S mini-swe-agent
# or
tmux new -s mini-swe-agent

# Clone repository (if not already done)
cd ~/
git clone https://github.com/your-repo/mini-swe-agent.git
cd mini-swe-agent

# Run with default 8 workers
bash scripts/run.sh

# Or customize worker count (4 recommended for g5.4xlarge)
WORKERS=4 bash scripts/run.sh
```

## Customizing Worker Count

```bash
# For 4 workers (safer, recommended for g5.4xlarge)
WORKERS=4 bash scripts/run.sh

# For 8 workers (moderate)
WORKERS=8 bash scripts/run.sh

# For 10 workers (maximum, risky)
WORKERS=10 bash scripts/run.sh
```

## Monitoring

### Check GPU Usage
```bash
watch -n 1 nvidia-smi
```

### Check Memory Usage
```bash
watch -n 1 free -h
```

### Check Singularity Processes
```bash
watch -n 1 'ps aux | grep singularity'
```

### Monitor Progress
```bash
tail -f results/swebench_pro_100_qwen2.5_coder_7b/run.log
```

### Monitor vLLM Server
```bash
tail -f vllm.log
```

## Expected Runtime

**With 8 workers:**
- 100 instances ÷ 8 workers = ~13 batches
- ~15-30 minutes per instance (depends on complexity)
- **Total: 3-6 hours** (approximately)

**With 4 workers:**
- 100 instances ÷ 4 workers = 25 batches
- **Total: 6-12 hours** (approximately)

## Cost Estimation

**g5.4xlarge pricing (us-east-1):**
- On-Demand: ~$1.62/hour
- Spot: ~$0.50-0.80/hour (70% savings)

**Estimated cost for 100 instances:**
- 6 hours × $1.62 = ~$10 (On-Demand)
- 6 hours × $0.60 = ~$4 (Spot)

**Recommendation:** Use Spot instances to save costs!

## Troubleshooting

### Out of Memory (OOM)
```bash
# Reduce workers
WORKERS=4 bash scripts/run_model.sh

# Check memory usage
free -h
docker stats
```

### GPU Out of Memory
```bash
# Model should fit in 24GB VRAM
# If OOM, check for memory leaks
nvidia-smi

# Restart containers
docker system prune -f
```

### Slow Performance
```bash
# Check disk I/O
iostat -x 1

# Use instance store if available (g5.4xlarge has 600GB NVMe)
# Mount instance store to /var/lib/docker for better Docker performance
```

### Docker Pull Rate Limit
```bash
# Login to Docker Hub
docker login

# Or use authenticated pulls in config
```

## File Structure After Run

```
mini-swe-agent/
├── results/
│   └── swebench_pro_100_qwen2.5_coder_7b/
│       ├── run.log              # Main log file
│       ├── predictions.jsonl    # Model predictions
│       └── [instance_results]/  # Individual instance results
```

## Comparison: g5.4xlarge vs CMU Babel

| Feature | g5.4xlarge | CMU Babel |
|---------|------------|-----------|
| RAM | 64GB | Varies (likely 128GB-512GB) |
| Workers | 4-8 | 16-100 |
| GPU | 1x A10G (24GB) | Varies |
| Runtime (100 inst.) | 6-12 hours | 2-6 hours |
| Cost | $10 (6hr On-Demand) | Free |

## Recommendations

1. **Test with 4 workers first** to ensure stability
2. **Use tmux/screen** to keep session alive if SSH disconnects
3. **Monitor resources** closely during first few instances
4. **Use Spot instances** to reduce costs by 70%
5. **Set up CloudWatch alarms** for OOM or disk space issues
6. **For Babel:** Your friend can use 16-50 workers depending on available RAM

## Next Steps

After successful run on AWS, have your friend run on Babel with:
```bash
# On CMU Babel (adjust based on available resources)
WORKERS=32 bash scripts/setup_and_run.sh
```
