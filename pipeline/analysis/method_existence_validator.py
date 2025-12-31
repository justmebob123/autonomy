"""
Method Existence Validator

Validates that methods called on objects actually exist on their classes.
"""

import ast
from typing import Dict, List, Set
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MethodExistenceError:
    """Represents a method existence validation error."""
    file: str
    line: int
    class_name: str
    method_name: str
    message: str
    severity: str


class MethodExistenceValidator:
    """Validates that methods exist on classes before being called."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[MethodExistenceError] = []
        self.class_methods: Dict[str, Set[str]] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all method calls in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect class methods
        self._collect_class_methods()
        
        # Second pass: validate method calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': err.file,
                    'line': err.line,
                    'class_name': err.class_name,
                    'method_name': err.method_name,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'classes_analyzed': len(self.class_methods),
            'by_severity': self._count_by_severity()
        }
    
    def _collect_class_methods(self):
        """Collect all methods defined in classes."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        methods = set()
                        
                        # Collect all methods in this class
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                methods.add(item.name)
                        
                        self.class_methods[class_name] = methods
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path):
        """Validate all method calls in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Track variable types (simple heuristic)
            var_types = {}
            
            for node in ast.walk(tree):
                # Track assignments to infer types
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            class_name = node.value.func.id
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    var_types[target.id] = class_name
                
                # Check method calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        self._validate_method_call(node, filepath, var_types)
                        
        except Exception:
            pass
    
    def _validate_method_call(self, node: ast.Call, filepath: Path, var_types: Dict[str, str]):
        """Validate a single method call."""
        if not isinstance(node.func, ast.Attribute):
            return
        
        method_name = node.func.attr
        
        # Try to determine the class
        class_name = None
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            class_name = var_types.get(var_name)
        
        # If we know the class, check if method exists
        if class_name and class_name in self.class_methods:
            if method_name not in self.class_methods[class_name]:
                # Check if it's a common built-in method
                common_methods = {'get', 'items', 'keys', 'values', 'append', 'extend', 
                                'pop', 'remove', 'add', 'update', 'clear', 'copy'}
                
                if method_name not in common_methods:
                    self.errors.append(MethodExistenceError(
                        file=str(filepath.relative_to(self.project_root)),
                        line=node.lineno,
                        class_name=class_name,
                        method_name=method_name,
                        message=f"Method '{method_name}' does not exist on class '{class_name}'",
                        severity='critical'
                    ))
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts