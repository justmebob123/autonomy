#!/usr/bin/env python3
"""
Check for potential UnboundLocalError with 'task' variable usage.
Looks for patterns where task.task_id is used before task is defined.
"""

import ast
import sys
from pathlib import Path

def check_task_usage(filepath):
    """Check if task variable is used before being defined."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    
    issues = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if this is an execute method
            if node.name == 'execute':
                # Track where task is defined and used
                task_defined_line = None
                task_used_lines = []
                
                # Check function parameters
                for arg in node.args.args:
                    if arg.arg == 'task':
                        task_defined_line = node.lineno
                        break
                
                # Walk through function body
                for stmt in ast.walk(node):
                    # Look for task assignments
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == 'task':
                                if task_defined_line is None or stmt.lineno < task_defined_line:
                                    task_defined_line = stmt.lineno
                    
                    # Look for task in for loop targets
                    if isinstance(stmt, ast.For):
                        if isinstance(stmt.target, ast.Tuple):
                            for elt in stmt.target.elts:
                                if isinstance(elt, ast.Name) and elt.id == 'task':
                                    if task_defined_line is None or stmt.lineno < task_defined_line:
                                        task_defined_line = stmt.lineno
                        elif isinstance(stmt.target, ast.Name) and stmt.target.id == 'task':
                            if task_defined_line is None or stmt.lineno < task_defined_line:
                                task_defined_line = stmt.lineno
                    
                    # Look for task usage (task.task_id)
                    if isinstance(stmt, ast.Attribute):
                        if isinstance(stmt.value, ast.Name) and stmt.value.id == 'task':
                            task_used_lines.append(stmt.lineno)
                
                # Check if any usage comes before definition
                if task_used_lines and task_defined_line:
                    for used_line in task_used_lines:
                        if used_line < task_defined_line:
                            issues.append({
                                'file': filepath,
                                'function': node.name,
                                'used_line': used_line,
                                'defined_line': task_defined_line,
                                'message': f'task used at line {used_line} before defined at line {task_defined_line}'
                            })
                elif task_used_lines and not task_defined_line:
                    # task is used but never defined (not a parameter, not assigned)
                    issues.append({
                        'file': filepath,
                        'function': node.name,
                        'used_line': min(task_used_lines),
                        'defined_line': None,
                        'message': f'task used at line {min(task_used_lines)} but never defined'
                    })
    
    return issues

def main():
    phase_files = Path('autonomy/pipeline/phases').glob('*.py')
    
    all_issues = []
    for filepath in phase_files:
        issues = check_task_usage(filepath)
        all_issues.extend(issues)
    
    if all_issues:
        print("⚠️  Found potential UnboundLocalError issues with 'task' variable:\n")
        for issue in all_issues:
            print(f"❌ {issue['file']}:{issue['used_line']}")
            print(f"   Function: {issue['function']}")
            print(f"   {issue['message']}\n")
        return 1
    else:
        print("✅ No issues found with 'task' variable usage")
        return 0

if __name__ == '__main__':
    sys.exit(main())