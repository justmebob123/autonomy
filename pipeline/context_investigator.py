"""
Context-Aware Investigation System

This module provides deep investigation capabilities that understand
the PURPOSE and INTENT of code, not just syntax.
"""

import ast
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class ContextInvestigator:
    """
    Investigates code context to understand intent and data flow.
    
    Goes beyond syntax to understand:
    - Where data comes from
    - What data is expected
    - How data flows through the system
    - Configuration requirements
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def investigate_parameter_removal(
        self,
        filepath: str,
        function_name: str,
        parameter_name: str,
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Investigate what happens if we remove a parameter.
        
        This is CRITICAL before removing parameters from function calls.
        
        Returns:
            - where_defined: Where the parameter is defined
            - data_source: Where the data comes from
            - data_structure: What the data looks like
            - usage_locations: Where the parameter is used
            - impact_analysis: What breaks if we remove it
            - recommended_action: What to do instead
        """
        result = {
            'parameter_name': parameter_name,
            'where_defined': None,
            'data_source': None,
            'data_structure': None,
            'usage_locations': [],
            'impact_analysis': [],
            'recommended_action': None
        }
        
        full_path = self.project_root / filepath
        if not full_path.exists():
            result['error'] = f"File not found: {filepath}"
            return result
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the function call
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this call uses the parameter
                    for keyword in node.keywords:
                        if keyword.arg == parameter_name:
                            # Found usage - trace where the value comes from
                            value_info = self._trace_value_source(keyword.value, source)
                            result['where_defined'] = value_info
                            
                            # Analyze the value
                            if isinstance(keyword.value, ast.Name):
                                var_name = keyword.value.id
                                result['data_source'] = f"Variable: {var_name}"
                                
                                # Find where this variable is defined
                                definition = self._find_variable_definition(tree, var_name)
                                if definition:
                                    result['data_structure'] = definition
            
            # Find where the parameter is used in the target function
            usage = self._find_parameter_usage(tree, function_name, parameter_name, class_name)
            result['usage_locations'] = usage
            
            # Analyze impact
            if usage:
                result['impact_analysis'].append(
                    f"Parameter '{parameter_name}' is used in {len(usage)} location(s)"
                )
                result['impact_analysis'].append(
                    "Removing this parameter will break functionality"
                )
                result['recommended_action'] = (
                    f"DO NOT remove '{parameter_name}'. Instead:\n"
                    f"1. Investigate where the data should come from\n"
                    f"2. Check if it should come from config\n"
                    f"3. Verify the target function signature\n"
                    f"4. Fix the data source, not remove the parameter"
                )
            else:
                result['impact_analysis'].append(
                    f"Parameter '{parameter_name}' is NOT used in the function"
                )
                result['recommended_action'] = (
                    f"Safe to remove '{parameter_name}' - it's not used"
                )
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def investigate_data_flow(
        self,
        filepath: str,
        variable_name: str,
        line_number: int
    ) -> Dict[str, Any]:
        """
        Trace where data comes from and where it goes.
        
        Critical for understanding KeyError and missing data issues.
        """
        result = {
            'variable_name': variable_name,
            'line_number': line_number,
            'defined_at': None,
            'source': None,
            'transformations': [],
            'used_at': [],
            'expected_structure': None
        }
        
        full_path = self.project_root / filepath
        if not full_path.exists():
            result['error'] = f"File not found: {filepath}"
            return result
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                source = ''.join(lines)
            
            tree = ast.parse(source)
            
            # Find where the variable is defined
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.name == variable_name:
                            result['defined_at'] = node.lineno
                            
                            # Analyze the source
                            if isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Attribute):
                                    result['source'] = f"Method call: {ast.unparse(node.value.func)}"
                                elif isinstance(node.value.func, ast.Name):
                                    result['source'] = f"Function call: {node.value.func.id}"
                            elif isinstance(node.value, ast.List):
                                result['source'] = f"List literal: {ast.unparse(node.value)}"
                            elif isinstance(node.value, ast.Dict):
                                result['source'] = f"Dict literal: {ast.unparse(node.value)}"
            
            # Find where it's used
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.name == variable_name:
                    if hasattr(node, 'lineno'):
                        result['used_at'].append(node.lineno)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def check_configuration_structure(
        self,
        config_file: str,
        expected_keys: List[str]
    ) -> Dict[str, Any]:
        """
        Check if configuration file has expected structure.
        
        Critical for KeyError issues related to configuration.
        """
        result = {
            'config_file': config_file,
            'exists': False,
            'structure': None,
            'has_expected_keys': {},
            'missing_keys': [],
            'recommendations': []
        }
        
        config_path = self.project_root / config_file
        result['exists'] = config_path.exists()
        
        if not result['exists']:
            result['recommendations'].append(
                f"Configuration file '{config_file}' does not exist"
            )
            result['recommendations'].append(
                "Check if the path is correct or if config needs to be created"
            )
            return result
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            result['structure'] = str(config_data)[:500]  # First 500 chars
            
            # Check for expected keys
            for key in expected_keys:
                if isinstance(config_data, dict):
                    result['has_expected_keys'][key] = key in config_data
                    if key not in config_data:
                        result['missing_keys'].append(key)
            
            if result['missing_keys']:
                result['recommendations'].append(
                    f"Missing keys in config: {', '.join(result['missing_keys'])}"
                )
                result['recommendations'].append(
                    "Add these keys to the configuration file"
                )
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['recommendations'].append(
                f"Error reading config: {str(e)}"
            )
            return result
    
    def _trace_value_source(self, node: ast.AST, source: str) -> str:
        """Trace where a value comes from."""
        try:
            return ast.unparse(node)
        except:
            return "unknown"
    
    def _find_variable_definition(self, tree: ast.AST, var_name: str) -> Optional[str]:
        """Find where a variable is defined."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.name == var_name:
                        try:
                            return ast.unparse(node.value)
                        except:
                            return "complex expression"
        return None
    
    def _find_parameter_usage(
        self,
        tree: ast.AST,
        function_name: str,
        parameter_name: str,
        class_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find where a parameter is used in a function."""
        usage = []
        
        # Find the function
        target_func = None
        if class_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == function_name:
                            target_func = item
                            break
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    target_func = node
                    break
        
        if not target_func:
            return usage
        
        # Find usage of the parameter
        for node in ast.walk(target_func):
            if isinstance(node, ast.Name) and node.name == parameter_name:
                if hasattr(node, 'lineno'):
                    usage.append({
                        'line': node.lineno,
                        'context': 'usage'
                    })
        
        return usage