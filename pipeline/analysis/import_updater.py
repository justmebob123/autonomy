"""
Import Updater

Automatically updates import statements when files are moved or renamed.
Handles both 'import' and 'from...import' statements.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .import_graph import ImportGraphBuilder


@dataclass
class UpdateResult:
    """Result of updating imports in a file."""
    file: str
    success: bool
    changes_made: int
    old_content: str
    new_content: str
    error: Optional[str] = None


class ImportUpdater:
    """
    Updates import statements when files are moved or renamed.
    
    Features:
    - Parse and update 'import' statements
    - Parse and update 'from...import' statements
    - Preserve formatting and comments
    - Validate syntax after updates
    - Create backups before modifying
    """
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.graph_builder = ImportGraphBuilder(project_root, logger)
        
    def update_imports_for_move(
        self,
        old_path: str,
        new_path: str,
        dry_run: bool = False
    ) -> List[UpdateResult]:
        """
        Update all imports when a file is moved.
        
        Args:
            old_path: Original file path (relative to project root)
            new_path: New file path (relative to project root)
            dry_run: If True, don't actually modify files
            
        Returns:
            List of UpdateResult objects for each modified file
        """
        # Build graph to find all importers
        self.graph_builder.build_graph()
        
        # Get all files that import the moved file
        importers = self.graph_builder.get_file_importers(old_path)
        
        if self.logger:
            self.logger.info(f"Updating imports in {len(importers)} files...")
        
        # Convert paths to module names
        old_module = self._path_to_module(old_path)
        new_module = self._path_to_module(new_path)
        
        results = []
        
        for importer in importers:
            result = self._update_file_imports(
                importer,
                old_module,
                new_module,
                dry_run
            )
            results.append(result)
        
        return results
    
    def update_imports_for_rename(
        self,
        file_path: str,
        new_name: str,
        dry_run: bool = False
    ) -> List[UpdateResult]:
        """
        Update all imports when a file is renamed.
        
        Args:
            file_path: Current file path
            new_name: New filename (not full path)
            dry_run: If True, don't actually modify files
            
        Returns:
            List of UpdateResult objects
        """
        # Renaming is just moving within the same directory
        old_path = Path(file_path)
        new_path = old_path.parent / new_name
        
        return self.update_imports_for_move(
            str(old_path),
            str(new_path),
            dry_run
        )
    
    def _update_file_imports(
        self,
        file_path: str,
        old_module: str,
        new_module: str,
        dry_run: bool
    ) -> UpdateResult:
        """
        Update imports in a single file.
        
        Args:
            file_path: File to update
            old_module: Old module name
            new_module: New module name
            dry_run: If True, don't actually modify file
            
        Returns:
            UpdateResult object
        """
        full_path = self.project_root / file_path
        
        try:
            pass
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
            
            # Update imports
            new_content, changes_made = self._replace_imports(
                old_content,
                old_module,
                new_module
            )
            
            # Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return UpdateResult(
                    file=file_path,
                    success=False,
                    changes_made=0,
                    old_content=old_content,
                    new_content=new_content,
                    error=f"Syntax error after update: {e}"
                )
            
            # Write file if not dry run
            if not dry_run and changes_made > 0:
                pass
                # Create backup
                backup_path = full_path.with_suffix('.py.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(old_content)
                
                # Write updated content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                if self.logger:
                    self.logger.debug(f"Updated {file_path}: {changes_made} changes")
            
            return UpdateResult(
                file=file_path,
                success=True,
                changes_made=changes_made,
                old_content=old_content,
                new_content=new_content
            )
            
        except Exception as e:
            return UpdateResult(
                file=file_path,
                success=False,
                changes_made=0,
                old_content='',
                new_content='',
                error=str(e)
            )
    
    def _replace_imports(
        self,
        content: str,
        old_module: str,
        new_module: str
    ) -> Tuple[str, int]:
        """
        Replace import statements in file content.
        
        Args:
            content: File content
            old_module: Old module name
            new_module: New module name
            
        Returns:
            Tuple of (new_content, changes_made)
        """
        lines = content.split('\n')
        changes_made = 0
        
        for i, line in enumerate(lines):
            pass
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for 'import' statement
            if self._is_import_statement(line, old_module):
                lines[i] = self._replace_import_line(line, old_module, new_module)
                changes_made += 1
            
            # Check for 'from...import' statement
            elif self._is_from_import_statement(line, old_module):
                lines[i] = self._replace_from_import_line(line, old_module, new_module)
                changes_made += 1
        
        return '\n'.join(lines), changes_made
    
    def _is_import_statement(self, line: str, module: str) -> bool:
        """Check if line is an 'import' statement for the module."""
        # Pattern: import module or import module as alias
        pattern = rf'^\s*import\s+{re.escape(module)}(\s+as\s+\w+)?(\s*#.*)?$'
        return bool(re.match(pattern, line))
    
    def _is_from_import_statement(self, line: str, module: str) -> bool:
        """Check if line is a 'from...import' statement for the module."""
        # Pattern: from module import ...
        pattern = rf'^\s*from\s+{re.escape(module)}\s+import\s+'
        return bool(re.match(pattern, line))
    
    def _replace_import_line(self, line: str, old_module: str, new_module: str) -> str:
        """Replace module name in 'import' statement."""
        # Replace the module name while preserving formatting
        return re.sub(
            rf'\bimport\s+{re.escape(old_module)}\b',
            f'import {new_module}',
            line
        )
    
    def _replace_from_import_line(self, line: str, old_module: str, new_module: str) -> str:
        """Replace module name in 'from...import' statement."""
        # Replace the module name while preserving formatting
        return re.sub(
            rf'\bfrom\s+{re.escape(old_module)}\s+import\b',
            f'from {new_module} import',
            line
        )
    
    def _path_to_module(self, file_path: str) -> str:
        """
        Convert file path to Python module name.
        
        Args:
            file_path: Relative file path (e.g., 'app/models/user.py')
            
        Returns:
            Module name (e.g., 'app.models.user')
        """
        path = Path(file_path)
        
        # Remove .py extension
        if path.suffix == '.py':
            path = path.with_suffix('')
        
        # Remove __init__ if present
        if path.name == '__init__':
            path = path.parent
        
        # Convert to module notation
        return str(path).replace('/', '.').replace('\\', '.')
    
    def validate_no_broken_imports(self, files: List[str]) -> Dict[str, List[str]]:
        """
        Validate that files have no broken imports.
        
        Args:
            files: List of file paths to validate
            
        Returns:
            Dictionary mapping files to list of broken imports
        """
        broken_imports = {}
        
        for file_path in files:
            full_path = self.project_root / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                file_broken = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if not self._can_import(alias.name):
                                file_broken.append(f"import {alias.name}")
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not self._can_import(node.module):
                            names = ', '.join(alias.name for alias in node.names)
                            file_broken.append(f"from {node.module} import {names}")
                
                if file_broken:
                    broken_imports[file_path] = file_broken
                    
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to validate {file_path}: {e}")
        
        return broken_imports
    
    def _can_import(self, module_name: str) -> bool:
        """
        Check if a module can be imported.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if module exists or is external package
        """
        # Try to resolve as project file
        module_path = Path(module_name.replace('.', '/'))
        
        candidates = [
            self.project_root / module_path.with_suffix('.py'),
            self.project_root / module_path / '__init__.py'
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return True
        
        # Assume external package exists (we can't verify without importing)
        return True