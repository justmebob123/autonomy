"""
AI Development Pipeline

A modular, state-managed pipeline for autonomous code generation.

Usage:
    # New architecture (recommended)
    from pipeline import PhaseCoordinator, PipelineConfig
    
    config = PipelineConfig(project_dir=Path("/path/to/project"))
    coordinator = PhaseCoordinator(config)
    coordinator.run()
    
    # Legacy architecture (still supported)
    from pipeline import Pipeline, PipelineConfig
    
    config = PipelineConfig(project_dir=Path("/path/to/project"))
    p = Pipeline(config)
    p.run()
"""

from .config import PipelineConfig, ServerConfig
from .logging_setup import setup_logging, get_logger

# New state-managed architecture
from .coordinator import PhaseCoordinator
from .state import StateManager, PipelineState, FileTracker, PriorityQueue, TaskPriority
from .context import ErrorContext, CodeContext
from .phases import (
    BasePhase,
    PhaseResult,
    PlanningPhase,
    CodingPhase,
    QAPhase,
    DebuggingPhase,
)

# Legacy architecture (for backward compatibility)
from .pipeline import Pipeline

__version__ = "3.1.0"
__all__ = [
    # Config
    "PipelineConfig",
    "ServerConfig",
    
    # Logging
    "setup_logging",
    "get_logger",
    
    # New architecture
    "PhaseCoordinator",
    "StateManager",
    "PipelineState",
    "FileTracker",
    "PriorityQueue",
    "TaskPriority",
    "ErrorContext",
    "CodeContext",
    "BasePhase",
    "PhaseResult",
    "PlanningPhase",
    "CodingPhase",
    "QAPhase",
    "DebuggingPhase",
    
    # Legacy
    "Pipeline",
]
