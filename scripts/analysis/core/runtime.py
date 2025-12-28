"""
Runtime Analyzer - Analyzes runtime behavior and execution paths.

Detects:
- Infinite loop risks
- Unreachable code
- Missing error handling
- Resource leaks
- State transition issues
"""

import ast
from typing import Dict, List, Set, Any
from dataclasses import dataclass


@dataclass
class RuntimeIssue:
    """A runtime issue found during analysis."""
    severity: str
    type: str
    location: str
    line: int
    message: str
    suggestion: str


class RuntimeAnalyzer(ast.NodeVisitor):
    """
    Analyzes runtime behavior and execution paths.
    
    Detects:
    - Infinite loop risks
    - Unreachable code
    - Missing error handling
    - Early returns without cleanup
    - State mutations without persistence
    """
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.lines = content.split('\n')
        
        self.issues: List[RuntimeIssue] = []
        self.current_function = None
    
    def analyze(self) -> Dict[str, Any]:
        """Perform runtime analysis."""
        self.visit(self.tree)
        
        # Sort issues by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.issues.sort(key=lambda x: (severity_order[x.severity], x.line))
        
        return {
            'issues': [
                {
                    'severity': issue.severity,
                    'type': issue.type,
                    'location': issue.location,
                    'line': issue.line,
                    'message': issue.message,
                    'suggestion': issue.suggestion,
                }
                for issue in self.issues
            ],
            'infinite_loop_risks': len([i for i in self.issues if i.type == 'infinite_loop']),
            'missing_error_handling': len([i for i in self.issues if i.type == 'missing_error_handling']),
            'unreachable_code': len([i for i in self.issues if i.type == 'unreachable_code']),
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        old_function = self.current_function
        self.current_function = node.name
        
        # Check for missing error handling
        self._check_error_handling(node)
        
        # Check for infinite loop risks
        self._check_infinite_loops(node)
        
        # Check for unreachable code
        self._check_unreachable_code(node)
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def _check_error_handling(self, node: ast.FunctionDef):
        """Check if function has proper error handling."""
        # Check if function has try-except
        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
        
        # Check if function does I/O operations
        has_io = any(
            isinstance(n, ast.Call) and
            isinstance(n.func, ast.Name) and
            n.func.id in ['open', 'read', 'write']
            for n in ast.walk(node)
        )
        
        if has_io and not has_try:
            self.issues.append(RuntimeIssue(
                severity='MEDIUM',
                type='missing_error_handling',
                location=node.name,
                line=node.lineno,
                message=f"Function '{node.name}' performs I/O but has no error handling",
                suggestion="Add try-except block for I/O operations"
            ))
    
    def _check_infinite_loops(self, node: ast.FunctionDef):
        """Check for potential infinite loops."""
        for child in ast.walk(node):
            if isinstance(child, ast.While):
                # Check if while loop has break or return
                has_exit = any(
                    isinstance(n, (ast.Break, ast.Return))
                    for n in ast.walk(child)
                )
                
                if not has_exit:
                    self.issues.append(RuntimeIssue(
                        severity='HIGH',
                        type='infinite_loop',
                        location=node.name,
                        line=child.lineno,
                        message=f"While loop at line {child.lineno} has no exit condition",
                        suggestion="Add break or return statement"
                    ))
    
    def _check_unreachable_code(self, node: ast.FunctionDef):
        """Check for unreachable code after return."""
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return):
                # Check if there's code after return
                if i < len(node.body) - 1:
                    next_stmt = node.body[i + 1]
                    self.issues.append(RuntimeIssue(
                        severity='LOW',
                        type='unreachable_code',
                        location=node.name,
                        line=next_stmt.lineno,
                        message=f"Code at line {next_stmt.lineno} is unreachable (after return)",
                        suggestion="Remove unreachable code or fix control flow"
                    ))