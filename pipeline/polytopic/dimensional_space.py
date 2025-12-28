"""
Dimensional Space Navigator

Manages objectives in 7D hyperdimensional space, providing navigation,
clustering, and trajectory analysis capabilities.
"""

from typing import List, Dict, Tuple, Optional, Any
import math
from collections import defaultdict
from datetime import datetime

from .polytopic_objective import PolytopicObjective


class DimensionalSpace:
    """
    7D hyperdimensional space for objective navigation.
    
    Provides algorithms for:
    - Positioning objectives in 7D space
    - Finding nearest neighbors
    - Calculating trajectories
    - Clustering similar objectives
    - Visualizing dimensional space
    """
    
    def __init__(self, dimensions: int = 7):
        """
        Initialize dimensional space.
        
        Args:
            dimensions: Number of dimensions (default 7)
        """
        self.dimensions = dimensions
        self.objectives: Dict[str, PolytopicObjective] = {}
        self.adjacency_graph: Dict[str, List[str]] = defaultdict(list)
        self.clusters: Dict[str, List[str]] = {}  # cluster_id -> [objective_ids]
        
    def add_objective(self, objective: PolytopicObjective) -> None:
        """
        Add objective to dimensional space.
        
        Args:
            objective: Polytopic objective to add
        """
        self.objectives[objective.id] = objective
        
        # Update adjacency graph
        self._update_adjacency(objective)
        
    def remove_objective(self, objective_id: str) -> None:
        """
        Remove objective from dimensional space.
        
        Args:
            objective_id: ID of objective to remove
        """
        if objective_id in self.objectives:
            del self.objectives[objective_id]
            
            # Clean up adjacency graph
            if objective_id in self.adjacency_graph:
                del self.adjacency_graph[objective_id]
            
            for neighbors in self.adjacency_graph.values():
                if objective_id in neighbors:
                    neighbors.remove(objective_id)
    
    def _update_adjacency(self, objective: PolytopicObjective, threshold: float = 0.3) -> None:
        """
        Update adjacency graph for an objective.
        
        Args:
            objective: Objective to update adjacencies for
            threshold: Maximum distance to consider adjacent
        """
        objective_id = objective.id
        self.adjacency_graph[objective_id] = []
        
        for other_id, other_obj in self.objectives.items():
            if other_id == objective_id:
                continue
                
            if objective.is_adjacent_to(other_obj, threshold):
                self.adjacency_graph[objective_id].append(other_id)
                
                # Update reverse adjacency
                if objective_id not in self.adjacency_graph[other_id]:
                    self.adjacency_graph[other_id].append(objective_id)
        
        # Update objective's adjacent_objectives list
        objective.adjacent_objectives = self.adjacency_graph[objective_id]
    
    def calculate_position(self, objective: PolytopicObjective) -> List[float]:
        """
        Calculate position in 7D space.
        
        Args:
            objective: Objective to position
            
        Returns:
            7D position vector
        """
        return objective.get_dimensional_vector()
    
    def find_nearest_neighbors(self, objective: PolytopicObjective, k: int = 3) -> List[Tuple[PolytopicObjective, float]]:
        """
        Find k nearest objectives in 7D space.
        
        Args:
            objective: Reference objective
            k: Number of neighbors to find
            
        Returns:
            List of (objective, distance) tuples, sorted by distance
        """
        distances = []
        
        for other_id, other_obj in self.objectives.items():
            if other_id == objective.id:
                continue
                
            distance = objective.calculate_distance_to(other_obj)
            distances.append((other_obj, distance))
        
        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def find_similar_objectives(self, objective: PolytopicObjective, 
                               similarity_threshold: float = 0.7) -> List[Tuple[PolytopicObjective, float]]:
        """
        Find objectives similar to the given one.
        
        Args:
            objective: Reference objective
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of (objective, similarity) tuples
        """
        similar = []
        
        for other_id, other_obj in self.objectives.items():
            if other_id == objective.id:
                continue
                
            similarity = objective.calculate_similarity(other_obj)
            if similarity >= similarity_threshold:
                similar.append((other_obj, similarity))
        
        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar
    
    def calculate_trajectory(self, objective: PolytopicObjective, 
                           time_steps: int = 5) -> List[List[float]]:
        """
        Calculate movement trajectory in 7D space.
        
        Args:
            objective: Objective to calculate trajectory for
            time_steps: Number of future time steps to predict
            
        Returns:
            List of predicted positions at each time step
        """
        trajectory = [objective.get_dimensional_vector()]
        
        for t in range(1, time_steps + 1):
            predicted = objective.predict_future_position(t)
            trajectory.append(predicted)
        
        return trajectory
    
    def calculate_centroid(self, objective_ids: List[str]) -> List[float]:
        """
        Calculate centroid of a group of objectives.
        
        Args:
            objective_ids: List of objective IDs
            
        Returns:
            7D centroid position
        """
        if not objective_ids:
            return [0.5] * self.dimensions
        
        positions = [self.objectives[obj_id].get_dimensional_vector() 
                    for obj_id in objective_ids if obj_id in self.objectives]
        
        if not positions:
            return [0.5] * self.dimensions
        
        # Calculate mean across all dimensions
        centroid = [sum(pos[i] for pos in positions) / len(positions) 
                   for i in range(self.dimensions)]
        
        return centroid
    
    def cluster_objectives(self, max_distance: float = 0.4) -> Dict[str, List[str]]:
        """
        Cluster objectives based on dimensional proximity.
        
        Args:
            max_distance: Maximum distance within a cluster
            
        Returns:
            Dict mapping cluster_id to list of objective IDs
        """
        if not self.objectives:
            return {}
        
        # Simple agglomerative clustering
        clusters = {obj_id: [obj_id] for obj_id in self.objectives.keys()}
        
        while True:
            # Find closest pair of clusters
            min_distance = float('inf')
            merge_pair = None
            
            cluster_ids = list(clusters.keys())
            for i, c1 in enumerate(cluster_ids):
                for c2 in cluster_ids[i+1:]:
                    # Calculate distance between cluster centroids
                    centroid1 = self.calculate_centroid(clusters[c1])
                    centroid2 = self.calculate_centroid(clusters[c2])
                    
                    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(centroid1, centroid2)))
                    
                    if distance < min_distance:
                        min_distance = distance
                        merge_pair = (c1, c2)
            
            # Stop if no clusters are close enough to merge
            if min_distance > max_distance or merge_pair is None:
                break
            
            # Merge clusters
            c1, c2 = merge_pair
            clusters[c1].extend(clusters[c2])
            del clusters[c2]
        
        # Assign cluster IDs
        self.clusters = {f"cluster_{i}": members 
                        for i, members in enumerate(clusters.values())}
        
        return self.clusters
    
    def get_cluster_for_objective(self, objective_id: str) -> Optional[str]:
        """
        Get cluster ID for an objective.
        
        Args:
            objective_id: Objective ID
            
        Returns:
            Cluster ID or None if not clustered
        """
        for cluster_id, members in self.clusters.items():
            if objective_id in members:
                return cluster_id
        return None
    
    def calculate_dimensional_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics across all objectives in the space.
        
        Returns:
            Dict with dimensional statistics
        """
        if not self.objectives:
            return {}
        
        dimension_names = ["temporal", "functional", "data", "state", 
                          "error", "context", "integration"]
        
        stats = {}
        
        for i, dim_name in enumerate(dimension_names):
            values = [obj.get_dimensional_vector()[i] for obj in self.objectives.values()]
            
            stats[dim_name] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "std": math.sqrt(sum((v - sum(values)/len(values))**2 for v in values) / len(values))
            }
        
        return stats
    
    def find_optimal_next_objective(self, current_state: Dict[str, Any]) -> Optional[PolytopicObjective]:
        """
        Find the optimal next objective to work on based on current state.
        
        Args:
            current_state: Current pipeline state information
            
        Returns:
            Best objective to work on next, or None
        """
        from .polytopic_objective import PolytopicObjective
        
        if not self.objectives:
            return None
        
        # Import ObjectiveStatus for comparison
        try:
            from ..objective_manager import ObjectiveStatus
        except ImportError:
            # Fallback to string comparison
            ObjectiveStatus = None
        
        # Score each objective based on multiple factors
        scores = {}
        
        for obj_id, obj in self.objectives.items():
            # Skip completed objectives
            if ObjectiveStatus:
                if obj.status == ObjectiveStatus.COMPLETED:
                    continue
            else:
                if str(obj.status).lower() == "completed":
                    continue
            
            score = 0.0
            
            # Factor 1: Readiness (40% weight)
            score += obj.readiness_score * 0.4
            
            # Factor 2: Priority (30% weight)
            level_str = str(obj.level).upper() if hasattr(obj.level, 'value') else str(obj.level).upper()
            priority_scores = {"PRIMARY": 1.0, "SECONDARY": 0.6, "TERTIARY": 0.3}
            score += priority_scores.get(level_str, 0.5) * 0.3
            
            # Factor 3: Inverse of risk (20% weight)
            score += (1.0 - obj.risk_score) * 0.2
            
            # Factor 4: Temporal urgency (10% weight)
            score += obj.dimensional_profile["temporal"] * 0.1
            
            scores[obj_id] = score
        
        if not scores:
            return None
        
        # Return objective with highest score
        best_id = max(scores.keys(), key=lambda k: scores[k])
        return self.objectives[best_id]
    
    def visualize_space_2d(self) -> str:
        """
        Generate 2D visualization of dimensional space using PCA.
        
        Returns:
            ASCII art visualization
        """
        if not self.objectives:
            return "No objectives in space"
        
        # For simplicity, project onto first two principal dimensions
        # In a real implementation, would use proper PCA
        
        # Use temporal (x) and functional (y) as primary dimensions
        points = []
        for obj in self.objectives.values():
            x = obj.dimensional_profile["temporal"]
            y = obj.dimensional_profile["functional"]
            points.append((x, y, obj.id[:8]))  # Truncate ID for display
        
        # Create ASCII grid
        grid_size = 20
        grid = [[' ' for _ in range(grid_size)] for _ in range(grid_size)]
        
        for x, y, obj_id in points:
            grid_x = int(x * (grid_size - 1))
            grid_y = int((1 - y) * (grid_size - 1))  # Invert y for display
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y][grid_x] = '*'
        
        # Build visualization
        lines = ["Dimensional Space (Temporal vs Functional):", ""]
        lines.append("  " + "─" * grid_size)
        
        for row in grid:
            lines.append("│ " + "".join(row) + " │")
        
        lines.append("  " + "─" * grid_size)
        lines.append("  0.0" + " " * (grid_size - 7) + "1.0 (Temporal)")
        
        return "\n".join(lines)
    
    def get_space_summary(self) -> Dict[str, Any]:
        """
        Get summary of dimensional space.
        
        Returns:
            Dict with space statistics
        """
        return {
            "total_objectives": len(self.objectives),
            "dimensions": self.dimensions,
            "clusters": len(self.clusters),
            "adjacency_edges": sum(len(neighbors) for neighbors in self.adjacency_graph.values()) // 2,
            "dimensional_stats": self.calculate_dimensional_statistics(),
            "objectives_by_level": {
                "PRIMARY": len([o for o in self.objectives.values() if o.level == "PRIMARY"]),
                "SECONDARY": len([o for o in self.objectives.values() if o.level == "SECONDARY"]),
                "TERTIARY": len([o for o in self.objectives.values() if o.level == "TERTIARY"])
            }
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DimensionalSpace(dimensions={self.dimensions}, objectives={len(self.objectives)})"