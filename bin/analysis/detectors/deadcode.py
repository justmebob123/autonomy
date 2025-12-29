"""
Dead Code Detector - Finds unused code.
"""

import ast
from typing import Dict, Set, Any


class DeadCodeDetector(ast.NodeVisitor):
    """Detects unused code."""
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()
    
    def detect(self) -> Dict[str, Any]:
        """Detect dead code."""
        self.visit(self.tree)
        
        unused = self.defined_functions - self.called_functions
        
        return {
            'unused_functions': list(unused),
            'total_functions': len(self.defined_functions),
            'used_functions': len(self.called_functions),
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definition."""
        self.defined_functions.add(node.name)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Track function call."""
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        self.generic_visit(node)