"""
Multi-Model Orchestration System

This module implements a revolutionary architecture where:
- Models can call other models as tools
- An arbiter coordinates specialist models
- Prompts adapt dynamically to context
- The application provides capabilities, models make decisions
"""

from .model_tool import ModelTool, SpecialistRegistry
from .conversation_manager import ConversationThread, MultiModelConversationManager
from .arbiter import ArbiterModel
from .orchestrated_pipeline import OrchestratedPipeline

__all__ = [
    'ModelTool',
    'SpecialistRegistry',
    'ConversationThread',
    'MultiModelConversationManager',
    'ArbiterModel',
    'OrchestratedPipeline',
]