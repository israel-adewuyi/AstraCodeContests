# AstraCodeContests

This repository contains tools for managing and benchmarking AI coding contests.

## Directory Structure

- `vllm_benchmark/` - vLLM server benchmarking tools with concurrent request support
- `server/` - Server components
- `sandbox_fusion/` - Sandbox execution environment
- Other contest management files

## vLLM Benchmarking

For comprehensive vLLM server benchmarking tools, see the `vllm_benchmark/` directory:

```bash
cd vllm_benchmark/
python run_benchmarks.py --scenarios
```

The benchmarking tools support:
- Concurrent request processing
- Multiple test scenarios
- Comprehensive metrics collection
- CSV and JSON output formats

See `vllm_benchmark/BENCHMARK_README.md` for detailed documentation. 