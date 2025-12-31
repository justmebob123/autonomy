"""
ToolDeveloper - Tool Creation and Testing Support

Supports tool creation, validation, and testing for custom tools.
"""

import ast
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from pipeline.logging_setup import get_logger


class ToolDeveloper:
    """
    Developer support for custom tools.
    
    Provides functionality for:
    - Creating tools from templates
    - Validating tool structure
    - Testing tools
    - Generating documentation
    
    Example:
        developer = ToolDeveloper('/project')
        
        # Create new tool
        developer.create_from_template('my_tool', {
            'description': 'My custom tool',
            'category': 'utility',
            'parameters': {'input': 'string'}
        })
        
        # Validate tool
        result = developer.validate_tool('my_tool')
        
        # Test tool
        test_result = developer.test_tool('my_tool', {'input': 'test'})
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize tool developer.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Tools directory
        if (self.project_dir / 'scripts' / 'custom_tools' / 'tools').exists():
            self.tools_dir = self.project_dir / 'scripts' / 'custom_tools' / 'tools'
        elif (self.project_dir.parent / 'scripts' / 'custom_tools' / 'tools').exists():
            self.tools_dir = self.project_dir.parent / 'scripts' / 'custom_tools' / 'tools'
        else:
            self.tools_dir = self.project_dir / 'scripts' / 'custom_tools' / 'tools'
        
        # Templates directory
        self.templates_dir = self.tools_dir.parent / 'core'
        
        self.logger.info(f"ToolDeveloper initialized with tools_dir: {self.tools_dir}")
    
    def create_from_template(self, tool_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tool from template.
        
        Args:
            tool_name: Name of the tool to create
            config: Tool configuration with:
                - description: Tool description
                - category: Tool category
                - parameters: Dict of parameters
                - author: Tool author (optional)
                - requires_filesystem: bool (optional)
                - requires_network: bool (optional)
                - timeout_seconds: int (optional)
                
        Returns:
            Result dict with success, filepath, message
        """
        try:
            # Validate tool name
            if not tool_name.isidentifier():
                return {
                    'success': False,
                    'error': f"Invalid tool name: {tool_name}. Must be valid Python identifier."
                }
            
            # Check if tool already exists
            tool_file = self.tools_dir / f"{tool_name}.py"
            if tool_file.exists():
                return {
                    'success': False,
                    'error': f"Tool already exists: {tool_file}"
                }
            
            # Ensure tools directory exists
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate tool code
            tool_code = self._generate_tool_code(tool_name, config)
            
            # Write tool file
            tool_file.write_text(tool_code)
            
            self.logger.info(f"Created tool: {tool_name} at {tool_file}")
            
            return {
                'success': True,
                'filepath': str(tool_file),
                'message': f"Tool '{tool_name}' created successfully",
                'tool_name': tool_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create tool {tool_name}: {e}")
            return {
                'success': False,
                'error': f"Tool creation failed: {e}"
            }
    
    def _generate_tool_code(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate tool code from configuration."""
        # Extract config
        description = config.get('description', 'Custom tool')
        category = config.get('category', 'utility')
        author = config.get('author', 'AI')
        parameters = config.get('parameters', {})
        requires_fs = config.get('requires_filesystem', False)
        requires_net = config.get('requires_network', False)
        requires_proc = config.get('requires_subprocess', False)
        timeout = config.get('timeout_seconds', 30)
        
        # Generate class name (CamelCase)
        class_name = ''.join(word.capitalize() for word in tool_name.split('_'))
        
        # Generate parameter signature
        param_list = []
        param_docs = []
        for param_name, param_type in parameters.items():
            if isinstance(param_type, str):
                param_list.append(f"{param_name}: {param_type}")
                param_docs.append(f"            {param_name}: {param_name} parameter")
            else:
                param_list.append(f"{param_name}: str")
                param_docs.append(f"            {param_name}: {param_name} parameter")
        
        param_signature = ', '.join(param_list) if param_list else '**kwargs'
        param_doc_str = '\n'.join(param_docs) if param_docs else '            **kwargs: Tool parameters'
        
        # Generate tool code
        code = f'''#!/usr/bin/env python3
"""
{class_name} - {description}

Auto-generated custom tool.
"""

from pathlib import Path
from core.base import BaseTool, ToolResult


class {class_name}(BaseTool):
    """{description}"""
    
    # Tool metadata
    name = "{tool_name}"
    description = "{description}"
    version = "1.0.0"
    category = "{category}"
    author = "{author}"
    
    # Security settings
    requires_filesystem = {requires_fs}
    requires_network = {requires_net}
    requires_subprocess = {requires_proc}
    timeout_seconds = {timeout}
    max_file_size_mb = 10
    
    def execute(self, {param_signature}) -> ToolResult:
        """
        Execute the tool.
        
        Args:
{param_doc_str}
            
        Returns:
            ToolResult with success, result, error, metadata
        """
        try:
            # TODO: Implement your tool logic here
            
            # Example: Process parameters
            result_data = {{
                'message': 'Tool executed successfully',
                'parameters': locals()
            }}
            
            # Return success
            return ToolResult(
                success=True,
                result=result_data,
                metadata={{
                    'tool_name': self.name,
                    'version': self.version
                }}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {{e}}"
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
    tool = {class_name}(args.project_dir)
    result = tool.run(**tool_args)
    
    # Output result as JSON
    print(json.dumps(result.to_dict()))
    sys.exit(0 if result.success else 1)
'''
        
        return code
    
    def validate_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Validate a tool's structure and code.
        
        Args:
            tool_name: Name of the tool to validate
            
        Returns:
            Validation result with success, errors, warnings
        """
        try:
            tool_file = self.tools_dir / f"{tool_name}.py"
            
            if not tool_file.exists():
                return {
                    'success': False,
                    'errors': [f"Tool file not found: {tool_file}"]
                }
            
            # Read tool code
            code = tool_file.read_text()
            
            errors = []
            warnings = []
            
            # Check 1: Valid Python syntax
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Syntax error: {e}")
                return {
                    'success': False,
                    'errors': errors,
                    'warnings': warnings
                }
            
            # Check 2: Has BaseTool import
            has_base_import = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == 'core.base':
                        has_base_import = True
                        break
            
            if not has_base_import:
                errors.append("Missing import: from core.base import BaseTool, ToolResult")
            
            # Check 3: Has class inheriting from BaseTool
            tool_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'BaseTool':
                            tool_class = node
                            break
                    if tool_class:
                        break
            
            if not tool_class:
                errors.append("No class inheriting from BaseTool found")
                return {
                    'success': False,
                    'errors': errors,
                    'warnings': warnings
                }
            
            # Check 4: Has required attributes
            required_attrs = ['name', 'description', 'version', 'category']
            found_attrs = set()
            
            for node in tool_class.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            found_attrs.add(target.id)
            
            missing_attrs = set(required_attrs) - found_attrs
            if missing_attrs:
                errors.append(f"Missing required attributes: {', '.join(missing_attrs)}")
            
            # Check 5: Has execute method
            has_execute = False
            for node in tool_class.body:
                if isinstance(node, ast.FunctionDef) and node.name == 'execute':
                    has_execute = True
                    
                    # Check execute returns ToolResult
                    if node.returns:
                        if isinstance(node.returns, ast.Name):
                            if node.returns.id != 'ToolResult':
                                warnings.append("execute() should return ToolResult")
            
            if not has_execute:
                errors.append("Missing execute() method")
            
            # Check 6: Has CLI interface
            has_main = False
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    if isinstance(node.test, ast.Compare):
                        if isinstance(node.test.left, ast.Name):
                            if node.test.left.id == '__name__':
                                has_main = True
                                break
            
            if not has_main:
                warnings.append("Missing CLI interface (if __name__ == '__main__':)")
            
            # Return validation result
            if errors:
                return {
                    'success': False,
                    'errors': errors,
                    'warnings': warnings
                }
            else:
                return {
                    'success': True,
                    'errors': [],
                    'warnings': warnings,
                    'message': f"Tool '{tool_name}' is valid"
                }
                
        except Exception as e:
            self.logger.error(f"Tool validation failed: {e}")
            return {
                'success': False,
                'errors': [f"Validation failed: {e}"]
            }
    
    def test_tool(self, tool_name: str, test_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to test
            test_args: Arguments to pass to tool
            
        Returns:
            Test result with success, output, errors
        """
        try:
            # First validate the tool
            validation = self.validate_tool(tool_name)
            if not validation['success']:
                return {
                    'success': False,
                    'error': 'Tool validation failed',
                    'validation_errors': validation['errors']
                }
            
            # Execute tool using subprocess
            import subprocess
            import sys
            
            tool_file = self.tools_dir / f"{tool_name}.py"
            
            cmd = [
                sys.executable,
                str(tool_file),
                '--project-dir', str(self.project_dir),
                '--args', json.dumps(test_args)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    return {
                        'success': True,
                        'output': output,
                        'message': f"Tool '{tool_name}' test passed"
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Tool returned invalid JSON',
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'success': False,
                    'error': f"Tool exited with code {result.returncode}",
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Tool execution timed out'
            }
        except Exception as e:
            self.logger.error(f"Tool test failed: {e}")
            return {
                'success': False,
                'error': f"Test failed: {e}"
            }
    
    def generate_docs(self, tool_name: str) -> Dict[str, Any]:
        """
        Generate documentation for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Result with success, documentation
        """
        try:
            from .registry import CustomToolRegistry
            from .definition import ToolDefinitionGenerator
            
            # Get tool metadata
            registry = CustomToolRegistry(str(self.project_dir))
            registry.discover_tools(force=True)
            
            generator = ToolDefinitionGenerator(registry)
            docs = generator.get_tool_documentation(tool_name)
            
            if docs:
                # Save to file
                docs_file = self.tools_dir / f"{tool_name}_README.md"
                docs_file.write_text(docs)
                
                return {
                    'success': True,
                    'documentation': docs,
                    'filepath': str(docs_file),
                    'message': f"Documentation generated for '{tool_name}'"
                }
            else:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not found"
                }
                
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {
                'success': False,
                'error': f"Documentation generation failed: {e}"
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all custom tools.
        
        Returns:
            List of tool information dicts
        """
        tools = []
        
        if not self.tools_dir.exists():
            return tools
        
        for tool_file in self.tools_dir.glob('*.py'):
            if tool_file.name.startswith('_'):
                continue
            
            tool_name = tool_file.stem
            validation = self.validate_tool(tool_name)
            
            tools.append({
                'name': tool_name,
                'filepath': str(tool_file),
                'valid': validation['success'],
                'errors': validation.get('errors', []),
                'warnings': validation.get('warnings', [])
            })
        
        return tools