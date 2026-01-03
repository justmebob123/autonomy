"""
Phase Builder

Builds phases with shared dependencies to eliminate initialization duplication.
"""

from pathlib import Path
from typing import Type, Any
import logging

from .phase_dependencies import PhaseDependencies
from .base import BasePhase
from ..config import PipelineConfig
from ..client import OllamaClient
from ..state.manager import StateManager
from ..state.file_tracker import FileTracker
from ..context.error import ErrorContext
from ..context.code import CodeContext
from ..client import ResponseParser
from ..logging_setup import get_logger


class PhaseBuilder:
    """
    Builds phases with shared dependencies.
    
    Eliminates duplication in phase initialization by creating
    shared instances of common dependencies.
    """
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        """
        Initialize phase builder.
        
        Args:
            config: Pipeline configuration
            client: Ollama client
        """
        self.config = config
        self.client = client
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        
        # Create shared dependencies once
        self.dependencies = self._create_dependencies()
    
    def _create_dependencies(self) -> PhaseDependencies:
        """Create all shared dependencies."""
        # State management
        state_manager = StateManager(self.project_dir)
        file_tracker = FileTracker(self.project_dir)
        
        # Registries
        from ..prompt_registry import PromptRegistry
        from ..tool_registry import ToolRegistry
        from ..role_registry import RoleRegistry
        
        prompt_registry = PromptRegistry(self.project_dir)
        tool_registry = ToolRegistry(self.project_dir)
        role_registry = RoleRegistry(self.project_dir, self.client)
        
        # Specialists
        from ..orchestration.unified_model_tool import UnifiedModelTool
        from ..orchestration.specialists import (
            create_coding_specialist,
            create_reasoning_specialist,
            create_analysis_specialist
        )
        
        # Get server URLs from config
        coding_model, coding_server = self.config.model_assignments.get(
            'coding', ('qwen2.5-coder:32b', 'ollama02.thiscluster.net')
        )
        reasoning_model = 'qwen2.5:32b'
        reasoning_server = coding_server
        analysis_model, analysis_server = self.config.model_assignments.get(
            'planning', ('qwen2.5:14b', 'ollama01.thiscluster.net')
        )
        
        # Create unified model tools
        coding_tool = UnifiedModelTool(coding_model, f"http://{coding_server}:11434")
        reasoning_tool = UnifiedModelTool(reasoning_model, f"http://{reasoning_server}:11434")
        analysis_tool = UnifiedModelTool(analysis_model, f"http://{analysis_server}:11434")
        
        # Create specialists
        coding_specialist = create_coding_specialist(coding_tool)
        reasoning_specialist = create_reasoning_specialist(reasoning_tool)
        analysis_specialist = create_analysis_specialist(analysis_tool)
        
        # Specialist request handler
        from ..specialist_request_handler import SpecialistRequestHandler
        specialist_request_handler = SpecialistRequestHandler({
            'coding': coding_specialist,
            'reasoning': reasoning_specialist,
            'analysis': analysis_specialist
        })
        
        # Message bus
        from ..messaging import MessageBus
        message_bus = MessageBus()
        
        # Adaptive prompts
        from ..adaptive_prompts import AdaptivePrompts
        adaptive_prompts = AdaptivePrompts(self.project_dir)
        
        # Architecture & IPC
        from ..architecture_manager import ArchitectureManager
        from ..ipc_integration import ObjectiveReader, StatusWriter, StatusReader
        
        arch_manager = ArchitectureManager(self.project_dir, self.logger)
        objective_reader = ObjectiveReader(self.project_dir, self.logger)
        status_writer = StatusWriter(self.project_dir, self.logger)
        status_reader = StatusReader(self.project_dir, self.logger)
        
        # Context providers
        error_context = ErrorContext()
        code_context = CodeContext(self.project_dir)
        
        # Response parsing
        parser = ResponseParser(self.client)
        
        # Document IPC
        from ..document_ipc import DocumentIPC
        doc_ipc = DocumentIPC(self.project_dir, self.logger)
        
        return PhaseDependencies(
            config=self.config,
            client=self.client,
            project_dir=self.project_dir,
            state_manager=state_manager,
            file_tracker=file_tracker,
            prompt_registry=prompt_registry,
            tool_registry=tool_registry,
            role_registry=role_registry,
            coding_specialist=coding_specialist,
            reasoning_specialist=reasoning_specialist,
            analysis_specialist=analysis_specialist,
            message_bus=message_bus,
            adaptive_prompts=adaptive_prompts,
            arch_manager=arch_manager,
            objective_reader=objective_reader,
            status_writer=status_writer,
            status_reader=status_reader,
            error_context=error_context,
            code_context=code_context,
            parser=parser,
            specialist_request_handler=specialist_request_handler,
            doc_ipc=doc_ipc
        )
    
    def build_phase(self, phase_class: Type[BasePhase], **overrides) -> BasePhase:
        """
        Build a phase with shared dependencies.
        
        Args:
            phase_class: Phase class to instantiate
            **overrides: Override specific dependencies
        
        Returns:
            Initialized phase instance
        """
        # Use overrides if provided, otherwise use shared dependencies
        return phase_class(
            config=overrides.get('config', self.dependencies.config),
            client=overrides.get('client', self.dependencies.client),
            state_manager=overrides.get('state_manager', self.dependencies.state_manager),
            file_tracker=overrides.get('file_tracker', self.dependencies.file_tracker),
            prompt_registry=overrides.get('prompt_registry', self.dependencies.prompt_registry),
            tool_registry=overrides.get('tool_registry', self.dependencies.tool_registry),
            role_registry=overrides.get('role_registry', self.dependencies.role_registry),
            coding_specialist=overrides.get('coding_specialist', self.dependencies.coding_specialist),
            reasoning_specialist=overrides.get('reasoning_specialist', self.dependencies.reasoning_specialist),
            analysis_specialist=overrides.get('analysis_specialist', self.dependencies.analysis_specialist),
            message_bus=overrides.get('message_bus', self.dependencies.message_bus),
            adaptive_prompts=overrides.get('adaptive_prompts', self.dependencies.adaptive_prompts)
        )