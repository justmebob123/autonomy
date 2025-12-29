"""
Call Graph Builder for analyzing function dependencies.
"""

import ast
from typing import Dict, Set, List


class CallGraphBuilder(ast.NodeVisitor):
    """Builds call graph for code analysis."""
    
    def __init__(self, tree: ast.AST):
        self.tree = tree
        self.graph: Dict[str, Set[str]] = {}
        self.current_function = None
    
    def build(self) -> Dict[str, List[str]]:
        """Build call graph."""
        self.visit(self.tree)
        return {k: list(v) for k, v in self.graph.items()}
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        old_function = self.current_function
        self.current_function = node.name
        self.graph[node.name] = set()
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        if self.current_function and isinstance(node.func, ast.Name):
            self.graph[self.current_function].add(node.func.id)
        self.generic_visit(node)