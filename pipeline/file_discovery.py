"""
File Discovery Utilities

Provides tools for finding similar files, detecting conflicts,
and extracting naming conventions.
"""

from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import re
import ast


class FileDiscovery:
    """Discovers and analyzes files in the project"""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self._cache = {}
    
    def find_similar_files(self, target_file: str, 
                          similarity_threshold: float = 0.6) -> List[Dict]:
        """
        Find files with similar names or functionality.
        
        Args:
            target_file: Proposed filename
            similarity_threshold: Minimum similarity (0.0-1.0)
            
        Returns:
            List of similar files with metadata
        """
        target_name = Path(target_file).stem
        similar = []
        
        for py_file in self.project_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            file_name = py_file.stem
            similarity = SequenceMatcher(None, target_name, file_name).ratio()
            
            if similarity >= similarity_threshold:
                similar.append({
                    'path': str(py_file.relative_to(self.project_dir)),
                    'name': file_name,
                    'similarity': similarity,
                    'size': py_file.stat().st_size,
                    'directory': str(py_file.parent.relative_to(self.project_dir)),
                    'purpose': self._extract_file_purpose(py_file),
                    'classes': self._extract_classes(py_file),
                    'functions': self._extract_functions(py_file)
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
    
    def find_conflicting_files(self) -> List[Dict]:
        """
        Find groups of files that may be duplicates or conflicts.
        
        Returns:
            List of conflict groups
        """
        from collections import defaultdict
        
        groups = defaultdict(list)
        all_files = list(self.project_dir.rglob("*.py"))
        
        # Group by stem similarity
        for i, file1 in enumerate(all_files):
            if file1.name == "__init__.py":
                continue
                
            name1 = file1.stem
            
            for file2 in all_files[i+1:]:
                if file2.name == "__init__.py":
                    continue
                    
                name2 = file2.stem
                similarity = SequenceMatcher(None, name1, name2).ratio()
                
                if similarity > 0.7:
                    group_key = min(name1, name2)
                    groups[group_key].extend([
                        str(file1.relative_to(self.project_dir)),
                        str(file2.relative_to(self.project_dir))
                    ])
        
        # Convert to conflict groups
        conflicts = []
        for pattern, files in groups.items():
            unique_files = list(set(files))
            if len(unique_files) > 1:
                conflicts.append({
                    'pattern': pattern,
                    'files': unique_files,
                    'count': len(unique_files),
                    'severity': self._assess_conflict_severity(unique_files)
                })
        
        return conflicts
    
    def _extract_file_purpose(self, filepath: Path) -> str:
        """Extract purpose from docstring or comments"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            if docstring:
                # Return first line of docstring
                return docstring.split('\n')[0][:100]
        except:
            pass
        return "Unknown"
    
    def _extract_classes(self, filepath: Path) -> List[str]:
        """Extract class names from file"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.ClassDef)]
        except:
            return []
    
    def _extract_functions(self, filepath: Path) -> List[str]:
        """Extract function names from file"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.FunctionDef) 
                   and not node.name.startswith('_')]
        except:
            return []
    
    def _assess_conflict_severity(self, files: List[str]) -> str:
        """Assess how severe a file conflict is"""
        # Check if files are in same directory
        directories = set(Path(f).parent for f in files)
        
        if len(directories) == 1:
            return "high"  # Same directory = likely duplicates
        elif len(directories) == 2:
            return "medium"  # Different directories = may be intentional
        else:
            return "low"  # Many directories = likely different purposes