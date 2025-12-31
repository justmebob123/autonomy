"""
Code Validation Analysis Module

Provides comprehensive code validation capabilities including:
- Attribute access validation
- Import-class name matching
- Abstract method checking
- Tool-handler verification
- Dictionary access validation
"""

import ast
import inspect
import importlib
import importlib.util
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from ..logging_setup import get_logger


class AttributeAccessValidator(ast.NodeVisitor):
    """
    Validates object attribute access patterns.
    
    Catches errors like:
    - task.target vs task.target_file
    - Accessing non-existent attributes
    - Typos in attribute names
    """
    
    def __init__(self, filepath: str, logger):
        self.filepath = filepath
        self.logger = logger
        self.issues = []
        self.known_classes = {}  # class_name -> {attributes}
        self.variable_types = {}  # var_name -> class_name
        
    def validate(self) -> List[Dict]:
        """Run validation and return issues."""
        try:
            with open(self.filepath, 'r') as f:
                content = f.read()
                tree = ast.parse(content, filename=self.filepath)
            
            # First pass: collect class definitions
            self._collect_class_definitions(tree)
            
            # Second pass: track variable assignments
            self._track_variable_types(tree)
            
            # Third pass: validate attribute access
            self.visit(tree)
            
            return self.issues
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'file': self.filepath,
                'line': e.lineno,
                'message': f"Syntax error: {e.msg}"
            }]
        except Exception as e:
            self.logger.error(f"Error validating {self.filepath}: {e}")
            return []
    
    def _collect_class_definitions(self, tree):
        """Collect all class definitions and their attributes."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                attrs = set()
                
                # Collect methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        attrs.add(item.name)
                    elif isinstance(item, ast.Assign):
                        # Class variables
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attrs.add(target.id)
                    elif isinstance(item, ast.AnnAssign):
                        # Annotated assignments
                        if isinstance(item.target, ast.Name):
                            attrs.add(item.target.id)
                
                # Look for self.attr assignments in __init__
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        for subnode in ast.walk(item):
                            if isinstance(subnode, ast.Assign):
                                for target in subnode.targets:
                                    if isinstance(target, ast.Attribute):
                                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                            attrs.add(target.attr)
                
                self.known_classes[node.name] = attrs
    
    def _track_variable_types(self, tree):
        """Track variable type assignments."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Look for patterns like: task = TaskState(...)
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        class_name = node.value.func.id
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.variable_types[target.id] = class_name
    
    def visit_Attribute(self, node):
        """Check attribute access."""
        # Get the object being accessed
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            attr_name = node.attr
            
            # Check if we know the type
            if var_name in self.variable_types:
                class_name = self.variable_types[var_name]
                if class_name in self.known_classes:
                    if attr_name not in self.known_classes[class_name]:
                        # Find similar attributes
                        similar = [a for a in self.known_classes[class_name] 
                                 if a.lower().startswith(attr_name.lower()[:3])]
                        
                        self.issues.append({
                            'type': 'unknown_attribute',
                            'file': self.filepath,
                            'object': var_name,
                            'class': class_name,
                            'attribute': attr_name,
                            'line': node.lineno,
                            'col': node.col_offset,
                            'similar': similar,
                            'message': f"Attribute '{attr_name}' not found in class '{class_name}'. Similar: {similar}"
                        })
        
        self.generic_visit(node)


