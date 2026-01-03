"""
Phase Dependencies

Container for phase dependencies to simplify initialization.
"""

from dataclasses import dataclass
from typing import Any, Dict
from pathlib import Path


@dataclass
class PhaseDependencies:
    """Container for all phase dependencies."""
    
    # Core dependencies
    config: Any  # PipelineConfig
    client: Any  # OllamaClient
    project_dir: Path
    
    # State management
    state_manager: Any  # StateManager
    file_tracker: Any  # FileTracker
    
    # Registries
    prompt_registry: Any  # PromptRegistry
    tool_registry: Any  # ToolRegistry
    role_registry: Any  # RoleRegistry
    
    # Specialists
    coding_specialist: Any
    reasoning_specialist: Any
    analysis_specialist: Any
    
    # Communication
    message_bus: Any
    adaptive_prompts: Any
    
    # Architecture & IPC
    arch_manager: Any  # ArchitectureManager
    objective_reader: Any  # ObjectiveReader
    status_writer: Any  # StatusWriter
    status_reader: Any  # StatusReader
    
    # Context providers
    error_context: Any  # ErrorContext
    code_context: Any  # CodeContext
    
    # Response parsing
    parser: Any  # ResponseParser
    
    # Specialist request handler
    specialist_request_handler: Any
    
    # Document IPC
    doc_ipc: Any  # DocumentIPC