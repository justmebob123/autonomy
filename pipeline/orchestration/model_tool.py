"""
Model-as-Tool Framework

Enables models to be called as tools by other models.
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
from datetime import datetime

from ..client import OllamaClient
from ..logging_setup import get_logger


class ModelTool:
    """
    Wrapper that makes a model callable as a tool.
    
    This allows one model to consult another model by calling it as a tool.
    The arbiter can monitor and intervene in these consultations.
    """
    
    def __init__(self, 
                 model: str, 
                 server: str, 
                 role: str,
                 context_window: int = 8192,
                 temperature: float = 0.3):
        """
        Initialize a model tool.
        
        Args:
            model: Model name (e.g., "qwen2.5:32b")
            server: Server host (e.g., "ollama02.thiscluster.net")
            role: Role of this model (e.g., "coding", "reasoning")
            context_window: Maximum context window size
            temperature: Sampling temperature
        """
        self.model = model
        self.server = server
        self.role = role
        self.context_window = context_window
        self.temperature = temperature
        
        # Import config
        from ..config import PipelineConfig
        config = PipelineConfig()
        self.client = OllamaClient(config)
        self.logger = get_logger()
        
        # Track usage
        self.call_count = 0
        self.total_tokens = 0
        self.success_count = 0
        self.failure_count = 0
    
    def __call__(self, query: str, context: Optional[Dict] = None, 
                 tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Call this model with a query.
        
        Args:
            query: The question or task for this model
            context: Additional context (conversation history, state, etc.)
            tools: Tools available to this model
        
        Returns:
            Dict with response, tool_calls, and metadata
        """
        self.call_count += 1
        start_time = datetime.now()
        
        try:
            # Build messages
            messages = self._build_messages(query, context)
            
            # Log the consultation
            self.logger.info(f"🔧 Consulting {self.role} specialist ({self.model})")
            self.logger.debug(f"  Query: {query[:100]}...")
            
            # Call model
            response = self.client.chat(
                host=self.server,
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=self.temperature
            )
            
            # Extract tool calls
            tool_calls = self._extract_tool_calls(response)
            
            # Update stats
            self.success_count += 1
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"  ✓ Response received ({duration:.2f}s)")
            if tool_calls:
                self.logger.info(f"  ✓ {len(tool_calls)} tool call(s) made")
            
            return {
                "model": self.model,
                "role": self.role,
                "query": query,
                "response": response,
                "tool_calls": tool_calls,
                "success": True,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"  ✗ Model consultation failed: {e}")
            
            return {
                "model": self.model,
                "role": self.role,
                "query": query,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_messages(self, query: str, context: Optional[Dict]) -> List[Dict]:
        """
        Build message list for the model.
        
        Args:
            query: The main query
            context: Additional context
        
        Returns:
            List of message dicts
        """
        messages = []
        
        # System prompt (role-specific)
        messages.append({
            "role": "system",
            "content": self._get_system_prompt()
        })
        
        # Context messages (if provided)
        if context and context.get("conversation_history"):
            messages.extend(context["conversation_history"])
        
        # Main query
        messages.append({
            "role": "user",
            "content": query
        })
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """
        Get role-specific system prompt.
        
        Returns:
            System prompt string
        """
        prompts = {
            "coding": """You are a coding specialist with expertise in Python development.
Your role is to provide expert guidance on code implementation, architecture, and best practices.
When consulted, provide clear, actionable advice with code examples when appropriate.
Use tools to create files, search code, and analyze implementations.""",
            
            "reasoning": """You are a reasoning specialist with expertise in strategic thinking and problem-solving.
Your role is to analyze complex situations, identify root causes, and recommend optimal approaches.
When consulted, provide structured analysis with clear reasoning and actionable recommendations.
Use tools to provide your analysis in a structured format.""",
            
            "analysis": """You are an analysis specialist focused on quick, accurate assessments.
Your role is to rapidly analyze code, identify issues, and provide concise feedback.
When consulted, provide direct, actionable insights without unnecessary elaboration.
Use tools to report findings efficiently.""",
            
            "interpreter": """You are FunctionGemma, a tool call interpretation specialist.
Your role is to extract, clarify, and correct tool calls from model responses.
When consulted, analyze the response and provide properly formatted tool calls.
Focus on accuracy and clarity in tool call extraction."""
        }
        
        return prompts.get(self.role, "You are a helpful AI assistant.")
    
    def _extract_tool_calls(self, response: Dict) -> List[Dict]:
        """
        Extract tool calls from model response.
        
        Args:
            response: Model response dict
        
        Returns:
            List of tool call dicts
        """
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        return tool_calls
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this model tool.
        
        Returns:
            Dict with usage stats
        """
        return {
            "model": self.model,
            "role": self.role,
            "call_count": self.call_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.call_count if self.call_count > 0 else 0,
        }


class SpecialistRegistry:
    """
    Registry of specialist models available as tools.
    
    This provides a central place to register and access specialist models.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self.specialists: Dict[str, ModelTool] = {}
        self.logger = get_logger()
        self._register_default_specialists()
    
    def _register_default_specialists(self):
        """Register the default specialist models."""
        
        # Coding specialist - 32b coder on ollama02
        self.register(
            name="coding",
            model_tool=ModelTool(
                model="qwen2.5-coder:32b",
                server="ollama02.thiscluster.net",
                role="coding",
                context_window=16384,
                temperature=0.3
            )
        )
        
        # Reasoning specialist - 32b model on ollama02
        self.register(
            name="reasoning",
            model_tool=ModelTool(
                model="qwen2.5:32b",
                server="ollama02.thiscluster.net",
                role="reasoning",
                context_window=16384,
                temperature=0.3
            )
        )
        
        # Analysis specialist - 14b model on ollama01
        self.register(
            name="analysis",
            model_tool=ModelTool(
                model="qwen2.5:14b",
                server="ollama01.thiscluster.net",
                role="analysis",
                context_window=8192,
                temperature=0.3
            )
        )
        
        # FunctionGemma interpreter - on ollama01
        self.register(
            name="interpreter",
            model_tool=ModelTool(
                model="functiongemma",
                server="ollama01.thiscluster.net",
                role="interpreter",
                context_window=8192,
                temperature=0.1  # Lower temp for more deterministic tool extraction
            )
        )
        
        self.logger.info(f"✓ Registered {len(self.specialists)} specialist models")
    
    def register(self, name: str, model_tool: ModelTool):
        """
        Register a specialist model.
        
        Args:
            name: Name to register under (e.g., "coding")
            model_tool: ModelTool instance
        """
        self.specialists[name] = model_tool
        self.logger.info(f"  ✓ Registered {name} specialist: {model_tool.model} on {model_tool.server}")
    
    def get(self, name: str) -> Optional[ModelTool]:
        """
        Get a specialist by name.
        
        Args:
            name: Specialist name
        
        Returns:
            ModelTool instance or None
        """
        return self.specialists.get(name)
    
    def get_all(self) -> Dict[str, ModelTool]:
        """
        Get all registered specialists.
        
        Returns:
            Dict of name -> ModelTool
        """
        return self.specialists.copy()
    
    def get_tool_definitions(self) -> List[Dict]:
        """
        Get tool definitions for all specialists.
        
        This allows the arbiter to call specialists as tools.
        
        Returns:
            List of tool definition dicts
        """
        tools = []
        
        for name, specialist in self.specialists.items():
            tools.append({
                "name": f"consult_{name}_specialist",
                "description": f"Consult the {name} specialist ({specialist.model}) for expert guidance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"The question or task for the {name} specialist"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for the specialist"
                        }
                    },
                    "required": ["query"]
                }
            })
        
        return tools
    
    def get_stats(self) -> Dict[str, Dict]:
        """
        Get usage statistics for all specialists.
        
        Returns:
            Dict of name -> stats
        """
        return {
            name: specialist.get_stats()
            for name, specialist in self.specialists.items()
        }


# Global registry instance
_registry = None

def get_specialist_registry() -> SpecialistRegistry:
    """
    Get the global specialist registry.
    
    Returns:
        SpecialistRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = SpecialistRegistry()
    return _registry