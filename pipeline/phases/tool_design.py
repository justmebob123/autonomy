"""
Tool Design Phase

Enables AI to design and implement custom tools for specific needs.
Uses the ToolDesigner meta-prompt to guide the design process.
"""

from pathlib import Path
from typing import Dict

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient
from ..prompts.tool_designer import get_tool_designer_prompt
from ..tools import get_tools_for_phase


class ToolDesignPhase(BasePhase):
    """
    Phase for designing custom tools.
    
    Process:
    1. Receive tool description
    2. Use ToolDesigner meta-prompt
    3. AI designs tool specification and implementation
    4. Validate safety and register tool
    5. Make available to all phases
    
    Integration:
    - Uses existing BasePhase infrastructure
    - Leverages ToolRegistry for registration
    - Uses create_file tool for persistence
    - Integrates with ToolCallHandler
    """
    
    phase_name = "tool_design"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        super().__init__(config, client)
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute tool design phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Must include 'tool_description' - what tool to design
            
        Returns:
            PhaseResult with success status and created tool info
        """
        tool_description = kwargs.get('tool_description')
        
        if not tool_description:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No tool description provided for tool design"
            )
        
        self.logger.info(f"🔧 Designing tool for: {tool_description}")
        
        # Get the ToolDesigner meta-prompt
        system_prompt = get_tool_designer_prompt(tool_description)
        
        # Get tools for this phase (include custom tools)
        tools = get_tools_for_phase(self.phase_name, self.tool_registry)
        
        # Add create_file tool if not already present
        create_file_tool = {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Create a new file with content",
                "parameters": {
                    "type": "object",
                    "required": ["filepath", "content"],
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the file to create (relative to project root)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    }
                }
            }
        }
        
        if not any(t.get("function", {}).get("name") == "create_file" for t in tools):
            tools.append(create_file_tool)
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Design a tool for: {tool_description}"
            }
        ]
        
        # Call the AI
        response = self.chat(messages, tools, task_type="tool_design")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"AI call failed: {response['error']}"
            )
        
        # Parse response
        tool_calls, text_response = self.parser.parse_response(response, tools)
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="AI did not make any tool calls to create the tool",
                data={"response": text_response}
            )
        
        # Process tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose)
        results = handler.process_tool_calls(tool_calls)
        
        # Check if tool files were created
        created_files = [r.get("filepath") for r in results if r.get("success")]
        
        if not created_files:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to create tool files",
                data={"results": results}
            )
        
        # Find the spec file and implementation file
        spec_file = None
        impl_file = None
        
        for filepath in created_files:
            if filepath.endswith('_spec.json'):
                spec_file = filepath
            elif filepath.endswith('.py'):
                impl_file = filepath
        
        if not spec_file or not impl_file:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Missing spec file or implementation file",
                files_created=created_files
            )
        
        # Load and register the tool
        try:
            import json
            full_spec_path = self.project_dir / spec_file
            
            if full_spec_path.exists():
                with open(full_spec_path, 'r') as f:
                    spec = json.load(f)
                
                # Register with ToolRegistry
                if self.tool_registry.register_tool(spec):
                    self.logger.info(f"✅ Successfully registered tool: {spec['name']}")
                    
                    return PhaseResult(
                        success=True,
                        phase=self.phase_name,
                        message=f"Created and registered tool: {spec['name']}",
                        files_created=created_files,
                        data={
                            "tool_name": spec['name'],
                            "description": spec.get('description', ''),
                            "category": spec.get('category', 'unknown'),
                            "spec_file": spec_file,
                            "impl_file": impl_file
                        }
                    )
                else:
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message="Tool files created but registration failed (safety validation may have failed)",
                        files_created=created_files
                    )
            else:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Tool spec file not found: {spec_file}"
                )
                
        except Exception as e:
            self.logger.error(f"Error registering tool: {e}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Error registering tool: {e}",
                files_created=created_files
            )
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """
        Generate markdown state file for this phase.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Markdown string
        """
        phase_state = state.phases.get(self.phase_name)
        
        md = f"""# Tool Design Phase State

## Statistics
- Runs: {phase_state.run_count if phase_state else 0}
- Successes: {phase_state.success_count if phase_state else 0}
- Failures: {phase_state.failure_count if phase_state else 0}

## Registered Tools
"""
        
        # List registered tools
        if hasattr(self, 'tool_registry'):
            tools = self.tool_registry.list_tools()
            if tools:
                # Group by category
                by_category = {}
                for tool in tools:
                    category = tool.get('category', 'unknown')
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append(tool)
                
                for category, category_tools in sorted(by_category.items()):
                    md += f"\n### {category.title()}\n"
                    for tool in category_tools:
                        md += f"\n#### {tool['name']}\n"
                        md += f"- **Description**: {tool['description']}\n"
                        md += f"- **Registered**: {tool.get('registered_at', 'unknown')}\n"
                        md += f"- **Version**: {tool.get('version', '1.0')}\n"
            else:
                md += "\nNo tools registered yet.\n"
        
        return md