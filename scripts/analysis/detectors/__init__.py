"""
Bug detection modules for the Deep Code Analysis Framework.

These modules detect specific bug patterns discovered during analysis:
- Use before definition
- Missing tool processing
- Incomplete error handling
- State management issues
"""

from .bugs import BugDetector
from .antipatterns import AntiPatternDetector
from .deadcode import DeadCodeDetector
from .parallel import ParallelImplementationDetector

__all__ = [
    'BugDetector',
    'AntiPatternDetector',
    'DeadCodeDetector',
    'ParallelImplementationDetector',
]