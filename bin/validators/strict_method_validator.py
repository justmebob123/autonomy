#!/usr/bin/env python3
"""
Strict Method Validator
Validates that all self.method() calls have corresponding method definitions.
This validator would have caught the publish_event error.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from difflib import get_close_matches


class StrictMethodValidator:
    """Validates self-method calls strictly"""
    
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.errors = []
        self.warnings = []
    
    def validate(self, project_root: Path) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate all self-method calls in the project.
        Returns (errors, warnings)
        """
        print("🔍 Running strict method validation...")
        
        for file_path in project_root.rglob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                self._validate_file(tree, file_path)
                
            except SyntaxError:
                # Skip files with syntax errors (handled by other validators)
                continue
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
        
        print(f"✅ Strict validation complete: {len(self.errors)} errors, {len(self.warnings)} warnings")
        return self.errors, self.warnings
    
    def _validate_file(self, tree: ast.AST, file_path: Path):
        """Validate all classes in a file"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._validate_class(node, file_path)
    
    def _validate_class(self, class_node: ast.ClassDef, file_path: Path):
        """Validate all self-method calls in a class"""
        class_name = class_node.name
        
        # Get all methods defined in this class
        defined_methods = set()
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                defined_methods.add(item.name)
        
        # Get all methods from parent classes
        parent_methods = self._get_parent_methods(class_name)
        all_available_methods = defined_methods | parent_methods
        
        # Find all self.method() calls
        for node in ast.walk(class_node):
            if isinstance(node, ast.Call):
                self._validate_method_call(
                    node, class_name, all_available_methods, 
                    defined_methods, parent_methods, file_path
                )
    
    def _validate_method_call(self, node: ast.Call, class_name: str,
                             all_methods: Set[str], defined_methods: Set[str],
                             parent_methods: Set[str], file_path: Path):
        """Validate a single method call"""
        # Check if it's a self.method() call
        if not isinstance(node.func, ast.Attribute):
            return
        
        if not isinstance(node.func.value, ast.Name):
            return
        
        if node.func.value.id != 'self':
            return
        
        method_name = node.func.attr
        
        # Check if method exists
        if method_name not in all_methods:
            # Method doesn't exist - this is an error
            similar = self._find_similar_methods(method_name, all_methods)
            
            error = {
                'file': str(file_path),
                'line': node.lineno,
                'class': class_name,
                'method_called': method_name,
                'severity': 'CRITICAL',
                'message': f"Method '{method_name}' not found in {class_name} or parent classes"
            }
            
            if similar:
                error['suggestion'] = f"Did you mean: {', '.join(similar)}?"
                error['similar_methods'] = similar
            
            self.errors.append(error)
        
        # Check if method is private but called from outside
        elif method_name.startswith('_') and method_name not in defined_methods:
            # Calling private method from parent class - warning
            self.warnings.append({
                'file': str(file_path),
                'line': node.lineno,
                'class': class_name,
                'method_called': method_name,
                'severity': 'WARNING',
                'message': f"Calling private method '{method_name}' from parent class"
            })
    
    def _get_parent_methods(self, class_name: str) -> Set[str]:
        """Get all methods from parent classes"""
        methods = set()
        
        # Get class info from symbol table
        class_info = self.symbol_table.classes.get(class_name)
        if not class_info:
            return methods
        
        # Get parent classes
        for parent in class_info.get('bases', []):
            parent_info = self.symbol_table.classes.get(parent)
            if parent_info:
                # Add parent's methods
                methods.update(parent_info.get('methods', []))
                # Recursively get grandparent methods
                methods.update(self._get_parent_methods(parent))
        
        return methods
    
    def _find_similar_methods(self, method_name: str, 
                             available_methods: Set[str]) -> List[str]:
        """Find methods with similar names using fuzzy matching"""
        similar = get_close_matches(
            method_name, 
            available_methods, 
            n=3, 
            cutoff=0.6
        )
        return similar
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "=" * 80)
        print("STRICT METHOD VALIDATION REPORT")
        print("=" * 80)
        
        if not self.errors and not self.warnings:
            print("✅ No issues found!")
            return
        
        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}):")
            print("-" * 80)
            for error in self.errors:
                print(f"\n❌ {error['file']}:{error['line']}")
                print(f"   Class: {error['class']}")
                print(f"   {error['message']}")
                if 'suggestion' in error:
                    print(f"   💡 {error['suggestion']}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            print("-" * 80)
            for warning in self.warnings:
                print(f"\n⚠️  {warning['file']}:{warning['line']}")
                print(f"   Class: {warning['class']}")
                print(f"   {warning['message']}")
        
        print("\n" + "=" * 80)


def main():
    """Run strict method validation"""
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from pipeline.analysis.symbol_table import SymbolTable
    from pipeline.analysis.symbol_collector import SymbolCollector
    
    # Get project root
    project_root = Path.cwd()
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    
    print(f"📁 Project: {project_root}")
    print()
    
    # Build symbol table
    print("🔍 Building symbol table...")
    symbol_table = SymbolTable(project_root)
    collector = SymbolCollector(symbol_table)
    collector.collect_from_project(project_root)
    print(f"✅ Symbol table built: {len(symbol_table.classes)} classes")
    print()
    
    # Run validation
    validator = StrictMethodValidator(symbol_table)
    errors, warnings = validator.validate(project_root)
    
    # Print report
    validator.print_report()
    
    # Exit with error code if errors found
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()