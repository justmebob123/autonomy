"""
Native Complexity Analyzer

Reimplemented from scripts/analysis/COMPLEXITY_ANALYZER.py as a native pipeline tool.
Calculates cyclomatic complexity for all functions and methods.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from pipeline.logging_setup import get_logger


@dataclass
class ComplexityResult:
    """Result of complexity analysis for a single function/method."""
    name: str
    file: str
    line: int
    complexity: int
    lines: int
    
    @property
    def priority(self) -> str:
        """Get refactoring priority based on complexity."""
        if self.complexity >= 50:
            return "CRITICAL"
        elif self.complexity >= 30:
            return "URGENT"
        elif self.complexity >= 20:
            return "HIGH"
        elif self.complexity >= 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    @property
    def effort_days(self) -> str:
        """Estimate refactoring effort in days."""
        if self.complexity >= 100:
            return "7-10 days"
        elif self.complexity >= 50:
            return "5-7 days"
        elif self.complexity >= 30:
            return "3-5 days"
        elif self.complexity >= 20:
            return "2-3 days"
        elif self.complexity >= 10:
            return "1-2 days"
        else:
            return "<1 day"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'file': self.file,
            'line': self.line,
            'complexity': self.complexity,
            'lines': self.lines,
            'priority': self.priority,
            'effort_days': self.effort_days
        }


@dataclass
class ComplexityAnalysisResult:
    """Complete result of complexity analysis."""
    results: List[ComplexityResult] = field(default_factory=list)
    total_functions: int = 0
    average_complexity: float = 0.0
    max_complexity: int = 0
    critical_count: int = 0
    urgent_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'results': [r.to_dict() for r in self.results],
            'total_functions': self.total_functions,
            'average_complexity': self.average_complexity,
            'max_complexity': self.max_complexity,
            'distribution': {
                'critical': self.critical_count,
                'urgent': self.urgent_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count
            }
        }


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating complexity."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.results: List[ComplexityResult] = []
        self.current_class = None
    
    def calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function/method."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            pass
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            # Logical operators
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Comprehensions
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
        
        return complexity
    
    def count_lines(self, node: ast.AST) -> int:
        """Count lines of code in a function."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        complexity = self.calculate_complexity(node)
        lines = self.count_lines(node)
        
        if self.current_class:
            name = f"{self.current_class}.{node.name}"
        else:
            name = node.name
        
        result = ComplexityResult(
            name=name,
            file=self.filepath,
            line=node.lineno,
            complexity=complexity,
            lines=lines
        )
        self.results.append(result)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class


class ComplexityAnalyzer:
    """
    Native complexity analyzer.
    
    Analyzes Python code to calculate cyclomatic complexity for all
    functions and methods, identifying refactoring priorities.
    
    Example:
        analyzer = ComplexityAnalyzer('/project')
        result = analyzer.analyze()
        
        # Get critical functions
        critical = [r for r in result.results if r.priority == 'CRITICAL']
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize complexity analyzer.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        self.results: List[ComplexityResult] = []
    
    def analyze_file(self, filepath: Path) -> List[ComplexityResult]:
        """
        Analyze a single Python file.
        
        Args:
            filepath: Path to Python file
        
        Returns:
            List of complexity results
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            visitor = ComplexityVisitor(str(filepath.relative_to(self.project_dir)))
            visitor.visit(tree)
            
            return visitor.results
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {filepath}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error analyzing {filepath}: {e}")
            return []
    
    def analyze(self, target: Optional[str] = None) -> ComplexityAnalysisResult:
        """
        Analyze complexity of Python files.
        
        Args:
            target: Optional specific file or directory (relative to project_dir)
        
        Returns:
            ComplexityAnalysisResult with all findings
        """
        self.results = []
        
        if target:
            target_path = self.project_dir / target
        else:
            target_path = self.project_dir
        
        if not target_path.exists():
            self.logger.error(f"Target not found: {target_path}")
            return ComplexityAnalysisResult()
        
        # Analyze files
        if target_path.is_file():
            if target_path.suffix == '.py':
                self.results.extend(self.analyze_file(target_path))
        else:
            pass
            # Analyze directory
            for root, dirs, files in os.walk(target_path):
                pass
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        filepath = Path(root) / file
                        self.results.extend(self.analyze_file(filepath))
        
        # Calculate statistics
        return self._calculate_statistics()
    
    def _calculate_statistics(self) -> ComplexityAnalysisResult:
        """Calculate statistics from results."""
        if not self.results:
            return ComplexityAnalysisResult()
        
        # Sort by complexity
        sorted_results = sorted(self.results, key=lambda x: x.complexity, reverse=True)
        
        # Calculate counts
        critical = [r for r in sorted_results if r.complexity >= 50]
        urgent = [r for r in sorted_results if 30 <= r.complexity < 50]
        high = [r for r in sorted_results if 20 <= r.complexity < 30]
        medium = [r for r in sorted_results if 10 <= r.complexity < 20]
        low = [r for r in sorted_results if r.complexity < 10]
        
        # Calculate average
        total_complexity = sum(r.complexity for r in sorted_results)
        avg_complexity = total_complexity / len(sorted_results)
        
        return ComplexityAnalysisResult(
            results=sorted_results,
            total_functions=len(sorted_results),
            average_complexity=avg_complexity,
            max_complexity=sorted_results[0].complexity if sorted_results else 0,
            critical_count=len(critical),
            urgent_count=len(urgent),
            high_count=len(high),
            medium_count=len(medium),
            low_count=len(low)
        )
    
    def generate_report(self, result: ComplexityAnalysisResult) -> str:
        """
        Generate text report from analysis result.
        
        Args:
            result: Analysis result
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CYCLOMATIC COMPLEXITY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Top 20 most complex
        lines.append("## TOP 20 MOST COMPLEX FUNCTIONS")
        lines.append("")
        lines.append(f"{'Rank':<6} {'Complexity':<12} {'Priority':<12} {'Effort':<15} {'Function':<50} {'File:Line'}")
        lines.append("-" * 150)
        
        for i, r in enumerate(result.results[:20], 1):
            lines.append(f"{i:<6} {r.complexity:<12} {r.priority:<12} {r.effort_days:<15} {r.name:<50} {r.file}:{r.line}")
        lines.append("")
        
        # Distribution
        lines.append("## COMPLEXITY DISTRIBUTION")
        lines.append("")
        lines.append(f"CRITICAL (>=50): {result.critical_count} functions")
        lines.append(f"URGENT (30-49): {result.urgent_count} functions")
        lines.append(f"HIGH (20-29): {result.high_count} functions")
        lines.append(f"MEDIUM (10-19): {result.medium_count} functions")
        lines.append(f"LOW (<10): {result.low_count} functions")
        lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY STATISTICS")
        lines.append("=" * 80)
        lines.append(f"Total functions analyzed: {result.total_functions}")
        lines.append(f"Average complexity: {result.average_complexity:.2f}")
        lines.append(f"Maximum complexity: {result.max_complexity}")
        lines.append(f"Functions needing refactoring (>=10): {result.critical_count + result.urgent_count + result.high_count + result.medium_count}")
        lines.append("")
        
        return "\n".join(lines)