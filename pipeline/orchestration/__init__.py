"""
Multi-Model Orchestration System

This module implements a revolutionary architecture where:
- Models can call other models as tools
- An arbiter coordinates specialist models
- Prompts adapt dynamically to context
- The application provides capabilities, models make decisions
"""

from .model_tool import ModelTool, SpecialistRegistry, get_specialist_registry
from .conversation_manager import ConversationThread, MultiModelConversationManager
from .arbiter import ArbiterModel
from .dynamic_prompts import DynamicPromptBuilder, PromptContext

__all__ = [
    'ModelTool',
    'SpecialistRegistry',
    'get_specialist_registry',
    'ConversationThread',
    'MultiModelConversationManager',
    'ArbiterModel',
    'DynamicPromptBuilder',
    'PromptContext',
]