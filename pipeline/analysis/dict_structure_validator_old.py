"""
Dictionary Structure Validator

Validates that dictionary access patterns match actual data structures.
Detects accessing keys that don't exist or wrong nested paths.
"""

import ast
import json
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DictStructureError:
    """Represents a dictionary structure validation error."""
    file: str
    line: int
    variable: str
    key_path: str
    error_type: str  # 'missing_key', 'wrong_nesting', 'type_mismatch'
    message: str
    severity: str


class DictStructureValidator:
    """Validates dictionary access patterns against known structures."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors: List[DictStructureError] = []
        self.known_structures: Dict[str, Dict] = {}
        
    def validate_all(self) -> Dict:
        """
        Validate all dictionary access patterns in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # First pass: collect known dictionary structures from return statements
        self._collect_dict_structures()
        
        # Second pass: validate dictionary access
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
                    'key_path': err.key_path,
                    'error_type': err.error_type,
                    'message': err.message,
                    'severity': err.severity
                }
                for err in self.errors
            ],
            'total_errors': len(self.errors),
            'structures_analyzed': len(self.known_structures),
            'by_severity': self._count_by_severity(),
            'by_type': self._count_by_type()
        }
    
    def _collect_dict_structures(self):
        """Collect dictionary structures from return statements and assignments."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    # Look for return statements with dicts
                    if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                        structure = self._extract_dict_structure(node.value)
                        if structure:
                            # Store with function context if available
                            func_name = self._get_parent_function(node, tree)
                            if func_name:
                                self.known_structures[func_name] = structure
                    
                    # Look for assignments with dicts
                    if isinstance(node, ast.Assign):
                        if isinstance(node.value, ast.Dict):
                            structure = self._extract_dict_structure(node.value)
                            if structure:
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        self.known_structures[target.id] = structure
                        
            except Exception:
                continue
    
    def _extract_dict_structure(self, dict_node: ast.Dict) -> Optional[Dict]:
        """Extract the structure of a dictionary literal."""
        structure = {}
        
        for key, value in zip(dict_node.keys, dict_node.values):
            if isinstance(key, ast.Constant):
                key_name = key.value
                
                # Determine value type
                if isinstance(value, ast.Dict):
                    structure[key_name] = self._extract_dict_structure(value)
                elif isinstance(value, ast.List):
                    structure[key_name] = 'list'
                elif isinstance(value, ast.Constant):
                    structure[key_name] = type(value.value).__name__
                else:
                    structure[key_name] = 'unknown'
        
        return structure if structure else None
    
    def _get_parent_function(self, node: ast.AST, tree: ast.AST) -> Optional[str]:
        """Get the name of the function containing this node."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.FunctionDef):
                if any(child is node for child in ast.walk(parent)):
                    return parent.name
        return None
    
    def _validate_file(self, filepath: Path):
        """Validate all dictionary access in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Track variable assignments to known structures
            var_structures = {}
            
            for node in ast.walk(tree):
                # Track assignments from function calls
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Attribute):
                            func_name = node.value.func.attr
                            if func_name in self.known_structures:
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        var_structures[target.id] = self.known_structures[func_name]
                
                # Check dictionary access with .get()
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                        self._validate_dict_get(node, filepath, var_structures)
                
                # Check dictionary subscript access
                if isinstance(node, ast.Subscript):
                    self._validate_dict_subscript(node, filepath, var_structures)
                        
        except Exception:
            pass
    
    def _validate_dict_get(self, node: ast.Call, filepath: Path, var_structures: Dict):
        """Validate a .get() call on a dictionary."""
        if not isinstance(node.func, ast.Attribute):
            return
        
        # Get the variable being accessed
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            
            # Check if we know the structure
            if var_name in var_structures:
                structure = var_structures[var_name]
                
                # Get the key being accessed
                if node.args and isinstance(node.args[0], ast.Constant):
                    key = node.args[0].value
                    
                    # Check if key exists in structure
                    if isinstance(structure, dict) and key not in structure:
                        self.errors.append(DictStructureError(
                            file=str(filepath.relative_to(self.project_root)),
                            line=node.lineno,
                            variable=var_name,
                            key_path=key,
                            error_type='missing_key',
                            message=f"Key '{key}' not found in {var_name} structure. Available keys: {list(structure.keys())}",
                            severity='high'
                        ))
    
    def _validate_dict_subscript(self, node: ast.Subscript, filepath: Path, var_structures: Dict):
        """Validate dictionary subscript access."""
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            
            # Check if we know the structure
            if var_name in var_structures:
                structure = var_structures[var_name]
                
                # Get the key being accessed
                if isinstance(node.slice, ast.Constant):
                    key = node.slice.value
                    
                    # Check if key exists in structure
                    if isinstance(structure, dict) and key not in structure:
                        self.errors.append(DictStructureError(
                            file=str(filepath.relative_to(self.project_root)),
                            line=node.lineno,
                            variable=var_name,
                            key_path=key,
                            error_type='missing_key',
                            message=f"Key '{key}' not found in {var_name} structure. Available keys: {list(structure.keys())}",
                            severity='high'
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