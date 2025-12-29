"""
Native Dead Code Detector

Reimplemented from scripts/analysis/DEAD_CODE_DETECTOR.py as a native pipeline tool.
Detects unused functions, methods, and imports with pattern awareness.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging

from ..logging_setup import get_logger


@dataclass
class DeadCodeIssue:
    """A single dead code issue marked for review."""
    name: str
    file: str
    line: int
    issue_type: str  # 'function', 'method', 'import', 'class'
    severity: str  # 'review', 'warning', 'error'
    reason: str  # Why this might be unused
    context: str  # Additional context
    similar_code: List[str] = field(default_factory=list)  # Similar implementations found


@dataclass
class DeadCodeResult:
    """Result of dead code analysis."""
    unused_functions: List[Tuple[str, str, int]] = field(default_factory=list)
    unused_methods: List[Tuple[str, str, int]] = field(default_factory=list)
    unused_imports: Dict[str, List[Tuple[str, int, str]]] = field(default_factory=dict)
    
    # Enhanced: Issues marked for review
    review_issues: List[DeadCodeIssue] = field(default_factory=list)
    
    @property
    def total_unused_functions(self) -> int:
        return len(self.unused_functions)
    
    @property
    def total_unused_methods(self) -> int:
        return len(self.unused_methods)
    
    @property
    def total_unused_imports(self) -> int:
        return sum(len(imports) for imports in self.unused_imports.values())
    
    @property
    def total_review_issues(self) -> int:
        return len(self.review_issues)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'unused_functions': [
                {'name': name, 'file': file, 'line': line}
                for name, file, line in self.unused_functions
            ],
            'unused_methods': [
                {'name': name, 'file': file, 'line': line}
                for name, file, line in self.unused_methods
            ],
            'unused_imports': {
                file: [
                    {'name': name, 'line': line, 'type': import_type}
                    for name, line, import_type in imports
                ]
                for file, imports in self.unused_imports.items()
            },
            'summary': {
                'total_unused_functions': self.total_unused_functions,
                'total_unused_methods': self.total_unused_methods,
                'total_unused_imports': self.total_unused_imports
            }
        }


class DeadCodeVisitor(ast.NodeVisitor):
    """AST visitor for detecting dead code."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions_defined: Dict[str, int] = {}
        self.functions_called: Set[str] = set()
        self.classes_defined: Dict[str, int] = {}
        self.methods_defined: Dict[str, int] = {}
        self.methods_called: Set[str] = set()
        self.imports: List[Tuple[str, int, str]] = []
        self.imports_used: Set[str] = set()
        self.inheritance: Dict[str, str] = {}
        self.current_class: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if self.current_class:
            # Method definition
            method_key = f"{self.current_class}.{node.name}"
            self.methods_defined[method_key] = node.lineno
        else:
            # Function definition
            self.functions_defined[node.name] = node.lineno
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.classes_defined[node.name] = node.lineno
        
        # Track inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritance[node.name] = base.id
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node: ast.Call):
        """Visit function/method call."""
        if isinstance(node.func, ast.Name):
            self.functions_called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.methods_called.add(node.func.attr)
            # Track attribute access for imports
            if isinstance(node.func.value, ast.Name):
                self.imports_used.add(node.func.value.id)
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Visit attribute access."""
        if isinstance(node.value, ast.Name):
            self.imports_used.add(node.value.id)
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.append((name, node.lineno, 'import'))
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.append((name, node.lineno, 'from'))


class DeadCodeDetector:
    """
    Native dead code detector.
    
    Detects unused functions, methods, and imports while being aware of:
    - Template method patterns
    - Inheritance hierarchies
    - Dynamic calls
    - Polymorphic dispatch
    
    Example:
        detector = DeadCodeDetector('/project')
        result = detector.analyze()
        
        # Get unused functions
        for name, file, line in result.unused_functions:
            print(f"Unused: {name} at {file}:{line}")
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None, 
                 architecture_config=None):
        """
        Initialize dead code detector.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
            architecture_config: Optional architecture configuration for intelligent detection
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        self.architecture_config = architecture_config
        
        # Global tracking across all files
        self.all_functions_defined: Dict[str, Tuple[str, int]] = {}
        self.all_functions_called: Set[str] = set()
        self.all_methods_defined: Dict[str, Tuple[str, int]] = {}
        self.all_methods_called: Set[str] = set()
        self.all_imports: Dict[str, List[Tuple[str, int, str]]] = defaultdict(list)
        self.all_imports_used: Dict[str, Set[str]] = defaultdict(set)
        
        # Enhanced: Track similar functionality
        self.function_signatures: Dict[str, List[Tuple[str, str, int]]] = defaultdict(list)  # name -> [(file, name, line)]
    
    def analyze_file(self, filepath: Path):
        """
        Analyze a single Python file.
        
        Args:
            filepath: Path to Python file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            relative_path = str(filepath.relative_to(self.project_dir))
            visitor = DeadCodeVisitor(relative_path)
            visitor.visit(tree)
            
            # Aggregate results
            for func_name, line in visitor.functions_defined.items():
                self.all_functions_defined[func_name] = (relative_path, line)
            
            self.all_functions_called.update(visitor.functions_called)
            
            for method_key, line in visitor.methods_defined.items():
                self.all_methods_defined[method_key] = (relative_path, line)
            
            self.all_methods_called.update(visitor.methods_called)
            
            self.all_imports[relative_path].extend(visitor.imports)
            self.all_imports_used[relative_path].update(visitor.imports_used)
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Error analyzing {filepath}: {e}")
    
    def is_template_method(self, method_name: str, class_name: str) -> bool:
        """Check if method is likely a template method."""
        template_patterns = ['execute', 'run', 'process', 'handle', 'validate']
        return any(pattern in method_name.lower() for pattern in template_patterns)
    
    def get_unused_functions(self) -> List[Tuple[str, str, int]]:
        """Get list of unused functions."""
        unused = []
        for func_name, (file, line) in self.all_functions_defined.items():
            if func_name not in self.all_functions_called:
                # Skip special methods and private functions
                if not func_name.startswith('_'):
                    unused.append((func_name, file, line))
        return sorted(unused)
    
    def get_unused_methods(self) -> List[Tuple[str, str, int]]:
        """Get list of unused methods (excluding template methods)."""
        unused = []
        for method_key, (file, line) in self.all_methods_defined.items():
            class_name, method_name = method_key.split('.')
            
            # Skip if method is called
            if method_name in self.all_methods_called:
                continue
            
            # Skip template methods
            if self.is_template_method(method_name, class_name):
                continue
            
            # Skip special methods
            if method_name.startswith('__'):
                continue
            
            unused.append((method_key, file, line))
        return sorted(unused)
    
    def get_unused_imports(self) -> Dict[str, List[Tuple[str, int, str]]]:
        """Get unused imports per file."""
        unused = {}
        for file, imports in self.all_imports.items():
            file_unused = []
            for import_name, line, import_type in imports:
                if import_name not in self.all_imports_used[file]:
                    file_unused.append((import_name, line, import_type))
            if file_unused:
                unused[file] = sorted(file_unused)
        return unused
    
    def analyze(self, target: Optional[str] = None) -> DeadCodeResult:
        """
        Analyze dead code in Python files.
        
        Args:
            target: Optional specific file or directory (relative to project_dir)
        
        Returns:
            DeadCodeResult with all findings
        """
        # Reset state
        self.all_functions_defined.clear()
        self.all_functions_called.clear()
        self.all_methods_defined.clear()
        self.all_methods_called.clear()
        self.all_imports.clear()
        self.all_imports_used.clear()
        
        if target:
            target_path = self.project_dir / target
        else:
            target_path = self.project_dir
        
        if not target_path.exists():
            self.logger.error(f"Target not found: {target_path}")
            return DeadCodeResult()
        
        # Analyze files
        if target_path.is_file():
            if target_path.suffix == '.py':
                self.analyze_file(target_path)
        else:
            # Analyze directory
            for root, dirs, files in os.walk(target_path):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        filepath = Path(root) / file
                        self.analyze_file(filepath)
        
        # Get results
        result = DeadCodeResult(
            unused_functions=self.get_unused_functions(),
            unused_methods=self.get_unused_methods(),
            unused_imports=self.get_unused_imports()
        )
        
        # Enhanced: Generate review issues with context
        result.review_issues = self._generate_review_issues(result)
        
        return result
    
    def generate_report(self, result: DeadCodeResult) -> str:
        """
        Generate text report from analysis result.
        
        Args:
            result: Analysis result
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DEAD CODE DETECTION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Unused functions
        lines.append(f"## UNUSED FUNCTIONS ({result.total_unused_functions})")
        lines.append("")
        for func_name, file, line in result.unused_functions:
            lines.append(f"- {func_name} at {file}:{line}")
        lines.append("")
        
        # Unused methods
        lines.append(f"## UNUSED METHODS ({result.total_unused_methods})")
        lines.append("")
        for method_key, file, line in result.unused_methods:
            lines.append(f"- {method_key} at {file}:{line}")
        lines.append("")
        
        # Unused imports
        lines.append(f"## UNUSED IMPORTS ({result.total_unused_imports})")
        lines.append("")
        for file, imports in sorted(result.unused_imports.items()):
            if imports:
                lines.append(f"### {file}")
                for import_name, line, import_type in imports:
                    lines.append(f"  - {import_name} at line {line} ({import_type})")
                lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total unused functions: {result.total_unused_functions}")
        lines.append(f"Total unused methods: {result.total_unused_methods}")
        lines.append(f"Total unused imports: {result.total_unused_imports}")
        lines.append(f"Total files with unused imports: {len(result.unused_imports)}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_review_issues(self, result: DeadCodeResult) -> List[DeadCodeIssue]:
        """
        Generate review issues with context instead of marking for deletion.
        
        This method analyzes unused code and provides context about why it might
        be unused, helping developers make informed decisions.
        """
        issues = []
        
        # Process unused functions
        for name, file, line in result.unused_functions:
            # Check if this is in a library directory
            is_library = (self.architecture_config and 
                         self.architecture_config.is_library_module(file))
            
            # Check for similar function names (potential duplicates)
            similar = self._find_similar_functions(name, file)
            
            if is_library:
                reason = "Library function not yet integrated into application"
                severity = "review"
                context = "This is library code meant to be imported. Consider integrating it or documenting its intended use."
            elif similar:
                reason = f"Similar functionality exists in {len(similar)} other file(s)"
                severity = "warning"
                context = "Potential duplicate implementation. Review all versions and merge if appropriate."
            else:
                reason = "Function defined but never called"
                severity = "review"
                context = "Verify if this function is needed. It may be dead code or awaiting integration."
            
            issues.append(DeadCodeIssue(
                name=name,
                file=file,
                line=line,
                issue_type='function',
                severity=severity,
                reason=reason,
                context=context,
                similar_code=similar
            ))
        
        # Process unused methods
        for name, file, line in result.unused_methods:
            is_library = (self.architecture_config and 
                         self.architecture_config.is_library_module(file))
            
            similar = self._find_similar_methods(name, file)
            
            if is_library:
                reason = "Library method not yet used by application"
                severity = "review"
                context = "This is library code. Verify if it's part of a public API or needs integration."
            elif similar:
                reason = f"Similar method exists in {len(similar)} other class(es)"
                severity = "warning"
                context = "Potential duplicate implementation. Consider if these should be unified."
            else:
                reason = "Method defined but never called"
                severity = "review"
                context = "May be part of interface/protocol or dead code. Review class design."
            
            issues.append(DeadCodeIssue(
                name=name,
                file=file,
                line=line,
                issue_type='method',
                severity=severity,
                reason=reason,
                context=context,
                similar_code=similar
            ))
        
        return issues
    
    def _find_similar_functions(self, func_name: str, current_file: str) -> List[str]:
        """Find functions with similar names in other files."""
        similar = []
        
        # Normalize function name for comparison
        normalized = func_name.lower().replace('_', '')
        
        for defined_name, (file, line) in self.all_functions_defined.items():
            if file == current_file:
                continue
            
            defined_normalized = defined_name.lower().replace('_', '')
            
            # Check for exact match or very similar names
            if (defined_normalized == normalized or 
                defined_normalized in normalized or 
                normalized in defined_normalized):
                similar.append(f"{file}:{line} ({defined_name})")
        
        return similar
    
    def _find_similar_methods(self, method_name: str, current_file: str) -> List[str]:
        """Find methods with similar names in other files."""
        similar = []
        
        normalized = method_name.lower().replace('_', '')
        
        for defined_name, (file, line) in self.all_methods_defined.items():
            if file == current_file:
                continue
            
            defined_normalized = defined_name.lower().replace('_', '')
            
            if (defined_normalized == normalized or 
                defined_normalized in normalized or 
                normalized in defined_normalized):
                similar.append(f"{file}:{line} ({defined_name})")
        
        return similar