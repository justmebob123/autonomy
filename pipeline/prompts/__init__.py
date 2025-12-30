"""
Prompts Package

This package contains:
1. Core prompts from prompts.py (SYSTEM_PROMPTS, get_*_prompt functions)
2. Meta-prompts for self-designing AI system:
   - prompt_architect.py: Meta-prompt for designing custom prompts
   - tool_designer.py: Meta-prompt for designing custom tools
   - role_creator.py: Meta-prompt for designing custom roles
   - team_orchestrator.py: Meta-prompt for team coordination

IMPORTANT: This __init__.py re-exports everything from ../prompts.py
to avoid shadowing issues when prompts/ directory exists alongside prompts.py
"""

# Re-export everything from prompts.py (the file, not the directory)
import sys
from pathlib import Path

# Import from the prompts.py file (sibling to this directory)
parent_dir = Path(__file__).parent.parent
prompts_file = parent_dir / "prompts.py"

# Load prompts.py module
import importlib.util
spec = importlib.util.spec_from_file_location("_prompts_module", prompts_file)
_prompts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_prompts_module)

# Re-export everything from prompts.py
SYSTEM_PROMPTS = _prompts_module.SYSTEM_PROMPTS
get_planning_prompt = _prompts_module.get_planning_prompt
get_coding_prompt = _prompts_module.get_coding_prompt
get_qa_prompt = _prompts_module.get_qa_prompt
get_debug_prompt = _prompts_module.get_debug_prompt
get_project_planning_prompt = _prompts_module.get_project_planning_prompt
get_documentation_prompt = _prompts_module.get_documentation_prompt
get_modification_decision_prompt = _prompts_module.get_modification_decision_prompt
get_refactoring_prompt = _prompts_module.get_refactoring_prompt

# Import meta-prompts from this directory
from .prompt_architect import get_prompt_architect_prompt
from .tool_designer import get_tool_designer_prompt
from .role_creator import get_role_creator_prompt
from .team_orchestrator import get_team_orchestrator_prompt

__all__ = [
    # From prompts.py
    "SYSTEM_PROMPTS",
    "get_planning_prompt",
    "get_coding_prompt",
    "get_qa_prompt",
    "get_debug_prompt",
    "get_project_planning_prompt",
    "get_documentation_prompt",
    "get_modification_decision_prompt",
    "get_refactoring_prompt",
    # Meta-prompts from this directory
    "get_prompt_architect_prompt",
    "get_tool_designer_prompt",
    "get_role_creator_prompt",
    "get_team_orchestrator_prompt",
]