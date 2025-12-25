"""
Pipeline Phases

This module contains all pipeline phases:
- PlanningPhase: Creates initial task plan from MASTER_PLAN.md
- CodingPhase: Implements code for tasks
- QAPhase: Reviews code for quality issues
- DebuggingPhase: Fixes issues found by QA
- ProjectPlanningPhase: Expands project when all tasks complete
- DocumentationPhase: Updates README and ARCHITECTURE
- ToolEvaluationPhase: Evaluates custom tools
- PromptImprovementPhase: Improves custom prompts
- RoleImprovementPhase: Improves custom roles
"""

from .base import BasePhase, PhaseResult
from .planning import PlanningPhase
from .coding import CodingPhase
from .qa import QAPhase
from .debugging import DebuggingPhase
from .project_planning import ProjectPlanningPhase
from .documentation import DocumentationPhase
from .tool_evaluation import ToolEvaluationPhase
from .prompt_improvement import PromptImprovementPhase
from .role_improvement import RoleImprovementPhase

__all__ = [
    "BasePhase",
    "PhaseResult",
    "PlanningPhase",
    "CodingPhase",
    "QAPhase",
    "DebuggingPhase",
    "ProjectPlanningPhase",
    "DocumentationPhase",
    "ToolEvaluationPhase",
    "PromptImprovementPhase",
    "RoleImprovementPhase",
]
