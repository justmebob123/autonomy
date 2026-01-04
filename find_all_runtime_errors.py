#!/usr/bin/env python3
"""
Comprehensive script to find potential runtime errors in the autonomy codebase.
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

def analyze_file(filepath):
    """Analyze a Python file for potential runtime errors."""
    try:
        with open(filepath) as f:
            content = f.read()
            tree = ast.parse(content, filepath)
    except SyntaxError as e:
        return {'syntax_errors': [str(e)]}
    except Exception as e:
        return {'parse_errors': [str(e)]}
    
    issues = {
        'missing_imports': [],
        'undefined_attributes': [],
        'missing_super_calls': [],
    }
    
    # Track imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    
    # Check for common missing imports
    common_modules = {
        'time': ['time.time', 'time.sleep'],
        're': ['re.match', 're.search', 're.compile', 're.sub'],
        'json': ['json.loads', 'json.dumps'],
        'datetime': ['datetime.now', 'datetime.datetime'],
        'subprocess': ['subprocess.run', 'subprocess.Popen'],
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                module = node.value.id
                attr = node.attr
                full_name = f"{module}.{attr}"
                
                for req_module, patterns in common_modules.items():
                    if any(full_name.startswith(p.split('.')[0]) for p in patterns):
                        if req_module not in imports:
                            issues['missing_imports'].append(f"Uses {full_name} but {req_module} not imported")
    
    # Check for classes with mixins
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if class uses LoopDetectionMixin
            base_names = [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases]
            if 'LoopDetectionMixin' in base_names:
                # Check if __init__ calls init_loop_detection
                has_init = False
                calls_init_loop = False
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        has_init = True
                        for n in ast.walk(item):
                            if isinstance(n, ast.Call):
                                if isinstance(n.func, ast.Attribute):
                                    if isinstance(n.func.value, ast.Name) and n.func.value.id == 'self':
                                        if n.func.attr == 'init_loop_detection':
                                            calls_init_loop = True
                
                if has_init and not calls_init_loop:
                    issues['missing_super_calls'].append(
                        f"Class {node.name} uses LoopDetectionMixin but doesn't call init_loop_detection()"
                    )
    
    return issues

def main():
    """Main function."""
    print("=" * 80)
    print("COMPREHENSIVE RUNTIME ERROR DETECTION")
    print("=" * 80)
    print()
    
    all_issues = defaultdict(list)
    
    # Check all Python files in pipeline
    for py_file in Path('autonomy/pipeline').rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
        
        issues = analyze_file(py_file)
        
        for issue_type, issue_list in issues.items():
            if issue_list:
                for issue in issue_list:
                    all_issues[issue_type].append((str(py_file), issue))
    
    # Report findings
    total_issues = sum(len(v) for v in all_issues.values())
    
    if total_issues == 0:
        print("✅ No potential runtime errors found!")
        return 0
    
    print(f"⚠️  Found {total_issues} potential issues:\n")
    
    for issue_type, issues in sorted(all_issues.items()):
        if issues:
            print(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)}):")
            print("-" * 80)
            for filepath, issue in issues:
                print(f"  {filepath}")
                print(f"    → {issue}")
    
    return 1

if __name__ == '__main__':
    sys.exit(main())