class ImportClassMatcher:
    """
    Verifies import names match actual class names.
    
    Catches errors like:
    - ConflictDetector vs IntegrationConflictDetector
    - Importing non-existent classes
    """
    
    def __init__(self, filepath: str, logger):
        self.filepath = filepath
        self.logger = logger
        self.issues = []
        self.project_root = self._find_project_root(filepath)
    
    def _find_project_root(self, filepath: str) -> Path:
        """Find project root by looking for pipeline directory."""
        path = Path(filepath).resolve()
        while path.parent != path:
            if (path / 'pipeline').exists():
                return path
            path = path.parent
        return Path(filepath).parent
    
    def validate(self) -> List[Dict]:
        """Check all imports match actual class names."""
        try:
            with open(self.filepath, 'r') as f:
                content = f.read()
                tree = ast.parse(content, filename=self.filepath)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self._check_import_from(node)
            
            return self.issues
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'file': self.filepath,
                'line': e.lineno,
                'message': f"Syntax error: {e.msg}"
            }]
        except Exception as e:
            self.logger.error(f"Error checking imports in {self.filepath}: {e}")
            return []
    
    def _check_import_from(self, node):
        """Check a from...import statement."""
        if not node.module:
            return
        
        module = node.module
        
        for alias in node.names:
            if alias.name == '*':
                continue
            
            imported_name = alias.name
            
            try:
                # Try to resolve the module
                if module.startswith('.'):
                    # Relative import - try to resolve
                    module_path = self._resolve_relative_import(module)
                    if not module_path:
                        continue
                    
                    # Check if file exists
                    if not module_path.exists():
                        self.issues.append({
                            'type': 'module_not_found',
                            'file': self.filepath,
                            'module': module,
                            'imported_name': imported_name,
                            'line': node.lineno,
                            'message': f"Module '{module}' not found"
                        })
                        continue
                    
                    # Parse the module file
                    with open(module_path, 'r') as f:
                        module_content = f.read()
                        module_tree = ast.parse(module_content)
                    
                    # Get all class names
                    actual_classes = [n.name for n in ast.walk(module_tree) 
                                    if isinstance(n, ast.ClassDef)]
                    
                    # Check if imported name exists
                    if imported_name not in actual_classes:
                        # Find similar names
                        similar = [c for c in actual_classes 
                                 if imported_name.lower() in c.lower() 
                                 or c.lower() in imported_name.lower()]
                        
                        self.issues.append({
                            'type': 'import_class_mismatch',
                            'file': self.filepath,
                            'module': module,
                            'imported_name': imported_name,
                            'line': node.lineno,
                            'actual_classes': actual_classes,
                            'similar_names': similar,
                            'message': f"'{imported_name}' not found in '{module}'. Available: {actual_classes}. Similar: {similar}"
                        })
                
            except Exception as e:
                self.logger.debug(f"Could not check import {imported_name} from {module}: {e}")
    
    def _resolve_relative_import(self, module: str) -> Optional[Path]:
        """Resolve relative import to file path."""
        # Count leading dots
        level = len(module) - len(module.lstrip('.'))
        module_name = module.lstrip('.')
        
        # Start from current file's directory
        current_dir = Path(self.filepath).parent
        
        # Go up 'level' directories
        for _ in range(level - 1):
            current_dir = current_dir.parent
        
        # Append module path
        if module_name:
            module_path = current_dir / module_name.replace('.', '/') + '.py'
        else:
            module_path = current_dir / '__init__.py'
        
        return module_path


