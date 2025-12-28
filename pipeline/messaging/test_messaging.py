"""
Unit tests for the Message Bus System
"""

import unittest
from datetime import datetime, timedelta
import time

from .message import Message, MessageType, MessagePriority
from .message_bus import MessageBus


class TestMessage(unittest.TestCase):
    """Test Message class"""
    
    def test_message_creation(self):
        """Test basic message creation"""
        msg = Message(
            sender="planning",
            recipient="coding",
            message_type=MessageType.TASK_CREATED,
            priority=MessagePriority.HIGH,
            payload={"task_id": "task_001"}
        )
        
        self.assertEqual(msg.sender, "planning")
        self.assertEqual(msg.recipient, "coding")
        self.assertEqual(msg.message_type, MessageType.TASK_CREATED)
        self.assertEqual(msg.priority, MessagePriority.HIGH)
        self.assertIsNotNone(msg.id)
        self.assertIsInstance(msg.timestamp, datetime)
    
    def test_message_serialization(self):
        """Test message to_dict and from_dict"""
        msg = Message(
            sender="qa",
            recipient="debugging",
            message_type=MessageType.ISSUE_FOUND,
            priority=MessagePriority.CRITICAL,
            payload={"issue_type": "bug", "severity": "high"},
            task_id="task_001",
            objective_id="primary_001"
        )
        
        # Serialize
        data = msg.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['sender'], "qa")
        self.assertEqual(data['message_type'], "issue_found")
        
        # Deserialize
        msg2 = Message.from_dict(data)
        self.assertEqual(msg2.sender, msg.sender)
        self.assertEqual(msg2.message_type, msg.message_type)
        self.assertEqual(msg2.priority, msg.priority)
        self.assertEqual(msg2.task_id, msg.task_id)
    
    def test_broadcast_detection(self):
        """Test broadcast message detection"""
        msg1 = Message(recipient="broadcast")
        msg2 = Message(recipient="*")
        msg3 = Message(recipient="specific_phase")
        
        self.assertTrue(msg1.is_broadcast())
        self.assertTrue(msg2.is_broadcast())
        self.assertFalse(msg3.is_broadcast())
    
    def test_priority_checks(self):
        """Test priority checking methods"""
        critical = Message(priority=MessagePriority.CRITICAL)
        high = Message(priority=MessagePriority.HIGH)
        normal = Message(priority=MessagePriority.NORMAL)
        
        self.assertTrue(critical.is_critical())
        self.assertTrue(critical.is_high_priority())
        
        self.assertFalse(high.is_critical())
        self.assertTrue(high.is_high_priority())
        
        self.assertFalse(normal.is_critical())
        self.assertFalse(normal.is_high_priority())


