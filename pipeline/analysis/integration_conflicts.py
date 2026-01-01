"""
Integration Conflict Detector

Detects duplicate/parallel implementations, naming inconsistencies,
and integration issues across the codebase.

This tool helps identify when the same functionality has been implemented
multiple times in different locations, which often indicates failed integration
or architectural confusion.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import difflib
import logging

from pipeline.logging_setup import get_logger


@dataclass
class IntegrationConflict:
    """A detected integration conflict."""
    conflict_type: str  # 'duplicate_implementation', 'naming_inconsistency', 'feature_overlap'
    severity: str  # 'high', 'medium', 'low'
    files: List[str]
    description: str
    recommendation: str
    details: Dict = field(default_factory=dict)


@dataclass
class IntegrationConflictResult:
    """Result of integration conflict analysis."""
    conflicts: List[IntegrationConflict] = field(default_factory=list)
    
    @property
    def high_severity_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == 'high')
    
    @property
    def medium_severity_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == 'medium')
    
    @property
    def low_severity_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == 'low')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'conflicts': [
                {
                    'type': c.conflict_type,
                    'severity': c.severity,
                    'files': c.files,
                    'description': c.description,
                    'recommendation': c.recommendation,
                    'details': c.details
                }
                for c in self.conflicts
            ],
            'summary': {
                'total': len(self.conflicts),
                'high': self.high_severity_count,
                'medium': self.medium_severity_count,
                'low': self.low_severity_count
            }
        }


class IntegrationConflictDetector:
    """
    Detects integration conflicts and duplicate implementations.
    
    Example:
        detector = IntegrationConflictDetector('/project', architecture_config)
        result = detector.analyze()
        
        for conflict in result.conflicts:
            print(f"{conflict.severity.upper()}: {conflict.description}")
            print(f"Files: {', '.join(conflict.files)}")
            print(f"Recommendation: {conflict.recommendation}")
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None,
                 architecture_config=None):
        """
        Initialize integration conflict detector.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
            architecture_config: Architecture configuration for intelligent detection
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        self.architecture_config = architecture_config
        
        # Track all classes and functions
        self.classes: Dict[str, List[Tuple[str, int]]] = {}  # class_name -> [(file, line)]
        self.functions: Dict[str, List[Tuple[str, int]]] = {}  # func_name -> [(file, line)]
        self.modules: Dict[str, str] = {}  # file -> module_purpose
    
    def analyze(self, target: Optional[str] = None) -> IntegrationConflictResult:
        """
        Analyze for integration conflicts.
        
        Args:
            target: Optional specific file or directory (relative to project_dir)
        
        Returns:
            IntegrationConflictResult with all findings
        """
        # Reset state
        self.classes.clear()
        self.functions.clear()
        self.modules.clear()
        
        if target:
            target_path = self.project_dir / target
        else:
            target_path = self.project_dir
        
        if not target_path.exists():
            self.logger.error(f"Target not found: {target_path}")
            return IntegrationConflictResult()
        
        # Analyze files
        if target_path.is_file():
            if target_path.suffix == '.py':
                self._analyze_file(target_path)
        else:
            # Analyze directory
            for root, dirs, files in os.walk(target_path):
                # Skip common directories AND backup directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv', 'node_modules', '.autonomy']]
                
                # Skip if we're inside a backup directory
                root_path = Path(root)
                if '.autonomy' in root_path.parts or 'backups' in root_path.parts:
                    continue
                
                for file in files:
                    if file.endswith('.py'):
                        filepath = Path(root) / file
                        self._analyze_file(filepath)
        
        # Detect conflicts
        conflicts = []
        conflicts.extend(self._detect_duplicate_classes())
        conflicts.extend(self._detect_duplicate_functions())
        conflicts.extend(self._detect_naming_conflicts())
        conflicts.extend(self._detect_parallel_implementations())
        
        return IntegrationConflictResult(conflicts=conflicts)
    
    def _analyze_file(self, filepath: Path):
        """Analyze a single Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(filepath))
            
            # Get relative path
            rel_path = str(filepath.relative_to(self.project_dir))
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name not in self.classes:
                        self.classes[node.name] = []
                    self.classes[node.name].append((rel_path, node.lineno))
                
                elif isinstance(node, ast.FunctionDef):
                    if node.name not in self.functions:
                        self.functions[node.name] = []
                    self.functions[node.name].append((rel_path, node.lineno))
            
            # Extract module docstring for purpose detection
            docstring = ast.get_docstring(tree)
            if docstring:
                self.modules[rel_path] = docstring.split('\n')[0]  # First line
        
        except Exception as e:
            self.logger.warning(f"Error analyzing {filepath}: {e}")
    
    def _detect_duplicate_classes(self) -> List[IntegrationConflict]:
        """Detect classes with same name in different files."""
        conflicts = []
        
        for class_name, locations in self.classes.items():
            if len(locations) > 1:
                files = [loc[0] for loc in locations]
                
                # Check if this is expected (e.g., test files)
                is_test_duplicate = any('test' in f.lower() for f in files)
                
                if is_test_duplicate:
                    continue  # Skip test duplicates
                
                # Determine severity based on architecture
                severity = self._determine_conflict_severity(files)
                
                conflicts.append(IntegrationConflict(
                    conflict_type='duplicate_implementation',
                    severity=severity,
                    files=files,
                    description=f"Class '{class_name}' implemented in {len(files)} different files",
                    recommendation=self._generate_class_conflict_recommendation(class_name, files),
                    details={
                        'class_name': class_name,
                        'locations': [f"{f}:{line}" for f, line in locations]
                    }
                ))
        
        return conflicts
    
    def _detect_duplicate_functions(self) -> List[IntegrationConflict]:
        """Detect functions with same name in different files."""
        conflicts = []
        
        for func_name, locations in self.functions.items():
            if len(locations) > 1:
                # Skip common names like __init__, main, etc.
                if func_name.startswith('_') or func_name in ['main', 'run', 'execute']:
                    continue
                
                files = [loc[0] for loc in locations]
                
                # Check if this is expected
                is_test_duplicate = any('test' in f.lower() for f in files)
                
                if is_test_duplicate:
                    continue
                
                severity = self._determine_conflict_severity(files)
                
                conflicts.append(IntegrationConflict(
                    conflict_type='duplicate_implementation',
                    severity=severity,
                    files=files,
                    description=f"Function '{func_name}' implemented in {len(files)} different files",
                    recommendation=self._generate_function_conflict_recommendation(func_name, files),
                    details={
                        'function_name': func_name,
                        'locations': [f"{f}:{line}" for f, line in locations]
                    }
                ))
        
        return conflicts
    
    def _detect_naming_conflicts(self) -> List[IntegrationConflict]:
        """Detect files with similar names that might indicate duplication."""
        conflicts = []
        
        # Get all Python files
        all_files = list(self.modules.keys())
        
        for i, file1 in enumerate(all_files):
            for file2 in all_files[i+1:]:
                # Extract base names
                base1 = Path(file1).stem
                base2 = Path(file2).stem
                
                # Check for similar names
                similarity = difflib.SequenceMatcher(None, base1, base2).ratio()
                
                if similarity > 0.7:  # 70% similar
                    # Check if they're in different directories
                    dir1 = str(Path(file1).parent)
                    dir2 = str(Path(file2).parent)
                    
                    if dir1 != dir2:
                        # This might be a naming conflict
                        severity = self._determine_conflict_severity([file1, file2])
                        
                        conflicts.append(IntegrationConflict(
                            conflict_type='naming_inconsistency',
                            severity=severity,
                            files=[file1, file2],
                            description=f"Similar file names: '{base1}' and '{base2}' in different directories",
                            recommendation=self._generate_naming_conflict_recommendation(file1, file2),
                            details={
                                'similarity': f"{similarity:.1%}",
                                'base_names': [base1, base2],
                                'directories': [dir1, dir2]
                            }
                        ))
        
        return conflicts
    
    def _detect_parallel_implementations(self) -> List[IntegrationConflict]:
        """Detect parallel implementations based on module purposes."""
        conflicts = []
        
        # Group modules by similar purposes
        purpose_groups: Dict[str, List[str]] = {}
        
        for file, purpose in self.modules.items():
            # Normalize purpose
            normalized = purpose.lower().strip()
            
            if normalized not in purpose_groups:
                purpose_groups[normalized] = []
            purpose_groups[normalized].append(file)
        
        # Find groups with multiple files
        for purpose, files in purpose_groups.items():
            if len(files) > 1:
                # Check if this is expected
                is_test_group = any('test' in f.lower() for f in files)
                
                if is_test_group:
                    continue
                
                severity = self._determine_conflict_severity(files)
                
                conflicts.append(IntegrationConflict(
                    conflict_type='feature_overlap',
                    severity=severity,
                    files=files,
                    description=f"{len(files)} modules with similar purpose: '{purpose}'",
                    recommendation=self._generate_overlap_recommendation(purpose, files),
                    details={
                        'purpose': purpose,
                        'file_count': len(files)
                    }
                ))
        
        return conflicts
    
    def _determine_conflict_severity(self, files: List[str]) -> str:
        """Determine conflict severity based on architecture."""
        if not self.architecture_config:
            return 'medium'
        
        # Check if files are in different architectural layers
        layers = set()
        for file in files:
            if self.architecture_config.is_library_module(file):
                layers.add('library')
            elif self.architecture_config.is_application_module(file):
                layers.add('application')
            else:
                layers.add('other')
        
        # Cross-layer conflicts are high severity
        if len(layers) > 1:
            return 'high'
        
        # Same layer conflicts are medium severity
        return 'medium'
    
    def _generate_class_conflict_recommendation(self, class_name: str, files: List[str]) -> str:
        """Generate recommendation for class conflict."""
        if not self.architecture_config:
            return f"Review all implementations of '{class_name}' and merge into single implementation."
        
        # Determine correct location
        library_files = [f for f in files if self.architecture_config.is_library_module(f)]
        app_files = [f for f in files if self.architecture_config.is_application_module(f)]
        
        if library_files and app_files:
            return (f"Move '{class_name}' to library ({library_files[0]}) and "
                   f"update application code ({', '.join(app_files)}) to import from library.")
        elif library_files:
            return f"Consolidate '{class_name}' into {library_files[0]} and update imports."
        else:
            return f"Review all implementations and merge into single file following architecture guidelines."
    
    def _generate_function_conflict_recommendation(self, func_name: str, files: List[str]) -> str:
        """Generate recommendation for function conflict."""
        return (f"Review all implementations of '{func_name}', compare features, "
               f"and merge into single implementation in the most appropriate location.")
    
    def _generate_naming_conflict_recommendation(self, file1: str, file2: str) -> str:
        """Generate recommendation for naming conflict."""
        base1 = Path(file1).stem
        base2 = Path(file2).stem
        
        return (f"Files '{base1}' and '{base2}' have similar names. "
               f"Review both to determine if they represent duplicate functionality. "
               f"If so, merge them. If not, rename one to clarify the distinction.")
    
    def _generate_overlap_recommendation(self, purpose: str, files: List[str]) -> str:
        """Generate recommendation for feature overlap."""
        return (f"Multiple modules claim to handle '{purpose}'. "
               f"Review all {len(files)} implementations, identify the complete feature set, "
               f"and consolidate into a single module following architecture guidelines.")
    
    def generate_report(self, result: IntegrationConflictResult) -> str:
        """
        Generate text report from analysis result.
        
        Args:
            result: Analysis result
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("INTEGRATION CONFLICT DETECTION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        if not result.conflicts:
            lines.append("✓ No integration conflicts detected!")
            lines.append("")
            return "\n".join(lines)
        
        # Group by severity
        high = [c for c in result.conflicts if c.severity == 'high']
        medium = [c for c in result.conflicts if c.severity == 'medium']
        low = [c for c in result.conflicts if c.severity == 'low']
        
        # High severity conflicts
        if high:
            lines.append(f"## HIGH SEVERITY CONFLICTS ({len(high)})")
            lines.append("")
            for conflict in high:
                lines.append(f"### {conflict.conflict_type.upper()}")
                lines.append(f"**Description:** {conflict.description}")
                lines.append(f"**Files:**")
                for file in conflict.files:
                    lines.append(f"  - {file}")
                lines.append(f"**Recommendation:** {conflict.recommendation}")
                lines.append("")
        
        # Medium severity conflicts
        if medium:
            lines.append(f"## MEDIUM SEVERITY CONFLICTS ({len(medium)})")
            lines.append("")
            for conflict in medium:
                lines.append(f"### {conflict.conflict_type.upper()}")
                lines.append(f"**Description:** {conflict.description}")
                lines.append(f"**Files:**")
                for file in conflict.files:
                    lines.append(f"  - {file}")
                lines.append(f"**Recommendation:** {conflict.recommendation}")
                lines.append("")
        
        # Low severity conflicts
        if low:
            lines.append(f"## LOW SEVERITY CONFLICTS ({len(low)})")
            lines.append("")
            for conflict in low:
                lines.append(f"### {conflict.conflict_type.upper()}")
                lines.append(f"**Description:** {conflict.description}")
                lines.append(f"**Files:** {', '.join(conflict.files)}")
                lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total conflicts: {len(result.conflicts)}")
        lines.append(f"High severity: {result.high_severity_count}")
        lines.append(f"Medium severity: {result.medium_severity_count}")
        lines.append(f"Low severity: {result.low_severity_count}")
        lines.append("")
        
        return "\n".join(lines)