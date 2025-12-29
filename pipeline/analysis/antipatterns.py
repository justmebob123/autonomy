"""
Anti-Pattern Detection - Native Pipeline Tool

Detects anti-patterns in Python code including:
- Too many arguments
- Long functions
- Deep nesting
- God classes
- And other code smells

Reimplemented from scripts/analysis/detectors/antipatterns.py as a native pipeline tool.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AntiPatternReport:
    """Report of detected anti-patterns"""
    filepath: str
    timestamp: datetime = field(default_factory=datetime.now)
    antipatterns: List[Dict[str, Any]] = field(default_factory=list)
    pattern_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'filepath': self.filepath,
            'timestamp': self.timestamp.isoformat(),
            'antipatterns': self.antipatterns,
            'pattern_counts': self.pattern_counts,
            'total_antipatterns': len(self.antipatterns)
        }


class AntiPatternDetector(ast.NodeVisitor):
    """Detects anti-patterns in Python code"""
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.antipatterns = []
        self.current_file = None
        self.current_class = None
        self.class_methods = {}
        
    def detect(self, filepath: str) -> AntiPatternReport:
        """
        Detect anti-patterns in a Python file.
        
        Args:
            filepath: Path to Python file (relative to project root)
            
        Returns:
            AntiPatternReport with detected anti-patterns
        """
        self.current_file = filepath
        self.antipatterns = []
        self.class_methods = {}
        
        try:
            full_path = self.project_root / filepath
            content = full_path.read_text()
            tree = ast.parse(content, filename=filepath)
            self.visit(tree)
            
            # Count by pattern type
            pattern_counts = {}
            for pattern in self.antipatterns:
                ptype = pattern['type']
                pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1
            
            return AntiPatternReport(
                filepath=filepath,
                antipatterns=self.antipatterns,
                pattern_counts=pattern_counts
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Anti-pattern detection failed for {filepath}: {e}")
            raise
    
    def visit_ClassDef(self, node):
        """Check for class anti-patterns"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Count methods
        method_count = sum(1 for item in node.body if isinstance(item, ast.FunctionDef))
        self.class_methods[node.name] = method_count
        
        # Check for god class (too many methods)
        if method_count > 20:
            self.antipatterns.append({
                'type': 'god_class',
                'line': node.lineno,
                'class': node.name,
                'method_count': method_count,
                'message': f'Class "{node.name}" has {method_count} methods (>20) - consider splitting'
            })
        
        # Check for too many attributes
        attr_count = sum(1 for item in node.body if isinstance(item, ast.Assign))
        if attr_count > 15:
            self.antipatterns.append({
                'type': 'too_many_attributes',
                'line': node.lineno,
                'class': node.name,
                'attribute_count': attr_count,
                'message': f'Class "{node.name}" has {attr_count} attributes (>15) - consider refactoring'
            })
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Check for function anti-patterns"""
        # Check for too many arguments
        arg_count = len(node.args.args)
        if arg_count > 5:
            self.antipatterns.append({
                'type': 'too_many_arguments',
                'line': node.lineno,
                'function': node.name,
                'argument_count': arg_count,
                'message': f'Function "{node.name}" has {arg_count} arguments (>5) - consider using a config object'
            })
        
        # Check for long function
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno
            if lines > 50:
                self.antipatterns.append({
                    'type': 'long_function',
                    'line': node.lineno,
                    'function': node.name,
                    'lines': lines,
                    'message': f'Function "{node.name}" has {lines} lines (>50) - consider breaking into smaller functions'
                })
        
        # Check for deep nesting
        max_depth = self._get_max_nesting_depth(node)
        if max_depth > 4:
            self.antipatterns.append({
                'type': 'deep_nesting',
                'line': node.lineno,
                'function': node.name,
                'depth': max_depth,
                'message': f'Function "{node.name}" has nesting depth {max_depth} (>4) - consider extracting nested logic'
            })
        
        # Check for too many return statements
        return_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.Return))
        if return_count > 5:
            self.antipatterns.append({
                'type': 'too_many_returns',
                'line': node.lineno,
                'function': node.name,
                'return_count': return_count,
                'message': f'Function "{node.name}" has {return_count} return statements (>5) - consider simplifying logic'
            })
        
        self.generic_visit(node)
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def _get_max_nesting_depth(self, node, current_depth=0):
        """Calculate maximum nesting depth"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def generate_report(self, result: AntiPatternReport) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append(f"Anti-Pattern Detection Report: {result.filepath}")
        lines.append(f"Timestamp: {result.timestamp.isoformat()}")
        lines.append(f"Total Anti-Patterns: {len(result.antipatterns)}")
        lines.append("")
        
        if result.pattern_counts:
            lines.append("Pattern Breakdown:")
            for pattern, count in sorted(result.pattern_counts.items()):
                lines.append(f"  {pattern}: {count}")
            lines.append("")
        
        if result.antipatterns:
            lines.append("Detected Anti-Patterns:")
            for pattern in result.antipatterns:
                lines.append(f"\n  Line {pattern['line']}: {pattern['type']}")
                lines.append(f"    {pattern['message']}")
        else:
            lines.append("No anti-patterns detected!")
        
        return "\n".join(lines)