"""
Unit tests for PolytopicVisualizer class.
"""

import unittest
from datetime import datetime, timedelta

from pipeline.polytopic import PolytopicObjective, DimensionalSpace, PolytopicVisualizer
from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus


class TestPolytopicVisualizations(unittest.TestCase):
    """Test cases for PolytopicVisualizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.space = DimensionalSpace(dimensions=7)
        
        # Create test objectives with different profiles
        self.obj1 = PolytopicObjective(
            id="obj_001",
            level=ObjectiveLevel.PRIMARY,
            title="High Urgency Objective",
            description="Urgent objective",
            status=ObjectiveStatus.APPROVED
        )
        self.obj1.dimensional_profile = {
            "temporal": 0.9,
            "functional": 0.7,
            "data": 0.5,
            "state": 0.6,
            "error": 0.8,
            "context": 0.5,
            "integration": 0.6
        }
        self.obj1.polytopic_position = self.obj1._calculate_position()
        self.obj1._update_metrics()
        
        self.obj2 = PolytopicObjective(
            id="obj_002",
            level=ObjectiveLevel.SECONDARY,
            title="Complex Objective",
            description="Complex objective",
            status=ObjectiveStatus.APPROVED
        )
        self.obj2.dimensional_profile = {
            "temporal": 0.4,
            "functional": 0.9,
            "data": 0.8,
            "state": 0.7,
            "error": 0.5,
            "context": 0.8,
            "integration": 0.9
        }
        self.obj2.polytopic_position = self.obj2._calculate_position()
        self.obj2._update_metrics()
        
        self.obj3 = PolytopicObjective(
            id="obj_003",
            level=ObjectiveLevel.TERTIARY,
            title="Simple Objective",
            description="Simple objective",
            status=ObjectiveStatus.APPROVED
        )
        self.obj3.dimensional_profile = {
            "temporal": 0.3,
            "functional": 0.4,
            "data": 0.3,
            "state": 0.2,
            "error": 0.3,
            "context": 0.4,
            "integration": 0.3
        }
        self.obj3.polytopic_position = self.obj3._calculate_position()
        self.obj3._update_metrics()
        
        # Add to space
        self.space.add_objective(self.obj1)
        self.space.add_objective(self.obj2)
        self.space.add_objective(self.obj3)
        
        # Create visualizer
        self.visualizer = PolytopicVisualizer(self.space)
    
    def test_visualizer_initialization(self):
        """Test visualizer initialization."""
        self.assertIsNotNone(self.visualizer)
        self.assertEqual(self.visualizer.space, self.space)
    
    def test_3d_visualization(self):
        """Test 3D space visualization."""
        viz = self.visualizer.visualize_3d_space()
        
        self.assertIsInstance(viz, str)
        self.assertIn("3D Polytopic Space", viz)
        self.assertIn("temporal", viz)
        self.assertIn("functional", viz)
        self.assertIn("data", viz)
    
    def test_3d_visualization_custom_dimensions(self):
        """Test 3D visualization with custom dimensions."""
        viz = self.visualizer.visualize_3d_space(("error", "context", "integration"))
        
        self.assertIsInstance(viz, str)
        self.assertIn("error", viz)
        self.assertIn("context", viz)
        self.assertIn("integration", viz)
    
    def test_trajectory_visualization(self):
        """Test trajectory visualization."""
        # Set velocity for obj1
        self.obj1.dimensional_velocity = {
            "temporal": 0.1,
            "functional": 0.0,
            "data": -0.05,
            "state": 0.0,
            "error": -0.1,
            "context": 0.0,
            "integration": 0.05
        }
        
        viz = self.visualizer.visualize_trajectory("obj_001", time_steps=3)
        
        self.assertIsInstance(viz, str)
        self.assertIn("Trajectory", viz)
        self.assertIn("Current Position", viz)
        self.assertIn("Predicted Trajectory", viz)
        self.assertIn("Dimensional Velocity", viz)
    
    def test_health_heatmap(self):
        """Test health heatmap visualization."""
        viz = self.visualizer.visualize_health_heatmap()
        
        self.assertIsInstance(viz, str)
        self.assertIn("Health Heatmap", viz)
        self.assertIn("obj_001", viz)
        self.assertIn("obj_002", viz)
        self.assertIn("obj_003", viz)
    
    def test_cluster_visualization(self):
        """Test cluster visualization."""
        viz = self.visualizer.visualize_clusters(max_distance=0.5)
        
        self.assertIsInstance(viz, str)
        self.assertIn("Clusters", viz)
        self.assertIn("Centroid", viz)
    
    def test_dimensional_distribution(self):
        """Test dimensional distribution visualization."""
        viz = self.visualizer.visualize_dimensional_distribution()
        
        self.assertIsInstance(viz, str)
        self.assertIn("Dimensional Distribution", viz)
        self.assertIn("TEMPORAL", viz)
        self.assertIn("FUNCTIONAL", viz)
        self.assertIn("mean=", viz)
        self.assertIn("std=", viz)
    
    def test_adjacency_graph(self):
        """Test adjacency graph visualization."""
        viz = self.visualizer.visualize_adjacency_graph(max_objectives=5)
        
        self.assertIsInstance(viz, str)
        self.assertIn("Adjacency Graph", viz)
    
    def test_comprehensive_report(self):
        """Test comprehensive visualization report."""
        report = self.visualizer.generate_comprehensive_report()
        
        self.assertIsInstance(report, str)
        self.assertIn("COMPREHENSIVE POLYTOPIC VISUALIZATION REPORT", report)
        self.assertIn("SPACE SUMMARY", report)
        self.assertIn("3D SPACE VISUALIZATION", report)
        self.assertIn("HEALTH HEATMAP", report)
        self.assertIn("CLUSTERS", report)
        self.assertIn("DIMENSIONAL DISTRIBUTION", report)
        self.assertIn("ADJACENCY GRAPH", report)
    
    def test_empty_space_handling(self):
        """Test visualization with empty space."""
        empty_space = DimensionalSpace(dimensions=7)
        empty_visualizer = PolytopicVisualizer(empty_space)
        
        viz = empty_visualizer.visualize_3d_space()
        self.assertIn("No objectives", viz)
        
        viz = empty_visualizer.visualize_health_heatmap()
        self.assertIn("No objectives", viz)


if __name__ == '__main__':
    unittest.main()