"""
Base Issue Formatter

Abstract base class for formatting refactoring issue data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IssueFormatter(ABC):
    """Base class for issue formatters."""
    
    def format(self, data: dict) -> str:
        """
        Format issue data into clear, actionable text.
        
        Args:
            data: Raw analysis data dictionary
        
        Returns:
            Formatted string with clear action items
        """
        # Default implementation for unknown types
        if not data:
            return "No analysis data available."
        
        # Format as simple key-value pairs
        lines = ["ISSUE DETAILS:"]
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                lines.append(f"- {key}: {len(value)} items")
            else:
                lines.append(f"- {key}: {value}")
        
        lines.append("\nACTION REQUIRED:")
        lines.append("Review the issue and use appropriate refactoring tools to resolve it.")
        
        return "\n".join(lines)