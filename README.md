# AstraCodeContests

Welcome to the AstraCodeContests! Runpod.io is what I used as the dev environment. 

## Prerequisites
- Linux-based system (e.g., Ubuntu)
- `git`, and `bash` installed

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/israel-adewuyi/AstraCodeContests.git
cd AstraCodeContests
```

### 2. Run the Setup Script
The `setup.sh` script in the repository root automates the installation of all dependencies, including the `SandboxFusion` repository, Miniconda, Python environments, and required packages.


```bash
chmod +x setup.sh
./setup.sh
```

## Running 
### SandboxFusion
From `AstraCodeContests` dir, run 
```bash
source ../miniconda3/etc/profile.d/conda.sh
conda activate sandbox-runtime
cd ../SandboxFusion/
make run-online
```

### Spinning Up vllm to run inference for a CP problem
- Astracode1.5B to solve the problem
```bash
source ../astracode/bin/activate
vllm serve --config server/config.yaml
```

- Qwen2.5-7B to generate private test suite
```bash
source ../astracode/bin/activate
vllm serve --config server/test_config.yaml
```

### Streamlit
```bash
source ../astracode/bin/activate
streamlit run app.py
```

## Testing

The repository includes a test suite to ensure code quality and reliability. To run the tests:

```bash
python run_tests.py
```

The test suite covers:
- Utility functions (`test_utils.py`)
- Progress tracking (`test_progress_tracker.py`)
- Clustering and solution selection (`test_clustering_selector.py`)
