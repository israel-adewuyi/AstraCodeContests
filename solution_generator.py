"""Solution generator module"""

import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import uuid
from server.server import send_requests
from utils import extract_python_code

@dataclass
class Solution:
    id: str
    prompt: str
    generation: str
    metadata: Dict[str, Any]

class SolutionGenerator:
    """Generates multiple solutions using the trained model"""

    def __init__(self, model_client=None, max_retries: int = 3):
        self.model_client = model_client
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

    def generate(self, problem, feedback: Optional[str] = None, num_solutions: int = 5) -> List[Solution]:
        """Generate N solutions for a problem"""
        self.logger.info(f"Generating {num_solutions} solutions for problem {problem.key}")
        
        # Build prompt based on problem and feedback
        prompt = self._build_solution_prompt(problem, feedback, num_solutions)
        responses = send_requests(prompt)

        code_snippets = [extract_python_code(res['message']['content']) for res in responses]

        list_of_solution = [
            Solution(
                id=str(uuid.uuid4()),
                prompt=prompt,
                generation=res['message']['content'],
                metadata=res.get("metadata", {})
            ) for code, res in zip(code_snippets, responses)
        ]

        return list_of_solution

    def _build_solution_prompt(self, problem, feedback: Optional[Dict], 
                              num_solutions: int) -> str:
        """Build prompt for solution generation"""
        base_prompt = f"""
        Solve the following competitive programming problem:
        
        Problem Statement: {problem.statement}
        Input Specification: {problem.input_specification}
        Output Specification: {problem.output_specification}
        
        Sample Test Cases:
        {self._format_sample_tests(problem)}
        
        Provide a complete solution in Python that handles all the requirements.
        """

        if feedback:
            base_prompt += f"""
            
            Previous solution failed with feedback: {feedback['error_type']}
            Error details: {feedback.get('details', '')}
            
            Please provide a corrected solution that addresses this issue.
            """

        data = {
            "model": "Qwen/Qwen3-1.7B",
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant"},
                {"role": "user", "content": base_prompt}
            ],
            "n": num_solutions
        }

        return data

    def _format_sample_tests(self, problem) -> str:
        """Format sample tests for prompt"""
        formatted = ""
        for i, test in enumerate(problem.get_sample_tests(), 1):
            formatted += f"""
            Test Case {i}:
            {test}
            """
        return formatted
