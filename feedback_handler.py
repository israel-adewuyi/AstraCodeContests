import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class Feedback:
    solution_id: str
    error_type: str  # wrong_answer, tle, runtime_error, etc.
    details: str
    test_case: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None

class FeedbackHandler:
    """Handles feedback from failed submissions and manages retry logic"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feedback_history: Dict[str, List[Feedback]] = {}
    
    def process_feedback(self, problem_key: str, solution_id: str, 
                        feedback_data: Dict, contest_manager) -> Dict:
        """Process feedback and trigger solution regeneration"""
        self.logger.info(f"Processing feedback for problem {problem_key}, solution {solution_id}")
        
        # Create feedback object
        feedback = Feedback(
            solution_id=solution_id,
            error_type=feedback_data.get("error_type", "unknown"),
            details=feedback_data.get("details", ""),
            test_case=feedback_data.get("test_case"),
            expected_output=feedback_data.get("expected_output"),
            actual_output=feedback_data.get("actual_output")
        )
        
        # Store feedback
        if problem_key not in self.feedback_history:
            self.feedback_history[problem_key] = []
        self.feedback_history[problem_key].append(feedback)
        
        # Generate new solutions with feedback
        problem = contest_manager.problems[problem_key]
        solution_generator = contest_manager.solution_generator
        
        new_solutions = solution_generator.generate(
            problem,
            num_solutions=contest_manager.config.num_solutions_per_problem,
            feedback=feedback_data
        )
        
        # Execute new solutions
        valid_solutions = contest_manager.execution_engine.filter_on_samples(
            problem, new_solutions
        )
        
        if not valid_solutions:
            return {
                "status": "failed",
                "reason": "no_valid_solutions_after_feedback"
            }
        
        # Run on private tests and select best
        private_results = contest_manager.execution_engine.run_on_private_tests(
            problem, valid_solutions
        )
        
        selected_solution = contest_manager.clustering_selector.select_best(
            private_results
        )
        
        # Update contest manager state
        contest_manager.selected_solutions[problem_key] = selected_solution
        
        return {
            "status": "success",
            "new_solution": selected_solution,
            "feedback_processed": True,
            "total_feedback_count": len(self.feedback_history[problem_key])
        }
    
    def get_feedback_history(self, problem_key: str) -> List[Feedback]:
        """Get feedback history for a problem"""
        return self.feedback_history.get(problem_key, [])
    
    def clear_feedback_history(self, problem_key: str):
        """Clear feedback history for a problem"""
        if problem_key in self.feedback_history:
            del self.feedback_history[problem_key] 