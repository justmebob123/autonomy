"""
Enhanced Function Call Validator

Improvements over original:
1. Tracks functions with qualified names (module.Class.function)
2. Comprehensive stdlib detection
3. Context-aware validation (distinguishes module.func from obj.method)
4. Decorator awareness
5. Import resolution

Now uses shared SymbolTable for improved accuracy.
"""

import ast
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import sys

from .validation_config import ValidationConfig
from .symbol_table import SymbolTable


@dataclass
class FunctionCallError:
    """Represents a function call validation error."""
    file: str
    line: int
    function_name: str
    error_type: str
    message: str
    severity: str


class FunctionCallValidator:
    """Enhanced validator with better context awareness."""
    
    # Comprehensive stdlib modules
    STDLIB_MODULES = {
        'sys', 'os', 'io', 'time', 'datetime', 'math', 'random', 'json',
        'pickle', 'csv', 're', 'collections', 'itertools', 'functools',
        'pathlib', 'shutil', 'glob', 'tempfile', 'subprocess', 'threading',
        'multiprocessing', 'queue', 'socket', 'urllib', 'http', 'email',
        'logging', 'argparse', 'configparser', 'unittest', 'doctest',
        'pdb', 'profile', 'timeit', 'trace', 'gc', 'inspect', 'types',
        'copy', 'pprint', 'enum', 'dataclasses', 'typing', 'abc',
        'contextlib', 'atexit', 'signal', 'warnings', 'weakref',
        'array', 'struct', 'codecs', 'unicodedata', 'string', 'textwrap',
        'difflib', 'hashlib', 'hmac', 'secrets', 'base64', 'binascii',
        'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
    }
    
    # Common decorators that modify signatures
    SIGNATURE_MODIFYING_DECORATORS = {
        'property', 'staticmethod', 'classmethod', 'cached_property',
        'lru_cache', 'wraps', 'contextmanager', 'abstractmethod',
    }
    
    def __init__(self, project_root: str, config_file: Optional[str] = None, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[FunctionCallError] = []
        self.symbol_table = symbol_table
        
        # Load configuration
        config_path = Path(config_file) if config_file else None
        self.config = ValidationConfig(self.project_root, config_path)
        
        # Track functions with qualified names
        self.function_signatures: Dict[str, Dict] = {}
        
        # Track imports per file
        self.file_imports: Dict[str, Dict[str, str]] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all function calls in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect ourselves
        if self.symbol_table:
            # Extract function signatures from SymbolTable
            for func_info in self.symbol_table.functions.values():
                sig_data = {
                    'required': func_info.required_params,
                    'optional': func_info.optional_params,
                    'has_varargs': func_info.has_varargs,
                    'has_kwargs': func_info.has_kwargs,
                    'qualified_name': func_info.qualified_name
                }
                self.function_signatures[func_info.qualified_name] = sig_data
            
            # Extract imports from SymbolTable
            for file, imports in self.symbol_table.file_imports.items():
                import_dict = {}
                for imp in imports:
                    import_dict[imp.local_name] = f"{imp.module}.{imp.name}"
                self.file_imports[file] = import_dict
        else:
            # Fallback: collect function signatures and imports ourselves
            self._collect_function_signatures()
            self._collect_imports()
        
        # Validate function calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            # Skip test files
            if 'test' in py_file.name or 'test' in str(py_file.parent):
                continue
            
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': err.file,
                    'line': err.line,
                    'function_name': err.function_name,
                    'error_type': err.error_type,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'functions_analyzed': len(self.function_signatures),
            'by_type': self._count_by_type()
        }
    
    def _collect_imports(self) -> None:
        """Collect import statements from all files."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                imports = {}
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            imports[name] = alias.name
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                name = alias.asname if alias.asname else alias.name
                                imports[name] = f"{node.module}.{alias.name}"
                
                file_key = str(py_file.relative_to(self.project_root))
                self.file_imports[file_key] = imports
                
            except Exception:
                continue
    
    def _collect_function_signatures(self) -> None:
        """Collect all function signatures with qualified names."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # Track current class context
                class_stack = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_stack.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        # Build qualified name
                        if class_stack:
                            qualified_name = f"{class_stack[-1]}.{node.name}"
                        else:
                            qualified_name = node.name
                        
                        # Check for signature-modifying decorators
                        has_decorator = any(
                            (isinstance(d, ast.Name) and d.id in self.SIGNATURE_MODIFYING_DECORATORS)
                            for d in node.decorator_list
                        )
                        
                        if has_decorator:
                            # Skip validation for decorated functions
                            continue
                        
                        # Get parameters
                        args = node.args
                        
                        required_params = []
                        optional_params = []
                        has_varargs = args.vararg is not None
                        has_kwargs = args.kwarg is not None
                        
                        # Regular args
                        num_defaults = len(args.defaults)
                        num_args = len(args.args)
                        num_required = num_args - num_defaults
                        
                        for i, arg in enumerate(args.args):
                            # Skip 'self' and 'cls'
                            if arg.arg in ('self', 'cls'):
                                continue
                            
                            if i < num_required:
                                required_params.append(arg.arg)
                            else:
                                optional_params.append(arg.arg)
                        
                        # Store signature data
                        sig_data = {
                            'required': required_params,
                            'optional': optional_params,
                            'has_varargs': has_varargs,
                            'has_kwargs': has_kwargs,
                            'qualified_name': qualified_name
                        }
                        
                        # Only store qualified name to avoid confusion
                        self.function_signatures[qualified_name] = sig_data
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path) -> None:
        """Validate function calls in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._check_function_call(node, filepath)
                        
        except Exception:
            pass
    
    def _is_stdlib_call(self, node: ast.Call, filepath: Path) -> bool:
        """Check if this is a stdlib function call."""
        # Check for module.function pattern
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                
                # Check if it's a stdlib module
                if module_name in self.STDLIB_MODULES:
                    return True
                
                # Check if it's imported from stdlib
                file_key = str(filepath.relative_to(self.project_root))
                if file_key in self.file_imports:
                    imports = self.file_imports[file_key]
                    if module_name in imports:
                        imported_module = imports[module_name].split('.')[0]
                        if imported_module in self.STDLIB_MODULES:
                            return True
        
        return False
    
    def _check_function_call(self, node: ast.Call, filepath: Path) -> None:
        """Check if function call has correct arguments."""
        # Get function name
        func_name = None
        qualified_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # Try to build qualified name
            if isinstance(node.func.value, ast.Name):
                qualified_name = f"{node.func.value.id}.{func_name}"
        else:
            return
        
        # Skip stdlib calls
        if self._is_stdlib_call(node, filepath):
            return
        
        # Skip if call uses *args or **kwargs
        has_starargs = any(isinstance(arg, ast.Starred) for arg in node.args)
        has_kwargs = any(kw.arg is None for kw in node.keywords)
        if has_starargs or has_kwargs:
            return
        
        # Skip common stdlib functions
        stdlib_functions = self.config.get_stdlib_functions()
        if func_name in stdlib_functions:
            return
        
        # Try to find signature
        sig = None
        
        # For method calls (obj.method), only validate if we can determine the exact class
        if isinstance(node.func, ast.Attribute):
            if qualified_name and qualified_name in self.function_signatures:
                sig = self.function_signatures[qualified_name]
            else:
                # Can't determine exact method - skip to avoid false positives
                return
        
        # For simple function calls, we can be more confident
        elif isinstance(node.func, ast.Name):
            # Look for any function with this name
            matching_sigs = [
                s for name, s in self.function_signatures.items() 
                if name == func_name or name.endswith(f".{func_name}")
            ]
            
            if len(matching_sigs) == 1:
                # Only one function with this name - safe to validate
                sig = matching_sigs[0]
            elif len(matching_sigs) > 1:
                # Multiple functions with same name - skip to avoid confusion
                return
            else:
                # Unknown function - might be from external package
                return
        else:
            return
        
        # If function has *args or **kwargs, it can accept any arguments
        if sig['has_varargs'] or sig['has_kwargs']:
            return
        
        # Count provided arguments
        num_positional = len(node.args)
        num_keyword = len(node.keywords)
        
        # Check if all required parameters are provided
        required = sig['required']
        optional = sig['optional']
        
        # Positional args cover required params
        if num_positional < len(required):
            # Check if missing params are provided as keywords
            provided_keywords = {kw.arg for kw in node.keywords}
            missing = set(required[num_positional:]) - provided_keywords
            
            if missing:
                self.errors.append(FunctionCallError(
                    file=str(filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    function_name=func_name,
                    error_type='missing_required',
                    message=f"Missing required arguments: {', '.join(missing)}",
                    severity='critical'
                ))
        
        # Check for unexpected keyword arguments
        if num_keyword > 0:
            valid_params = set(required + optional)
            provided_keywords = {kw.arg for kw in node.keywords}
            unexpected = provided_keywords - valid_params
            
            if unexpected:
                self.errors.append(FunctionCallError(
                    file=str(filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    function_name=func_name,
                    error_type='unexpected_kwarg',
                    message=f"Unexpected keyword argument: {', '.join(unexpected)}",
                    severity='high'
                ))
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count errors by type."""
        counts = {}
        for err in self.errors:
            counts[err.error_type] = counts.get(err.error_type, 0) + 1
        return counts