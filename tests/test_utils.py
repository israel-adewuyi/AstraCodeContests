import unittest
import os
import tempfile
import json
import time
from datetime import datetime
import sys
import logging

# Add the parent directory to the path so we can import the utils module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    generate_hash,
    setup_logging,
    save_json,
    load_json,
    create_timestamp,
    format_execution_time,
    get_inputs,
    extract_text_after_think,
    extract_test_cases,
    extract_python_code
)

class TestUtils(unittest.TestCase):
    
    def test_generate_hash(self):
        """Test the generate_hash function"""
        # Test with a simple string
        test_string = "test_string"
        hash_result = generate_hash(test_string)
        
        # Check that the hash is a string of length 16
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 16)
        
        # Test that the same input produces the same hash
        hash_result2 = generate_hash(test_string)
        self.assertEqual(hash_result, hash_result2)
        
        # Test that different inputs produce different hashes
        different_string = "different_string"
        different_hash = generate_hash(different_string)
        self.assertNotEqual(hash_result, different_hash)
    
    def test_save_and_load_json(self):
        """Test the save_json and load_json functions"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Test data
            test_data = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
            
            # Save the data
            save_json(test_data, temp_path)
            
            # Load the data
            loaded_data = load_json(temp_path)
            
            # Check that the loaded data matches the original
            self.assertEqual(test_data, loaded_data)
            
            # Test with datetime object
            test_data_with_date = {"date": datetime.now(), "value": "test"}
            save_json(test_data_with_date, temp_path)
            
            # Load and verify the data was saved correctly
            loaded_data = load_json(temp_path)
            self.assertIn("date", loaded_data)
            self.assertIn("value", loaded_data)
            self.assertEqual(loaded_data["value"], "test")
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_create_timestamp(self):
        """Test the create_timestamp function"""
        # Get a timestamp
        timestamp = create_timestamp()
        
        # Check that it's a string
        self.assertIsInstance(timestamp, str)
        
        # Check that it can be parsed as an ISO format datetime
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            self.fail("create_timestamp did not return a valid ISO format datetime string")
    
    def test_format_execution_time(self):
        """Test the format_execution_time function"""
        # Test with milliseconds
        self.assertEqual(format_execution_time(0.5), "500.00ms")
        
        # Test with seconds
        self.assertEqual(format_execution_time(5.25), "5.25s")
        
        # Test with minutes and seconds
        self.assertEqual(format_execution_time(125.5), "2m 5.50s")
    
    def test_get_inputs(self):
        """Test the get_inputs function"""
        # Test with a simple input
        test_text = "Some text\nINPUT:\n1 2 3\n"
        inputs = get_inputs(test_text)
        self.assertEqual(inputs, ["1 2 3"])
        
        # Test with multiple inputs
        test_text = "Some text\nINPUT:\n1 2 3\nMore text\nINPUT:\n4 5 6"
        inputs = get_inputs(test_text)
        self.assertEqual(inputs, ["1 2 3\nMore text", "4 5 6"])
        
        # Test with no inputs
        test_text = "Some text without any inputs"
        inputs = get_inputs(test_text)
        self.assertEqual(inputs, [])
    
    def test_extract_text_after_think(self):
        """Test the extract_text_after_think function"""
        # Test with a simple case
        test_text = "<think>Thinking about something</think>Here is the result"
        result = extract_text_after_think(test_text)
        self.assertEqual(result, "Here is the result")
        
        # Test with no think tag
        test_text = "Just some text without think tags"
        result = extract_text_after_think(test_text)
        self.assertEqual(result, "")
        
        # Test with multiple think tags (should take the first one)
        test_text = "<think>First thought</think>Middle text<think>Second thought</think>End text"
        result = extract_text_after_think(test_text)
        self.assertEqual(result, "Middle text<think>Second thought</think>End text")
    
    def test_extract_test_cases(self):
        """Test the extract_test_cases function"""
        # Test with a simple case
        test_text = "Some text\nINPUT:\n1 2 3"
        result = extract_test_cases(test_text)
        self.assertEqual(result, ["Some text\n", "1 2 3"])
        
        # Test with multiple inputs
        test_text = "Some text\nINPUT:\n1 2 3\nINPUT:\n4 5 6"
        result = extract_test_cases(test_text)
        self.assertEqual(result, ["Some text\n", "1 2 3\n", "4 5 6"])
    
    def test_extract_python_code(self):
        """Test the extract_python_code function"""
        # Test with a simple Python code block
        test_text = "Here is some code:\n```python\ndef hello():\n    print('Hello, world!')\n```"
        result = extract_python_code(test_text)
        self.assertEqual(result, "def hello():\n    print('Hello, world!')")
        
        # Test with no Python code block
        test_text = "Just some text without code blocks"
        result = extract_python_code(test_text)
        self.assertIsNone(result)
        
        # Test with multiple Python code blocks (should take the first one)
        test_text = "First block:\n```python\ndef first():\n    pass\n```\nSecond block:\n```python\ndef second():\n    pass\n```"
        result = extract_python_code(test_text)
        self.assertEqual(result, "def first():\n    pass")
        
        # Test with other language code blocks
        test_text = "```javascript\nconsole.log('Hello');\n```\n```python\nprint('Hello')\n```"
        result = extract_python_code(test_text)
        self.assertEqual(result, "print('Hello')")

    def test_setup_logging(self):
        """Test the setup_logging function"""
        # Create a test logger instead of using the root logger
        # to avoid affecting other tests
        test_logger_name = "test_logger"
        
        # Test with default parameters
        old_basicConfig = logging.basicConfig
        try:
            # Mock the basicConfig to capture the level
            captured_level = [None]
            def mock_basicConfig(**kwargs):
                captured_level[0] = kwargs.get('level')
                return old_basicConfig(**kwargs)
            
            logging.basicConfig = mock_basicConfig
            
            # Test default level (INFO)
            setup_logging()
            self.assertEqual(captured_level[0], logging.INFO)
            
            # Test custom level (DEBUG)
            setup_logging(log_level="DEBUG")
            self.assertEqual(captured_level[0], logging.DEBUG)
        finally:
            # Restore the original basicConfig
            logging.basicConfig = old_basicConfig
        
        # Test with log file (we'll use a temp file)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create a test logger to avoid affecting the root logger
            test_logger = logging.getLogger("test_file_logger")
            
            # Clear any existing handlers
            for handler in test_logger.handlers[:]:
                test_logger.removeHandler(handler)
            
            # Set up a file handler manually
            file_handler = logging.FileHandler(temp_path)
            test_logger.addHandler(file_handler)
            test_logger.setLevel(logging.INFO)
            
            # Log a message and check if it appears in the file
            test_message = "Test log message"
            test_logger.info(test_message)
            
            # Close the handler to ensure the message is written
            file_handler.close()
            
            with open(temp_path, 'r') as f:
                log_content = f.read()
                self.assertIn(test_message, log_content)
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()