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

def run_scenario_benchmarks(config: Dict[str, Any], save_csv: bool = True):
    """Run all scenarios defined in the config file"""
    server_config = config.get('server', {})
    benchmark_config = config.get('benchmark', {})
    scenarios = config.get('test_scenarios', [])
    
    # Create benchmarker
    vllm_config = BenchmarkConfig(
        url=server_config.get('url', 'http://localhost:63455/v1/chat/completions'),
        model=server_config.get('model', 'Qwen/Qwen3-1.7B'),
        max_concurrent_requests=benchmark_config.get('max_concurrent_requests', 20),
        timeout=server_config.get('timeout', 3600),
        auth_token=server_config.get('auth_token', 'token-abc123')
    )
    
    benchmarker = VLLMBenchmarker(vllm_config)
    
    all_results = []
    
    print("="*80)
    print("RUNNING BENCHMARK SCENARIOS")
    print("="*80)
    
    for scenario in scenarios:
        scenario_name = scenario['name']
        completions_list = scenario['completions']
        prompt = scenario['prompt']
        
        print(f"\n{'='*60}")
        print(f"SCENARIO: {scenario_name}")
        print(f"Prompt: {prompt}")
        print(f"Testing completions: {completions_list}")
        print(f"{'='*60}")
        
        scenario_results = []
        
        for num_completions in completions_list:
            print(f"\nTesting {num_completions} completions...")
            
            # Use concurrent requests instead of batch processing
            concurrent_requests = min(num_completions, vllm_config.max_concurrent_requests)
            result = benchmarker.run_benchmark(prompt, num_completions, concurrent_requests)
            benchmarker.print_results(result)
            
            # Add scenario info to result
            result_dict = {
                'scenario': scenario_name,
                'prompt': prompt,
                'num_completions': result.num_completions,
                'num_requests': result.num_requests,
                'concurrent_requests': result.concurrent_requests,
                'total_time': result.total_time,
                'avg_latency': result.avg_latency,
                'throughput': result.throughput,
                'success_rate': result.success_rate,
                'error_count': result.error_count,
                'min_latency': min(result.response_times) if result.response_times else 0,
                'max_latency': max(result.response_times) if result.response_times else 0,
                'median_latency': result.response_times[len(result.response_times)//2] if result.response_times else 0
            }
            
            scenario_results.append(result_dict)
            all_results.append(result_dict)
            
            # Save individual result
            benchmarker.save_results(result, f"benchmark_{scenario_name}_{num_completions}_completions.json")
        
        # Print scenario summary
        print(f"\n{'-'*60}")
        print(f"SCENARIO SUMMARY: {scenario_name}")
        print(f"{'-'*60}")
        print(f"{'Completions':<12} {'Time (s)':<10} {'Throughput':<12} {'Latency (s)':<12} {'Success %':<10}")
        print("-" * 60)
        
        for result_dict in scenario_results:
            print(f"{result_dict['num_completions']:<12} {result_dict['total_time']:<10.2f} "
                  f"{result_dict['throughput']:<12.2f} {result_dict['avg_latency']:<12.3f} "
                  f"{result_dict['success_rate']:<10.1%}")
    
    # Save comprehensive CSV report
    if save_csv and all_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"benchmark_report_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'scenario', 'prompt', 'num_completions', 'num_requests', 'concurrent_requests',
                'total_time', 'avg_latency', 'throughput', 'success_rate', 'error_count',
                'min_latency', 'max_latency', 'median_latency'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        print(f"\nComprehensive report saved to: {csv_filename}")
    
    return all_results

def run_simple_benchmark(prompt: str, completions: int, config_file: str = "benchmark_config.json"):
    """Run a simple single benchmark"""
    config = load_config(config_file)
    
    server_config = config.get('server', {})
    benchmark_config = config.get('benchmark', {})
    
    vllm_config = BenchmarkConfig(
        url=server_config.get('url', 'http://localhost:63455/v1/chat/completions'),
        model=server_config.get('model', 'Qwen/Qwen3-1.7B'),
        max_concurrent_requests=benchmark_config.get('max_concurrent_requests', 20),
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
    parser.add_argument('--config', '-c', type=str, default='vllm_benchmark/benchmark_config.json',
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
    
    if args.scenarios:
        # Run all scenarios
        config = load_config(args.config)
        run_scenario_benchmarks(config, save_csv=not args.no_csv)
    
    elif args.prompt and args.completions:
        # Run single benchmark
        run_simple_benchmark(args.prompt, args.completions, args.config)
    
    else:
        # Run default scenario
        print("Running default benchmark scenario...")
        config = load_config(args.config)
        if config:
            run_scenario_benchmarks(config, save_csv=not args.no_csv)
        else:
            print("No config file found. Please specify --prompt and --completions or use --scenarios with a valid config file.")

if __name__ == "__main__":
    main() 