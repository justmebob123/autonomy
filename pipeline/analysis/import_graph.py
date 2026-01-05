"""
Import Graph Builder

Builds and maintains a complete import graph for the project.
Tracks import relationships, detects circular dependencies, and finds orphaned files.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ImportNode:
    """Represents a file in the import graph."""
    filepath: str
    imports: Set[str] = field(default_factory=set)  # Files this imports
    imported_by: Set[str] = field(default_factory=set)  # Files that import this
    external_imports: Set[str] = field(default_factory=set)  # External packages
    is_orphaned: bool = False
    is_entry_point: bool = False


@dataclass
class CircularDependency:
    """Represents a circular dependency chain."""
    cycle: List[str]
    severity: str  # 'high', 'medium', 'low'
    
    def __str__(self):
        return " -> ".join(self.cycle + [self.cycle[0]])


class ImportGraphBuilder:
    """
    Builds complete import graph for a Python project.
    
    Features:
    - Parse all Python files
    - Track import relationships
    - Detect circular dependencies
    - Find orphaned files
    - Cache for performance
    """
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.nodes: Dict[str, ImportNode] = {}
        self.circular_dependencies: List[CircularDependency] = []
        self._cache_valid = False
        
    def build_graph(self, force_rebuild: bool = False) -> Dict[str, ImportNode]:
        """
        Build complete import graph for the project.
        
        Args:
            force_rebuild: Force rebuild even if cache is valid
            
        Returns:
            Dictionary mapping file paths to ImportNode objects
        """
        if self._cache_valid and not force_rebuild:
            return self.nodes
        
        self.nodes = {}
        self.circular_dependencies = []
        
        # Find all Python files
        python_files = self._find_python_files()
        
        if self.logger:
            self.logger.info(f"Building import graph for {len(python_files)} Python files...")
        
        # Parse each file and extract imports
        for filepath in python_files:
            self._parse_file(filepath)
        
        # Build reverse relationships (imported_by)
        self._build_reverse_relationships()
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        # Find orphaned files
        self._find_orphaned_files()
        
        self._cache_valid = True
        
        if self.logger:
            self.logger.info(f"Import graph built: {len(self.nodes)} nodes, "
                           f"{len(self.circular_dependencies)} circular dependencies")
        
        return self.nodes
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            pass
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', '.git', '.venv', 'venv', 'env',
                'node_modules', '.pytest_cache', '.mypy_cache',
                'build', 'dist', '*.egg-info'
            }]
            
            for file in files:
                if file.endswith('.py'):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(self.project_root))
                    python_files.append(rel_path)
        
        return python_files
    
    def _parse_file(self, filepath: str):
        """Parse a Python file and extract import information."""
        full_path = self.project_root / filepath
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(full_path))
            
            node = ImportNode(filepath=filepath)
            
            for ast_node in ast.walk(tree):
                if isinstance(ast_node, ast.Import):
                    for alias in ast_node.names:
                        module_path = self._resolve_import(alias.name, filepath)
                        if module_path:
                            node.imports.add(module_path)
                        else:
                            node.external_imports.add(alias.name)
                
                elif isinstance(ast_node, ast.ImportFrom):
                    if ast_node.module:
                        module_path = self._resolve_import(ast_node.module, filepath)
                        if module_path:
                            node.imports.add(module_path)
                        else:
                            node.external_imports.add(ast_node.module)
            
            self.nodes[filepath] = node
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to parse {filepath}: {e}")
    
    def _resolve_import(self, module_name: str, current_file: str) -> Optional[str]:
        """
        Resolve an import to a file path.
        
        Args:
            module_name: Import module name (e.g., 'app.models.user')
            current_file: File doing the import
            
        Returns:
            Relative file path or None if external package
        """
        # Handle relative imports
        if module_name.startswith('.'):
            current_dir = Path(current_file).parent
            # Count leading dots
            level = len(module_name) - len(module_name.lstrip('.'))
            module_name = module_name.lstrip('.')
            
            # Go up directories
            for _ in range(level - 1):
                current_dir = current_dir.parent
            
            if module_name:
                module_path = current_dir / module_name.replace('.', '/')
            else:
                module_path = current_dir
        else:
            pass
            # Absolute import
            module_path = Path(module_name.replace('.', '/'))
        
        # Try to find the file
        candidates = [
            module_path.with_suffix('.py'),
            module_path / '__init__.py'
        ]
        
        for candidate in candidates:
            full_path = self.project_root / candidate
            if full_path.exists():
                return str(candidate)
        
        # Not found - external package
        return None
    
    def _build_reverse_relationships(self):
        """Build reverse import relationships (imported_by)."""
        for filepath, node in self.nodes.items():
            for imported_file in node.imports:
                if imported_file in self.nodes:
                    self.nodes[imported_file].imported_by.add(filepath)
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(filepath: str, path: List[str]) -> List[List[str]]:
            """DFS to find cycles."""
            cycles = []
            
            if filepath in rec_stack:
                pass
                # Found a cycle
                cycle_start = path.index(filepath)
                cycle = path[cycle_start:]
                cycles.append(cycle)
                return cycles
            
            if filepath in visited:
                return cycles
            
            visited.add(filepath)
            rec_stack.add(filepath)
            path.append(filepath)
            
            if filepath in self.nodes:
                for imported_file in self.nodes[filepath].imports:
                    if imported_file in self.nodes:
                        cycles.extend(dfs(imported_file, path[:]))
            
            rec_stack.remove(filepath)
            
            return cycles
        
        # Find all cycles
        all_cycles = []
        for filepath in self.nodes:
            if filepath not in visited:
                cycles = dfs(filepath, [])
                all_cycles.extend(cycles)
        
        # Deduplicate cycles (same cycle can be found from different starting points)
        unique_cycles = []
        seen_cycles = set()
        
        for cycle in all_cycles:
            pass
            # Normalize cycle (start from smallest element)
            normalized = tuple(sorted(cycle))
            if normalized not in seen_cycles:
                seen_cycles.add(normalized)
                
                # Determine severity
                severity = 'high' if len(cycle) == 2 else 'medium' if len(cycle) <= 4 else 'low'
                
                unique_cycles.append(CircularDependency(
                    cycle=cycle,
                    severity=severity
                ))
        
        self.circular_dependencies = unique_cycles
    
    def _find_orphaned_files(self):
        """Find files that are not imported by anyone."""
        # Entry points are files that import others but aren't imported
        # Orphaned files are files that neither import nor are imported
        
        for filepath, node in self.nodes.items():
            pass
            # Check if this file is imported by anyone
            if not node.imported_by:
                pass
                # Not imported by anyone
                if node.imports or node.external_imports:
                    pass
                    # Imports others - likely an entry point
                    node.is_entry_point = True
                else:
                    pass
                    # Doesn't import anything either - orphaned
                    node.is_orphaned = True
    
    def get_file_imports(self, filepath: str) -> List[str]:
        """Get all files imported by a specific file."""
        if filepath not in self.nodes:
            return []
        return list(self.nodes[filepath].imports)
    
    def get_file_importers(self, filepath: str) -> List[str]:
        """Get all files that import a specific file."""
        if filepath not in self.nodes:
            return []
        return list(self.nodes[filepath].imported_by)
    
    def get_import_chain(self, filepath: str, max_depth: int = 3) -> Dict:
        """
        Get the import chain for a file up to a certain depth.
        
        Args:
            filepath: File to analyze
            max_depth: Maximum depth to traverse
            
        Returns:
            Dictionary representing the import tree
        """
        if filepath not in self.nodes:
            return {}
        
        def build_chain(file: str, depth: int, visited: Set[str]) -> Dict:
            if depth >= max_depth or file in visited:
                return {}
            
            visited.add(file)
            
            chain = {
                'file': file,
                'imports': []
            }
            
            if file in self.nodes:
                for imported_file in self.nodes[file].imports:
                    if imported_file in self.nodes:
                        sub_chain = build_chain(imported_file, depth + 1, visited.copy())
                        if sub_chain:
                            chain['imports'].append(sub_chain)
            
            return chain
        
        return build_chain(filepath, 0, set())
    
    def get_circular_dependencies(self) -> List[CircularDependency]:
        """Get all detected circular dependencies."""
        return self.circular_dependencies
    
    def get_orphaned_files(self) -> List[str]:
        """Get all orphaned files."""
        return [filepath for filepath, node in self.nodes.items() if node.is_orphaned]
    
    def get_entry_points(self) -> List[str]:
        """Get all entry point files."""
        return [filepath for filepath, node in self.nodes.items() if node.is_entry_point]
    
    def invalidate_cache(self):
        """Invalidate the cache, forcing a rebuild on next build_graph call."""
        self._cache_valid = False
    
    def to_dict(self) -> Dict:
        """Export graph to dictionary format."""
        return {
            'nodes': {
                filepath: {
                    'imports': list(node.imports),
                    'imported_by': list(node.imported_by),
                    'external_imports': list(node.external_imports),
                    'is_orphaned': node.is_orphaned,
                    'is_entry_point': node.is_entry_point
                }
                for filepath, node in self.nodes.items()
            },
            'circular_dependencies': [
                {
                    'cycle': dep.cycle,
                    'severity': dep.severity
                }
                for dep in self.circular_dependencies
            ],
            'stats': {
                'total_files': len(self.nodes),
                'circular_dependencies': len(self.circular_dependencies),
                'orphaned_files': len(self.get_orphaned_files()),
                'entry_points': len(self.get_entry_points())
            }
        }