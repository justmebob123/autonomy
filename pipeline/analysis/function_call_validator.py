"""
Function Call Validator

Validates function calls have correct arguments.
Understands Python calling conventions, optional parameters, and *args/**kwargs.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass


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
    """Validates function calls with Python-aware analysis."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[FunctionCallError] = []
        
        # Track function signatures
        self.function_signatures: Dict[str, Dict] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all function calls in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect function signatures
        self._collect_function_signatures()
        
        # Second pass: validate function calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            # Skip test files (they have different patterns)
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
    
    def _collect_function_signatures(self):
        """Collect all function signatures."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        
                        # Get parameters
                        args = node.args
                        
                        # Count required parameters (excluding self, *args, **kwargs)
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
                        
                        self.function_signatures[func_name] = {
                            'required': required_params,
                            'optional': optional_params,
                            'has_varargs': has_varargs,
                            'has_kwargs': has_kwargs
                        }
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path):
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
    
    def _check_function_call(self, node: ast.Call, filepath: Path):
        """Check if function call has correct arguments."""
        # Get function name
        func_name = None
        is_method_call = False
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            is_method_call = True
        else:
            return
        
        # Skip common stdlib functions that have flexible signatures
        stdlib_functions = {
            'parse', 'get', 'post', 'put', 'delete', 'patch',  # HTTP/parsing
            'register', 'generate', 'consult_specialist',  # Common patterns
            'format', 'join', 'split', 'replace', 'strip',  # String methods
            'append', 'extend', 'insert', 'remove', 'pop',  # List methods
            'update', 'setdefault', 'fromkeys',  # Dict methods
            'read', 'write', 'readline', 'readlines',  # File methods
            'open', 'close', 'flush',  # IO methods
        }
        
        if func_name in stdlib_functions:
            return
        
        # Skip if we don't have signature info
        if func_name not in self.function_signatures:
            return
        
        sig = self.function_signatures[func_name]
        
        # For method calls, Python automatically passes 'self'
        # So we don't need to check for it
        
        # Count provided arguments
        num_positional = len(node.args)
        num_keyword = len(node.keywords)
        
        # If function has *args or **kwargs, it can accept any arguments
        if sig['has_varargs'] or sig['has_kwargs']:
            return
        
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