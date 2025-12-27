"""
Tool Creator System

Automatically creates new tools when gaps are identified in the system's capabilities.

Analyzes:
- Failed tool calls (tools that don't exist)
- Repeated manual operations (could be automated)
- Common patterns (could be a tool)
- User requests (explicit tool needs)
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import re

from .logging_setup import get_logger


class ToolSpecification:
    """Specification for a new tool."""
    
    def __init__(self, name: str, description: str, parameters: Dict, 
                 implementation_hint: str = None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.implementation_hint = implementation_hint
        self.created_at = datetime.now()
        self.usage_count = 0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'implementation_hint': self.implementation_hint,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count
        }
    
    def to_tool_definition(self) -> Dict:
        """Convert to OpenAI tool definition format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': self.parameters,
                    'required': list(self.parameters.keys())
                }
            }
        }


class ToolCreator:
    """
    Automatically creates new tools based on identified needs.
    
    Monitors:
    - Unknown tool calls (model tries to use non-existent tool)
    - Repeated operations (could be automated)
    - Pattern-based needs (common sequences)
    - Explicit requests (user or model asks for tool)
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize tool creator.
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        
        # Tool specifications
        self.tool_specs = {}
        
        # Tool creation requests
        self.creation_requests = []
        
        # Unknown tool tracking
        self.unknown_tools = {}
        
        # Load existing specs
        self.load_tool_specs()
    
    def record_unknown_tool(self, tool_name: str, context: Dict):
        """
        Record an attempt to use an unknown tool.
        
        Args:
            tool_name: Name of the unknown tool
            context: Context of the attempt
        """
        if tool_name not in self.unknown_tools:
            self.unknown_tools[tool_name] = {
                'name': tool_name,
                'attempts': 0,
                'contexts': [],
                'first_seen': datetime.now().isoformat()
            }
        
        self.unknown_tools[tool_name]['attempts'] += 1
        self.unknown_tools[tool_name]['contexts'].append({
            'timestamp': datetime.now().isoformat(),
            'phase': context.get('phase', 'unknown'),
            'description': context.get('description', '')
        })
        
        self.logger.info(f"🔧 Unknown tool '{tool_name}' attempted (count: {self.unknown_tools[tool_name]['attempts']})")
        
        # If attempted multiple times, consider creating it
        if self.unknown_tools[tool_name]['attempts'] >= 3:
            self._propose_tool_creation(tool_name)
    
    def _propose_tool_creation(self, tool_name: str):
        """
        Propose creation of a new tool.
        
        Args:
            tool_name: Name of the tool to create
        """
        unknown_tool = self.unknown_tools[tool_name]
        
        # Analyze contexts to infer tool purpose
        contexts = unknown_tool['contexts']
        
        # Extract common patterns from contexts
        descriptions = [c.get('description', '') for c in contexts]
        
        # Infer parameters from tool name and contexts
        parameters = self._infer_parameters(tool_name, descriptions)
        
        # Create tool specification
        spec = ToolSpecification(
            name=tool_name,
            description=f"Auto-generated tool based on {len(contexts)} usage attempts",
            parameters=parameters,
            implementation_hint=f"Contexts: {descriptions[:3]}"
        )
        
        # Add to creation requests
        self.creation_requests.append({
            'spec': spec,
            'reason': 'unknown_tool_attempts',
            'attempts': unknown_tool['attempts'],
            'timestamp': datetime.now()
        })
        
        self.logger.info(f"💡 Proposed new tool: {tool_name}")
    
    def _infer_parameters(self, tool_name: str, descriptions: List[str]) -> Dict:
        """
        Infer tool parameters from name and usage contexts.
        
        Args:
            tool_name: Tool name
            descriptions: Usage descriptions
        
        Returns:
            Dict of parameter specifications
        """
        parameters = {}
        
        # Common parameter patterns
        if 'file' in tool_name.lower():
            parameters['file_path'] = {
                'type': 'string',
                'description': 'Path to the file'
            }
        
        if 'create' in tool_name.lower():
            parameters['content'] = {
                'type': 'string',
                'description': 'Content to create'
            }
        
        if 'search' in tool_name.lower() or 'find' in tool_name.lower():
            parameters['query'] = {
                'type': 'string',
                'description': 'Search query'
            }
        
        if 'update' in tool_name.lower() or 'modify' in tool_name.lower():
            parameters['changes'] = {
                'type': 'object',
                'description': 'Changes to apply'
            }
        
        # If no parameters inferred, add generic ones
        if not parameters:
            parameters['input'] = {
                'type': 'string',
                'description': 'Input for the tool'
            }
        
        return parameters
    
    def create_tool_from_pattern(self, pattern: Dict) -> Optional[ToolSpecification]:
        """
        Create a tool from a recognized pattern.
        
        Args:
            pattern: Pattern dict with tool sequence
        
        Returns:
            ToolSpecification if created, None otherwise
        """
        tool_sequence = pattern.get('tool_calls', [])
        
        if len(tool_sequence) < 2:
            return None
        
        # Create composite tool name
        tool_name = '_'.join(tool_sequence[:3])
        
        # Check if already exists
        if tool_name in self.tool_specs:
            return None
        
        # Create specification
        spec = ToolSpecification(
            name=tool_name,
            description=f"Composite tool combining: {', '.join(tool_sequence)}",
            parameters={
                'context': {
                    'type': 'object',
                    'description': 'Context for the operation'
                }
            },
            implementation_hint=f"Execute tools in sequence: {tool_sequence}"
        )
        
        self.tool_specs[tool_name] = spec
        self.logger.info(f"🔨 Created composite tool: {tool_name}")
        
        return spec
    
    def request_tool_creation(self, tool_name: str, description: str, 
                            parameters: Dict, requester: str = 'system'):
        """
        Explicitly request creation of a new tool.
        
        Args:
            tool_name: Name of the tool
            description: Tool description
            parameters: Tool parameters
            requester: Who requested the tool
        """
        spec = ToolSpecification(
            name=tool_name,
            description=description,
            parameters=parameters
        )
        
        self.creation_requests.append({
            'spec': spec,
            'reason': 'explicit_request',
            'requester': requester,
            'timestamp': datetime.now()
        })
        
        self.logger.info(f"📝 Tool creation requested: {tool_name} by {requester}")
    
    def get_pending_requests(self) -> List[Dict]:
        """
        Get pending tool creation requests.
        
        Returns:
            List of pending requests
        """
        return self.creation_requests
    
    def approve_tool_creation(self, request_index: int) -> Optional[ToolSpecification]:
        """
        Approve a tool creation request.
        
        Args:
            request_index: Index of the request to approve
        
        Returns:
            Created ToolSpecification if successful
        """
        if request_index >= len(self.creation_requests):
            return None
        
        request = self.creation_requests[request_index]
        spec = request['spec']
        
        # Add to tool specs
        self.tool_specs[spec.name] = spec
        
        # Remove from requests
        self.creation_requests.pop(request_index)
        
        # Save specs
        self.save_tool_specs()
        
        self.logger.info(f"✅ Approved tool creation: {spec.name}")
        
        return spec
    
    def get_tool_definitions(self) -> List[Dict]:
        """
        Get all tool definitions in OpenAI format.
        
        Returns:
            List of tool definitions
        """
        return [spec.to_tool_definition() for spec in self.tool_specs.values()]
    
    def get_statistics(self) -> Dict:
        """Get tool creator statistics."""
        return {
            'total_tools': len(self.tool_specs),
            'pending_requests': len(self.creation_requests),
            'unknown_tools': len(self.unknown_tools),
            'most_requested': sorted(
                self.unknown_tools.items(),
                key=lambda x: x[1]['attempts'],
                reverse=True
            )[:5]
        }
    
    def save_tool_specs(self):
        """Save tool specifications to disk."""
        specs_file = self.project_dir / '.pipeline' / 'tool_specs.json'
        specs_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'tool_specs': {
                name: spec.to_dict()
                for name, spec in self.tool_specs.items()
            },
            'unknown_tools': self.unknown_tools,
            'pending_requests': [
                {
                    'spec': req['spec'].to_dict(),
                    'reason': req['reason'],
                    'timestamp': req['timestamp'].isoformat() if hasattr(req['timestamp'], 'isoformat') else str(req['timestamp'])
                }
                for req in self.creation_requests
            ]
        }
        
        with open(specs_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"💾 Saved {len(self.tool_specs)} tool specifications")
    
    def load_tool_specs(self):
        """Load tool specifications from disk."""
        specs_file = self.project_dir / '.pipeline' / 'tool_specs.json'
        
        if not specs_file.exists():
            return
        
        try:
            with open(specs_file, 'r') as f:
                data = json.load(f)
            
            # Load tool specs
            for name, spec_data in data.get('tool_specs', {}).items():
                self.tool_specs[name] = ToolSpecification(
                    name=spec_data['name'],
                    description=spec_data['description'],
                    parameters=spec_data['parameters'],
                    implementation_hint=spec_data.get('implementation_hint')
                )
            
            # Load unknown tools
            self.unknown_tools = data.get('unknown_tools', {})
            
            self.logger.info(f"📂 Loaded {len(self.tool_specs)} tool specifications")
            
        except Exception as e:
            self.logger.error(f"Failed to load tool specs: {e}")