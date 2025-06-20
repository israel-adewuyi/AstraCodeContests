import logging
from typing import List, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass
import random

@dataclass
class Cluster:
    id: str
    solutions: List[str]
    representative_output: str
    size: int

class ClusteringSelector:
    """Groups solutions by output similarity and selects the best candidate"""
    
    def __init__(self, similarity_threshold: float = 0.9):
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
    
    def select_best(self, execution_results: Dict[str, List]) -> Dict:
        """Select the best solution using clustering approach"""
        self.logger.info("Starting clustering and selection process")
        
        # Extract outputs for each solution
        solution_outputs = self._extract_solution_outputs(execution_results)
        
        # Group solutions by output similarity
        clusters = self._cluster_solutions(solution_outputs)
        
        # Find the largest cluster
        largest_cluster = max(clusters, key=lambda c: c.size)
        
        # Select random solution from largest cluster
        selected_solution_id = random.choice(largest_cluster.solutions)
        
        self.logger.info(f"Selected solution {selected_solution_id} from cluster of size {largest_cluster.size}")
        
        return {
            "selected_solution_id": selected_solution_id,
            "cluster_size": largest_cluster.size,
            "total_clusters": len(clusters),
            "cluster_info": {
                "id": largest_cluster.id,
                "representative_output": largest_cluster.representative_output
            }
        }
    
    def _extract_solution_outputs(self, execution_results: Dict[str, List]) -> Dict[str, List[str]]:
        """Extract outputs for each solution across all test cases"""
        solution_outputs = {}
        
        for solution_id, results in execution_results.items():
            outputs = []
            for result in results:
                if result.status.value == "success":
                    outputs.append(result.output)
                else:
                    # Use error status as output for failed executions
                    outputs.append(f"ERROR_{result.status.value}")
            
            solution_outputs[solution_id] = outputs
        
        return solution_outputs
    
    def _cluster_solutions(self, solution_outputs: Dict[str, List[str]]) -> List[Cluster]:
        """Group solutions by output similarity"""
        clusters = []
        processed_solutions = set()
        
        solution_ids = list(solution_outputs.keys())
        
        for i, solution_id in enumerate(solution_ids):
            if solution_id in processed_solutions:
                continue
            
            # Start new cluster
            cluster_solutions = [solution_id]
            processed_solutions.add(solution_id)
            
            # Find similar solutions
            for j, other_solution_id in enumerate(solution_ids[i+1:], i+1):
                if other_solution_id in processed_solutions:
                    continue
                
                if self._are_solutions_similar(
                    solution_outputs[solution_id],
                    solution_outputs[other_solution_id]
                ):
                    cluster_solutions.append(other_solution_id)
                    processed_solutions.add(other_solution_id)
            
            # Create cluster
            cluster = Cluster(
                id=f"cluster_{len(clusters)}",
                solutions=cluster_solutions,
                representative_output=self._get_representative_output(
                    solution_outputs, cluster_solutions
                ),
                size=len(cluster_solutions)
            )
            clusters.append(cluster)
        
        self.logger.info(f"Created {len(clusters)} clusters")
        return clusters
    
    def _are_solutions_similar(self, outputs1: List[str], outputs2: List[str]) -> bool:
        """Check if two solutions produce similar outputs"""
        if len(outputs1) != len(outputs2):
            return False
        
        # Calculate similarity based on matching outputs
        matching_outputs = sum(1 for o1, o2 in zip(outputs1, outputs2) if o1 == o2)
        similarity = matching_outputs / len(outputs1)
        
        return similarity >= self.similarity_threshold
    
    def _get_representative_output(self, solution_outputs: Dict[str, List[str]], 
                                 solution_ids: List[str]) -> str:
        """Get representative output for a cluster"""
        # Use the first solution's outputs as representative
        return str(solution_outputs[solution_ids[0]]) 