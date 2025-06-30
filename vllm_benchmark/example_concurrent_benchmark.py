#!/usr/bin/env python3
"""
Example: Concurrent vLLM Benchmarking

This script demonstrates how to properly benchmark vLLM server using concurrent requests
instead of sequential batch processing.
"""

import asyncio
import time
from benchmark_vllm import VLLMBenchmarker, BenchmarkConfig

async def demonstrate_concurrent_vs_sequential():
    """Demonstrate the difference between concurrent and sequential approaches"""
    
    # Configuration
    config = BenchmarkConfig(
        url="http://localhost:63455/v1/chat/completions",
        model="Qwen/Qwen3-1.7B",
        max_concurrent_requests=20
    )
    
    benchmarker = VLLMBenchmarker(config)
    prompt = "Write a short story about artificial intelligence."
    
    print("="*80)
    print("vLLM CONCURRENT BENCHMARKING DEMONSTRATION")
    print("="*80)
    
    # Test different completion counts
    completion_counts = [50, 100, 200]
    concurrent_levels = [5, 10, 20]
    
    print(f"\nTesting completion counts: {completion_counts}")
    print(f"Testing concurrent levels: {concurrent_levels}")
    print(f"Prompt: {prompt}")
    
    # Test different completion counts with fixed concurrency
    print(f"\n{'='*60}")
    print("TESTING DIFFERENT COMPLETION COUNTS (20 concurrent)")
    print(f"{'='*60}")
    
    for completions in completion_counts:
        print(f"\nTesting {completions} completions...")
        
        # Use async concurrent approach
        result = await benchmarker.run_benchmark_async(prompt, completions, 20)
        
        print(f"  Time: {result.total_time:.2f}s")
        print(f"  Throughput: {result.throughput:.2f} completions/sec")
        print(f"  Avg Latency: {result.avg_latency:.3f}s")
        print(f"  Success Rate: {result.success_rate:.1%}")
    
    # Test different concurrency levels with fixed completions
    print(f"\n{'='*60}")
    print("TESTING DIFFERENT CONCURRENCY LEVELS (100 completions)")
    print(f"{'='*60}")
    
    for concurrent in concurrent_levels:
        print(f"\nTesting {concurrent} concurrent requests...")
        
        # Use async concurrent approach
        result = await benchmarker.run_benchmark_async(prompt, 100, concurrent)
        
        print(f"  Time: {result.total_time:.2f}s")
        print(f"  Throughput: {result.throughput:.2f} completions/sec")
        print(f"  Avg Latency: {result.avg_latency:.3f}s")
        print(f"  Success Rate: {result.success_rate:.1%}")
        print(f"  Requests: {result.num_requests}")

def demonstrate_vllm_adaptive_batching():
    """Demonstrate how vLLM's adaptive batching works"""
    
    print(f"\n{'='*60}")
    print("UNDERSTANDING vLLM ADAPTIVE BATCHING")
    print(f"{'='*60}")
    
    print("""
vLLM's adaptive batching works as follows:

1. **Concurrent Requests**: You can send multiple requests simultaneously
2. **Internal Batching**: vLLM automatically batches requests internally based on:
   - Available GPU memory
   - Model capacity
   - Request characteristics (similar prompts batch better)
3. **Dynamic Adjustment**: As requests complete, new ones are added to batches
4. **Optimal Throughput**: This maximizes GPU utilization and throughput

Key Benefits:
- No need to manually manage batch sizes
- Automatic optimization based on hardware
- Better resource utilization
- Reduced latency through parallel processing

Example:
- Send 1000 requests with 50 concurrent connections
- vLLM processes ~15 requests in each GPU batch (depending on memory)
- As batches complete, new requests are automatically added
- Results in optimal throughput without overwhelming the system
""")

def main():
    """Main demonstration function"""
    print("Starting vLLM Concurrent Benchmarking Demonstration...")
    
    # Show explanation first
    demonstrate_vllm_adaptive_batching()
    
    # Run actual benchmarks
    try:
        asyncio.run(demonstrate_concurrent_vs_sequential())
    except Exception as e:
        print(f"Benchmark failed: {e}")
        print("Make sure your vLLM server is running on http://localhost:63455")
    
    print(f"\n{'='*60}")
    print("USAGE EXAMPLES")
    print(f"{'='*60}")
    
    print("""
# Basic concurrent benchmark
python benchmark_vllm.py --prompt "Your prompt" --completions 100 --concurrent 20

# Compare different completion counts
python benchmark_vllm.py --compare 50 100 200 500 --concurrent 20

# Test different concurrency levels
python benchmark_vllm.py --completions 100 --concurrent-tests 5 10 20 50

# Use synchronous requests (if async doesn't work)
python benchmark_vllm.py --prompt "Your prompt" --completions 100 --concurrent 20 --sync

# Save results to files
python benchmark_vllm.py --prompt "Your prompt" --completions 100 --concurrent 20 --save
""")

if __name__ == "__main__":
    main() 