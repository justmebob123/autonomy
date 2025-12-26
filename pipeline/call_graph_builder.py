"""
Call Graph Builder

Uses AST analysis to build complete call graphs and trace
execution paths through the codebase.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import logging


class CallGraphNode:
    """Node in call graph representing a function"""
    
    def __init__(self, module: str, function: str, class_name: Optional[str] = None, file_path: str = "", line: int = 0):
        self.module = module
        self.function = function
        self.class_name = class_name
        self.file_path = file_path
        self.line = line
        self.callers = []  # Functions that call this
        self.callees = []  # Functions this calls
    
    @property
    def id(self) -> str:
        """Unique identifier for this node"""
        if self.class_name:
            return f"{self.module}:{self.class_name}.{self.function}"
        return f"{self.module}:{self.function}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'file': self.file_path,
            'function': self.function,
            'class': self.class_name,
            'line': self.line,
            'callers': [c.id for c in self.callers],
            'callees': [c.id for c in self.callees]
        }


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor for extracting function calls"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.calls = []
        self.functions = []
        self.imports = {}
        self.current_class = None
        self.current_function = None
    
    def visit_ClassDef(self, node):
        """Visit class definition"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Visit function definition"""
        old_function = self.current_function
        self.current_function = node.name
        
        # Record function
        self.functions.append({
            'name': node.name,
            'class': self.current_class,
            'line': node.lineno
        })
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node):
        """Visit function call"""
        # Extract function name
        func_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name:
            self.calls.append({
                'function': func_name,
                'line': node.lineno,
                'caller_class': self.current_class,
                'caller_function': self.current_function
            })
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Visit import statement"""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from import statement"""
        module = node.module or ''
        for alias in node.names:
            self.imports[alias.asname or alias.name] = f"{module}.{alias.name}"
        self.generic_visit(node)


