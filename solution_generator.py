"""Solution generator module"""

import logging
import time
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
import uuid
# from server.server import send_requests
from utils import extract_python_code
from transformers import AutoTokenizer

@dataclass
class Solution:
    id: str
    prompt: str
    generation: str
    metadata: Dict[str, Any]

class SolutionGenerator:
    """Generates multiple solutions using the trained model"""

    def __init__(self, model_name: str, port: int, max_retries: int = 3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.port = port
        
        self.sampling_temp = 1.0
        self.max_tokens = 1024

    def generate(self, problem, feedback: Optional[str] = None, num_solutions: int = 5) -> List[Solution]:
        """Generate N solutions for a problem"""
        self.logger.info(f"Generating {num_solutions} solutions for problem {problem.key}")
        
        try:
            # Build prompt based on problem and feedback
            prompt = self._build_solution_prompt(problem, feedback, num_solutions)
            payload = self._prepare_payload(
                prompt, 
                num_solutions, 
                self.sampling_temp,
                self.max_token
            )
            self._flush_server()
            responses = self._send_request(url, payload).json
            # responses = send_requests(prompt)

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
        except Exception as e:
            raise

    def _build_prompt(self, problem, feedback: Optional[Dict], tokenize: bool, add_gen_prompt) -> str:
        """Build prompt for solution generation"""
        base_prompt = f"""
        Provide a Python solution to a competitive programming question.
        
        Problem Statement: {problem.statement}
        Input Specification: {problem.input_specification}
        Output Specification: {problem.output_specification}
        
        Examples:
        {self._format_sample_tests(problem)}
        
        Think step by step and write python code to solve this problem. 
        Present the code in ```python\nYour code\n```
        """

        if feedback:
            base_prompt += f"""
            
            Previous solution failed with feedback: {feedback['error_type']}
            Error details: {feedback.get('details', '')}
            
            Please provide a corrected solution that addresses this issue.
            """

        # return data
        messages = [
            {"role": "user", "content": base_prompt}
        ]
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=tokenize,
            add_generation_prompt=add_gen_prompt
        )
       
    def _send_request(self, url, data: Optional[dict] = None):
        """Method to send info the requests to the sglang server"""
        try:
            response = requests.post(url, json=data)
            return response
        except Exception as e:
            raise
         
    def _prepare_payload(
        self, 
        prompt: Union[List[str], List[int]],
        num_generations: int, 
        sampling_temp: float,
        max_tokens: int,
    ):
        payload = {
            "input_ids": prompt,
            "sampling_params": {
                "max_new_tokens": max_tokens,
                "repetition_penalty": 1.05,
                "top_p": 0.8,
                "top_k": 20,
                "temperature": sampling_temp,
                "n": num_generations
            }
        }

        return payload

    def _format_sample_tests(self, problem) -> str:
        """Format sample tests for prompt"""
        formatted = ""
        for i, test in enumerate(problem.get_sample_tests(), 1):
            formatted += f"""
            Test Case {i}:
            {test}
            """
        return formatted

    # def inference(
    #     self, 
    #     prompt: List[int], 
    #     stop_at_newline: bool,
    #     eval_prompt: bool = False,
    #     num_generations: int = None,
    #     sampling_temp: float = 0.6,
    #     max_tokens: int = 2048
    # ):
    #     try:
    #         self.flush_server()
    #         url = f"http://localhost:{self.port}/generate"
    #         payload = self._prepare_payload(
    #             prompt, 
    #             num_generations, 
    #             stop_at_newline, 
    #             eval_prompt,
    #             sampling_temp,
    #             max_tokens=max_tokens
    #         )
    #         return self._send_request(url, payload).json()
    #     except Exception as e:
    #         self.shutdown
    #         raise
        
    def _flush_server(self) -> None:
        """Flushes the server cache. Running this method before every inference."""
        url = f"http://localhost:{self.port}/flush_cache"
        self._send_request(url)