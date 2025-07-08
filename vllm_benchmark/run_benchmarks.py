#!/usr/bin/env python3
"""
Simple Benchmark Runner

This script provides an easy way to run benchmarks using a configuration file
or simple command-line arguments.
"""

import json
import argparse
from benchmark_vllm import VLLMBenchmarker, BenchmarkConfig, BenchmarkResult
from typing import List, Dict, Any
import csv
from datetime import datetime

def load_config(config_file: str = "benchmark_config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_file} not found. Using defaults.")
        return {}

def run_simple_benchmark(prompt: str, completions: int, config_file: str = "benchmark_config.json"):
    """Run a simple single benchmark"""
    config = load_config(config_file)
    
    server_config = config.get('server', {})
    benchmark_config = config.get('benchmark', {})
    
    vllm_config = BenchmarkConfig(
        url=server_config.get('url', 'http://localhost:63450/v1/chat/completions'),
        model=server_config.get('model', 'Qwen/Qwen3-1.7B'),
        max_concurrent_requests=benchmark_config.get('max_concurrent_requests', 16),
        timeout=server_config.get('timeout', 3600),
        auth_token=server_config.get('auth_token', 'token-abc123')
    )
    
    benchmarker = VLLMBenchmarker(vllm_config)
    
    print(f"Running simple benchmark: {completions} completions")
    print(f"Prompt: {prompt}")
    
    # Use concurrent requests instead of batch processing
    concurrent_requests = min(completions, vllm_config.max_concurrent_requests)
    result = benchmarker.run_benchmark(prompt, completions, concurrent_requests)
    benchmarker.print_results(result)
    benchmarker.save_results(result)
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Run vLLM benchmarks')
    parser.add_argument('--config', '-c', type=str, default='benchmark_config.json',
                       help='Configuration file path')
    parser.add_argument('--scenarios', '-s', action='store_true',
                       help='Run all scenarios from config file')
    parser.add_argument('--prompt', '-p', type=str,
                       help='Custom prompt for single benchmark')
    parser.add_argument('--completions', '-n', type=int,
                       help='Number of completions for single benchmark')
    parser.add_argument('--no-csv', action='store_true',
                       help='Skip saving CSV report')
    
    args = parser.parse_args()
    
    if args.prompt and args.completions:
        # Run single benchmark
        run_simple_benchmark(args.prompt, args.completions, args.config)
    else:
        print("Please specify --prompt and --completions or use --scenarios with a valid config file.")

if __name__ == "__main__":
    main() 