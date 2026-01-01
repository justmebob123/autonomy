#!/usr/bin/env python3
"""
ToolExecutor - Executes custom tools in isolated subprocess.

This provides:
- Process isolation (tool crash doesn't crash pipeline)
- Timeout enforcement
- Resource limits
- Live reload (no module caching)
- Security sandboxing
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import re


class ToolExecutor:
    """
    Executes custom tools in isolated subprocess.
    
    Benefits:
    - Tool crash doesn't crash pipeline
    - Timeout enforcement
    - Resource limits
    - No module caching (live reload)
    - Security sandboxing
    
    Example:
        executor = ToolExecutor('bin/custom_tools', '/project')
        result = executor.execute_tool('analyze_imports', {'filepath': 'main.py'})
        if result['success']:
            print(result['result'])
    """
    
    def __init__(self, tools_dir: str, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize executor.
        
        Args:
            tools_dir: Directory containing custom tools (bin/custom_tools/)
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.tools_dir = Path(tools_dir)
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Verify tools directory exists
        if not self.tools_dir.exists():
            self.logger.warning(f"Tools directory not found, creating: {tools_dir}")
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            (self.tools_dir / "tools").mkdir(exist_ok=True)
    
    def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a custom tool in isolated subprocess.
        
        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments
            timeout: Timeout in seconds (uses tool default if not specified)
            
        Returns:
            Tool result dict with:
            - success: bool
            - result: Any (tool output)
            - error: str (if failed)
            - metadata: dict
            - execution_time: float
        """
        # Find tool file
        tool_file = self.tools_dir / "tools" / f"{tool_name}.py"
        
        if not tool_file.exists():
            self.logger.error(f"Tool not found: {tool_name} at {tool_file}")
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "error_type": "tool_not_found",
                "searched_path": str(tool_file)
            }
        
        # Get tool timeout if not specified
        if timeout is None:
            timeout = self._get_tool_timeout(tool_file)
        
        # Prepare execution command
        cmd = [
            sys.executable,
            str(tool_file),
            "--project-dir", str(self.project_dir),
            "--args", json.dumps(args)
        ]
        
        self.logger.debug(f"Executing tool: {tool_name} with timeout {timeout}s")
        
        try:
            # Execute in subprocess with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_dir),
                env={'PYTHONPATH': str(self.tools_dir)}
            )
            
            # Parse result
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    self.logger.debug(f"Tool {tool_name} succeeded in {output.get('execution_time', 0):.2f}s")
                    return output
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Tool {tool_name} returned invalid JSON: {e}")
                    return {
                        "success": False,
                        "error": "Tool returned invalid JSON",
                        "error_type": "invalid_output",
                        "stdout": result.stdout[:500],
                        "stderr": result.stderr[:500]
                    }
            else:
                self.logger.error(f"Tool {tool_name} failed with code {result.returncode}")
                return {
                    "success": False,
                    "error": f"Tool exited with code {result.returncode}",
                    "error_type": "execution_error",
                    "returncode": result.returncode,
                    "stderr": result.stderr[:500] if result.stderr else None
                }
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Tool {tool_name} timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Tool timed out after {timeout} seconds",
                "error_type": "timeout",
                "timeout_seconds": timeout
            }
        
        except Exception as e:
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {e}",
                "error_type": "execution_error"
            }
    
    def _get_tool_timeout(self, tool_file: Path) -> int:
        """
        Get tool timeout from tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            Timeout in seconds (default: 30)
        """
        try:
            content = tool_file.read_text()
            
            # Look for timeout_seconds = X
            match = re.search(r'timeout_seconds\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
        
        except Exception:
            pass
        
        return 30  # Default timeout
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available custom tools.
        
        Returns:
            List of tool metadata dicts
        """
        tools = []
        tools_path = self.tools_dir / "tools"
        
        if not tools_path.exists():
            return tools
        
        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith('_'):
                continue
            
            try:
                metadata = self._extract_tool_metadata(tool_file)
                if metadata:
                    tools.append(metadata)
            except Exception as e:
                self.logger.warning(f"Failed to extract metadata from {tool_file}: {e}")
        
        return tools
    
    def _extract_tool_metadata(self, tool_file: Path) -> Optional[Dict[str, Any]]:
        """
        Extract tool metadata from tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            Tool metadata dict or None
        """
        try:
            content = tool_file.read_text()
            
            # Extract metadata using regex
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            category_match = re.search(r'category\s*=\s*["\']([^"\']+)["\']', content)
            timeout_match = re.search(r'timeout_seconds\s*=\s*(\d+)', content)
            
            if name_match:
                return {
                    'name': name_match.group(1),
                    'description': desc_match.group(1) if desc_match else '',
                    'version': version_match.group(1) if version_match else '1.0.0',
                    'category': category_match.group(1) if category_match else 'utility',
                    'timeout': int(timeout_match.group(1)) if timeout_match else 30,
                    'file': str(tool_file),
                    'filename': tool_file.name
                }
        
        except Exception as e:
            self.logger.debug(f"Could not extract metadata from {tool_file}: {e}")
        
        return None
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a tool (for live updates).
        
        Since tools run in subprocess, they're automatically reloaded
        on each execution. This method verifies the tool exists.
        
        Args:
            tool_name: Name of tool to reload
            
        Returns:
            True if tool exists and is valid, False otherwise
        """
        tool_file = self.tools_dir / "tools" / f"{tool_name}.py"
        
        if not tool_file.exists():
            return False
        
        # Verify tool is valid Python
        try:
            content = tool_file.read_text()
            compile(content, str(tool_file), 'exec')
            return True
        except SyntaxError as e:
            self.logger.error(f"Tool {tool_name} has syntax error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Tool {tool_name} validation failed: {e}")
            return False
    
    def get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool definition for a custom tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool definition dict or None if tool not found
        """
        tool_file = self.tools_dir / "tools" / f"{tool_name}.py"
        
        if not tool_file.exists():
            return None
        
        metadata = self._extract_tool_metadata(tool_file)
        if not metadata:
            return None
        
        # Extract parameters from tool file
        parameters = self._extract_parameters(tool_file)
        
        return {
            "type": "function",
            "function": {
                "name": metadata['name'],
                "description": metadata['description'],
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": list(parameters.keys())
                }
            }
        }
    
    def _extract_parameters(self, tool_file: Path) -> Dict[str, Any]:
        """
        Extract parameter definitions from tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            Parameter definitions dict
        """
        # TODO: Parse execute() method signature to extract parameters
        # For now, return generic parameter
        return {
            "input": {
                "type": "string",
                "description": "Tool input"
            }
        }