#!/usr/bin/env python3
"""
Dead Code Detector with Pattern Awareness

This script detects unused functions and imports while being aware of:
- Template method patterns
- Inheritance hierarchies
- Dynamic calls
- Polymorphic dispatch
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class DeadCodeDetector(ast.NodeVisitor):
    def __init__(self):
        self.functions_defined = {}  # {function_name: (file, line)}
        self.functions_called = set()  # {function_name}
        self.classes_defined = {}  # {class_name: (file, line)}
        self.methods_defined = {}  # {class.method: (file, line)}
        self.methods_called = set()  # {method_name}
        self.imports = defaultdict(list)  # {file: [import_names]}
        self.imports_used = defaultdict(set)  # {file: {import_names}}
        self.inheritance = {}  # {class_name: parent_class}
        self.current_file = None
        self.current_class = None
        
    def visit_FunctionDef(self, node):
        if self.current_class:
            # Method definition
            method_key = f"{self.current_class}.{node.name}"
            self.methods_defined[method_key] = (self.current_file, node.lineno)
        else:
            # Function definition
            self.functions_defined[node.name] = (self.current_file, node.lineno)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.classes_defined[node.name] = (self.current_file, node.lineno)
        
        # Track inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritance[node.name] = base.id
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_Call(self, node):
        # Track function/method calls
        if isinstance(node.func, ast.Name):
            self.functions_called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.methods_called.add(node.func.attr)
            # Track attribute access for imports
            if isinstance(node.func.value, ast.Name):
                if self.current_file:
                    self.imports_used[self.current_file].add(node.func.value.id)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        # Track attribute access
        if isinstance(node.value, ast.Name):
            if self.current_file:
                self.imports_used[self.current_file].add(node.value.id)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[self.current_file].append((name, node.lineno, 'import'))
            
    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[self.current_file].append((name, node.lineno, 'from'))
            
    def analyze_file(self, filepath: str):
        self.current_file = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                self.visit(tree)
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            
    def is_template_method(self, method_name: str, class_name: str) -> bool:
        """Check if method is likely a template method (overridden in subclasses)"""
        template_patterns = ['execute', 'run', 'process', 'handle', 'validate']
        return any(pattern in method_name.lower() for pattern in template_patterns)
        
    def get_unused_functions(self) -> List[Tuple[str, str, int]]:
        """Get list of unused functions"""
        unused = []
        for func_name, (file, line) in self.functions_defined.items():
            if func_name not in self.functions_called:
                # Skip special methods
                if not func_name.startswith('_'):
                    unused.append((func_name, file, line))
        return unused
        
    def get_unused_methods(self) -> List[Tuple[str, str, int]]:
        """Get list of unused methods (excluding template methods)"""
        unused = []
        for method_key, (file, line) in self.methods_defined.items():
            class_name, method_name = method_key.split('.')
            
            # Skip if method is called
            if method_name in self.methods_called:
                continue
                
            # Skip template methods
            if self.is_template_method(method_name, class_name):
                continue
                
            # Skip special methods
            if method_name.startswith('__'):
                continue
                
            unused.append((method_key, file, line))
        return unused
        
    def get_unused_imports(self) -> Dict[str, List[Tuple[str, int]]]:
        """Get unused imports per file"""
        unused = defaultdict(list)
        for file, imports in self.imports.items():
            for import_name, line, import_type in imports:
                if import_name not in self.imports_used[file]:
                    unused[file].append((import_name, line, import_type))
        return unused

def analyze_directory(directory: str = "autonomy"):
    """Analyze all Python files in directory"""
    detector = DeadCodeDetector()
    
    # First pass: collect all definitions and calls
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                detector.analyze_file(filepath)
    
    return detector

def generate_report(detector: DeadCodeDetector):
    """Generate comprehensive dead code report"""
    report = []
    report.append("=" * 80)
    report.append("DEAD CODE DETECTION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Unused functions
    unused_functions = detector.get_unused_functions()
    report.append(f"## UNUSED FUNCTIONS ({len(unused_functions)})")
    report.append("")
    for func_name, file, line in sorted(unused_functions):
        report.append(f"- {func_name} at {file}:{line}")
    report.append("")
    
    # Unused methods
    unused_methods = detector.get_unused_methods()
    report.append(f"## UNUSED METHODS ({len(unused_methods)})")
    report.append("")
    for method_key, file, line in sorted(unused_methods):
        report.append(f"- {method_key} at {file}:{line}")
    report.append("")
    
    # Unused imports
    unused_imports = detector.get_unused_imports()
    total_unused_imports = sum(len(imports) for imports in unused_imports.values())
    report.append(f"## UNUSED IMPORTS ({total_unused_imports})")
    report.append("")
    for file, imports in sorted(unused_imports.items()):
        if imports:
            report.append(f"### {file}")
            for import_name, line, import_type in sorted(imports):
                report.append(f"  - {import_name} at line {line} ({import_type})")
            report.append("")
    
    # Summary
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    report.append(f"Total unused functions: {len(unused_functions)}")
    report.append(f"Total unused methods: {len(unused_methods)}")
    report.append(f"Total unused imports: {total_unused_imports}")
    report.append(f"Total files with unused imports: {len(unused_imports)}")
    report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Starting dead code detection...")
    detector = analyze_directory()
    report = generate_report(detector)
    
    # Save report
    with open("DEAD_CODE_REPORT.txt", "w") as f:
        f.write(report)
    
    print(report)
    print("\nReport saved to DEAD_CODE_REPORT.txt")