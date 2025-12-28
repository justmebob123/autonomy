"""
ToolDefinitionGenerator - Generates OpenAI-compatible tool definitions

Generates tool definitions from custom tools for LLM tool calling.
"""

from typing import Dict, Any, Optional, List
import logging

from ..logging_setup import get_logger
from .registry import ToolRegistry, ToolMetadata


class ToolDefinitionGenerator:
    """
    Generates OpenAI-compatible tool definitions.
    
    Creates tool definitions from custom tool metadata for use with LLM tool calling.
    
    Example:
        generator = ToolDefinitionGenerator(registry)
        definition = generator.generate_definition('analyze_imports')
        definitions = generator.generate_all_definitions()
    """
    
    def __init__(self, registry: ToolRegistry, logger: Optional[logging.Logger] = None):
        """
        Initialize definition generator.
        
        Args:
            registry: Tool registry instance
            logger: Optional logger instance
        """
        self.registry = registry
        self.logger = logger or get_logger()
    
    def generate_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate OpenAI-compatible definition for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool definition dict or None if tool not found
        """
        # Get from registry (uses cache)
        return self.registry.get_tool_definition(tool_name)
    
    def generate_all_definitions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate definitions for all tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool definitions
        """
        tools = self.registry.list_tools(category)
        definitions = []
        
        for tool in tools:
            definition = self.generate_definition(tool.name)
            if definition:
                definitions.append(definition)
        
        return definitions
    
    def generate_definitions_for_phase(self, phase: str) -> List[Dict[str, Any]]:
        """
        Generate definitions for a specific phase.
        
        Args:
            phase: Phase name (e.g., 'coding', 'analysis')
            
        Returns:
            List of tool definitions
        """
        return self.registry.get_tools_for_phase(phase)
    
    def validate_definition(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool definition.
        
        Args:
            definition: Tool definition dict
            
        Returns:
            Validation result with 'valid' and 'errors'
        """
        errors = []
        
        # Check required fields
        if 'type' not in definition:
            errors.append("Missing 'type' field")
        elif definition['type'] != 'function':
            errors.append("Type must be 'function'")
        
        if 'function' not in definition:
            errors.append("Missing 'function' field")
        else:
            func = definition['function']
            
            # Check function fields
            if 'name' not in func:
                errors.append("Missing 'name' in function")
            
            if 'description' not in func:
                errors.append("Missing 'description' in function")
            
            if 'parameters' not in func:
                errors.append("Missing 'parameters' in function")
            else:
                params = func['parameters']
                
                # Check parameters structure
                if 'type' not in params:
                    errors.append("Missing 'type' in parameters")
                elif params['type'] != 'object':
                    errors.append("Parameters type must be 'object'")
                
                if 'properties' not in params:
                    errors.append("Missing 'properties' in parameters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON schema for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            JSON schema dict or None
        """
        definition = self.generate_definition(tool_name)
        if not definition:
            return None
        
        return definition.get('function', {}).get('parameters', {})
    
    def format_for_ollama(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Format tool definition for Ollama.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Ollama-compatible definition or None
        """
        # Ollama uses same format as OpenAI
        return self.generate_definition(tool_name)
    
    def format_for_anthropic(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Format tool definition for Anthropic Claude.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Anthropic-compatible definition or None
        """
        definition = self.generate_definition(tool_name)
        if not definition:
            return None
        
        # Anthropic uses slightly different format
        func = definition['function']
        return {
            'name': func['name'],
            'description': func['description'],
            'input_schema': func['parameters']
        }
    
    def get_tool_documentation(self, tool_name: str) -> Optional[str]:
        """
        Generate documentation for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Markdown documentation or None
        """
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return None
        
        doc = f"# {metadata.name}\n\n"
        doc += f"**Version**: {metadata.version}\n"
        doc += f"**Category**: {metadata.category}\n"
        doc += f"**Author**: {metadata.author}\n\n"
        doc += f"## Description\n\n{metadata.description}\n\n"
        
        if metadata.parameters:
            doc += "## Parameters\n\n"
            for param_name, param_spec in metadata.parameters.items():
                param_type = param_spec.get('type', 'string')
                param_desc = param_spec.get('description', '')
                doc += f"- **{param_name}** (`{param_type}`): {param_desc}\n"
            doc += "\n"
        
        doc += "## Security\n\n"
        doc += f"- Requires Filesystem: {metadata.requires_filesystem}\n"
        doc += f"- Requires Network: {metadata.requires_network}\n"
        doc += f"- Requires Subprocess: {metadata.requires_subprocess}\n"
        doc += f"- Timeout: {metadata.timeout_seconds}s\n"
        doc += f"- Max File Size: {metadata.max_file_size_mb}MB\n"
        
        return doc