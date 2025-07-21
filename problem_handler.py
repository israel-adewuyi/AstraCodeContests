import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from utils import generate_hash, extract_text_after_think, get_inputs, extract_python_code, extract_test_cases  
from server.server import send_requests
from prompt import PRIVATE_TESTS_SYS_PROMPT

@dataclass
class TestCase:
    input_data: str
    expected_output: str
    description: Optional[str] = None

@dataclass
class PrivateTestSuite:
    test_cases: List[TestCase]
    response: str

class Problem:
    """Represents a CP problem with enhanced functionality"""

    def __init__(self, **kwargs):
        """Initialize problem with all attributes"""
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.key = generate_hash(f"{self.contest_id}-{self.problem_id}")
        # self.private_tests: Optional[PrivateTestSuite] = None
        self.sample_tests: List[TestCase] = []
        self.logger = logging.getLogger(__name__)

    def generate_private_tests(self, tokenizer):
        """Generate private test suite using the bigger model"""
        self.logger.info(f"Generating private tests for problem {self.key}")
        
        # Construct prompt for test generation
        prompt = self._build_test_generation_prompt()
        response = send_requests(prompt)
        test_cases = self._parse_test_generation_response(response[0]['message']['content'])
        
        self.private_tests = PrivateTestSuite(
            test_cases=test_cases,
            response=response,
        )

        self.logger.info(f"Generated {len(test_cases)} private test cases")
        return self.private_tests

    def _build_test_generation_prompt(self) -> dict:
        """Build prompt for test case generation"""
        
        prompt = f"""
        You are tasked with generating comprehensive test cases for a competitive programming problem to create a private test suite. The problem may have either a single test case or multiple test cases, where the first line specifies `T` (the number of test cases) followed by `T` test cases. Your task is to generate 10-15 diverse test cases, including edge cases, boundary conditions, large inputs, and corner cases.

        Instructions:
        1. Input Structure:
        - For single test case problems, generate the input directly without a `T` line.
        - For multiple test case problems (e.g., first line contains `T`), set `T=1` for simplicity and generate the test case content accordingly.
        2. Diversity: Ensure test cases cover edge cases (e.g., minimum/maximum values), boundary conditions, large inputs (within constraints), and corner cases (unusual but valid inputs).
        3. Formatting:
        - Use newlines to separate inputs as required by the problem.
        - Format each test case as:
            INPUT:
            <input test case>
        4. Constraints: Adhere to the problem's input specification (e.g., value ranges, array sizes).
        5. Avoid Example Inputs: Generated test cases must be completely different from the example provided.

        Problem Details:
        - Problem Statement: {self.statement}
        - Input Specification: {self.input_specification}

        Format examples:

        1. Single Test Case Problem:
        - Problem Statement: Given an integer `n`, compute the sum of integers from 1 to `n`.
        - Input Specification: A single integer `n` (1 ≤ n ≤ 10^5).
        - Example Input: 5
        - Generated Test Cases:
            INPUT:
            1
            INPUT:
            100000
            INPUT:
            42
            INPUT:
            99999

        2. Multiple Test Case Problem:
        - Problem Statement: Given `T` test cases, for each test case, given an integer `n`, compute the sum of integers from 1 to `n`.
        - Input Specification: The first line contains `T` (1 ≤ T ≤ 100). Each of the next `T` lines contains an integer `n` (1 ≤ n ≤ 10^5).
        - Example Input: 
            2
            3
            4
        - Generated Test Cases (with T=1 for simplicity):
            INPUT:
            1
            1
            INPUT:
            1
            100000
            INPUT:
            1
            50000
            INPUT:
            1
            99999 

        Examples for this problem:
        - Example Input: {self.examples[0]["input"][0]}

        Task:
        Generate 10-15 diverse test cases for the given problem, following the input structure (single or multiple test cases as specified). 
        Ensure each test case is formatted correctly, adheres to the input specification, and is distinct from the example input.

        Output:
        Provide the test cases in the format:
        INPUT:
        <input test case>
        """
        
        data = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [
                {"role": "system", "content": PRIVATE_TESTS_SYS_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }
        
        return data

    def _parse_test_generation_response(self, response: str) -> List[TestCase]:
        """Parse model response into TestCase objects"""
        test_cases = extract_test_cases(response)[1:6]
        self.logger.info(f"Test cases are {test_cases}")
        return test_cases

    def get_sample_tests(self) -> List[TestCase]:
        """Get sample test cases"""
        return self.examples

    def get_private_tests(self) -> Optional[PrivateTestSuite]:
        """Get private test suite"""
        return self.private_tests 
    
    def delete_private_case(self) -> None:
        """Delete all the private test cases"""
        if hasattr(self, "private_tests"):
            del self.private_tests
            self.logger.info(f"Deleted private tests for problem {self.key}")
        self.logger.info(f"No private tests for problem {self.key}")