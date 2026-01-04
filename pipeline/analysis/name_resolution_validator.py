#!/usr/bin/env python3
"""
Name Resolution Validator

Detects NameError by verifying all used names are either:
1. Imported
2. Defined locally
3. Builtins
"""

import ast
import builtins
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class NameUsage:
    """Information about a name usage."""
    name: str
    line: int
    col: int
    context: str  # 'load' or 'store'


class NameResolutionValidator(ast.NodeVisitor):
    """
    Validates that all used names are defined.
    
    Detects NameError patterns by tracking:
    - All name usages (reads)
    - All imports
    - All local definitions (functions, classes, variables)
    - Builtin names
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        
        # Track all names
        self.imported_names = set()      # Names imported
        self.defined_names = set()       # Names defined locally
        self.used_names = {}             # name -> [line_nums]
        self.builtin_names = set(dir(builtins))
        
        # Track scope
        self.current_scope = 'module'
        self.scope_stack = []
    
    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from...import statement."""
        for alias in node.names:
            if alias.name == '*':
                # Can't track star imports precisely
                continue
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        self.defined_names.add(node.name)
        
        # Enter function scope
        old_scope = self.current_scope
        self.scope_stack.append(self.current_scope)
        self.current_scope = f'function:{node.name}'
        
        self.generic_visit(node)
        
        # Exit function scope
        self.current_scope = old_scope
        if self.scope_stack:
            self.scope_stack.pop()
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node):
        """Visit class definition."""
        self.defined_names.add(node.name)
        
        # Enter class scope
        old_scope = self.current_scope
        self.scope_stack.append(self.current_scope)
        self.current_scope = f'class:{node.name}'
        
        self.generic_visit(node)
        
        # Exit class scope
        self.current_scope = old_scope
        if self.scope_stack:
            self.scope_stack.pop()
    
    def visit_Assign(self, node):
        """Visit assignment (tracks module-level variables)."""
        if self.current_scope == 'module':
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.defined_names.add(target.id)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name usage."""
        if isinstance(node.ctx, ast.Load):
            # This is a read (usage)
            name = node.id
            if name not in self.used_names:
                self.used_names[name] = []
            self.used_names[name].append(node.lineno)
        elif isinstance(node.ctx, ast.Store) and self.current_scope == 'module':
            # Module-level assignment
            self.defined_names.add(node.id)
        
        self.generic_visit(node)
    
    def check_names(self):
        """Check that all used names are defined."""
        for name, line_nums in self.used_names.items():
            # Check if name is defined
            if name in self.imported_names:
                continue
            if name in self.defined_names:
                continue
            if name in self.builtin_names:
                continue
            
            # Special cases
            if name in {'self', 'cls'}:
                continue
            
            # Name is not defined!
            for line_num in line_nums:
                self.errors.append({
                    'file': self.filepath,
                    'line': line_num,
                    'severity': 'critical',
                    'type': 'name_not_defined',
                    'name': name,
                    'message': f"Name '{name}' is not defined (not imported and not defined locally)"
                })
    
    def validate(self, tree: ast.AST) -> List[Dict]:
        """Run validation and return errors."""
        self.visit(tree)
        self.check_names()
        return self.errors


def validate_file(filepath: str) -> List[Dict]:
    """Validate a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        validator = NameResolutionValidator(filepath)
        return validator.validate(tree)
    
    except SyntaxError as e:
        return [{
            'file': filepath,
            'line': e.lineno,
            'severity': 'critical',
            'type': 'syntax_error',
            'message': str(e)
        }]
    except Exception as e:
        return [{
            'file': filepath,
            'line': 0,
            'severity': 'error',
            'type': 'validation_error',
            'message': f"Failed to validate: {e}"
        }]


def validate_directory(directory: str) -> List[Dict]:
    """Validate all Python files in a directory."""
    all_errors = []
    
    for filepath in Path(directory).rglob('*.py'):
        if '__pycache__' in str(filepath):
            continue
        
        errors = validate_file(str(filepath))
        all_errors.extend(errors)
    
    return all_errors


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("ERROR: Project directory required")
        print()
        print("Usage: name_resolution_validator.py <project_directory>")
        print()
        print("This validator detects NameError by checking all used names are defined.")
        print()
        sys.exit(1)
    
    directory = sys.argv[1]
    errors = validate_directory(directory)
    
    if errors:
        print(f"❌ Found {len(errors)} name resolution errors:\n")
        
        # Group by file
        by_file = {}
        for error in errors:
            file = error['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(error)
        
        for file, file_errors in sorted(by_file.items()):
            print(f"\n📁 {file}")
            for error in file_errors:
                print(f"  Line {error['line']}: {error['message']}")
        
        print(f"\n❌ Total: {len(errors)} errors")
        sys.exit(1)
    else:
        print("✅ No name resolution errors found")
        sys.exit(0)


if __name__ == '__main__':
    main()