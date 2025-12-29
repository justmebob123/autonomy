"""
AST Helper utilities for code analysis.
"""

import ast
from typing import List, Optional


class ASTHelper:
    """Helper functions for AST manipulation."""
    
    @staticmethod
    def get_function_names(tree: ast.AST) -> List[str]:
        """Get all function names in AST."""
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
    
    @staticmethod
    def get_class_names(tree: ast.AST) -> List[str]:
        """Get all class names in AST."""
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]
    
    @staticmethod
    def find_function(tree: ast.AST, name: str) -> Optional[ast.FunctionDef]:
        """Find function by name."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None