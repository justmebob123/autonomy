"""
Data Flow Analysis - Native Pipeline Tool

Analyzes data flow in Python code including:
- Variable lifecycle tracking
- Uninitialized variable detection
- Unused assignment detection
- Variable scope analysis

Reimplemented from scripts/analysis/core/dataflow.py as a native pipeline tool.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class DataFlowReport:
    """Report of data flow analysis"""
    filepath: str
    timestamp: datetime = field(default_factory=datetime.now)
    variables: Dict[str, List[Tuple[str, int]]] = field(default_factory=dict)
    uninitialized_vars: List[str] = field(default_factory=list)
    unused_assignments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'filepath': self.filepath,
            'timestamp': self.timestamp.isoformat(),
            'total_variables': len(self.variables),
            'uninitialized_vars': self.uninitialized_vars,
            'unused_assignments': self.unused_assignments
        }


class DataFlowAnalyzer(ast.NodeVisitor):
    """Analyzes data flow in Python code"""
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.variables = defaultdict(list)
        self.current_scope = 'module'
        self.scope_stack = ['module']
        self.current_file = None
        
    def analyze(self, filepath: str) -> DataFlowReport:
        """
        Analyze data flow in a Python file.
        
        Args:
            filepath: Path to Python file (relative to project root)
            
        Returns:
            DataFlowReport with data flow analysis
        """
        self.current_file = filepath
        self.variables = defaultdict(list)
        self.scope_stack = ['module']
        
        try:
            full_path = self.project_root / filepath
            content = full_path.read_text()
            tree = ast.parse(content, filename=filepath)
            self.visit(tree)
            
            # Find uninitialized variables (used before defined)
            uninitialized = []
            for var, actions in self.variables.items():
                if actions and actions[0][0] == 'load':
                    uninitialized.append(var)
            
            # Find unused assignments (assigned but never read)
            unused_assignments = []
            for var, actions in self.variables.items():
                if len(actions) > 0:
                    # Check if last action is store and never followed by load
                    for i, (action, line) in enumerate(actions):
                        if action == 'store':
                            # Check if there's a load after this store
                            has_load_after = any(a[0] == 'load' for a in actions[i+1:])
                            if not has_load_after and i == len(actions) - 1:
                                unused_assignments.append({
                                    'variable': var,
                                    'line': line,
                                    'message': f'Variable "{var}" assigned but never used'
                                })
            
            return DataFlowReport(
                filepath=filepath,
                variables=dict(self.variables),
                uninitialized_vars=uninitialized,
                unused_assignments=unused_assignments
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Data flow analysis failed for {filepath}: {e}")
            raise
    
    def visit_FunctionDef(self, node):
        """Enter function scope"""
        self.scope_stack.append(node.name)
        self.current_scope = node.name
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1] if self.scope_stack else 'module'
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def visit_ClassDef(self, node):
        """Enter class scope"""
        self.scope_stack.append(node.name)
        self.current_scope = node.name
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1] if self.scope_stack else 'module'
    
    def visit_Name(self, node):
        """Track variable usage"""
        var_name = f"{self.current_scope}.{node.id}"
        
        if isinstance(node.ctx, ast.Store):
            self.variables[var_name].append(('store', node.lineno))
        elif isinstance(node.ctx, ast.Load):
            self.variables[var_name].append(('load', node.lineno))
        elif isinstance(node.ctx, ast.Del):
            self.variables[var_name].append(('del', node.lineno))
        
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        """Track augmented assignments (+=, -=, etc.)"""
        if isinstance(node.target, ast.Name):
            var_name = f"{self.current_scope}.{node.target.id}"
            # Augmented assignment is both load and store
            self.variables[var_name].append(('load', node.lineno))
            self.variables[var_name].append(('store', node.lineno))
        self.generic_visit(node)
    
    def generate_report(self, result: DataFlowReport) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append(f"Data Flow Analysis Report: {result.filepath}")
        lines.append(f"Timestamp: {result.timestamp.isoformat()}")
        lines.append(f"Total Variables Tracked: {len(result.variables)}")
        lines.append("")
        
        if result.uninitialized_vars:
            lines.append(f"Uninitialized Variables ({len(result.uninitialized_vars)}):")
            for var in result.uninitialized_vars:
                lines.append(f"  - {var}")
            lines.append("")
        
        if result.unused_assignments:
            lines.append(f"Unused Assignments ({len(result.unused_assignments)}):")
            for assignment in result.unused_assignments:
                lines.append(f"  Line {assignment['line']}: {assignment['message']}")
            lines.append("")
        
        if not result.uninitialized_vars and not result.unused_assignments:
            lines.append("No data flow issues detected!")
        
        return "\n".join(lines)