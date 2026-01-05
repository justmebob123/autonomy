"""
Import Impact Analyzer

Analyzes the impact of moving, renaming, or deleting files on imports.
Predicts which files will be affected and provides risk assessment.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum

from .import_graph import ImportGraphBuilder


class RiskLevel(str, Enum):
    """Risk level for file operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ImportChange:
    """Represents a required import change."""
    file: str
    line_number: Optional[int]
    old_import: str
    new_import: str
    import_type: str  # 'import' or 'from'


@dataclass
class ImpactReport:
    """Report of the impact of a file operation."""
    operation: str  # 'move', 'rename', 'delete'
    source_file: str
    target_file: Optional[str]
    risk_level: RiskLevel
    affected_files: List[str] = field(default_factory=list)
    import_changes: List[ImportChange] = field(default_factory=list)
    circular_dependency_risk: bool = False
    test_files_affected: List[str] = field(default_factory=list)
    estimated_changes: int = 0
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ImportImpactAnalyzer:
    """
    Analyzes the impact of file operations on imports.
    
    Features:
    - Predict affected files for move/rename/delete
    - Calculate risk level
    - Generate list of required import changes
    - Detect potential circular dependency issues
    - Identify affected test files
    """
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.graph_builder = ImportGraphBuilder(project_root, logger)
        
    def analyze_move_impact(self, source_path: str, target_path: str) -> ImpactReport:
        """
        Analyze the impact of moving a file.
        
        Args:
            source_path: Current file path (relative to project root)
            target_path: New file path (relative to project root)
            
        Returns:
            ImpactReport with detailed analysis
        """
        # Build graph if not already built
        self.graph_builder.build_graph()
        
        report = ImpactReport(
            operation='move',
            source_file=source_path,
            target_file=target_path,
            risk_level=RiskLevel.LOW  # Will be updated based on analysis
        )
        
        # Check if source file exists in graph
        if source_path not in self.graph_builder.nodes:
            report.warnings.append(f"Source file {source_path} not found in import graph")
            report.risk_level = RiskLevel.LOW
            return report
        
        # Get all files that import this file
        importers = self.graph_builder.get_file_importers(source_path)
        report.affected_files = importers
        
        # Generate import changes for each affected file
        old_module = self._path_to_module(source_path)
        new_module = self._path_to_module(target_path)
        
        for importer in importers:
            change = ImportChange(
                file=importer,
                line_number=None,  # Will be determined during actual update
                old_import=old_module,
                new_import=new_module,
                import_type='unknown'  # Will be determined during actual update
            )
            report.import_changes.append(change)
        
        # Identify test files
        report.test_files_affected = [
            f for f in importers 
            if 'test' in f.lower() or f.startswith('tests/')
        ]
        
        # Calculate risk level
        report.risk_level = self._calculate_risk_level(
            len(importers),
            len(report.test_files_affected),
            source_path,
            target_path
        )
        
        # Check for circular dependency risk
        report.circular_dependency_risk = self._check_circular_risk(
            source_path,
            target_path
        )
        
        # Estimate total changes
        report.estimated_changes = len(report.import_changes)
        
        # Add recommendations
        self._add_recommendations(report)
        
        return report
    
    def analyze_rename_impact(self, file_path: str, new_name: str) -> ImpactReport:
        """
        Analyze the impact of renaming a file.
        
        Args:
            file_path: Current file path
            new_name: New filename (not full path)
            
        Returns:
            ImpactReport with detailed analysis
        """
        # Renaming is just moving within the same directory
        source_path = Path(file_path)
        target_path = source_path.parent / new_name
        
        return self.analyze_move_impact(str(source_path), str(target_path))
    
    def analyze_delete_impact(self, file_path: str) -> ImpactReport:
        """
        Analyze the impact of deleting a file.
        
        Args:
            file_path: File to delete
            
        Returns:
            ImpactReport with detailed analysis
        """
        # Build graph if not already built
        self.graph_builder.build_graph()
        
        report = ImpactReport(
            operation='delete',
            source_file=file_path,
            target_file=None,
            risk_level=RiskLevel.LOW  # Will be updated based on analysis
        )
        
        # Check if file exists in graph
        if file_path not in self.graph_builder.nodes:
            report.warnings.append(f"File {file_path} not found in import graph")
            report.risk_level = RiskLevel.LOW
            return report
        
        # Get all files that import this file
        importers = self.graph_builder.get_file_importers(file_path)
        report.affected_files = importers
        
        # For deletion, all imports will break
        module_name = self._path_to_module(file_path)
        for importer in importers:
            change = ImportChange(
                file=importer,
                line_number=None,
                old_import=module_name,
                new_import='',  # No replacement
                import_type='unknown'
            )
            report.import_changes.append(change)
        
        # Identify test files
        report.test_files_affected = [
            f for f in importers 
            if 'test' in f.lower() or f.startswith('tests/')
        ]
        
        # Deletion is always high risk if anything imports it
        if importers:
            report.risk_level = RiskLevel.HIGH
            report.warnings.append(
                f"Deleting this file will break {len(importers)} files that import it"
            )
        else:
            report.risk_level = RiskLevel.LOW
        
        report.estimated_changes = len(importers)
        
        # Add recommendations
        if importers:
            report.recommendations.append(
                "Consider moving functionality to another file before deleting"
            )
            report.recommendations.append(
                "Update all importing files to remove or replace imports"
            )
        
        return report
    
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
    
    def _calculate_risk_level(
        self,
        num_importers: int,
        num_test_files: int,
        source_path: str,
        target_path: str
    ) -> RiskLevel:
        """
        Calculate risk level for a file operation.
        
        Args:
            num_importers: Number of files that import this file
            num_test_files: Number of test files affected
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            RiskLevel enum value
        """
        # No importers = low risk
        if num_importers == 0:
            return RiskLevel.LOW
        
        # Many importers = higher risk
        if num_importers > 10:
            return RiskLevel.HIGH
        
        if num_importers > 5:
            return RiskLevel.MEDIUM
        
        # Moving to different top-level directory = higher risk
        source_parts = Path(source_path).parts
        target_parts = Path(target_path).parts
        
        if source_parts[0] != target_parts[0]:
            return RiskLevel.MEDIUM
        
        # Test files affected = medium risk
        if num_test_files > 0:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _check_circular_risk(self, source_path: str, target_path: str) -> bool:
        """
        Check if moving a file could create circular dependencies.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if there's a risk of circular dependencies
        """
        # Get existing circular dependencies
        circular_deps = self.graph_builder.get_circular_dependencies()
        
        # Check if source file is involved in any circular dependencies
        for dep in circular_deps:
            if source_path in dep.cycle:
                return True
        
        return False
    
    def _add_recommendations(self, report: ImpactReport):
        """Add recommendations based on the impact analysis."""
        if report.risk_level == RiskLevel.HIGH:
            report.recommendations.append(
                "High risk operation - consider breaking into smaller steps"
            )
            report.recommendations.append(
                "Create backup before proceeding"
            )
            report.recommendations.append(
                "Run tests after making changes"
            )
        
        if report.circular_dependency_risk:
            report.recommendations.append(
                "File is involved in circular dependencies - review carefully"
            )
        
        if report.test_files_affected:
            report.recommendations.append(
                f"{len(report.test_files_affected)} test files affected - "
                "run tests after changes"
            )
        
        if report.estimated_changes > 10:
            report.recommendations.append(
                f"Large number of changes ({report.estimated_changes}) - "
                "consider using automated import update"
            )
    
    def get_import_distance(self, file1: str, file2: str) -> int:
        """
        Calculate the import distance between two files.
        
        Args:
            file1: First file path
            file2: Second file path
            
        Returns:
            Number of hops in the import graph, or -1 if not connected
        """
        self.graph_builder.build_graph()
        
        if file1 not in self.graph_builder.nodes or file2 not in self.graph_builder.nodes:
            return -1
        
        # BFS to find shortest path
        from collections import deque
        
        queue = deque([(file1, 0)])
        visited = {file1}
        
        while queue:
            current, distance = queue.popleft()
            
            if current == file2:
                return distance
            
            # Check imports
            if current in self.graph_builder.nodes:
                for imported_file in self.graph_builder.nodes[current].imports:
                    if imported_file not in visited:
                        visited.add(imported_file)
                        queue.append((imported_file, distance + 1))
        
        return -1  # Not connected