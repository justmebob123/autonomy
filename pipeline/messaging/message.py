"""
Message classes for the Message Bus System

Defines the core message structure and enumerations for message types and priorities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid


class MessageType(Enum):
    """Types of messages that can be sent through the message bus"""
    
    # Task lifecycle events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"
    
    # Issue lifecycle events
    ISSUE_FOUND = "issue_found"
    ISSUE_ASSIGNED = "issue_assigned"
    ISSUE_IN_PROGRESS = "issue_in_progress"
    ISSUE_RESOLVED = "issue_resolved"
    ISSUE_VERIFIED = "issue_verified"
    ISSUE_CLOSED = "issue_closed"
    ISSUE_REOPENED = "issue_reopened"
    
    # Objective lifecycle events
    OBJECTIVE_ACTIVATED = "objective_activated"
    OBJECTIVE_BLOCKED = "objective_blocked"
    OBJECTIVE_DEGRADING = "objective_degrading"
    OBJECTIVE_CRITICAL = "objective_critical"
    OBJECTIVE_COMPLETED = "objective_completed"
    OBJECTIVE_DOCUMENTED = "objective_documented"
    
    # Phase coordination events
    PHASE_TRANSITION = "phase_transition"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_ERROR = "phase_error"
    PHASE_REQUEST = "phase_request"
    PHASE_RESPONSE = "phase_response"
    PHASE_TIMEOUT = "phase_timeout"
    
    # System events
    SYSTEM_ALERT = "system_alert"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"
    HEALTH_CHECK = "health_check"
    HEALTH_DEGRADED = "health_degraded"
    HEALTH_RECOVERED = "health_recovered"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_QA_PASSED = "file_qa_passed"
    FILE_QA_FAILED = "file_qa_failed"
    
    # Analytics events
    PREDICTION_GENERATED = "prediction_generated"
    ANOMALY_DETECTED = "anomaly_detected"
    TREND_IDENTIFIED = "trend_identified"
    METRIC_UPDATED = "metric_updated"


class MessagePriority(Enum):
    """Priority levels for messages"""
    CRITICAL = 0  # Immediate attention required
    HIGH = 1      # Important, handle soon
    NORMAL = 2    # Standard priority
    LOW = 3       # Can be deferred


@dataclass
class Message:
    """
    A message in the message bus system.
    
    Messages are the primary means of communication between phases,
    enabling structured, auditable, and intelligent coordination.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Routing information
    sender: str = ""  # Phase name that sent the message
    recipient: str = ""  # Phase name or "broadcast" for all phases
    
    # Message classification
    message_type: MessageType = MessageType.SYSTEM_INFO
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Message content
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Context linking
    objective_id: Optional[str] = None
    task_id: Optional[str] = None
    issue_id: Optional[str] = None
    file_path: Optional[str] = None
    
    # Request-response pattern
    requires_response: bool = False
    response_timeout: Optional[int] = None  # Seconds
    in_response_to: Optional[str] = None  # Message ID this responds to
    
    # Metadata
    tags: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'sender': self.sender,
            'recipient': self.recipient,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'payload': self.payload,
            'objective_id': self.objective_id,
            'task_id': self.task_id,
            'issue_id': self.issue_id,
            'file_path': self.file_path,
            'requires_response': self.requires_response,
            'response_timeout': self.response_timeout,
            'in_response_to': self.in_response_to,
            'tags': self.tags,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        # Convert string timestamp back to datetime
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Convert string enums back to enum objects
        if isinstance(data.get('message_type'), str):
            data['message_type'] = MessageType(data['message_type'])
        
        if isinstance(data.get('priority'), (str, int)):
            if isinstance(data['priority'], str):
                data['priority'] = MessagePriority[data['priority']]
            else:
                data['priority'] = MessagePriority(data['priority'])
        
        return cls(**data)
    
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message"""
        return self.recipient == "broadcast" or self.recipient == "*"
    
    def is_for_recipient(self, recipient: str) -> bool:
        """Check if this message is for the given recipient"""
        return self.is_broadcast() or self.recipient == recipient
    
    def is_critical(self) -> bool:
        """Check if this is a critical priority message"""
        return self.priority == MessagePriority.CRITICAL
    
    def is_high_priority(self) -> bool:
        """Check if this is high or critical priority"""
        return self.priority in (MessagePriority.CRITICAL, MessagePriority.HIGH)
    
    def __str__(self) -> str:
        """String representation of message"""
        return (f"Message({self.message_type.value}, "
                f"from={self.sender}, to={self.recipient}, "
                f"priority={self.priority.name})")
    
    def __repr__(self) -> str:
        """Detailed representation of message"""
        return (f"Message(id={self.id}, type={self.message_type.value}, "
                f"sender={self.sender}, recipient={self.recipient}, "
                f"priority={self.priority.name}, "
                f"timestamp={self.timestamp.isoformat()})")