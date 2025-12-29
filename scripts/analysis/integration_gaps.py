#!/usr/bin/env python3
"""
Integration Gap Finder

Identifies incomplete features, unused classes, and architectural gaps
by analyzing class instantiation, method calls, and integration points.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class IntegrationGapFinder(ast.NodeVisitor):
    def __init__(self):
        self.classes_defined = {}  # {class_name: (file, line)}
        self.classes_instantiated = set()  # {class_name}
        self.methods_defined = defaultdict(list)  # {class_name: [method_names]}
        self.methods_called = defaultdict(set)  # {class_name: {method_names}}
        self.imports = defaultdict(set)  # {file: {imported_classes}}
        self.current_file = None
        self.current_class = None
        
    def visit_ClassDef(self, node):
        self.classes_defined[node.name] = (self.current_file, node.lineno)
        
        old_class = self.current_class
        self.current_class = node.name
        
        # Collect all methods in this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods_defined[node.name].append(item.name)
        
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_Call(self, node):
        # Track class instantiation
        if isinstance(node.func, ast.Name):
            # Direct instantiation: ClassName()
            self.classes_instantiated.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method call: obj.method()
            if isinstance(node.func.value, ast.Name):
                # Track which methods are called on which classes
                # This is approximate - we'd need type inference for accuracy
                method_name = node.func.attr
                # Store for later analysis
                
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name.split('.')[-1]  # Get last part of module.Class
            self.imports[self.current_file].add(name)
            
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports[self.current_file].add(alias.name)
            
    def analyze_file(self, filepath: str):
        self.current_file = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                self.visit(tree)
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            
    def get_unused_classes(self) -> List[Tuple[str, str, int]]:
        """Get classes that are defined but never instantiated"""
        unused = []
        for class_name, (file, line) in self.classes_defined.items():
            if class_name not in self.classes_instantiated:
                # Skip base classes and abstract classes
                if not class_name.startswith('Base') and not class_name.startswith('Abstract'):
                    unused.append((class_name, file, line))
        return unused
        
    def get_classes_with_unused_methods(self) -> Dict[str, List[str]]:
        """Get classes where many methods are defined but not called"""
        result = {}
        for class_name, methods in self.methods_defined.items():
            if class_name in self.classes_instantiated:
                # Class is used, check if methods are called
                called = self.methods_called.get(class_name, set())
                unused_methods = [m for m in methods if m not in called and not m.startswith('_')]
                
                # If more than 50% of public methods are unused, flag it
                public_methods = [m for m in methods if not m.startswith('_')]
                if public_methods and len(unused_methods) / len(public_methods) > 0.5:
                    result[class_name] = unused_methods
                    
        return result
        
    def get_imported_but_unused_classes(self) -> Dict[str, List[str]]:
        """Get classes that are imported but never used"""
        result = defaultdict(list)
        for file, imported in self.imports.items():
            for class_name in imported:
                if class_name in self.classes_defined:
                    if class_name not in self.classes_instantiated:
                        result[file].append(class_name)
        return result

def analyze_directory(directory: str = "autonomy") -> IntegrationGapFinder:
    """Analyze all Python files in directory"""
    finder = IntegrationGapFinder()
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                finder.analyze_file(filepath)
    
    return finder

def generate_report(finder: IntegrationGapFinder):
    """Generate integration gap report"""
    report = []
    report.append("=" * 80)
    report.append("INTEGRATION GAP ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Unused classes
    unused_classes = finder.get_unused_classes()
    report.append(f"## UNUSED CLASSES ({len(unused_classes)})")
    report.append("")
    report.append("Classes that are defined but never instantiated:")
    report.append("")
    for class_name, file, line in sorted(unused_classes):
        report.append(f"- {class_name}")
        report.append(f"  Location: {file}:{line}")
        report.append(f"  Status: Defined but never instantiated")
        report.append("")
    
    # Classes with many unused methods
    classes_with_unused = finder.get_classes_with_unused_methods()
    report.append(f"## CLASSES WITH MANY UNUSED METHODS ({len(classes_with_unused)})")
    report.append("")
    report.append("Classes where >50% of public methods are unused:")
    report.append("")
    for class_name, unused_methods in sorted(classes_with_unused.items()):
        report.append(f"- {class_name}")
        report.append(f"  Unused methods: {', '.join(unused_methods)}")
        report.append(f"  Count: {len(unused_methods)} unused methods")
        report.append("")
    
    # Imported but unused
    imported_unused = finder.get_imported_but_unused_classes()
    total_imported_unused = sum(len(classes) for classes in imported_unused.values())
    report.append(f"## IMPORTED BUT UNUSED CLASSES ({total_imported_unused})")
    report.append("")
    for file, classes in sorted(imported_unused.items()):
        if classes:
            report.append(f"### {file}")
            for class_name in sorted(classes):
                report.append(f"  - {class_name}")
            report.append("")
    
    # Summary
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    report.append(f"Total unused classes: {len(unused_classes)}")
    report.append(f"Classes with >50% unused methods: {len(classes_with_unused)}")
    report.append(f"Imported but unused classes: {total_imported_unused}")
    report.append("")
    
    # Recommendations
    report.append("## RECOMMENDATIONS")
    report.append("")
    report.append("1. Review unused classes - may indicate incomplete features")
    report.append("2. Investigate classes with many unused methods - possible over-engineering")
    report.append("3. Remove imported but unused classes to reduce dependencies")
    report.append("4. Consider if unused code should be:")
    report.append("   - Integrated into the system")
    report.append("   - Removed as dead code")
    report.append("   - Documented as future features")
    report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Starting integration gap analysis...")
    finder = analyze_directory()
    report = generate_report(finder)
    
    # Save report
    with open("INTEGRATION_GAP_REPORT.txt", "w") as f:
        f.write(report)
    
    print(report)
    print("\nReport saved to INTEGRATION_GAP_REPORT.txt")