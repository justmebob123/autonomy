#!/usr/bin/env python3
"""
Comprehensive analysis script to find all placeholders, stubs, and incomplete implementations.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json

class PlaceholderAnalyzer:
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
        self.issues = []
        
    def analyze(self):
        """Run all analysis checks."""
        print("=" * 80)
        print("COMPREHENSIVE PLACEHOLDER AND STUB ANALYSIS")
        print("=" * 80)
        print()
        
        # 1. Search for explicit placeholders
        self.find_placeholder_comments()
        
        # 2. Search for TODO/FIXME/HACK
        self.find_todo_comments()
        
        # 3. Find NotImplementedError
        self.find_not_implemented()
        
        # 4. Find empty functions
        self.find_empty_functions()
        
        # 5. Find functions that only return empty values
        self.find_empty_returns()
        
        # 6. Find suspicious patterns
        self.find_suspicious_patterns()
        
        # 7. Generate report
        self.generate_report()
    
    def find_placeholder_comments(self):
        """Find explicit placeholder comments."""
        print("1. Searching for PLACEHOLDER comments...")
        pattern = re.compile(r'#.*placeholder', re.IGNORECASE)
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            self.issues.append({
                                'type': 'PLACEHOLDER_COMMENT',
                                'severity': 'HIGH',
                                'file': str(py_file),
                                'line': line_num,
                                'content': line.strip()
                            })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] == 'PLACEHOLDER_COMMENT'])
        print(f"   Found {count} placeholder comments")
    
    def find_todo_comments(self):
        """Find TODO/FIXME/HACK comments."""
        print("2. Searching for TODO/FIXME/HACK comments...")
        pattern = re.compile(r'#.*(TODO|FIXME|HACK|XXX).*implement', re.IGNORECASE)
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            self.issues.append({
                                'type': 'TODO_IMPLEMENT',
                                'severity': 'MEDIUM',
                                'file': str(py_file),
                                'line': line_num,
                                'content': line.strip()
                            })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] == 'TODO_IMPLEMENT'])
        print(f"   Found {count} TODO/FIXME comments about implementation")
    
    def find_not_implemented(self):
        """Find NotImplementedError raises."""
        print("3. Searching for NotImplementedError...")
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for stmt in node.body:
                            if isinstance(stmt, ast.Raise):
                                if isinstance(stmt.exc, ast.Name) and stmt.exc.id == 'NotImplementedError':
                                    # Check if this is an abstract method (acceptable)
                                    is_abstract = any(
                                        isinstance(d, ast.Name) and d.id in ('abstractmethod', 'abc.abstractmethod')
                                        for d in node.decorator_list
                                    )
                                    
                                    if not is_abstract:
                                        self.issues.append({
                                            'type': 'NOT_IMPLEMENTED',
                                            'severity': 'HIGH',
                                            'file': str(py_file),
                                            'line': node.lineno,
                                            'function': node.name,
                                            'content': f"Function '{node.name}' raises NotImplementedError"
                                        })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] == 'NOT_IMPLEMENTED'])
        print(f"   Found {count} NotImplementedError (non-abstract)")
    
    def find_empty_functions(self):
        """Find functions with empty or only pass."""
        print("4. Searching for empty functions...")
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        body = node.body
                        
                        # Skip docstring
                        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                            body = body[1:]
                        
                        # Check if empty or only pass
                        if not body or (len(body) == 1 and isinstance(body[0], ast.Pass)):
                            # Check if abstract
                            is_abstract = any(
                                isinstance(d, ast.Name) and d.id in ('abstractmethod', 'abc.abstractmethod')
                                for d in node.decorator_list
                            )
                            
                            if not is_abstract:
                                self.issues.append({
                                    'type': 'EMPTY_FUNCTION',
                                    'severity': 'MEDIUM',
                                    'file': str(py_file),
                                    'line': node.lineno,
                                    'function': node.name,
                                    'content': f"Function '{node.name}' is empty or only has pass"
                                })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] == 'EMPTY_FUNCTION'])
        print(f"   Found {count} empty functions (non-abstract)")
    
    def find_empty_returns(self):
        """Find functions that only return empty values."""
        print("5. Searching for functions returning only empty values...")
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        body = node.body
                        
                        # Skip docstring
                        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                            body = body[1:]
                        
                        # Check if only returns empty value
                        if len(body) == 1 and isinstance(body[0], ast.Return):
                            ret_val = body[0].value
                            ret_type = None
                            
                            if ret_val is None:
                                ret_type = "None"
                            elif isinstance(ret_val, ast.Constant):
                                if ret_val.value in (False, 0, "", [], {}):
                                    ret_type = repr(ret_val.value)
                            elif isinstance(ret_val, ast.Dict) and not ret_val.keys:
                                ret_type = "{}"
                            elif isinstance(ret_val, ast.List) and not ret_val.elts:
                                ret_type = "[]"
                            
                            if ret_type:
                                self.issues.append({
                                    'type': 'EMPTY_RETURN',
                                    'severity': 'LOW',
                                    'file': str(py_file),
                                    'line': node.lineno,
                                    'function': node.name,
                                    'content': f"Function '{node.name}' only returns {ret_type}"
                                })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] == 'EMPTY_RETURN'])
        print(f"   Found {count} functions returning only empty values")
    
    def find_suspicious_patterns(self):
        """Find suspicious patterns in code."""
        print("6. Searching for suspicious patterns...")
        
        patterns = [
            (r'return\s+None\s*#.*placeholder', 'SUSPICIOUS_RETURN', 'MEDIUM'),
            (r'return\s+\{\}\s*#.*placeholder', 'SUSPICIOUS_RETURN', 'MEDIUM'),
            (r'return\s+\[\]\s*#.*placeholder', 'SUSPICIOUS_RETURN', 'MEDIUM'),
            (r'#.*stub', 'STUB_COMMENT', 'MEDIUM'),
        ]
        
        for py_file in self.root_dir.rglob('*.py'):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, issue_type, severity in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                self.issues.append({
                                    'type': issue_type,
                                    'severity': severity,
                                    'file': str(py_file),
                                    'line': line_num,
                                    'content': line.strip()
                                })
            except Exception:
                pass
        
        count = len([i for i in self.issues if i['type'] in ('SUSPICIOUS_RETURN', 'STUB_COMMENT')])
        print(f"   Found {count} suspicious patterns")
    
    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__',
            '.git',
            'test_',
            '.pyc',
            'venv',
            'env',
        ]
        
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def generate_report(self):
        """Generate comprehensive report."""
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print()
        
        # Group by severity
        by_severity = {}
        for issue in self.issues:
            severity = issue['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
        
        # Print summary
        print(f"Total issues found: {len(self.issues)}")
        print()
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            if severity in by_severity:
                issues = by_severity[severity]
                print(f"{severity} SEVERITY: {len(issues)} issues")
                
                # Group by type
                by_type = {}
                for issue in issues:
                    issue_type = issue['type']
                    if issue_type not in by_type:
                        by_type[issue_type] = []
                    by_type[issue_type].append(issue)
                
                for issue_type, type_issues in sorted(by_type.items()):
                    print(f"  {issue_type}: {len(type_issues)}")
                    for issue in type_issues[:5]:  # Show first 5
                        print(f"    {issue['file']}:{issue['line']}")
                        print(f"      {issue['content'][:80]}")
                    if len(type_issues) > 5:
                        print(f"    ... and {len(type_issues) - 5} more")
                print()
        
        # Save detailed report
        report_file = self.root_dir / 'PLACEHOLDER_ANALYSIS_REPORT.json'
        with open(report_file, 'w') as f:
            json.dump(self.issues, f, indent=2)
        
        print(f"Detailed report saved to: {report_file}")
        print()
        
        # Critical issues
        critical = [i for i in self.issues if i['severity'] == 'HIGH']
        if critical:
            print("=" * 80)
            print("CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION")
            print("=" * 80)
            print()
            for issue in critical:
                print(f"❌ {issue['file']}:{issue['line']}")
                print(f"   Type: {issue['type']}")
                print(f"   {issue['content']}")
                print()

if __name__ == '__main__':
    analyzer = PlaceholderAnalyzer()
    analyzer.analyze()