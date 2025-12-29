#!/usr/bin/env python3
"""
CodeComplexity - Analyze code complexity metrics

Analyzes Python files for cyclomatic complexity, lines of code, and other metrics.
"""

from pathlib import Path
import ast
from core.base import BaseTool, ToolResult


class CodeComplexity(BaseTool):
    """Analyze code complexity metrics for Python files."""
    
    # Tool metadata
    name = "code_complexity"
    description = "Analyze cyclomatic complexity and code metrics for Python files"
    version = "1.0.0"
    category = "analysis"
    author = "NinjaTech AI"
    
    # Security settings
    requires_filesystem = True
    requires_network = False
    requires_subprocess = False
    timeout_seconds = 30
    max_file_size_mb = 10
    
    def execute(self, filepath: str) -> ToolResult:
        """
        Execute complexity analysis.
        
        Args:
            filepath: Path to Python file (relative to project root)
            
        Returns:
            ToolResult with complexity metrics
        """
        try:
            # Validate input
            if not filepath.endswith('.py'):
                return ToolResult(
                    success=False,
                    error="File must be a Python file (.py)"
                )
            
            # Get full path
            full_path = self.project_dir / filepath
            
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {filepath}"
                )
            
            # Read and parse file
            content = full_path.read_text()
            
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return ToolResult(
                    success=False,
                    error=f"Syntax error in file: {e}"
                )
            
            # Analyze complexity
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'complexity': complexity,
                        'lines': self._count_lines(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
            
            # Calculate metrics
            total_lines = len(content.splitlines())
            total_functions = len(functions)
            total_classes = len(classes)
            
            avg_complexity = sum(f['complexity'] for f in functions) / total_functions if total_functions > 0 else 0
            max_complexity = max((f['complexity'] for f in functions), default=0)
            
            # Sort functions by complexity
            functions.sort(key=lambda x: x['complexity'], reverse=True)
            
            # Return result
            return ToolResult(
                success=True,
                result={
                    'filepath': filepath,
                    'metrics': {
                        'total_lines': total_lines,
                        'total_functions': total_functions,
                        'total_classes': total_classes,
                        'average_complexity': round(avg_complexity, 2),
                        'max_complexity': max_complexity
                    },
                    'functions': functions[:10],  # Top 10 most complex
                    'classes': classes
                },
                metadata={
                    'filepath': filepath,
                    'analysis_type': 'complexity'
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Analysis failed: {e}"
            )
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _count_lines(self, node: ast.FunctionDef) -> int:
        """Count lines in a function."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 0


# CLI interface for subprocess execution
if __name__ == '__main__':
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-dir', required=True)
    parser.add_argument('--args', required=True)
    args = parser.parse_args()
    
    # Parse arguments
    tool_args = json.loads(args.args)
    
    # Create and run tool
    tool = CodeComplexity(args.project_dir)
    result = tool.run(**tool_args)
    
    # Output result as JSON
    print(json.dumps(result.to_dict()))
    sys.exit(0 if result.success else 1)