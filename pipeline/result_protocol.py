"""
Result Protocol - Standardized interface for all result types

This module provides a common interface for result objects across the codebase,
allowing consistent handling of success/failure, data access, and error reporting.
"""

from typing import Protocol, Any, Optional, Dict, runtime_checkable


@runtime_checkable
class Result(Protocol):
    """
    Common interface for all result types.
    
    This protocol defines the standard interface that all result objects
    should implement, enabling consistent result handling across subsystems.
    """
    
    @property
    def success(self) -> bool:
        """Whether the operation succeeded"""
        ...
    
    @property
    def data(self) -> Any:
        """Result data (if successful)"""
        ...
    
    @property
    def error(self) -> Optional[str]:
        """Error message (if failed)"""
        ...
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata about the result"""
        ...


class SubprocessResult:
    """
    Adapter for subprocess.CompletedProcess to implement Result protocol.
    
    Wraps subprocess results to provide consistent interface.
    """
    
    def __init__(self, proc):
        """
        Initialize from subprocess.CompletedProcess.
        
        Args:
            proc: subprocess.CompletedProcess instance
        """
        self._proc = proc
    
    @property
    def success(self) -> bool:
        """Operation succeeded if return code is 0"""
        return self._proc.returncode == 0
    
    @property
    def data(self) -> str:
        """Standard output as data"""
        return self._proc.stdout if self._proc.stdout else ""
    
    @property
    def error(self) -> Optional[str]:
        """Standard error if failed, None if succeeded"""
        if not self.success and self._proc.stderr:
            return self._proc.stderr
        return None
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata including return code and command"""
        return {
            'returncode': self._proc.returncode,
            'args': self._proc.args if hasattr(self._proc, 'args') else None
        }


class DictResult:
    """
    Adapter for dict-based results to implement Result protocol.
    
    Wraps dictionary results to provide consistent interface.
    """
    
    def __init__(self, result_dict: Dict[str, Any]):
        """
        Initialize from dictionary.
        
        Args:
            result_dict: Dictionary with result data
        """
        self._dict = result_dict
    
    @property
    def success(self) -> bool:
        """Success from 'success' key, defaults to True if not present"""
        return self._dict.get('success', True)
    
    @property
    def data(self) -> Any:
        """Data from 'data' key, or entire dict if not present"""
        return self._dict.get('data', self._dict)
    
    @property
    def error(self) -> Optional[str]:
        """Error from 'error' key"""
        return self._dict.get('error')
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """All keys except success, data, error"""
        return {
            k: v for k, v in self._dict.items()
            if k not in ('success', 'data', 'error')
        }


def ensure_result(obj: Any) -> Result:
    """
    Ensure an object implements the Result protocol.
    
    If the object already implements Result, return it as-is.
    Otherwise, wrap it in an appropriate adapter.
    
    Args:
        obj: Object to ensure is a Result
        
    Returns:
        Object implementing Result protocol
        
    Raises:
        TypeError: If object cannot be adapted to Result
    """
    # Check if already implements Result
    if isinstance(obj, Result):
        return obj
    
    # Check if it's a subprocess result
    if hasattr(obj, 'returncode') and hasattr(obj, 'stdout'):
        return SubprocessResult(obj)
    
    # Check if it's a dict
    if isinstance(obj, dict):
        return DictResult(obj)
    
    # Check if it has the required attributes
    if hasattr(obj, 'success') and hasattr(obj, 'data'):
        return obj  # Assume it implements the protocol
    
    raise TypeError(f"Cannot adapt {type(obj)} to Result protocol")