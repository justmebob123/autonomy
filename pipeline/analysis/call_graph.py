"""
Native Call Graph Generator

Reimplemented from scripts/analysis/CALL_GRAPH_GENERATOR.py as a native pipeline tool.
Generates comprehensive call graphs for visualization.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging

from pipeline.logging_setup import get_logger


@dataclass
class CallGraphResult:
    """Result of call graph analysis."""
    functions: Dict[str, Tuple[str, int]] = field(default_factory=dict)
    calls: Dict[str, Set[str]] = field(default_factory=dict)
    called_by: Dict[str, Set[str]] = field(default_factory=dict)
    
    @property
    def total_functions(self) -> int:
        return len(self.functions)
    
    @property
    def total_calls(self) -> int:
        return sum(len(callees) for callees in self.calls.values())
    
    def get_most_called(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most called functions."""
        call_counts = {
            func: len(callers)
            for func, callers in self.called_by.items()
        }
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_most_calling(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get functions that call the most other functions."""
        call_counts = {
            func: len(callees)
            for func, callees in self.calls.items()
        }
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'functions': {
                name: {'file': file, 'line': line}
                for name, (file, line) in self.functions.items()
            },
            'calls': {
                caller: list(callees)
                for caller, callees in self.calls.items()
            },
            'statistics': {
                'total_functions': self.total_functions,
                'total_calls': self.total_calls,
                'most_called': [
                    {'function': func, 'call_count': count}
                    for func, count in self.get_most_called()
                ],
                'most_calling': [
                    {'function': func, 'call_count': count}
                    for func, count in self.get_most_calling()
                ]
            }
        }


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor for building call graph."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions: Dict[str, int] = {}
        self.calls: Dict[str, Set[str]] = defaultdict(set)
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name
        
        self.functions[func_name] = node.lineno
        
        old_function = self.current_function
        self.current_function = func_name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node: ast.Call):
        """Visit function/method call."""
        if self.current_function:
            # Track what this function calls
            if isinstance(node.func, ast.Name):
                self.calls[self.current_function].add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Method call
                method_name = node.func.attr
                self.calls[self.current_function].add(method_name)
        
        self.generic_visit(node)


class CallGraphGenerator:
    """
    Native call graph generator.
    
    Generates comprehensive call graphs showing function/method relationships.
    Useful for understanding code flow and dependencies.
    
    Example:
        generator = CallGraphGenerator('/project')
        result = generator.analyze()
        
        # Get most called functions
        for func, count in result.get_most_called(10):
            print(f"{func}: called {count} times")
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize call graph generator.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Global tracking
        self.all_functions: Dict[str, Tuple[str, int]] = {}
        self.all_calls: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze_file(self, filepath: Path):
        """
        Analyze a single Python file.
        
        Args:
            filepath: Path to Python file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            relative_path = str(filepath.relative_to(self.project_dir))
            visitor = CallGraphVisitor(relative_path)
            visitor.visit(tree)
            
            # Aggregate results
            for func_name, line in visitor.functions.items():
                self.all_functions[func_name] = (relative_path, line)
            
            for caller, callees in visitor.calls.items():
                self.all_calls[caller].update(callees)
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Error analyzing {filepath}: {e}")
    
    def analyze(self, target: Optional[str] = None) -> CallGraphResult:
        """
        Analyze call graph in Python files.
        
        Args:
            target: Optional specific file or directory (relative to project_dir)
        
        Returns:
            CallGraphResult with all findings
        """
        # Reset state
        self.all_functions.clear()
        self.all_calls.clear()
        
        if target:
            target_path = self.project_dir / target
        else:
            target_path = self.project_dir
        
        if not target_path.exists():
            self.logger.error(f"Target not found: {target_path}")
            return CallGraphResult()
        
        # Analyze files
        if target_path.is_file():
            if target_path.suffix == '.py':
                self.analyze_file(target_path)
        else:
            # Analyze directory
            for root, dirs, files in os.walk(target_path):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        filepath = Path(root) / file
                        self.analyze_file(filepath)
        
        # Build called_by mapping
        called_by: Dict[str, Set[str]] = defaultdict(set)
        for caller, callees in self.all_calls.items():
            for callee in callees:
                called_by[callee].add(caller)
        
        return CallGraphResult(
            functions=self.all_functions,
            calls=self.all_calls,
            called_by=called_by
        )
    
    def generate_report(self, result: CallGraphResult) -> str:
        """
        Generate text report from analysis result.
        
        Args:
            result: Analysis result
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CALL GRAPH ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Statistics
        lines.append("## STATISTICS")
        lines.append("")
        lines.append(f"Total functions: {result.total_functions}")
        lines.append(f"Total calls: {result.total_calls}")
        lines.append("")
        
        # Most called functions
        lines.append("## TOP 20 MOST CALLED FUNCTIONS")
        lines.append("")
        lines.append(f"{'Rank':<6} {'Call Count':<12} {'Function'}")
        lines.append("-" * 80)
        for i, (func, count) in enumerate(result.get_most_called(20), 1):
            lines.append(f"{i:<6} {count:<12} {func}")
        lines.append("")
        
        # Functions with most calls
        lines.append("## TOP 20 FUNCTIONS WITH MOST CALLS")
        lines.append("")
        lines.append(f"{'Rank':<6} {'Call Count':<12} {'Function'}")
        lines.append("-" * 80)
        for i, (func, count) in enumerate(result.get_most_calling(20), 1):
            lines.append(f"{i:<6} {count:<12} {func}")
        lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total functions analyzed: {result.total_functions}")
        lines.append(f"Total function calls: {result.total_calls}")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_dot(self, result: CallGraphResult, max_nodes: int = 100) -> str:
        """
        Generate DOT format graph for visualization.
        
        Args:
            result: Analysis result
            max_nodes: Maximum number of nodes to include
        
        Returns:
            DOT format string
        """
        lines = []
        lines.append("digraph CallGraph {")
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        lines.append("")
        
        # Get most important functions (most called)
        important_funcs = set(func for func, _ in result.get_most_called(max_nodes))
        
        # Add nodes
        for func in important_funcs:
            if func in result.functions:
                file, line = result.functions[func]
                label = f"{func}\\n{file}:{line}"
                lines.append(f'  "{func}" [label="{label}"];')
        
        lines.append("")
        
        # Add edges
        for caller, callees in result.calls.items():
            if caller in important_funcs:
                for callee in callees:
                    if callee in important_funcs:
                        lines.append(f'  "{caller}" -> "{callee}";')
        
        lines.append("}")
        
        return "\n".join(lines)