"""
Phase Resources

Consolidated access to phase-specific resources (tools and prompts).
"""

from typing import List, Dict, Any
from .tools import get_tools_for_phase
from .prompts import get_debug_prompt, get_modification_decision_prompt


def get_phase_tools(phase_name: str) -> List[Dict[str, Any]]:
    """Get tools for a specific phase."""
    return get_tools_for_phase(phase_name)


def get_debugging_prompt(issue: Dict, context: Dict) -> str:
    """Get debugging prompt for an issue."""
    return get_debug_prompt(issue, context)

def get_modification_decision(context: Dict) -> str:
    """Get modification decision prompt."""
    return get_modification_decision_prompt(context)