class TestMessageBus(unittest.TestCase):
    """Test MessageBus class"""
    
    def setUp(self):
        """Set up test message bus"""
        self.bus = MessageBus()
    
    def test_publish_and_subscribe(self):
        """Test basic publish-subscribe pattern"""
        # Subscribe
        self.bus.subscribe("coding", [MessageType.TASK_CREATED])
        
        # Publish
        msg = self.bus.send_direct(
            sender="planning",
            recipient="coding",
            message_type=MessageType.TASK_CREATED,
            payload={"task_id": "task_001"}
        )
        
        # Retrieve
        messages = self.bus.get_messages("coding")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_type, MessageType.TASK_CREATED)
    
    def test_broadcast(self):
        """Test broadcast messaging"""
        # Subscribe multiple phases
        self.bus.subscribe("coding", [MessageType.OBJECTIVE_ACTIVATED])
        self.bus.subscribe("qa", [MessageType.OBJECTIVE_ACTIVATED])
        self.bus.subscribe("debugging", [MessageType.OBJECTIVE_ACTIVATED])
        
        # Broadcast
        msg = self.bus.broadcast(
            sender="coordinator",
            message_type=MessageType.OBJECTIVE_ACTIVATED,
            payload={"objective_id": "primary_001"}
        )
        
        # All subscribers should receive
        self.assertEqual(len(self.bus.get_messages("coding")), 1)
        self.assertEqual(len(self.bus.get_messages("qa")), 1)
        self.assertEqual(len(self.bus.get_messages("debugging")), 1)
    
    def test_message_filtering(self):
        """Test message filtering by type and priority"""
        # Send various messages
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {"id": "1"}, priority=MessagePriority.HIGH)
        self.bus.send_direct("planning", "coding", MessageType.TASK_STARTED, 
                           {"id": "2"}, priority=MessagePriority.NORMAL)
        self.bus.send_direct("planning", "coding", MessageType.TASK_COMPLETED, 
                           {"id": "3"}, priority=MessagePriority.CRITICAL)
        
        # Filter by type
        created = self.bus.get_messages("coding", 
                                       message_types=[MessageType.TASK_CREATED])
        self.assertEqual(len(created), 1)
        
        # Filter by priority
        critical = self.bus.get_messages("coding", 
                                        priority=MessagePriority.CRITICAL)
        self.assertEqual(len(critical), 1)
    
    def test_message_clearing(self):
        """Test clearing messages from queue"""
        # Send messages
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, {"id": "1"})
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, {"id": "2"})
        
        self.assertEqual(len(self.bus.get_messages("coding")), 2)
        
        # Clear all
        cleared = self.bus.clear_messages("coding")
        self.assertEqual(cleared, 2)
        self.assertEqual(len(self.bus.get_messages("coding")), 0)
    
    def test_statistics(self):
        """Test message bus statistics"""
        # Send various messages
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, {})
        self.bus.broadcast("coordinator", MessageType.OBJECTIVE_ACTIVATED, {})
        
        stats = self.bus.get_statistics()
        self.assertEqual(stats['total_published'], 2)
        self.assertEqual(stats['total_direct'], 1)
        self.assertEqual(stats['total_broadcast'], 1)
    
    def test_message_search(self):
        """Test message search functionality"""
        # Send messages with different attributes
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {}, objective_id="primary_001", task_id="task_001")
        self.bus.send_direct("qa", "debugging", MessageType.ISSUE_FOUND, 
                           {}, objective_id="primary_001", issue_id="issue_001")
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {}, objective_id="secondary_001", task_id="task_002")
        
        # Search by objective
        results = self.bus.search_messages(objective_id="primary_001")
        self.assertEqual(len(results), 2)
        
        # Search by sender
        results = self.bus.search_messages(sender="planning")
        self.assertEqual(len(results), 2)
        
        # Search by message type
        results = self.bus.search_messages(
            message_types=[MessageType.TASK_CREATED]
        )
        self.assertEqual(len(results), 2)
    
    def test_priority_ordering(self):
        """Test that messages are ordered by priority"""
        # Send messages with different priorities
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {"id": "1"}, priority=MessagePriority.NORMAL)
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {"id": "2"}, priority=MessagePriority.CRITICAL)
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, 
                           {"id": "3"}, priority=MessagePriority.HIGH)
        
        messages = self.bus.get_messages("coding")
        
        # Should be ordered: CRITICAL, HIGH, NORMAL
        self.assertEqual(messages[0].priority, MessagePriority.CRITICAL)
        self.assertEqual(messages[1].priority, MessagePriority.HIGH)
        self.assertEqual(messages[2].priority, MessagePriority.NORMAL)
    
    def test_handler_registration(self):
        """Test message handler registration and execution"""
        handled_messages = []
        
        def handler(msg: Message):
            handled_messages.append(msg)
        
        # Register handler
        self.bus.register_handler("coding", MessageType.TASK_CREATED, handler)
        
        # Send message
        self.bus.send_direct("planning", "coding", MessageType.TASK_CREATED, {})
        
        # Handler should have been called
        self.assertEqual(len(handled_messages), 1)


class TestRequestResponse(unittest.TestCase):
    """Test request-response pattern"""
    
    def setUp(self):
        """Set up test message bus"""
        self.bus = MessageBus()
    
    def test_request_response_success(self):
        """Test successful request-response"""
        # Simulate responder in separate thread
        def responder():
            time.sleep(0.1)  # Simulate processing
            messages = self.bus.get_messages("responder")
            if messages:
                request = messages[0]
                self.bus.send_response(
                    request,
                    sender="responder",
                    payload={"result": "success"}
                )
        
        import threading
        thread = threading.Thread(target=responder)
        thread.start()
        
        # Send request
        response = self.bus.request_response(
            sender="requester",
            recipient="responder",
            message_type=MessageType.PHASE_REQUEST,
            payload={"action": "test"},
            timeout=2
        )
        
        thread.join()
        
        # Should receive response
        self.assertIsNotNone(response)
        self.assertEqual(response.payload["result"], "success")
    
    def test_request_response_timeout(self):
        """Test request-response timeout"""
        # Send request with no responder
        response = self.bus.request_response(
            sender="requester",
            recipient="nonexistent",
            message_type=MessageType.PHASE_REQUEST,
            payload={"action": "test"},
            timeout=1
        )
        
        # Should timeout
        self.assertIsNone(response)


if __name__ == '__main__':
    unittest.main()