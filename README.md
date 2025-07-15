# AstraCodeContests

This repository contains tools for managing and benchmarking AI coding contests.

## Directory Structure

- `vllm_benchmark/` - vLLM server benchmarking tools with concurrent request support
- `server/` - Server components
- `sandbox_fusion/` - Sandbox execution environment
- `tests/` - Unit tests for the codebase
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

## Testing

The repository includes a comprehensive test suite to ensure code quality and reliability. To run the tests:

```bash
python run_tests.py
```

The test suite covers:
- Utility functions (`test_utils.py`)
- Progress tracking (`test_progress_tracker.py`)
- Clustering and solution selection (`test_clustering_selector.py`)

### Adding New Tests

When adding new functionality, please also add corresponding tests. Follow the existing test structure:

1. Create a new test file in the `tests/` directory
2. Use the `unittest` framework
3. Ensure tests are isolated and don't depend on external state
4. Run the tests to verify they pass before submitting changes