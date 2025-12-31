#!/usr/bin/env python3
"""Verify which method existence errors are real vs false positives."""

import ast
import sys
from pathlib import Path

def get_class_methods(filepath, class_name):
    """Extract all methods from a class."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                return methods
        return None
    except Exception as e:
        return None

# Check each reported error
checks = [
    ("pipeline/import_analyzer.py", "ImportAnalyzer", ["analyze", "generate_report", "analyze_consistency"]),
    ("pipeline/analysis/file_refactoring.py", "DuplicateDetector", ["analyze", "generate_report", "detect"]),
    ("pipeline/analysis/integration_gaps.py", "IntegrationGapFinder", ["analyze", "generate_report"]),
    ("pipeline/analysis/call_graph.py", "CallGraphGenerator", ["analyze", "generate_report", "generate_dot"]),
    ("pipeline/analysis/code_validation.py", "DictAccessValidator", ["validate_all", "generate_report"]),
]

print("=" * 80)
print("METHOD EXISTENCE VERIFICATION")
print("=" * 80)
print()

for filepath, class_name, expected_methods in checks:
    full_path = Path(filepath)
    if not full_path.exists():
        print(f"❌ {filepath} - FILE NOT FOUND")
        continue
    
    actual_methods = get_class_methods(full_path, class_name)
    if actual_methods is None:
        print(f"❌ {class_name} in {filepath} - CLASS NOT FOUND")
        continue
    
    print(f"✓ {class_name} in {filepath}")
    print(f"  Actual methods: {', '.join(sorted(actual_methods))}")
    print()
    
    for method in expected_methods:
        if method in actual_methods:
            print(f"  ✅ {method}() EXISTS")
        else:
            print(f"  ❌ {method}() MISSING - REAL BUG")
    print()

print("=" * 80)