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
    code: str
    prompt_used: str
    generation: str
    model_used: str
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
        print(f"Solution is \n {code_snippets}")

        list_of_solution = [
            Solution(
                id=str(uuid.uuid4()),
                code=code,
                prompt_used=prompt,
                generation=res['message']['content'],
                model_used=res.get("model", "solution_model"),
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

    def _call_model(self, prompt: str) -> Optional[Dict]:
        """Call the model to generate solution"""
        try:
            # Implement your model calling logic here
            # This could be using sglang, OpenAI API, or your custom model
            response = self.model_client.generate(prompt)
            return self._parse_model_response(response)
        except Exception as e:
            self.logger.error(f"Model call failed: {str(e)}")
            return None

    def _parse_model_response(self, response: str) -> Dict:
        """Parse model response into structured format"""
        # Implement parsing logic based on your model's output format
        # This is a placeholder
        return {
            "code": response,
            "language": "python",
            "model": "solution_model",
            "metadata": {}
        }

    def _generate_dummy_solution(self, problem, attempt: int) -> Dict:
        """Generate dummy solution for development"""
        return {
            "code": f"""
def solve():
    # Dummy solution for {problem.key}, attempt {attempt}
    n, m = map(int, input().split())
    return n + m

if __name__ == "__main__":
    print(solve())
""",
            "language": "python",
            "model": "dummy_model",
            "metadata": {"attempt": attempt}
        }

    def execute(self, code_str: str):
        """Execute code in sandbox"""
        pass
