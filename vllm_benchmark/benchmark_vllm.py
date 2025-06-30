#!/usr/bin/env python3
"""
vLLM Server Benchmarking Script

This script benchmarks the throughput of a vLLM server by sending concurrent requests
and measuring performance metrics including latency and throughput.
"""

import requests
import time
import json
import argparse
import statistics
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking"""
    url: str = "http://localhost:63455/v1/chat/completions"
    model: str = "Qwen/Qwen3-1.7B"
    max_concurrent_requests: int = 50  # Maximum concurrent requests
    timeout: int = 3600
    auth_token: str = "token-abc123"

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    num_completions: int
    num_requests: int
    concurrent_requests: int
    total_time: float
    avg_latency: float
    throughput: float  # completions per second
    success_rate: float
    error_count: int
    response_times: List[float]
    server_metrics: Optional[Dict[str, Any]] = None

class VLLMBenchmarker:
    """Benchmarking tool for vLLM server with concurrent requests"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.auth_token}"
        }
        self.session = None
    
    def create_request_data(self, prompt: str, num_completions: int = 1) -> Dict[str, Any]:
        """Create request data for the vLLM server"""
        return {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "n": num_completions,
            "max_tokens": 4050,
            "temperature": 0.7
        }
    
    async def send_single_request_async(self, session: aiohttp.ClientSession, 
                                      data: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        """Send a single request asynchronously"""
        start_time = time.time()
        
        try:
            async with session.post(
                self.config.url,
                headers=self.headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract server metrics if available
                    server_metrics = {}
                    if 'usage' in result:
                        server_metrics.update(result['usage'])
                    
                    # Check for custom headers that might contain timing info
                    for header, value in response.headers.items():
                        if any(keyword in header.lower() for keyword in ['time', 'latency', 'throughput']):
                            server_metrics[header] = value
                    
                    return {
                        'success': True,
                        'request_id': request_id,
                        'response_time': response_time,
                        'data': result,
                        'server_metrics': server_metrics,
                        'choices_count': len(result.get('choices', [])),
                        'status_code': response.status
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'request_id': request_id,
                        'response_time': response_time,
                        'error': f"HTTP {response.status}: {error_text}",
                        'choices_count': 0,
                        'status_code': response.status
                    }
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': False,
                'request_id': request_id,
                'response_time': response_time,
                'error': str(e),
                'choices_count': 0,
                'status_code': None
            }
    
    def send_single_request_sync(self, data: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        """Send a single request synchronously (for ThreadPoolExecutor)"""
        start_time = time.time()
        
        try:
            response = requests.post(
                self.config.url,
                headers=self.headers,
                json=data,
                timeout=self.config.timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract server metrics if available
                server_metrics = {}
                if 'usage' in result:
                    server_metrics.update(result['usage'])
                
                # Check for custom headers that might contain timing info
                for header, value in response.headers.items():
                    if any(keyword in header.lower() for keyword in ['time', 'latency', 'throughput']):
                        server_metrics[header] = value
                
                return {
                    'success': True,
                    'request_id': request_id,
                    'response_time': response_time,
                    'data': result,
                    'server_metrics': server_metrics,
                    'choices_count': len(result.get('choices', [])),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'request_id': request_id,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'choices_count': 0,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': False,
                'request_id': request_id,
                'response_time': response_time,
                'error': str(e),
                'choices_count': 0,
                'status_code': None
            }
    
    async def run_benchmark_async(self, prompt: str, num_completions: int, 
                                concurrent_requests: Optional[int] = None) -> BenchmarkResult:
        """Run benchmark using async requests for true concurrency"""
        if concurrent_requests is None:
            concurrent_requests = min(num_completions, self.config.max_concurrent_requests)
        
        logger.info(f"Starting async benchmark: {num_completions} completions with {concurrent_requests} concurrent requests")
        
        # Calculate how many requests we need
        # Each request can ask for multiple completions (n parameter)
        completions_per_request = max(1, num_completions // concurrent_requests)
        num_requests = (num_completions + completions_per_request - 1) // completions_per_request
        
        logger.info(f"Using {num_requests} requests with {completions_per_request} completions each")
        
        # Prepare all request data
        request_data_list = []
        for i in range(num_requests):
            # Calculate completions for this request
            completions_this_request = min(completions_per_request, 
                                         num_completions - i * completions_per_request)
            if completions_this_request <= 0:
                break
                
            data = self.create_request_data(prompt, completions_this_request)
            request_data_list.append((data, i))
        
        # Run concurrent requests
        all_response_times = []
        total_successful_completions = 0
        total_errors = 0
        server_metrics_aggregated = {}
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def limited_request(data, request_id):
                async with semaphore:
                    return await self.send_single_request_async(session, data, request_id)
            
            # Create all tasks
            tasks = [limited_request(data, request_id) for data, request_id in request_data_list]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Request failed with exception: {result}")
                total_errors += 1
                continue
                
            all_response_times.append(result['response_time'])
            
            if result['success']:
                total_successful_completions += result['choices_count']
                
                # Aggregate server metrics
                if result.get('server_metrics'):
                    for key, value in result['server_metrics'].items():
                        if key not in server_metrics_aggregated:
                            server_metrics_aggregated[key] = []
                        server_metrics_aggregated[key].append(value)
            else:
                total_errors += 1
                logger.warning(f"Request {result['request_id']} failed: {result.get('error', 'Unknown error')}")
        
        # Calculate final metrics
        success_rate = total_successful_completions / num_completions if num_completions > 0 else 0
        throughput = total_successful_completions / total_time if total_time > 0 else 0
        avg_latency = statistics.mean(all_response_times) if all_response_times else 0
        
        # Aggregate server metrics
        final_server_metrics = {}
        for key, values in server_metrics_aggregated.items():
            try:
                numeric_values = [float(v) for v in values if str(v).replace('.', '').replace('-', '').isdigit()]
                if numeric_values:
                    final_server_metrics[key] = statistics.mean(numeric_values)
                else:
                    final_server_metrics[key] = values[-1] if values else None
            except (ValueError, TypeError):
                final_server_metrics[key] = values[-1] if values else None
        
        return BenchmarkResult(
            num_completions=num_completions,
            num_requests=num_requests,
            concurrent_requests=concurrent_requests,
            total_time=total_time,
            avg_latency=avg_latency,
            throughput=throughput,
            success_rate=success_rate,
            error_count=total_errors,
            response_times=all_response_times,
            server_metrics=final_server_metrics
        )
    
    def run_benchmark_sync(self, prompt: str, num_completions: int, 
                          concurrent_requests: Optional[int] = None) -> BenchmarkResult:
        """Run benchmark using ThreadPoolExecutor for concurrent requests"""
        if concurrent_requests is None:
            concurrent_requests = min(num_completions, self.config.max_concurrent_requests)
        
        logger.info(f"Starting sync benchmark: {num_completions} completions with {concurrent_requests} concurrent requests")
        
        # Calculate how many requests we need
        completions_per_request = max(1, num_completions // concurrent_requests)
        num_requests = (num_completions + completions_per_request - 1) // completions_per_request
        
        logger.info(f"Using {num_requests} requests with {completions_per_request} completions each")
        
        # Prepare all request data
        request_data_list = []
        for i in range(num_requests):
            completions_this_request = min(completions_per_request, 
                                         num_completions - i * completions_per_request)
            if completions_this_request <= 0:
                break
                
            data = self.create_request_data(prompt, completions_this_request)
            request_data_list.append((data, i))
        
        # Run concurrent requests using ThreadPoolExecutor
        all_response_times = []
        total_successful_completions = 0
        total_errors = 0
        server_metrics_aggregated = {}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            # Submit all requests
            future_to_request = {
                executor.submit(self.send_single_request_sync, data, request_id): (data, request_id)
                for data, request_id in request_data_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_request):
                try:
                    result = future.result()
                    all_response_times.append(result['response_time'])
                    
                    if result['success']:
                        total_successful_completions += result['choices_count']
                        
                        # Aggregate server metrics
                        if result.get('server_metrics'):
                            for key, value in result['server_metrics'].items():
                                if key not in server_metrics_aggregated:
                                    server_metrics_aggregated[key] = []
                                server_metrics_aggregated[key].append(value)
                    else:
                        total_errors += 1
                        logger.warning(f"Request {result['request_id']} failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Request failed with exception: {e}")
                    total_errors += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate final metrics
        success_rate = total_successful_completions / num_completions if num_completions > 0 else 0
        throughput = total_successful_completions / total_time if total_time > 0 else 0
        avg_latency = statistics.mean(all_response_times) if all_response_times else 0
        
        # Aggregate server metrics
        final_server_metrics = {}
        for key, values in server_metrics_aggregated.items():
            try:
                numeric_values = [float(v) for v in values if str(v).replace('.', '').replace('-', '').isdigit()]
                if numeric_values:
                    final_server_metrics[key] = statistics.mean(numeric_values)
                else:
                    final_server_metrics[key] = values[-1] if values else None
            except (ValueError, TypeError):
                final_server_metrics[key] = values[-1] if values else None
        
        return BenchmarkResult(
            num_completions=num_completions,
            num_requests=num_requests,
            concurrent_requests=concurrent_requests,
            total_time=total_time,
            avg_latency=avg_latency,
            throughput=throughput,
            success_rate=success_rate,
            error_count=total_errors,
            response_times=all_response_times,
            server_metrics=final_server_metrics
        )
    
    def run_benchmark(self, prompt: str, num_completions: int, 
                     concurrent_requests: Optional[int] = None, 
                     use_async: bool = True) -> BenchmarkResult:
        """Run benchmark with choice of async or sync implementation"""
        if use_async:
            return asyncio.run(self.run_benchmark_async(prompt, num_completions, concurrent_requests))
        else:
            return self.run_benchmark_sync(prompt, num_completions, concurrent_requests)
    
    def print_results(self, result: BenchmarkResult):
        """Print benchmark results in a formatted way"""
        print("\n" + "="*60)
        print("BENCHMARK RESULTS")
        print("="*60)
        print(f"Total Completions Requested: {result.num_completions}")
        print(f"Request Configuration: {result.num_requests} requests, {result.concurrent_requests} concurrent")
        print(f"Total Time: {result.total_time:.2f} seconds")
        print(f"Average Latency: {result.avg_latency:.2f} seconds")
        print(f"Throughput: {result.throughput:.2f} completions/second")
        print(f"Success Rate: {result.success_rate:.2%}")
        print(f"Error Count: {result.error_count}")
        
        if result.response_times:
            print(f"Latency Statistics:")
            print(f"  Min: {min(result.response_times):.3f}s")
            print(f"  Max: {max(result.response_times):.3f}s")
            print(f"  Median: {statistics.median(result.response_times):.3f}s")
            print(f"  Std Dev: {statistics.stdev(result.response_times):.3f}s")
        
        if result.server_metrics:
            print(f"\nServer Metrics:")
            for key, value in result.server_metrics.items():
                print(f"  {key}: {value}")
        
        print("="*60)
    
    def save_results(self, result: BenchmarkResult, filename: Optional[str] = None):
        """Save benchmark results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"res/benchmark_results_{timestamp}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'num_completions': result.num_completions,
            'num_requests': result.num_requests,
            'concurrent_requests': result.concurrent_requests,
            'total_time': result.total_time,
            'avg_latency': result.avg_latency,
            'throughput': result.throughput,
            'success_rate': result.success_rate,
            'error_count': result.error_count,
            'response_times': result.response_times,
            'server_metrics': result.server_metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results saved to {filename}")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Benchmark vLLM server performance with concurrent requests')
    parser.add_argument('--prompt', '-p', type=str, 
                       default="Generate a creative story about a robot learning to paint.",
                       help='Prompt to send to the model')
    parser.add_argument('--completions', '-n', type=int, default=100,
                       help='Number of completions to generate')
    parser.add_argument('--concurrent', '-c', type=int, default=10,
                       help='Number of concurrent requests')
    parser.add_argument('--url', type=str, default="http://localhost:63455/v1/chat/completions",
                       help='vLLM server URL')
    parser.add_argument('--model', type=str, default="Qwen/Qwen3-1.7B",
                       help='Model name')
    parser.add_argument('--save', '-s', action='store_true',
                       help='Save results to JSON file')
    parser.add_argument('--sync', action='store_true',
                       help='Use synchronous requests instead of async')
    parser.add_argument('--compare', nargs='+', type=int,
                       help='Compare multiple completion counts (e.g., 10 50 100 200)')
    parser.add_argument('--concurrent-tests', nargs='+', type=int,
                       help='Compare different concurrent request levels (e.g., 5 10 20 50)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = BenchmarkConfig(
        url=args.url,
        model=args.model,
        max_concurrent_requests=args.concurrent
    )
    
    # Create benchmarker
    benchmarker = VLLMBenchmarker(config)
    
    if args.compare:
        # Run comparison benchmarks
        print(f"Running comparison benchmarks for completion counts: {args.compare}")
        print(f"Prompt: {args.prompt}")
        print(f"Model: {args.model}")
        print(f"Concurrent requests: {args.concurrent}")
        
        results = []
        for num_completions in args.compare:
            print(f"\n{'='*40}")
            print(f"Testing {num_completions} completions...")
            print(f"{'='*40}")
            
            result = benchmarker.run_benchmark(args.prompt, num_completions, args.concurrent, not args.sync)
            benchmarker.print_results(result)
            results.append(result)
            
            if args.save:
                benchmarker.save_results(result, f"benchmark_{num_completions}_completions.json")
        
        # Print comparison summary
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"{'Completions':<12} {'Time (s)':<10} {'Throughput':<12} {'Latency (s)':<12} {'Success %':<10}")
        print("-" * 60)
        
        for result in results:
            print(f"{result.num_completions:<12} {result.total_time:<10.2f} "
                  f"{result.throughput:<12.2f} {result.avg_latency:<12.3f} "
                  f"{result.success_rate:<10.1%}")
    
    elif args.concurrent_tests:
        # Test different concurrent request levels
        print(f"Testing different concurrent request levels: {args.concurrent_tests}")
        print(f"Prompt: {args.prompt}")
        print(f"Completions: {args.completions}")
        
        results = []
        for concurrent in args.concurrent_tests:
            print(f"\n{'='*40}")
            print(f"Testing {concurrent} concurrent requests...")
            print(f"{'='*40}")
            
            result = benchmarker.run_benchmark(args.prompt, args.completions, concurrent, not args.sync)
            benchmarker.print_results(result)
            results.append(result)
            
            if args.save:
                benchmarker.save_results(result, f"benchmark_{concurrent}_concurrent.json")
        
        # Print comparison summary
        print(f"\n{'='*60}")
        print("CONCURRENCY COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"{'Concurrent':<12} {'Time (s)':<10} {'Throughput':<12} {'Latency (s)':<12} {'Success %':<10}")
        print("-" * 60)
        
        for result in results:
            print(f"{result.concurrent_requests:<12} {result.total_time:<10.2f} "
                  f"{result.throughput:<12.2f} {result.avg_latency:<12.3f} "
                  f"{result.success_rate:<10.1%}")
    
    else:
        # Run single benchmark
        print(f"Running benchmark with {args.completions} completions and {args.concurrent} concurrent requests")
        print(f"Prompt: {args.prompt}")
        
        result = benchmarker.run_benchmark(args.prompt, args.completions, args.concurrent, not args.sync)
        benchmarker.print_results(result)
        
        if args.save:
            benchmarker.save_results(result)

if __name__ == "__main__":
    main() 