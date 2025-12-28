"""
Unit tests for Message Analytics
"""

import unittest
from datetime import datetime, timedelta
import time

from .message import Message, MessageType, MessagePriority
from .message_bus import MessageBus
from .analytics import MessageAnalytics


class TestMessageAnalytics(unittest.TestCase):
    """Test MessageAnalytics class"""
    
    def setUp(self):
        """Set up test message bus and analytics"""
        self.bus = MessageBus()
        self.analytics = MessageAnalytics(self.bus)
        
        # Create some test messages
        self._create_test_messages()
    
    def _create_test_messages(self):
        """Create test messages for analysis"""
        # Planning creates tasks
        for i in range(5):
            self.bus.send_direct(
                sender="planning",
                recipient="broadcast",
                message_type=MessageType.TASK_CREATED,
                payload={'task_id': f'task_{i}'},
                priority=MessagePriority.NORMAL
            )
        
        # QA finds issues
        for i in range(3):
            priority = MessagePriority.CRITICAL if i == 0 else MessagePriority.HIGH
            self.bus.send_direct(
                sender="qa",
                recipient="broadcast",
                message_type=MessageType.ISSUE_FOUND,
                payload={'issue_id': f'issue_{i}'},
                priority=priority
            )
        
        # Debugging resolves issues
        for i in range(2):
            self.bus.send_direct(
                sender="debugging",
                recipient="broadcast",
                message_type=MessageType.ISSUE_RESOLVED,
                payload={'issue_id': f'issue_{i}'},
                priority=MessagePriority.NORMAL
            )
    
    def test_frequency_analysis(self):
        """Test frequency analysis"""
        freq = self.analytics.get_frequency_analysis()
        
        self.assertEqual(freq['total_messages'], 10)
        self.assertIn('by_type', freq)
        self.assertIn('by_sender', freq)
        self.assertIn('by_priority', freq)
        
        # Check message types
        self.assertEqual(freq['by_type']['task_created'], 5)
        self.assertEqual(freq['by_type']['issue_found'], 3)
        self.assertEqual(freq['by_type']['issue_resolved'], 2)
        
        # Check senders
        self.assertEqual(freq['by_sender']['planning'], 5)
        self.assertEqual(freq['by_sender']['qa'], 3)
        self.assertEqual(freq['by_sender']['debugging'], 2)
    
    def test_frequency_analysis_with_time_window(self):
        """Test frequency analysis with time window"""
        # Analyze last hour
        freq = self.analytics.get_frequency_analysis(timedelta(hours=1))
        
        # Should include all recent messages
        self.assertEqual(freq['total_messages'], 10)
        
        # Analyze last second (should be empty if messages are old)
        time.sleep(0.1)
        freq = self.analytics.get_frequency_analysis(timedelta(seconds=0.05))
        self.assertEqual(freq['total_messages'], 0)
    
    def test_pattern_detection(self):
        """Test pattern detection"""
        patterns = self.analytics.detect_patterns(timedelta(hours=1))
        
        self.assertIn('repeated_errors', patterns)
        self.assertIn('message_bursts', patterns)
        self.assertIn('slow_responses', patterns)
        self.assertIn('common_sequences', patterns)
        
        # Pattern detection should return valid structure
        # (burst detection requires >10 messages in 5 minutes, which we don't have in test)
        self.assertIsInstance(patterns['message_bursts'], list)
        self.assertIsInstance(patterns['repeated_errors'], list)
        self.assertIsInstance(patterns['slow_responses'], list)
        self.assertIsInstance(patterns['common_sequences'], list)
    
    def test_performance_metrics(self):
        """Test performance metrics"""
        perf = self.analytics.get_performance_metrics()
        
        self.assertEqual(perf['total_messages'], 10)
        self.assertGreater(perf['processing_rate'], 0)
        
        # Check critical message ratio (1 critical out of 10)
        self.assertAlmostEqual(perf['critical_message_ratio'], 0.1, places=2)
        self.assertEqual(perf['critical_message_count'], 1)
        
        # Check unique counts
        self.assertEqual(perf['unique_senders'], 3)
        self.assertEqual(perf['message_types_count'], 3)
    
    def test_trend_analysis(self):
        """Test trend analysis"""
        windows = [
            timedelta(minutes=5),
            timedelta(minutes=10),
            timedelta(hours=1),
        ]
        
        trends = self.analytics.get_trend_analysis(windows)
        
        self.assertIn('message_volume', trends)
        self.assertIn('critical_ratio', trends)
        self.assertIn('error_rate', trends)
        
        # Should have data for each window
        self.assertEqual(len(trends['message_volume']), 3)
    
    def test_phase_communication_matrix(self):
        """Test phase communication matrix"""
        # Add some direct messages
        self.bus.send_direct(
            sender="planning",
            recipient="coding",
            message_type=MessageType.TASK_CREATED,
            payload={}
        )
        
        self.bus.send_direct(
            sender="qa",
            recipient="debugging",
            message_type=MessageType.ISSUE_FOUND,
            payload={}
        )
        
        matrix = self.analytics.get_phase_communication_matrix()
        
        self.assertIn('matrix', matrix)
        self.assertIn('total_direct_messages', matrix)
        
        # Check direct message counts
        self.assertEqual(matrix['total_direct_messages'], 2)
        self.assertEqual(matrix['matrix']['planning']['coding'], 1)
        self.assertEqual(matrix['matrix']['qa']['debugging'], 1)
    
    def test_objective_message_analysis(self):
        """Test objective-level message analysis"""
        # Add messages with objective IDs
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={},
            objective_id="primary_001"
        )
        
        self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_FOUND,
            payload={},
            priority=MessagePriority.CRITICAL,
            objective_id="primary_001"
        )
        
        analysis = self.analytics.get_objective_message_analysis()
        
        self.assertIn('primary_001', analysis)
        obj_data = analysis['primary_001']
        
        self.assertEqual(obj_data['total'], 2)
        self.assertEqual(obj_data['critical_count'], 1)
        self.assertIn('by_type', obj_data)
    
    def test_report_generation(self):
        """Test report generation"""
        report = self.analytics.generate_report(timedelta(hours=1))
        
        self.assertIsInstance(report, str)
        self.assertIn('MESSAGE BUS ANALYTICS REPORT', report)
        self.assertIn('FREQUENCY ANALYSIS', report)
        self.assertIn('PERFORMANCE METRICS', report)
        self.assertIn('PATTERN DETECTION', report)
        
        # Check that key metrics are in report
        self.assertIn('Total Messages: 10', report)
        self.assertIn('planning: 5', report)
    
    def test_empty_analytics(self):
        """Test analytics with no messages"""
        empty_bus = MessageBus()
        empty_analytics = MessageAnalytics(empty_bus)
        
        freq = empty_analytics.get_frequency_analysis()
        self.assertEqual(freq['total_messages'], 0)
        
        perf = empty_analytics.get_performance_metrics()
        self.assertEqual(perf['total_messages'], 0)
        
        patterns = empty_analytics.detect_patterns()
        self.assertEqual(len(patterns['repeated_errors']), 0)


if __name__ == '__main__':
    unittest.main()