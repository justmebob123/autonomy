"""
Error signature tracking for detecting bug transitions and progress.
"""
from typing import Optional, Set, Dict, Any
from dataclasses import dataclass
import hashlib


@dataclass
class ErrorSignature:
    """Represents a unique error signature for tracking progress."""
    
    error_type: str  # KeyError, UnboundLocalError, SyntaxError, etc.
    message: str     # The error message
    file: str        # File where error occurred
    line: int        # Line number
    
    def __hash__(self):
        """Hash based on all components for set operations."""
        return hash((self.error_type, self.message, self.file, self.line))
    
    def __eq__(self, other):
        """Equality based on all components."""
        if not isinstance(other, ErrorSignature):
            return False
        return (self.error_type == other.error_type and
                self.message == other.message and
                self.file == other.file and
                self.line == other.line)
    
    def __str__(self):
        """Human-readable representation."""
        return f"{self.error_type}: {self.message} at {self.file}:{self.line}"
    
    def short_id(self) -> str:
        """Generate a short ID for this error signature."""
        content = f"{self.error_type}:{self.message}:{self.file}:{self.line}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    @classmethod
    def from_error_dict(cls, error: Dict[str, Any]) -> Optional['ErrorSignature']:
        """Create ErrorSignature from error dictionary."""
        try:
            pass
            # Extract error type from traceback or error message
            error_type = error.get('type', 'RuntimeError')
            
            # Get the actual error message
            message = error.get('message', '')
            traceback = error.get('traceback', '')
            
            # Try to extract error type from traceback
            if traceback:
                lines = traceback.strip().split('\n')
                # Look for the actual exception line (usually last non-empty line)
                for line in reversed(lines):
                    line = line.strip()
                    if line and not line.startswith('File') and not line.startswith('Traceback'):
                        pass
                        # This should be the exception line like "KeyError: 'url'"
                        if ':' in line:
                            error_type = line.split(':')[0].strip()
                            message = ':'.join(line.split(':')[1:]).strip()
                        break
            
            # Get file and line from traceback
            file = error.get('file', 'unknown')
            line = error.get('line', 0)
            
            # Try to extract from traceback if not in error dict
            if traceback and (file == 'unknown' or line == 0):
                lines = traceback.strip().split('\n')
                for i, tline in enumerate(lines):
                    if tline.strip().startswith('File'):
                        pass
                        # Parse: File "/path/to/file.py", line 123, in function
                        parts = tline.split(',')
                        if len(parts) >= 2:
                            file_part = parts[0].replace('File', '').strip().strip('"\'')
                            line_part = parts[1].strip()
                            if line_part.startswith('line'):
                                try:
                                    line = int(line_part.replace('line', '').strip())
                                    file = file_part
                                except ValueError:
                                    pass
            
            return cls(
                error_type=error_type,
                message=message,
                file=file,
                line=line
            )
        except Exception as e:
            pass
            # If we can't parse the error, return None
            return None


class ProgressTracker:
    """Tracks error signatures across iterations to detect progress."""
    
    def __init__(self):
        self.error_history: list[Set[ErrorSignature]] = []
        self.bugs_fixed_count = 0
        self.bugs_discovered_count = 0
        self.current_iteration = 0
    
    def add_iteration(self, errors: list[Dict[str, Any]]) -> None:
        """Add errors from current iteration."""
        self.current_iteration += 1
        
        # Convert errors to signatures
        signatures = set()
        for error in errors:
            sig = ErrorSignature.from_error_dict(error)
            if sig:
                signatures.add(sig)
        
        self.error_history.append(signatures)
    
    def detect_transition(self) -> Optional[Dict[str, Any]]:
        """
        Detect if we transitioned from one bug to another.
        
        Returns:
            None if no transition, or dict with:
            - type: 'BUG_FIXED', 'NEW_BUG', 'BUG_TRANSITION', 'NO_PROGRESS'
            - fixed: set of fixed error signatures
            - new: set of new error signatures
            - persisting: set of persisting error signatures
        """
        if len(self.error_history) < 2:
            return None
        
        previous_errors = self.error_history[-2]
        current_errors = self.error_history[-1]
        
        # Calculate differences
        fixed = previous_errors - current_errors
        new = current_errors - previous_errors
        persisting = previous_errors & current_errors
        
        # Update counters
        self.bugs_fixed_count += len(fixed)
        self.bugs_discovered_count += len(new)
        
        # Determine transition type
        if fixed and new:
            return {
                'type': 'BUG_TRANSITION',
                'fixed': fixed,
                'new': new,
                'persisting': persisting
            }
        elif fixed and not new:
            return {
                'type': 'BUG_FIXED',
                'fixed': fixed,
                'new': set(),
                'persisting': persisting
            }
        elif new and not fixed:
            return {
                'type': 'NEW_BUG',
                'fixed': set(),
                'new': new,
                'persisting': persisting
            }
        elif persisting:
            return {
                'type': 'NO_PROGRESS',
                'fixed': set(),
                'new': set(),
                'persisting': persisting
            }
        else:
            return None
    
    def get_current_errors(self) -> Set[ErrorSignature]:
        """Get current error signatures."""
        if not self.error_history:
            return set()
        return self.error_history[-1]
    
    def get_previous_errors(self) -> Set[ErrorSignature]:
        """Get previous error signatures."""
        if len(self.error_history) < 2:
            return set()
        return self.error_history[-2]
    
    def is_making_progress(self) -> bool:
        """Check if we're making progress (fixing bugs or discovering new ones)."""
        transition = self.detect_transition()
        if not transition:
            return False
        return transition['type'] in ['BUG_FIXED', 'BUG_TRANSITION', 'NEW_BUG']
    
    def get_stats(self) -> Dict[str, int]:
        """Get progress statistics."""
        return {
            'iterations': self.current_iteration,
            'bugs_fixed': self.bugs_fixed_count,
            'bugs_discovered': self.bugs_discovered_count,
            'current_bugs': len(self.get_current_errors())
        }