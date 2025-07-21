#!/bin/bash

set -e

PROJECT_ROOT="$PWD"
WORKSPACE_ROOT=$(dirname "$PROJECT_ROOT")
SANDBOX_FUSION_DIR="$WORKSPACE_ROOT/SandboxFusion"
MINICONDA_DIR="$WORKSPACE_ROOT/miniconda3"

if [ ! -f "README.md" ] || [ ! -d ".git" ]; then
    echo "Error: This script must be run from the AstraCodeContests repository directory."
    echo "Please navigate to the AstraCodeContests directory and try again."
    exit 1
fi

# Clone SandboxFusion if not present
if [ -d "$SANDBOX_FUSION_DIR" ]; then
    echo "SandboxFusion repository already exists, skipping clone process"
else
    git clone https://github.com/bytedance/SandboxFusion.git "$SANDBOX_FUSION_DIR"
fi

# Install Miniconda if not already installed
if [ -d "$MINICONDA_DIR" ]; then
    echo "Miniconda already installed, skipping installation"
else
    if [ ! -f "/tmp/Miniconda3-latest-Linux-x86_64.sh" ]; then
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/Miniconda3-latest-Linux-x86_64.sh
    fi
    bash /tmp/Miniconda3-latest-Linux-x86_64.sh -b -p "$MINICONDA_DIR"
    rm -f /tmp/Miniconda3-latest-Linux-x86_64.sh
fi
source "$MINICONDA_DIR/etc/profile.d/conda.sh"

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create and activate sandbox env
conda create -n sandbox python=3.12 -y
conda activate sandbox

# Install dependencies in SandboxFusion
cd "$SANDBOX_FUSION_DIR"
conda install -c conda-forge poetry -y
poetry install
mkdir -p docs/build
cd runtime/python
bash install-python-runtime.sh || {
    echo "Warning: install-python-runtime.sh failed, continuing anyway"
}

conda activate sandbox-runtime
conda install -c conda-forge uvicorn structlog fastapi databases aiofiles aiohttp transformers aiosqlite psutil tenacity -y

# Set up virtual env
cd "$PROJECT_ROOT" 
conda activate sandbox
python -m venv "$WORKSPACE_ROOT/astracode"
source "$WORKSPACE_ROOT/astracode/bin/activate"
pip install vllm --extra-index-url https://download.pytorch.org/whl/cu124
pip install streamlit

# Deactivate virtual env
deactivate

echo "Setup complete!"