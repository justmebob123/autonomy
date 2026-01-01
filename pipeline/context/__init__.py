"""
Context Providers

Provides various types of context for AI decision making.
"""

from .architectural import ArchitecturalContextProvider, PlacementRule, ValidationResult
from .error import ErrorContext
from .code import CodeContext

__all__ = [
    'ArchitecturalContextProvider',
    'PlacementRule',
    'ValidationResult',
    'ErrorContext',
    'CodeContext',
]
