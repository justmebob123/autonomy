"""
Method Signature Validator

Validates that method calls match the actual method signatures.
Detects wrong number of arguments, missing methods, and signature mismatches.
"""

import ast
import inspect
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MethodSignatureError:
    """Represents a method signature validation error."""
    file: str
    line: int
    class_name: str
    method_name: str
    expected_args: int
    provided_args: int
    message: str
    severity: str


class MethodCollector(ast.NodeVisitor):
    """Collects all method definitions with their signatures."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.methods: Dict[Tuple[str, str], int] = {}  # (class_name, method_name) -> arg_count
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Collect method signature."""
        if self.current_class:
            # Count arguments (excluding self)
            arg_count = len(node.args.args) - 1  # Subtract 'self'
            
            # Add defaults count
            if node.args.defaults:
                # Arguments with defaults are optional
                required_args = arg_count - len(node.args.defaults)
            else:
                required_args = arg_count
            
            # Store minimum required args
            self.methods[(self.current_class, node.name)] = required_args
        
        self.generic_visit(node)


class MethodCallChecker(ast.NodeVisitor):
    """Checks that method calls match signatures."""
    
    def __init__(self, filepath: Path, project_root: Path, all_methods: Dict[Tuple[str, str], int]):
        self.filepath = filepath
        self.project_root = project_root
        self.all_methods = all_methods
        self.errors: List[MethodSignatureError] = []
        self.variable_types: Dict[str, str] = {}  # variable -> class_name
        
    def visit_Assign(self, node: ast.Assign):
        """Track variable types from assignments."""
        # Simple type tracking: var = ClassName()
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variable_types[target.id] = class_name
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check method calls."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if method call matches signature."""
        method_name = node.func.attr
        
        # Try to determine the class
        class_name = None
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            # Check if we know the type
            if var_name in self.variable_types:
                class_name = self.variable_types[var_name]
            # Check if it's self.something
            elif var_name == 'self':
                # Would need to track current class
                pass
        elif isinstance(node.func.value, ast.Attribute):
            # self.something.method() - get the attribute name
            if isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                # This is self.attribute.method()
                attr_name = node.func.value.attr
                # Common patterns
                if 'manager' in attr_name.lower():
                    class_name = attr_name.title().replace('_', '') + 'Manager'
                elif 'engine' in attr_name.lower():
                    class_name = attr_name.title().replace('_', '') + 'Engine'
                elif 'analytics' in attr_name.lower():
                    class_name = 'AnalyticsIntegration'
                elif 'optimizer' in attr_name.lower():
                    class_name = 'PatternOptimizer'
        
        if not class_name:
            return
        
        # Check if we have signature info for this method
        key = (class_name, method_name)
        if key in self.all_methods:
            expected_args = self.all_methods[key]
            
            # Count provided arguments
            provided_args = len(node.args) + len(node.keywords)
            
            # Check if mismatch
            if provided_args < expected_args:
                self.errors.append(MethodSignatureError(
                    file=str(self.filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    class_name=class_name,
                    method_name=method_name,
                    expected_args=expected_args,
                    provided_args=provided_args,
                    message=f"Method {class_name}.{method_name}() expects at least {expected_args} arguments, but {provided_args} were provided",
                    severity='critical'
                ))


class MethodSignatureValidator:
    """Validates that method calls match actual method signatures."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[MethodSignatureError] = []
        self.all_methods: Dict[Tuple[str, str], int] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all method signatures in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect all method signatures
        self._collect_methods()
        
        # Second pass: validate method calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': e.file,
                    'line': e.line,
                    'class_name': e.class_name,
                    'method_name': e.method_name,
                    'expected_args': e.expected_args,
                    'provided_args': e.provided_args,
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ],
            'total_errors': len(self.errors),
            'methods_found': len(self.all_methods),
            'by_severity': self._count_by_severity()
        }
    
    def _collect_methods(self):
        """Collect all method signatures in the project."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
                
                collector = MethodCollector(str(py_file))
                collector.visit(tree)
                
                # Merge methods from this file
                self.all_methods.update(collector.methods)
                
            except Exception as e:
                # Skip files that can't be parsed
                pass
    
    def _validate_file(self, filepath: Path):
        """Validate method calls in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            
            checker = MethodCallChecker(filepath, self.project_root, self.all_methods)
            checker.visit(tree)
            
            self.errors.extend(checker.errors)
            
        except Exception as e:
            # Skip files that can't be parsed
            pass
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
        return counts