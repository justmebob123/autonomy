#!/usr/bin/env python3
"""
BaseTool - Base class for all custom tools.

All custom tools must inherit from BaseTool and implement execute().
This provides standard interface, validation, error handling, and timeout.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time
import signal
import sys


@dataclass
class ToolResult:
    """
    Standard result format for all tools.
    
    Attributes:
        success: Whether tool executed successfully
        result: Tool output (any type)
        error: Error message if failed
        metadata: Additional information
        execution_time: Time taken to execute
    """
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata or {},
            'execution_time': self.execution_time
        }


class TimeoutError(Exception):
    """Raised when tool execution times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Tool execution timed out")


class BaseTool(ABC):
    """
    Base class for all custom tools.
    
    All custom tools must:
    1. Inherit from BaseTool
    2. Set class attributes (name, description, version, category)
    3. Implement execute() method
    4. Return ToolResult
    5. Handle all errors
    6. Validate inputs
    
    Example:
        class AnalyzeImports(BaseTool):
            name = "analyze_imports"
            description = "Analyze import statements in Python file"
            version = "1.0.0"
            category = "analysis"
            requires_filesystem = True
            
            def validate_inputs(self, **kwargs):
                if 'filepath' not in kwargs:
                    return False, "filepath is required"
                if not kwargs['filepath'].endswith('.py'):
                    return False, "filepath must be a Python file"
                return True, None
            
            def execute(self, **kwargs):
                filepath = kwargs['filepath']
                full_path = self.project_dir / filepath
                
                if not full_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found: {filepath}"
                    )
                
                # Analyze imports
                imports = self._analyze_imports(full_path)
                
                return ToolResult(
                    success=True,
                    result=imports,
                    metadata={'filepath': filepath}
                )
    """
    
    # Tool metadata (MUST override in subclass)
    name: str = "base_tool"
    description: str = "Base tool class"
    version: str = "1.0.0"
    category: str = "utility"
    author: str = "AI"
    
    # Security settings (override as needed)
    requires_filesystem: bool = False
    requires_network: bool = False
    requires_subprocess: bool = False
    timeout_seconds: int = 30
    max_file_size_mb: int = 10
    
    def __init__(self, project_dir: str):
        """
        Initialize tool with project directory.
        
        Args:
            project_dir: Path to project root directory
        """
        self.project_dir = Path(project_dir)
        self.start_time: Optional[float] = None
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool (MUST implement in subclass).
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success, result, error, metadata
            
        Example:
            def execute(self, filepath: str) -> ToolResult:
                try:
                    # Validate
                    if not filepath:
                        return ToolResult(success=False, error="filepath required")
                    
                    # Execute
                    result = self._analyze_file(filepath)
                    
                    # Return
                    return ToolResult(
                        success=True,
                        result=result,
                        metadata={'filepath': filepath}
                    )
                    
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        """
        pass
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate tool inputs (override in subclass for custom validation).
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            (is_valid, error_message)
            
        Example:
            def validate_inputs(self, **kwargs):
                if 'filepath' not in kwargs:
                    return False, "filepath is required"
                
                filepath = kwargs['filepath']
                if not filepath.endswith('.py'):
                    return False, "filepath must be a Python file"
                
                full_path = self.project_dir / filepath
                if not full_path.exists():
                    return False, f"File not found: {filepath}"
                
                return True, None
        """
        return True, None
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run the tool with validation, error handling, and timeout.
        
        This is the main entry point that wraps execute() with:
        - Input validation
        - Error handling
        - Timeout enforcement
        - Execution time tracking
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult
        """
        self.start_time = time.time()
        
        try:
            # Validate inputs
            is_valid, error = self.validate_inputs(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=f"Invalid input: {error}",
                    execution_time=time.time() - self.start_time
                )
            
            # Set timeout alarm (Unix only)
            if sys.platform != 'win32' and self.timeout_seconds > 0:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            try:
                # Execute tool
                result = self.execute(**kwargs)
                
                # Cancel alarm
                if sys.platform != 'win32' and self.timeout_seconds > 0:
                    signal.alarm(0)
                
                # Add execution time
                result.execution_time = time.time() - self.start_time
                
                # Add metadata
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update({
                    'tool_name': self.name,
                    'tool_version': self.version,
                    'execution_time': result.execution_time
                })
                
                return result
                
            except TimeoutError:
                return ToolResult(
                    success=False,
                    error=f"Tool timed out after {self.timeout_seconds} seconds",
                    execution_time=time.time() - self.start_time
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {e}",
                execution_time=time.time() - self.start_time if self.start_time else 0
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.
        
        Returns:
            Dict with tool information
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'category': self.category,
            'author': self.author,
            'security': {
                'requires_filesystem': self.requires_filesystem,
                'requires_network': self.requires_network,
                'requires_subprocess': self.requires_subprocess,
                'timeout_seconds': self.timeout_seconds,
                'max_file_size_mb': self.max_file_size_mb
            }
        }