#!/usr/bin/env python3
"""Quick analysis of remaining files"""

import os
import ast
from pathlib import Path
from collections import defaultdict

def count_complexity(node):
    """Quick complexity count"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def analyze_file(filepath):
    """Analyze a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = count_complexity(node)
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'complexity': complexity
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node.lineno)
        
        lines = len(content.split('\n'))
        
        return {
            'filepath': filepath,
            'lines': lines,
            'functions': len(functions),
            'classes': len(classes),
            'imports': len(imports),
            'max_complexity': max([f['complexity'] for f in functions]) if functions else 0,
            'avg_complexity': sum([f['complexity'] for f in functions]) / len(functions) if functions else 0,
            'high_complexity_funcs': [f for f in functions if f['complexity'] > 20]
        }
    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e)
        }

def main():
    """Analyze all Python files"""
    base_dir = Path('autonomy')
    results = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                result = analyze_file(filepath)
                results.append(result)
    
    # Sort by max complexity
    results.sort(key=lambda x: x.get('max_complexity', 0), reverse=True)
    
    # Print summary
    print("=" * 80)
    print("QUICK FILE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal files analyzed: {len(results)}")
    print(f"\nTop 20 files by complexity:")
    print(f"{'File':<50} {'Lines':<8} {'Funcs':<8} {'Max Complexity'}")
    print("-" * 80)
    
    for result in results[:20]:
        if 'error' not in result:
            filepath = result['filepath'].replace('autonomy/', '')
            print(f"{filepath:<50} {result['lines']:<8} {result['functions']:<8} {result['max_complexity']}")
    
    # Files with high complexity functions
    print(f"\n\nFiles with functions >20 complexity:")
    print("-" * 80)
    for result in results:
        if 'error' not in result and result['high_complexity_funcs']:
            filepath = result['filepath'].replace('autonomy/', '')
            print(f"\n{filepath}:")
            for func in result['high_complexity_funcs']:
                print(f"  - {func['name']} (line {func['line']}): complexity {func['complexity']}")

if __name__ == '__main__':
    main()