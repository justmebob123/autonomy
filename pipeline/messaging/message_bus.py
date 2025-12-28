"""
Message Bus implementation for phase-to-phase communication

The MessageBus provides structured, event-driven communication between phases
with support for publish-subscribe patterns, direct messaging, and request-response.
"""

from typing import Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import threading
import time

from .message import Message, MessageType, MessagePriority


logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for phase-to-phase communication.
    
    Features:
    - Publish-subscribe pattern
    - Direct messaging
    - Request-response with timeout
    - Priority-based routing
    - Message persistence
    - Full audit trail
    """
    
    def __init__(self, state_manager=None):
        """
        Initialize the message bus.
        
        Args:
            state_manager: Optional StateManager for message persistence
        """
        self.state_manager = state_manager
        
        # Message storage
        self.queue: List[Message] = []
        self.message_history: List[Message] = []
        
        # Subscriptions: message_type -> set of phase names
        self.subscriptions: Dict[MessageType, Set[str]] = defaultdict(set)
        
        # Phase-specific message queues: phase_name -> list of messages
        self.phase_queues: Dict[str, List[Message]] = defaultdict(list)
        
        # Pending responses: message_id -> (response_message, timestamp)
        self.pending_responses: Dict[str, tuple] = {}
        
        # Message handlers: phase_name -> {message_type -> callback}
        self.handlers: Dict[str, Dict[MessageType, Callable]] = defaultdict(dict)
        
        # Statistics
        self.stats = {
            'total_published': 0,
            'total_delivered': 0,
            'total_broadcast': 0,
            'total_direct': 0,
            'by_type': defaultdict(int),
            'by_priority': defaultdict(int),
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Configuration
        self.max_history_size = 10000
        self.max_queue_size = 1000
        self.message_ttl = timedelta(hours=24)  # Messages expire after 24 hours
        
        logger.info("MessageBus initialized")
    
    def publish(self, message: Message) -> None:
        """
        Publish a message to the bus.
        
        The message will be routed to:
        - All subscribers if broadcast
        - Specific recipient if direct
        
        Args:
            message: Message to publish
        """
        with self.lock:
            # Add to queue
            self.queue.append(message)
            
            # Add to history
            self.message_history.append(message)
            
            # Update statistics
            self.stats['total_published'] += 1
            self.stats['by_type'][message.message_type] += 1
            self.stats['by_priority'][message.priority] += 1
            
            if message.is_broadcast():
                self.stats['total_broadcast'] += 1
                # Deliver to all subscribers
                subscribers = self.subscriptions.get(message.message_type, set())
                for phase_name in subscribers:
                    self._deliver_to_phase(phase_name, message)
            else:
                self.stats['total_direct'] += 1
                # Deliver to specific recipient
                self._deliver_to_phase(message.recipient, message)
            
            # Persist if state manager available
            if self.state_manager:
                self._persist_message(message)
            
            # Cleanup old messages
            self._cleanup_old_messages()
            
            logger.debug(f"Published message: {message}")
    
    def subscribe(self, phase_name: str, message_types: List[MessageType]) -> None:
        """
        Subscribe a phase to specific message types.
        
        Args:
            phase_name: Name of the phase subscribing
            message_types: List of message types to subscribe to
        """
        with self.lock:
            for message_type in message_types:
                self.subscriptions[message_type].add(phase_name)
            
            logger.info(f"Phase '{phase_name}' subscribed to {len(message_types)} message types")
    
    def unsubscribe(self, phase_name: str, message_types: Optional[List[MessageType]] = None) -> None:
        """
        Unsubscribe a phase from message types.
        
        Args:
            phase_name: Name of the phase
            message_types: List of message types to unsubscribe from, or None for all
        """
        with self.lock:
            if message_types is None:
                # Unsubscribe from all
                for subscribers in self.subscriptions.values():
                    subscribers.discard(phase_name)
            else:
                for message_type in message_types:
                    self.subscriptions[message_type].discard(phase_name)
            
            logger.info(f"Phase '{phase_name}' unsubscribed")
    
    def get_messages(self, phase_name: str, 
                    since: Optional[datetime] = None,
                    message_types: Optional[List[MessageType]] = None,
                    priority: Optional[MessagePriority] = None,
                    limit: Optional[int] = None) -> List[Message]:
        """
        Get messages for a specific phase.
        
        Args:
            phase_name: Name of the phase
            since: Only return messages after this timestamp
            message_types: Filter by message types
            priority: Filter by priority
            limit: Maximum number of messages to return
        
        Returns:
            List of messages matching the criteria
        """
        with self.lock:
            messages = self.phase_queues.get(phase_name, [])
            
            # Apply filters
            if since:
                messages = [m for m in messages if m.timestamp > since]
            
            if message_types:
                messages = [m for m in messages if m.message_type in message_types]
            
            if priority:
                messages = [m for m in messages if m.priority == priority]
            
            # Sort by priority (critical first) then timestamp
            messages.sort(key=lambda m: (m.priority.value, m.timestamp))
            
            # Apply limit
            if limit:
                messages = messages[:limit]
            
            return messages
    
    def clear_messages(self, phase_name: str, message_ids: Optional[List[str]] = None) -> int:
        """
        Clear messages from a phase's queue.
        
        Args:
            phase_name: Name of the phase
            message_ids: Specific message IDs to clear, or None for all
        
        Returns:
            Number of messages cleared
        """
        with self.lock:
            if phase_name not in self.phase_queues:
                return 0
            
            if message_ids is None:
                # Clear all
                count = len(self.phase_queues[phase_name])
                self.phase_queues[phase_name] = []
                return count
            else:
                # Clear specific messages
                original_count = len(self.phase_queues[phase_name])
                self.phase_queues[phase_name] = [
                    m for m in self.phase_queues[phase_name]
                    if m.id not in message_ids
                ]
                return original_count - len(self.phase_queues[phase_name])
    
    def send_direct(self, sender: str, recipient: str, 
                   message_type: MessageType, payload: Dict,
                   priority: MessagePriority = MessagePriority.NORMAL,
                   **kwargs) -> Message:
        """
        Send a direct message to a specific phase.
        
        Args:
            sender: Name of sending phase
            recipient: Name of receiving phase
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            **kwargs: Additional message fields
        
        Returns:
            The created message
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            priority=priority,
            payload=payload,
            **kwargs
        )
        
        self.publish(message)
        return message
    
    def broadcast(self, sender: str, message_type: MessageType, 
                 payload: Dict,
                 priority: MessagePriority = MessagePriority.NORMAL,
                 **kwargs) -> Message:
        """
        Broadcast a message to all subscribers.
        
        Args:
            sender: Name of sending phase
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            **kwargs: Additional message fields
        
        Returns:
            The created message
        """
        message = Message(
            sender=sender,
            recipient="broadcast",
            message_type=message_type,
            priority=priority,
            payload=payload,
            **kwargs
        )
        
        self.publish(message)
        return message
    
    def request_response(self, sender: str, recipient: str,
                        message_type: MessageType, payload: Dict,
                        timeout: int = 60,
                        priority: MessagePriority = MessagePriority.NORMAL) -> Optional[Message]:
        """
        Send a message and wait for a response.
        
        Args:
            sender: Name of sending phase
            recipient: Name of receiving phase
            message_type: Type of message
            payload: Message payload
            timeout: Timeout in seconds
            priority: Message priority
        
        Returns:
            Response message or None if timeout
        """
        # Send request
        request = Message(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            priority=priority,
            payload=payload,
            requires_response=True,
            response_timeout=timeout
        )
        
        self.publish(request)
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                # Check for response
                if request.id in self.pending_responses:
                    response, _ = self.pending_responses.pop(request.id)
                    return response
            
            time.sleep(0.1)  # Poll every 100ms
        
        # Timeout
        logger.warning(f"Request-response timeout: {request}")
        return None
    
    def send_response(self, original_message: Message, 
                     sender: str, payload: Dict) -> Message:
        """
        Send a response to a message that requires a response.
        
        Args:
            original_message: The message being responded to
            sender: Name of sending phase
            payload: Response payload
        
        Returns:
            The response message
        """
        response = Message(
            sender=sender,
            recipient=original_message.sender,
            message_type=MessageType.PHASE_RESPONSE,
            priority=original_message.priority,
            payload=payload,
            in_response_to=original_message.id
        )
        
        # Store response for request_response to find
        with self.lock:
            self.pending_responses[original_message.id] = (response, datetime.now())
        
        self.publish(response)
        return response
    
    def register_handler(self, phase_name: str, message_type: MessageType,
                        handler: Callable[[Message], None]) -> None:
        """
        Register a handler function for a message type.
        
        Args:
            phase_name: Name of the phase
            message_type: Type of message to handle
            handler: Callback function that takes a Message
        """
        with self.lock:
            self.handlers[phase_name][message_type] = handler
            logger.debug(f"Registered handler for {phase_name}: {message_type.value}")
    
    def get_statistics(self) -> Dict:
        """Get message bus statistics"""
        with self.lock:
            return {
                'total_published': self.stats['total_published'],
                'total_delivered': self.stats['total_delivered'],
                'total_broadcast': self.stats['total_broadcast'],
                'total_direct': self.stats['total_direct'],
                'by_type': dict(self.stats['by_type']),
                'by_priority': dict(self.stats['by_priority']),
                'queue_size': len(self.queue),
                'history_size': len(self.message_history),
                'active_subscriptions': sum(len(s) for s in self.subscriptions.values()),
            }
    
    def search_messages(self, 
                       sender: Optional[str] = None,
                       recipient: Optional[str] = None,
                       message_types: Optional[List[MessageType]] = None,
                       since: Optional[datetime] = None,
                       until: Optional[datetime] = None,
                       objective_id: Optional[str] = None,
                       task_id: Optional[str] = None,
                       issue_id: Optional[str] = None,
                       limit: Optional[int] = None) -> List[Message]:
        """
        Search message history with various filters.
        
        Args:
            sender: Filter by sender
            recipient: Filter by recipient
            message_types: Filter by message types
            since: Messages after this time
            until: Messages before this time
            objective_id: Filter by objective
            task_id: Filter by task
            issue_id: Filter by issue
            limit: Maximum results
        
        Returns:
            List of matching messages
        """
        with self.lock:
            results = self.message_history.copy()
            
            # Apply filters
            if sender:
                results = [m for m in results if m.sender == sender]
            
            if recipient:
                results = [m for m in results if m.recipient == recipient]
            
            if message_types:
                results = [m for m in results if m.message_type in message_types]
            
            if since:
                results = [m for m in results if m.timestamp >= since]
            
            if until:
                results = [m for m in results if m.timestamp <= until]
            
            if objective_id:
                results = [m for m in results if m.objective_id == objective_id]
            
            if task_id:
                results = [m for m in results if m.task_id == task_id]
            
            if issue_id:
                results = [m for m in results if m.issue_id == issue_id]
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda m: m.timestamp, reverse=True)
            
            # Apply limit
            if limit:
                results = results[:limit]
            
            return results
    
    def _deliver_to_phase(self, phase_name: str, message: Message) -> None:
        """
        Deliver a message to a phase's queue.
        
        Args:
            phase_name: Name of the phase
            message: Message to deliver
        """
        self.phase_queues[phase_name].append(message)
        self.stats['total_delivered'] += 1
        
        # Call handler if registered
        if phase_name in self.handlers:
            handler = self.handlers[phase_name].get(message.message_type)
            if handler:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}", exc_info=True)
    
    def _persist_message(self, message: Message) -> None:
        """
        Persist a message to state manager.
        
        Args:
            message: Message to persist
        """
        try:
            # This would integrate with StateManager
            # For now, just log
            logger.debug(f"Persisting message: {message.id}")
        except Exception as e:
            logger.error(f"Error persisting message: {e}")
    
    def _cleanup_old_messages(self) -> None:
        """Remove old messages from history to prevent memory bloat"""
        # Remove expired messages
        cutoff_time = datetime.now() - self.message_ttl
        self.message_history = [
            m for m in self.message_history
            if m.timestamp > cutoff_time
        ]
        
        # Limit history size
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
        
        # Limit queue size
        if len(self.queue) > self.max_queue_size:
            self.queue = self.queue[-self.max_queue_size:]
        
        # Clean up old pending responses
        cutoff = datetime.now() - timedelta(minutes=5)
        expired = [
            msg_id for msg_id, (_, timestamp) in self.pending_responses.items()
            if timestamp < cutoff
        ]
        for msg_id in expired:
            del self.pending_responses[msg_id]