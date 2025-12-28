"""
Unit tests for PolytopicObjective class.
"""

import unittest
from datetime import datetime, timedelta
import math

from pipeline.polytopic.polytopic_objective import PolytopicObjective


class TestPolytopicObjective(unittest.TestCase):
    """Test cases for PolytopicObjective."""
    
    def setUp(self):
        """Set up test fixtures."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        self.objective = PolytopicObjective(
            id="test_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test Objective",
            description="A test objective for unit testing",
            status=ObjectiveStatus.APPROVED,
            target_date=(datetime.now() + timedelta(days=30)).isoformat(),
            tasks=["Task 1", "Task 2", "Task 3"],
            depends_on=["dep_001"],
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
    
    def test_initialization(self):
        """Test objective initialization."""
        from pipeline.objective_manager import ObjectiveLevel
        
        self.assertEqual(self.objective.id, "test_001")
        self.assertEqual(self.objective.level, ObjectiveLevel.PRIMARY)
        self.assertIsNotNone(self.objective.dimensional_profile)
        self.assertIsNotNone(self.objective.polytopic_position)
        self.assertEqual(len(self.objective.dimensional_profile), 7)
    
    def test_dimensional_profile_defaults(self):
        """Test default dimensional profile values."""
        for dim, value in self.objective.dimensional_profile.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_position_calculation(self):
        """Test 7D position calculation."""
        position = self.objective.get_dimensional_vector()
        self.assertEqual(len(position), 7)
        
        # Position should match dimensional profile values
        sorted_dims = sorted(self.objective.dimensional_profile.keys())
        for i, dim in enumerate(sorted_dims):
            self.assertEqual(position[i], self.objective.dimensional_profile[dim])
    
    def test_metrics_calculation(self):
        """Test intelligence metrics calculation."""
        self.assertGreaterEqual(self.objective.complexity_score, 0.0)
        self.assertLessEqual(self.objective.complexity_score, 1.0)
        
        self.assertGreaterEqual(self.objective.risk_score, 0.0)
        self.assertLessEqual(self.objective.risk_score, 1.0)
        
        self.assertGreaterEqual(self.objective.readiness_score, 0.0)
        self.assertLessEqual(self.objective.readiness_score, 1.0)
    
    def test_update_dimensional_profile(self):
        """Test updating dimensional profile."""
        old_value = self.objective.dimensional_profile["temporal"]
        new_value = 0.8
        
        self.objective.update_dimensional_profile("temporal", new_value)
        
        self.assertEqual(self.objective.dimensional_profile["temporal"], new_value)
        self.assertEqual(self.objective.dimensional_velocity["temporal"], new_value - old_value)
        self.assertGreater(len(self.objective.dimensional_history), 0)
    
    def test_update_invalid_dimension(self):
        """Test updating invalid dimension raises error."""
        with self.assertRaises(ValueError):
            self.objective.update_dimensional_profile("invalid_dim", 0.5)
    
    def test_update_invalid_value(self):
        """Test updating with invalid value raises error."""
        with self.assertRaises(ValueError):
            self.objective.update_dimensional_profile("temporal", 1.5)
        
        with self.assertRaises(ValueError):
            self.objective.update_dimensional_profile("temporal", -0.1)
    
    def test_distance_calculation(self):
        """Test distance calculation between objectives."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        other = PolytopicObjective(
            id="test_002",
            level=ObjectiveLevel.SECONDARY,
            title="Other Objective",
            description="Another test objective",
            status=ObjectiveStatus.PROPOSED
        )
        
        distance = self.objective.calculate_distance_to(other)
        self.assertGreaterEqual(distance, 0.0)
        self.assertLessEqual(distance, math.sqrt(7))
    
    def test_similarity_calculation(self):
        """Test similarity calculation."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        # Create identical objective
        identical = PolytopicObjective(
            id="test_003",
            level=ObjectiveLevel.PRIMARY,
            title="Identical",
            description="Identical objective",
            status=ObjectiveStatus.APPROVED
        )
        identical.dimensional_profile = self.objective.dimensional_profile.copy()
        identical.polytopic_position = self.objective.polytopic_position.copy()
        
        similarity = self.objective.calculate_similarity(identical)
        self.assertAlmostEqual(similarity, 1.0, places=5)
    
    def test_dominant_dimensions(self):
        """Test getting dominant dimensions."""
        self.objective.dimensional_profile["temporal"] = 0.9
        self.objective.dimensional_profile["error"] = 0.8
        
        dominant = self.objective.get_dominant_dimensions(threshold=0.7)
        self.assertIn("temporal", dominant)
        self.assertIn("error", dominant)
    
    def test_weak_dimensions(self):
        """Test getting weak dimensions."""
        self.objective.dimensional_profile["data"] = 0.2
        self.objective.dimensional_profile["state"] = 0.3
        
        weak = self.objective.get_weak_dimensions(threshold=0.4)
        self.assertIn("data", weak)
        self.assertIn("state", weak)
    
    def test_adjacency_check(self):
        """Test adjacency checking."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        # Create nearby objective
        nearby = PolytopicObjective(
            id="test_004",
            level=ObjectiveLevel.PRIMARY,
            title="Nearby",
            description="Nearby objective",
            status=ObjectiveStatus.APPROVED
        )
        nearby.dimensional_profile = self.objective.dimensional_profile.copy()
        nearby.dimensional_profile["temporal"] += 0.1  # Slight difference
        nearby.polytopic_position = nearby._calculate_position()
        
        self.assertTrue(self.objective.is_adjacent_to(nearby, threshold=0.5))
    
    def test_trajectory_direction(self):
        """Test trajectory direction calculation."""
        self.objective.dimensional_velocity["temporal"] = 0.1
        self.objective.dimensional_velocity["functional"] = -0.1
        self.objective.dimensional_velocity["data"] = 0.01
        
        directions = self.objective.get_trajectory_direction()
        
        self.assertEqual(directions["temporal"], "increasing")
        self.assertEqual(directions["functional"], "decreasing")
        self.assertEqual(directions["data"], "stable")
    
    def test_future_position_prediction(self):
        """Test future position prediction."""
        self.objective.dimensional_velocity["temporal"] = 0.1
        
        predicted = self.objective.predict_future_position(time_steps=2)
        
        self.assertEqual(len(predicted), 7)
        # Temporal should increase
        current_temporal = self.objective.dimensional_profile["temporal"]
        self.assertGreater(predicted[sorted(self.objective.dimensional_profile.keys()).index("temporal")],
                          current_temporal)
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        data = self.objective.to_dict()
        
        self.assertIn("dimensional_profile", data)
        self.assertIn("polytopic_position", data)
        self.assertIn("complexity_score", data)
        
        # Reconstruct
        reconstructed = PolytopicObjective.from_dict(data)
        
        self.assertEqual(reconstructed.id, self.objective.id)
        self.assertEqual(reconstructed.dimensional_profile, self.objective.dimensional_profile)
        self.assertEqual(reconstructed.complexity_score, self.objective.complexity_score)


if __name__ == '__main__':
    unittest.main()