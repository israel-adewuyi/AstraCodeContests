import logging
import subprocess
import tempfile
import os
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sandbox_fusion import compute_score

class ExecutionStatus(Enum):
    SUCCESS = "success"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "tle"
    MEMORY_LIMIT_EXCEEDED = "mle"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"

@dataclass
class ExecutionResult:
    solution_id: str
    status: ExecutionStatus
    output: str
    error_message: Optional[str]
    execution_time: float
    memory_used: Optional[int]
    test_case: Optional[str] = None

class ExecutionEngine:
    """Handles execution of solutions in sandbox environment"""

    def __init__(self, timeout_seconds: int = 30, memory_limit_mb: int = 512):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.logger = logging.getLogger(__name__)

    def filter_on_samples(self, problem, solutions: List) -> List:
        """Filter solutions by running them on sample test cases"""
        self.logger.info(f"Filtering {len(solutions)} solutions on sample tests")

        valid_solutions = []
        sample_tests = problem.get_sample_tests()

        for solution in solutions:
            score = compute_score(
                    sandbox_fusion_url="http://localhost:8080/run_code",
                    concurrent_semaphore=None,
                    completion=solution.generation,
                    test_cases=sample_tests,
            )
            print(score)
            valid_solutions.append(score)
            # if self._passes_all_samples(solution, sample_tests):
            #     valid_solutions.append(solution)

        self.logger.info(f"{len(valid_solutions)} solutions passed sample tests")
        return valid_solutions

    def run_on_private_tests(self, problem, solutions: List) -> Dict[str, List[ExecutionResult]]:
        """Run solutions on private test suite"""
        self.logger.info(f"Running {len(solutions)} solutions on private tests")

        private_tests = problem.get_private_tests()
        if not private_tests:
            raise ValueError("Private tests not generated")

        results = {}
        for solution in solutions:
            solution_results = []
            for test_case in private_tests.test_cases:
                result = self._execute_solution(solution, test_case.input_data)
                solution_results.append(result)
            results[solution.id] = solution_results

        return results
  
    def _passes_all_samples(self, solution, sample_tests) -> bool:
        """Check if solution passes all sample test cases"""
        for test_case in sample_tests:
            result = self._execute_solution(solution, test_case.input_data)
            if result.status != ExecutionStatus.SUCCESS:
                return False
            
            # Compare output (normalize whitespace)
            if not self._outputs_match(result.output, test_case.expected_output):
                return False
        
        return True
    
    def _execute_solution(self, solution, input_data: str) -> ExecutionResult:
        """Execute a single solution with given input"""
        start_time = time.time()
        
        try:
            # Create temporary file for solution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(solution.code)
                temp_file = f.name
            
            # Execute in sandbox
            process = subprocess.run(
                ['python', temp_file],
                input=input_data.encode(),
                capture_output=True,
                timeout=self.timeout_seconds,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # Clean up
            os.unlink(temp_file)
            
            # Analyze result
            if process.returncode == 0:
                return ExecutionResult(
                    solution_id=solution.id,
                    status=ExecutionStatus.SUCCESS,
                    output=process.stdout.strip(),
                    error_message=None,
                    execution_time=execution_time,
                    memory_used=None  # Would need to implement memory tracking
                )
            else:
                return ExecutionResult(
                    solution_id=solution.id,
                    status=ExecutionStatus.RUNTIME_ERROR,
                    output="",
                    error_message=process.stderr,
                    execution_time=execution_time,
                    memory_used=None
                )
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                solution_id=solution.id,
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                output="",
                error_message="Time limit exceeded",
                execution_time=self.timeout_seconds,
                memory_used=None
            )
        except Exception as e:
            return ExecutionResult(
                solution_id=solution.id,
                status=ExecutionStatus.RUNTIME_ERROR,
                output="",
                error_message=str(e),
                execution_time=time.time() - start_time,
                memory_used=None
            )

    def _outputs_match(self, actual: str, expected: str) -> bool:
        """Compare actual and expected outputs"""
        # Normalize whitespace and line endings
        actual_normalized = actual.strip().replace('\r\n', '\n').replace('\r', '\n')
        expected_normalized = expected.strip().replace('\r\n', '\n').replace('\r', '\n')
        return actual_normalized == expected_normalized
    