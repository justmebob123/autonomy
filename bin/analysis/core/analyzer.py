"""
Deep Code Analyzer - Main orchestrator for comprehensive code analysis.

This is the primary entry point for performing depth-61 recursive analysis.
It coordinates all analysis modules and produces comprehensive reports.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .complexity import ComplexityAnalyzer
from .dataflow import DataFlowAnalyzer
from .integration import IntegrationAnalyzer
from .patterns import PatternDetector
from .runtime import RuntimeAnalyzer
from ..detectors.bugs import BugDetector
from ..detectors.antipatterns import AntiPatternDetector
from ..detectors.deadcode import DeadCodeDetector
from ..detectors.parallel import ParallelImplementationDetector


@dataclass
class AnalysisResult:
    """Complete analysis result for a file."""
    filepath: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Basic metrics
    lines: int = 0
    classes: int = 0
    functions: int = 0
    
    # Complexity analysis
    complexity: Dict[str, Any] = field(default_factory=dict)
    
    # Data flow analysis
    dataflow: Dict[str, Any] = field(default_factory=dict)
    
    # Integration analysis
    integration: Dict[str, Any] = field(default_factory=dict)
    
    # Pattern detection
    patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime analysis
    runtime: Dict[str, Any] = field(default_factory=dict)
    
    # Bug detection
    bugs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Anti-patterns
    antipatterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Dead code
    deadcode: Dict[str, Any] = field(default_factory=dict)
    
    # Parallel implementations
    parallel: List[Dict[str, Any]] = field(default_factory=list)
    
    # Overall assessment
    severity: str = "UNKNOWN"  # EXCELLENT, GOOD, ACCEPTABLE, HIGH, CRITICAL
    issues_count: int = 0
    recommendations: List[str] = field(default_factory=list)


class DeepCodeAnalyzer:
    """
    Main orchestrator for comprehensive code analysis.
    
    Performs depth-61 recursive analysis including:
    - Complexity analysis
    - Data flow analysis
    - Integration analysis
    - Pattern detection
    - Runtime behavior analysis
    - Bug detection
    - Anti-pattern detection
    - Dead code detection
    - Parallel implementation detection
    
    Example:
        analyzer = DeepCodeAnalyzer('path/to/file.py')
        result = analyzer.analyze()
        print(result.severity)
        print(result.bugs)
    """
    
    def __init__(self, filepath: str, project_root: Optional[str] = None):
        """
        Initialize analyzer.
        
        Args:
            filepath: Path to Python file to analyze
            project_root: Optional project root for cross-file analysis
        """
        self.filepath = Path(filepath)
        self.project_root = Path(project_root) if project_root else self.filepath.parent
        
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Read file content
        self.content = self.filepath.read_text()
        
        # Parse AST
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {filepath}: {e}")
        
        # Initialize analyzers
        self.complexity_analyzer = ComplexityAnalyzer(self.tree, self.content)
        self.dataflow_analyzer = DataFlowAnalyzer(self.tree, self.content)
        self.integration_analyzer = IntegrationAnalyzer(
            self.tree, self.content, str(self.filepath), str(self.project_root)
        )
        self.pattern_detector = PatternDetector(self.tree, self.content)
        self.runtime_analyzer = RuntimeAnalyzer(self.tree, self.content)
        
        # Initialize detectors
        self.bug_detector = BugDetector(self.tree, self.content)
        self.antipattern_detector = AntiPatternDetector(self.tree, self.content)
        self.deadcode_detector = DeadCodeDetector(self.tree, self.content)
        self.parallel_detector = ParallelImplementationDetector(
            self.tree, self.content, str(self.project_root)
        )
    
    def analyze(self) -> AnalysisResult:
        """
        Perform comprehensive analysis.
        
        Returns:
            AnalysisResult with all analysis data
        """
        result = AnalysisResult(filepath=str(self.filepath))
        
        # Basic metrics
        result.lines = len(self.content.split('\n'))
        result.classes = len([n for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)])
        result.functions = len([n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)])
        
        # Run all analyzers
        result.complexity = self.complexity_analyzer.analyze()
        result.dataflow = self.dataflow_analyzer.analyze()
        result.integration = self.integration_analyzer.analyze()
        result.patterns = self.pattern_detector.analyze()
        result.runtime = self.runtime_analyzer.analyze()
        
        # Run all detectors
        result.bugs = self.bug_detector.detect()
        result.antipatterns = self.antipattern_detector.detect()
        result.deadcode = self.deadcode_detector.detect()
        result.parallel = self.parallel_detector.detect()
        
        # Calculate overall assessment
        result.issues_count = (
            len(result.bugs) +
            len(result.antipatterns) +
            len(result.deadcode.get('unused_functions', [])) +
            len(result.parallel)
        )
        
        # Determine severity
        critical_bugs = [b for b in result.bugs if b.get('severity') == 'CRITICAL']
        high_bugs = [b for b in result.bugs if b.get('severity') == 'HIGH']
        
        if critical_bugs:
            result.severity = "CRITICAL"
        elif high_bugs or result.complexity.get('max_complexity', 0) > 50:
            result.severity = "HIGH"
        elif result.complexity.get('max_complexity', 0) > 30:
            result.severity = "ACCEPTABLE"
        elif result.complexity.get('average_complexity', 0) < 10:
            result.severity = "EXCELLENT"
        else:
            result.severity = "GOOD"
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _generate_recommendations(self, result: AnalysisResult) -> List[str]:
        """Generate prioritized recommendations based on analysis."""
        recommendations = []
        
        # Critical bugs
        critical_bugs = [b for b in result.bugs if b.get('severity') == 'CRITICAL']
        if critical_bugs:
            recommendations.append(
                f"🔴 CRITICAL: Fix {len(critical_bugs)} critical bugs immediately"
            )
        
        # High complexity
        if result.complexity.get('max_complexity', 0) > 50:
            recommendations.append(
                f"🔴 CRITICAL: Refactor functions with complexity > 50 "
                f"(found {len([f for f in result.complexity.get('functions', []) if f['complexity'] > 50])})"
            )
        
        # Dead code
        unused_funcs = len(result.deadcode.get('unused_functions', []))
        if unused_funcs > 0:
            recommendations.append(
                f"⚠️ MEDIUM: Remove {unused_funcs} unused functions"
            )
        
        # Parallel implementations
        if result.parallel:
            recommendations.append(
                f"⚠️ MEDIUM: Consolidate {len(result.parallel)} parallel implementations"
            )
        
        # Anti-patterns
        if result.antipatterns:
            recommendations.append(
                f"⚠️ MEDIUM: Address {len(result.antipatterns)} anti-patterns"
            )
        
        # Integration issues
        integration_issues = result.integration.get('issues', [])
        if integration_issues:
            recommendations.append(
                f"⚠️ MEDIUM: Fix {len(integration_issues)} integration issues"
            )
        
        # Data flow issues
        dataflow_issues = result.dataflow.get('issues', [])
        if dataflow_issues:
            recommendations.append(
                f"⚠️ LOW: Address {len(dataflow_issues)} data flow issues"
            )
        
        return recommendations
    
    def analyze_directory(self, directory: str, pattern: str = "*.py") -> List[AnalysisResult]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze
            pattern: File pattern to match (default: *.py)
            
        Returns:
            List of AnalysisResult for each file
        """
        results = []
        dir_path = Path(directory)
        
        for filepath in dir_path.rglob(pattern):
            if filepath.is_file():
                try:
                    analyzer = DeepCodeAnalyzer(str(filepath), str(self.project_root))
                    result = analyzer.analyze()
                    results.append(result)
                except Exception as e:
                    print(f"Error analyzing {filepath}: {e}")
        
        return results
    
    def get_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for multiple analysis results.
        
        Args:
            results: List of AnalysisResult
            
        Returns:
            Summary statistics
        """
        return {
            'total_files': len(results),
            'total_lines': sum(r.lines for r in results),
            'total_functions': sum(r.functions for r in results),
            'total_classes': sum(r.classes for r in results),
            'total_bugs': sum(len(r.bugs) for r in results),
            'critical_bugs': sum(len([b for b in r.bugs if b.get('severity') == 'CRITICAL']) for r in results),
            'total_issues': sum(r.issues_count for r in results),
            'severity_distribution': {
                'CRITICAL': len([r for r in results if r.severity == 'CRITICAL']),
                'HIGH': len([r for r in results if r.severity == 'HIGH']),
                'ACCEPTABLE': len([r for r in results if r.severity == 'ACCEPTABLE']),
                'GOOD': len([r for r in results if r.severity == 'GOOD']),
                'EXCELLENT': len([r for r in results if r.severity == 'EXCELLENT']),
            },
            'average_complexity': sum(r.complexity.get('average_complexity', 0) for r in results) / len(results) if results else 0,
            'max_complexity': max((r.complexity.get('max_complexity', 0) for r in results), default=0),
        }