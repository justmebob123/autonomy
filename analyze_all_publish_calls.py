#!/usr/bin/env python3
"""
Analyze all MessageBus.publish() calls to identify incorrect usage patterns.
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

class PublishCallAnalyzer(ast.NodeVisitor):
    """Analyzes MessageBus.publish() calls."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.calls = []
        
    def visit_Call(self, node: ast.Call):
        """Check for message_bus.publish() calls."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'publish':
                # Check if it's self.message_bus.publish
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'message_bus':
                        self._analyze_publish_call(node)
        
        self.generic_visit(node)
    
    def _analyze_publish_call(self, node: ast.Call):
        """Analyze a publish() call."""
        call_info = {
            'file': str(self.filepath),
            'line': node.lineno,
            'positional_args': len(node.args),
            'keyword_args': [kw.arg for kw in node.keywords],
            'first_arg_type': self._get_arg_type(node.args[0]) if node.args else None,
            'is_correct': True,
            'issues': []
        }
        
        # Check for incorrect patterns
        if call_info['positional_args'] > 1:
            call_info['is_correct'] = False
            call_info['issues'].append(f"Too many positional args: {call_info['positional_args']} (expected 1)")
        
        if call_info['keyword_args']:
            call_info['is_correct'] = False
            call_info['issues'].append(f"Invalid keyword args: {', '.join(call_info['keyword_args'])}")
        
        if call_info['first_arg_type'] and call_info['first_arg_type'] != 'Message':
            if 'MessageType' in call_info['first_arg_type']:
                call_info['is_correct'] = False
                call_info['issues'].append(f"First arg is {call_info['first_arg_type']}, should be Message object")
        
        self.calls.append(call_info)
    
    def _get_arg_type(self, arg):
        """Try to determine the type of an argument."""
        if isinstance(arg, ast.Name):
            return arg.id
        elif isinstance(arg, ast.Attribute):
            return f"{self._get_arg_type(arg.value)}.{arg.attr}"
        elif isinstance(arg, ast.Call):
            if isinstance(arg.func, ast.Name):
                return arg.func.id
            elif isinstance(arg.func, ast.Attribute):
                return arg.func.attr
        return "Unknown"

def analyze_project(project_root: Path) -> Dict[str, Any]:
    """Analyze all publish() calls in the project."""
    all_calls = []
    
    for py_file in project_root.rglob("*.py"):
        if py_file.name.startswith('.'):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
            
            analyzer = PublishCallAnalyzer(py_file)
            analyzer.visit(tree)
            all_calls.extend(analyzer.calls)
            
        except Exception as e:
            pass
    
    # Categorize calls
    correct_calls = [c for c in all_calls if c['is_correct']]
    incorrect_calls = [c for c in all_calls if not c['is_correct']]
    
    return {
        'total_calls': len(all_calls),
        'correct_calls': len(correct_calls),
        'incorrect_calls': len(incorrect_calls),
        'all_calls': all_calls,
        'incorrect_details': incorrect_calls
    }

def main():
    project_root = Path(".")
    
    print("=" * 80)
    print("MESSAGEBUS.PUBLISH() CALL ANALYSIS")
    print("=" * 80)
    print()
    
    results = analyze_project(project_root)
    
    print(f"📊 SUMMARY")
    print(f"   Total publish() calls found: {results['total_calls']}")
    print(f"   ✅ Correct calls: {results['correct_calls']}")
    print(f"   ❌ Incorrect calls: {results['incorrect_calls']}")
    print()
    
    if results['incorrect_calls'] > 0:
        print("=" * 80)
        print("❌ INCORRECT CALLS FOUND")
        print("=" * 80)
        print()
        
        for i, call in enumerate(results['incorrect_details'], 1):
            print(f"{i}. {call['file']}:{call['line']}")
            print(f"   Positional args: {call['positional_args']}")
            print(f"   Keyword args: {call['keyword_args']}")
            print(f"   First arg type: {call['first_arg_type']}")
            print(f"   Issues:")
            for issue in call['issues']:
                print(f"      - {issue}")
            print()
    
    print("=" * 80)
    print()
    
    return 0 if results['incorrect_calls'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())