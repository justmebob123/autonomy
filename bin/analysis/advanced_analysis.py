#!/usr/bin/env python3
"""
Improved Depth-61 Analyzer
Handles inheritance patterns, template methods, and indirect calls
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ImprovedDepth61Analyzer(ast.NodeVisitor):
    """
    Enhanced analyzer that understands:
    1. Template method pattern
    2. Inheritance chains
    3. Indirect method calls
    4. Polymorphic calls
    """
    
    def __init__(self, filepath: str, project_root: Path):
        self.filepath = filepath
        self.project_root = project_root
        self.content = Path(filepath).read_text()
        self.tree = ast.parse(self.content)
        
        # Track everything
        self.functions = {}
        self.classes = {}
        self.inheritance = {}  # class -> parent classes
        self.method_calls = defaultdict(list)
        self.direct_calls = defaultdict(list)
        self.indirect_calls = defaultdict(list)  # Through self.method()
        
        # Template method tracking
        self.template_methods = {}  # method -> calls which methods
        self.overridden_methods = defaultdict(list)  # method -> classes that override it
        
    def analyze(self):
        """Run analysis"""
        self.visit(self.tree)
        self._analyze_template_patterns()
        self._analyze_inheritance_calls()
        return self
    
    def visit_ClassDef(self, node):
        """Track classes and inheritance"""
        class_name = node.name
        
        # Track inheritance
        bases = [ast.unparse(base) for base in node.bases]
        self.inheritance[class_name] = bases
        
        self.classes[class_name] = {
            'line': node.lineno,
            'bases': bases,
            'methods': []
        }
        
        # Track methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.classes[class_name]['methods'].append(item.name)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Track functions and what they call"""
        func_name = node.name
        
        self.functions[func_name] = {
            'line': node.lineno,
            'calls': []
        }
        
        # Find what this function calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    # Direct function call
                    called = child.func.id
                    self.functions[func_name]['calls'].append(called)
                    self.direct_calls[called].append(func_name)
                    
                elif isinstance(child.func, ast.Attribute):
                    # Method call
                    method = child.func.attr
                    self.functions[func_name]['calls'].append(method)
                    
                    # Check if it's self.method()
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == 'self':
                        self.indirect_calls[method].append(func_name)
        
        self.generic_visit(node)
    
    def _analyze_template_patterns(self):
        """Identify template method patterns"""
        for func_name, data in self.functions.items():
            calls = data['calls']
            if calls:
                self.template_methods[func_name] = calls
    
    def _analyze_inheritance_calls(self):
        """Analyze which methods are called through inheritance"""
        # For each class, check if it overrides parent methods
        for class_name, data in self.classes.items():
            for method in data['methods']:
                # Check if parent classes have this method
                for base in data['bases']:
                    base_name = base.split('.')[-1]  # Handle module.Class
                    if base_name in self.classes:
                        if method in self.classes[base_name]['methods']:
                            self.overridden_methods[method].append(class_name)
    
    def is_method_used(self, method_name: str) -> Tuple[bool, str]:
        """
        Check if a method is used, considering:
        1. Direct calls
        2. Indirect calls (self.method)
        3. Template method pattern
        4. Inheritance
        """
        # Direct calls
        if method_name in self.direct_calls:
            return True, f"Called directly by: {self.direct_calls[method_name]}"
        
        # Indirect calls (self.method)
        if method_name in self.indirect_calls:
            return True, f"Called indirectly by: {self.indirect_calls[method_name]}"
        
        # Template method pattern
        for template, calls in self.template_methods.items():
            if method_name in calls:
                return True, f"Called by template method: {template}"
        
        # Overridden in subclasses
        if method_name in self.overridden_methods:
            return True, f"Overridden in: {self.overridden_methods[method_name]}"
        
        return False, "Not found in call graph"
    
    def generate_report(self) -> str:
        """Generate report"""
        report = []
        
        report.append("=" * 80)
        report.append(f"IMPROVED DEPTH-61 ANALYSIS: {self.filepath}")
        report.append("=" * 80)
        
        # Analyze each function
        report.append("\nFUNCTION USAGE ANALYSIS")
        report.append("-" * 80)
        
        unused = []
        used_indirect = []
        
        for func_name in self.functions:
            is_used, reason = self.is_method_used(func_name)
            
            if not is_used and not func_name.startswith('__'):
                unused.append((func_name, self.functions[func_name]['line']))
            elif 'template' in reason.lower() or 'indirect' in reason.lower():
                used_indirect.append((func_name, reason))
        
        if used_indirect:
            report.append(f"\n✅ Functions used indirectly (template/inheritance): {len(used_indirect)}")
            for func, reason in used_indirect[:5]:
                report.append(f"  - {func}(): {reason}")
            if len(used_indirect) > 5:
                report.append(f"  ... and {len(used_indirect) - 5} more")
        
        if unused:
            report.append(f"\n⚠️ Potentially unused functions: {len(unused)}")
            for func, line in unused[:10]:
                report.append(f"  - {func}() at line {line}")
            if len(unused) > 10:
                report.append(f"  ... and {len(unused) - 10} more")
        else:
            report.append("\n✅ All functions appear to be used")
        
        # Template method analysis
        if self.template_methods:
            report.append("\nTEMPLATE METHOD PATTERNS")
            report.append("-" * 80)
            for template, calls in list(self.template_methods.items())[:5]:
                report.append(f"\n  {template}() calls:")
                for call in calls[:5]:
                    report.append(f"    - {call}()")
        
        # Inheritance analysis
        if self.inheritance:
            report.append("\nINHERITANCE HIERARCHY")
            report.append("-" * 80)
            for class_name, bases in self.inheritance.items():
                if bases:
                    report.append(f"  {class_name} extends {', '.join(bases)}")
        
        return '\n'.join(report)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python IMPROVED_DEPTH_61_ANALYZER.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    project_root = Path('autonomy')
    
    analyzer = ImprovedDepth61Analyzer(filepath, project_root)
    analyzer.analyze()
    print(analyzer.generate_report())