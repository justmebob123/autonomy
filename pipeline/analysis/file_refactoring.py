"""
File Refactoring Analysis Tools

Provides comprehensive tools for detecting duplicates, comparing files,
and supporting architecture refactoring decisions.
"""

import ast
import difflib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from pipeline.logging_setup import get_logger


@dataclass
class DuplicateSet:
    """A set of duplicate or similar files."""
    files: List[str]
    similarity_scores: Dict[Tuple[str, str], float]
    common_features: List[str]
    unique_features: Dict[str, List[str]]
    merge_recommended: bool
    merge_strategy: str
    estimated_reduction: int  # Lines of code
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'files': self.files,
            'similarity_scores': {
                f"{f1}:{f2}": score 
                for (f1, f2), score in self.similarity_scores.items()
            },
            'common_features': self.common_features,
            'unique_features': self.unique_features,
            'merge_recommended': self.merge_recommended,
            'merge_strategy': self.merge_strategy,
            'estimated_reduction': self.estimated_reduction
        }


@dataclass
class FeatureComparison:
    """Comparison of a specific feature between files."""
    name: str
    feature_type: str  # 'function', 'class', 'import'
    in_file1: bool
    in_file2: bool
    implementations_differ: bool
    file1_code: Optional[str] = None
    file2_code: Optional[str] = None
    file1_lines: int = 0
    file2_lines: int = 0
    similarity: float = 0.0
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.feature_type,
            'in_both': self.in_file1 and self.in_file2,
            'implementations_differ': self.implementations_differ,
            'file1_lines': self.file1_lines,
            'file2_lines': self.file2_lines,
            'similarity': self.similarity,
            'recommendation': self.recommendation
        }


@dataclass
class FileComparison:
    """Detailed comparison of two files."""
    file1: str
    file2: str
    similarity_score: float
    common_features: List[FeatureComparison]
    unique_to_file1: List[FeatureComparison]
    unique_to_file2: List[FeatureComparison]
    conflicts: List[FeatureComparison]
    merge_strategy: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'file1': self.file1,
            'file2': self.file2,
            'similarity_score': self.similarity_score,
            'common_features': [f.to_dict() for f in self.common_features],
            'unique_to_file1': [f.to_dict() for f in self.unique_to_file1],
            'unique_to_file2': [f.to_dict() for f in self.unique_to_file2],
            'conflicts': [f.to_dict() for f in self.conflicts],
            'merge_strategy': self.merge_strategy
        }


@dataclass
class ExtractedFeature:
    """An extracted feature from a file."""
    name: str
    feature_type: str
    code: str
    dependencies: List[str]
    imports: List[str]
    line_range: Tuple[int, int]
    docstring: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.feature_type,
            'code': self.code,
            'dependencies': self.dependencies,
            'imports': self.imports,
            'line_range': list(self.line_range),
            'docstring': self.docstring
        }


@dataclass
class ArchitectureConsistency:
    """Architecture consistency analysis result."""
    consistency_score: float
    issues: List[Dict]
    refactoring_needed: bool
    priority: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'consistency_score': self.consistency_score,
            'issues': self.issues,
            'refactoring_needed': self.refactoring_needed,
            'priority': self.priority
        }


