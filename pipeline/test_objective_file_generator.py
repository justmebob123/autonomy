"""
Tests for ObjectiveFileGenerator
"""

import unittest
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

from .objective_file_generator import (
    ObjectiveFileGenerator,
    ExtractedObjective,
    ObjectiveLevel
)
from .state.manager import PipelineState, TaskState, TaskStatus


class TestObjectiveFileGenerator(unittest.TestCase):
    """Test ObjectiveFileGenerator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.generator = ObjectiveFileGenerator(self.project_dir)
        
        # Create test state
        self.state = PipelineState()
        
        # Create test tasks
        self.tasks = [
            TaskState(
                task_id="task_001",
                description="Implement user authentication",
                target_file="src/auth/login.py",
                priority=50,
                status=TaskStatus.NEW,
                created_at=datetime.now().isoformat()
            ),
            TaskState(
                task_id="task_002",
                description="Create database models",
                target_file="src/models/user.py",
                priority=50,
                status=TaskStatus.NEW,
                created_at=datetime.now().isoformat()
            ),
            TaskState(
                task_id="task_003",
                description="Add API endpoints",
                target_file="src/api/routes.py",
                priority=50,
                status=TaskStatus.NEW,
                created_at=datetime.now().isoformat()
            )
        ]
        
        for task in self.tasks:
            self.state.tasks[task.task_id] = task
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()
    
    def test_extract_objectives_from_master_plan(self):
        """Test extracting objectives from MASTER_PLAN"""
        context = """
        MASTER_PLAN.md:
        ```markdown
        # Project Master Plan
        
        ## Core Authentication System
        Implement a secure authentication system with login, logout, and session management.
        
        Success criteria:
        - User can log in with credentials
        - Sessions are managed securely
        - Logout functionality works
        
        ## Database Layer
        Create database models and migrations for user data.
        
        ## API Layer
        Build RESTful API endpoints for all features.
        ```
        """
        
        objectives = self.generator._extract_objectives(context, self.tasks)
        
        self.assertGreater(len(objectives), 0)
        self.assertTrue(any('Authentication' in obj.title for obj in objectives))
    
    def test_determine_objective_level(self):
        """Test objective level determination"""
        # Test PRIMARY
        level = self.generator._determine_objective_level(
            "Core Authentication",
            "This is critical and must be implemented"
        )
        self.assertEqual(level, ObjectiveLevel.PRIMARY)
        
        # Test TERTIARY
        level = self.generator._determine_objective_level(
            "Optional Features",
            "Nice to have enhancements for future"
        )
        self.assertEqual(level, ObjectiveLevel.TERTIARY)
        
        # Test SECONDARY (default)
        level = self.generator._determine_objective_level(
            "User Profile",
            "Standard user profile functionality"
        )
        self.assertEqual(level, ObjectiveLevel.SECONDARY)
    
    def test_calculate_dimensional_profile(self):
        """Test dimensional profile calculation"""
        profile = self.generator._calculate_dimensional_profile(
            "Critical Authentication System",
            "Complex state management with security requirements",
            self.tasks
        )
        
        self.assertIn('temporal', profile)
        self.assertIn('functional', profile)
        self.assertIn('data', profile)
        self.assertIn('state', profile)
        self.assertIn('error', profile)
        self.assertIn('context', profile)
        self.assertIn('integration', profile)
        
        # Check ranges
        for value in profile.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        
        # Critical should have high temporal
        self.assertGreater(profile['temporal'], 0.0)
        
        # State management should have high state dimension
        self.assertGreater(profile['state'], 0.0)
    
    def test_extract_success_criteria(self):
        """Test success criteria extraction"""
        content = """
        Success criteria:
        - Feature A works correctly
        - Feature B is tested
        - Documentation is complete
        """
        
        criteria = self.generator._extract_success_criteria(content)
        
        self.assertEqual(len(criteria), 3)
        self.assertIn("Feature A works correctly", criteria)
    
    def test_match_tasks_to_objective(self):
        """Test task matching to objectives"""
        matched = self.generator._match_tasks_to_objective(
            "Authentication System",
            "Login and user management",
            self.tasks
        )
        
        # Should match task_001 (authentication)
        self.assertTrue(any(t.task_id == "task_001" for t in matched))
    
    def test_generate_objective_file(self):
        """Test objective file generation"""
        objectives = [
            ExtractedObjective(
                title="Test Objective",
                description="Test description",
                level=ObjectiveLevel.PRIMARY,
                success_criteria=["Criterion 1", "Criterion 2"],
                dependencies=["Dependency 1"],
                dimensional_profile={
                    'temporal': 0.8,
                    'functional': 0.6,
                    'data': 0.5,
                    'state': 0.7,
                    'error': 0.6,
                    'context': 0.5,
                    'integration': 0.4
                },
                tasks=["task_001", "task_002"]
            )
        ]
        
        content = self.generator._generate_objective_file(
            objectives, ObjectiveLevel.PRIMARY, self.state
        )
        
        self.assertIn("PRIMARY OBJECTIVES", content)
        self.assertIn("Test Objective", content)
        self.assertIn("PRIMARY_001", content)
        self.assertIn("Criterion 1", content)
        self.assertIn("task_001", content)
        self.assertIn("Temporal", content)
    
    def test_write_objective_files(self):
        """Test writing objective files to disk"""
        files = {
            'PRIMARY_OBJECTIVES.md': '# PRIMARY OBJECTIVES\n\nTest content',
            'SECONDARY_OBJECTIVES.md': '# SECONDARY OBJECTIVES\n\nTest content'
        }
        
        created = self.generator.write_objective_files(files)
        
        self.assertEqual(len(created), 2)
        
        # Verify files exist
        primary_path = self.project_dir / 'PRIMARY_OBJECTIVES.md'
        secondary_path = self.project_dir / 'SECONDARY_OBJECTIVES.md'
        
        self.assertTrue(primary_path.exists())
        self.assertTrue(secondary_path.exists())
        
        # Verify content
        self.assertIn('PRIMARY OBJECTIVES', primary_path.read_text())
        self.assertIn('SECONDARY OBJECTIVES', secondary_path.read_text())
    
    def test_link_tasks_to_objectives(self):
        """Test linking tasks to objectives"""
        objective_files = {
            'PRIMARY_OBJECTIVES.md': """
            # PRIMARY OBJECTIVES
            
            ## Objective 1: Test
            **ID**: `PRIMARY_001`
            
            ### Tasks
            - ⏳ `task_001`: Test task
            - ⏳ `task_002`: Another task
            """
        }
        
        linked_count = self.generator.link_tasks_to_objectives(
            self.state, objective_files
        )
        
        self.assertEqual(linked_count, 2)
        self.assertEqual(self.state.tasks['task_001'].objective_id, 'PRIMARY_001')
        self.assertEqual(self.state.tasks['task_002'].objective_id, 'PRIMARY_001')
        self.assertEqual(self.state.tasks['task_001'].objective_level, 'primary')
    
    def test_create_default_objectives(self):
        """Test creating default objectives when no context"""
        objectives = self.generator._create_default_objectives(self.tasks)
        
        self.assertGreater(len(objectives), 0)
        
        # Should group by directory
        for obj in objectives:
            self.assertIsNotNone(obj.title)
            self.assertEqual(obj.level, ObjectiveLevel.PRIMARY)
            self.assertGreater(len(obj.tasks), 0)
    
    def test_generate_objective_files_integration(self):
        """Test full objective file generation workflow"""
        context = """
        MASTER_PLAN.md:
        ```markdown
        # Master Plan
        
        ## Core Features
        Critical features that must be implemented first.
        
        ## Additional Features
        Nice to have features for later.
        ```
        """
        
        files = self.generator.generate_objective_files(
            self.state, context, self.tasks
        )
        
        self.assertIsInstance(files, dict)
        
        # Should have at least one file
        self.assertGreater(len(files), 0)
        
        # Files should have proper format
        for filename, content in files.items():
            self.assertTrue(filename.endswith('_OBJECTIVES.md'))
            self.assertIn('OBJECTIVES', content)


class TestDimensionalProfileCalculation(unittest.TestCase):
    """Test dimensional profile calculation accuracy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = TemporaryDirectory()
        self.generator = ObjectiveFileGenerator(Path(self.temp_dir.name))
    
    def tearDown(self):
        """Clean up"""
        self.temp_dir.cleanup()
    
    def test_high_temporal_urgency(self):
        """Test high temporal dimension for urgent tasks"""
        profile = self.generator._calculate_dimensional_profile(
            "Critical Urgent Feature",
            "Must be done ASAP, highest priority",
            []
        )
        
        self.assertGreater(profile['temporal'], 0.5)
    
    def test_high_functional_complexity(self):
        """Test high functional dimension for complex tasks"""
        profile = self.generator._calculate_dimensional_profile(
            "Advanced Algorithm",
            "Complex optimization with sophisticated logic",
            []
        )
        
        self.assertGreater(profile['functional'], 0.4)
    
    def test_high_state_management(self):
        """Test high state dimension for stateful tasks"""
        profile = self.generator._calculate_dimensional_profile(
            "Session Management",
            "Persistent state with cache and database",
            []
        )
        
        self.assertGreater(profile['state'], 0.3)
    
    def test_high_integration_complexity(self):
        """Test high integration dimension for system-wide tasks"""
        profile = self.generator._calculate_dimensional_profile(
            "System Architecture",
            "Framework infrastructure for entire platform",
            []
        )
        
        self.assertGreater(profile['integration'], 0.3)


if __name__ == '__main__':
    unittest.main()