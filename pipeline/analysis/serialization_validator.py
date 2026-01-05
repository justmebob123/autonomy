#!/usr/bin/env python3
"""
Serialization Validator

Detects TypeError from non-JSON-serializable objects by tracking:
1. What gets stored in dictionaries
2. What gets passed to json.dumps, to_dict, etc.
3. Whether values are JSON-serializable types
"""

import ast
from pathlib import Path
from typing import Dict, List, Set


class SerializationValidator(ast.NodeVisitor):
    """
    Validates that serialized data contains only JSON-serializable types.
    
    Detects TypeError patterns by tracking:
    - Dictionary assignments
    - Calls to json.dumps, to_dict, etc.
    - Non-serializable types (Path, datetime, custom objects)
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.warnings = []
        
        # Track potentially problematic patterns
        self.dict_assignments = []  # (line, key, value_type)
        self.serialization_calls = []  # (line, function, arg)
        
        # Non-serializable types
        self.non_serializable_types = {
            'Path', 'PosixPath', 'WindowsPath',
            'datetime', 'date', 'time', 'timedelta',
            'Decimal', 'UUID', 'Enum'
        }
    
    def visit_Call(self, node):
        """Visit function call."""
        # Check for serialization functions
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in {'dumps', 'dump'}:
                pass
                # json.dumps() or json.dump()
                self.serialization_calls.append({
                    'line': node.lineno,
                    'function': 'json.dumps',
                    'node': node
                })
            elif node.func.attr == 'to_dict':
                pass
                # obj.to_dict()
                self.serialization_calls.append({
                    'line': node.lineno,
                    'function': 'to_dict',
                    'node': node
                })
        elif isinstance(node.func, ast.Name):
            if node.func.id in {'json', 'dumps', 'dump'}:
                self.serialization_calls.append({
                    'line': node.lineno,
                    'function': node.func.id,
                    'node': node
                })
        
        # Check for Path() calls
        if isinstance(node.func, ast.Name) and node.func.id == 'Path':
            pass
            # This creates a Path object
            self._check_path_usage(node)
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        """Visit subscript (dict[key] = value)."""
        # Check if this is a dictionary assignment
        if isinstance(node.ctx, ast.Store):
            pass
            # This is dict[key] = value
            # Check what's being assigned
            parent = getattr(node, '_parent', None)
            if parent and isinstance(parent, ast.Assign):
                for value in parent.value if isinstance(parent.value, (list, tuple)) else [parent.value]:
                    self._check_value_type(node.lineno, value)
        
        self.generic_visit(node)
    
    def visit_Dict(self, node):
        """Visit dictionary literal."""
        # Check all values in the dictionary
        for key, value in zip(node.keys, node.values):
            if value:
                self._check_value_type(node.lineno, value)
        
        self.generic_visit(node)
    
    def _check_path_usage(self, node):
        """Check if Path() result is being stored in a serializable structure."""
        # Look at parent context
        parent = getattr(node, '_parent', None)
        
        # Check if Path() is in a dict or list
        if parent:
            if isinstance(parent, (ast.Dict, ast.List, ast.Tuple)):
                self.warnings.append({
                    'file': self.filepath,
                    'line': node.lineno,
                    'severity': 'warning',
                    'type': 'path_in_collection',
                    'message': f"Path object in collection at line {node.lineno} - may cause serialization error"
                })
            elif isinstance(parent, ast.Assign):
                pass
                # Check if assigned to a dict key
                for target in parent.targets:
                    if isinstance(target, ast.Subscript):
                        self.warnings.append({
                            'file': self.filepath,
                            'line': node.lineno,
                            'severity': 'warning',
                            'type': 'path_in_dict',
                            'message': f"Path object assigned to dict at line {node.lineno} - may cause serialization error. Use str(Path(...))"
                        })
    
    def _check_value_type(self, line: int, value_node):
        """Check if a value is potentially non-serializable."""
        # Check for Path() calls
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                if value_node.func.id in self.non_serializable_types:
                    self.warnings.append({
                        'file': self.filepath,
                        'line': line,
                        'severity': 'warning',
                        'type': 'non_serializable_type',
                        'value_type': value_node.func.id,
                        'message': f"Non-serializable type '{value_node.func.id}' at line {line} - convert to string"
                    })
        
        # Check for attribute access that might be Path
        elif isinstance(value_node, ast.Attribute):
            pass
            # Could be something.path or Path.something
            if 'path' in value_node.attr.lower():
                self.warnings.append({
                    'file': self.filepath,
                    'line': line,
                    'severity': 'info',
                    'type': 'potential_path',
                    'message': f"Potential Path object at line {line} - verify it's converted to string"
                })
    
    def validate(self, tree: ast.AST) -> tuple:
        """Run validation and return (errors, warnings)."""
        # Add parent references
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child._parent = node
        
        self.visit(tree)
        return self.errors, self.warnings


def validate_file(filepath: str) -> tuple:
    """Validate a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        validator = SerializationValidator(filepath)
        return validator.validate(tree)
    
    except SyntaxError as e:
        return ([{
            'file': filepath,
            'line': e.lineno,
            'severity': 'critical',
            'type': 'syntax_error',
            'message': str(e)
        }], [])
    except Exception as e:
        return ([{
            'file': filepath,
            'line': 0,
            'severity': 'error',
            'type': 'validation_error',
            'message': f"Failed to validate: {e}"
        }], [])


def validate_directory(directory: str) -> tuple:
    """Validate all Python files in a directory."""
    all_errors = []
    all_warnings = []
    
    for filepath in Path(directory).rglob('*.py'):
        if '__pycache__' in str(filepath):
            continue
        
        errors, warnings = validate_file(str(filepath))
        all_errors.extend(errors)
        all_warnings.extend(warnings)
    
    return all_errors, all_warnings


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("ERROR: Project directory required")
        print()
        print("Usage: serialization_validator.py <project_directory>")
        print()
        print("This validator detects non-JSON-serializable objects (Path, datetime, etc.).")
        print()
        sys.exit(1)
    
    directory = sys.argv[1]
    errors, warnings = validate_directory(directory)
    
    if errors:
        print(f"❌ Found {len(errors)} serialization errors:\n")
        for error in errors:
            print(f"  {error['file']}:{error['line']}")
            print(f"    {error['message']}")
            print()
    
    if warnings:
        print(f"⚠️  Found {len(warnings)} potential serialization issues:\n")
        
        # Group by file
        by_file = {}
        for warning in warnings:
            file = warning['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(warning)
        
        for file, file_warnings in sorted(by_file.items()):
            print(f"\n📁 {file}")
            for warning in file_warnings:
                print(f"  Line {warning['line']}: {warning['message']}")
    
    if not errors and not warnings:
        print("✅ No serialization issues found")
        sys.exit(0)
    elif errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()