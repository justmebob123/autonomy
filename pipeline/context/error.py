"""
Error Context

Provides rich error information for debugging and retry attempts.
"""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class ErrorRecord:
    """Record of a single error occurrence"""
    error_type: str
    message: str
    timestamp: str = ""
    phase: str = ""
    task_id: str = ""
    filepath: str = ""
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: str = ""
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "timestamp": self.timestamp,
            "phase": self.phase,
            "task_id": self.task_id,
            "filepath": self.filepath,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "stack_trace": self.stack_trace,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ErrorRecord":
        return cls(**data)
    
    @classmethod
    def from_exception(cls, exc: Exception, **kwargs) -> "ErrorRecord":
        """Create an ErrorRecord from an exception"""
        return cls(
            error_type=type(exc).__name__,
            message=str(exc),
            stack_trace=traceback.format_exc(),
            **kwargs
        )
    
    @classmethod
    def from_syntax_error(cls, error_msg: str, filepath: str = "",
                          code: str = "", **kwargs) -> "ErrorRecord":
        """Create an ErrorRecord from a syntax error message"""
        # Parse "Line X: message" format
        line_num = None
        message = error_msg
        
        if error_msg.startswith("Line "):
            parts = error_msg.split(":", 1)
            if len(parts) == 2:
                try:
                    line_num = int(parts[0].replace("Line ", ""))
                    message = parts[1].strip()
                except ValueError:
                    pass
        
        # Extract code snippet around error line
        snippet = ""
        if code and line_num:
            lines = code.split("\n")
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 2)
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>> " if i == line_num - 1 else "    "
                snippet_lines.append(f"{prefix}{i+1}: {lines[i]}")
            snippet = "\n".join(snippet_lines)
        
        return cls(
            error_type="SyntaxError",
            message=message,
            filepath=filepath,
            line_number=line_num,
            code_snippet=snippet,
            **kwargs
        )
    
    def format_for_llm(self) -> str:
        """Format error for LLM context"""
        lines = [f"ERROR [{self.error_type}]: {self.message}"]
        
        if self.filepath:
            lines.append(f"File: {self.filepath}")
        
        if self.line_number:
            lines.append(f"Line: {self.line_number}")
        
        if self.code_snippet:
            lines.append("Code context:")
            lines.append(self.code_snippet)
        
        return "\n".join(lines)
    
    def format_short(self) -> str:
        """Short one-line format"""
        loc = ""
        if self.filepath:
            loc = f" in {self.filepath}"
            if self.line_number:
                loc += f":{self.line_number}"
        return f"[{self.error_type}]{loc}: {self.message}"


class ErrorContext:
    """
    Manages error history and provides context for retries.
    
    Tracks errors across attempts and generates helpful context
    for LLMs to understand what went wrong and how to fix it.
    """
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self._errors: List[ErrorRecord] = []
        self._by_file: Dict[str, List[ErrorRecord]] = {}
        self._by_task: Dict[str, List[ErrorRecord]] = {}
    
    def add(self, error: ErrorRecord):
        """Add an error to the context"""
        self._errors.append(error)
        
        # Trim history if needed
        if len(self._errors) > self.max_history:
            self._errors = self._errors[-self.max_history:]
        
        # Index by file
        if error.filepath:
            if error.filepath not in self._by_file:
                self._by_file[error.filepath] = []
            self._by_file[error.filepath].append(error)
        
        # Index by task
        if error.task_id:
            if error.task_id not in self._by_task:
                self._by_task[error.task_id] = []
            self._by_task[error.task_id].append(error)
    
    def add_syntax_error(self, error_msg: str, filepath: str = "",
                         code: str = "", task_id: str = "", phase: str = "coding"):
        """Convenience method to add a syntax error"""
        error = ErrorRecord.from_syntax_error(
            error_msg, filepath, code,
            task_id=task_id, phase=phase
        )
        self.add(error)
    
    def add_exception(self, exc: Exception, **kwargs):
        """Convenience method to add an exception"""
        error = ErrorRecord.from_exception(exc, **kwargs)
        self.add(error)
    
    def get_for_file(self, filepath: str) -> List[ErrorRecord]:
        """Get all errors for a file"""
        return self._by_file.get(filepath, [])
    
    def get_for_task(self, task_id: str) -> List[ErrorRecord]:
        """Get all errors for a task"""
        return self._by_task.get(task_id, [])
    
    def get_recent(self, count: int = 5) -> List[ErrorRecord]:
        """Get most recent errors"""
        return self._errors[-count:]
    
    def get_by_type(self, error_type: str) -> List[ErrorRecord]:
        """Get all errors of a specific type"""
        return [e for e in self._errors if e.error_type == error_type]
    
    def clear(self):
        """Clear all errors"""
        self._errors = []
        self._by_file = {}
        self._by_task = {}
    
    def clear_for_file(self, filepath: str):
        """Clear errors for a specific file"""
        if filepath in self._by_file:
            pass
            # Remove from main list
            file_errors = set(id(e) for e in self._by_file[filepath])
            self._errors = [e for e in self._errors if id(e) not in file_errors]
            # Remove from index
            del self._by_file[filepath]
    
    def format_for_task(self, task_id: str, max_errors: int = 5) -> str:
        """Format error context for a task retry"""
        errors = self.get_for_task(task_id)[-max_errors:]
        
        if not errors:
            return ""
        
        lines = [
            "=== PREVIOUS ERRORS FOR THIS TASK ===",
            f"Total attempts: {len(errors)}",
            ""
        ]
        
        for i, error in enumerate(errors, 1):
            lines.append(f"--- Attempt {i} ---")
            lines.append(error.format_for_llm())
            lines.append("")
        
        lines.append("=== FIX THESE ISSUES ===")
        
        return "\n".join(lines)
    
    def format_for_file(self, filepath: str, max_errors: int = 3) -> str:
        """Format error context for a file"""
        errors = self.get_for_file(filepath)[-max_errors:]
        
        if not errors:
            return ""
        
        lines = [f"Previous errors in {filepath}:"]
        for error in errors:
            lines.append(f"  - {error.format_short()}")
        
        return "\n".join(lines)
    
    def get_error_patterns(self) -> Dict[str, int]:
        """Analyze error patterns"""
        patterns = {}
        for error in self._errors:
            patterns[error.error_type] = patterns.get(error.error_type, 0) + 1
        return patterns
    
    def get_problematic_files(self, threshold: int = 2) -> List[str]:
        """Get files with multiple errors"""
        return [
            filepath for filepath, errors in self._by_file.items()
            if len(errors) >= threshold
        ]
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return {
            "errors": [e.to_dict() for e in self._errors],
            "max_history": self.max_history,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ErrorContext":
        """Deserialize from dict"""
        ctx = cls(max_history=data.get("max_history", 10))
        for error_data in data.get("errors", []):
            ctx.add(ErrorRecord.from_dict(error_data))
        return ctx
