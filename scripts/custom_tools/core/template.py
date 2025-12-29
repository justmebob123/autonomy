#!/usr/bin/env python3
"""
Tool Template Generator - Creates tool scaffolding.

Generates complete, working tool code from specifications.
"""

from typing import Dict, Optional, Any


TOOL_TEMPLATE = '''#!/usr/bin/env python3
"""
{name} - {description}

Auto-generated custom tool.

Category: {category}
Version: {version}
Author: {author}
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base import BaseTool, ToolResult


class {class_name}(BaseTool):
    """
    {description}
    
    Parameters:
{param_docs}
    
    Returns:
        ToolResult with success, result, error, metadata
    
    Usage:
        {usage}
    
    Examples:
{examples_docs}
    """
    
    # Tool metadata
    name = "{name}"
    description = "{description}"
    version = "{version}"
    category = "{category}"
    author = "{author}"
    
    # Security settings
    requires_filesystem = {requires_filesystem}
    requires_network = {requires_network}
    requires_subprocess = {requires_subprocess}
    timeout_seconds = {timeout}
    max_file_size_mb = {max_file_size}
    
    def validate_inputs(self, **kwargs) -> tuple:
        """
        Validate tool inputs.
        
        Returns:
            (is_valid, error_message)
        """
{validation_code}
        
        return True, None
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult
        """
        try:
{implementation_code}
            
            return ToolResult(
                success=True,
                result=result,
                metadata={{
                    "tool": self.name,
                    "version": self.version
                }}
            )
            
        except FileNotFoundError as e:
            return ToolResult(
                success=False,
                error=f"File not found: {{e}}"
            )
        
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=f"Permission denied: {{e}}"
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution failed: {{e}}"
            )


def main():
    """CLI entry point for subprocess execution."""
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("--project-dir", required=True, help="Project directory")
    parser.add_argument("--args", required=True, help="Tool arguments (JSON)")
    
    args = parser.parse_args()
    
    try:
        # Parse arguments
        tool_args = json.loads(args.args)
        
        # Execute tool
        tool = {class_name}(args.project_dir)
        result = tool.run(**tool_args)
        
        # Output result as JSON
        output = result.to_dict()
        print(json.dumps(output))
        
        sys.exit(0 if result.success else 1)
    
    except json.JSONDecodeError as e:
        print(json.dumps({{
            "success": False,
            "error": f"Invalid arguments JSON: {{e}}"
        }}))
        sys.exit(1)
    
    except Exception as e:
        print(json.dumps({{
            "success": False,
            "error": f"Tool initialization failed: {{e}}"
        }}))
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


class TemplateGenerator:
    """
    Generates tool code from specifications.
    
    Creates complete, working tool code following BaseTool pattern.
    """
    
    @staticmethod
    def generate(
        name: str,
        description: str,
        parameters: Dict[str, str],
        usage: str = "",
        examples: list = None,
        category: str = "utility",
        requires_filesystem: bool = False,
        requires_network: bool = False,
        requires_subprocess: bool = False,
        timeout: int = 30,
        max_file_size: int = 10,
        author: str = "AI",
        version: str = "1.0.0"
    ) -> str:
        """
        Generate tool code from template.
        
        Args:
            name: Tool name (verb_noun format)
            description: Tool description
            parameters: Parameter descriptions {param_name: description}
            usage: Usage description
            examples: List of example usage strings
            category: Tool category
            requires_filesystem: Whether tool needs filesystem access
            requires_network: Whether tool needs network access
            requires_subprocess: Whether tool needs subprocess
            timeout: Timeout in seconds
            max_file_size: Max file size in MB
            author: Tool author
            version: Tool version
            
        Returns:
            Generated tool code
        """
        # Generate class name (CamelCase)
        class_name = ''.join(word.capitalize() for word in name.split('_'))
        
        # Generate parameter documentation
        if parameters:
            param_docs = '\n'.join(
                f"        {param}: {desc}"
                for param, desc in parameters.items()
            )
        else:
            param_docs = "        No parameters"
        
        # Generate examples documentation
        if examples:
            examples_docs = '\n'.join(
                f"        {example}"
                for example in examples
            )
        else:
            examples_docs = "        No examples provided"
        
        # Generate validation code
        validation_lines = []
        for param in parameters.keys():
            validation_lines.append(f"        if '{param}' not in kwargs:")
            validation_lines.append(f"            return False, '{param} is required'")
        
        if validation_lines:
            validation_code = '\n'.join(validation_lines)
        else:
            validation_code = "        pass  # No required parameters"
        
        # Generate implementation placeholder
        param_list = ', '.join(parameters.keys()) if parameters else 'No parameters'
        implementation_code = f"""            # TODO: Implement tool logic here
            # Available parameters: {param_list}
            
            # Example implementation:
            # 1. Extract parameters
{TemplateGenerator._generate_param_extraction(parameters)}
            
            # 2. Perform operation
            # result_data = perform_operation(...)
            
            # 3. Return result
            result = {{
                "message": "Tool executed successfully",
                "parameters": kwargs,
                "note": "This is a template - implement actual logic here"
            }}"""
        
        # Fill template
        return TOOL_TEMPLATE.format(
            name=name,
            description=description,
            class_name=class_name,
            param_docs=param_docs,
            usage=usage or f"Use {name} when you need to {description.lower()}",
            examples_docs=examples_docs,
            category=category,
            version=version,
            author=author,
            requires_filesystem=str(requires_filesystem),
            requires_network=str(requires_network),
            requires_subprocess=str(requires_subprocess),
            timeout=timeout,
            max_file_size=max_file_size,
            validation_code=validation_code,
            implementation_code=implementation_code
        )
    
    @staticmethod
    def _generate_param_extraction(parameters: Dict[str, str]) -> str:
        """Generate parameter extraction code."""
        if not parameters:
            return "            # No parameters to extract"
        
        lines = []
        for param in parameters.keys():
            lines.append(f"            {param} = kwargs.get('{param}')")
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate_spec(
        name: str,
        description: str,
        parameters: Dict[str, str],
        category: str = "utility",
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Generate tool specification (for registry.json).
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Parameter descriptions
            category: Tool category
            version: Tool version
            
        Returns:
            Tool specification dict
        """
        return {
            "name": name,
            "description": description,
            "version": version,
            "category": category,
            "parameters": {
                param_name: {
                    "type": "string",  # Default to string, can be refined
                    "description": param_desc
                }
                for param_name, param_desc in parameters.items()
            },
            "returns": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "result": {"type": "object"},
                    "error": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            }
        }