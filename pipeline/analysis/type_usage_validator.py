"""
Type Usage Validator

Validates that objects are used according to their types.
Detects using dict methods on dataclasses, accessing attributes on dicts, etc.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TypeUsageError:
    """Represents a type usage validation error."""
    file: str
    line: int
    variable: str
    actual_type: str
    attempted_operation: str
    message: str
    severity: str


class TypeUsageValidator:
    """Validates that objects are used according to their types."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[TypeUsageError] = []
        self.dataclasses: Set[str] = set()
        self.regular_classes: Set[str] = set()
        
    def validate_all(self) -> Dict:
        """
        Validate all type usage in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: identify dataclasses and regular classes
        self._collect_class_types()
        
        # Second pass: validate type usage
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': err.file,
                    'line': err.line,
                    'variable': err.variable,
                    'actual_type': err.actual_type,
                    'attempted_operation': err.attempted_operation,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'dataclasses_found': len(self.dataclasses),
            'classes_found': len(self.regular_classes),
            'by_severity': self._count_by_severity()
        }
    
    def _collect_class_types(self):
        """Collect dataclasses and regular classes."""
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
                        
                        # Check if it's a dataclass
                        is_dataclass = False
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                                is_dataclass = True
                                break
                        
                        if is_dataclass:
                            self.dataclasses.add(class_name)
                        else:
                            self.regular_classes.add(class_name)
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path):
        """Validate all type usage in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Track variable types
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
        """Validate a method call against the object's type."""
        if not isinstance(node.func, ast.Attribute):
            return
        
        method_name = node.func.attr
        
        # Get the variable being called
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            
            # Check if we know the type
            if var_name in var_types:
                var_type = var_types[var_name]
                
                # Check for dict methods on dataclasses
                dict_methods = {'get', 'items', 'keys', 'values', 'pop', 'update', 'setdefault'}
                
                if var_type in self.dataclasses and method_name in dict_methods:
                    self.errors.append(TypeUsageError(
                        file=str(filepath.relative_to(self.project_root)),
                        line=node.lineno,
                        variable=var_name,
                        actual_type=f"dataclass {var_type}",
                        attempted_operation=f".{method_name}()",
                        message=f"Cannot use dict method '.{method_name}()' on dataclass {var_type}. Use attribute access or asdict() instead.",
                        severity='critical'
                    ))
                
                # Check for attribute access on dicts (less common but possible)
                # This would require more sophisticated type tracking
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts