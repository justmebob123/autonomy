"""
Import Analyzer

Analyzes import statements and suggests proper placement.
"""

import ast
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ImportAnalyzer:
    """Analyzes imports and suggests proper fixes."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def analyze_missing_import(
        self,
        filepath: str,
        module_name: str,
        usage_line: int
    ) -> Dict:
        """
        Analyze where an import should be added.
        
        Returns:
            - should_add_import: bool
            - import_location: 'top' or 'local'
            - existing_imports: list of current imports
            - suggested_import: the import statement to add
            - reason: why this location
        """
        result = {
            'module_name': module_name,
            'usage_line': usage_line,
            'should_add_import': True,
            'import_location': 'top',
            'existing_imports': [],
            'suggested_import': None,
            'reason': None
        }
        
        full_path = self.project_root / filepath
        if not full_path.exists():
            result['error'] = f"File not found: {filepath}"
            return result
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
                lines = source.split('\n')
            
            tree = ast.parse(source)
            
            # Find existing imports
            existing_imports = []
            last_import_line = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        existing_imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'line': node.lineno
                        })
                        last_import_line = max(last_import_line, node.lineno)
                elif isinstance(node, ast.ImportFrom):
                    existing_imports.append({
                        'type': 'from',
                        'module': node.module,
                        'names': [alias.name for alias in node.names],
                        'line': node.lineno
                    })
                    last_import_line = max(last_import_line, node.lineno)
            
            result['existing_imports'] = existing_imports
            
            # Check if import already exists
            for imp in existing_imports:
                if imp.get('module') == module_name:
                    result['should_add_import'] = False
                    result['reason'] = f"Import already exists at line {imp['line']}"
                    return result
            
            # Determine where to add import
            # Rule: Add at module level (top) unless it's a conditional import
            result['import_location'] = 'top'
            result['suggested_import'] = f"import {module_name}"
            
            # Find the right line to insert (after existing imports)
            if last_import_line > 0:
                result['insert_after_line'] = last_import_line
                result['reason'] = f"Add after existing imports (line {last_import_line})"
            else:
                pass
                # No imports yet, add after docstring/comments
                insert_line = 1
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        insert_line = i
                        break
                result['insert_after_line'] = insert_line
                result['reason'] = f"Add at top of file (line {insert_line})"
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def check_import_scope(
        self,
        filepath: str,
        import_statement: str,
        line_number: int
    ) -> Dict:
        """
        Check if an import is in the correct scope.
        
        Returns whether import should be at module level or local.
        """
        result = {
            'import_statement': import_statement,
            'line_number': line_number,
            'current_scope': None,
            'recommended_scope': 'module',
            'reason': None
        }
        
        full_path = self.project_root / filepath
        if not full_path.exists():
            result['error'] = f"File not found: {filepath}"
            return result
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the scope of the import
            for node in ast.walk(tree):
                if hasattr(node, 'lineno') and node.lineno == line_number:
                    pass
                    # Check if inside a function
                    for parent in ast.walk(tree):
                        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if any(child.lineno == line_number for child in ast.walk(parent)):
                                result['current_scope'] = 'function'
                                result['recommended_scope'] = 'module'
                                result['reason'] = (
                                    "Import inside function should be moved to module level. "
                                    "Imports should be at the top of the file for better performance "
                                    "and to avoid repeated imports on each function call."
                                )
                                return result
                        
                        # Check if inside a try block
                        if isinstance(parent, ast.Try):
                            if any(child.lineno == line_number for child in ast.walk(parent)):
                                result['current_scope'] = 'try_block'
                                result['recommended_scope'] = 'module'
                                result['reason'] = (
                                    "Import inside try block should be moved to module level. "
                                    "Only use try blocks for imports when handling optional dependencies."
                                )
                                return result
            
            result['current_scope'] = 'module'
            result['recommended_scope'] = 'module'
            result['reason'] = "Import is correctly placed at module level"
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def suggest_import_fix(
        self,
        filepath: str,
        error_message: str
    ) -> Dict:
        """
        Suggest how to fix an import-related error.
        
        Analyzes error message and suggests the correct fix.
        """
        result = {
            'error_message': error_message,
            'missing_module': None,
            'suggested_fix': None,
            'import_statement': None
        }
        
        # Extract module name from error
        import re
        
        # Pattern: "cannot access local variable 'yaml'"
        match = re.search(r"cannot access local variable '(\w+)'", error_message)
        if match:
            module_name = match.group(1)
            result['missing_module'] = module_name
            result['suggested_fix'] = f"Add 'import {module_name}' at the top of the file"
            result['import_statement'] = f"import {module_name}"
            return result
        
        # Pattern: "name 'yaml' is not defined"
        match = re.search(r"name '(\w+)' is not defined", error_message)
        if match:
            module_name = match.group(1)
            result['missing_module'] = module_name
            result['suggested_fix'] = f"Add 'import {module_name}' at the top of the file"
            result['import_statement'] = f"import {module_name}"
            return result
        
        # Pattern: "No module named 'yaml'"
        match = re.search(r"No module named '(\w+)'", error_message)
        if match:
            module_name = match.group(1)
            result['missing_module'] = module_name
            result['suggested_fix'] = f"Install module: pip install {module_name}"
            result['import_statement'] = f"import {module_name}"
            return result
        
        return result
    
    def detect_circular_imports(self) -> List[List[str]]:
        """
        Detect circular import dependencies in the project.
        
        Returns:
            List of circular import chains (each chain is a list of module names)
        """
        import_graph = {}
        
        # Build import graph
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                module_name = str(py_file.relative_to(self.project_root)).replace('/', '.').replace('.py', '')
                
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                import_graph[module_name] = imports
                
            except Exception:
                continue
        
        # Find cycles using DFS
        def find_cycles(node, path, visited, cycles):
            if node in path:
                pass
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in import_graph.get(node, []):
                find_cycles(neighbor, path[:], visited, cycles)
        
        cycles = []
        visited = set()
        
        for module in import_graph:
            if module not in visited:
                find_cycles(module, [], visited, cycles)
        
        return cycles
    
    def validate_all_imports(self) -> List[Dict]:
        """
        Validate all imports in the project.
        
        Returns:
            List of invalid imports with details
        """
        invalid_imports = []
        
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            pass
                            # Try to import the module
                            try:
                                __import__(alias.name)
                            except ImportError as e:
                                invalid_imports.append({
                                    'file': str(py_file.relative_to(self.project_root)),
                                    'line': node.lineno,
                                    'module': alias.name,
                                    'error': str(e)
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            try:
                                __import__(node.module)
                            except ImportError as e:
                                invalid_imports.append({
                                    'file': str(py_file.relative_to(self.project_root)),
                                    'line': node.lineno,
                                    'module': node.module,
                                    'error': str(e)
                                })
                
            except Exception:
                continue
        
        return invalid_imports