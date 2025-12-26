#!/usr/bin/env python3
"""
Deep Recursive Analysis - Depth 59
Examines call stacks, state transitions, integration patterns, and emergent behaviors
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
import re

class DeepRecursiveAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.call_graph = defaultdict(set)
        self.state_transitions = defaultdict(list)
        self.method_signatures = {}
        self.class_hierarchy = {}
        self.variable_flow = defaultdict(set)
        self.recursion_depth = 0
        self.max_depth = 59
        
    def analyze_file(self, filepath, depth=0):
        """Recursively analyze a Python file"""
        if depth > self.max_depth:
            return
        
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            for node in ast.walk(tree):
                # Analyze class definitions
                if isinstance(node, ast.ClassDef):
                    self.analyze_class(node, filepath, depth)
                
                # Analyze function definitions
                elif isinstance(node, ast.FunctionDef):
                    self.analyze_function(node, filepath, depth)
                
                # Analyze assignments (state changes)
                elif isinstance(node, ast.Assign):
                    self.analyze_assignment(node, filepath)
                
                # Analyze function calls
                elif isinstance(node, ast.Call):
                    self.analyze_call(node, filepath)
        
        except Exception as e:
            pass  # Skip files with syntax errors
    
    def analyze_class(self, node, filepath, depth):
        """Analyze class structure and inheritance"""
        class_name = node.name
        bases = [self.get_name(base) for base in node.bases]
        
        self.class_hierarchy[class_name] = {
            'file': str(filepath),
            'bases': bases,
            'methods': [],
            'depth': depth
        }
        
        # Analyze methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.class_hierarchy[class_name]['methods'].append(item.name)
                self.analyze_function(item, filepath, depth + 1)
    
    def analyze_function(self, node, filepath, depth):
        """Analyze function signature and body"""
        func_name = node.name
        
        # Extract parameters
        params = []
        for arg in node.args.args:
            params.append(arg.arg)
        
        # Extract return type
        return_type = None
        if node.returns:
            return_type = self.get_name(node.returns)
        
        self.method_signatures[func_name] = {
            'file': str(filepath),
            'params': params,
            'return_type': return_type,
            'depth': depth
        }
        
        # Analyze function calls within this function
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                called = self.get_name(item.func)
                if called:
                    self.call_graph[func_name].add(called)
    
    def analyze_assignment(self, node, filepath):
        """Analyze state variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    var_name = target.attr
                    
                    # Track state transitions
                    if isinstance(node.value, ast.Call):
                        func_called = self.get_name(node.value.func)
                        self.state_transitions[var_name].append({
                            'file': str(filepath),
                            'assigned_from': func_called
                        })
    
    def analyze_call(self, node, filepath):
        """Analyze function/method calls"""
        func_name = self.get_name(node.func)
        
        if func_name:
            # Track variable flow through function calls
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    self.variable_flow[arg.id].add(func_name)
    
    def get_name(self, node):
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self.get_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self.get_name(node.value)
        return None
    
    def calculate_call_depth(self, func_name, visited=None, depth=0):
        """Calculate maximum call depth from a function"""
        if visited is None:
            visited = set()
        
        if func_name in visited or depth > self.max_depth:
            return depth
        
        visited.add(func_name)
        
        if func_name not in self.call_graph:
            return depth
        
        max_depth = depth
        for called in self.call_graph[func_name]:
            child_depth = self.calculate_call_depth(called, visited.copy(), depth + 1)
            max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def find_recursive_patterns(self):
        """Find recursive and circular call patterns"""
        recursive = []
        circular = []
        
        for func in self.call_graph:
            # Check for direct recursion
            if func in self.call_graph[func]:
                recursive.append(func)
            
            # Check for circular calls
            visited = set()
            stack = [func]
            
            while stack:
                current = stack.pop()
                if current in visited:
                    if current == func:
                        circular.append(func)
                    continue
                
                visited.add(current)
                
                if current in self.call_graph:
                    for called in self.call_graph[current]:
                        if called == func:
                            circular.append(func)
                        else:
                            stack.append(called)
        
        return list(set(recursive)), list(set(circular))
    
    def analyze_integration_depth(self):
        """Analyze integration depth between subsystems"""
        integration_depth = {}
        
        phases_dir = self.base_dir / "pipeline" / "phases"
        
        if phases_dir.exists():
            for phase_file in phases_dir.glob("*.py"):
                if phase_file.name not in ["__init__.py", "base.py"]:
                    phase_name = phase_file.stem
                    
                    # Count import depth
                    with open(phase_file, 'r') as f:
                        content = f.read()
                    
                    # Count relative imports
                    relative_imports = len(re.findall(r'from\s+\.\.', content))
                    
                    # Count absolute imports
                    absolute_imports = len(re.findall(r'from\s+pipeline\.', content))
                    
                    # Count method calls to other subsystems
                    method_calls = len(re.findall(r'self\.\w+\.\w+\(', content))
                    
                    integration_depth[phase_name] = {
                        'relative_imports': relative_imports,
                        'absolute_imports': absolute_imports,
                        'method_calls': method_calls,
                        'total': relative_imports + absolute_imports + method_calls
                    }
        
        return integration_depth
    
    def analyze_state_complexity(self):
        """Analyze state variable complexity"""
        state_file = self.base_dir / "pipeline" / "state" / "manager.py"
        
        complexity = {
            'total_variables': 0,
            'mutable_collections': 0,
            'nested_structures': 0,
            'state_methods': 0
        }
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                content = f.read()
            
            # Count Dict, List types
            complexity['mutable_collections'] = len(re.findall(r':\s*(Dict|List)\[', content))
            
            # Count nested structures
            complexity['nested_structures'] = len(re.findall(r'Dict\[.*?Dict\[', content))
            
            # Count state manipulation methods
            complexity['state_methods'] = len(re.findall(r'def\s+\w+.*?state.*?\):', content))
            
            # Count total state variables
            complexity['total_variables'] = len(re.findall(r'^\s+\w+:\s+', content, re.MULTILINE))
        
        return complexity
    
    def generate_deep_report(self):
        """Generate comprehensive deep analysis report"""
        print("="*80)
        print("DEEP RECURSIVE ANALYSIS - DEPTH 59")
        print("="*80)
        
        # Analyze all Python files
        print("\n🔍 Analyzing Python files recursively...")
        for root, dirs, files in os.walk(self.base_dir / "pipeline"):
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    self.analyze_file(filepath, 0)
        
        # Class Hierarchy
        print(f"\n🏛️  CLASS HIERARCHY: {len(self.class_hierarchy)} classes")
        for class_name, info in sorted(self.class_hierarchy.items()):
            if info['bases']:
                print(f"   {class_name:30s} extends {', '.join(info['bases'])}")
                print(f"      Methods: {len(info['methods'])}, Depth: {info['depth']}")
        
        # Method Signatures
        print(f"\n📝 METHOD SIGNATURES: {len(self.method_signatures)} methods analyzed")
        print(f"   Average parameters per method: {sum(len(m['params']) for m in self.method_signatures.values()) / len(self.method_signatures):.1f}")
        
        # Call Graph
        print(f"\n📞 CALL GRAPH: {len(self.call_graph)} functions with calls")
        total_calls = sum(len(v) for v in self.call_graph.values())
        print(f"   Total function calls: {total_calls}")
        print(f"   Average calls per function: {total_calls / len(self.call_graph):.1f}")
        
        # Call Depth Analysis
        print(f"\n📏 CALL DEPTH ANALYSIS:")
        max_depths = {}
        for func in list(self.call_graph.keys())[:20]:  # Sample first 20
            depth = self.calculate_call_depth(func)
            max_depths[func] = depth
        
        if max_depths:
            avg_depth = sum(max_depths.values()) / len(max_depths)
            max_depth = max(max_depths.values())
            print(f"   Average call depth: {avg_depth:.1f}")
            print(f"   Maximum call depth: {max_depth}")
            print(f"   Functions with depth > 10:")
            for func, depth in sorted(max_depths.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {func:40s}: {depth}")
        
        # Recursive Patterns
        recursive, circular = self.find_recursive_patterns()
        print(f"\n🔄 RECURSIVE PATTERNS:")
        print(f"   Direct recursion: {len(recursive)} functions")
        print(f"   Circular calls: {len(circular)} functions")
        if recursive:
            print(f"   Recursive functions: {', '.join(recursive[:5])}")
        
        # State Transitions
        print(f"\n🔀 STATE TRANSITIONS: {len(self.state_transitions)} variables")
        for var, transitions in sorted(self.state_transitions.items())[:10]:
            print(f"   {var:30s}: {len(transitions)} transitions")
        
        # Variable Flow
        print(f"\n🌊 VARIABLE FLOW: {len(self.variable_flow)} variables tracked")
        high_flow = [(var, len(funcs)) for var, funcs in self.variable_flow.items() if len(funcs) > 3]
        print(f"   Variables with high flow (>3 functions): {len(high_flow)}")
        for var, count in sorted(high_flow, key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {var:30s}: flows through {count} functions")
        
        # Integration Depth
        integration = self.analyze_integration_depth()
        print(f"\n🔗 INTEGRATION DEPTH: {len(integration)} phases")
        for phase, depth in sorted(integration.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
            print(f"   {phase:30s}: {depth['total']} integration points")
            print(f"      Imports: {depth['relative_imports']} relative, {depth['absolute_imports']} absolute")
            print(f"      Method calls: {depth['method_calls']}")
        
        # State Complexity
        state_complexity = self.analyze_state_complexity()
        print(f"\n💾 STATE COMPLEXITY:")
        for metric, value in state_complexity.items():
            print(f"   {metric:30s}: {value}")
        
        print("\n" + "="*80)
        print("DEEP ANALYSIS COMPLETE")
        print("="*80)

if __name__ == "__main__":
    analyzer = DeepRecursiveAnalyzer(".")
    analyzer.generate_deep_report()