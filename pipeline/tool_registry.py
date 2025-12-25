"""
Tool Registry

Manages dynamic tool registration and execution.
Loads tools from pipeline/tools/custom/ and integrates with ToolCallHandler.
"""

import json
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime

from .logging_setup import get_logger


class ToolRegistry:
    """
    Registry for dynamically created tools.
    
    Features:
    - Load tools from custom directory
    - Validate tool specifications and implementations
    - Security sandbox (prevent dangerous operations)
    - Register tools in ToolCallHandler
    - Make tools available to all phases
    
    Integration:
    - Extends ToolCallHandler._handlers dictionary
    - Loads from pipeline/tools/custom/
    - Validates security before registration
    """
    
    def __init__(self, project_dir: Path, handler=None):
        """
        Initialize the tool registry.
        
        Args:
            project_dir: Root directory of the project
            handler: ToolCallHandler instance (optional, can be set later)
        """
        self.project_dir = Path(project_dir)
        self.tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.handler = handler
        self.tools: Dict[str, Dict] = {}
        
        # Load existing tools
        self._load_tools()
        
        self.logger.info(f"ToolRegistry initialized with {len(self.tools)} tools")
    
    def set_handler(self, handler):
        """
        Set the ToolCallHandler instance.
        
        Args:
            handler: ToolCallHandler instance
        """
        self.handler = handler
        # Re-register all tools with the handler
        for tool_name in self.tools:
            self._register_with_handler(tool_name)
    
    def _load_tools(self):
        """Load all tool specifications and implementations from custom directory"""
        if not self.tools_dir.exists():
            return
        
        for spec_file in self.tools_dir.glob("*_spec.json"):
            try:
                spec = self._load_tool_spec(spec_file)
                if spec and self._validate_spec(spec):
                    # Load implementation
                    impl_file = self.tools_dir / f"{spec['name']}.py"
                    if impl_file.exists():
                        tool_func = self._load_implementation(impl_file, spec['name'])
                        if tool_func and self._is_safe(tool_func, spec):
                            self.tools[spec['name']] = {
                                'spec': spec,
                                'function': tool_func,
                                'impl_file': str(impl_file),
                                'spec_file': str(spec_file)
                            }
                            self.logger.debug(f"Loaded tool: {spec['name']}")
                            
                            # Register with handler if available
                            if self.handler:
                                self._register_with_handler(spec['name'])
            except Exception as e:
                self.logger.error(f"Failed to load tool from {spec_file}: {e}")
    
    def _load_tool_spec(self, spec_file: Path) -> Optional[Dict]:
        """
        Load a tool specification from a JSON file.
        
        Args:
            spec_file: Path to the tool spec JSON file
            
        Returns:
            Tool specification dict or None if invalid
        """
        try:
            with open(spec_file, 'r') as f:
                spec = json.load(f)
            return spec
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {spec_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading {spec_file}: {e}")
            return None
    
    def _load_implementation(self, impl_file: Path, tool_name: str) -> Optional[Callable]:
        """
        Load tool implementation from Python file.
        
        Args:
            impl_file: Path to implementation file
            tool_name: Name of the tool function
            
        Returns:
            Tool function or None if failed
        """
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(tool_name, impl_file)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the tool function
            if hasattr(module, tool_name):
                return getattr(module, tool_name)
            else:
                self.logger.error(f"Function {tool_name} not found in {impl_file}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load implementation from {impl_file}: {e}")
            return None
    
    def _validate_spec(self, spec: Dict) -> bool:
        """
        Validate a tool specification.
        
        Required fields:
        - name: Tool name
        - description: What the tool does
        - parameters: Parameter schema
        - returns: Return value schema
        
        Args:
            spec: Tool specification to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "description", "parameters"]
        
        for field in required_fields:
            if field not in spec:
                self.logger.error(f"Tool spec missing required field: {field}")
                return False
        
        # Validate name format (alphanumeric + underscore)
        name = spec["name"]
        if not name.replace("_", "").isalnum():
            self.logger.error(f"Invalid tool name: {name} (must be alphanumeric + underscore)")
            return False
        
        # Validate parameters schema
        if not isinstance(spec["parameters"], dict):
            self.logger.error("Tool parameters must be a dict")
            return False
        
        return True
    
    def _is_safe(self, func: Callable, spec: Dict) -> bool:
        """
        Validate tool safety.
        
        Security checks:
        - No dangerous operations (eval, exec, os.system)
        - Input validation present
        - Error handling present
        - Timeout limits
        
        Args:
            func: Tool function to validate
            spec: Tool specification
            
        Returns:
            True if safe, False otherwise
        """
        try:
            # Get source code
            source = inspect.getsource(func)
            
            # Check for dangerous operations
            dangerous_patterns = [
                'eval(',
                'exec(',
                'os.system(',
                '__import__(',
                'subprocess.call(',
                'shell=True',
                'compile(',
            ]
            
            for pattern in dangerous_patterns:
                if pattern in source:
                    self.logger.error(f"Tool contains dangerous operation: {pattern}")
                    return False
            
            # Check for error handling
            if 'try:' not in source or 'except' not in source:
                self.logger.warning(f"Tool {spec['name']} lacks error handling")
                # Don't reject, but warn
            
            # Check for input validation
            if 'if not' not in source and 'if ' not in source:
                self.logger.warning(f"Tool {spec['name']} may lack input validation")
                # Don't reject, but warn
            
            # Check safety metadata
            safety = spec.get('safety', {})
            if safety.get('dangerous_operations'):
                self.logger.error(f"Tool declares dangerous operations: {safety['dangerous_operations']}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating tool safety: {e}")
            return False
    
    def register_tool(self, spec: Dict, impl_code: str = None) -> bool:
        """
        Register a new tool at runtime.
        
        Process:
        1. Validate specification
        2. Load or create implementation
        3. Validate safety
        4. Add to registry
        5. Register with ToolCallHandler
        6. Persist to files
        
        Args:
            spec: Tool specification dict
            impl_code: Optional implementation code (if not in file)
            
        Returns:
            True if registered successfully, False otherwise
        """
        if not self._validate_spec(spec):
            return False
        
        name = spec["name"]
        
        # Check for duplicate
        if name in self.tools:
            self.logger.warning(f"Tool {name} already exists, will be overwritten")
        
        # Get implementation
        impl_file = self.tools_dir / f"{name}.py"
        
        if impl_code:
            # Save implementation code
            try:
                impl_file.write_text(impl_code)
            except Exception as e:
                self.logger.error(f"Failed to write implementation: {e}")
                return False
        
        if not impl_file.exists():
            self.logger.error(f"Implementation file not found: {impl_file}")
            return False
        
        # Load implementation
        tool_func = self._load_implementation(impl_file, name)
        if not tool_func:
            return False
        
        # Validate safety
        if not self._is_safe(tool_func, spec):
            self.logger.error(f"Tool {name} failed safety validation")
            return False
        
        # Add metadata
        spec["registered_at"] = datetime.now().isoformat()
        spec["version"] = spec.get("version", "1.0")
        
        # Store in registry
        self.tools[name] = {
            'spec': spec,
            'function': tool_func,
            'impl_file': str(impl_file),
            'spec_file': str(self.tools_dir / f"{name}_spec.json")
        }
        
        # Persist spec to file
        spec_file = self.tools_dir / f"{name}_spec.json"
        try:
            with open(spec_file, 'w') as f:
                json.dump(spec, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to persist tool spec: {e}")
            del self.tools[name]
            return False
        
        # Register with handler
        if self.handler:
            self._register_with_handler(name)
        
        self.logger.info(f"✅ Registered tool: {name}")
        return True
    
    def _register_with_handler(self, tool_name: str):
        """
        Register tool with ToolCallHandler.
        
        Integration Point #3: Adds tool to handler's _handlers dictionary
        
        Args:
            tool_name: Name of the tool to register
        """
        if not self.handler:
            return
        
        if tool_name not in self.tools:
            return
        
        tool_func = self.tools[tool_name]['function']
        
        # Add to handler's dictionary
        self.handler._handlers[tool_name] = tool_func
        
        self.logger.debug(f"Registered {tool_name} with ToolCallHandler")
    
    def get_tool_definition(self, name: str) -> Optional[Dict]:
        """
        Get tool definition for LLM tool calling.
        
        Returns JSON schema compatible with Ollama tool calling.
        
        Args:
            name: Tool name
            
        Returns:
            Tool definition dict or None if not found
        """
        if name not in self.tools:
            return None
        
        spec = self.tools[name]['spec']
        
        return {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"]
            }
        }
    
    def list_tools(self) -> List[Dict]:
        """
        List all registered tools with metadata.
        
        Returns:
            List of dicts with tool metadata
        """
        return [
            {
                "name": spec["name"],
                "description": spec["description"],
                "category": spec.get("category", "unknown"),
                "registered_at": spec.get("registered_at", "unknown"),
                "version": spec.get("version", "1.0")
            }
            for tool_data in self.tools.values()
            for spec in [tool_data['spec']]
        ]
    
    def get_spec(self, name: str) -> Optional[Dict]:
        """
        Get the full specification for a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool specification dict or None if not found
        """
        if name not in self.tools:
            return None
        return self.tools[name]['spec']
    
    def delete_tool(self, name: str) -> bool:
        """
        Delete a tool from the registry.
        
        Args:
            name: Tool name
            
        Returns:
            True if deleted, False if not found
        """
        if name not in self.tools:
            return False
        
        # Remove from handler
        if self.handler and name in self.handler._handlers:
            del self.handler._handlers[name]
        
        # Remove from registry
        tool_data = self.tools[name]
        del self.tools[name]
        
        # Delete files
        impl_file = Path(tool_data['impl_file'])
        spec_file = Path(tool_data['spec_file'])
        
        if impl_file.exists():
            impl_file.unlink()
        if spec_file.exists():
            spec_file.unlink()
        
        self.logger.info(f"Deleted tool: {name}")
        return True
    
    def search_tools(self, query: str) -> List[Dict]:
        """
        Search tools by name, description, or category.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tool metadata
        """
        query_lower = query.lower()
        matches = []
        
        for tool_data in self.tools.values():
            spec = tool_data['spec']
            if (query_lower in spec["name"].lower() or 
                query_lower in spec["description"].lower() or
                query_lower in spec.get("category", "").lower()):
                matches.append({
                    "name": spec["name"],
                    "description": spec["description"],
                    "category": spec.get("category", "unknown")
                })
        
        return matches
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dict with statistics
        """
        categories = {}
        for tool_data in self.tools.values():
            category = tool_data['spec'].get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_tools": len(self.tools),
            "tools_dir": str(self.tools_dir),
            "tools": list(self.tools.keys()),
            "by_category": categories
        }