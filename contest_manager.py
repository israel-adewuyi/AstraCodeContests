import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from progress_tracker import ProgressTracker

from problem_handler import Problem
from solution_generator import SolutionGenerator
from execution_engine import ExecutionEngine
from clustering_selector import ClusteringSelector
from feedback_handler import FeedbackHandler

from transformers import AutoTokenizer

class ContestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ContestConfig:
    contest_id: int
    model_name: str = "israel-adewuyi/Astracode_demo"
    num_solutions_per_problem: int = 512
    max_retries: int = 3
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    port: int = 63455

class ContestManager:
    """Manages the overall contest state and orchestrates the solution pipeline"""

    def __init__(self, config: ContestConfig):
        self.config = config
        self.status = ContestStatus.PENDING
        self.problems: Dict[str, Problem] = {}
        self.solutions: Dict[str, List[Dict]] = {}
        self.selected_solutions: Dict[str, Dict] = {}

        # Initialize components
        self.solution_generator = SolutionGenerator(config.model_name, config.port)
        self.execution_engine = ExecutionEngine(
            timeout_seconds=config.timeout_seconds,
            memory_limit_mb=config.memory_limit_mb
        )
        self.clustering_selector = ClusteringSelector()
        self.feedback_handler = FeedbackHandler()
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B")

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.progress_tracker = ProgressTracker()
        self.executor = ThreadPoolExecutor(max_workers=4)  # or configurable
        self.futures = {}

    def add_problem(self, problem_data: Dict) -> str:
        """Add a new problem to the contest"""
        problem = Problem(**problem_data)
        self.problems[problem.key] = problem
        self.solutions[problem.key] = []
        self.logger.info(f"Added problem {problem.key}")
        return problem.key

    def solve_problem(self, problem_key: str) -> Dict:
        """Main pipeline for solving a single problem"""
        if problem_key not in self.problems:
            raise ValueError(f"Problem {problem_key} not found")

        problem = self.problems[problem_key]
        self.solutions[problem.key] = []
        # self.progress_tracker.reset(problem_key)
        self.logger.info(f"Starting solution pipeline for problem {problem_key}")

        try:
            # Step 1: Generate private test suite if not exists
            if not hasattr(problem, 'private_tests') or (hasattr(problem, 'private_tests') and len(problem.get_private_tests().test_cases) == 0):
                private_tests = problem.generate_private_tests(self.tokenizer)
            else:
                self.logger.info(f"Reusing previously generated private tests for problem {problem_key}")
                
            assert len(private_tests.test_cases) > 0

            # # Step 2: Generate N solutions
            solutions = self.solution_generator.generate(
                problem,
                num_solutions=self.config.num_solutions_per_problem
            )

            # self.logger.info("Solutions have been generated")

            # # Step 3: Execute solutions on sample test cases
            # valid_solutions = self.execution_engine.run_on_sample_tests(
            #     problem, solutions
            # )

            # if not valid_solutions:
            #     self.logger.warning(f"No valid solutions for problem {problem_key}")
            #     return {"status": "failed", "reason": "no_valid_solutions"}

            # # Step 4: Execute on private test suite
            # private_results = self.execution_engine.run_on_private_tests(
            #     problem, valid_solutions
            # )
            
            # self.logger.info("Running solutions on private tests completed")
            
            # solutions_dict = {sol.id: sol for sol in solutions}

            # # # Step 5: Cluster and select best solution
            # selected_solution = self.clustering_selector.select_best(
            #     private_results
            # )
            
            # selected_solution["generation"] = solutions_dict[selected_solution["selected_solution_id"]].generation

            # self.selected_solutions[problem_key] = selected_solution
            # self.solutions[problem_key] = solutions

            # self.logger.info(f"Successfully solved problem {problem_key}")
            # return {
            #     "status": "success",
            #     "selected_solution": selected_solution,
            #     "total_solutions": len(solutions),
            #     "valid_solutions": len(valid_solutions)
            # }

        except Exception as e:
            self.logger.error(f"Error solving problem {problem_key}: {str(e)}")
            return {"status": "failed", "reason": str(e)}

    def handle_feedback(self, problem_key: str, solution_id: str, 
                       feedback: Dict) -> Dict:
        """Handle feedback from failed submissions"""
        return self.feedback_handler.process_feedback(
            problem_key, solution_id, feedback, self
        )

    def solve_all_problems(self) -> Dict:
        """Solve all problems in the contest"""
        self.status = ContestStatus.IN_PROGRESS
        results = {}

        for problem_key in self.problems:
            results[problem_key] = self.solve_problem(problem_key)

        self.status = ContestStatus.COMPLETED
        return results

    def save_state(self, filepath: str):
        """Save contest state to file"""
        state = {
            "config": asdict(self.config),
            "status": self.status.value,
            "problems": {k: v.__dict__ for k, v in self.problems.items()},
            "selected_solutions": self.selected_solutions
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """Load contest state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
 
        # Reconstruct state
        self.config = ContestConfig(**state["config"])
        self.status = ContestStatus(state["status"])
        # Reconstruct problems and other components...

    def solve_problem_threaded(self, problem_key):
        self.progress_tracker.update(problem_key, "started")
        try:
            self.progress_tracker.update(problem_key, "generating solutions")
            # ... (insert checkpoints in the pipeline)
            self.progress_tracker.reset()
            result = self.solve_problem(problem_key)
            self.progress_tracker.update(problem_key, "completed", detail=result)
            return result
        except Exception as e:
            self.progress_tracker.update(problem_key, "failed", detail=str(e))
            raise

    def solve_all_problems_concurrently(self):
        self.status = ContestStatus.IN_PROGRESS
        self.futures = {}
        for problem_key in self.problems:
            future = self.executor.submit(self.solve_problem_threaded, problem_key)
            self.futures[problem_key] = future

    def get_progress(self, problem_key=None):
        if problem_key:
            return self.progress_tracker.get(problem_key)
        return self.progress_tracker.all()

    def delete_problem(self, problem_key: str) -> bool:
        """Delete a problem and its associated data from the contest."""
        if problem_key in self.problems:
            del self.problems[problem_key]
            if problem_key in self.solutions:
                del self.solutions[problem_key]
            if problem_key in self.selected_solutions:
                del self.selected_solutions[problem_key]
            self.logger.info(f"Deleted problem {problem_key}")
            return True
        else:
            self.logger.warning(f"Attempted to delete non-existent problem {problem_key}")
            return False

    def reset_solution(self):
        for problem_key in self.problems:
            if problem_key in self.solutions:
                del self.solutions[problem_key]
            if problem_key in self.selected_solutions:
                del self.selected_solutions[problem_key]
            self.logger.info(f"Deleted solutions for problem {problem_key}")
            self.problems[problem_key].delete_private_case()
        
if __name__ == "__main__":
    # Example usage
    config = ContestConfig(contest_id=410)
    manager = ContestManager(config)

    problem_data = {
        "statement": """In AtCoder Kingdom, there are N horse races being held. Horses aged A_i or younger can participate in the i-th race.
Among the N races, how many races can a K-year-old horse participate in?""",
        "input_specification": """The input is given from Standard Input in the following format:
        N
        A_1, A_2,  … A_N
        K
        All input values are integers.
        1≤N≤100
        1≤A_i≤100
        1≤K≤100
        """,
        "output_specification": "Output the answer as an integer.",
        "contest_id": 410,
        "problem_id": "A",
        "examples": [{"input" : ["5\n3 1 4 1 5\n4"], "output" : ["2"]}]
    }

    problem_key = manager.add_problem(problem_data)
    # result = None
    result = manager.solve_problem(problem_key)
    print(result)
