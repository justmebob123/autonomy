"""
Enhanced Type Usage Validator V2

Eliminates false positives by implementing proper type inference.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass

from .enhanced_type_tracker import EnhancedTypeTracker, TypeInfo


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


class TypeUsageValidatorV2:
    """Enhanced validator with proper type inference."""
    
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
        
        # Second pass: validate type usage with enhanced tracking
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
        """Validate all type usage in a file with enhanced tracking."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Use enhanced type tracker
            tracker = EnhancedTypeTracker(source, self.dataclasses, str(filepath))
            tracker.visit(tree)
            
            # Now validate method calls with proper type information
            validator = TypeUsageChecker(
                filepath,
                self.project_root,
                tracker,
                self.dataclasses
            )
            validator.visit(tree)
            
            self.errors.extend(validator.errors)
                        
        except Exception:
            pass
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts


class TypeUsageChecker(ast.NodeVisitor):
    """Checks type usage with enhanced type information."""
    
    def __init__(self, filepath: Path, project_root: Path, tracker: EnhancedTypeTracker, dataclasses: Set[str]):
        self.filepath = filepath
        self.project_root = project_root
        self.tracker = tracker
        self.dataclasses = dataclasses
        self.errors: List[TypeUsageError] = []
    
    def visit_Call(self, node: ast.Call):
        """Check method calls for type mismatches."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if method call is valid for the object's type."""
        if not isinstance(node.func.value, ast.Name):
            return
        
        var_name = node.func.value.id
        method_name = node.func.attr
        
        # Get type information from tracker
        var_type = self.tracker.get_type(var_name)
        
        if not var_type:
            # Unknown type - skip validation
            return
        
        # Dict methods that shouldn't be used on dataclasses
        dict_methods = {'get', 'items', 'keys', 'values', 'pop', 'update', 'setdefault'}
        
        # Only report error if we're CERTAIN it's a dataclass (not a dict)
        if var_type.is_dataclass and not var_type.is_dict and method_name in dict_methods:
            self.errors.append(TypeUsageError(
                file=str(self.filepath.relative_to(self.project_root)),
                line=node.lineno,
                variable=var_name,
                actual_type=f"dataclass {var_type.type_name}",
                attempted_operation=f".{method_name}()",
                message=f"Cannot use dict method '.{method_name}()' on dataclass {var_type.type_name}. Use attribute access or asdict() instead.",
                severity='critical'
            ))