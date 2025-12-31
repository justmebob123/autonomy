"""
Custom Tools Framework

External, isolated, live-reloadable tools for the autonomy pipeline.

This framework provides:
- Process isolation (tools run in subprocess)
- Live reload (no module caching)
- Crash safety (tool crash doesn't crash pipeline)
- Modular architecture (BaseTool pattern)
- Consistent structure (follows scripts/analysis/ model)

Usage:
    from custom_tools import ToolExecutor
    
    executor = ToolExecutor('scripts/custom_tools', '/project')
    result = executor.execute_tool('analyze_imports', {'filepath': 'main.py'})
"""

__version__ = "2.0.0"
__author__ = "SuperNinja AI"

from .core.base import BaseTool, ToolResult
from .core.executor import ToolExecutor
from .core.template import TemplateGenerator
from .core.validator import CustomToolValidator

__all__ = [
    'BaseTool',
    'ToolResult',
    'ToolExecutor',
    'TemplateGenerator',
    'CustomToolValidator',
]