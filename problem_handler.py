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
        Generate comprehensive test cases for the following competitive programming problem:
        
        Problem Statement: {self.statement}
        Input Specification: {self.input_specification}
        
        Generate 10-15 diverse test cases including:
        - Edge cases
        - Boundary conditions
        - Large inputs
        - Corner cases
        
        Pay attention to how to use newline to separate the inputs. 
        You can use the following as an example
        INPUT:
        {self.examples[0]["input"][0]}
        Note that what you generate should be completely different from the example provided.
        
        Note that if a problem has multiple test cases, you can just set the number of test cases to 1 and generate the necessary content
        
        Format each test case as:
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