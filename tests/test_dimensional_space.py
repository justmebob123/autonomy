"""
Unit tests for DimensionalSpace class.
"""

import unittest
from datetime import datetime, timedelta

from pipeline.polytopic.polytopic_objective import PolytopicObjective
from pipeline.polytopic.dimensional_space import DimensionalSpace


class TestDimensionalSpace(unittest.TestCase):
    """Test cases for DimensionalSpace."""
    
    def setUp(self):
        """Set up test fixtures."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        self.space = DimensionalSpace(dimensions=7)
        
        # Create test objectives
        self.obj1 = PolytopicObjective(
            id="obj_001",
            level=ObjectiveLevel.PRIMARY,
            title="Objective 1",
            description="First test objective",
            status=ObjectiveStatus.APPROVED
        )
        self.obj1.dimensional_profile = {
            "temporal": 0.8,
            "functional": 0.6,
            "data": 0.5,
            "state": 0.4,
            "error": 0.3,
            "context": 0.5,
            "integration": 0.6
        }
        self.obj1.polytopic_position = self.obj1._calculate_position()
        
        self.obj2 = PolytopicObjective(
            id="obj_002",
            level=ObjectiveLevel.SECONDARY,
            title="Objective 2",
            description="Second test objective",
            status=ObjectiveStatus.PROPOSED
        )
        self.obj2.dimensional_profile = {
            "temporal": 0.3,
            "functional": 0.7,
            "data": 0.6,
            "state": 0.5,
            "error": 0.4,
            "context": 0.6,
            "integration": 0.7
        }
        self.obj2.polytopic_position = self.obj2._calculate_position()
        
        self.obj3 = PolytopicObjective(
            id="obj_003",
            level=ObjectiveLevel.TERTIARY,
            title="Objective 3",
            description="Third test objective",
            status=ObjectiveStatus.PROPOSED
        )
        self.obj3.dimensional_profile = {
            "temporal": 0.9,
            "functional": 0.5,
            "data": 0.4,
            "state": 0.3,
            "error": 0.2,
            "context": 0.4,
            "integration": 0.5
        }
        self.obj3.polytopic_position = self.obj3._calculate_position()
    
    def test_initialization(self):
        """Test space initialization."""
        self.assertEqual(self.space.dimensions, 7)
        self.assertEqual(len(self.space.objectives), 0)
    
    def test_add_objective(self):
        """Test adding objective to space."""
        self.space.add_objective(self.obj1)
        
        self.assertEqual(len(self.space.objectives), 1)
        self.assertIn("obj_001", self.space.objectives)
    
    def test_remove_objective(self):
        """Test removing objective from space."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        
        self.space.remove_objective("obj_001")
        
        self.assertEqual(len(self.space.objectives), 1)
        self.assertNotIn("obj_001", self.space.objectives)
    
    def test_adjacency_update(self):
        """Test adjacency graph updates."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj3)  # obj3 is similar to obj1 in temporal
        
        # Check if adjacency was calculated
        self.assertIn("obj_001", self.space.adjacency_graph)
    
    def test_find_nearest_neighbors(self):
        """Test finding nearest neighbors."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        neighbors = self.space.find_nearest_neighbors(self.obj1, k=2)
        
        self.assertEqual(len(neighbors), 2)
        self.assertTrue(all(isinstance(obj, PolytopicObjective) for obj, _ in neighbors))
        self.assertTrue(all(isinstance(dist, float) for _, dist in neighbors))
        
        # Distances should be sorted
        distances = [dist for _, dist in neighbors]
        self.assertEqual(distances, sorted(distances))
    
    def test_find_similar_objectives(self):
        """Test finding similar objectives."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        similar = self.space.find_similar_objectives(self.obj1, similarity_threshold=0.5)
        
        self.assertIsInstance(similar, list)
        for obj, sim in similar:
            self.assertIsInstance(obj, PolytopicObjective)
            self.assertGreaterEqual(sim, 0.5)
            self.assertLessEqual(sim, 1.0)
    
    def test_calculate_trajectory(self):
        """Test trajectory calculation."""
        self.obj1.dimensional_velocity = {
            "temporal": 0.1,
            "functional": 0.0,
            "data": -0.05,
            "state": 0.0,
            "error": 0.0,
            "context": 0.0,
            "integration": 0.0
        }
        
        self.space.add_objective(self.obj1)
        
        trajectory = self.space.calculate_trajectory(self.obj1, time_steps=3)
        
        self.assertEqual(len(trajectory), 4)  # Current + 3 future
        self.assertTrue(all(len(pos) == 7 for pos in trajectory))
    
    def test_calculate_centroid(self):
        """Test centroid calculation."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        
        centroid = self.space.calculate_centroid(["obj_001", "obj_002"])
        
        self.assertEqual(len(centroid), 7)
        self.assertTrue(all(0.0 <= val <= 1.0 for val in centroid))
    
    def test_cluster_objectives(self):
        """Test objective clustering."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        clusters = self.space.cluster_objectives(max_distance=0.5)
        
        self.assertIsInstance(clusters, dict)
        self.assertGreater(len(clusters), 0)
        
        # All objectives should be in some cluster
        all_clustered = []
        for members in clusters.values():
            all_clustered.extend(members)
        
        self.assertEqual(set(all_clustered), {"obj_001", "obj_002", "obj_003"})
    
    def test_get_cluster_for_objective(self):
        """Test getting cluster for objective."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        
        self.space.cluster_objectives(max_distance=0.5)
        
        cluster_id = self.space.get_cluster_for_objective("obj_001")
        self.assertIsNotNone(cluster_id)
        self.assertIn("obj_001", self.space.clusters[cluster_id])
    
    def test_dimensional_statistics(self):
        """Test dimensional statistics calculation."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        stats = self.space.calculate_dimensional_statistics()
        
        self.assertEqual(len(stats), 7)
        
        for dim_stats in stats.values():
            self.assertIn("mean", dim_stats)
            self.assertIn("min", dim_stats)
            self.assertIn("max", dim_stats)
            self.assertIn("std", dim_stats)
    
    def test_find_optimal_next_objective(self):
        """Test finding optimal next objective."""
        from pipeline.objective_manager import ObjectiveStatus
        
        self.obj1.status = ObjectiveStatus.APPROVED
        self.obj2.status = ObjectiveStatus.PROPOSED
        self.obj3.status = ObjectiveStatus.COMPLETED
        
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        optimal = self.space.find_optimal_next_objective({})
        
        self.assertIsNotNone(optimal)
        self.assertNotEqual(optimal.status, ObjectiveStatus.COMPLETED)
    
    def test_visualize_space_2d(self):
        """Test 2D visualization generation."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        
        visualization = self.space.visualize_space_2d()
        
        self.assertIsInstance(visualization, str)
        self.assertIn("Dimensional Space", visualization)
    
    def test_get_space_summary(self):
        """Test space summary generation."""
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        summary = self.space.get_space_summary()
        
        self.assertEqual(summary["total_objectives"], 3)
        self.assertEqual(summary["dimensions"], 7)
        self.assertIn("dimensional_stats", summary)
        self.assertIn("objectives_by_level", summary)


if __name__ == '__main__':
    unittest.main()