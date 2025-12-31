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
        
        # Track class definitions and their methods with file paths
        # Key format: "filepath:classname" to handle duplicate class names
        self.class_methods: Dict[str, Set[str]] = {}
        self.class_parents: Dict[str, List[str]] = {}
        
        # Track which files define which classes (for duplicate detection)
        self.class_locations: Dict[str, List[str]] = {}  # classname -> [filepaths]
        
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
        
        # Detect duplicate class names
        duplicates = self._detect_duplicate_classes()
        
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
            'duplicate_classes': duplicates,
            'by_severity': self._count_by_severity()
        }
    
    def _detect_duplicate_classes(self) -> Dict[str, List[str]]:
        """Detect classes defined in multiple files."""
        duplicates = {}
        for class_name, locations in self.class_locations.items():
            if len(locations) > 1:
                duplicates[class_name] = locations
        return duplicates
    
    def _collect_class_definitions(self):
        """Collect all class definitions and their methods."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # Get relative path for tracking
                rel_path = str(py_file.relative_to(self.project_root))
                
                # Use proper visitor pattern instead of ast.walk
                for node in tree.body:
                    self._collect_from_node(node, rel_path)
                        
            except Exception:
                continue
    
    def _collect_from_node(self, node, filepath: str):
        """Recursively collect class definitions from AST nodes."""
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            
            # Create unique key with filepath
            class_key = f"{filepath}:{class_name}"
            
            # Collect methods
            methods = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
                elif isinstance(item, ast.ClassDef):
                    # Nested class - recurse
                    self._collect_from_node(item, filepath)
            
            # Store with filepath key
            self.class_methods[class_key] = methods
            
            # Also store simple name for backward compatibility
            # But track all locations for duplicate detection
            if class_name not in self.class_locations:
                self.class_locations[class_name] = []
            self.class_locations[class_name].append(filepath)
            
            # For simple lookups, use the most recent definition
            # (This maintains backward compatibility while tracking duplicates)
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
            self.class_parents[class_key] = parents
            
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check for nested classes in functions
            for item in node.body:
                if isinstance(item, ast.ClassDef):
                    self._collect_from_node(item, filepath)
    
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
        self.var_types: Dict[str, str] = {}  # var_name -> class_name
        self.var_type_sources: Dict[str, str] = {}  # var_name -> source_file
        self.imports: Dict[str, str] = {}  # class_name -> imported_from
        self.errors: List[MethodExistenceError] = []
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to resolve class sources."""
        if node.module:
            for alias in node.names:
                class_name = alias.asname if alias.asname else alias.name
                
                # Handle relative imports
                module_path = node.module
                if node.level > 0:
                    # Relative import (e.g., from .analysis.complexity)
                    # Get current file's directory
                    current_dir = str(self.filepath.parent.relative_to(self.project_root))
                    
                    # Go up 'level' directories
                    parts = current_dir.split('/')
                    for _ in range(node.level - 1):
                        if parts:
                            parts.pop()
                    
                    # Add module path
                    if parts:
                        module_path = '/'.join(parts) + '/' + module_path.replace('.', '/')
                    else:
                        module_path = module_path.replace('.', '/')
                else:
                    # Absolute import (e.g., from autonomy.pipeline.tool_validator)
                    # Remove 'autonomy.' prefix if present
                    if module_path.startswith('autonomy.'):
                        module_path = module_path[9:]  # Remove 'autonomy.'
                    module_path = module_path.replace('.', '/')
                
                self.imports[class_name] = module_path
        
        self.generic_visit(node)
    
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
                            # Track source file if we know where it was imported from
                            if func_name in self.imports:
                                self.var_type_sources[target.id] = self.imports[func_name]
        
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
        
        # Check if method exists, preferring the imported source
        source_file = self.var_type_sources.get(var_name)
        if source_file:
            # Try to find the class from the specific source file
            class_key = f"{source_file}.py:{class_name}"
            if class_key in self.validator.class_methods:
                if method_name in self.validator.class_methods[class_key]:
                    return  # Method exists in the correct source
        
        # Fall back to general check
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