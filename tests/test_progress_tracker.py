import unittest
import sys
import os
import threading
import time

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from progress_tracker import ProgressTracker

class TestProgressTracker(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh ProgressTracker instance for each test"""
        self.tracker = ProgressTracker()
    
    def test_update_and_get(self):
        """Test updating and retrieving progress"""
        # Test initial state
        self.assertEqual(self.tracker.get("problem1"), {})
        
        # Test updating with status only
        self.tracker.update("problem1", "in_progress")
        self.assertEqual(self.tracker.get("problem1"), {"status": "in_progress"})
        
        # Test updating with status and detail
        detail = {"step": 1, "message": "Processing"}
        self.tracker.update("problem1", "in_progress", detail)
        self.assertEqual(
            self.tracker.get("problem1"), 
            {"status": "in_progress", "detail": detail}
        )
        
        # Test updating a different problem
        self.tracker.update("problem2", "pending")
        self.assertEqual(self.tracker.get("problem2"), {"status": "pending"})
        
        # Ensure problem1 is still intact
        self.assertEqual(
            self.tracker.get("problem1"), 
            {"status": "in_progress", "detail": detail}
        )
    
    def test_reset_specific(self):
        """Test resetting a specific problem"""
        # Set up some data
        self.tracker.update("problem1", "completed", {"result": "success"})
        self.tracker.update("problem2", "failed", {"error": "timeout"})
        
        # Reset problem1
        self.tracker.reset("problem1")
        
        # Check that problem1 is gone but problem2 remains
        self.assertEqual(self.tracker.get("problem1"), {})
        self.assertEqual(
            self.tracker.get("problem2"), 
            {"status": "failed", "detail": {"error": "timeout"}}
        )
    
    def test_reset_all(self):
        """Test resetting all problems"""
        # Set up some data
        self.tracker.update("problem1", "completed", {"result": "success"})
        self.tracker.update("problem2", "failed", {"error": "timeout"})
        
        # Reset all
        self.tracker.reset()
        
        # Check that all problems are gone
        self.assertEqual(self.tracker.get("problem1"), {})
        self.assertEqual(self.tracker.get("problem2"), {})
        self.assertEqual(self.tracker.all(), {})
    
    def test_all(self):
        """Test retrieving all progress data"""
        # Set up some data
        self.tracker.update("problem1", "completed", {"result": "success"})
        self.tracker.update("problem2", "failed", {"error": "timeout"})
        
        # Get all data
        all_data = self.tracker.all()
        
        # Check the data
        self.assertEqual(len(all_data), 2)
        self.assertEqual(
            all_data["problem1"], 
            {"status": "completed", "detail": {"result": "success"}}
        )
        self.assertEqual(
            all_data["problem2"], 
            {"status": "failed", "detail": {"error": "timeout"}}
        )
    
    def test_thread_safety(self):
        """Test thread safety of the ProgressTracker"""
        # Number of threads to create
        num_threads = 10
        # Number of updates per thread
        updates_per_thread = 100
        
        # Function to run in each thread
        def update_progress(thread_id):
            for i in range(updates_per_thread):
                problem_key = f"problem{thread_id}"
                status = f"status{i}"
                detail = {"thread": thread_id, "iteration": i}
                self.tracker.update(problem_key, status, detail)
                # Small sleep to increase chance of thread interleaving
                time.sleep(0.0001)
        
        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=update_progress, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that each problem has the final update from its thread
        all_data = self.tracker.all()
        self.assertEqual(len(all_data), num_threads)
        
        for i in range(num_threads):
            problem_key = f"problem{i}"
            expected_status = f"status{updates_per_thread-1}"
            expected_detail = {"thread": i, "iteration": updates_per_thread-1}
            
            self.assertIn(problem_key, all_data)
            self.assertEqual(all_data[problem_key]["status"], expected_status)
            self.assertEqual(all_data[problem_key]["detail"], expected_detail)

if __name__ == '__main__':
    unittest.main()