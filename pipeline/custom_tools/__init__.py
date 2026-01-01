"""
Custom Tools Integration Package

Provides integration between scripts/custom_tools/ and the pipeline system.

Components:
- CustomToolRegistry: Discovers and registers custom tools
- CustomToolHandler: Executes custom tools with isolation
- ToolDefinitionGenerator: Generates OpenAI-compatible definitions
- ToolDeveloper: Supports tool creation and testing
"""

from .registry import CustomToolRegistry
from .handler import CustomToolHandler
from .definition import ToolDefinitionGenerator
from .developer import ToolDeveloper

__all__ = [
    'CustomToolRegistry',
    'CustomToolHandler',
    'ToolDefinitionGenerator',
    'ToolDeveloper',
]

__version__ = '1.0.0'