"""
Unified Model Tool

Merges the duplicate model communication layers:
- pipeline.client.Client (existing LLM communication)
- pipeline.orchestration.model_tool.ModelTool (Phase 1 infrastructure)

This class wraps the existing Client with ModelTool features,
providing a unified interface for all model communication.
"""

from typing import Dict, List, Optional, Any
import logging
import time

logger = logging.getLogger(__name__)


class UnifiedModelTool:
    """
    Unified model communication layer.
    
    Wraps existing Client with ModelTool features:
    - Usage tracking
    - Context window management
    - Consistent response format
    - Error handling
    
    This allows orchestration components to use the same
    model communication as the existing pipeline.
    """
    
    def __init__(
        self,
        model_name: str,
        host: str,
        context_window: Optional[int] = None,
        client_class=None
    ):
        """
        Initialize unified model tool.
        
        Args:
            model_name: Name of the model (e.g., "qwen2.5:14b")
            host: Ollama server host (e.g., "http://localhost:11434")
            context_window: Context window size (auto-detected if None)
            client_class: Client class to use (for dependency injection/testing)
        """
        self.model_name = model_name
        self.host = host
        
        # Initialize logger
        from pipeline.logging_setup import get_logger
        self.logger = get_logger()
        
        # Import OllamaClient here to avoid circular imports
        if client_class is None:
            from pipeline.client import OllamaClient
            from pipeline.config import PipelineConfig
            
            # Create config for client
            config = PipelineConfig()
            config.model = model_name
            
            # Create client with config
            self.client = OllamaClient(config)
        else:
            # Use provided client class (for testing)
            self.client = client_class(model_name, host)
        
        # Set context window
        self.context_window = context_window or self._get_context_window()
        
        # Initialize usage statistics
        self.usage_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_tokens': 0,
            'total_time': 0.0
        }
        
        logger.info(
            f"UnifiedModelTool initialized: {model_name} @ {host} "
            f"(context: {self.context_window})"
        )
    
    def _get_context_window(self) -> int:
        """
        Get context window size for model.
        
        Returns:
            Context window size in tokens
        """
        model_lower = self.model_name.lower()
        
        # Large models (32b)
        if '32b' in model_lower or 'coder:32b' in model_lower:
            return 16384
        
        # Medium models (14b)
        elif '14b' in model_lower:
            return 8192
        
        # Small models
        elif '7b' in model_lower or 'gemma' in model_lower:
            return 4096
        
        # Default
        else:
            return 8192
    
    def execute(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute model call with unified interface.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            tools: Optional list of tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with:
                - success: bool
                - response: str (model response text)
                - tool_calls: list (parsed tool calls)
                - usage: dict (token usage)
                - error: str (if failed)
        """
        self.usage_stats['total_calls'] += 1
        start_time = time.time()
        
        # Log which model and server we're using
        self.logger.info(f"🤖 Calling {self.model_name} on {self.host}")
        
        try:
            # Prepare messages with system prompt
            if system_prompt:
                # Add system message if not already present
                if not messages or messages[0].get('role') != 'system':
                    messages = [{'role': 'system', 'content': system_prompt}] + messages
            
            # Call client using chat() method
            # Extract host and model from initialization
            response = self.client.chat(
                host=self.host,
                model=self.model_name,
                messages=messages,
                tools=tools,
                temperature=temperature,
                timeout=None  # No timeout for specialist calls
            )
            
            # Track success
            self.usage_stats['successful_calls'] += 1
            elapsed = time.time() - start_time
            self.usage_stats['total_time'] += elapsed
            
            # Parse response
            result = self._parse_response(response)
            result['success'] = True
            result['elapsed_time'] = elapsed
            
            # Track token usage
            if 'usage' in result:
                self.usage_stats['total_tokens'] += result['usage'].get('total_tokens', 0)
            
            logger.debug(
                f"Model call successful: {self.model_name} "
                f"({elapsed:.2f}s, {result.get('usage', {}).get('total_tokens', 0)} tokens)"
            )
            
            return result
            
        except Exception as e:
            # Track failure
            self.usage_stats['failed_calls'] += 1
            elapsed = time.time() - start_time
            self.usage_stats['total_time'] += elapsed
            
            logger.error(f"Model call failed: {self.model_name} - {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'response': '',
                'tool_calls': [],
                'usage': {},
                'elapsed_time': elapsed
            }
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse response from client into unified format.
        
        Args:
            response: Raw response from client
            
        Returns:
            Parsed response dict
        """
        # Extract message
        message = response.get('message', {})
        
        # Extract content
        content = message.get('content', '')
        
        # Extract tool calls
        tool_calls = self._parse_tool_calls(message)
        
        # Extract usage
        usage = response.get('usage', {})
        
        return {
            'response': content,
            'tool_calls': tool_calls,
            'usage': usage,
            'raw_response': response
        }
    
    def _parse_tool_calls(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse tool calls from message.
        
        Args:
            message: Message dict from response
            
        Returns:
            List of tool call dicts in the format expected by ToolCallHandler
        """
        tool_calls = message.get('tool_calls', [])
        
        if not tool_calls:
            return []
        
        # Return tool calls in the exact format from the client
        # ToolCallHandler expects: {"function": {"name": "...", "arguments": {...}}}
        return tool_calls
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dict with usage statistics
        """
        stats = self.usage_stats.copy()
        
        # Calculate derived metrics
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
            stats['avg_time'] = stats['total_time'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
            stats['avg_time'] = 0.0
        
        if stats['successful_calls'] > 0:
            stats['avg_tokens'] = stats['total_tokens'] / stats['successful_calls']
        else:
            stats['avg_tokens'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_tokens': 0,
            'total_time': 0.0
        }
        logger.info(f"Statistics reset for {self.model_name}")
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"UnifiedModelTool(model={self.model_name}, "
            f"host={self.host}, "
            f"context={self.context_window}, "
            f"calls={self.usage_stats['total_calls']})"
        )


def create_unified_model_tool(
    model_name: str,
    host: str,
    context_window: Optional[int] = None
) -> UnifiedModelTool:
    """
    Factory function to create a unified model tool.
    
    Args:
        model_name: Name of the model
        host: Ollama server host
        context_window: Context window size (auto-detected if None)
        
    Returns:
        UnifiedModelTool instance
    """
    return UnifiedModelTool(model_name, host, context_window)