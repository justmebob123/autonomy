"""
Function Signature Extractor

Extracts function signatures from Python files to verify parameter compatibility.
"""

import ast
import inspect
from typing import Dict, List, Optional, Any
from pathlib import Path


class SignatureExtractor:
    """Extracts function signatures from Python source code."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def extract_function_signature(
        self,
        filepath: str,
        function_name: str,
        class_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract function signature from a Python file.
        
        Args:
            filepath: Path to Python file (relative to project root)
            function_name: Name of function to extract
            class_name: Optional class name if function is a method
            
        Returns:
            Dictionary with signature information or None if not found
        """
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the function
            target_node = None
            
            if class_name:
                # Look for method in class
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name == function_name:
                                target_node = item
                                break
                        break
            else:
                # Look for top-level function
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        target_node = node
                        break
            
            if not target_node:
                return None
            
            # Extract signature information
            signature = {
                'name': function_name,
                'class': class_name,
                'parameters': [],
                'has_args': False,
                'has_kwargs': False,
                'docstring': ast.get_docstring(target_node),
                'line_number': target_node.lineno
            }
            
            # Process arguments
            args = target_node.args
            
            # Regular arguments
            for i, arg in enumerate(args.args):
                param_info = {
                    'name': arg.arg,
                    'type': self._get_annotation(arg.annotation),
                    'default': None,
                    'kind': 'positional_or_keyword'
                }
                
                # Check if it has a default value
                defaults_offset = len(args.args) - len(args.defaults)
                if i >= defaults_offset:
                    default_idx = i - defaults_offset
                    param_info['default'] = self._get_default_value(args.defaults[default_idx])
                
                signature['parameters'].append(param_info)
            
            # *args
            if args.vararg:
                signature['has_args'] = True
                signature['parameters'].append({
                    'name': args.vararg.arg,
                    'type': self._get_annotation(args.vararg.annotation),
                    'default': None,
                    'kind': 'var_positional'
                })
            
            # Keyword-only arguments
            for i, arg in enumerate(args.kwonlyargs):
                param_info = {
                    'name': arg.arg,
                    'type': self._get_annotation(arg.annotation),
                    'default': self._get_default_value(args.kw_defaults[i]) if args.kw_defaults[i] else None,
                    'kind': 'keyword_only'
                }
                signature['parameters'].append(param_info)
            
            # **kwargs
            if args.kwarg:
                signature['has_kwargs'] = True
                signature['parameters'].append({
                    'name': args.kwarg.arg,
                    'type': self._get_annotation(args.kwarg.annotation),
                    'default': None,
                    'kind': 'var_keyword'
                })
            
            return signature
            
        except Exception as e:
            return {
                'error': str(e),
                'name': function_name,
                'class': class_name
            }
    
    def _get_annotation(self, annotation) -> Optional[str]:
        """Extract type annotation as string."""
        if annotation is None:
            return None
        
        try:
            return ast.unparse(annotation)
        except:
            return str(annotation)
    
    def _get_default_value(self, default) -> str:
        """Extract default value as string."""
        if default is None:
            return None
        
        try:
            return ast.unparse(default)
        except:
            return str(default)
    
    def validate_function_call(
        self,
        filepath: str,
        function_name: str,
        call_kwargs: Dict[str, Any],
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate that a function call uses valid parameters.
        
        Args:
            filepath: Path to file containing function
            function_name: Name of function
            call_kwargs: Dictionary of keyword arguments being passed
            class_name: Optional class name if function is a method
            
        Returns:
            Dictionary with validation results
        """
        signature = self.extract_function_signature(filepath, function_name, class_name)
        
        if not signature:
            return {
                'valid': False,
                'error': f"Could not find function {function_name} in {filepath}"
            }
        
        if 'error' in signature:
            return {
                'valid': False,
                'error': signature['error']
            }
        
        # Get valid parameter names
        valid_params = {p['name'] for p in signature['parameters']}
        
        # Check if function accepts **kwargs
        has_kwargs = signature['has_kwargs']
        
        # Find invalid parameters
        invalid_params = []
        for param in call_kwargs.keys():
            if param not in valid_params and not has_kwargs:
                invalid_params.append(param)
        
        if invalid_params:
            return {
                'valid': False,
                'invalid_parameters': invalid_params,
                'valid_parameters': list(valid_params),
                'has_kwargs': has_kwargs,
                'signature': signature
            }
        
        return {
            'valid': True,
            'signature': signature
        }
    
    def format_signature(self, signature: Dict[str, Any]) -> str:
        """Format signature as readable string."""
        if 'error' in signature:
            return f"Error: {signature['error']}"
        
        params = []
        for param in signature['parameters']:
            param_str = param['name']
            
            if param['type']:
                param_str += f": {param['type']}"
            
            if param['default']:
                param_str += f" = {param['default']}"
            
            if param['kind'] == 'var_positional':
                param_str = f"*{param_str}"
            elif param['kind'] == 'var_keyword':
                param_str = f"**{param_str}"
            
            params.append(param_str)
        
        func_name = signature['name']
        if signature['class']:
            func_name = f"{signature['class']}.{func_name}"
        
        return f"{func_name}({', '.join(params)})"