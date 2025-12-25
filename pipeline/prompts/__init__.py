"""
Prompts Package

Contains meta-prompts for self-designing AI system:
- prompt_architect.py: Meta-prompt for designing custom prompts
- tool_designer.py: Meta-prompt for designing custom tools
- role_creator.py: Meta-prompt for designing custom roles
- team_orchestrator.py: Meta-prompt for team coordination
"""

from .prompt_architect import get_prompt_architect_prompt
from .tool_designer import get_tool_designer_prompt
from .role_creator import get_role_creator_prompt
from .team_orchestrator import get_team_orchestrator_prompt

__all__ = [
    "get_prompt_architect_prompt",
    "get_tool_designer_prompt",
    "get_role_creator_prompt",
    "get_team_orchestrator_prompt",
]