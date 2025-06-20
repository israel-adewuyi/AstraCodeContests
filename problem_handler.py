import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from utils import generate_hash

@dataclass
class TestCase:
    input_data: str
    expected_output: str
    description: Optional[str] = None

@dataclass
class PrivateTestSuite:
    test_cases: List[TestCase]
    generation_prompt: str
    model_used: str

class Problem:
    """Represents a CP problem with enhanced functionality"""

    def __init__(self, **kwargs):
        """Initialize problem with all attributes"""
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.key = generate_hash(f"{self.contest_id}-{self.problem_id}")
        self.private_tests: Optional[PrivateTestSuite] = None
        self.sample_tests: List[TestCase] = []

        # Parse examples if provided
        if hasattr(self, 'examples'):
            self._parse_examples()

        self.logger = logging.getLogger(__name__)

    def _parse_examples(self):
        """Parse sample test cases from examples"""
        # This is a simplified parser - you'll need to implement based on your format
        if isinstance(self.examples, str):
            # Parse examples string into TestCase objects
            # This is placeholder logic
            self.sample_tests = [
                TestCase("sample_input_1", "sample_output_1"),
                TestCase("sample_input_2", "sample_output_2")
            ]

    def generate_private_tests(self, model_client=None):
        """Generate private test suite using the bigger model"""
        if self.private_tests:
            self.logger.info(f"Private tests already exist for problem {self.key}")
            return self.private_tests

        self.logger.info(f"Generating private tests for problem {self.key}")

        # Construct prompt for test generation
        prompt = self._build_test_generation_prompt()

        if model_client:
            # Use the provided model client to generate tests
            response = model_client.generate(prompt)
            test_cases = self._parse_test_generation_response(response)
        else:
            # Fallback to dummy tests for development
            test_cases = self._generate_dummy_tests()

        self.private_tests = PrivateTestSuite(
            test_cases=test_cases,
            generation_prompt=prompt,
            model_used="test_generation_model"
        )

        self.logger.info(f"Generated {len(test_cases)} private test cases")
        return self.private_tests

    def _build_test_generation_prompt(self) -> str:
        """Build prompt for test case generation"""
        return f"""
        Generate comprehensive test cases for the following competitive programming problem:
        
        Problem Statement: {self.statement}
        Input Specification: {self.input_specification}
        Output Specification: {self.output_specification}
        
        Generate 10-15 diverse test cases including:
        - Edge cases
        - Boundary conditions
        - Large inputs
        - Corner cases
        
        Format each test case as:
        INPUT:
        <input_data>
        EXPECTED_OUTPUT:
        <expected_output>
        """

    def _parse_test_generation_response(self, response: str) -> List[TestCase]:
        """Parse model response into TestCase objects"""
        # Implement parsing logic based on your model's output format
        test_cases = []
        # Parse response and create TestCase objects
        return test_cases

    def _generate_dummy_tests(self) -> List[TestCase]:
        """Generate dummy test cases for development"""
        return [
            TestCase("1 2", "3", "Simple addition"),
            TestCase("1000000 1000000", "2000000", "Large numbers"),
            TestCase("0 0", "0", "Zero case")
        ]

    def get_sample_tests(self) -> List[TestCase]:
        """Get sample test cases"""
        return self.sample_tests

    def get_private_tests(self) -> Optional[PrivateTestSuite]:
        """Get private test suite"""
        return self.private_tests

    def to_dict(self) -> Dict[str, Any]:
        """Convert problem to dictionary for serialization"""
        return {
            "key": self.key,
            "contest_id": self.contest_id,
            "problem_id": self.problem_id,
            "statement": self.statement,
            "input_specification": self.input_specification,
            "output_specification": self.output_specification,
            "examples": self.examples,
            "sample_tests": [
                {"input": tc.input_data, "output": tc.expected_output, 
                 "description": tc.description}
                for tc in self.sample_tests
            ],
            "has_private_tests": self.private_tests is not None
        }
    