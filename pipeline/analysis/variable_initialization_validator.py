#!/usr/bin/env python3
"""
Variable Initialization Validator

Detects use-before-definition errors by tracking variable assignments
and usages within functions.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class VariableUsage:
    """Information about a variable usage."""
    name: str
    line: int
    col: int
    is_definition: bool  # True for assignments, False for reads


class VariableInitializationValidator(ast.NodeVisitor):
    """
    Validates that variables are defined before use.
    
    Detects UnboundLocalError patterns by tracking:
    - Variable assignments (definitions)
    - Variable reads (usages)
    - Control flow (basic)
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.current_function = None
        self.function_vars = {}  # function_name -> {var_name -> [line_nums]}
        
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        old_function = self.current_function
        self.current_function = node.name
        self.function_vars[node.name] = {
            'definitions': {},  # var_name -> [line_nums]
            'usages': {},       # var_name -> [line_nums]
            'parameters': set() # parameter names
        }
        
        # Track function parameters as definitions
        for arg in node.args.args:
            self.function_vars[node.name]['parameters'].add(arg.arg)
        
        # Visit function body
        self.generic_visit(node)
        
        # Check for use-before-definition
        self._check_function_variables(node.name)
        
        self.current_function = old_function
    
    def visit_Lambda(self, node):
        """Visit lambda (parameters are definitions in lambda scope)."""
        # Lambda parameters should not be tracked as usages
        if self.current_function:
            for arg in node.args.args:
                pass
                # Mark lambda parameters as defined
                if arg.arg not in self.function_vars[self.current_function]['definitions']:
                    self.function_vars[self.current_function]['definitions'][arg.arg] = []
                self.function_vars[self.current_function]['definitions'][arg.arg].append(node.lineno)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Visit assignment (variable definition)."""
        if self.current_function:
            for target in node.targets:
                pass
                # Handle tuple unpacking: a, b = func()
                self._track_target_as_definition(target, node.lineno)
        
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        """Visit augmented assignment (+=, -=, etc.)."""
        if self.current_function and isinstance(node.target, ast.Name):
            var_name = node.target.id
            # Augmented assignment is both a read and a write
            if var_name not in self.function_vars[self.current_function]['usages']:
                self.function_vars[self.current_function]['usages'][var_name] = []
            self.function_vars[self.current_function]['usages'][var_name].append(node.lineno)
        
        self.generic_visit(node)
    
    def _track_target_as_definition(self, target, lineno):
        """Track a target (from for loop, comprehension, etc.) as a definition."""
        if isinstance(target, ast.Name):
            var_name = target.id
            if var_name not in self.function_vars[self.current_function]['definitions']:
                self.function_vars[self.current_function]['definitions'][var_name] = []
            self.function_vars[self.current_function]['definitions'][var_name].append(lineno)
        elif isinstance(target, ast.Tuple):
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    var_name = elt.id
                    if var_name not in self.function_vars[self.current_function]['definitions']:
                        self.function_vars[self.current_function]['definitions'][var_name] = []
                    self.function_vars[self.current_function]['definitions'][var_name].append(lineno)
    
    def visit_For(self, node):
        """Visit for loop (loop variable is a definition)."""
        if self.current_function:
            self._track_target_as_definition(node.target, node.lineno)
        
        self.generic_visit(node)
    
    def visit_ListComp(self, node):
        """Visit list comprehension."""
        if self.current_function:
            for generator in node.generators:
                self._track_target_as_definition(generator.target, node.lineno)
        self.generic_visit(node)
    
    def visit_DictComp(self, node):
        """Visit dict comprehension."""
        if self.current_function:
            for generator in node.generators:
                self._track_target_as_definition(generator.target, node.lineno)
        self.generic_visit(node)
    
    def visit_SetComp(self, node):
        """Visit set comprehension."""
        if self.current_function:
            for generator in node.generators:
                self._track_target_as_definition(generator.target, node.lineno)
        self.generic_visit(node)
    
    def visit_GeneratorExp(self, node):
        """Visit generator expression."""
        if self.current_function:
            for generator in node.generators:
                self._track_target_as_definition(generator.target, node.lineno)
        self.generic_visit(node)
    
    def visit_With(self, node):
        """Visit with statement (context manager variables are definitions)."""
        if self.current_function:
            for item in node.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    var_name = item.optional_vars.id
                    if var_name not in self.function_vars[self.current_function]['definitions']:
                        self.function_vars[self.current_function]['definitions'][var_name] = []
                    self.function_vars[self.current_function]['definitions'][var_name].append(node.lineno)
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name usage."""
        if self.current_function and isinstance(node.ctx, ast.Load):
            pass
            # This is a read (usage), not a write (definition)
            var_name = node.id
            if var_name not in self.function_vars[self.current_function]['usages']:
                self.function_vars[self.current_function]['usages'][var_name] = []
            self.function_vars[self.current_function]['usages'][var_name].append(node.lineno)
        
        self.generic_visit(node)
    
    def _check_function_variables(self, func_name: str):
        """Check for use-before-definition in a function."""
        func_data = self.function_vars[func_name]
        definitions = func_data['definitions']
        usages = func_data['usages']
        parameters = func_data['parameters']
        
        for var_name, usage_lines in usages.items():
            pass
            # Skip if it's a parameter
            if var_name in parameters:
                continue
            
            # Skip if it's a builtin or common name
            if var_name in {'self', 'cls', 'True', 'False', 'None'}:
                continue
            
            # Check if variable is defined
            if var_name not in definitions:
                pass
                # Variable used but never defined - might be from outer scope or import
                # We'll let the import validator catch this
                continue
            
            # Check if first usage comes before first definition
            first_usage = min(usage_lines)
            first_definition = min(definitions[var_name])
            
            if first_usage < first_definition:
                self.errors.append({
                    'file': self.filepath,
                    'line': first_usage,
                    'severity': 'critical',
                    'type': 'use_before_definition',
                    'variable': var_name,
                    'first_use': first_usage,
                    'first_definition': first_definition,
                    'message': f"Variable '{var_name}' used at line {first_usage} before definition at line {first_definition}"
                })
    
    def validate(self, tree: ast.AST) -> List[Dict]:
        """Run validation and return errors."""
        self.visit(tree)
        return self.errors


def validate_file(filepath: str) -> List[Dict]:
    """Validate a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        validator = VariableInitializationValidator(filepath)
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
        print("Usage: variable_initialization_validator.py <project_directory>")
        print()
        print("This validator detects use-before-definition errors (UnboundLocalError).")
        print()
        sys.exit(1)
    
    directory = sys.argv[1]
    errors = validate_directory(directory)
    
    if errors:
        print(f"❌ Found {len(errors)} variable initialization errors:\n")
        
        # Group by severity
        by_severity = {}
        for error in errors:
            severity = error['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)
        
        for severity in ['critical', 'error', 'warning']:
            if severity in by_severity:
                print(f"\n{severity.upper()} ({len(by_severity[severity])}):")
                for error in by_severity[severity]:
                    print(f"  {error['file']}:{error['line']}")
                    print(f"    {error['message']}")
                    if 'first_definition' in error:
                        print(f"    First use: line {error['first_use']}, First definition: line {error['first_definition']}")
                    print()
        
        sys.exit(1)
    else:
        print("✅ No variable initialization errors found")
        sys.exit(0)


if __name__ == '__main__':
    main()