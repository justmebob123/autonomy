#!/usr/bin/env python3
"""Test that merge_file_implementations fix works correctly."""

import ast
import tempfile
from pathlib import Path

# Simulate the FIXED merge logic
def merge_files_fixed(source_files_content):
    """Fixed version of merge logic."""
    all_imports = set()
    all_classes = {}
    all_functions = {}
    all_other_code = []
    module_docstring = None
    
    for content in source_files_content:
        tree = ast.parse(content)
        
        # Extract module docstring
        if ast.get_docstring(tree) and not module_docstring:
            module_docstring = ast.get_docstring(tree)
        
        # FIXED: Skip docstring node when iterating
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                all_imports.add(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                if node.name not in all_classes:
                    all_classes[node.name] = ast.unparse(node)
            elif isinstance(node, ast.FunctionDef):
                if node.name not in all_functions:
                    all_functions[node.name] = ast.unparse(node)
            elif i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                # Skip module docstring (first node that's a string expression)
                continue
            else:
                all_other_code.append(ast.unparse(node))
    
    # Build merged content
    merged_lines = []
    
    if module_docstring:
        merged_lines.append(f'"""{module_docstring}"""')
        merged_lines.append("")
    
    if all_imports:
        merged_lines.extend(sorted(all_imports))
        merged_lines.append("")
    
    if all_other_code:
        merged_lines.extend(all_other_code)
        merged_lines.append("")
    
    if all_classes:
        for class_code in all_classes.values():
            merged_lines.append(class_code)
            merged_lines.append("")
    
    if all_functions:
        for func_code in all_functions.values():
            merged_lines.append(func_code)
            merged_lines.append("")
    
    return "\n".join(merged_lines)


# Simulate the BROKEN merge logic (old version)
def merge_files_broken(source_files_content):
    """Broken version that duplicates docstrings."""
    all_imports = set()
    all_classes = {}
    all_functions = {}
    all_other_code = []
    module_docstring = None
    
    for content in source_files_content:
        tree = ast.parse(content)
        
        # Extract module docstring
        if ast.get_docstring(tree) and not module_docstring:
            module_docstring = ast.get_docstring(tree)
        
        # BROKEN: Doesn't skip docstring node
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                all_imports.add(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                if node.name not in all_classes:
                    all_classes[node.name] = ast.unparse(node)
            elif isinstance(node, ast.FunctionDef):
                if node.name not in all_functions:
                    all_functions[node.name] = ast.unparse(node)
            else:
                # BUG: This includes the docstring node!
                all_other_code.append(ast.unparse(node))
    
    # Build merged content
    merged_lines = []
    
    if module_docstring:
        merged_lines.append(f'"""{module_docstring}"""')
        merged_lines.append("")
    
    if all_imports:
        merged_lines.extend(sorted(all_imports))
        merged_lines.append("")
    
    if all_other_code:
        merged_lines.extend(all_other_code)
        merged_lines.append("")
    
    if all_classes:
        for class_code in all_classes.values():
            merged_lines.append(class_code)
            merged_lines.append("")
    
    if all_functions:
        for func_code in all_functions.values():
            merged_lines.append(func_code)
            merged_lines.append("")
    
    return "\n".join(merged_lines)


def test_merge():
    """Test the merge fix."""
    
    # Create test files with docstrings
    file1 = '''"""Resource Estimator Module

Provides the ResourceEstimator class for estimating project resources."""

import sys

class ResourceEstimator:
    def estimate(self):
        pass
'''
    
    file2 = '''"""Resource Estimator Module

Provides functionality to estimate project effort and cost based on parsed tasks and durations."""

import os

def calculate_cost():
    pass
'''
    
    file3 = '''"""Resource Estimator Module

Provides the ResourceEstimator class for estimating project resources."""

import json

CONSTANT = 42
'''
    
    source_files = [file1, file2, file3]
    
    print("=" * 80)
    print("TESTING MERGE FIX")
    print("=" * 80)
    
    # Test broken version
    print("\n1. BROKEN VERSION (duplicates docstrings):")
    print("-" * 80)
    broken_result = merge_files_broken(source_files)
    broken_docstring_count = broken_result.count('"""Resource Estimator Module')
    print(f"Docstring appears {broken_docstring_count} times")
    print(f"Total size: {len(broken_result)} bytes")
    print("\nFirst 500 chars:")
    print(broken_result[:500])
    
    # Test fixed version
    print("\n\n2. FIXED VERSION (no duplicates):")
    print("-" * 80)
    fixed_result = merge_files_fixed(source_files)
    fixed_docstring_count = fixed_result.count('"""Resource Estimator Module')
    print(f"Docstring appears {fixed_docstring_count} times")
    print(f"Total size: {len(fixed_result)} bytes")
    print("\nFirst 500 chars:")
    print(fixed_result[:500])
    
    # Verify fix
    print("\n\n3. VERIFICATION:")
    print("-" * 80)
    if broken_docstring_count > 1:
        print(f"✅ CONFIRMED: Broken version duplicates docstring ({broken_docstring_count} times)")
    else:
        print(f"❌ UNEXPECTED: Broken version didn't duplicate docstring")
    
    if fixed_docstring_count == 1:
        print(f"✅ CONFIRMED: Fixed version has docstring exactly once")
    else:
        print(f"❌ FAILED: Fixed version has docstring {fixed_docstring_count} times (expected 1)")
    
    size_reduction = len(broken_result) - len(fixed_result)
    print(f"\n📊 Size reduction: {size_reduction} bytes ({size_reduction/len(broken_result)*100:.1f}%)")
    
    # Show what would happen with many files
    print("\n\n4. EXTRAPOLATION TO REAL SCENARIO:")
    print("-" * 80)
    print("If merging 100 files with similar docstrings:")
    print(f"  Broken version: ~{len(broken_result) * 100 / 3:,.0f} bytes")
    print(f"  Fixed version:  ~{len(fixed_result) * 100 / 3:,.0f} bytes")
    print(f"  Difference:     ~{size_reduction * 100 / 3:,.0f} bytes")
    
    return fixed_docstring_count == 1 and broken_docstring_count > 1


if __name__ == "__main__":
    success = test_merge()
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: Fix works correctly!")
    else:
        print("❌ TEST FAILED: Fix doesn't work as expected")
    print("=" * 80)