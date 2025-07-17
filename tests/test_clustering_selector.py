import unittest
import sys
import os
import logging
import random

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clustering_selector import ClusteringSelector, Cluster

class TestClusteringSelector(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh ClusteringSelector instance for each test"""
        # Disable logging for tests
        logging.disable(logging.CRITICAL)
        
        # Set a fixed seed for random to make tests deterministic
        random.seed(42)
        
        # Create a selector with default threshold
        self.selector = ClusteringSelector()
    
    def tearDown(self):
        """Clean up after each test"""
        # Re-enable logging
        logging.disable(logging.NOTSET)
    
    def test_are_solutions_similar_identical(self):
        """Test similarity check with identical outputs"""
        outputs1 = ["1", "2", "3"]
        outputs2 = ["1", "2", "3"]
        
        self.assertTrue(self.selector._are_solutions_similar(outputs1, outputs2))
    
    def test_are_solutions_similar_different_length(self):
        """Test similarity check with different length outputs"""
        outputs1 = ["1", "2", "3"]
        outputs2 = ["1", "2"]
        
        self.assertFalse(self.selector._are_solutions_similar(outputs1, outputs2))
    
    def test_are_solutions_similar_below_threshold(self):
        """Test similarity check with similarity below threshold"""
        outputs1 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        outputs2 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "different"]
        
        # 9/10 = 0.9, which is exactly at the threshold, so it should be similar
        self.assertTrue(self.selector._are_solutions_similar(outputs1, outputs2))
        
        # Create a selector with higher threshold
        selector_strict = ClusteringSelector(similarity_threshold=0.95)
        self.assertFalse(selector_strict._are_solutions_similar(outputs1, outputs2))
    
    def test_get_representative_output(self):
        """Test getting representative output for a cluster"""
        solution_outputs = {
            "sol1": ["1", "2", "3"],
            "sol2": ["1", "2", "4"],
            "sol3": ["1", "3", "3"]
        }
        solution_ids = ["sol1", "sol2", "sol3"]
        
        # The representative output should be the first solution's output
        expected = str(solution_outputs["sol1"])
        result = self.selector._get_representative_output(solution_outputs, solution_ids)
        
        self.assertEqual(result, expected)
    
    def test_cluster_solutions_single_cluster(self):
        """Test clustering with all solutions in one cluster"""
        solution_outputs = {
            "sol1": ["1", "2", "3"],
            "sol2": ["1", "2", "3"],
            "sol3": ["1", "2", "3"]
        }
        
        clusters = self.selector._cluster_solutions(solution_outputs)
        
        # Should have only one cluster with all solutions
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].size, 3)
        self.assertCountEqual(clusters[0].solutions, ["sol1", "sol2", "sol3"])
    
    def test_cluster_solutions_multiple_clusters(self):
        """Test clustering with multiple clusters"""
        solution_outputs = {
            "sol1": ["1", "2", "3"],
            "sol2": ["1", "2", "3"],
            "sol3": ["4", "5", "6"],
            "sol4": ["4", "5", "6"],
            "sol5": ["7", "8", "9"]
        }
        
        clusters = self.selector._cluster_solutions(solution_outputs)
        
        # Should have three clusters
        self.assertEqual(len(clusters), 3)
        
        # Sort clusters by size to make testing easier
        clusters.sort(key=lambda c: c.size, reverse=True)
        
        # First cluster should have sol1 and sol2
        self.assertEqual(clusters[0].size, 2)
        self.assertCountEqual(clusters[0].solutions, ["sol1", "sol2"])
        
        # Second cluster should have sol3 and sol4
        self.assertEqual(clusters[1].size, 2)
        self.assertCountEqual(clusters[1].solutions, ["sol3", "sol4"])
        
        # Third cluster should have sol5
        self.assertEqual(clusters[2].size, 1)
        self.assertCountEqual(clusters[2].solutions, ["sol5"])
    
    def test_select_best(self):
        """Test selecting the best solution"""
        solution_outputs = {
            "sol1": ["1", "2", "3"],
            "sol2": ["1", "2", "3"],
            "sol3": ["1", "2", "3"],
            "sol4": ["4", "5", "6"],
            "sol5": ["7", "8", "9"]
        }
        
        result = self.selector.select_best(solution_outputs)
        
        # Should select from the largest cluster (sol1, sol2, sol3)
        self.assertIn(result["selected_solution_id"], ["sol1", "sol2", "sol3"])
        self.assertEqual(result["cluster_size"], 3)
        self.assertEqual(result["total_clusters"], 3)
        self.assertEqual(result["cluster_info"]["id"], "cluster_0")
    
    def test_select_best_with_random_seed(self):
        """Test that selection is deterministic with fixed random seed"""
        solution_outputs = {
            "sol1": ["1", "2", "3"],
            "sol2": ["1", "2", "3"],
            "sol3": ["1", "2", "3"],
            "sol4": ["4", "5", "6"],
            "sol5": ["7", "8", "9"]
        }
        
        # With seed 42, it should consistently select the same solution
        random.seed(42)
        result1 = self.selector.select_best(solution_outputs)
        
        random.seed(42)
        result2 = self.selector.select_best(solution_outputs)
        
        self.assertEqual(result1["selected_solution_id"], result2["selected_solution_id"])

if __name__ == '__main__':
    unittest.main()