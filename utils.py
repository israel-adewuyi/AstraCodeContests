"""Enhanced utilities for the CP solution system"""
import re
import hashlib
import json
import logging
from typing import Any, Dict
from datetime import datetime

def generate_hash(input_string: str) -> str:
    """Generates a unique identifier for each contest problem"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input_string.encode('utf-8'))
    return sha256_hash.hexdigest()[:16]  # Use first 16 chars for readability

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if log_file:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format
        )

def save_json(data: Any, filepath: str):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def create_timestamp() -> str:
    """Create timestamp string"""
    return datetime.now().isoformat()

def format_execution_time(seconds: float) -> str:
    """Format execution time in human readable format"""
    if seconds < 1:
        return f"{seconds*1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"

def get_inputs(text: str):
    # Split the text by "INPUT:" (case-sensitive)
    parts = text.split("INPUT:")
    
    # Remove any leading/trailing whitespace and filter out empty strings
    input_blocks = [block.strip() for block in parts[1:] if block.strip()]
    
    return input_blocks

def extract_text_after_think(text):
    """
    Extracts the text after the thinking token.
    
    Parameters:
    text (str): The input string containing the 'Thinking' token.
    
    Returns:
    str: The part of the text after <think>, or an empty string if not found.
    """
    # Split the text at 'Thinking'
    parts = text.split("</think>", 1)
    
    # Return the part after 'Thinking' if it exists, else return an empty string
    if len(parts) > 1:
        return parts[1].strip()
    else:
        return ""

def extract_test_cases(text):
    """
    Extracts the test cases from the given text.
    """
    return text.split("INPUT:\n")

def extract_python_code(text):
    """
    Extracts the first Python code snippet from the given text.
    
    Parameters:
        text (str): The input string containing potential Python code snippets.
    
    Returns:
        str: The extracted Python code, or None if no match is found.
    """
    # Use regular expression to find the first Python code block
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    
    # If a match is found, return the code with leading/trailing whitespace stripped
    if match:
        return match.group(1).strip()
    else:
        return None
