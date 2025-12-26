"""
Debugging Utilities

Standalone utility functions for debugging operations.
These functions are extracted from DebuggingPhase to reduce coupling.
"""

from typing import Dict, Optional, Any, List
from datetime import datetime
from .state.manager import PipelineState, TaskStatus, FileStatus
import json
import time

from .error_strategies import get_strategy, enhance_prompt_with_strategy
from .failure_prompts import get_retry_prompt
from .sudo_filter import filter_sudo_from_tool_calls
from .state.priority import TaskPriority



def is_same_error(error1: Dict, error2: Dict) -> bool:
    """
    Check if two errors are the same.
    
    Args:
        error1: First error dict
        error2: Second error dict
        
    Returns:
        True if errors are the same
    """
    # Compare error type
    type1 = error1.get('type', '')
    type2 = error2.get('type', '')
    
    if type1 != type2:
        return False
    
    # Compare error message (first 100 chars)
    msg1 = str(error1.get('message', ''))[:100]
    msg2 = str(error2.get('message', ''))[:100]
    
    if msg1 != msg2:
        return False
    
    # Compare file (if available)
    file1 = error1.get('file', '')
    file2 = error2.get('file', '')
    
    if file1 and file2 and file1 != file2:
        return False
    
    return True


def assess_error_complexity(issue: Dict, attempt_count: int = 0) -> str:
    """
    Assess error complexity to determine debugging strategy.
    
    Args:
        issue: Error issue dictionary
        attempt_count: Number of previous fix attempts
    
    Returns:
        'simple' - Direct fix
        'complex' - Team orchestration needed
        'novel' - Self-designing approach needed
    """
    # Check number of attempts
    if attempt_count >= 3:
        return 'complex'  # Multiple failed attempts
    
    # Check error type
    error_type = issue.get('type', '')
    if error_type in ['SyntaxError', 'IndentationError']:
        return 'simple'
    
    # Check if multiple files involved
    if 'multiple_files' in issue.get('context', {}):
        return 'complex'
    
    # Check if circular dependencies
    if 'circular' in issue.get('message', '').lower():
        return 'complex'
    
    # Check if multiple error types
    message = issue.get('message', '').lower()
    error_indicators = ['syntax', 'indentation', 'import', 'attribute', 'type']
    error_count = sum(1 for indicator in error_indicators if indicator in message)
    if error_count >= 2:
        return 'complex'
    
    # Default to simple
    return 'simple'


def analyze_no_tool_call_response(content: str, issue: Dict) -> str:
    """
    Analyze AI response to understand why no tool calls were made.
    
    Args:
        content: AI response content
        issue: The issue being debugged
    
    Returns:
        Brief analysis string explaining the situation
    """
    if not content:
        return "AI returned empty response"
    
    content_lower = content.lower()
    
    # Check for common patterns
    if "cannot" in content_lower or "can't" in content_lower or "unable" in content_lower:
        return "AI believes it cannot fix this issue"
    
    if "need more" in content_lower or "require" in content_lower or "missing" in content_lower:
        return "AI needs more information or context"
    
    if "not sure" in content_lower or "unclear" in content_lower or "don't know" in content_lower:
        return "AI is uncertain about the fix"
    
    if "explanation" in content_lower or "because" in content_lower or "reason" in content_lower:
        return "AI provided explanation instead of fix"
    
    if "tool" in content_lower or "function" in content_lower or "call" in content_lower:
        return "AI mentioned tools but didn't call them"
    
    if len(content) > 1000:
        return "AI provided lengthy response without action"
    
    return "AI responded but reason for no tool calls unclear"


def get_next_issue(state: PipelineState) -> Optional[Dict]:
    """
    Get the next issue to fix from the pipeline state.
    
    Args:
        state: Current pipeline state
        
    Returns:
        Issue dictionary or None if no issues found
    """
    # Check rejected files
    for file_state in state.files.values():
        if file_state.qa_status == FileStatus.REJECTED and file_state.issues:
            return file_state.issues[0]
    
    # Check task errors
    for task in state.tasks.values():
        if task.status == TaskStatus.QA_FAILED and task.errors:
            last_error = task.errors[-1]
            return {
                "filepath": task.target_file,
                "type": last_error.error_type,
                "description": last_error.message,
                "line": last_error.line_number,
            }
    
    return None

def get_error_strategy(error_type: str, context: Dict) -> Dict:
    """Get error handling strategy."""
    return get_strategy(error_type, context)


def enhance_prompt_with_error_strategy(prompt: str, strategy: Dict) -> str:
    """Enhance prompt with error handling strategy."""
    return enhance_prompt_with_strategy(prompt, strategy)


def get_failure_retry_prompt(failure_info: Dict, attempt_number: int) -> str:
    """Get retry prompt for failure."""
    return get_retry_prompt(failure_info, attempt_number)


def filter_sudo_commands(tool_calls: list) -> list:
    """Filter sudo commands from tool calls."""
    return filter_sudo_from_tool_calls(tool_calls)


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """Safely dump object to JSON string."""
    try:
        return json.dumps(obj, indent=indent)
    except (TypeError, ValueError) as e:
        return f"{{&quot;error&quot;: &quot;Failed to serialize: {str(e)}&quot;}}"


def safe_json_loads(json_str: str) -> Any:
    """Safely load JSON string."""
    try:
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        return {"error": f"Failed to parse: {str(e)}"}


def sleep_with_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> None:
    """Sleep with exponential backoff."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    time.sleep(delay)


def get_current_timestamp() -> float:
    """Get current timestamp."""
    return time.time()

def get_current_datetime() -> datetime:
    """Get current datetime object."""
    return datetime.now()


def get_timestamp_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()
