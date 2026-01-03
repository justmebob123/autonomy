#!/usr/bin/env python3
"""
Keyword Argument Validator

Validates that keyword arguments in method calls exist in the method signature.
This is a CRITICAL validator that catches errors like:
    self.message_bus.publish(MessageType.X, source=..., payload=...)
where 'source' and 'payload' are not valid parameters.

Priority: P0 - CRITICAL
"""

import ast
import inspect
import sys
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from pipeline.analysis.symbol_table import SymbolTable
except ImportError:
    SymbolTable = None


@dataclass
class KeywordArgumentError:
    """Represents a keyword argument validation error."""
    file: str
    line: int
    class_name: str
    method_name: str
    invalid_kwargs: Set[str]
    valid_kwargs: Set[str]
    message: str
    severity: str


class MethodSignatureCollector(ast.NodeVisitor):
    """Collects method signatures with their parameter names."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.methods: Dict[Tuple[str, str], Set[str]] = {}  # (class, method) -> set of param names
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Collect method parameter names."""
        if self.current_class:
            # Get all parameter names (excluding 'self')
            param_names = set()
            
            # Regular parameters
            for arg in node.args.args[1:]:  # Skip 'self'
                param_names.add(arg.arg)
            
            # Keyword-only parameters
            for arg in node.args.kwonlyargs:
                param_names.add(arg.arg)
            
            # **kwargs means any keyword argument is valid
            if node.args.kwarg:
                param_names.add('**kwargs')  # Special marker
            
            self.methods[(self.current_class, node.name)] = param_names
        
        self.generic_visit(node)


class KeywordArgumentChecker(ast.NodeVisitor):
    """Checks that keyword arguments in calls are valid."""
    
    def __init__(self, filepath: Path, project_root: Path, all_methods: Dict[Tuple[str, str], Set[str]]):
        self.filepath = filepath
        self.project_root = project_root
        self.all_methods = all_methods
        self.errors: List[KeywordArgumentError] = []
        self.variable_types: Dict[str, str] = {}
        
    def visit_Assign(self, node: ast.Assign):
        """Track variable types."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variable_types[target.id] = class_name
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check method calls for invalid keyword arguments."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if keyword arguments are valid."""
        method_name = node.func.attr
        
        # Try to determine the class
        class_name = self._infer_class_name(node.func)
        
        if not class_name:
            return
        
        # Check if we have signature info
        key = (class_name, method_name)
        if key in self.all_methods:
            valid_kwargs = self.all_methods[key]
            
            # If method accepts **kwargs, all keyword arguments are valid
            if '**kwargs' in valid_kwargs:
                return
            
            # Get provided keyword arguments
            provided_kwargs = {kw.arg for kw in node.keywords if kw.arg}  # Exclude **kwargs
            
            # Find invalid kwargs
            invalid_kwargs = provided_kwargs - valid_kwargs
            
            if invalid_kwargs:
                self.errors.append(KeywordArgumentError(
                    file=str(self.filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    class_name=class_name,
                    method_name=method_name,
                    invalid_kwargs=invalid_kwargs,
                    valid_kwargs=valid_kwargs,
                    message=f"Method {class_name}.{method_name}() called with invalid keyword arguments: {', '.join(invalid_kwargs)}. Valid kwargs: {', '.join(valid_kwargs) if valid_kwargs else 'none'}",
                    severity='critical'
                ))
    
    def _infer_class_name(self, func_node) -> Optional[str]:
        """Try to infer the class name from the function node."""
        if isinstance(func_node.value, ast.Name):
            var_name = func_node.value.id
            if var_name in self.variable_types:
                return self.variable_types[var_name]
            elif var_name == 'self':
                return None  # Would need class context
        elif isinstance(func_node.value, ast.Attribute):
            # self.something.method()
            if isinstance(func_node.value.value, ast.Name) and func_node.value.value.id == 'self':
                attr_name = func_node.value.attr
                # Common patterns
                if 'bus' in attr_name.lower():
                    return 'MessageBus'
                elif 'manager' in attr_name.lower():
                    return attr_name.title().replace('_', '') + 'Manager'
                elif 'engine' in attr_name.lower():
                    return attr_name.title().replace('_', '') + 'Engine'
                elif 'analytics' in attr_name.lower():
                    return 'AnalyticsIntegration'
        
        return None


class KeywordArgumentValidator:
    """Validates that keyword arguments in method calls are valid."""
    
    def __init__(self, project_root: str, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[KeywordArgumentError] = []
        self.symbol_table = symbol_table
        self.all_methods: Dict[Tuple[str, str], Set[str]] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all keyword arguments in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect methods
        if self.symbol_table:
            self._extract_from_symbol_table()
        else:
            self._collect_methods()
        
        # Validate method calls
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
                    'invalid_kwargs': list(e.invalid_kwargs),
                    'valid_kwargs': list(e.valid_kwargs),
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ],
            'total_errors': len(self.errors),
            'methods_found': len(self.all_methods),
            'by_severity': self._count_by_severity()
        }
    
    def _extract_from_symbol_table(self):
        """Extract method signatures from SymbolTable."""
        for class_info in self.symbol_table.classes.values():
            if ':' in class_info.name:  # Skip qualified names
                continue
            for method_name, method_info in class_info.methods.items():
                key = (class_info.name, method_name)
                # For now, we'll need to parse the actual file to get param names
                # This is a limitation of the current SymbolTable
                # We'll fall back to collecting methods
                pass
        
        # Fallback to collecting methods
        self._collect_methods()
    
    def _collect_methods(self):
        """Collect all method signatures in the project."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
                
                collector = MethodSignatureCollector(str(py_file))
                collector.visit(tree)
                
                # Merge methods from this file
                self.all_methods.update(collector.methods)
                
            except Exception:
                pass
    
    def _validate_file(self, filepath: Path):
        """Validate keyword arguments in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            
            checker = KeywordArgumentChecker(filepath, self.project_root, self.all_methods)
            checker.visit(tree)
            
            self.errors.extend(checker.errors)
            
        except Exception:
            pass
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
        return counts


def main():
    """Run keyword argument validation."""
    import sys
    
    project_dir = "."
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    
    print(f"🔍 Validating keyword arguments in: {project_dir}")
    print("=" * 80)
    print()
    
    validator = KeywordArgumentValidator(project_dir)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Methods found: {result['methods_found']}")
    print(f"   Total errors: {result['total_errors']}")
    print(f"   By severity:")
    for severity, count in result['by_severity'].items():
        if count > 0:
            print(f"      {severity}: {count}")
    print()
    
    if result['total_errors'] > 0:
        print("❌ ERRORS FOUND ({})".format(result['total_errors']))
        print("=" * 80)
        print()
        
        for i, error in enumerate(result['errors'], 1):
            print(f"{i}. {error['file']}:{error['line']}")
            print(f"   Class: {error['class_name']}")
            print(f"   Method: {error['method_name']}")
            print(f"   Invalid kwargs: {', '.join(error['invalid_kwargs'])}")
            print(f"   Valid kwargs: {', '.join(error['valid_kwargs']) if error['valid_kwargs'] else 'none'}")
            print(f"   Severity: {error['severity']}")
            print(f"   Message: {error['message']}")
            print()
    else:
        print("✅ NO ERRORS FOUND")
        print()
    
    print("=" * 80)
    
    return 0 if result['total_errors'] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())