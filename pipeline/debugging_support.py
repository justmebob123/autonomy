"""
Debugging Support Module

Consolidates support utilities for debugging operations.
"""

from typing import Dict, Any
import json
import time

from .error_strategies import get_strategy, enhance_prompt_with_strategy
from .failure_prompts import get_retry_prompt
from .sudo_filter import filter_sudo_from_tool_calls


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