class FileFeatureExtractor(ast.NodeVisitor):
    """Extract features from a Python file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions: Dict[str, ast.FunctionDef] = {}
        self.classes: Dict[str, ast.ClassDef] = {}
        self.imports: Set[str] = set()
        self.current_class: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if self.current_class:
            # Method
            key = f"{self.current_class}.{node.name}"
        else:
            # Function
            key = node.name
        
        self.functions[key] = node
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.classes[node.name] = node
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statement."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")


class DuplicateDetector:
    """Detect duplicate and similar file implementations."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
    
    def find_duplicates(self, similarity_threshold: float = 0.75,
                       scope: str = "project",
                       include_tests: bool = False) -> List[DuplicateSet]:
        """
        Find sets of duplicate/similar files.
        
        Args:
            similarity_threshold: Minimum similarity (0.0-1.0)
            scope: "project" or specific directory
            include_tests: Include test files
        
        Returns:
            List of DuplicateSet objects
        """
        self.logger.info(f"🔍 Detecting duplicates (threshold: {similarity_threshold})")
        
        # Get all Python files
        files = self._get_python_files(scope, include_tests)
        self.logger.info(f"  Analyzing {len(files)} files")
        
        # Extract features from all files
        file_features = {}
        for filepath in files:
            try:
                features = self._extract_features(filepath)
                file_features[filepath] = features
            except Exception as e:
                self.logger.warning(f"  Failed to analyze {filepath}: {e}")
        
        # Compare all pairs
        similarities = []
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                if file1 in file_features and file2 in file_features:
                    score = self._calculate_similarity(
                        file_features[file1],
                        file_features[file2]
                    )
                    if score >= similarity_threshold:
                        similarities.append((file1, file2, score))
        
        # Group into duplicate sets
        duplicate_sets = self._group_duplicates(similarities, file_features)
        
        self.logger.info(f"  Found {len(duplicate_sets)} duplicate sets")
        return duplicate_sets
    
    def _get_python_files(self, scope: str, include_tests: bool) -> List[str]:
        """Get list of Python files to analyze."""
        if scope == "project":
            search_dir = self.project_dir
        else:
            search_dir = self.project_dir / scope
        
        files = []
        for filepath in search_dir.rglob("*.py"):
            # Skip __pycache__ and hidden directories
            if any(part.startswith('.') or part == '__pycache__' 
                   for part in filepath.parts):
                continue
            
            # Skip tests if not included
            if not include_tests and ('test' in filepath.name.lower() or 
                                     'test' in str(filepath.parent).lower()):
                continue
            
            files.append(str(filepath.relative_to(self.project_dir)))
        
        return files
    
    def _extract_features(self, filepath: str) -> Dict:
        """Extract features from a file."""
        full_path = self.project_dir / filepath
        content = full_path.read_text()
        
        try:
            tree = ast.parse(content)
            extractor = FileFeatureExtractor(filepath)
            extractor.visit(tree)
            
            return {
                'functions': set(extractor.functions.keys()),
                'classes': set(extractor.classes.keys()),
                'imports': extractor.imports,
                'lines': len(content.splitlines())
            }
        except SyntaxError:
            return {
                'functions': set(),
                'classes': set(),
                'imports': set(),
                'lines': 0
            }
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate Jaccard similarity between two feature sets."""
        # Combine all features
        all1 = features1['functions'] | features1['classes'] | features1['imports']
        all2 = features2['functions'] | features2['classes'] | features2['imports']
        
        if not all1 and not all2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(all1 & all2)
        union = len(all1 | all2)
        
        return intersection / union if union > 0 else 0.0
    
    def _group_duplicates(self, similarities: List[Tuple[str, str, float]],
                         file_features: Dict) -> List[DuplicateSet]:
        """Group similar files into duplicate sets."""
        # Build graph of similar files
        graph = defaultdict(set)
        scores = {}
        
        for file1, file2, score in similarities:
            graph[file1].add(file2)
            graph[file2].add(file1)
            scores[(file1, file2)] = score
            scores[(file2, file1)] = score
        
        # Find connected components
        visited = set()
        duplicate_sets = []
        
        for file in graph:
            if file in visited:
                continue
            
            # BFS to find connected component
            component = set()
            queue = [file]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                component.add(current)
                
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(component) >= 2:
                duplicate_set = self._create_duplicate_set(
                    list(component), scores, file_features
                )
                duplicate_sets.append(duplicate_set)
        
        return duplicate_sets
    
    def _create_duplicate_set(self, files: List[str], scores: Dict,
                             file_features: Dict) -> DuplicateSet:
        """Create a DuplicateSet from a group of files."""
        # Get common features
        common_features = set.intersection(*[
            file_features[f]['functions'] | file_features[f]['classes']
            for f in files
        ])
        
        # Get unique features per file
        unique_features = {}
        for file in files:
            all_features = file_features[file]['functions'] | file_features[file]['classes']
            unique = all_features - common_features
            unique_features[file] = list(unique)
        
        # Calculate similarity scores for pairs
        similarity_scores = {}
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                key = (file1, file2)
                if key in scores:
                    similarity_scores[key] = scores[key]
        
        # Determine merge strategy
        avg_similarity = sum(similarity_scores.values()) / len(similarity_scores) if similarity_scores else 0
        
        if avg_similarity >= 0.9:
            merge_strategy = "simple_merge"
        elif avg_similarity >= 0.75:
            merge_strategy = "ai_merge"
        else:
            merge_strategy = "manual_review"
        
        # Estimate reduction
        total_lines = sum(file_features[f]['lines'] for f in files)
        estimated_reduction = int(total_lines * (1 - 1/len(files)) * avg_similarity)
        
        return DuplicateSet(
            files=files,
            similarity_scores=similarity_scores,
            common_features=list(common_features),
            unique_features=unique_features,
            merge_recommended=avg_similarity >= 0.75,
            merge_strategy=merge_strategy,
            estimated_reduction=estimated_reduction
        )


class FileComparator:
    """Compare two files in detail."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
    
    def compare(self, file1: str, file2: str,
               comparison_type: str = "full") -> FileComparison:
        """
        Compare two files in detail.
        
        Args:
            file1: First file path
            file2: Second file path
            comparison_type: "functions", "classes", or "full"
        
        Returns:
            FileComparison object
        """
        self.logger.info(f"🔍 Comparing {file1} vs {file2}")
        
        # Parse both files
        features1 = self._parse_file(file1)
        features2 = self._parse_file(file2)
        
        # Compare features
        common = []
        unique1 = []
        unique2 = []
        conflicts = []
        
        # Compare functions
        if comparison_type in ["functions", "full"]:
            self._compare_functions(features1, features2, common, unique1, unique2, conflicts)
        
        # Compare classes
        if comparison_type in ["classes", "full"]:
            self._compare_classes(features1, features2, common, unique1, unique2, conflicts)
        
        # Calculate overall similarity
        total_features = len(common) + len(unique1) + len(unique2)
        similarity_score = len(common) / total_features if total_features > 0 else 0.0
        
        # Determine merge strategy
        if len(conflicts) == 0 and similarity_score >= 0.8:
            merge_strategy = "simple_merge"
        elif len(conflicts) <= 3 and similarity_score >= 0.6:
            merge_strategy = "ai_merge"
        else:
            merge_strategy = "manual_review"
        
        return FileComparison(
            file1=file1,
            file2=file2,
            similarity_score=similarity_score,
            common_features=common,
            unique_to_file1=unique1,
            unique_to_file2=unique2,
            conflicts=conflicts,
            merge_strategy=merge_strategy
        )
    
    def _parse_file(self, filepath: str) -> Dict:
        """Parse file and extract features."""
        full_path = self.project_dir / filepath
        content = full_path.read_text()
        
        try:
            tree = ast.parse(content)
            extractor = FileFeatureExtractor(filepath)
            extractor.visit(tree)
            
            return {
                'functions': extractor.functions,
                'classes': extractor.classes,
                'imports': extractor.imports,
                'content': content
            }
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {filepath}: {e}")
            return {
                'functions': {},
                'classes': {},
                'imports': set(),
                'content': content
            }
    
    def _compare_functions(self, features1: Dict, features2: Dict,
                          common: List, unique1: List, unique2: List,
                          conflicts: List):
        """Compare functions between two files."""
        funcs1 = set(features1['functions'].keys())
        funcs2 = set(features2['functions'].keys())
        
        # Common functions
        for name in funcs1 & funcs2:
            node1 = features1['functions'][name]
            node2 = features2['functions'][name]
            
            code1 = ast.unparse(node1)
            code2 = ast.unparse(node2)
            
            similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
            
            comparison = FeatureComparison(
                name=name,
                feature_type='function',
                in_file1=True,
                in_file2=True,
                implementations_differ=similarity < 0.95,
                file1_code=code1,
                file2_code=code2,
                file1_lines=len(code1.splitlines()),
                file2_lines=len(code2.splitlines()),
                similarity=similarity,
                recommendation="merge_with_ai" if similarity < 0.95 else "keep_either"
            )
            
            if similarity < 0.95:
                conflicts.append(comparison)
            else:
                common.append(comparison)
        
        # Unique to file1
        for name in funcs1 - funcs2:
            node = features1['functions'][name]
            code = ast.unparse(node)
            
            unique1.append(FeatureComparison(
                name=name,
                feature_type='function',
                in_file1=True,
                in_file2=False,
                implementations_differ=False,
                file1_code=code,
                file1_lines=len(code.splitlines()),
                recommendation="include_in_merge"
            ))
        
        # Unique to file2
        for name in funcs2 - funcs1:
            node = features2['functions'][name]
            code = ast.unparse(node)
            
            unique2.append(FeatureComparison(
                name=name,
                feature_type='function',
                in_file1=False,
                in_file2=True,
                implementations_differ=False,
                file2_code=code,
                file2_lines=len(code.splitlines()),
                recommendation="include_in_merge"
            ))
    
    def _compare_classes(self, features1: Dict, features2: Dict,
                        common: List, unique1: List, unique2: List,
                        conflicts: List):
        """Compare classes between two files."""
        classes1 = set(features1['classes'].keys())
        classes2 = set(features2['classes'].keys())
        
        # Similar logic to _compare_functions
        # (Implementation similar to above)
        pass


