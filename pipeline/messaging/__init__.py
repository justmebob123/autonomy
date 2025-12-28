"""
Message Bus System for Autonomy Pipeline

This module provides structured, event-driven communication between phases.
It enables real-time coordination, full audit trails, and intelligent routing.
"""

from .message import Message, MessageType, MessagePriority
from .message_bus import MessageBus

__all__ = [
    'Message',
    'MessageType',
    'MessagePriority',
    'MessageBus',
]