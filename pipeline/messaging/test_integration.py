"""
Integration tests for Message Bus System

Tests the complete message flow between phases and coordinator.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from .message import Message, MessageType, MessagePriority
from .message_bus import MessageBus
from ..state.manager import StateManager, PipelineState


class TestMessageBusIntegration(unittest.TestCase):
    """Integration tests for message bus with phases"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        
        # Create state manager
        self.state_manager = StateManager(self.project_dir)
        
        # Create message bus
        self.bus = MessageBus(state_manager=self.state_manager)
        
        # Subscribe phases
        self.bus.subscribe("planning", [
            MessageType.OBJECTIVE_ACTIVATED,
            MessageType.OBJECTIVE_BLOCKED,
        ])
        
        self.bus.subscribe("qa", [
            MessageType.TASK_COMPLETED,
            MessageType.FILE_MODIFIED,
        ])
        
        self.bus.subscribe("debugging", [
            MessageType.ISSUE_FOUND,
            MessageType.TASK_FAILED,
        ])
        
        self.bus.subscribe("coordinator", [
            MessageType.OBJECTIVE_BLOCKED,
            MessageType.PHASE_ERROR,
            MessageType.ISSUE_FOUND,
        ])
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_planning_to_qa_flow(self):
        """Test message flow from Planning to QA"""
        # Planning creates a task
        task_msg = self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={
                'task_id': 'task_001',
                'description': 'Implement feature X',
                'target_file': 'src/feature.py'
            },
            task_id='task_001',
            file_path='src/feature.py'
        )
        
        # QA should receive the message (subscribed to broadcast)
        qa_messages = self.bus.get_messages("qa")
        # Note: QA is not subscribed to TASK_CREATED, so won't receive it
        # This is correct - QA subscribes to TASK_COMPLETED
        
        # Simulate task completion
        complete_msg = self.bus.send_direct(
            sender="coding",
            recipient="broadcast",
            message_type=MessageType.TASK_COMPLETED,
            payload={
                'task_id': 'task_001',
                'file': 'src/feature.py'
            },
            task_id='task_001',
            file_path='src/feature.py'
        )
        
        # QA should now receive this message
        qa_messages = self.bus.get_messages("qa")
        self.assertEqual(len(qa_messages), 1)
        self.assertEqual(qa_messages[0].message_type, MessageType.TASK_COMPLETED)
        self.assertEqual(qa_messages[0].payload['task_id'], 'task_001')
    
    def test_qa_to_debugging_flow(self):
        """Test message flow from QA to Debugging"""
        # QA finds an issue
        issue_msg = self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_FOUND,
            payload={
                'issue_id': 'issue_001',
                'issue_type': 'bug',
                'severity': 'critical',
                'file': 'src/feature.py',
                'description': 'Null pointer exception'
            },
            priority=MessagePriority.CRITICAL,
            issue_id='issue_001',
            task_id='task_001',
            file_path='src/feature.py'
        )
        
        # Debugging should receive the message
        debug_messages = self.bus.get_messages("debugging")
        self.assertEqual(len(debug_messages), 1)
        self.assertEqual(debug_messages[0].message_type, MessageType.ISSUE_FOUND)
        self.assertEqual(debug_messages[0].priority, MessagePriority.CRITICAL)
        self.assertEqual(debug_messages[0].payload['issue_id'], 'issue_001')
        
        # Coordinator should also receive (subscribed to ISSUE_FOUND)
        coord_messages = self.bus.get_messages("coordinator")
        self.assertEqual(len(coord_messages), 1)
        self.assertEqual(coord_messages[0].message_type, MessageType.ISSUE_FOUND)
    
    def test_debugging_resolution_flow(self):
        """Test message flow when debugging resolves an issue"""
        # Debugging resolves an issue
        resolved_msg = self.bus.send_direct(
            sender="debugging",
            recipient="broadcast",
            message_type=MessageType.ISSUE_RESOLVED,
            payload={
                'issue_id': 'issue_001',
                'file': 'src/feature.py',
                'resolution': 'Fixed null pointer check'
            },
            issue_id='issue_001',
            task_id='task_001',
            file_path='src/feature.py'
        )
        
        # All phases should be able to see this in history
        history = self.bus.search_messages(
            message_types=[MessageType.ISSUE_RESOLVED],
            limit=10
        )
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].payload['issue_id'], 'issue_001')
    
    def test_coordinator_critical_monitoring(self):
        """Test coordinator receives critical messages"""
        # Send various priority messages
        self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_FOUND,
            payload={'issue_id': 'issue_001', 'severity': 'low'},
            priority=MessagePriority.NORMAL
        )
        
        self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_FOUND,
            payload={'issue_id': 'issue_002', 'severity': 'critical'},
            priority=MessagePriority.CRITICAL
        )
        
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.OBJECTIVE_BLOCKED,
            payload={'objective_id': 'primary_001'},
            priority=MessagePriority.CRITICAL
        )
        
        # Coordinator should receive all ISSUE_FOUND and OBJECTIVE_BLOCKED
        coord_messages = self.bus.get_messages("coordinator")
        self.assertEqual(len(coord_messages), 3)
        
        # Filter for critical only
        critical_messages = self.bus.get_messages(
            "coordinator",
            priority=MessagePriority.CRITICAL
        )
        self.assertEqual(len(critical_messages), 2)
    
    def test_message_context_linking(self):
        """Test that messages maintain context links"""
        # Create a message with full context
        msg = self.bus.send_direct(
            sender="qa",
            recipient="debugging",
            message_type=MessageType.ISSUE_FOUND,
            payload={'issue_id': 'issue_001'},
            objective_id='primary_001',
            task_id='task_001',
            issue_id='issue_001',
            file_path='src/feature.py'
        )
        
        # Retrieve and verify context
        messages = self.bus.get_messages("debugging")
        self.assertEqual(len(messages), 1)
        
        retrieved = messages[0]
        self.assertEqual(retrieved.objective_id, 'primary_001')
        self.assertEqual(retrieved.task_id, 'task_001')
        self.assertEqual(retrieved.issue_id, 'issue_001')
        self.assertEqual(retrieved.file_path, 'src/feature.py')
    
    def test_message_search_by_context(self):
        """Test searching messages by context"""
        # Create messages with different contexts
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={'task_id': 'task_001'},
            objective_id='primary_001',
            task_id='task_001'
        )
        
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={'task_id': 'task_002'},
            objective_id='primary_001',
            task_id='task_002'
        )
        
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={'task_id': 'task_003'},
            objective_id='secondary_001',
            task_id='task_003'
        )
        
        # Search by objective
        primary_messages = self.bus.search_messages(
            objective_id='primary_001'
        )
        self.assertEqual(len(primary_messages), 2)
        
        # Search by task
        task_messages = self.bus.search_messages(
            task_id='task_001'
        )
        self.assertEqual(len(task_messages), 1)
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from planning to resolution"""
        # 1. Planning creates task
        self.bus.send_direct(
            sender="planning",
            recipient="broadcast",
            message_type=MessageType.TASK_CREATED,
            payload={'task_id': 'task_001', 'description': 'Feature X'},
            task_id='task_001',
            objective_id='primary_001'
        )
        
        # 2. Coding completes task
        self.bus.send_direct(
            sender="coding",
            recipient="broadcast",
            message_type=MessageType.TASK_COMPLETED,
            payload={'task_id': 'task_001', 'file': 'src/feature.py'},
            task_id='task_001'
        )
        
        # 3. QA finds issue
        self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_FOUND,
            payload={'issue_id': 'issue_001', 'severity': 'high'},
            priority=MessagePriority.HIGH,
            issue_id='issue_001',
            task_id='task_001'
        )
        
        # 4. Debugging resolves issue
        self.bus.send_direct(
            sender="debugging",
            recipient="broadcast",
            message_type=MessageType.ISSUE_RESOLVED,
            payload={'issue_id': 'issue_001', 'resolution': 'Fixed'},
            issue_id='issue_001',
            task_id='task_001'
        )
        
        # 5. QA verifies fix
        self.bus.send_direct(
            sender="qa",
            recipient="broadcast",
            message_type=MessageType.ISSUE_VERIFIED,
            payload={'issue_id': 'issue_001'},
            issue_id='issue_001',
            task_id='task_001'
        )
        
        # Verify complete workflow in history
        workflow_messages = self.bus.search_messages(
            task_id='task_001'
        )
        
        # Should have all 5 messages
        self.assertEqual(len(workflow_messages), 5)
        
        # Verify message types in order (reverse chronological)
        expected_types = [
            MessageType.ISSUE_VERIFIED,
            MessageType.ISSUE_RESOLVED,
            MessageType.ISSUE_FOUND,
            MessageType.TASK_COMPLETED,
            MessageType.TASK_CREATED,
        ]
        
        actual_types = [msg.message_type for msg in workflow_messages]
        self.assertEqual(actual_types, expected_types)
    
    def test_message_statistics(self):
        """Test message bus statistics tracking"""
        # Send various messages
        self.bus.broadcast("planning", MessageType.TASK_CREATED, {})
        self.bus.send_direct("qa", "debugging", MessageType.ISSUE_FOUND, {})
        self.bus.broadcast("coordinator", MessageType.SYSTEM_ALERT, {})
        
        # Get statistics
        stats = self.bus.get_statistics()
        
        self.assertEqual(stats['total_published'], 3)
        self.assertEqual(stats['total_broadcast'], 2)
        self.assertEqual(stats['total_direct'], 1)
        self.assertGreater(stats['total_delivered'], 0)


if __name__ == '__main__':
    unittest.main()