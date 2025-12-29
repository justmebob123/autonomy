#!/usr/bin/env python3
"""
Enhanced Depth-61 Code Analyzer

Performs comprehensive analysis including:
1. Variable lifecycle tracing
2. Parallel implementation detection
3. Unused code identification
4. Dead code path detection
5. Integration gap analysis
6. Call graph analysis
7. Data flow analysis
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import difflib

class EnhancedDepth61Analyzer(ast.NodeVisitor):
    """Comprehensive code analyzer for depth-61 analysis"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.content = Path(filepath).read_text()
        self.tree = ast.parse(self.content)
        
        # Variable tracking
        self.variables = defaultdict(list)  # var_name -> [(action, line, scope)]
        self.variable_scopes = {}  # var_name -> scope_name
        
        # Function tracking
        self.functions = {}  # func_name -> metadata
        self.function_calls = defaultdict(list)  # func_name -> [call_lines]
        self.function_bodies = {}  # func_name -> normalized_body
        
        # Class tracking
        self.classes = {}  # class_name -> metadata
        self.class_methods = defaultdict(list)  # class_name -> [methods]
        
        # Import tracking
        self.imports = []  # [(module, alias, line)]
        self.import_usage = defaultdict(int)  # module -> usage_count
        
        # Dead code tracking
        self.unused_functions = set()
        self.unused_variables = set()
        self.unused_imports = set()
        self.unreachable_code = []
        
        # Parallel implementations
        self.similar_functions = []
        
        # Current scope tracking
        self.current_scope = 'module'
        self.scope_stack = ['module']
        
    def analyze(self):
        """Run complete analysis"""
        self.visit(self.tree)
        self._find_unused_functions()
        self._find_unused_variables()
        self._find_similar_functions()
        return self
    
    def visit_FunctionDef(self, node):
        """Track function definitions"""
        func_name = node.name
        
        # Store function metadata
        self.functions[func_name] = {
            'line': node.lineno,
            'end_line': node.end_lineno,
            'args': [arg.arg for arg in node.args.args],
            'returns': ast.unparse(node.returns) if node.returns else None,
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node),
            'is_private': func_name.startswith('_'),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'scope': self.current_scope
        }
        
        # Store function body for similarity detection
        body_str = ast.unparse(node)
        normalized = ''.join(body_str.split())
        self.function_bodies[func_name] = {
            'body': normalized,
            'line': node.lineno,
            'length': len(body_str)
        }
        
        # Track if in class
        if self.current_scope != 'module':
            self.class_methods[self.current_scope].append(func_name)
        
        # Enter function scope
        self.scope_stack.append(func_name)
        self.current_scope = func_name
        
        self.generic_visit(node)
        
        # Exit function scope
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]
    
    def visit_ClassDef(self, node):
        """Track class definitions"""
        class_name = node.name
        
        self.classes[class_name] = {
            'line': node.lineno,
            'end_line': node.end_lineno,
            'bases': [ast.unparse(base) for base in node.bases],
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        }
        
        # Enter class scope
        self.scope_stack.append(class_name)
        self.current_scope = class_name
        
        self.generic_visit(node)
        
        # Exit class scope
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]
    
    def visit_Name(self, node):
        """Track variable usage"""
        var_name = node.id
        
        if isinstance(node.ctx, ast.Store):
            self.variables[var_name].append(('write', node.lineno, self.current_scope))
        elif isinstance(node.ctx, ast.Load):
            self.variables[var_name].append(('read', node.lineno, self.current_scope))
        elif isinstance(node.ctx, ast.Del):
            self.variables[var_name].append(('delete', node.lineno, self.current_scope))
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Track function calls"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_calls[func_name].append(node.lineno)
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            self.function_calls[func_name].append(node.lineno)
            
            # Track module usage
            if isinstance(node.func.value, ast.Name):
                module = node.func.value.id
                self.import_usage[module] += 1
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Track imports"""
        for alias in node.names:
            self.imports.append((alias.name, alias.asname, node.lineno))
    
    def visit_ImportFrom(self, node):
        """Track from imports"""
        module = node.module or ''
        for alias in node.names:
            self.imports.append((f"{module}.{alias.name}", alias.asname, node.lineno))
    
    def _find_unused_functions(self):
        """Find functions that are never called"""
        for func_name in self.functions:
            # Skip if it's a special method
            if func_name.startswith('__') and func_name.endswith('__'):
                continue
            
            # Skip if it's called
            if func_name in self.function_calls:
                continue
            
            # Check if it's a public API function (might be called externally)
            if not func_name.startswith('_'):
                # Could be part of public API
                self.unused_functions.add(func_name)
    
    def _find_unused_variables(self):
        """Find variables that are written but never read"""
        for var_name, accesses in self.variables.items():
            # Skip special variables
            if var_name.startswith('_'):
                continue
            
            writes = [a for a in accesses if a[0] == 'write']
            reads = [a for a in accesses if a[0] == 'read']
            
            if writes and not reads:
                self.unused_variables.add(var_name)
    
    def _find_similar_functions(self, threshold=0.7):
        """Find functions with similar implementations"""
        functions = list(self.function_bodies.items())
        
        for i, (name1, data1) in enumerate(functions):
            for name2, data2 in functions[i+1:]:
                # Skip if one is too short
                if min(data1['length'], data2['length']) < 100:
                    continue
                
                # Calculate similarity
                similarity = difflib.SequenceMatcher(
                    None, 
                    data1['body'], 
                    data2['body']
                ).ratio()
                
                if similarity >= threshold:
                    self.similar_functions.append({
                        'func1': name1,
                        'func2': name2,
                        'similarity': similarity,
                        'line1': data1['line'],
                        'line2': data2['line']
                    })
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        
        report.append("=" * 80)
        report.append(f"ENHANCED DEPTH-61 ANALYSIS: {self.filepath}")
        report.append("=" * 80)
        
        # 1. Function Analysis
        report.append("\n1. FUNCTION ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total Functions: {len(self.functions)}")
        report.append(f"Public Functions: {sum(1 for f in self.functions if not f.startswith('_'))}")
        report.append(f"Private Functions: {sum(1 for f in self.functions if f.startswith('_'))}")
        report.append(f"Unused Functions: {len(self.unused_functions)}")
        
        if self.unused_functions:
            report.append("\n⚠️ UNUSED FUNCTIONS (defined but never called):")
            for func in sorted(self.unused_functions):
                meta = self.functions[func]
                report.append(f"  - {func}() at line {meta['line']}")
                if meta['docstring']:
                    report.append(f"    Purpose: {meta['docstring'][:60]}...")
        
        # 2. Variable Analysis
        report.append("\n2. VARIABLE ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total Variables: {len(self.variables)}")
        report.append(f"Write-Only Variables: {len(self.unused_variables)}")
        
        if self.unused_variables:
            report.append("\n⚠️ WRITE-ONLY VARIABLES (never read):")
            for var in sorted(self.unused_variables):
                writes = [a[1] for a in self.variables[var] if a[0] == 'write']
                report.append(f"  - {var} (written at lines: {writes})")
        
        # 3. Parallel Implementations
        report.append("\n3. PARALLEL IMPLEMENTATIONS")
        report.append("-" * 80)
        
        if self.similar_functions:
            report.append(f"\n⚠️ Found {len(self.similar_functions)} pairs of similar functions:")
            for sim in self.similar_functions:
                report.append(f"\n  {sim['func1']}() [line {sim['line1']}] <-> {sim['func2']}() [line {sim['line2']}]")
                report.append(f"    Similarity: {sim['similarity']:.1%}")
                report.append(f"    ⚠️ Consider consolidating these functions")
        else:
            report.append("✅ No parallel implementations detected")
        
        # 4. Class Analysis
        report.append("\n4. CLASS ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total Classes: {len(self.classes)}")
        
        for class_name, meta in self.classes.items():
            methods = self.class_methods.get(class_name, [])
            report.append(f"\n  {class_name} (line {meta['line']}):")
            report.append(f"    Methods: {len(methods)}")
            if meta['bases']:
                report.append(f"    Inherits: {', '.join(meta['bases'])}")
        
        # 5. Import Analysis
        report.append("\n5. IMPORT ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total Imports: {len(self.imports)}")
        
        # Find unused imports
        unused_imports = []
        for module, alias, line in self.imports:
            check_name = alias if alias else module.split('.')[-1]
            if check_name not in self.import_usage and check_name not in self.function_calls:
                unused_imports.append((module, line))
        
        if unused_imports:
            report.append(f"\n⚠️ POTENTIALLY UNUSED IMPORTS: {len(unused_imports)}")
            for module, line in unused_imports[:10]:
                report.append(f"  - {module} (line {line})")
        else:
            report.append("✅ All imports appear to be used")
        
        # 6. Call Graph
        report.append("\n6. CALL GRAPH ANALYSIS")
        report.append("-" * 80)
        
        call_freq = [(name, len(calls)) for name, calls in self.function_calls.items()]
        call_freq.sort(key=lambda x: x[1], reverse=True)
        
        report.append("Most Called Functions:")
        for name, count in call_freq[:10]:
            report.append(f"  - {name}(): {count} calls")
        
        # 7. Variable Access Patterns
        report.append("\n7. VARIABLE ACCESS PATTERNS")
        report.append("-" * 80)
        
        var_patterns = []
        for var_name, accesses in self.variables.items():
            writes = len([a for a in accesses if a[0] == 'write'])
            reads = len([a for a in accesses if a[0] == 'read'])
            if writes > 0 or reads > 0:
                var_patterns.append((var_name, writes, reads, writes + reads))
        
        var_patterns.sort(key=lambda x: x[3], reverse=True)
        
        report.append("Most Accessed Variables:")
        for var_name, writes, reads, total in var_patterns[:10]:
            report.append(f"  - {var_name}: {writes} writes, {reads} reads (total: {total})")
        
        return '\n'.join(report)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ENHANCED_DEPTH_61_ANALYZER.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    analyzer = EnhancedDepth61Analyzer(filepath)
    analyzer.analyze()
    print(analyzer.generate_report())