"""
Deep Code Analysis Framework

A comprehensive, unified system for performing depth-61 recursive analysis
of Python codebases, detecting bugs, identifying architectural issues, and
ensuring code quality.

This framework integrates all analysis methodologies developed during the
autonomy project examination.
"""

__version__ = "2.0.0"
__author__ = "SuperNinja AI"

from .core.analyzer import DeepCodeAnalyzer
from .core.complexity import ComplexityAnalyzer
from .core.dataflow import DataFlowAnalyzer
from .core.integration import IntegrationAnalyzer
from .core.patterns import PatternDetector
from .core.runtime import RuntimeAnalyzer
from .detectors.bugs import BugDetector
from .detectors.antipatterns import AntiPatternDetector
from .detectors.deadcode import DeadCodeDetector
from .detectors.parallel import ParallelImplementationDetector
from .reporters.markdown import MarkdownReporter
from .reporters.json import JSONReporter
from .utils.ast_helpers import ASTHelper
from .utils.graph import CallGraphBuilder

__all__ = [
    'DeepCodeAnalyzer',
    'ComplexityAnalyzer',
    'DataFlowAnalyzer',
    'IntegrationAnalyzer',
    'PatternDetector',
    'RuntimeAnalyzer',
    'BugDetector',
    'AntiPatternDetector',
    'DeadCodeDetector',
    'ParallelImplementationDetector',
    'MarkdownReporter',
    'JSONReporter',
    'ASTHelper',
    'CallGraphBuilder',
]