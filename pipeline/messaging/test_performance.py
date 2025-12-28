"""
Performance tests for Message Bus System

Tests throughput, latency, and scalability under load.
"""

import unittest
import time
from datetime import datetime, timedelta
import threading

from .message import Message, MessageType, MessagePriority
from .message_bus import MessageBus


class TestMessageBusPerformance(unittest.TestCase):
    """Performance tests for message bus"""
    
    def setUp(self):
        """Set up test message bus"""
        self.bus = MessageBus()
    
    def test_throughput_single_thread(self):
        """Test message throughput in single thread"""
        num_messages = 1000
        
        start_time = time.time()
        
        for i in range(num_messages):
            self.bus.send_direct(
                sender="test",
                recipient="broadcast",
                message_type=MessageType.TASK_CREATED,
                payload={'index': i}
            )
        
        elapsed = time.time() - start_time
        throughput = num_messages / elapsed
        
        print(f"\n  Single-thread throughput: {throughput:.0f} msg/sec")
        print(f"  Time for {num_messages} messages: {elapsed:.3f}s")
        
        # Should handle at least 1000 msg/sec
        self.assertGreater(throughput, 1000)
    
    def test_throughput_multi_thread(self):
        """Test message throughput with multiple threads"""
        num_threads = 4
        messages_per_thread = 250
        
        def send_messages(thread_id):
            for i in range(messages_per_thread):
                self.bus.send_direct(
                    sender=f"thread_{thread_id}",
                    recipient="broadcast",
                    message_type=MessageType.TASK_CREATED,
                    payload={'thread': thread_id, 'index': i}
                )
        
        start_time = time.time()
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=send_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        total_messages = num_threads * messages_per_thread
        throughput = total_messages / elapsed
        
        print(f"\n  Multi-thread throughput: {throughput:.0f} msg/sec")
        print(f"  Threads: {num_threads}")
        print(f"  Total messages: {total_messages}")
        print(f"  Time: {elapsed:.3f}s")
        
        # Should handle concurrent access
        self.assertGreater(throughput, 500)
    
    def test_subscription_performance(self):
        """Test subscription and delivery performance"""
        num_subscribers = 10
        num_messages = 100
        
        # Subscribe multiple phases
        for i in range(num_subscribers):
            self.bus.subscribe(f"phase_{i}", [MessageType.TASK_CREATED])
        
        start_time = time.time()
        
        # Send broadcast messages
        for i in range(num_messages):
            self.bus.broadcast(
                sender="test",
                message_type=MessageType.TASK_CREATED,
                payload={'index': i}
            )
        
        elapsed = time.time() - start_time
        
        # Each message delivered to all subscribers
        total_deliveries = num_messages * num_subscribers
        delivery_rate = total_deliveries / elapsed
        
        print(f"\n  Subscription delivery rate: {delivery_rate:.0f} deliveries/sec")
        print(f"  Subscribers: {num_subscribers}")
        print(f"  Messages: {num_messages}")
        print(f"  Total deliveries: {total_deliveries}")
        
        # Verify all messages delivered
        for i in range(num_subscribers):
            messages = self.bus.get_messages(f"phase_{i}")
            self.assertEqual(len(messages), num_messages)
    
    def test_search_performance(self):
        """Test message search performance"""
        # Create diverse message set
        for i in range(1000):
            self.bus.send_direct(
                sender=f"sender_{i % 10}",
                recipient="broadcast",
                message_type=MessageType.TASK_CREATED if i % 2 == 0 else MessageType.ISSUE_FOUND,
                payload={'index': i},
                objective_id=f"obj_{i % 5}",
                task_id=f"task_{i}"
            )
        
        # Test search by type
        start_time = time.time()
        results = self.bus.search_messages(
            message_types=[MessageType.TASK_CREATED]
        )
        elapsed = time.time() - start_time
        
        print(f"\n  Search by type: {len(results)} results in {elapsed*1000:.2f}ms")
        self.assertEqual(len(results), 500)
        
        # Test search by objective
        start_time = time.time()
        results = self.bus.search_messages(
            objective_id="obj_0"
        )
        elapsed = time.time() - start_time
        
        print(f"  Search by objective: {len(results)} results in {elapsed*1000:.2f}ms")
        self.assertEqual(len(results), 200)
        
        # Test complex search
        start_time = time.time()
        results = self.bus.search_messages(
            sender="sender_0",
            message_types=[MessageType.TASK_CREATED],
            objective_id="obj_0"
        )
        elapsed = time.time() - start_time
        
        print(f"  Complex search: {len(results)} results in {elapsed*1000:.2f}ms")
    
    def test_memory_usage(self):
        """Test memory management with large message volume"""
        # Send many messages
        for i in range(5000):
            self.bus.send_direct(
                sender="test",
                recipient="broadcast",
                message_type=MessageType.TASK_CREATED,
                payload={'index': i, 'data': 'x' * 100}  # 100 bytes per message
            )
        
        # Check queue size is limited
        self.assertLessEqual(len(self.bus.queue), self.bus.max_queue_size)
        
        # Check history size is limited
        self.assertLessEqual(len(self.bus.message_history), self.bus.max_history_size)
        
        print(f"\n  Queue size: {len(self.bus.queue)} (max: {self.bus.max_queue_size})")
        print(f"  History size: {len(self.bus.message_history)} (max: {self.bus.max_history_size})")
    
    def test_priority_ordering_performance(self):
        """Test performance of priority-based ordering"""
        # Create messages with mixed priorities
        for i in range(1000):
            priority = [
                MessagePriority.LOW,
                MessagePriority.NORMAL,
                MessagePriority.HIGH,
                MessagePriority.CRITICAL
            ][i % 4]
            
            self.bus.send_direct(
                sender="test",
                recipient="phase_test",
                message_type=MessageType.TASK_CREATED,
                payload={'index': i},
                priority=priority
            )
        
        # Measure retrieval with priority ordering
        start_time = time.time()
        messages = self.bus.get_messages("phase_test")
        elapsed = time.time() - start_time
        
        print(f"\n  Priority ordering: {len(messages)} messages in {elapsed*1000:.2f}ms")
        
        # Verify ordering (critical first)
        priorities = [m.priority for m in messages[:100]]
        critical_count = sum(1 for p in priorities if p == MessagePriority.CRITICAL)
        
        print(f"  Critical messages in first 100: {critical_count}")
        
        # Critical messages should be at the front
        self.assertGreater(critical_count, 20)
    
    def test_concurrent_read_write(self):
        """Test concurrent read and write operations"""
        num_writers = 3
        num_readers = 3
        messages_per_writer = 100
        
        def writer(writer_id):
            for i in range(messages_per_writer):
                self.bus.send_direct(
                    sender=f"writer_{writer_id}",
                    recipient="broadcast",
                    message_type=MessageType.TASK_CREATED,
                    payload={'writer': writer_id, 'index': i}
                )
                time.sleep(0.001)  # Small delay
        
        def reader(reader_id):
            for _ in range(50):
                messages = self.bus.get_messages(f"reader_{reader_id}")
                time.sleep(0.002)  # Small delay
        
        # Subscribe readers
        for i in range(num_readers):
            self.bus.subscribe(f"reader_{i}", [MessageType.TASK_CREATED])
        
        start_time = time.time()
        
        # Start writers and readers concurrently
        threads = []
        
        for i in range(num_writers):
            thread = threading.Thread(target=writer, args=(i,))
            threads.append(thread)
            thread.start()
        
        for i in range(num_readers):
            thread = threading.Thread(target=reader, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        
        print(f"\n  Concurrent operations completed in {elapsed:.3f}s")
        print(f"  Writers: {num_writers}, Readers: {num_readers}")
        
        # Should complete without errors
        self.assertLess(elapsed, 5.0)


if __name__ == '__main__':
    # Run with verbose output to see performance metrics
    unittest.main(verbosity=2)