"""
Tests for Tool Validator
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.tool_validator import ToolValidator, ToolMetrics


class TestToolMetrics(unittest.TestCase):
    """Test tool metrics tracking."""
    
    def test_metrics_initialization(self):
        """Test metrics are properly initialized."""
        metrics = ToolMetrics("test-tool")
        
        self.assertEqual(metrics.tool_name, "test-tool")
        self.assertEqual(metrics.total_calls, 0)
        self.assertEqual(metrics.successful_calls, 0)
        self.assertEqual(metrics.failed_calls, 0)
        self.assertEqual(metrics.success_rate, 0.0)
    
    def test_record_successful_call(self):
        """Test recording successful calls."""
        metrics = ToolMetrics("test-tool")
        
        metrics.record_call(success=True, execution_time=1.5, phase="execution")
        
        self.assertEqual(metrics.total_calls, 1)
        self.assertEqual(metrics.successful_calls, 1)
        self.assertEqual(metrics.failed_calls, 0)
        self.assertEqual(metrics.success_rate, 1.0)
        self.assertEqual(metrics.avg_execution_time, 1.5)
        self.assertIsNotNone(metrics.first_used)
        self.assertIsNotNone(metrics.last_used)
    
    def test_record_failed_call(self):
        """Test recording failed calls."""
        metrics = ToolMetrics("test-tool")
        
        metrics.record_call(success=False, error_type="timeout")
        
        self.assertEqual(metrics.total_calls, 1)
        self.assertEqual(metrics.successful_calls, 0)
        self.assertEqual(metrics.failed_calls, 1)
        self.assertEqual(metrics.success_rate, 0.0)
        self.assertEqual(metrics.error_types["timeout"], 1)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ToolMetrics("test-tool")
        
        # Record 7 successful and 3 failed calls
        for _ in range(7):
            metrics.record_call(success=True)
        for _ in range(3):
            metrics.record_call(success=False)
        
        self.assertEqual(metrics.total_calls, 10)
        self.assertEqual(metrics.success_rate, 0.7)
    
    def test_days_since_last_use(self):
        """Test days since last use calculation."""
        metrics = ToolMetrics("test-tool")
        
        # No usage yet
        self.assertEqual(metrics.days_since_last_use, 999)
        
        # Record a call
        metrics.record_call(success=True)
        self.assertEqual(metrics.days_since_last_use, 0)


class TestToolValidator(unittest.TestCase):
    """Test tool validation system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.validator = ToolValidator(self.project_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validator_initialization(self):
        """Test validator is properly initialized."""
        self.assertEqual(self.validator.min_attempts_for_creation, 5)
        self.assertEqual(self.validator.similarity_threshold, 0.8)
        self.assertEqual(self.validator.min_success_rate, 0.2)
        self.assertEqual(self.validator.deprecation_days, 30)
    
    def test_validate_tool_name(self):
        """Test tool name validation."""
        # Valid names
        self.assertTrue(self.validator._is_valid_tool_name("execute-command"))
        self.assertTrue(self.validator._is_valid_tool_name("create-file"))
        self.assertTrue(self.validator._is_valid_tool_name("web-search"))
        
        # Invalid names
        self.assertFalse(self.validator._is_valid_tool_name("Execute-Command"))  # Uppercase
        self.assertFalse(self.validator._is_valid_tool_name("create_file"))  # Underscore
        self.assertFalse(self.validator._is_valid_tool_name("web search"))  # Space
        self.assertFalse(self.validator._is_valid_tool_name("-start"))  # Starts with hyphen
    
    def test_validate_contexts(self):
        """Test context validation."""
        # Valid contexts
        valid_contexts = [
            {'description': 'First attempt to use tool'},
            {'description': 'Second attempt with different params'},
            {'description': 'Third attempt in different phase'}
        ]
        self.assertTrue(self.validator._validate_contexts(valid_contexts))
        
        # Invalid: too few contexts
        self.assertFalse(self.validator._validate_contexts([
            {'description': 'Only one'}
        ]))
        
        # Invalid: missing descriptions
        self.assertFalse(self.validator._validate_contexts([
            {},
            {},
            {}
        ]))
        
        # Invalid: all same description
        self.assertFalse(self.validator._validate_contexts([
            {'description': 'Same'},
            {'description': 'Same'},
            {'description': 'Same'}
        ]))
    
    def test_validate_tool_creation_insufficient_attempts(self):
        """Test validation fails with insufficient attempts."""
        contexts = [
            {'description': f'Attempt {i}'} for i in range(3)
        ]
        
        should_create, reason = self.validator.validate_tool_creation_request(
            "test-tool", 3, contexts
        )
        
        self.assertFalse(should_create)
        self.assertIn("Insufficient attempts", reason)
    
    def test_validate_tool_creation_invalid_name(self):
        """Test validation fails with invalid name."""
        contexts = [
            {'description': f'Attempt {i}'} for i in range(5)
        ]
        
        should_create, reason = self.validator.validate_tool_creation_request(
            "Invalid_Name", 5, contexts
        )
        
        self.assertFalse(should_create)
        self.assertIn("Invalid tool name", reason)
    
    def test_validate_tool_creation_success(self):
        """Test successful validation."""
        contexts = [
            {'description': f'Attempt {i} with different context'} for i in range(5)
        ]
        
        should_create, reason = self.validator.validate_tool_creation_request(
            "valid-tool", 5, contexts
        )
        
        self.assertTrue(should_create)
        self.assertIn("passed", reason)
    
    def test_find_similar_tools(self):
        """Test finding similar tools."""
        existing_tools = [
            "execute-command",
            "create-file",
            "web-search"
        ]
        
        # Very similar
        similar = self.validator.find_similar_tools("execute-cmd", existing_tools)
        self.assertIn("execute-command", similar)
        
        # Not similar
        similar = self.validator.find_similar_tools("totally-different", existing_tools)
        self.assertEqual(len(similar), 0)
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        # Valid parameters
        valid_params = {
            'file_path': {
                'type': 'string',
                'description': 'Path to the file'
            },
            'count': {
                'type': 'integer',
                'description': 'Number of items'
            }
        }
        
        is_valid, errors = self.validator.validate_parameters(valid_params)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid: missing type
        invalid_params = {
            'file_path': {
                'description': 'Path to the file'
            }
        }
        
        is_valid, errors = self.validator.validate_parameters(invalid_params)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Invalid: bad parameter name
        invalid_params = {
            'File-Path': {
                'type': 'string',
                'description': 'Path'
            }
        }
        
        is_valid, errors = self.validator.validate_parameters(invalid_params)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_record_tool_usage(self):
        """Test recording tool usage."""
        self.validator.record_tool_usage(
            "test-tool",
            success=True,
            execution_time=1.5,
            phase="execution"
        )
        
        self.assertIn("test-tool", self.validator.tool_metrics)
        metrics = self.validator.tool_metrics["test-tool"]
        self.assertEqual(metrics.total_calls, 1)
        self.assertEqual(metrics.successful_calls, 1)
    
    def test_get_tool_effectiveness(self):
        """Test getting tool effectiveness."""
        # Record some usage
        for _ in range(8):
            self.validator.record_tool_usage("test-tool", success=True)
        for _ in range(2):
            self.validator.record_tool_usage("test-tool", success=False)
        
        effectiveness = self.validator.get_tool_effectiveness("test-tool")
        
        self.assertIsNotNone(effectiveness)
        self.assertEqual(effectiveness['total_calls'], 10)
        self.assertEqual(effectiveness['success_rate'], 0.8)
    
    def test_identify_deprecated_tools_unused(self):
        """Test identifying deprecated tools (unused)."""
        # Create a tool that hasn't been used recently
        metrics = ToolMetrics("old-tool")
        metrics.last_used = datetime.now() - timedelta(days=40)
        self.validator.tool_metrics["old-tool"] = metrics
        
        deprecated = self.validator.identify_deprecated_tools()
        
        self.assertEqual(len(deprecated), 1)
        self.assertEqual(deprecated[0][0], "old-tool")
        self.assertIn("Unused", deprecated[0][1])
    
    def test_identify_deprecated_tools_low_success(self):
        """Test identifying deprecated tools (low success rate)."""
        # Create a tool with low success rate but recent usage
        # Need at least 10 calls to trigger low success rate check
        # Success rate must be < 0.2 (20%)
        metrics = ToolMetrics("failing-tool")
        for _ in range(1):
            metrics.record_call(success=True)  # 1 success
        for _ in range(9):
            metrics.record_call(success=False)  # 9 failures = 10% success rate
        
        # Ensure it's been used recently (within 30 days)
        metrics.last_used = datetime.now()
        
        self.validator.tool_metrics["failing-tool"] = metrics
        
        deprecated = self.validator.identify_deprecated_tools()
        
        # Should find the failing tool
        self.assertGreater(len(deprecated), 0)
        failing_tools = [name for name, reason in deprecated if name == "failing-tool"]
        self.assertEqual(len(failing_tools), 1)
        
        # Verify reason mentions success rate
        reason = next(reason for name, reason in deprecated if name == "failing-tool")
        self.assertIn("success rate", reason.lower())
    
    def test_get_tool_recommendations(self):
        """Test getting tool recommendations."""
        # High performer
        high_perf = ToolMetrics("high-performer")
        for _ in range(15):
            high_perf.record_call(success=True)
        self.validator.tool_metrics["high-performer"] = high_perf
        
        # Needs improvement
        needs_imp = ToolMetrics("needs-improvement")
        for _ in range(7):
            needs_imp.record_call(success=True)
        for _ in range(3):
            needs_imp.record_call(success=False)
        self.validator.tool_metrics["needs-improvement"] = needs_imp
        
        recommendations = self.validator.get_tool_recommendations()
        
        self.assertIn("high-performer", recommendations['high_performers'])
        self.assertIn("needs-improvement", recommendations['needs_improvement'])
    
    def test_save_and_load_metrics(self):
        """Test saving and loading metrics."""
        # Record some usage
        self.validator.record_tool_usage("test-tool", success=True, execution_time=1.5)
        self.validator.record_tool_usage("test-tool", success=False, error_type="timeout")
        
        # Save metrics
        self.validator.save_metrics()
        
        # Create new validator and load
        new_validator = ToolValidator(self.project_dir)
        
        # Verify metrics were loaded
        self.assertIn("test-tool", new_validator.tool_metrics)
        metrics = new_validator.tool_metrics["test-tool"]
        self.assertEqual(metrics.total_calls, 2)
        self.assertEqual(metrics.successful_calls, 1)
        self.assertEqual(metrics.failed_calls, 1)
    
    def test_generate_effectiveness_report(self):
        """Test generating effectiveness report."""
        # Add some tools with different metrics
        for _ in range(10):
            self.validator.record_tool_usage("good-tool", success=True)
        
        for _ in range(5):
            self.validator.record_tool_usage("bad-tool", success=False)
        
        report = self.validator.generate_effectiveness_report()
        
        self.assertIn("Tool Effectiveness Report", report)
        self.assertIn("good-tool", report)
        self.assertIn("bad-tool", report)
        self.assertIn("High Performers", report)


if __name__ == '__main__':
    unittest.main()