class AbstractMethodChecker:
    """
    Checks abstract methods are implemented.
    
    Catches errors like:
    - Missing generate_state_markdown method
    - Unimplemented abstract methods from base classes
    """
    
    def __init__(self, filepath: str, class_name: str, logger):
        self.filepath = filepath
        self.class_name = class_name
        self.logger = logger
        self.issues = []
    
    def validate(self) -> List[Dict]:
        """Check all abstract methods are implemented."""
        try:
            # Load the module with proper parent package
            import sys
            from pathlib import Path
            
            # Add parent directory to sys.path temporarily
            parent_dir = str(Path(self.filepath).parent.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Load the module
            spec = importlib.util.spec_from_file_location("temp_module", self.filepath)
            if not spec or not spec.loader:
                return [{
                    'type': 'module_load_error',
                    'file': self.filepath,
                    'message': f"Cannot load module from {self.filepath}"
                }]
            
            module = importlib.util.module_from_spec(spec)
            
            # Set __package__ to allow relative imports
            module.__package__ = "pipeline.phases"
            
            spec.loader.exec_module(module)
            
            # Get the class
            if not hasattr(module, self.class_name):
                return [{
                    'type': 'class_not_found',
                    'file': self.filepath,
                    'class_name': self.class_name,
                    'message': f"Class '{self.class_name}' not found in {self.filepath}"
                }]
            
            cls = getattr(module, self.class_name)
            
            # Get all abstract methods from base classes
            abstract_methods = {}
            for base in inspect.getmro(cls)[1:]:  # Skip the class itself
                for name, method in inspect.getmembers(base):
                    if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                        abstract_methods[name] = base.__name__
            
            # Check if implemented
            for method_name, base_class in abstract_methods.items():
                if not hasattr(cls, method_name):
                    self.issues.append({
                        'type': 'missing_abstract_method',
                        'file': self.filepath,
                        'class_name': self.class_name,
                        'method_name': method_name,
                        'base_class': base_class,
                        'message': f"Abstract method '{method_name}' from '{base_class}' not implemented in '{self.class_name}'"
                    })
                else:
                    # Check if it's actually implemented (not just inherited as abstract)
                    method = getattr(cls, method_name)
                    if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                        self.issues.append({
                            'type': 'abstract_method_not_overridden',
                            'file': self.filepath,
                            'class_name': self.class_name,
                            'method_name': method_name,
                            'base_class': base_class,
                            'message': f"Abstract method '{method_name}' inherited but not overridden in '{self.class_name}'"
                        })
            
            return self.issues
            
        except Exception as e:
            self.logger.error(f"Error checking abstract methods in {self.filepath}: {e}")
            return [{
                'type': 'validation_error',
                'file': self.filepath,
                'message': f"Error: {e}"
            }]


class ToolHandlerVerifier:
    """
    Verifies tool-handler-registration chain.
    
    Catches errors like:
    - Missing tool handlers
    - Unregistered tools
    - Wrong handler registered for tool
    """
    
    def __init__(self, project_dir: str, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.issues = []
    
    def validate(self) -> List[Dict]:
        """Verify all tools have handlers and are registered."""
        try:
            # 1. Get all tool definitions
            tools = self._get_all_tools()
            
            # 2. Get all handler methods
            handlers = self._get_all_handlers()
            
            # 3. Get handler registrations
            registrations = self._get_handler_registrations()
            
            # 4. Check each tool
            for tool_name, tool_file in tools:
                # Check handler exists
                expected_handler = f"_handle_{tool_name}"
                if expected_handler not in handlers:
                    self.issues.append({
                        'type': 'missing_handler',
                        'tool_name': tool_name,
                        'expected_handler': expected_handler,
                        'tool_file': tool_file,
                        'message': f"Handler '{expected_handler}' not found for tool '{tool_name}'"
                    })
                
                # Check registration
                if tool_name not in registrations:
                    self.issues.append({
                        'type': 'missing_registration',
                        'tool_name': tool_name,
                        'expected_handler': expected_handler,
                        'message': f"Tool '{tool_name}' not registered in handlers dict"
                    })
                elif registrations[tool_name] != expected_handler:
                    self.issues.append({
                        'type': 'wrong_handler_registered',
                        'tool_name': tool_name,
                        'expected_handler': expected_handler,
                        'actual_handler': registrations[tool_name],
                        'message': f"Tool '{tool_name}' registered with wrong handler: {registrations[tool_name]} (expected {expected_handler})"
                    })
            
            return self.issues
            
        except Exception as e:
            self.logger.error(f"Error verifying tool handlers: {e}")
            return [{
                'type': 'validation_error',
                'message': f"Error: {e}"
            }]
    
    def _get_all_tools(self) -> List[Tuple[str, str]]:
        """Get all tool names from tool modules."""
        tools = []
        tool_files = [
            "pipeline/tool_modules/file_updates.py",
            "pipeline/tool_modules/refactoring_tools.py",
            "pipeline/tool_modules/tool_definitions.py"
        ]
        
        for filepath in tool_files:
            full_path = self.project_dir / filepath
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                tool_names = re.findall(r'"name":\s*"(\w+)"', content)
                tools.extend([(name, filepath) for name in tool_names])
        
        return tools
    
    def _get_all_handlers(self) -> Set[str]:
        """Get all handler method names."""
        handlers_file = self.project_dir / "pipeline/handlers.py"
        if not handlers_file.exists():
            return set()
        
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        handler_names = re.findall(r'def (_handle_\w+)\(self', content)
        return set(handler_names)
    
    def _get_handler_registrations(self) -> Dict[str, str]:
        """Get handler registrations from handlers dict."""
        handlers_file = self.project_dir / "pipeline/handlers.py"
        if not handlers_file.exists():
            return {}
        
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        registrations = re.findall(r'"(\w+)":\s*self\.(_handle_\w+)', content)
        return dict(registrations)


class DictAccessValidator(ast.NodeVisitor):
    """
    Validates dictionary access patterns.
    
    Catches errors like:
    - Accessing dict[key] without checking if key in dict
    - Potential KeyError risks
    """
    
    def __init__(self, filepath: str, logger):
        self.filepath = filepath
        self.logger = logger
        self.issues = []
        self.safe_accesses = set()  # (dict_name, key) tuples that are safe
    
    def validate(self) -> List[Dict]:
        """Run validation and return issues."""
        try:
            with open(self.filepath, 'r') as f:
                content = f.read()
                tree = ast.parse(content, filename=self.filepath)
            
            # First pass: find safe accesses (with 'in' checks)
            self._find_safe_accesses(tree)
            
            # Second pass: check all dict accesses
            self.visit(tree)
            
            return self.issues
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'file': self.filepath,
                'line': e.lineno,
                'message': f"Syntax error: {e.msg}"
            }]
        except Exception as e:
            self.logger.error(f"Error validating dict access in {self.filepath}: {e}")
            return []
    
    def _find_safe_accesses(self, tree):
        """Find dictionary accesses that are protected by 'in' checks."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Look for: key in dict
                if isinstance(node.ops[0], ast.In):
                    if isinstance(node.left, ast.Constant):  # key
                        key = node.left.value
                        if isinstance(node.comparators[0], ast.Attribute):
                            # dict.attr
                            dict_name = ast.unparse(node.comparators[0])
                            self.safe_accesses.add((dict_name, key))
    
    def visit_Subscript(self, node):
        """Check dictionary subscript access."""
        # Check if this is a dictionary access
        if isinstance(node.value, ast.Attribute):
            dict_name = ast.unparse(node.value)
            
            # Get the key
            if isinstance(node.slice, ast.Constant):
                key = node.slice.value
                
                # Check if this access is safe
                if (dict_name, key) not in self.safe_accesses:
                    self.issues.append({
                        'type': 'unsafe_dict_access',
                        'file': self.filepath,
                        'dict': dict_name,
                        'key': key,
                        'line': node.lineno,
                        'col': node.col_offset,
                        'message': f"Unsafe dictionary access: {dict_name}['{key}'] without checking if key exists"
                    })
        
        self.generic_visit(node)