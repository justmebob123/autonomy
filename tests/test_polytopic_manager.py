"""
Unit tests for PolytopicObjectiveManager class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from pipeline.polytopic.polytopic_manager import PolytopicObjectiveManager
from pipeline.polytopic.polytopic_objective import PolytopicObjective
from pipeline.state.manager import StateManager, PipelineState


class TestPolytopicObjectiveManager(unittest.TestCase):
    """Test cases for PolytopicObjectiveManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        
        # Create state manager
        self.state_manager = StateManager(str(self.project_dir))
        
        # Create manager
        self.manager = PolytopicObjectiveManager(str(self.project_dir), self.state_manager)
        
        # Create test objective file
        self._create_test_objective_file()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def _create_test_objective_file(self):
        """Create a test objective markdown file."""
        content = """# Primary Objectives

## 1. Test Objective

**ID**: primary_001
**Status**: approved
**Target Date**: 2024-12-31
**Priority**: PRIMARY

### Description
This is a test objective with state management and error handling requirements.
It involves integration with multiple components and requires careful context management.

### Tasks
- [ ] Implement state store (src/state.py)
- [ ] Add error handling (src/errors.py)
- [ ] Create integration tests (tests/integration.py)
- [ ] Update documentation

### Dependencies
- secondary_001
- secondary_002

### Acceptance Criteria
- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Security review passed

### Dimensional Profile
- Temporal: 0.7 (moderate urgency)
- Functional: 0.8 (high complexity)
- Data: 0.6 (moderate dependencies)
- State: 0.9 (complex state management)
- Error: 0.7 (higher risk)
- Context: 0.6 (moderate context)
- Integration: 0.8 (high integration needs)

---
"""
        
        objectives_file = self.project_dir / "PRIMARY_OBJECTIVES.md"
        objectives_file.write_text(content)
    
    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager.dimensional_space)
        self.assertEqual(self.manager.dimensional_space.dimensions, 7)
    
    def test_load_objectives(self):
        """Test loading objectives from files."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        objectives_by_level = self.manager.load_objectives(state)
        
        self.assertIsInstance(objectives_by_level, dict)
        
        # Check that objectives are PolytopicObjective instances
        for level_objectives in objectives_by_level.values():
            for obj in level_objectives.values():
                self.assertIsInstance(obj, PolytopicObjective)
                self.assertIsNotNone(obj.dimensional_profile)
                self.assertIsNotNone(obj.polytopic_position)
    
    def test_calculate_dimensional_profile(self):
        """Test dimensional profile calculation."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        obj = PolytopicObjective(
            id="test_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test",
            description="A test objective with state management and error handling",
            status=ObjectiveStatus.APPROVED,
            target_date=(datetime.now() + timedelta(days=7)).isoformat(),
            tasks=["Task 1 (file.py)", "Task 2 (data.json)"],
            depends_on=["dep_001", "dep_002"],
            acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"]
        )
        
        profile = self.manager.calculate_dimensional_profile(obj)
        
        self.assertEqual(len(profile), 7)
        
        # Check all dimensions are in valid range
        for dim, value in profile.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        
        # Temporal should be high (7 days)
        self.assertGreater(profile["temporal"], 0.7)
        
        # State should be elevated (mentions "state")
        self.assertGreater(profile["state"], 0.0)
        
        # Error should be elevated (mentions "error")
        self.assertGreater(profile["error"], 0.0)
    
    def test_find_optimal_objective(self):
        """Test finding optimal objective."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        optimal = self.manager.find_optimal_objective(state)
        
        if len(self.manager.dimensional_space.objectives) > 0:
            self.assertIsInstance(optimal, PolytopicObjective)
    
    def test_calculate_objective_distance(self):
        """Test calculating distance between objectives."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        obj1 = PolytopicObjective(
            id="obj_001",
            level=ObjectiveLevel.PRIMARY,
            title="Objective 1",
            description="First objective",
            status=ObjectiveStatus.APPROVED
        )
        
        obj2 = PolytopicObjective(
            id="obj_002",
            level=ObjectiveLevel.SECONDARY,
            title="Objective 2",
            description="Second objective",
            status=ObjectiveStatus.PROPOSED
        )
        
        distance = self.manager.calculate_objective_distance(obj1, obj2)
        
        self.assertIsInstance(distance, float)
        self.assertGreaterEqual(distance, 0.0)
    
    def test_get_adjacent_objectives(self):
        """Test getting adjacent objectives."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        if len(self.manager.dimensional_space.objectives) > 0:
            obj = list(self.manager.dimensional_space.objectives.values())[0]
            adjacent = self.manager.get_adjacent_objectives(obj)
            
            self.assertIsInstance(adjacent, list)
    
    def test_analyze_dimensional_health(self):
        """Test dimensional health analysis."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        obj = PolytopicObjective(
            id="test_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test",
            description="Test objective",
            status=ObjectiveStatus.APPROVED
        )
        obj.dimensional_profile = {
            "temporal": 0.9,  # High urgency
            "functional": 0.6,
            "data": 0.5,
            "state": 0.4,
            "error": 0.8,  # High risk
            "context": 0.5,
            "integration": 0.6
        }
        obj._update_metrics()
        
        health = self.manager.analyze_dimensional_health(obj)
        
        self.assertIn("objective_id", health)
        self.assertIn("overall_health", health)
        self.assertIn("dimensional_analysis", health)
        self.assertIn("concerns", health)
        self.assertIn("recommendations", health)
        
        # Should have concerns due to high temporal and error
        self.assertGreater(len(health["concerns"]), 0)
        self.assertGreater(len(health["recommendations"]), 0)
    
    def test_get_dimensional_statistics(self):
        """Test getting dimensional statistics."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        if len(self.manager.dimensional_space.objectives) > 0:
            stats = self.manager.get_dimensional_statistics()
            
            self.assertIsInstance(stats, dict)
    
    def test_cluster_objectives(self):
        """Test clustering objectives."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        if len(self.manager.dimensional_space.objectives) >= 2:
            clusters = self.manager.cluster_objectives(max_distance=0.5)
            
            self.assertIsInstance(clusters, dict)
    
    def test_visualize_dimensional_space(self):
        """Test visualizing dimensional space."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        visualization = self.manager.visualize_dimensional_space()
        
        self.assertIsInstance(visualization, str)
    
    def test_get_space_summary(self):
        """Test getting space summary."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        summary = self.manager.get_space_summary()
        
        self.assertIn("total_objectives", summary)
        self.assertIn("dimensions", summary)
        self.assertEqual(summary["dimensions"], 7)
    
    def test_update_objective_dimensions(self):
        """Test updating objective dimensions."""
        state = PipelineState(
            pipeline_run_id="test_run"
        )
        
        self.manager.load_objectives(state)
        
        if len(self.manager.dimensional_space.objectives) > 0:
            obj_id = list(self.manager.dimensional_space.objectives.keys())[0]
            
            self.manager.update_objective_dimensions(obj_id, "temporal", 0.9)
            
            obj = self.manager.dimensional_space.objectives[obj_id]
            self.assertEqual(obj.dimensional_profile["temporal"], 0.9)
    
    def test_predict_objective_trajectory(self):
        """Test predicting objective trajectory."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        obj = PolytopicObjective(
            id="test_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test",
            description="Test objective",
            status=ObjectiveStatus.APPROVED
        )
        obj.dimensional_velocity = {"temporal": 0.1, "functional": 0.0, "data": 0.0,
                                    "state": 0.0, "error": 0.0, "context": 0.0, "integration": 0.0}
        
        self.manager.dimensional_space.objectives["test_001"] = obj
        self.manager.dimensional_space.add_objective(obj)
        
        trajectory = self.manager.predict_objective_trajectory("test_001", time_steps=3)
        
        self.assertEqual(len(trajectory), 4)  # Current + 3 future
    
    def test_find_similar_objectives(self):
        """Test finding similar objectives."""
        from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus
        
        obj1 = PolytopicObjective(
            id="obj_001",
            level=ObjectiveLevel.PRIMARY,
            title="Objective 1",
            description="First objective",
            status=ObjectiveStatus.APPROVED
        )
        
        obj2 = PolytopicObjective(
            id="obj_002",
            level=ObjectiveLevel.PRIMARY,
            title="Objective 2",
            description="Second objective",
            status=ObjectiveStatus.APPROVED
        )
        obj2.dimensional_profile = obj1.dimensional_profile.copy()
        obj2.polytopic_position = obj2._calculate_position()
        
        self.manager.dimensional_space.objectives["obj_001"] = obj1
        self.manager.dimensional_space.objectives["obj_002"] = obj2
        self.manager.dimensional_space.add_objective(obj1)
        self.manager.dimensional_space.add_objective(obj2)
        
        similar = self.manager.find_similar_objectives("obj_001", similarity_threshold=0.9)
        
        self.assertGreater(len(similar), 0)
        self.assertEqual(similar[0][0], "obj_002")


if __name__ == '__main__':
    unittest.main()