# vLLM Server Benchmarking Tools

This directory contains comprehensive tools for benchmarking your vLLM server's performance across different load scenarios using **concurrent requests**.

## Files Overview

- `benchmark_vllm.py` - Main benchmarking library with concurrent request support
- `run_benchmarks.py` - Simple runner script for easy benchmark execution
- `benchmark_config.json` - Configuration file for customizing benchmark parameters
- `BENCHMARK_README.md` - This documentation file

## Quick Start

### 1. Basic Single Benchmark

```bash
# Run a simple benchmark with 100 completions using 20 concurrent requests
python run_benchmarks.py --prompt "Write a short story about AI" --completions 100
```

### 2. Run All Predefined Scenarios

```bash
# Run all scenarios from the config file
python run_benchmarks.py --scenarios
```

### 3. Compare Multiple Completion Counts

```bash
# Compare performance across different completion counts
python benchmark_vllm.py --compare 10 50 100 200 500
```

## Configuration

Edit `benchmark_config.json` to customize:

- **Server settings**: URL, model, authentication
- **Concurrent requests**: Maximum concurrent requests (default: 20)
- **Test scenarios**: Different prompts and completion counts to test

### Example Configuration

```json
{
  "server": {
    "url": "http://localhost:63455/v1/chat/completions",
    "model": "Qwen/Qwen3-1.7B",
    "auth_token": "token-abc123",
    "timeout": 3600
  },
  "benchmark": {
    "max_concurrent_requests": 20,
    "default_prompt": "Generate a creative story about a robot learning to paint.",
    "default_completions": 100
  },
  "test_scenarios": [
    {
      "name": "Small Load",
      "completions": [10, 25, 50],
      "prompt": "Write a short poem about coding."
    },
    {
      "name": "Medium Load", 
      "completions": [100, 200, 500],
      "prompt": "Explain the concept of machine learning in simple terms."
    },
    {
      "name": "Heavy Load",
      "completions": [1000, 2000, 5000],
      "prompt": "Generate a comprehensive analysis of artificial intelligence trends in 2024."
    }
  ]
}
```

## Features

### 1. Concurrent Request Processing
- Sends multiple requests simultaneously to leverage vLLM's adaptive batching
- Configurable concurrent request limits (default: 20 concurrent requests)
- Handles large completion counts efficiently through parallel processing

### 2. Comprehensive Metrics
- **Latency**: Average, min, max, median, standard deviation
- **Throughput**: Completions per second
- **Success Rate**: Percentage of successful requests
- **Error Tracking**: Detailed error categorization
- **Server Metrics**: Extracts timing info from vLLM server responses

### 3. Multiple Output Formats
- **Console Output**: Real-time progress and formatted results
- **JSON Files**: Individual benchmark results with full details
- **CSV Reports**: Comprehensive comparison across all scenarios
- **Logging**: Detailed logs for debugging

### 4. Flexible Usage
- Command-line interface for quick tests
- Configuration file for complex scenarios
- Programmatic API for custom integrations

## Usage Examples

### run_benchmarks.py (Simple Interface)

```bash
# Basic usage with configuration file
python run_benchmarks.py --prompt "Your prompt here" --completions 100

# Run all scenarios from config file
python run_benchmarks.py --scenarios

# Skip CSV report generation
python run_benchmarks.py --scenarios --no-csv

# Use custom config file
python run_benchmarks.py --config my_config.json --scenarios
```

### benchmark_vllm.py (Advanced Interface)

```bash
# Basic usage with concurrent requests
python benchmark_vllm.py --prompt "Your prompt here" --completions 100 --concurrent 20

# With custom concurrent request limit
python benchmark_vllm.py --prompt "Your prompt" --completions 500 --concurrent 30

# Compare multiple completion counts
python benchmark_vllm.py --compare 10 50 100 200 500

# Test different concurrency levels
python benchmark_vllm.py --completions 100 --concurrent-tests 5 10 20 50

# Save results to files
python benchmark_vllm.py --prompt "Your prompt" --completions 100 --save

# Use synchronous requests instead of async
python benchmark_vllm.py --prompt "Your prompt" --completions 100 --sync

# Custom server URL
python benchmark_vllm.py --url "http://your-server:port/v1/chat/completions" --prompt "Test" --completions 50
```

### Programmatic Usage

```python
from benchmark_vllm import VLLMBenchmarker, BenchmarkConfig

# Create configuration
config = BenchmarkConfig(
    url="http://localhost:63455/v1/chat/completions",
    model="Qwen/Qwen3-1.7B",
    max_concurrent_requests=20
)

# Create benchmarker
benchmarker = VLLMBenchmarker(config)

# Run benchmark with concurrent requests
result = benchmarker.run_benchmark(
    prompt="Write a story about AI",
    num_completions=100,
    concurrent_requests=20
)

# Print results
benchmarker.print_results(result)

# Save results
benchmarker.save_results(result, "my_benchmark_results.json")
```

## Output Files

### JSON Results
Each benchmark run creates a JSON file with:
- Complete timing information
- Response statistics
- Server metrics (if available)
- Error details

### CSV Reports
When running multiple scenarios, a comprehensive CSV report is generated with:
- All scenarios and their results
- Comparison data across different completion counts
- Formatted for easy analysis in Excel/Google Sheets

## Interpreting Results

### Key Metrics

1. **Throughput (completions/second)**: Higher is better
2. **Average Latency**: Lower is better
3. **Success Rate**: Should be close to 100%
4. **Latency Distribution**: Check min/max/median for consistency

### Performance Patterns

- **Concurrency Scaling**: Throughput increases with concurrent requests up to optimal point
- **vLLM Adaptive Batching**: Server automatically batches requests for optimal GPU utilization
- **Latency Consistency**: Low standard deviation indicates stable performance
- **Error Patterns**: Monitor for connection or server errors

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check server URL and authentication
2. **Timeout Errors**: Increase timeout in config or reduce concurrent requests
3. **Memory Issues**: Reduce concurrent requests for large completion counts
4. **Server Overload**: Monitor server resources during benchmarks

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Features

### Custom Metrics Collection
The benchmarker automatically extracts server metrics from:
- Response headers with timing information
- Usage statistics in vLLM responses
- Custom headers with performance data

### Concurrent Request Optimization
- Automatically calculates optimal request distribution
- Handles edge cases for large completion counts
- Provides detailed request-level metrics

### Error Handling
- Categorizes errors by type (connection, receive, length, exceptions)
- Continues benchmarking even with partial failures
- Provides detailed error reporting

## Integration with Monitoring

The benchmarking tools can be integrated with monitoring systems:
- Export metrics to Prometheus/Grafana
- Send alerts for performance degradation
- Track performance trends over time

## Performance Tips

1. **Start Conservative**: Begin with low concurrent request counts to establish baseline
2. **Monitor Resources**: Watch CPU, memory, and GPU usage during tests
3. **Test Incrementally**: Gradually increase concurrency to find optimal point
4. **Use Representative Prompts**: Test with prompts similar to your actual use case
5. **Consider Network**: Account for network latency in distributed setups 