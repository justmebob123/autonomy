"""
Context Package

Provides rich context for LLM prompts including error history and code diffs.
"""

from .error import ErrorContext, ErrorRecord
from .code import CodeContext, CodeDiff

__all__ = [
    "ErrorContext",
    "ErrorRecord", 
    "CodeContext",
    "CodeDiff",
]
