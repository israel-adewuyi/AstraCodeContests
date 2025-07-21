# Source : https://github.com/volcengine/verl/tree/main/verl/utils/reward_score/sandbox_fusion
#
#
# Copyright 2025 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import traceback

from typing import Dict, Union, Any, List
from .utils import check_correctness

"""
Verify code correctness using the Sandbox Fusion (https://github.com/bytedance/SandboxFusion).
You can either deploy the sandbox_fusion service yourself or use the
FaaS service provided by public cloud, eg: volcengine.com.
"""
logger = logging.getLogger(__name__)


def make_result(score: float, feedback: Union[str, Dict[str, Any]]) -> Dict[str, Union[float, str, Dict, List]]:
    return {
        'score': score,
        'feedback': feedback
    }

def compute_score(sandbox_fusion_url, concurrent_semaphore, completion, test_cases, continuous=False, timeout=5) -> Dict[str, Union[float, str, dict, List]]:
    """
    Computes the code score using the remote sandbox API.

    Args:
        sandbox_fusion_url: The URL of the sandbox_fusion service, eg: "https://<your service endpoint>/run_code"

        completion: The completion string containing the code.
        test_cases: JSON string or dictionary containing "inputs" and "outputs".
        continuous: Whether to compute a continuous score (based on the first N test cases).
        timeout: Timeout for each test case.

    Returns:
        A tuple (score, metadata_list).
        score: Float score (0.0 to 1.0).
        metadata_list: List containing execution metadata for each test case.
    """
    solution = completion
    if "```python" in completion:
        solution = completion.split("```python")[-1].split("```")[0]
    elif "```" in completion:
        # Handle cases like ```\ncode\n```
        parts = completion.split("```")
        if len(parts) >= 2:
            solution = parts[1]
            # Remove potential language specifier like 'python\n'
            if "\n" in solution:
                first_line, rest = solution.split("\n", 1)
                if first_line.strip().isalpha():  # Simple check for language name
                    solution = rest
    else:
        return make_result(0.0, [{"error": "Invalid completion (missing code block)"}])

    try:
        if not isinstance(test_cases, dict):
            try:
                if isinstance(test_cases, list):
                    test_cases = test_cases[0]
                else:
                    test_cases = json.loads(test_cases)[0]
                logger.info(f"There are {len(test_cases)} private test cases to be evaluated.")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse test_cases JSON: {e}")
                return make_result(0.0, [{"error": "Invalid test_cases JSON format"}])

        if not test_cases or "input" not in test_cases or "output" not in test_cases:
            logger.error("Invalid test_cases structure.")
            return make_result(0.0, [{"error": "Invalid test_cases structure (missing inputs/outputs)"}])

        # Check all test cases
        # Note: The return value of check_correctness might need adaptation here
        # Assume check_correctness returns (results_list, metadata_list)
        # results_list contains True, False, or error codes (-1, -2, -3, etc.)
        res_list, metadata_list = check_correctness(sandbox_fusion_url=sandbox_fusion_url, in_outs=test_cases, generation=solution, timeout=timeout, concurrent_semaphore=concurrent_semaphore)

        # Calculate score
        if not res_list:  # If there are no results (e.g., invalid input)
            return make_result(0.0, metadata_list)

        if continuous:
            # Calculate pass rate for the first N (e.g., 10) test cases
            num_to_consider = min(len(res_list), 10)
            if num_to_consider == 0:
                score = 0.0
            else:
                passed_count = sum(1 for r in res_list[:num_to_consider] if r is True)
                score = passed_count / num_to_consider
            # Return all metadata, even if score is based on the first N
            final_metadata = metadata_list
        else:
            # Calculate pass rate for all test cases
            passed_count = sum(1 for r in res_list if r is True)
            total_cases = len(res_list)
            score = passed_count / total_cases if total_cases > 0 else 0.0
            final_metadata = metadata_list

    except Exception as e:
        logger.error(f"Error during compute_score: {e}")
        traceback.print_exc()
        score = 0.0
        # Try to return partial metadata if available, otherwise return error info
        final_metadata = metadata_list if "metadata_list" in locals() else [{"error": f"Unhandled exception: {e}"}]

    # Ensure float and list are returned
    return make_result(float(score), final_metadata if isinstance(final_metadata, list) else [final_metadata])
