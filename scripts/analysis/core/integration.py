"""
Integration Analyzer - Detects miswired subsystems and partial integrations.

This analyzer identifies:
- Unused inherited methods (LoopDetectionMixin not used)
- Missing next_phase in PhaseResult returns
- Incomplete tool call processing
- Partial feature implementations
- Orphaned subsystems
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field


@dataclass
class IntegrationIssue:
    """An integration issue found during analysis."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    type: str
    location: str
    line: int
    message: str
    suggestion: Optional[str] = None
    related_files: List[str] = field(default_factory=list)


class IntegrationAnalyzer(ast.NodeVisitor):
    """
    Analyzes integration points and detects miswiring.
    
    Detects:
    - Inherited but unused methods (e.g., LoopDetectionMixin)
    - Missing required parameters (e.g., next_phase)
    - Incomplete implementations
    - Orphaned subsystems
    - Parallel implementations
    - Inconsistent patterns
    
    Example:
        analyzer = IntegrationAnalyzer(tree, content, filepath, project_root)
        result = analyzer.analyze()
        for issue in result['issues']:
            print(f"{issue['severity']}: {issue['message']}")
    """
    
    def __init__(self, tree: ast.AST, content: str, filepath: str, project_root: str):
        self.tree = tree
        self.content = content
        self.filepath = filepath
        self.project_root = project_root
        self.lines = content.split('\n')
        
        # Track classes and their bases
        self.classes: Dict[str, List[str]] = {}
        self.class_methods: Dict[str, Set[str]] = {}
        
        # Track method calls
        self.method_calls: Set[str] = set()
        
        # Track imports
        self.imports: Dict[str, str] = {}
        
        # Track PhaseResult returns
        self.phase_results: List[Dict[str, Any]] = []
        
        # Track tool call processing
        self.has_tool_call_processing = False
        self.has_track_tool_calls = False
        
        # Issues found
        self.issues: List[IntegrationIssue] = []
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform integration analysis.
        
        Returns:
            Dictionary with integration information and issues
        """
        self.visit(self.tree)
        
        # Check for integration issues
        self._check_mixin_usage()
        self._check_phase_result_completeness()
        self._check_tool_call_processing()
        self._check_state_management()
        
        # Sort issues by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.issues.sort(key=lambda x: (severity_order[x.severity], x.line))
        
        return {
            'classes': self.classes,
            'method_calls': list(self.method_calls),
            'phase_results': self.phase_results,
            'issues': [
                {
                    'severity': issue.severity,
                    'type': issue.type,
                    'location': issue.location,
                    'line': issue.line,
                    'message': issue.message,
                    'suggestion': issue.suggestion,
                    'related_files': issue.related_files,
                }
                for issue in self.issues
            ],
            'critical_issues': len([i for i in self.issues if i.severity == 'CRITICAL']),
            'high_issues': len([i for i in self.issues if i.severity == 'HIGH']),
            'medium_issues': len([i for i in self.issues if i.severity == 'MEDIUM']),
            'low_issues': len([i for i in self.issues if i.severity == 'LOW']),
        }
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        # Track class and its bases
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
        
        self.classes[node.name] = bases
        self.class_methods[node.name] = set()
        
        # Visit methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.class_methods[node.name].add(item.name)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function/method call."""
        # Track method calls
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            self.method_calls.add(method_name)
            
            # Check for specific patterns
            if method_name == 'process_tool_calls':
                self.has_tool_call_processing = True
            elif method_name == 'track_tool_calls':
                self.has_track_tool_calls = True
        
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check for PhaseResult
            if func_name == 'PhaseResult':
                self._track_phase_result(node)
        
        self.generic_visit(node)
    
    def visit_Return(self, node: ast.Return):
        """Visit return statement."""
        if node.value and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id == 'PhaseResult':
                    self._track_phase_result(node.value)
        
        self.generic_visit(node)
    
    def _track_phase_result(self, node: ast.Call):
        """Track PhaseResult creation."""
        # Extract arguments
        args = {}
        for keyword in node.keywords:
            args[keyword.arg] = ast.unparse(keyword.value)
        
        self.phase_results.append({
            'line': node.lineno,
            'has_next_phase': 'next_phase' in args,
            'has_success': 'success' in args,
            'args': args,
        })
    
    def _check_mixin_usage(self):
        """Check if inherited mixins are actually used."""
        for class_name, bases in self.classes.items():
            # Check for LoopDetectionMixin
            if 'LoopDetectionMixin' in bases:
                methods = self.class_methods.get(class_name, set())
                
                # Check if mixin methods are called
                has_check_for_loops = 'check_for_loops' in self.method_calls
                has_track_tool_calls = 'track_tool_calls' in self.method_calls
                has_init_loop_detection = 'init_loop_detection' in self.method_calls
                
                if not (has_check_for_loops or has_track_tool_calls or has_init_loop_detection):
                    self.issues.append(IntegrationIssue(
                        severity='MEDIUM',
                        type='unused_mixin',
                        location=class_name,
                        line=0,
                        message=f"Class '{class_name}' inherits from LoopDetectionMixin but doesn't use its methods",
                        suggestion="Either use check_for_loops() and track_tool_calls(), or remove the mixin inheritance"
                    ))
    
    def _check_phase_result_completeness(self):
        """Check if PhaseResult returns are complete."""
        for result in self.phase_results:
            if not result['has_next_phase']:
                self.issues.append(IntegrationIssue(
                    severity='MEDIUM',
                    type='missing_next_phase',
                    location='PhaseResult',
                    line=result['line'],
                    message=f"PhaseResult at line {result['line']} missing 'next_phase' parameter",
                    suggestion="Add next_phase parameter to help coordinator determine workflow"
                ))
    
    def _check_tool_call_processing(self):
        """Check if tool calls are processed correctly."""
        # Check if file has tool call processing
        if 'tool_calls' in self.content:
            # Should have both processing and tracking
            if not self.has_tool_call_processing:
                self.issues.append(IntegrationIssue(
                    severity='HIGH',
                    type='missing_tool_processing',
                    location='tool_calls',
                    line=0,
                    message="File references 'tool_calls' but doesn't call process_tool_calls()",
                    suggestion="Add: results = handler.process_tool_calls(tool_calls)"
                ))
            
            # Check order: process before track
            if self.has_tool_call_processing and self.has_track_tool_calls:
                # Find line numbers
                process_line = None
                track_line = None
                
                for i, line in enumerate(self.lines, 1):
                    if 'process_tool_calls' in line and '=' in line:
                        process_line = i
                    if 'track_tool_calls' in line and process_line:
                        track_line = i
                        break
                
                if process_line and track_line and track_line < process_line:
                    self.issues.append(IntegrationIssue(
                        severity='CRITICAL',
                        type='wrong_order',
                        location='tool_calls',
                        line=track_line,
                        message=f"track_tool_calls() at line {track_line} called before process_tool_calls() at line {process_line}",
                        suggestion="Process tool calls before tracking them"
                    ))
    
    def _check_state_management(self):
        """Check if state management is complete."""
        # Check for state mutations without save
        has_state_mutation = False
        has_state_save = False
        
        for i, line in enumerate(self.lines, 1):
            # Check for state mutations
            if re.search(r'(task|state)\.\w+\s*=', line):
                has_state_mutation = True
            
            # Check for state save
            if 'state_manager.save' in line or 'self.state_manager.save' in line:
                has_state_save = True
        
        if has_state_mutation and not has_state_save:
            self.issues.append(IntegrationIssue(
                severity='HIGH',
                type='missing_state_save',
                location='state_management',
                line=0,
                message="File mutates state but doesn't call state_manager.save()",
                suggestion="Add state_manager.save(state) after state mutations"
            ))