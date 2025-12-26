"""
Call Chain Tracing System for Application Troubleshooting Phase.

This module provides tools to trace execution paths and identify where
errors occur in the application flow.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple


class CallChainTracer:
    """Traces call chains and execution paths in Python code."""
    
    def __init__(self, project_root: str):
        """
        Initialize the call chain tracer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.call_graph = {}
        self.function_definitions = {}
        self.import_graph = {}
        
    def trace(self, entry_point: Optional[str] = None) -> Dict[str, Any]:
        """
        Trace call chains starting from an entry point.
        
        Args:
            entry_point: Optional entry point file (e.g., 'main.py')
            
        Returns:
            Dictionary containing trace results
        """
        # Build call graph
        self._build_call_graph()
        
        # Find entry points if not specified
        if not entry_point:
            entry_points = self._find_entry_points()
        else:
            entry_points = [entry_point]
        
        results = {
            'entry_points': entry_points,
            'call_graph': self.call_graph,
            'function_definitions': self.function_definitions,
            'import_graph': self.import_graph,
            'critical_paths': self._identify_critical_paths(),
            'error_prone_functions': self._identify_error_prone_functions()
        }
        
        return results
    
    def _build_call_graph(self):
        """Build a call graph of the entire project."""
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            
            try:
                self._analyze_file(file_path)
            except Exception as e:
                # Skip files that can't be parsed
                continue
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped."""
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'tests', 'test'}
        return any(skip_dir in file_path.parts for skip_dir in skip_dirs)
    
    def _analyze_file(self, file_path: Path):
        """Analyze a Python file to extract call information."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            relative_path = str(file_path.relative_to(self.project_root))
            
            # Extract function definitions and calls
            visitor = CallGraphVisitor(relative_path)
            visitor.visit(tree)
            
            # Store results
            self.call_graph[relative_path] = visitor.calls
            self.function_definitions[relative_path] = visitor.functions
            self.import_graph[relative_path] = visitor.imports
            
        except Exception as e:
            pass
    
    def _find_entry_points(self) -> List[str]:
        """Find potential entry points in the project."""
        entry_points = []
        
        # Common entry point names
        entry_names = ['main.py', 'run.py', 'app.py', 'server.py', '__main__.py']
        
        for name in entry_names:
            for file_path in self.project_root.rglob(name):
                if not self._should_skip_file(file_path):
                    relative_path = str(file_path.relative_to(self.project_root))
                    entry_points.append(relative_path)
        
        # Also look for files with if __name__ == '__main__'
        for file_path, functions in self.function_definitions.items():
            if any(f.get('is_main') for f in functions):
                if file_path not in entry_points:
                    entry_points.append(file_path)
        
        return entry_points
    
    def _identify_critical_paths(self) -> List[Dict[str, Any]]:
        """Identify critical execution paths."""
        critical_paths = []
        
        # Look for paths involving error handling, configuration, or initialization
        critical_keywords = ['error', 'exception', 'config', 'init', 'setup', 'start']
        
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                func_name = func['name'].lower()
                
                if any(keyword in func_name for keyword in critical_keywords):
                    critical_paths.append({
                        'file': file_path,
                        'function': func['name'],
                        'line': func['line'],
                        'type': self._classify_function(func['name'])
                    })
        
        return critical_paths
    
    def _classify_function(self, func_name: str) -> str:
        """Classify a function based on its name."""
        func_lower = func_name.lower()
        
        if 'error' in func_lower or 'exception' in func_lower:
            return 'error_handling'
        elif 'config' in func_lower or 'setting' in func_lower:
            return 'configuration'
        elif 'init' in func_lower or 'setup' in func_lower:
            return 'initialization'
        elif 'start' in func_lower or 'run' in func_lower:
            return 'execution'
        elif 'test' in func_lower:
            return 'testing'
        else:
            return 'general'
    
    def _identify_error_prone_functions(self) -> List[Dict[str, Any]]:
        """Identify functions that are likely to be error-prone."""
        error_prone = []
        
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                risk_score = 0
                risk_factors = []
                
                # Check complexity indicators
                if func.get('num_calls', 0) > 10:
                    risk_score += 2
                    risk_factors.append('High number of function calls')
                
                if func.get('has_try_except'):
                    risk_score += 1
                    risk_factors.append('Contains error handling')
                
                if func.get('has_external_calls'):
                    risk_score += 2
                    risk_factors.append('Makes external calls')
                
                # Check for I/O operations
                io_keywords = ['open', 'read', 'write', 'file', 'socket', 'request']
                if any(keyword in func['name'].lower() for keyword in io_keywords):
                    risk_score += 1
                    risk_factors.append('Performs I/O operations')
                
                if risk_score >= 3:
                    error_prone.append({
                        'file': file_path,
                        'function': func['name'],
                        'line': func['line'],
                        'risk_score': risk_score,
                        'risk_factors': risk_factors
                    })
        
        # Sort by risk score
        error_prone.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return error_prone
    
    def trace_function_calls(self, function_name: str) -> Dict[str, Any]:
        """
        Trace all calls to a specific function.
        
        Args:
            function_name: Name of the function to trace
            
        Returns:
            Dictionary containing trace results
        """
        results = {
            'function': function_name,
            'definitions': [],
            'callers': [],
            'callees': []
        }
        
        # Find where the function is defined
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                if func['name'] == function_name:
                    results['definitions'].append({
                        'file': file_path,
                        'line': func['line']
                    })
        
        # Find who calls this function
        for file_path, calls in self.call_graph.items():
            if function_name in calls:
                results['callers'].append({
                    'file': file_path,
                    'calls': calls[function_name]
                })
        
        # Find what this function calls
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                if func['name'] == function_name:
                    if file_path in self.call_graph:
                        results['callees'] = list(self.call_graph[file_path].keys())
        
        return results
    
    def format_report(self, results: Dict[str, Any]) -> str:
        """Format trace results as a readable report."""
        report = []
        report.append("=" * 80)
        report.append("CALL CHAIN TRACE REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Entry points section
        report.append("Entry Points:")
        report.append("-" * 80)
        for entry in results.get('entry_points', []):
            report.append(f"  • {entry}")
        report.append("")
        
        # Critical paths section
        report.append("Critical Execution Paths:")
        report.append("-" * 80)
        critical_paths = results.get('critical_paths', [])
        if critical_paths:
            # Group by type
            by_type = {}
            for path in critical_paths:
                path_type = path['type']
                if path_type not in by_type:
                    by_type[path_type] = []
                by_type[path_type].append(path)
            
            for path_type, paths in by_type.items():
                report.append(f"  {path_type.upper()}:")
                for path in paths[:5]:  # Show first 5 of each type
                    report.append(f"    • {path['function']} in {path['file']}:{path['line']}")
                if len(paths) > 5:
                    report.append(f"    ... and {len(paths) - 5} more")
                report.append("")
        else:
            report.append("  No critical paths identified")
            report.append("")
        
        # Error-prone functions section
        report.append("Error-Prone Functions:")
        report.append("-" * 80)
        error_prone = results.get('error_prone_functions', [])
        if error_prone:
            for func in error_prone[:10]:  # Show top 10
                report.append(f"  • {func['function']} in {func['file']}:{func['line']}")
                report.append(f"    Risk Score: {func['risk_score']}")
                report.append(f"    Risk Factors:")
                for factor in func['risk_factors']:
                    report.append(f"      - {factor}")
                report.append("")
            
            if len(error_prone) > 10:
                report.append(f"  ... and {len(error_prone) - 10} more functions")
                report.append("")
        else:
            report.append("  No error-prone functions identified")
            report.append("")
        
        # Import graph section
        report.append("Import Dependencies:")
        report.append("-" * 80)
        import_graph = results.get('import_graph', {})
        if import_graph:
            # Show files with most imports
            sorted_imports = sorted(
                import_graph.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            for file_path, imports in sorted_imports[:10]:
                if imports:
                    report.append(f"  • {file_path} ({len(imports)} imports)")
                    for imp in imports[:3]:
                        report.append(f"    - {imp}")
                    if len(imports) > 3:
                        report.append(f"    ... and {len(imports) - 3} more")
                    report.append("")
        else:
            report.append("  No import information available")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor to extract call graph information."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.calls = {}
        self.functions = []
        self.imports = []
        self.current_function = None
        
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'num_calls': 0,
            'has_try_except': False,
            'has_external_calls': False,
            'is_main': False
        }
        
        # Check if it's a main block
        if node.name == '__main__':
            func_info['is_main'] = True
        
        # Store current function context
        prev_function = self.current_function
        self.current_function = node.name
        
        # Visit function body
        self.generic_visit(node)
        
        # Count calls in this function
        func_info['num_calls'] = sum(
            len(calls) for func, calls in self.calls.items()
            if func == node.name
        )
        
        self.functions.append(func_info)
        self.current_function = prev_function
        
    def visit_Call(self, node):
        """Visit function call."""
        func_name = self._get_call_name(node)
        
        if func_name and self.current_function:
            if func_name not in self.calls:
                self.calls[func_name] = []
            
            self.calls[func_name].append({
                'line': node.lineno,
                'in_function': self.current_function
            })
        
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Visit try-except block."""
        if self.current_function:
            for func in self.functions:
                if func['name'] == self.current_function:
                    func['has_try_except'] = True
                    break
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append(alias.name)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from-import statement."""
        if node.module:
            self.imports.append(node.module)
        
        self.generic_visit(node)
    
    def _get_call_name(self, node) -> Optional[str]:
        """Extract the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None