"""
Anti-Pattern Detector - Detects code anti-patterns and smells.
"""

import ast
from typing import List, Dict, Any


class AntiPatternDetector(ast.NodeVisitor):
    """Detects anti-patterns in code."""
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.antipatterns: List[Dict[str, Any]] = []
    
    def detect(self) -> List[Dict[str, Any]]:
        """Detect anti-patterns."""
        self.visit(self.tree)
        return self.antipatterns
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function for anti-patterns."""
        # Check for too many parameters
        if len(node.args.args) > 7:
            self.antipatterns.append({
                'name': 'Too Many Parameters',
                'location': node.name,
                'line': node.lineno,
                'severity': 'MEDIUM',
                'message': f"Function '{node.name}' has {len(node.args.args)} parameters (max recommended: 7)",
            })
        
        self.generic_visit(node)