"""
Custom Tools Integration Package

Provides integration between scripts/custom_tools/ and the pipeline system.

Components:
- ToolRegistry: Discovers and registers custom tools
- CustomToolHandler: Executes custom tools with isolation
- ToolDefinitionGenerator: Generates OpenAI-compatible definitions
- ToolDeveloper: Supports tool creation and testing
"""

from .registry import ToolRegistry
from .handler import CustomToolHandler
from .definition import ToolDefinitionGenerator

__all__ = [
    'ToolRegistry',
    'CustomToolHandler',
    'ToolDefinitionGenerator',
]

__version__ = '1.0.0'