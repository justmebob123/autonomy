"""
Integration tests for Coordinator with PolytopicObjectiveManager.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pipeline.coordinator import PhaseCoordinator
from pipeline.config import PipelineConfig
from pipeline.state.manager import PipelineState, TaskState, TaskStatus
from pipeline.polytopic import PolytopicObjective
from pipeline.objective_manager import ObjectiveLevel, ObjectiveStatus


class TestCoordinatorPolytopicIntegration(unittest.TestCase):
    """Test cases for Coordinator with Polytopic integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        
        # Create config
        self.config = PipelineConfig(
            project_dir=str(self.project_dir),
            max_iterations=1  # Limit iterations for testing
        )
        
        # Create test objective files
        self._create_test_objectives()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def _create_test_objectives(self):
        """Create test objective markdown files."""
        primary_content = """# Primary Objectives

## 1. Test Feature Implementation

**ID**: primary_001
**Status**: approved
**Target Date**: 2024-12-31
**Priority**: PRIMARY

### Description
Implement a test feature with state management and error handling.

### Tasks
- [ ] Create state store (src/state.py)
- [ ] Add error handling (src/errors.py)
- [ ] Write tests (tests/test_feature.py)

### Dependencies
None

### Acceptance Criteria
- [ ] All tests passing
- [ ] Code coverage > 80%

### Dimensional Profile
- Temporal: 0.7
- Functional: 0.8
- Data: 0.6
- State: 0.9
- Error: 0.7
- Context: 0.6
- Integration: 0.8

---
"""
        
        objectives_file = self.project_dir / "PRIMARY_OBJECTIVES.md"
        objectives_file.write_text(primary_content)
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_coordinator_initialization_with_polytopic(self, mock_client):
        """Test coordinator initializes with PolytopicObjectiveManager."""
        coordinator = PhaseCoordinator(self.config)
        
        # Check that objective_manager is PolytopicObjectiveManager
        from pipeline.polytopic import PolytopicObjectiveManager
        self.assertIsInstance(coordinator.objective_manager, PolytopicObjectiveManager)
        
        # Check that dimensional_space is initialized
        self.assertIsNotNone(coordinator.objective_manager.dimensional_space)
        self.assertEqual(coordinator.objective_manager.dimensional_space.dimensions, 7)
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_strategic_decision_with_polytopic(self, mock_client):
        """Test strategic decision-making uses polytopic features."""
        coordinator = PhaseCoordinator(self.config)
        
        # Create state with objectives
        state = PipelineState(pipeline_run_id="test_run")
        state.objectives = {"primary": {"primary_001": {}}}
        
        # Mock the objective manager methods
        mock_objective = PolytopicObjective(
            id="primary_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test Feature",
            description="Test objective",
            status=ObjectiveStatus.APPROVED
        )
        mock_objective.complexity_score = 0.75
        mock_objective.risk_score = 0.65
        mock_objective.readiness_score = 0.80
        
        coordinator.objective_manager.find_optimal_objective = Mock(return_value=mock_objective)
        coordinator.objective_manager.analyze_dimensional_health = Mock(return_value={
            'overall_health': 'HEALTHY',
            'concerns': [],
            'recommendations': ['Continue with current objective']
        })
        
        # Mock get_objective_action
        from pipeline.objective_manager import PhaseAction
        mock_action = PhaseAction(
            phase='coding',
            task=None,
            reason='Implement pending tasks',
            priority=1
        )
        coordinator.objective_manager.get_objective_action = Mock(return_value=mock_action)
        coordinator.objective_manager.save_objective = Mock()
        
        # Call strategic decision-making
        decision = coordinator._determine_next_action_strategic(state)
        
        # Verify decision includes polytopic information
        self.assertEqual(decision['phase'], 'coding')
        self.assertIsNotNone(decision['objective'])
        self.assertIn('dimensional_health', decision)
        
        # Verify polytopic methods were called
        coordinator.objective_manager.find_optimal_objective.assert_called_once()
        coordinator.objective_manager.analyze_dimensional_health.assert_called_once()
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_dimensional_health_logging(self, mock_client):
        """Test dimensional health is logged correctly."""
        coordinator = PhaseCoordinator(self.config)
        
        # Create mock objective with dimensional properties
        mock_objective = PolytopicObjective(
            id="primary_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test Feature",
            description="Test objective",
            status=ObjectiveStatus.APPROVED
        )
        mock_objective.complexity_score = 0.75
        mock_objective.risk_score = 0.65
        mock_objective.readiness_score = 0.80
        mock_objective.dimensional_profile = {
            "temporal": 0.9,
            "functional": 0.8,
            "data": 0.6,
            "state": 0.7,
            "error": 0.5,
            "context": 0.6,
            "integration": 0.7
        }
        
        # Test get_dominant_dimensions
        dominant = mock_objective.get_dominant_dimensions(threshold=0.7)
        self.assertIn("temporal", dominant)
        self.assertIn("functional", dominant)
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_space_summary_in_run_summary(self, mock_client):
        """Test dimensional space summary is included in run summary."""
        coordinator = PhaseCoordinator(self.config)
        
        # Mock space summary
        coordinator.objective_manager.get_space_summary = Mock(return_value={
            'total_objectives': 3,
            'dimensions': 7,
            'objectives_by_level': {
                'PRIMARY': 1,
                'SECONDARY': 1,
                'TERTIARY': 1
            },
            'clusters': 2
        })
        
        # Create state
        state = PipelineState(pipeline_run_id="test_run")
        coordinator.state_manager.save(state)
        
        # Call summarize_run
        result = coordinator._summarize_run()
        
        # Verify space summary was called
        coordinator.objective_manager.get_space_summary.assert_called()
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_visualize_dimensional_space(self, mock_client):
        """Test dimensional space visualization method."""
        coordinator = PhaseCoordinator(self.config)
        
        # Mock visualization methods
        coordinator.objective_manager.visualize_dimensional_space = Mock(
            return_value="Dimensional Space Visualization"
        )
        coordinator.objective_manager.get_space_summary = Mock(return_value={
            'total_objectives': 3,
            'dimensions': 7
        })
        coordinator.objective_manager.get_dimensional_statistics = Mock(return_value={
            'temporal': {'mean': 0.6, 'std': 0.2},
            'functional': {'mean': 0.7, 'std': 0.15}
        })
        
        # Call visualization
        coordinator.visualize_dimensional_space()
        
        # Verify methods were called
        coordinator.objective_manager.visualize_dimensional_space.assert_called_once()
        coordinator.objective_manager.get_space_summary.assert_called_once()
        coordinator.objective_manager.get_dimensional_statistics.assert_called_once()
    
    @patch('pipeline.coordinator.OllamaClient')
    def test_dimensional_metrics_in_phase_decision(self, mock_client):
        """Test dimensional metrics are included in phase decisions."""
        coordinator = PhaseCoordinator(self.config)
        
        # Create state
        state = PipelineState(pipeline_run_id="test_run")
        state.objectives = {"primary": {"primary_001": {}}}
        
        # Create mock objective with metrics
        mock_objective = PolytopicObjective(
            id="primary_001",
            level=ObjectiveLevel.PRIMARY,
            title="Test Feature",
            description="Test objective",
            status=ObjectiveStatus.APPROVED
        )
        mock_objective.complexity_score = 0.75
        mock_objective.risk_score = 0.65
        mock_objective.readiness_score = 0.80
        
        # Mock methods
        coordinator.objective_manager.find_optimal_objective = Mock(return_value=mock_objective)
        coordinator.objective_manager.analyze_dimensional_health = Mock(return_value={
            'overall_health': 'HEALTHY',
            'concerns': [],
            'recommendations': ['Continue']
        })
        
        from pipeline.objective_manager import PhaseAction
        coordinator.objective_manager.get_objective_action = Mock(return_value=PhaseAction(
            phase='coding',
            task=None,
            reason='Test',
            priority=1
        ))
        coordinator.objective_manager.save_objective = Mock()
        
        # Get decision
        decision = coordinator._determine_next_action_strategic(state)
        
        # Verify objective has metrics
        obj = decision['objective']
        self.assertEqual(obj.complexity_score, 0.75)
        self.assertEqual(obj.risk_score, 0.65)
        self.assertEqual(obj.readiness_score, 0.80)


if __name__ == '__main__':
    unittest.main()