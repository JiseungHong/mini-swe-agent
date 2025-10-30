#!/bin/bash
# Install SingularityCE (container runtime)
# This script uninstalls the wrong Python "singularity" package and installs SingularityCE

set -e

echo "========================================================================"
echo "Installing SingularityCE"
echo "========================================================================"
echo ""

# Uninstall Python singularity package if it exists
echo "Removing Python singularity package (if installed)..."
pip uninstall -y singularity 2>/dev/null || echo "Python singularity not installed, skipping"
echo ""

# Install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y build-essential libseccomp-dev pkg-config squashfs-tools cryptsetup wget
echo "✓ Dependencies installed"
echo ""

# Install Go (required for SingularityCE)
if ! command -v go &> /dev/null; then
    echo "Installing Go..."
    export VERSION=1.21.5 OS=linux ARCH=amd64
    wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz
    sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz
    rm go$VERSION.$OS-$ARCH.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
    echo "✓ Go installed"
else
    echo "✓ Go already installed"
fi
echo ""

# Install SingularityCE
echo "Installing SingularityCE..."
export VERSION=4.1.0
wget https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-ce-${VERSION}.tar.gz
tar -xzf singularity-ce-${VERSION}.tar.gz
cd singularity-ce-${VERSION}
./mconfig
make -C builddir
sudo make -C builddir install
cd ..
rm -rf singularity-ce-${VERSION}*
echo "✓ SingularityCE installed"
echo ""

# Verify installation
echo "Verifying installation..."
singularity --version
echo ""

echo "========================================================================"
echo "Installation complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "1. Source your bashrc: source ~/.bashrc"
echo "2. Test singularity: singularity pull docker://hello-world"
echo "3. Resume mini-swe-agent: SKIP_SETUP=1 SKIP_VLLM=1 bash scripts/run.sh"
