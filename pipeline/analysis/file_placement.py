"""
File Placement Analyzer

Analyzes files to determine if they are in the correct location
according to architectural conventions.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..context.architectural import ArchitecturalContextProvider, ValidationResult


@dataclass
class MisplacedFile:
    """Information about a misplaced file."""
    file: str
    current_location: str
    suggested_location: str
    reason: str
    confidence: float
    import_impact: Dict


class FilePlacementAnalyzer:
    """
    Analyzes file placements and finds misplaced files.
    
    Features:
    - Find files in wrong locations
    - Suggest correct locations
    - Analyze architectural violations
    - Estimate impact of moves
    """
    
    def __init__(self, project_root: str, logger=None, arch_context=None):
        self.project_root = Path(project_root)
        self.logger = logger
        
        # Use provided architectural context or create new one
        if arch_context:
            self.arch_context = arch_context
        else:
            self.arch_context = ArchitecturalContextProvider(project_root, logger)
    
    def find_misplaced_files(
        self,
        min_confidence: float = 0.6,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[MisplacedFile]:
        """
        Find all misplaced files in the project.
        
        Args:
            min_confidence: Minimum confidence to consider a file misplaced
            exclude_patterns: Patterns to exclude (e.g., ['test_*', '__pycache__'])
            
        Returns:
            List of MisplacedFile objects
        """
        if exclude_patterns is None:
            exclude_patterns = [
                '__pycache__',
                '.git',
                '.venv',
                'venv',
                'env',
                '*.pyc',
                '.pytest_cache',
                '.mypy_cache',
            ]
        
        misplaced_files = []
        
        # Find all Python files
        for py_file in self._find_python_files(exclude_patterns):
            # Validate location
            validation = self.arch_context.validate_file_location(py_file)
            
            # Check if misplaced with sufficient confidence
            if not validation.valid and validation.confidence >= min_confidence:
                misplaced = MisplacedFile(
                    file=py_file,
                    current_location=str(Path(py_file).parent),
                    suggested_location=str(Path(validation.suggested_location).parent) if validation.suggested_location else '',
                    reason=validation.reason,
                    confidence=validation.confidence,
                    import_impact={}  # Will be filled by caller if needed
                )
                misplaced_files.append(misplaced)
        
        if self.logger:
            self.logger.info(f"Found {len(misplaced_files)} misplaced files")
        
        return misplaced_files
    
    def analyze_file_placement(self, file_path: str) -> ValidationResult:
        """
        Analyze a specific file's placement.
        
        Args:
            file_path: File to analyze
            
        Returns:
            ValidationResult object
        """
        return self.arch_context.validate_file_location(file_path)
    
    def suggest_location(self, file_path: str) -> Optional[str]:
        """
        Suggest optimal location for a file.
        
        Args:
            file_path: File to analyze
            
        Returns:
            Suggested file path or None
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_name = Path(file_path).name
            suggested_path, confidence = self.arch_context.suggest_file_location(
                content,
                file_name
            )
            
            return suggested_path if confidence >= 0.5 else None
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to suggest location for {file_path}: {e}")
            return None
    
    def _find_python_files(self, exclude_patterns: List[str]) -> List[str]:
        """Find all Python files, excluding specified patterns."""
        python_files = []
        
        for root, dirs, files in self.project_root.rglob('*.py'):
            # Get relative path
            try:
                rel_path = root.relative_to(self.project_root)
            except ValueError:
                continue
            
            # Check exclusions
            if self._should_exclude(str(rel_path), exclude_patterns):
                continue
            
            python_files.append(str(rel_path))
        
        return python_files
    
    def _should_exclude(self, path: str, patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns."""
        for pattern in patterns:
            if pattern in path:
                return True
            
            # Handle wildcard patterns
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(path, pattern):
                    return True
        
        return False