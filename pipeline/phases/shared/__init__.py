"""
Shared infrastructure for all phases.

This package contains common utilities, base classes, and shared components
used across multiple phases to eliminate code duplication.
"""

from .status_formatter import StatusFormatter
from .base_prompt_builder import BasePromptBuilder
from .base_orchestrator import BaseOrchestrator

__all__ = [
    'StatusFormatter',
    'BasePromptBuilder',
    'BaseOrchestrator',
]