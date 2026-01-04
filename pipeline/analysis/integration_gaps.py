"""
Native Integration Gap Finder

Reimplemented from scripts/analysis/INTEGRATION_GAP_FINDER.py as a native pipeline tool.
Identifies incomplete features, unused classes, and architectural gaps.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging

from pipeline.logging_setup import get_logger


@dataclass
class IntegrationGapResult:
    """Result of integration gap analysis."""
    unused_classes: List[Tuple[str, str, int]] = field(default_factory=list)
    classes_with_unused_methods: Dict[str, List[str]] = field(default_factory=dict)
    imported_but_unused: Dict[str, List[str]] = field(default_factory=dict)
    
    @property
    def total_unused_classes(self) -> int:
        return len(self.unused_classes)
    
    @property
    def total_classes_with_gaps(self) -> int:
        return len(self.classes_with_unused_methods)
    
    @property
    def total_unused_imports(self) -> int:
        return sum(len(imports) for imports in self.imported_but_unused.values())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'unused_classes': [
                {'name': name, 'file': file, 'line': line}
                for name, file, line in self.unused_classes
            ],
            'classes_with_unused_methods': {
                class_name: methods
                for class_name, methods in self.classes_with_unused_methods.items()
            },
            'imported_but_unused': self.imported_but_unused,
            'summary': {
                'total_unused_classes': self.total_unused_classes,
                'total_classes_with_gaps': self.total_classes_with_gaps,
                'total_unused_imports': self.total_unused_imports
            }
        }


class IntegrationGapVisitor(ast.NodeVisitor):
    """AST visitor for finding integration gaps."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.classes_defined: Dict[str, int] = {}
        self.classes_instantiated: Set[str] = set()
        self.methods_defined: Dict[str, List[str]] = defaultdict(list)
        self.methods_called: Dict[str, Set[str]] = defaultdict(set)
        self.imports: Set[str] = set()
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.classes_defined[node.name] = node.lineno
        
        old_class = self.current_class
        self.current_class = node.name
        
        # Collect all methods in this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods_defined[node.name].append(item.name)
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node: ast.Call):
        """Visit function/method call."""
        # Track class instantiation
        if isinstance(node.func, ast.Name):
            # Direct instantiation: ClassName()
            self.classes_instantiated.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method call: obj.method()
            method_name = node.func.attr
            # Track method calls (approximate - would need type inference for accuracy)
            if isinstance(node.func.value, ast.Name):
                # Could be a class method call
                pass
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            name = alias.name.split('.')[-1]  # Get last part
            self.imports.add(name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statement."""
        for alias in node.names:
            self.imports.add(alias.name)


class IntegrationGapFinder:
    """
    Native integration gap finder.
    
    Identifies incomplete features, unused classes, and architectural gaps
    by analyzing class instantiation, method calls, and integration points.
    
    Example:
        finder = IntegrationGapFinder('/project')
        result = finder.analyze()
        
        # Get unused classes
        for name, file, line in result.unused_classes:
            print(f"Unused class: {name} at {file}:{line}")
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize integration gap finder.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Global tracking
        self.all_classes_defined: Dict[str, Tuple[str, int]] = {}
        self.all_classes_instantiated: Set[str] = set()
        self.all_methods_defined: Dict[str, List[str]] = defaultdict(list)
        self.all_methods_called: Dict[str, Set[str]] = defaultdict(set)
        self.all_imports: Dict[str, Set[str]] = defaultdict(set)
    
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
            visitor = IntegrationGapVisitor(relative_path)
            visitor.visit(tree)
            
            # Aggregate results
            for class_name, line in visitor.classes_defined.items():
                self.all_classes_defined[class_name] = (relative_path, line)
            
            self.all_classes_instantiated.update(visitor.classes_instantiated)
            
            for class_name, methods in visitor.methods_defined.items():
                self.all_methods_defined[class_name].extend(methods)
            
            self.all_imports[relative_path].update(visitor.imports)
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Error analyzing {filepath}: {e}")
    
    def get_unused_classes(self) -> List[Tuple[str, str, int]]:
        """Get classes that are defined but never instantiated."""
        from pipeline.analysis.integration_points import is_integration_point
        
        unused = []
        for class_name, (file, line) in self.all_classes_defined.items():
            if class_name not in self.all_classes_instantiated:
                # Skip if this is a known integration point
                if is_integration_point(file, 'class', class_name):
                    self.logger.info(f"Skipping integration point: {class_name} in {file}")
                    continue
                
                # Skip base classes and abstract classes
                if not class_name.startswith('Base') and not class_name.startswith('Abstract'):
                    unused.append((class_name, file, line))
        return sorted(unused)
    
    def get_classes_with_unused_methods(self) -> Dict[str, List[str]]:
        """Get classes where many methods are defined but not called."""
        result = {}
        for class_name, methods in self.all_methods_defined.items():
            if class_name in self.all_classes_instantiated:
                # Class is used, check if methods are called
                called = self.all_methods_called.get(class_name, set())
                unused_methods = [m for m in methods if m not in called and not m.startswith('_')]
                
                # If more than 50% of public methods are unused, flag it
                public_methods = [m for m in methods if not m.startswith('_')]
                if public_methods and len(unused_methods) / len(public_methods) > 0.5:
                    result[class_name] = unused_methods
        
        return result
    
    def get_imported_but_unused_classes(self) -> Dict[str, List[str]]:
        """Get classes that are imported but never used."""
        result = {}
        for file, imports in self.all_imports.items():
            unused = []
            for import_name in imports:
                # Check if imported class is instantiated
                if import_name not in self.all_classes_instantiated:
                    # Check if it's a defined class
                    if import_name in self.all_classes_defined:
                        unused.append(import_name)
            if unused:
                result[file] = sorted(unused)
        return result
    
    def analyze(self, target: Optional[str] = None) -> IntegrationGapResult:
        """
        Analyze integration gaps in Python files.
        
        Args:
            target: Optional specific file or directory (relative to project_dir)
        
        Returns:
            IntegrationGapResult with all findings
        """
        # Reset state
        self.all_classes_defined.clear()
        self.all_classes_instantiated.clear()
        self.all_methods_defined.clear()
        self.all_methods_called.clear()
        self.all_imports.clear()
        
        if target:
            target_path = self.project_dir / target
        else:
            target_path = self.project_dir
        
        if not target_path.exists():
            self.logger.error(f"Target not found: {target_path}")
            return IntegrationGapResult()
        
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
        return IntegrationGapResult(
            unused_classes=self.get_unused_classes(),
            classes_with_unused_methods=self.get_classes_with_unused_methods(),
            imported_but_unused=self.get_imported_but_unused_classes()
        )
    
    def generate_report(self, result: IntegrationGapResult) -> str:
        """
        Generate text report from analysis result.
        
        Args:
            result: Analysis result
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("INTEGRATION GAP ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Unused classes
        lines.append(f"## UNUSED CLASSES ({result.total_unused_classes})")
        lines.append("")
        for class_name, file, line in result.unused_classes:
            lines.append(f"- {class_name} at {file}:{line}")
        lines.append("")
        
        # Classes with many unused methods
        lines.append(f"## CLASSES WITH MANY UNUSED METHODS ({result.total_classes_with_gaps})")
        lines.append("")
        for class_name, methods in sorted(result.classes_with_unused_methods.items()):
            lines.append(f"### {class_name}")
            lines.append(f"  Unused methods ({len(methods)}):")
            for method in methods:
                lines.append(f"    - {method}")
            lines.append("")
        
        # Imported but unused
        lines.append(f"## IMPORTED BUT UNUSED CLASSES ({result.total_unused_imports})")
        lines.append("")
        for file, classes in sorted(result.imported_but_unused.items()):
            if classes:
                lines.append(f"### {file}")
                for class_name in classes:
                    lines.append(f"  - {class_name}")
                lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total unused classes: {result.total_unused_classes}")
        lines.append(f"Total classes with integration gaps: {result.total_classes_with_gaps}")
        lines.append(f"Total imported but unused classes: {result.total_unused_imports}")
        lines.append("")
        
        return "\n".join(lines)