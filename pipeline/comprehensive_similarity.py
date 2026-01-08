"""
Comprehensive File Similarity Analyzer

Analyzes files for similarity based on multiple dimensions:
- Naming similarity (filename, class names, function names)
- Structural similarity (class hierarchy, function signatures)
- Behavioral similarity (call graph, variable usage)
- Semantic similarity (purpose, functionality)
"""

import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from difflib import SequenceMatcher
from collections import defaultdict
import re

from .logging_setup import get_logger


class ComprehensiveSimilarityAnalyzer:
    """
    Deep analysis of file similarities across multiple dimensions.
    
    This analyzer goes beyond simple filename matching to understand:
    - What classes and functions are defined
    - What external dependencies are used
    - What patterns and idioms are employed
    - What architectural role the file plays
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Caches for analysis results
        self._file_metadata = {}
        self._call_graph = defaultdict(set)
        self._class_hierarchy = {}
        self._import_graph = defaultdict(set)
        
    def find_similar_files(self, target_file: str, 
                          similarity_threshold: float = 0.3) -> List[Dict]:
        """
        Find files similar to target across multiple dimensions.
        
        Args:
            target_file: Target filename (can be proposed or existing)
            similarity_threshold: Minimum overall similarity (0.0-1.0)
            
        Returns:
            List of similar files with detailed similarity breakdown
        """
        target_path = self.project_dir / target_file
        target_exists = target_path.exists()
        
        # Extract target metadata
        if target_exists:
            target_meta = self._analyze_file(target_path)
        else:
            # For proposed files, extract what we can from the name
            target_meta = self._infer_metadata_from_name(target_file)
        
        # Analyze all Python files
        similar_files = []
        for py_file in self.project_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            if target_exists and py_file == target_path:
                continue
                
            # Analyze candidate file
            candidate_meta = self._analyze_file(py_file)
            
            # Calculate multi-dimensional similarity
            similarity_scores = self._calculate_similarity(target_meta, candidate_meta)
            overall_similarity = self._compute_overall_similarity(similarity_scores)
            
            if overall_similarity >= similarity_threshold:
                similar_files.append({
                    'path': str(py_file.relative_to(self.project_dir)),
                    'name': py_file.stem,
                    'similarity': overall_similarity,
                    'similarity_breakdown': similarity_scores,
                    'size': py_file.stat().st_size,
                    'directory': str(py_file.parent.relative_to(self.project_dir)),
                    'purpose': candidate_meta.get('purpose', 'Unknown'),
                    'classes': candidate_meta.get('classes', []),
                    'functions': candidate_meta.get('functions', []),
                    'imports': candidate_meta.get('imports', []),
                    'relationships': self._describe_relationships(candidate_meta),
                    'architectural_role': self._infer_architectural_role(candidate_meta)
                })
        
        return sorted(similar_files, key=lambda x: x['similarity'], reverse=True)
    
    def _analyze_file(self, filepath: Path) -> Dict:
        """Extract comprehensive metadata from a file."""
        if str(filepath) in self._file_metadata:
            return self._file_metadata[str(filepath)]
        
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content, filename=str(filepath))
        except Exception as e:
            self.logger.warning(f"Failed to parse {filepath}: {e}")
            return self._get_empty_metadata(filepath)
        
        metadata = {
            'filepath': str(filepath),
            'filename': filepath.stem,
            'purpose': self._extract_purpose(tree),
            'classes': self._extract_classes(tree),
            'functions': self._extract_functions(tree),
            'methods': self._extract_methods(tree),
            'imports': self._extract_imports(tree),
            'decorators': self._extract_decorators(tree),
            'base_classes': self._extract_base_classes(tree),
            'function_signatures': self._extract_function_signatures(tree),
            'called_functions': self._extract_called_functions(tree),
            'variables': self._extract_variables(tree),
            'constants': self._extract_constants(tree),
            'patterns': self._detect_patterns(tree, content),
            'complexity': self._estimate_complexity(tree),
            'lines_of_code': len(content.splitlines())
        }
        
        self._file_metadata[str(filepath)] = metadata
        return metadata
    
    def _infer_metadata_from_name(self, filename: str) -> Dict:
        """Infer metadata from filename for proposed files."""
        stem = Path(filename).stem
        
        # Infer purpose from naming patterns
        purpose = "Unknown"
        if any(x in stem.lower() for x in ['service', 'handler', 'manager']):
            purpose = "Service/Handler component"
        elif any(x in stem.lower() for x in ['model', 'schema', 'entity']):
            purpose = "Data model"
        elif any(x in stem.lower() for x in ['test', 'spec']):
            purpose = "Test file"
        elif any(x in stem.lower() for x in ['util', 'helper', 'tool']):
            purpose = "Utility/Helper"
        elif any(x in stem.lower() for x in ['api', 'endpoint', 'route']):
            purpose = "API endpoint"
        
        return {
            'filepath': filename,
            'filename': stem,
            'purpose': purpose,
            'classes': [],
            'functions': [],
            'methods': [],
            'imports': [],
            'decorators': [],
            'base_classes': [],
            'function_signatures': [],
            'called_functions': [],
            'variables': [],
            'constants': [],
            'patterns': [],
            'complexity': 0,
            'lines_of_code': 0
        }
    
    def _calculate_similarity(self, target: Dict, candidate: Dict) -> Dict[str, float]:
        """Calculate similarity across multiple dimensions."""
        return {
            'name_similarity': self._name_similarity(target, candidate),
            'class_similarity': self._class_similarity(target, candidate),
            'function_similarity': self._function_similarity(target, candidate),
            'import_similarity': self._import_similarity(target, candidate),
            'pattern_similarity': self._pattern_similarity(target, candidate),
            'purpose_similarity': self._purpose_similarity(target, candidate),
            'structural_similarity': self._structural_similarity(target, candidate),
            'behavioral_similarity': self._behavioral_similarity(target, candidate)
        }
    
    def _name_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare filename similarity."""
        return SequenceMatcher(None, target['filename'], candidate['filename']).ratio()
    
    def _class_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare class definitions."""
        target_classes = set(target.get('classes', []))
        candidate_classes = set(candidate.get('classes', []))
        
        if not target_classes and not candidate_classes:
            return 0.0
        if not target_classes or not candidate_classes:
            return 0.0
        
        # Jaccard similarity
        intersection = len(target_classes & candidate_classes)
        union = len(target_classes | candidate_classes)
        return intersection / union if union > 0 else 0.0
    
    def _function_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare function definitions."""
        target_funcs = set(target.get('functions', []))
        candidate_funcs = set(candidate.get('functions', []))
        
        if not target_funcs and not candidate_funcs:
            return 0.0
        if not target_funcs or not candidate_funcs:
            return 0.0
        
        # Check for similar function names (not just exact matches)
        similar_count = 0
        for t_func in target_funcs:
            for c_func in candidate_funcs:
                if SequenceMatcher(None, t_func, c_func).ratio() > 0.7:
                    similar_count += 1
                    break
        
        max_funcs = max(len(target_funcs), len(candidate_funcs))
        return similar_count / max_funcs if max_funcs > 0 else 0.0
    
    def _import_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare import statements."""
        target_imports = set(target.get('imports', []))
        candidate_imports = set(candidate.get('imports', []))
        
        if not target_imports and not candidate_imports:
            return 0.0
        if not target_imports or not candidate_imports:
            return 0.0
        
        intersection = len(target_imports & candidate_imports)
        union = len(target_imports | candidate_imports)
        return intersection / union if union > 0 else 0.0
    
    def _pattern_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare design patterns and idioms."""
        target_patterns = set(target.get('patterns', []))
        candidate_patterns = set(candidate.get('patterns', []))
        
        if not target_patterns and not candidate_patterns:
            return 0.0
        if not target_patterns or not candidate_patterns:
            return 0.0
        
        intersection = len(target_patterns & candidate_patterns)
        union = len(target_patterns | candidate_patterns)
        return intersection / union if union > 0 else 0.0
    
    def _purpose_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare file purposes."""
        target_purpose = target.get('purpose', '').lower()
        candidate_purpose = candidate.get('purpose', '').lower()
        
        if not target_purpose or not candidate_purpose:
            return 0.0
        
        return SequenceMatcher(None, target_purpose, candidate_purpose).ratio()
    
    def _structural_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare structural characteristics."""
        # Compare complexity, size, organization
        target_complexity = target.get('complexity', 0)
        candidate_complexity = candidate.get('complexity', 0)
        
        if target_complexity == 0 and candidate_complexity == 0:
            return 0.0
        
        # Normalize complexity difference to 0-1 scale
        max_complexity = max(target_complexity, candidate_complexity)
        if max_complexity == 0:
            return 0.0
        
        complexity_diff = abs(target_complexity - candidate_complexity)
        return 1.0 - (complexity_diff / max_complexity)
    
    def _behavioral_similarity(self, target: Dict, candidate: Dict) -> float:
        """Compare behavioral characteristics (what functions are called)."""
        target_calls = set(target.get('called_functions', []))
        candidate_calls = set(candidate.get('called_functions', []))
        
        if not target_calls and not candidate_calls:
            return 0.0
        if not target_calls or not candidate_calls:
            return 0.0
        
        intersection = len(target_calls & candidate_calls)
        union = len(target_calls | candidate_calls)
        return intersection / union if union > 0 else 0.0
    
    def _compute_overall_similarity(self, scores: Dict[str, float]) -> float:
        """Compute weighted overall similarity score."""
        weights = {
            'name_similarity': 0.15,
            'class_similarity': 0.20,
            'function_similarity': 0.20,
            'import_similarity': 0.15,
            'pattern_similarity': 0.10,
            'purpose_similarity': 0.10,
            'structural_similarity': 0.05,
            'behavioral_similarity': 0.05
        }
        
        total_score = sum(scores[key] * weights[key] for key in weights)
        return total_score
    
    def _extract_purpose(self, tree: ast.AST) -> str:
        """Extract file purpose from docstring."""
        docstring = ast.get_docstring(tree)
        if docstring:
            return docstring.split('\n')[0][:200]
        return "Unknown"
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names."""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract top-level function names."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only top-level functions (not methods)
                if not any(isinstance(parent, ast.ClassDef) 
                          for parent in ast.walk(tree) 
                          if hasattr(parent, 'body') and node in parent.body):
                    functions.append(node.name)
        return functions
    
    def _extract_methods(self, tree: ast.AST) -> List[str]:
        """Extract method names from classes."""
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(f"{node.name}.{item.name}")
        return methods
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    
    def _extract_decorators(self, tree: ast.AST) -> List[str]:
        """Extract decorator names."""
        decorators = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                        decorators.append(dec.func.id)
        return decorators
    
    def _extract_base_classes(self, tree: ast.AST) -> List[str]:
        """Extract base classes."""
        bases = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
        return bases
    
    def _extract_function_signatures(self, tree: ast.AST) -> List[str]:
        """Extract function signatures."""
        signatures = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                signatures.append(f"{node.name}({', '.join(args)})")
        return signatures
    
    def _extract_called_functions(self, tree: ast.AST) -> List[str]:
        """Extract functions that are called."""
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        return calls
    
    def _extract_variables(self, tree: ast.AST) -> List[str]:
        """Extract variable names."""
        variables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
        return variables
    
    def _extract_constants(self, tree: ast.AST) -> List[str]:
        """Extract constant names (UPPER_CASE variables)."""
        constants = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append(target.id)
        return constants
    
    def _detect_patterns(self, tree: ast.AST, content: str) -> List[str]:
        """Detect design patterns and idioms."""
        patterns = []
        
        # Detect common patterns
        if 'singleton' in content.lower():
            patterns.append('singleton')
        if 'factory' in content.lower():
            patterns.append('factory')
        if '@property' in content:
            patterns.append('property_decorator')
        if 'with ' in content:
            patterns.append('context_manager')
        if '__enter__' in content and '__exit__' in content:
            patterns.append('context_manager_protocol')
        if 'async def' in content:
            patterns.append('async_await')
        if '@dataclass' in content:
            patterns.append('dataclass')
        if 'TypedDict' in content or 'Protocol' in content:
            patterns.append('typing_protocol')
        
        return patterns
    
    def _estimate_complexity(self, tree: ast.AST) -> int:
        """Estimate cyclomatic complexity."""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _describe_relationships(self, metadata: Dict) -> Dict[str, List[str]]:
        """Describe relationships this file has."""
        return {
            'imports_from': metadata.get('imports', [])[:5],
            'defines_classes': metadata.get('classes', [])[:5],
            'defines_functions': metadata.get('functions', [])[:5],
            'uses_patterns': metadata.get('patterns', [])
        }
    
    def _infer_architectural_role(self, metadata: Dict) -> str:
        """Infer the architectural role of this file."""
        filename = metadata.get('filename', '').lower()
        classes = metadata.get('classes', [])
        functions = metadata.get('functions', [])
        imports = metadata.get('imports', [])
        
        # Infer role from various signals
        if 'test' in filename:
            return "Test"
        elif 'model' in filename or any('Model' in c for c in classes):
            return "Data Model"
        elif 'service' in filename or 'handler' in filename:
            return "Service/Handler"
        elif 'api' in filename or 'endpoint' in filename:
            return "API Endpoint"
        elif 'util' in filename or 'helper' in filename:
            return "Utility"
        elif 'manager' in filename:
            return "Manager/Coordinator"
        elif len(classes) > 0 and len(functions) == 0:
            return "Class Definition"
        elif len(functions) > 0 and len(classes) == 0:
            return "Function Library"
        else:
            return "Mixed"
    
    def _get_empty_metadata(self, filepath: Path) -> Dict:
        """Return empty metadata for unparseable files."""
        return {
            'filepath': str(filepath),
            'filename': filepath.stem,
            'purpose': 'Unknown (parse error)',
            'classes': [],
            'functions': [],
            'methods': [],
            'imports': [],
            'decorators': [],
            'base_classes': [],
            'function_signatures': [],
            'called_functions': [],
            'variables': [],
            'constants': [],
            'patterns': [],
            'complexity': 0,
            'lines_of_code': 0
        }