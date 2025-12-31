"""
Function Call Validator

Validates that function and method calls use correct parameters and signatures.
"""

import ast
import inspect
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class FunctionCallError:
    """Represents a function call validation error."""
    file: str
    line: int
    function: str
    error_type: str  # 'missing_required', 'unexpected_kwarg', 'wrong_param_name'
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'


class FunctionCallValidator:
    """Validates function and method calls against their signatures."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[FunctionCallError] = []
        self.function_signatures: Dict[str, inspect.Signature] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all function calls in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect function signatures
        self._collect_signatures()
        
        # Second pass: validate calls
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        return {
            'errors': [
                {
                    'file': err.file,
                    'line': err.line,
                    'function': err.function,
                    'error_type': err.error_type,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'by_severity': self._count_by_severity(),
            'by_type': self._count_by_type()
        }
    
    def _collect_signatures(self):
        """Collect function signatures from all Python files."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Store function signature info
                        func_name = node.name
                        required_args = []
                        optional_args = []
                        
                        # Get positional arguments
                        for i, arg in enumerate(node.args.args):
                            # Check if has default value
                            default_offset = len(node.args.args) - len(node.args.defaults)
                            if i >= default_offset:
                                optional_args.append(arg.arg)
                            else:
                                required_args.append(arg.arg)
                        
                        # Store signature info
                        self.function_signatures[func_name] = {
                            'required': required_args,
                            'optional': optional_args,
                            'file': str(py_file.relative_to(self.project_root))
                        }
                        
            except Exception:
                continue
    
    def _validate_file(self, filepath: Path):
        """Validate all function calls in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._validate_call(node, filepath)
                    
        except Exception:
            pass
    
    def _validate_call(self, node: ast.Call, filepath: Path):
        """Validate a single function call."""
        # Get function name
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if not func_name or func_name not in self.function_signatures:
            return
        
        sig_info = self.function_signatures[func_name]
        required_params = sig_info['required']
        optional_params = sig_info['optional']
        all_params = required_params + optional_params
        
        # Get provided arguments
        provided_positional = len(node.args)
        provided_keywords = {kw.arg for kw in node.keywords if kw.arg}
        
        # Check 1: Missing required positional arguments
        if provided_positional < len(required_params):
            # Check if missing args are provided as keywords
            missing = []
            for i in range(provided_positional, len(required_params)):
                param = required_params[i]
                if param not in provided_keywords:
                    missing.append(param)
            
            if missing:
                self.errors.append(FunctionCallError(
                    file=str(filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    function=func_name,
                    error_type='missing_required',
                    message=f"Missing required arguments: {', '.join(missing)}",
                    severity='critical'
                ))
        
        # Check 2: Unexpected keyword arguments
        for kw in node.keywords:
            if kw.arg and kw.arg not in all_params:
                self.errors.append(FunctionCallError(
                    file=str(filepath.relative_to(self.project_root)),
                    line=node.lineno,
                    function=func_name,
                    error_type='unexpected_kwarg',
                    message=f"Unexpected keyword argument: '{kw.arg}'",
                    severity='critical'
                ))
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for err in self.errors:
            counts[err.severity] += 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count errors by type."""
        counts = {}
        for err in self.errors:
            counts[err.error_type] = counts.get(err.error_type, 0) + 1
        return counts