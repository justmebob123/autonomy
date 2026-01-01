"""
CustomToolRegistry - Custom Tool Discovery and Registration

Automatically discovers and registers custom tools from scripts/custom_tools/tools/
Provides tool metadata, definitions, and management.
"""

import ast
import re
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging
import time

from pipeline.logging_setup import get_logger


@dataclass
class ToolMetadata:
    """Metadata for a custom tool."""
    name: str
    description: str
    version: str
    category: str
    author: str
    filepath: Path
    timeout_seconds: int
    requires_filesystem: bool
    requires_network: bool
    requires_subprocess: bool
    max_file_size_mb: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    last_modified: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'category': self.category,
            'author': self.author,
            'filepath': str(self.filepath),
            'timeout_seconds': self.timeout_seconds,
            'security': {
                'requires_filesystem': self.requires_filesystem,
                'requires_network': self.requires_network,
                'requires_subprocess': self.requires_subprocess,
                'max_file_size_mb': self.max_file_size_mb,
            },
            'parameters': self.parameters,
            'last_modified': self.last_modified,
        }


class CustomToolRegistry:
    """
    Registry for custom tools.
    
    Discovers, registers, and manages custom tools from scripts/custom_tools/tools/
    Provides tool metadata, definitions, and caching.
    
    Example:
        registry = CustomToolRegistry('/project')
        registry.discover_tools()
        
        # Get tool metadata
        metadata = registry.get_tool_metadata('analyze_imports')
        
        # Get OpenAI-compatible definition
        definition = registry.get_tool_definition('analyze_imports')
        
        # List all tools
        tools = registry.list_tools()
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize tool registry.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        # Tools directory - ALWAYS use pipeline's own scripts directory
        # Custom tools are part of the pipeline, not the project being worked on
        pipeline_root = Path(__file__).parent.parent.parent  # Go up from pipeline/custom_tools/registry.py to autonomy/
        self.tools_dir = pipeline_root / 'scripts' / 'custom_tools' / 'tools'
        
        # Registry cache
        self._tools: Dict[str, ToolMetadata] = {}
        self._definitions_cache: Dict[str, Dict[str, Any]] = {}
        self._last_scan: float = 0.0
        self._scan_interval: float = 5.0  # Rescan every 5 seconds
        
        self.logger.info(f"CustomToolRegistry initialized with tools_dir: {self.tools_dir}")
    
    def discover_tools(self, force: bool = False) -> int:
        """
        Discover all custom tools in tools directory.
        
        Args:
            force: Force rescan even if recently scanned
            
        Returns:
            Number of tools discovered
        """
        # Check if we need to rescan
        current_time = time.time()
        if not force and (current_time - self._last_scan) < self._scan_interval:
            self.logger.debug("Skipping tool discovery (recently scanned)")
            return len(self._tools)
        
        self.logger.info("Discovering custom tools...")
        start_time = time.time()
        
        # Clear cache
        self._tools.clear()
        self._definitions_cache.clear()
        
        # Check if tools directory exists
        if not self.tools_dir.exists():
            self.logger.warning(f"Tools directory not found: {self.tools_dir}")
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            return 0
        
        # Scan for tool files
        discovered = 0
        for tool_file in self.tools_dir.glob('*.py'):
            # Skip private files
            if tool_file.name.startswith('_'):
                continue
            
            try:
                metadata = self._extract_tool_metadata(tool_file)
                if metadata:
                    self._tools[metadata.name] = metadata
                    discovered += 1
                    self.logger.debug(f"Discovered tool: {metadata.name} ({metadata.category})")
            except Exception as e:
                self.logger.warning(f"Failed to extract metadata from {tool_file}: {e}")
        
        self._last_scan = current_time
        elapsed = time.time() - start_time
        
        self.logger.info(f"Discovered {discovered} custom tools in {elapsed*1000:.1f}ms")
        return discovered
    
    def _extract_tool_metadata(self, tool_file: Path) -> Optional[ToolMetadata]:
        """
        Extract metadata from a tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            ToolMetadata or None if extraction failed
        """
        try:
            content = tool_file.read_text()
            
            # Parse file to find class definition
            tree = ast.parse(content)
            
            # Find tool class (should inherit from BaseTool)
            tool_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if inherits from BaseTool
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'BaseTool':
                            tool_class = node
                            break
                    if tool_class:
                        break
            
            if not tool_class:
                self.logger.debug(f"No BaseTool class found in {tool_file}")
                return None
            
            # Extract class attributes
            name = self._extract_class_attribute(tool_class, 'name', content)
            description = self._extract_class_attribute(tool_class, 'description', content)
            version = self._extract_class_attribute(tool_class, 'version', content)
            category = self._extract_class_attribute(tool_class, 'category', content)
            author = self._extract_class_attribute(tool_class, 'author', content)
            
            # Extract security settings
            timeout = self._extract_class_attribute(tool_class, 'timeout_seconds', content, default=30)
            requires_fs = self._extract_class_attribute(tool_class, 'requires_filesystem', content, default=False)
            requires_net = self._extract_class_attribute(tool_class, 'requires_network', content, default=False)
            requires_proc = self._extract_class_attribute(tool_class, 'requires_subprocess', content, default=False)
            max_size = self._extract_class_attribute(tool_class, 'max_file_size_mb', content, default=10)
            
            # Extract parameters from execute() method
            parameters = self._extract_parameters(tool_class, content)
            
            # Get file modification time
            last_modified = tool_file.stat().st_mtime
            
            if not name:
                self.logger.warning(f"Tool {tool_file} missing 'name' attribute")
                return None
            
            return ToolMetadata(
                name=name,
                description=description or '',
                version=version or '1.0.0',
                category=category or 'utility',
                author=author or 'Unknown',
                filepath=tool_file,
                timeout_seconds=int(timeout) if timeout else 30,
                requires_filesystem=bool(requires_fs),
                requires_network=bool(requires_net),
                requires_subprocess=bool(requires_proc),
                max_file_size_mb=int(max_size) if max_size else 10,
                parameters=parameters,
                last_modified=last_modified,
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {tool_file}: {e}")
            return None
    
    def _extract_class_attribute(self, class_node: ast.ClassDef, attr_name: str, 
                                 content: str, default: Any = None) -> Any:
        """Extract class attribute value."""
        # Look for attribute in class body
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        # Get value
                        if isinstance(node.value, ast.Constant):
                            return node.value.value
                        elif isinstance(node.value, ast.Str):
                            return node.value.s
                        elif isinstance(node.value, ast.Num):
                            return node.value.n
                        elif isinstance(node.value, (ast.NameConstant, ast.Constant)):
                            return node.value.value
        
        # Fallback to regex
        pattern = rf'{attr_name}\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        
        # Try numeric pattern
        pattern = rf'{attr_name}\s*=\s*(\d+)'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1))
        
        # Try boolean pattern
        pattern = rf'{attr_name}\s*=\s*(True|False)'
        match = re.search(pattern, content)
        if match:
            return match.group(1) == 'True'
        
        return default
    
    def _extract_parameters(self, class_node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Extract parameters from execute() method signature."""
        parameters = {}
        
        # Find execute() method
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'execute':
                # Extract parameters from signature
                for arg in node.args.args:
                    if arg.arg == 'self' or arg.arg == 'kwargs':
                        continue
                    
                    # Get parameter name
                    param_name = arg.arg
                    
                    # Try to get type annotation
                    param_type = 'string'  # Default
                    if arg.annotation:
                        if isinstance(arg.annotation, ast.Name):
                            type_name = arg.annotation.id
                            if type_name == 'str':
                                param_type = 'string'
                            elif type_name == 'int':
                                param_type = 'integer'
                            elif type_name == 'bool':
                                param_type = 'boolean'
                            elif type_name == 'float':
                                param_type = 'number'
                            elif type_name == 'list' or type_name == 'List':
                                param_type = 'array'
                            elif type_name == 'dict' or type_name == 'Dict':
                                param_type = 'object'
                    
                    # Try to extract description from docstring
                    param_desc = f"{param_name} parameter"
                    if node.body and isinstance(node.body[0], ast.Expr):
                        if isinstance(node.body[0].value, (ast.Str, ast.Constant)):
                            docstring = node.body[0].value.s if isinstance(node.body[0].value, ast.Str) else node.body[0].value.value
                            # Look for parameter description in docstring
                            pattern = rf'{param_name}[:\s]+([^\n]+)'
                            match = re.search(pattern, docstring, re.IGNORECASE)
                            if match:
                                param_desc = match.group(1).strip()
                    
                    parameters[param_name] = {
                        'type': param_type,
                        'description': param_desc
                    }
                
                break
        
        return parameters
    
    def register_tool(self, metadata: ToolMetadata) -> bool:
        """
        Register a tool manually.
        
        Args:
            metadata: Tool metadata
            
        Returns:
            True if registered successfully
        """
        try:
            self._tools[metadata.name] = metadata
            # Clear cached definition
            if metadata.name in self._definitions_cache:
                del self._definitions_cache[metadata.name]
            self.logger.info(f"Registered tool: {metadata.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register tool {metadata.name}: {e}")
            return False
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolMetadata or None if not found
        """
        # Auto-discover if not found
        if tool_name not in self._tools:
            self.discover_tools()
        
        return self._tools.get(tool_name)
    
    def get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool definition.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool definition dict or None if not found
        """
        # Check cache
        if tool_name in self._definitions_cache:
            return self._definitions_cache[tool_name]
        
        # Get metadata
        metadata = self.get_tool_metadata(tool_name)
        if not metadata:
            return None
        
        # Generate definition
        definition = {
            'type': 'function',
            'function': {
                'name': metadata.name,
                'description': metadata.description,
                'parameters': {
                    'type': 'object',
                    'properties': metadata.parameters,
                    'required': list(metadata.parameters.keys())
                }
            }
        }
        
        # Cache definition
        self._definitions_cache[tool_name] = definition
        
        return definition
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolMetadata]:
        """
        List all registered tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of ToolMetadata
        """
        # Auto-discover if empty
        if not self._tools:
            self.discover_tools()
        
        tools = list(self._tools.values())
        
        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    def get_tool_categories(self) -> Set[str]:
        """
        Get all tool categories.
        
        Returns:
            Set of category names
        """
        # Auto-discover if empty
        if not self._tools:
            self.discover_tools()
        
        return {t.category for t in self._tools.values()}
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a tool (for live updates).
        
        Args:
            tool_name: Name of tool to reload
            
        Returns:
            True if reloaded successfully
        """
        try:
            # Get current metadata
            metadata = self._tools.get(tool_name)
            if not metadata:
                self.logger.warning(f"Tool {tool_name} not found for reload")
                return False
            
            # Check if file was modified
            current_mtime = metadata.filepath.stat().st_mtime
            if current_mtime <= metadata.last_modified:
                self.logger.debug(f"Tool {tool_name} not modified, skipping reload")
                return True
            
            # Re-extract metadata
            new_metadata = self._extract_tool_metadata(metadata.filepath)
            if not new_metadata:
                self.logger.error(f"Failed to reload tool {tool_name}")
                return False
            
            # Update registry
            self._tools[tool_name] = new_metadata
            
            # Clear cached definition
            if tool_name in self._definitions_cache:
                del self._definitions_cache[tool_name]
            
            self.logger.info(f"Reloaded tool: {tool_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload tool {tool_name}: {e}")
            return False
    
    def tool_exists(self, tool_name: str) -> bool:
        """
        Check if a tool exists.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool exists
        """
        # Auto-discover if empty
        if not self._tools:
            self.discover_tools()
        
        return tool_name in self._tools
    
    def get_tools_for_phase(self, phase: str) -> List[Dict[str, Any]]:
        """
        Get tool definitions for a specific phase.
        
        Args:
            phase: Phase name (e.g., 'coding', 'analysis')
            
        Returns:
            List of tool definitions
        """
        # Auto-discover if empty
        if not self._tools:
            self.discover_tools()
        
        # Get tools matching phase category
        definitions = []
        for tool in self._tools.values():
            if tool.category == phase or tool.category == 'utility':
                definition = self.get_tool_definition(tool.name)
                if definition:
                    definitions.append(definition)
        
        return definitions
    
    def clear_cache(self):
        """Clear all caches."""
        self._definitions_cache.clear()
        self._last_scan = 0.0
        self.logger.debug("Tool registry cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Statistics dict
        """
        # Auto-discover if empty
        if not self._tools:
            self.discover_tools()
        
        categories = {}
        for tool in self._tools.values():
            categories[tool.category] = categories.get(tool.category, 0) + 1
        
        return {
            'total_tools': len(self._tools),
            'categories': categories,
            'tools_dir': str(self.tools_dir),
            'last_scan': self._last_scan,
            'cache_size': len(self._definitions_cache),
        }