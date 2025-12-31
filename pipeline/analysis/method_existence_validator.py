"""
Method Existence Validator

Validates that methods exist on classes, checking parent and base classes.
Properly handles inheritance, stdlib classes, and function patterns.
"""

import ast
from typing import Dict, List, Set, Optional
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
    """Validates method existence with inheritance and stdlib awareness."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[MethodExistenceError] = []
        
        # Track class definitions and their methods
        self.class_methods: Dict[str, Set[str]] = {}
        self.class_parents: Dict[str, List[str]] = {}
        
        # Known base classes and their methods
        self.known_base_classes = {
            'ast.NodeVisitor': {'visit', 'generic_visit'},
            'NodeVisitor': {'visit', 'generic_visit'},
            'CustomTool': {'run', 'execute', 'validate'},
            'BasePhase': {'execute', 'chat_with_history', 'write_own_status'},
        }
        
        # Known standard library classes (skip validation for these)
        self.stdlib_classes = {
            'Path', 'PosixPath', 'WindowsPath',  # pathlib
            'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'bool',  # builtins
            'defaultdict', 'OrderedDict', 'Counter', 'deque',  # collections
            'datetime', 'date', 'time', 'timedelta',  # datetime
            'Thread', 'Lock', 'Event', 'Queue',  # threading
            'Logger',  # logging
            'HTTPResponse', 'HTTPConnection',  # http
            'socket',  # socket
        }
        
        # Known function patterns that return objects (not classes)
        self.function_patterns = {
            'get_logger', 'get_specialist_registry', 'get_strategy',
            'getattr', 'hasattr', 'isinstance', 'type', 'len', 'range',
            'open', 'print', 'input', 'enumerate', 'zip', 'map', 'filter',
        }
        
    def validate_all(self) -> Dict:
        """
        Validate all method existence in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect all class definitions and their methods
        self._collect_class_definitions()
        
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
    
    def _collect_class_definitions(self):
        """Collect all class definitions and their methods."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # Use proper visitor pattern instead of ast.walk
                for node in tree.body:
                    self._collect_from_node(node)
                        
            except Exception:
                continue
    
    def _collect_from_node(self, node):
        """Recursively collect class definitions from AST nodes."""
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            
            # Collect methods
            methods = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
                elif isinstance(item, ast.ClassDef):
                    # Nested class - recurse
                    self._collect_from_node(item)
            
            self.class_methods[class_name] = methods
            
            # Collect parent classes
            parents = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    parents.append(base.id)
                elif isinstance(base, ast.Attribute):
                    # Handle ast.NodeVisitor, etc.
                    if isinstance(base.value, ast.Name):
                        parents.append(f"{base.value.id}.{base.attr}")
            
            self.class_parents[class_name] = parents
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check for nested classes in functions
            for item in node.body:
                if isinstance(item, ast.ClassDef):
                    self._collect_from_node(item)
    
    def _validate_file(self, filepath: Path):
        """Validate method calls in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Use visitor to track types and validate
            visitor = MethodCallVisitor(filepath, self.project_root, self)
            visitor.visit(tree)
            
            self.errors.extend(visitor.errors)
                        
        except Exception:
            pass
    
    def _method_exists(self, class_name: str, method_name: str) -> bool:
        """Check if method exists on class or any of its parents."""
        # Check direct class
        if class_name in self.class_methods:
            if method_name in self.class_methods[class_name]:
                return True
        
        # Check parent classes
        if class_name in self.class_parents:
            for parent in self.class_parents[class_name]:
                # Check known base classes
                if parent in self.known_base_classes:
                    if method_name in self.known_base_classes[parent]:
                        return True
                
                # Recursively check parent
                if self._method_exists(parent, method_name):
                    return True
        
        return False
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts


class MethodCallVisitor(ast.NodeVisitor):
    """Visitor to track variable types and validate method calls."""
    
    def __init__(self, filepath: Path, project_root: Path, validator: MethodExistenceValidator):
        self.filepath = filepath
        self.project_root = project_root
        self.validator = validator
        self.var_types: Dict[str, str] = {}
        self.errors: List[MethodExistenceError] = []
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments to class instances."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                # Only track if it looks like a class (starts with uppercase)
                # AND exists in our class registry
                if func_name and func_name[0].isupper() and func_name in self.validator.class_methods:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.var_types[target.id] = func_name
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check method calls."""
        if isinstance(node.func, ast.Attribute):
            self._check_method_call(node)
        
        self.generic_visit(node)
    
    def _check_method_call(self, node: ast.Call):
        """Check if a method exists on a class (including parent classes)."""
        if not isinstance(node.func.value, ast.Name):
            return
        
        var_name = node.func.value.id
        method_name = node.func.attr
        
        # Skip common safe patterns (dict/list/string methods)
        safe_methods = {
            'get', 'items', 'keys', 'values', 'append', 'extend', 'pop',
            'split', 'join', 'strip', 'replace', 'format', 'splitlines',
            'lower', 'upper', 'startswith', 'endswith', 'find', 'index',
            'read', 'write', 'close', 'open', 'exists', 'mkdir', 'rmdir',
            'read_text', 'write_text', 'unlink', 'rename', 'copy',
        }
        
        if method_name in safe_methods:
            return
        
        # Get class name
        if var_name not in self.var_types:
            # Unknown type - skip validation
            return
        
        class_name = self.var_types[var_name]
        
        # Skip standard library classes
        if class_name in self.validator.stdlib_classes:
            return
        
        # Skip function patterns (not actual classes)
        if class_name in self.validator.function_patterns:
            return
        
        # Check if method exists
        if self.validator._method_exists(class_name, method_name):
            return
        
        # Method doesn't exist - report error
        self.errors.append(MethodExistenceError(
            file=str(self.filepath.relative_to(self.project_root)),
            line=node.lineno,
            class_name=class_name,
            method_name=method_name,
            message=f"Method '{method_name}' does not exist on class '{class_name}'",
            severity='critical'
        ))