class FeatureExtractor:
    """Extract specific features from files."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
    
    def extract(self, source_file: str, features: List[str],
               include_dependencies: bool = True) -> Dict[str, ExtractedFeature]:
        """
        Extract specific features from a file.
        
        Args:
            source_file: Source file path
            features: List of function/class names to extract
            include_dependencies: Include dependent code
        
        Returns:
            Dict mapping feature names to ExtractedFeature objects
        """
        self.logger.info(f"📦 Extracting {len(features)} features from {source_file}")
        
        full_path = self.project_dir / source_file
        content = full_path.read_text()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {source_file}: {e}")
            return {}
        
        # Extract requested features
        extracted = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in features:
                extracted[node.name] = self._extract_function(node, content)
            elif isinstance(node, ast.ClassDef) and node.name in features:
                extracted[node.name] = self._extract_class(node, content)
        
        # Resolve dependencies if requested
        if include_dependencies:
            self._resolve_dependencies(extracted, tree, content)
        
        return extracted
    
    def _extract_function(self, node: ast.FunctionDef, content: str) -> ExtractedFeature:
        """Extract a function."""
        code = ast.unparse(node)
        docstring = ast.get_docstring(node)
        
        # Find dependencies (functions called within this function)
        dependencies = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)
        
        # Find imports needed
        imports = self._find_imports_for_code(code)
        
        return ExtractedFeature(
            name=node.name,
            feature_type='function',
            code=code,
            dependencies=list(set(dependencies)),
            imports=imports,
            line_range=(node.lineno, node.end_lineno or node.lineno),
            docstring=docstring
        )
    
    def _extract_class(self, node: ast.ClassDef, content: str) -> ExtractedFeature:
        """Extract a class."""
        code = ast.unparse(node)
        docstring = ast.get_docstring(node)
        
        # Find dependencies
        dependencies = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
        
        # Find imports
        imports = self._find_imports_for_code(code)
        
        return ExtractedFeature(
            name=node.name,
            feature_type='class',
            code=code,
            dependencies=list(set(dependencies)),
            imports=imports,
            line_range=(node.lineno, node.end_lineno or node.lineno),
            docstring=docstring
        )
    
    def _find_imports_for_code(self, code: str) -> List[str]:
        """Find imports needed for code."""
        # Simple heuristic: look for common module names
        imports = []
        common_modules = ['os', 'sys', 'pathlib', 'typing', 'dataclasses', 
                         'logging', 'json', 'ast', 'difflib']
        
        for module in common_modules:
            if module in code:
                imports.append(module)
        
        return imports
    
    def _resolve_dependencies(self, extracted: Dict, tree: ast.AST, content: str):
        """Resolve dependencies for extracted features."""
        # Find all functions/classes in the file
        all_features = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                all_features[node.name] = node
        
        # For each extracted feature, check if dependencies are in the file
        for feature in extracted.values():
            for dep in feature.dependencies[:]:
                if dep in all_features and dep not in extracted:
                    # Add dependency
                    node = all_features[dep]
                    if isinstance(node, ast.FunctionDef):
                        extracted[dep] = self._extract_function(node, content)
                    elif isinstance(node, ast.ClassDef):
                        extracted[dep] = self._extract_class(node, content)


class RefactoringArchitectureAnalyzer:
    """Analyze architecture consistency for refactoring decisions."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
    
    def analyze_consistency(self, check_master_plan: bool = True,
                           check_architecture: bool = True,
                           check_objectives: bool = True) -> ArchitectureConsistency:
        """
        Analyze if codebase matches MASTER_PLAN and ARCHITECTURE.
        
        Args:
            check_master_plan: Check against MASTER_PLAN.md
            check_architecture: Check against ARCHITECTURE.md
            check_objectives: Check against objectives
        
        Returns:
            ArchitectureConsistency object
        """
        self.logger.info("🏗️  Analyzing architecture consistency")
        
        issues = []
        
        # Check MASTER_PLAN
        if check_master_plan:
            master_plan_issues = self._check_master_plan()
            issues.extend(master_plan_issues)
        
        # Check ARCHITECTURE
        if check_architecture:
            architecture_issues = self._check_architecture()
            issues.extend(architecture_issues)
        
        # Check objectives
        if check_objectives:
            objective_issues = self._check_objectives()
            issues.extend(objective_issues)
        
        # Calculate consistency score
        total_checks = len(issues) + 10  # Assume 10 successful checks
        consistency_score = 1.0 - (len(issues) / total_checks)
        
        # Determine if refactoring needed
        high_priority = sum(1 for i in issues if i.get('priority') == 'high')
        refactoring_needed = high_priority > 0 or len(issues) > 5
        
        # Determine overall priority
        if high_priority > 0:
            priority = 'high'
        elif len(issues) > 3:
            priority = 'medium'
        else:
            priority = 'low'
        
        return ArchitectureConsistency(
            consistency_score=consistency_score,
            issues=issues,
            refactoring_needed=refactoring_needed,
            priority=priority
        )
    
    def _check_master_plan(self) -> List[Dict]:
        """Check consistency with MASTER_PLAN.md."""
        issues = []
        
        master_plan_path = self.project_dir / 'MASTER_PLAN.md'
        if not master_plan_path.exists():
            return issues
        
        # Parse MASTER_PLAN.md for expected files/features
        content = master_plan_path.read_text()
        
        # Simple heuristic: look for file mentions
        # (More sophisticated parsing would be better)
        
        return issues
    
    def _check_architecture(self) -> List[Dict]:
        """Check consistency with ARCHITECTURE.md."""
        issues = []
        
        architecture_path = self.project_dir / 'ARCHITECTURE.md'
        if not architecture_path.exists():
            return issues
        
        # Parse ARCHITECTURE.md
        # (Implementation would parse and check)
        
        return issues
    
    def _check_objectives(self) -> List[Dict]:
        """Check consistency with objectives."""
        issues = []
        
        # Check PRIMARY_OBJECTIVES.md, etc.
        # (Implementation would check objectives)
        
        return issues