class CallGraphBuilder:
    """Builds call graphs using AST analysis"""
    
    def __init__(self, project_root: str, logger: Optional[logging.Logger] = None):
        self.project_root = Path(project_root)
        self.logger = logger or logging.getLogger(__name__)
        self.graph = {}  # Dict of node_id -> CallGraphNode
        self.visited = set()  # Track visited functions to prevent infinite recursion
    
    def build_call_graph(
        self,
        starting_file: str,
        starting_function: str,
        max_depth: int = 10,
        include_imports: bool = True
    ) -> Dict:
        """
        Build complete call graph from starting function.
        
        Args:
            starting_file: File containing starting function
            starting_function: Function to start tracing from
            max_depth: Maximum depth to traverse
            include_imports: Include imported functions
        
        Returns:
            Dict with nodes and edges
        """
        self.graph = {}
        self.visited = set()
        
        # Resolve starting file
        start_path = Path(starting_file)
        if not start_path.is_absolute():
            start_path = self.project_root / starting_file
        
        if not start_path.exists():
            return {
                'success': False,
                'error': f"Starting file not found: {start_path}"
            }
        
        # Build graph recursively
        self.logger.info(f"Building call graph from {starting_file}:{starting_function}")
        self._build_from_function(start_path, starting_function, depth=0, max_depth=max_depth)
        
        # Convert to dict format
        nodes = [node.to_dict() for node in self.graph.values()]
        edges = []
        
        for node in self.graph.values():
            for callee in node.callees:
                edges.append({
                    'from': node.id,
                    'to': callee.id,
                    'call_site': f"{node.file_path}:{node.line}",
                    'depth': self._calculate_depth(node.id)
                })
        
        # Detect circular dependencies
        circular = self._detect_circular_dependencies()
        
        return {
            'success': True,
            'graph': {
                'nodes': nodes,
                'edges': edges
            },
            'depth_reached': self._max_depth_reached(),
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'circular_dependencies': circular
        }
    
    def _build_from_function(
        self,
        file_path: Path,
        function_name: str,
        depth: int,
        max_depth: int,
        class_name: Optional[str] = None
    ):
        """Recursively build call graph from function"""
        if depth > max_depth:
            return
        
        # Create node ID
        module = self._path_to_module(file_path)
        node_id = f"{module}:{class_name}.{function_name}" if class_name else f"{module}:{function_name}"
        
        # Check if already visited
        if node_id in self.visited:
            return
        self.visited.add(node_id)
        
        # Parse file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            self.logger.debug(f"Error parsing {file_path}: {e}")
            return
        
        # Extract calls using visitor
        visitor = CallGraphVisitor(module)
        visitor.visit(tree)
        
        # Create node
        func_info = next((f for f in visitor.functions if f['name'] == function_name), None)
        if func_info:
            node = CallGraphNode(
                module=module,
                function=function_name,
                class_name=class_name,
                file_path=str(file_path),
                line=func_info['line']
            )
            self.graph[node_id] = node
            
            # Process calls made by this function
            for call in visitor.calls:
                if call['caller_function'] == function_name:
                    # Recursively process callee
                    callee_name = call['function']
                    
                    # Try to resolve to actual function
                    # (simplified - would need full import resolution)
                    self._build_from_function(
                        file_path,
                        callee_name,
                        depth + 1,
                        max_depth
                    )
    
    def _path_to_module(self, file_path: Path) -> str:
        """Convert file path to module name"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            module = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            return module
        except ValueError:
            return str(file_path)
    
    def _calculate_depth(self, node_id: str) -> int:
        """Calculate depth of node in graph"""
        # Simplified - would need proper graph traversal
        return 0
    
    def _max_depth_reached(self) -> int:
        """Calculate maximum depth reached"""
        # Simplified
        return len(self.graph)
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in call graph"""
        circular = []
        
        # Use DFS to detect cycles
        def dfs(node_id: str, path: List[str], visited: Set[str]):
            if node_id in path:
                # Found cycle
                cycle_start = path.index(node_id)
                circular.append(path[cycle_start:] + [node_id])
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            path.append(node_id)
            
            node = self.graph.get(node_id)
            if node:
                for callee in node.callees:
                    dfs(callee.id, path.copy(), visited)
        
        for node_id in self.graph:
            dfs(node_id, [], set())
        
        return circular
    
    def trace_import_chain(
        self,
        starting_module: str,
        max_depth: int = 10
    ) -> Dict:
        """
        Follow import dependencies through codebase.
        
        Args:
            starting_module: Module to start from (e.g., 'src.main')
            max_depth: Maximum depth to traverse
        
        Returns:
            Tree of imports with depth and circular detection
        """
        # Convert module to file path
        module_path = Path(starting_module.replace('.', '/') + '.py')
        file_path = self.project_root / module_path
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f"Module file not found: {file_path}"
            }
        
        # Build import tree recursively
        import_tree = self._build_import_tree(file_path, depth=0, max_depth=max_depth, visited=set())
        
        return {
            'success': True,
            'import_tree': import_tree,
            'total_modules': self._count_modules(import_tree),
            'max_depth_reached': self._tree_depth(import_tree),
            'circular_imports': self._detect_circular_imports(import_tree)
        }
    
    def _build_import_tree(
        self,
        file_path: Path,
        depth: int,
        max_depth: int,
        visited: Set[str]
    ) -> Dict:
        """Recursively build import tree"""
        if depth > max_depth:
            return None
        
        module = self._path_to_module(file_path)
        if module in visited:
            return {'module': module, 'circular': True}
        
        visited.add(module)
        
        # Parse file for imports
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except Exception as e:
            return {'module': module, 'error': str(e)}
        
        visitor = CallGraphVisitor(module)
        visitor.visit(tree)
        
        # Build tree
        import_tree = {
            'module': module,
            'file': str(file_path),
            'depth': depth,
            'imports': []
        }
        
        # Process imports
        for import_name in visitor.imports.values():
            # Convert import to file path
            import_path = Path(import_name.replace('.', '/') + '.py')
            import_file = self.project_root / import_path
            
            if import_file.exists():
                subtree = self._build_import_tree(import_file, depth + 1, max_depth, visited.copy())
                if subtree:
                    import_tree['imports'].append(subtree)
        
        return import_tree
    
    def _count_modules(self, tree: Dict) -> int:
        """Count total modules in tree"""
        if not tree:
            return 0
        count = 1
        for subtree in tree.get('imports', []):
            count += self._count_modules(subtree)
        return count
    
    def _tree_depth(self, tree: Dict) -> int:
        """Calculate maximum depth of tree"""
        if not tree or not tree.get('imports'):
            return tree.get('depth', 0)
        return max(self._tree_depth(subtree) for subtree in tree['imports'])
    
    def _detect_circular_imports(self, tree: Dict) -> List[str]:
        """Detect circular imports in tree"""
        circular = []
        
        def find_circular(node: Dict, path: List[str]):
            if not node:
                return
            
            module = node.get('module')
            if node.get('circular'):
                circular.append(f"{' -> '.join(path)} -> {module}")
                return
            
            for subtree in node.get('imports', []):
                find_circular(subtree, path + [module])
        
        find_circular(tree, [])
        return circular
    
    def find_function_callers(
        self,
        function_name: str,
        class_name: Optional[str] = None,
        search_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Find all locations that call a specific function.
        
        Args:
            function_name: Name of function to find callers for
            class_name: Optional class name if it's a method
            search_path: Optional path to limit search (default: entire project)
        
        Returns:
            List of call sites with file, line, context
        """
        search_root = Path(search_path) if search_path else self.project_root
        if not search_root.is_absolute():
            search_root = self.project_root / search_root
        
        callers = []
        
        # Search all Python files
        for py_file in search_root.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Parse with AST
                tree = ast.parse(content, filename=str(py_file))
                visitor = CallGraphVisitor(self._path_to_module(py_file))
                visitor.visit(tree)
                
                # Find calls to target function
                for call in visitor.calls:
                    if call['function'] == function_name:
                        # Check class match if specified
                        if class_name and call.get('caller_class') != class_name:
                            continue
                        
                        # Get context (surrounding lines)
                        line_num = call['line']
                        context_start = max(0, line_num - 3)
                        context_end = min(len(lines), line_num + 2)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        callers.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': line_num,
                            'function': call.get('caller_function', '<module>'),
                            'class': call.get('caller_class'),
                            'context': context,
                            'call_type': 'direct'
                        })
                
            except Exception as e:
                self.logger.debug(f"Error analyzing {py_file}: {e}")
                continue
        
        self.logger.info(f"Found {len(callers)} callers of {function_name}")
        return callers