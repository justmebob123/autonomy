#!/usr/bin/env python3
"""
TestTool - A test tool for demonstration

Auto-generated custom tool.
"""

from pathlib import Path
from core.base import BaseTool, ToolResult


class TestTool(BaseTool):
    """A test tool for demonstration"""
    
    # Tool metadata
    name = "test_tool"
    description = "A test tool for demonstration"
    version = "1.0.0"
    category = "testing"
    author = "Test Suite"
    
    # Security settings
    requires_filesystem = False
    requires_network = False
    requires_subprocess = False
    timeout_seconds = 10
    max_file_size_mb = 10
    
    def execute(self, input_text: str, count: int) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            input_text: input_text parameter
            count: count parameter
            
        Returns:
            ToolResult with success, result, error, metadata
        """
        try:
            # TODO: Implement your tool logic here
            
            # Example: Process parameters
            result_data = {
                'message': 'Tool executed successfully',
                'parameters': locals()
            }
            
            # Return success
            return ToolResult(
                success=True,
                result=result_data,
                metadata={
                    'tool_name': self.name,
                    'version': self.version
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {e}"
            )


# CLI interface for subprocess execution
if __name__ == '__main__':
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-dir', required=True)
    parser.add_argument('--args', required=True)
    args = parser.parse_args()
    
    # Parse arguments
    tool_args = json.loads(args.args)
    
    # Create and run tool
    tool = TestTool(args.project_dir)
    result = tool.run(**tool_args)
    
    # Output result as JSON
    print(json.dumps(result.to_dict()))
    sys.exit(0 if result.success else 1)
