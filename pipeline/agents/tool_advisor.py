"""
Tool Advisor Agent

Uses FunctionGemma to help with tool calling decisions and validation.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple


class ToolAdvisor:
    """
    Tool calling advisor using FunctionGemma.
    
    Helps other AIs:
    - Choose appropriate tools for tasks
    - Format tool calls correctly
    - Validate tool call syntax
    - Fix malformed tool calls
    """
    
    def __init__(self, client, config):
        """
        Initialize tool advisor.
        
        Args:
            client: OllamaClient instance
            config: PipelineConfig instance
        """
        self.client = client
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def suggest_tools(self, task_description: str, available_tools: List[Dict]) -> List[str]:
        """
        Suggest which tools to use for a task.
        
        Args:
            task_description: Description of what needs to be done
            available_tools: List of available tool definitions
            
        Returns:
            List of recommended tool names
        """
        # Build prompt for FunctionGemma
        tool_names = [t['function']['name'] for t in available_tools]
        tool_descriptions = {
            t['function']['name']: t['function'].get('description', '')
            for t in available_tools
        }
        
        prompt = f"""Given this task, which tools should be used?

TASK: {task_description}

AVAILABLE TOOLS:
{json.dumps(tool_descriptions, indent=2)}

Respond with a JSON list of tool names that should be used.
Example: ["tool1", "tool2"]"""
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Use FunctionGemma
        response = self._call_functiongemma(messages)
        
        if not response or "error" in response:
            self.logger.warning("FunctionGemma tool suggestion failed, returning all tools")
            return tool_names
        
        # Parse response
        content = response.get('content', '')
        try:
            # Try to extract JSON list
            import re
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                suggested = json.loads(json_match.group())
                # Filter to only valid tool names
                return [t for t in suggested if t in tool_names]
        except json.JSONDecodeError:
            # Response wasn't valid JSON, continue to fallback
            pass
        except Exception as e:
            self.logger.debug(f"Failed to parse tool suggestions: {e}")
        
        return tool_names
    
    def validate_tool_call(self, tool_call: Dict, tool_definition: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate a tool call against its definition.
        
        Args:
            tool_call: The tool call to validate
            tool_definition: The tool's definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tool_name = tool_call.get('name')
        arguments = tool_call.get('arguments', {})
        
        if not tool_name:
            return False, "Tool call missing 'name' field"
        
        # Check if tool exists
        if tool_definition['function']['name'] != tool_name:
            return False, f"Tool '{tool_name}' not found in definition"
        
        # Check required parameters
        parameters = tool_definition['function'].get('parameters', {})
        required = parameters.get('required', [])
        
        for param in required:
            if param not in arguments:
                return False, f"Missing required parameter: {param}"
        
        # Check parameter types (basic validation)
        properties = parameters.get('properties', {})
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get('type')
                actual_type = type(value).__name__
                
                # Map Python types to JSON schema types
                type_map = {
                    'str': 'string',
                    'int': 'integer',
                    'float': 'number',
                    'bool': 'boolean',
                    'list': 'array',
                    'dict': 'object'
                }
                
                if expected_type and type_map.get(actual_type) != expected_type:
                    return False, f"Parameter '{param}' has wrong type: expected {expected_type}, got {actual_type}"
        
        return True, None
    
    def fix_tool_call(self, malformed_call: str, available_tools: List[Dict]) -> Optional[Dict]:
        """
        Attempt to fix a malformed tool call.
        
        Args:
            malformed_call: The malformed tool call string
            available_tools: List of available tool definitions
            
        Returns:
            Fixed tool call dict, or None if cannot fix
        """
        prompt = f"""Fix this malformed tool call:

MALFORMED CALL:
{malformed_call}

AVAILABLE TOOLS:
{json.dumps([t['function'] for t in available_tools], indent=2)}

Respond with a valid JSON tool call in this format:
{{
    "name": "tool_name",
    "arguments": {{
        "param1": "value1"
    }}
}}"""
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_functiongemma(messages)
        
        if not response or "error" in response:
            return None
        
        content = response.get('content', '')
        try:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*?\}', content, re.DOTALL)
            if json_match:
                fixed_call = json.loads(json_match.group())
                return fixed_call
        except json.JSONDecodeError:
            # Response wasn't valid JSON
            pass
        except Exception as e:
            self.logger.debug(f"Failed to parse fixed tool call: {e}")
        
        return None
    
    def explain_tool_usage(self, tool_name: str, tool_definition: Dict) -> str:
        """
        Generate an explanation of how to use a tool.
        
        Args:
            tool_name: Name of the tool
            tool_definition: The tool's definition
            
        Returns:
            Human-readable explanation
        """
        prompt = f"""Explain how to use this tool:

TOOL DEFINITION:
{json.dumps(tool_definition['function'], indent=2)}

Provide a clear, concise explanation with an example."""
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_functiongemma(messages)
        
        if response and "error" not in response:
            return response.get('content', 'No explanation available')
        
        return 'No explanation available'
    
    def _call_functiongemma(self, messages: List[Dict]) -> Optional[Dict]:
        """
        Call FunctionGemma model.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Response dict or None
        """
        # Find FunctionGemma on available servers
        functiongemma_host = None
        for host, models in self.client.available_models.items():
            if any('functiongemma' in m.lower() for m in models):
                functiongemma_host = host
                break
        
        if not functiongemma_host:
            self.logger.warning("FunctionGemma not available on any server")
            return None
        
        try:
            response = self.client.chat(
                functiongemma_host,
                "functiongemma",
                messages,
                tools=None,
                temperature=0.1,  # Low temperature for precise responses
                timeout=None  # UNLIMITED
            )
            return response
        except Exception as e:
            self.logger.error(f"FunctionGemma call failed: {e}")
            return None