"""
Bug Detector - Detects specific bug patterns found during analysis.

This detector incorporates all bug patterns discovered during the
depth-61 examination of the autonomy codebase:

1. Variable used before definition (role_design.py)
2. Missing tool call processing (prompt_improvement.py, role_improvement.py)
3. Missing next_phase in PhaseResult (qa.py)
4. Missing task status update (qa.py)
5. Wrong order: track before process (role_design.py)
"""

import ast
import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Bug:
    """A bug found during analysis."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    pattern: str  # Bug pattern name
    location: str
    line: int
    message: str
    fix: str
    example: str


class BugDetector(ast.NodeVisitor):
    """
    Detects specific bug patterns.
    
    Bug Patterns Detected:
    1. Variable used before definition
    2. Missing tool call processing
    3. Missing next_phase in PhaseResult
    4. Missing task status update before return
    5. Wrong order: track_tool_calls before process_tool_calls
    6. State mutation without save
    7. Missing error handling in I/O operations
    8. Infinite loop without exit condition
    
    Example:
        detector = BugDetector(tree, content)
        bugs = detector.detect()
        for bug in bugs:
            if bug['severity'] == 'CRITICAL':
                print(f"CRITICAL BUG: {bug['message']}")
    """
    
    def __init__(self, tree: ast.AST, content: str):
        self.tree = tree
        self.content = content
        self.lines = content.split('\n')
        
        self.bugs: List[Bug] = []
        
        # Track variables
        self.defined_vars: Dict[str, int] = {}
        self.used_vars: Dict[str, int] = {}
        
        # Track tool call processing
        self.tool_call_lines: Dict[str, int] = {}
    
    def detect(self) -> List[Dict[str, Any]]:
        """
        Detect all bug patterns.
        
        Returns:
            List of bugs found
        """
        # Pattern 1: Variable used before definition
        self._detect_use_before_def()
        
        # Pattern 2: Missing tool call processing
        self._detect_missing_tool_processing()
        
        # Pattern 3: Missing next_phase
        self._detect_missing_next_phase()
        
        # Pattern 4: Missing task status update
        self._detect_missing_status_update()
        
        # Pattern 5: Wrong order (track before process)
        self._detect_wrong_order()
        
        # Pattern 6: State mutation without save
        self._detect_missing_state_save()
        
        # Pattern 7: Missing error handling
        self._detect_missing_error_handling()
        
        # Sort by severity and line
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.bugs.sort(key=lambda x: (severity_order[x.severity], x.line))
        
        return [
            {
                'severity': bug.severity,
                'pattern': bug.pattern,
                'location': bug.location,
                'line': bug.line,
                'message': bug.message,
                'fix': bug.fix,
                'example': bug.example,
            }
            for bug in self.bugs
        ]
    
    def _detect_use_before_def(self):
        """Detect variables used before definition."""
        # This is handled by DataFlowAnalyzer
        # But we add specific pattern matching for common cases
        
        for i, line in enumerate(self.lines, 1):
            # Pattern: self.track_tool_calls(tool_calls, results)
            # where results is defined later
            if 'track_tool_calls' in line and 'results' in line:
                # Check if results is defined before this line
                results_defined = False
                for j in range(i):
                    if 'results =' in self.lines[j]:
                        results_defined = True
                        break
                
                if not results_defined:
                    self.bugs.append(Bug(
                        severity='CRITICAL',
                        pattern='use_before_def',
                        location=f'line {i}',
                        line=i,
                        message=f"Variable 'results' used at line {i} before definition",
                        fix="Move 'results = handler.process_tool_calls(tool_calls)' before this line",
                        example="# Fix:\nresults = handler.process_tool_calls(tool_calls)\nself.track_tool_calls(tool_calls, results)"
                    ))
    
    def _detect_missing_tool_processing(self):
        """Detect missing tool call processing."""
        has_tool_calls = 'tool_calls' in self.content
        has_process = 'process_tool_calls' in self.content
        has_track = 'track_tool_calls' in self.content
        
        if has_tool_calls and has_track and not has_process:
            # Find line with track_tool_calls
            for i, line in enumerate(self.lines, 1):
                if 'track_tool_calls' in line:
                    self.bugs.append(Bug(
                        severity='CRITICAL',
                        pattern='missing_tool_processing',
                        location=f'line {i}',
                        line=i,
                        message="track_tool_calls() called but tool_calls are never processed",
                        fix="Add tool call processing before tracking",
                        example="# Fix:\nhandler = ToolCallHandler(...)\nresults = handler.process_tool_calls(tool_calls)\nself.track_tool_calls(tool_calls, results)"
                    ))
                    break
    
    def _detect_missing_next_phase(self):
        """Detect missing next_phase in PhaseResult."""
        for i, line in enumerate(self.lines, 1):
            if 'return PhaseResult(' in line:
                # Check if next_phase is in this or next few lines
                has_next_phase = False
                for j in range(i-1, min(i+5, len(self.lines))):
                    if 'next_phase' in self.lines[j]:
                        has_next_phase = True
                        break
                
                if not has_next_phase:
                    self.bugs.append(Bug(
                        severity='MEDIUM',
                        pattern='missing_next_phase',
                        location=f'line {i}',
                        line=i,
                        message=f"PhaseResult at line {i} missing 'next_phase' parameter",
                        fix="Add next_phase parameter to PhaseResult",
                        example='# Fix:\nreturn PhaseResult(\n    success=False,\n    phase=self.phase_name,\n    message="...",\n    next_phase="planning"  # Add this\n)'
                    ))
    
    def _detect_missing_status_update(self):
        """Detect missing task status update before return."""
        for i, line in enumerate(self.lines, 1):
            if 'return PhaseResult(' in line:
                # Check if task.status is updated in previous lines
                has_status_update = False
                for j in range(max(0, i-10), i):
                    if 'task.status' in self.lines[j] or 'TaskStatus' in self.lines[j]:
                        has_status_update = True
                        break
                
                # Check if this is an error return
                is_error_return = False
                for j in range(i-1, min(i+5, len(self.lines))):
                    if 'success=False' in self.lines[j]:
                        is_error_return = True
                        break
                
                if is_error_return and not has_status_update:
                    self.bugs.append(Bug(
                        severity='HIGH',
                        pattern='missing_status_update',
                        location=f'line {i}',
                        line=i,
                        message=f"Error return at line {i} without updating task.status",
                        fix="Update task.status before returning",
                        example='# Fix:\ntask.status = TaskStatus.FAILED\nstate_manager.save(state)\nreturn PhaseResult(success=False, ...)'
                    ))
    
    def _detect_wrong_order(self):
        """Detect wrong order: track before process."""
        process_line = None
        track_line = None
        
        for i, line in enumerate(self.lines, 1):
            if 'process_tool_calls' in line and '=' in line:
                process_line = i
            if 'track_tool_calls' in line:
                track_line = i
        
        if process_line and track_line and track_line < process_line:
            self.bugs.append(Bug(
                severity='CRITICAL',
                pattern='wrong_order',
                location=f'lines {track_line}-{process_line}',
                line=track_line,
                message=f"track_tool_calls() at line {track_line} called before process_tool_calls() at line {process_line}",
                fix="Process tool calls before tracking them",
                example='# Fix:\n# First process\nresults = handler.process_tool_calls(tool_calls)\n# Then track\nself.track_tool_calls(tool_calls, results)'
            ))
    
    def _detect_missing_state_save(self):
        """Detect state mutations without save."""
        has_mutation = False
        has_save = False
        mutation_line = None
        
        for i, line in enumerate(self.lines, 1):
            if re.search(r'(task|state)\.\w+\s*=', line):
                has_mutation = True
                if not mutation_line:
                    mutation_line = i
            
            if 'state_manager.save' in line or 'self.state_manager.save' in line:
                has_save = True
        
        if has_mutation and not has_save and mutation_line:
            self.bugs.append(Bug(
                severity='HIGH',
                pattern='missing_state_save',
                location=f'line {mutation_line}',
                line=mutation_line,
                message=f"State mutation at line {mutation_line} without calling state_manager.save()",
                fix="Call state_manager.save(state) after mutations",
                example='# Fix:\ntask.status = TaskStatus.COMPLETED\nstate_manager.save(state)  # Add this'
            ))
    
    def _detect_missing_error_handling(self):
        """Detect missing error handling for I/O operations."""
        for i, line in enumerate(self.lines, 1):
            # Check for I/O operations
            if any(op in line for op in ['open(', '.read(', '.write(', 'json.load', 'json.dump']):
                # Check if in try block
                in_try = False
                indent = len(line) - len(line.lstrip())
                
                # Look backwards for try
                for j in range(i-1, max(0, i-20), -1):
                    prev_line = self.lines[j]
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    
                    if prev_indent < indent and 'try:' in prev_line:
                        in_try = True
                        break
                
                if not in_try:
                    self.bugs.append(Bug(
                        severity='MEDIUM',
                        pattern='missing_error_handling',
                        location=f'line {i}',
                        line=i,
                        message=f"I/O operation at line {i} without error handling",
                        fix="Wrap I/O operations in try-except block",
                        example='# Fix:\ntry:\n    with open(file) as f:\n        data = f.read()\nexcept IOError as e:\n    # Handle error'
                    ))