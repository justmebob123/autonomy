"""
Bug Detection - Native Pipeline Tool

Detects potential bugs in Python code including:
- Identity comparison with literals
- Bare except clauses
- Mutable default arguments
- Comparison with None using ==
- And other common Python bugs

Reimplemented from scripts/analysis/detectors/bugs.py as a native pipeline tool.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BugReport:
    """Report of detected bugs"""
    filepath: str
    timestamp: datetime = field(default_factory=datetime.now)
    bugs: List[Dict[str, Any]] = field(default_factory=list)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'filepath': self.filepath,
            'timestamp': self.timestamp.isoformat(),
            'bugs': self.bugs,
            'severity_counts': self.severity_counts,
            'total_bugs': len(self.bugs)
        }


class BugDetector(ast.NodeVisitor):
    """Detects potential bugs in Python code"""
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.bugs = []
        self.current_file = None
        
    def detect(self, filepath: str) -> BugReport:
        """
        Detect bugs in a Python file.
        
        Args:
            filepath: Path to Python file (relative to project root)
            
        Returns:
            BugReport with detected bugs
        """
        self.current_file = filepath
        self.bugs = []
        
        try:
            full_path = self.project_root / filepath
            content = full_path.read_text()
            tree = ast.parse(content, filename=filepath)
            self.visit(tree)
            
            # Count by severity
            severity_counts = {}
            for bug in self.bugs:
                severity = bug['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return BugReport(
                filepath=filepath,
                bugs=self.bugs,
                severity_counts=severity_counts
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Bug detection failed for {filepath}: {e}")
            raise
    
    def visit_Compare(self, node):
        """Check for comparison bugs"""
        # Check for identity comparison with literals
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)):
                if isinstance(comparator, (ast.Constant, ast.Num, ast.Str)):
                    self.bugs.append({
                        'type': 'identity_comparison_literal',
                        'severity': 'MEDIUM',
                        'line': node.lineno,
                        'message': 'Using "is" or "is not" with literals - use == or != instead',
                        'suggestion': 'Replace "is" with "==" or "is not" with "!="'
                    })
            
            # Check for comparison with None using ==
            if isinstance(op, (ast.Eq, ast.NotEq)):
                if isinstance(comparator, ast.Constant) and comparator.value is None:
                    self.bugs.append({
                        'type': 'none_comparison',
                        'severity': 'LOW',
                        'line': node.lineno,
                        'message': 'Comparing with None using == or != - use "is None" or "is not None"',
                        'suggestion': 'Use "is None" or "is not None" instead'
                    })
        
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Check for bare except clauses"""
        for handler in node.handlers:
            if handler.type is None:
                self.bugs.append({
                    'type': 'bare_except',
                    'severity': 'MEDIUM',
                    'line': handler.lineno,
                    'message': 'Bare except clause catches all exceptions including SystemExit and KeyboardInterrupt',
                    'suggestion': 'Specify exception type: except Exception: or except SpecificError:'
                })
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Check for mutable default arguments"""
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.bugs.append({
                    'type': 'mutable_default_argument',
                    'severity': 'HIGH',
                    'line': node.lineno,
                    'function': node.name,
                    'message': f'Function "{node.name}" has mutable default argument - this can cause unexpected behavior',
                    'suggestion': 'Use None as default and create mutable object inside function'
                })
        
        self.generic_visit(node)
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def visit_Assert(self, node):
        """Check for assert usage"""
        self.bugs.append({
            'type': 'assert_usage',
            'severity': 'LOW',
            'line': node.lineno,
            'message': 'Using assert statement - asserts can be disabled with -O flag',
            'suggestion': 'Use explicit if statement and raise exception for production code'
        })
        
        self.generic_visit(node)
    
    def analyze_all(self) -> BugReport:
        """
        Analyze all Python files in the project.
        
        Returns:
            BugReport with all detected bugs across all files
        """
        all_bugs = []
        files_analyzed = 0
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for filepath in python_files:
            try:
                rel_path = filepath.relative_to(self.project_root)
                result = self.detect(str(rel_path))
                all_bugs.extend(result.bugs)
                files_analyzed += 1
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error analyzing {filepath}: {e}")
        
        # Create combined report
        from datetime import datetime
        return BugReport(
            filepath="all_files",
            timestamp=datetime.now(),
            bugs=all_bugs,
            severity_counts={
                'critical': sum(1 for b in all_bugs if b.get('severity') == 'critical'),
                'high': sum(1 for b in all_bugs if b.get('severity') == 'high'),
                'medium': sum(1 for b in all_bugs if b.get('severity') == 'medium'),
                'low': sum(1 for b in all_bugs if b.get('severity') == 'low')
            }
        )
    
    def generate_report(self, result: BugReport) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append(f"Bug Detection Report: {result.filepath}")
        lines.append(f"Timestamp: {result.timestamp.isoformat()}")
        lines.append(f"Total Bugs: {len(result.bugs)}")
        lines.append("")
        
        if result.severity_counts:
            lines.append("Severity Breakdown:")
            for severity, count in sorted(result.severity_counts.items()):
                lines.append(f"  {severity}: {count}")
            lines.append("")
        
        if result.bugs:
            lines.append("Detected Bugs:")
            for bug in result.bugs:
                lines.append(f"\n  Line {bug['line']}: [{bug['severity']}] {bug['type']}")
                lines.append(f"    {bug['message']}")
                if 'suggestion' in bug:
                    lines.append(f"    Suggestion: {bug['suggestion']}")
        else:
            lines.append("No bugs detected!")
        
        return "\n".join(lines)