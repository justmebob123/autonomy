"""
CustomToolHandler - Executes custom tools with isolation and safety

Handles execution of custom tools via ToolExecutor with:
- Process isolation
- Timeout enforcement
- Result processing
- Error handling
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from pipeline.logging_setup import get_logger
from .registry import CustomToolRegistry


class CustomToolHandler:
    """
    Handler for custom tool execution.
    
    Executes custom tools via ToolExecutor with isolation and safety.
    Integrates with existing pipeline handlers.
    
    Example:
        handler = CustomToolHandler('/project', registry)
        result = handler.execute_tool('analyze_imports', {'filepath': 'main.py'})
        if result['success']:
            print(result['result'])
    """
    
    def __init__(self, project_dir: str, registry: CustomToolRegistry, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize custom tool handler.
        
        Args:
            project_dir: Project root directory
            registry: Tool registry instance
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.registry = registry
        self.logger = logger or get_logger()
        
        # Import ToolExecutor
        try:
            import sys
            # ALWAYS use pipeline's own scripts directory
            # Custom tools are part of the pipeline, not the project being worked on
            pipeline_root = Path(__file__).parent.parent.parent  # Go up from pipeline/custom_tools/handler.py to autonomy/
            tools_dir = pipeline_root / 'scripts' / 'custom_tools'
            
            # Add scripts directory to path for imports
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            
            # Import ToolExecutor from bin (manual tools) for execution infrastructure
            from bin.custom_tools.core.executor import ToolExecutor
            self.executor = ToolExecutor(
                str(tools_dir),
                str(self.project_dir),
                self.logger
            )
            self.logger.info("CustomToolHandler initialized with ToolExecutor")
        except ImportError as e:
            self.logger.error(f"Failed to import ToolExecutor: {e}")
            self.executor = None
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any], 
                    timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a custom tool.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            timeout: Optional timeout override
            
        Returns:
            Tool result dict with:
            - success: bool
            - result: Any (tool output)
            - error: str (if failed)
            - metadata: dict
            - execution_time: float
        """
        self.logger.info(f"Executing custom tool: {tool_name}")
        
        # Check if executor is available
        if not self.executor:
            return {
                'success': False,
                'error': 'ToolExecutor not available',
                'error_type': 'executor_unavailable'
            }
        
        # Check if tool exists
        if not self.registry.tool_exists(tool_name):
            self.logger.error(f"Custom tool not found: {tool_name}")
            return {
                'success': False,
                'error': f'Custom tool not found: {tool_name}',
                'error_type': 'tool_not_found'
            }
        
        # Get tool metadata
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return {
                'success': False,
                'error': f'Failed to get metadata for tool: {tool_name}',
                'error_type': 'metadata_error'
            }
        
        # Validate arguments
        validation_result = self._validate_arguments(tool_name, args, metadata)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'error_type': 'validation_error'
            }
        
        # Use tool timeout if not specified
        if timeout is None:
            timeout = metadata.timeout_seconds
        
        # Execute tool via ToolExecutor
        try:
            result = self.executor.execute_tool(tool_name, args, timeout)
            
            # Process result
            processed_result = self._process_result(tool_name, result, metadata)
            
            if processed_result['success']:
                self.logger.info(f"Custom tool {tool_name} executed successfully")
            else:
                self.logger.warning(f"Custom tool {tool_name} failed: {processed_result.get('error')}")
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Custom tool {tool_name} execution failed: {e}")
            return {
                'success': False,
                'error': f'Tool execution failed: {e}',
                'error_type': 'execution_error'
            }
    
    def _validate_arguments(self, tool_name: str, args: Dict[str, Any], 
                          metadata: Any) -> Dict[str, Any]:
        """
        Validate tool arguments.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            metadata: Tool metadata
            
        Returns:
            Validation result dict with 'valid' and 'error'
        """
        # Check required parameters
        required_params = set(metadata.parameters.keys())
        provided_params = set(args.keys())
        
        # Check for missing parameters
        missing = required_params - provided_params
        if missing:
            return {
                'valid': False,
                'error': f"Missing required parameters: {', '.join(missing)}"
            }
        
        # Check for extra parameters (warning only)
        extra = provided_params - required_params
        if extra:
            self.logger.warning(f"Tool {tool_name} received extra parameters: {', '.join(extra)}")
        
        # Validate parameter types
        for param_name, param_value in args.items():
            if param_name in metadata.parameters:
                param_spec = metadata.parameters[param_name]
                expected_type = param_spec.get('type', 'string')
                
                # Type validation
                if not self._validate_type(param_value, expected_type):
                    return {
                        'valid': False,
                        'error': f"Parameter '{param_name}' has invalid type. Expected {expected_type}, got {type(param_value).__name__}"
                    }
        
        return {'valid': True, 'error': None}
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type."""
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected_python_type)
    
    def _process_result(self, tool_name: str, result: Dict[str, Any], 
                       metadata: Any) -> Dict[str, Any]:
        """
        Process tool result.
        
        Args:
            tool_name: Name of the tool
            result: Raw tool result
            metadata: Tool metadata
            
        Returns:
            Processed result dict
        """
        # Add tool metadata to result
        if 'metadata' not in result:
            result['metadata'] = {}
        
        result['metadata'].update({
            'tool_name': tool_name,
            'tool_version': metadata.version,
            'tool_category': metadata.category,
            'is_custom_tool': True,
        })
        
        # Add security info
        result['metadata']['security'] = {
            'requires_filesystem': metadata.requires_filesystem,
            'requires_network': metadata.requires_network,
            'requires_subprocess': metadata.requires_subprocess,
        }
        
        return result
    
    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool call without executing it.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Validation result dict
        """
        # Check if tool exists
        if not self.registry.tool_exists(tool_name):
            return {
                'valid': False,
                'error': f'Custom tool not found: {tool_name}'
            }
        
        # Get tool metadata
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return {
                'valid': False,
                'error': f'Failed to get metadata for tool: {tool_name}'
            }
        
        # Validate arguments
        return self._validate_arguments(tool_name, args, metadata)
    
    def get_tool_timeout(self, tool_name: str) -> int:
        """
        Get timeout for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Timeout in seconds (default: 30)
        """
        metadata = self.registry.get_tool_metadata(tool_name)
        if metadata:
            return metadata.timeout_seconds
        return 30
    
    def is_custom_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is a custom tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if custom tool
        """
        return self.registry.tool_exists(tool_name)
    
    def list_custom_tools(self, category: Optional[str] = None) -> list:
        """
        List all custom tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool metadata dicts
        """
        tools = self.registry.list_tools(category)
        return [t.to_dict() for t in tools]
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a tool for live updates.
        
        Args:
            tool_name: Name of tool to reload
            
        Returns:
            True if reloaded successfully
        """
        return self.registry.reload_tool(tool_name)