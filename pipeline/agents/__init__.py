"""
Multi-Agent System

Provides specialist agents for consultation and collaboration.
"""

from .tool_advisor import ToolAdvisor
from .consultation import ConsultationManager

__all__ = ['ToolAdvisor', 'ConsultationManager']