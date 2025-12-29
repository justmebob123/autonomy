#!/usr/bin/env python3
"""
Call Graph Generator

Generates comprehensive call graphs showing function/method relationships
across the entire codebase. Supports inheritance-aware analysis.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class CallGraphGenerator(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}  # {func_name: (file, line)}
        self.methods = {}  # {class.method: (file, line)}
        self.calls = defaultdict(set)  # {caller: {callees}}
        self.inheritance = {}  # {class: parent}
        self.class_methods = defaultdict(set)  # {class: {methods}}
        
        self.current_file = None
        self.current_class = None
        self.current_function = None
        
    def visit_ClassDef(self, node):
        # Track inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritance[node.name] = base.id
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        if self.current_class:
            # Method
            method_key = f"{self.current_class}.{node.name}"
            self.methods[method_key] = (self.current_file, node.lineno)
            self.class_methods[self.current_class].add(node.name)
            old_function = self.current_function
            self.current_function = method_key
        else:
            # Function
            self.functions[node.name] = (self.current_file, node.lineno)
            old_function = self.current_function
            self.current_function = node.name
            
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_Call(self, node):
        if self.current_function:
            # Track what this function calls
            if isinstance(node.func, ast.Name):
                # Direct function call
                self.calls[self.current_function].add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Method call
                method_name = node.func.attr
                # Try to determine the class
                if isinstance(node.func.value, ast.Name):
                    # Could be self.method() or obj.method()
                    if node.func.value.id == 'self' and self.current_class:
                        method_key = f"{self.current_class}.{method_name}"
                        self.calls[self.current_function].add(method_key)
                    else:
                        # Generic method call
                        self.calls[self.current_function].add(f"*.{method_name}")
                        
        self.generic_visit(node)
        
    def analyze_file(self, filepath: str):
        self.current_file = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                self.visit(tree)
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            
    def get_callers(self, target: str) -> Set[str]:
        """Get all functions that call the target"""
        callers = set()
        for caller, callees in self.calls.items():
            if target in callees:
                callers.add(caller)
        return callers
        
    def get_callees(self, source: str) -> Set[str]:
        """Get all functions called by the source"""
        return self.calls.get(source, set())
        
    def get_call_chain(self, start: str, max_depth: int = 5) -> List[List[str]]:
        """Get call chains starting from a function"""
        chains = []
        
        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current in path:  # Cycle detection
                return
                
            new_path = path + [current]
            callees = self.get_callees(current)
            
            if not callees:
                chains.append(new_path)
            else:
                for callee in callees:
                    dfs(callee, new_path, depth + 1)
        
        dfs(start, [], 0)
        return chains
        
    def generate_dot_graph(self) -> str:
        """Generate DOT format graph for visualization"""
        lines = ['digraph CallGraph {']
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box];')
        lines.append('')
        
        # Add nodes
        for func in self.functions:
            lines.append(f'  "{func}" [color=blue];')
        for method in self.methods:
            lines.append(f'  "{method}" [color=green];')
        lines.append('')
        
        # Add edges
        for caller, callees in self.calls.items():
            for callee in callees:
                lines.append(f'  "{caller}" -> "{callee}";')
        
        lines.append('}')
        return '\n'.join(lines)

def analyze_directory(directory: str = "autonomy") -> CallGraphGenerator:
    """Analyze all Python files in directory"""
    generator = CallGraphGenerator()
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                generator.analyze_file(filepath)
    
    return generator

def generate_report(generator: CallGraphGenerator):
    """Generate call graph report"""
    report = []
    report.append("=" * 80)
    report.append("CALL GRAPH ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Statistics
    report.append("## STATISTICS")
    report.append("")
    report.append(f"Total functions: {len(generator.functions)}")
    report.append(f"Total methods: {len(generator.methods)}")
    report.append(f"Total call relationships: {sum(len(callees) for callees in generator.calls.values())}")
    report.append(f"Functions/methods with calls: {len(generator.calls)}")
    report.append("")
    
    # Most called functions
    call_counts = defaultdict(int)
    for callees in generator.calls.values():
        for callee in callees:
            call_counts[callee] += 1
    
    most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    
    report.append("## TOP 20 MOST CALLED FUNCTIONS/METHODS")
    report.append("")
    for func, count in most_called:
        report.append(f"- {func}: called {count} times")
    report.append("")
    
    # Functions that call many others
    most_callers = sorted(
        [(caller, len(callees)) for caller, callees in generator.calls.items()],
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    report.append("## TOP 20 FUNCTIONS WITH MOST CALLS")
    report.append("")
    for func, count in most_callers:
        report.append(f"- {func}: calls {count} other functions")
    report.append("")
    
    # Inheritance hierarchy
    report.append("## INHERITANCE HIERARCHY")
    report.append("")
    for child, parent in sorted(generator.inheritance.items()):
        report.append(f"- {child} extends {parent}")
    report.append("")
    
    # Summary
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    report.append("")
    report.append("Call graph analysis complete. Use the DOT file to visualize:")
    report.append("  dot -Tpng call_graph.dot -o call_graph.png")
    report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Starting call graph generation...")
    generator = analyze_directory()
    
    # Generate report
    report = generate_report(generator)
    with open("CALL_GRAPH_REPORT.txt", "w") as f:
        f.write(report)
    
    # Generate DOT file
    dot_graph = generator.generate_dot_graph()
    with open("call_graph.dot", "w") as f:
        f.write(dot_graph)
    
    print(report)
    print("\nReport saved to CALL_GRAPH_REPORT.txt")
    print("DOT graph saved to call_graph.dot")
    print("\nTo visualize: dot -Tpng call_graph.dot -o call_graph.png")