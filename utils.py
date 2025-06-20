"""Enhanced utilities for the CP solution system"""

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

# Usage
# input_str = "This is a test string."
# print(generate_hash(input_str))
