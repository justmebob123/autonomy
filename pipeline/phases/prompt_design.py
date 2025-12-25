"""
Prompt Design Phase

Enables AI to design custom prompts for specific tasks or roles.
Uses the PromptArchitect meta-prompt to guide the design process.
"""

from pathlib import Path
from typing import Dict, Optional

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient
from ..prompts.prompt_architect import get_prompt_architect_prompt
from ..tools import get_tools_for_phase


class PromptDesignPhase(BasePhase):
    """
    Phase for designing custom prompts.
    
    Process:
    1. Receive task description
    2. Use PromptArchitect meta-prompt
    3. AI designs prompt specification
    4. Validate and register prompt
    5. Make available to all phases
    
    Integration:
    - Uses existing BasePhase infrastructure
    - Leverages PromptRegistry for registration
    - Uses create_file tool for persistence
    """
    
    phase_name = "prompt_design"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        super().__init__(config, client)
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute prompt design phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Must include 'task_description' - what prompt to design
            
        Returns:
            PhaseResult with success status and created prompt info
        """
        task_description = kwargs.get('task_description')
        
        if not task_description:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No task description provided for prompt design"
            )
        
        self.logger.info(f"🎨 Designing prompt for: {task_description}")
        
        # Get the PromptArchitect meta-prompt
        system_prompt = get_prompt_architect_prompt(task_description)
        
        # Get tools for this phase
        tools = get_tools_for_phase(self.phase_name)
        
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
                "content": f"Design a prompt for: {task_description}"
            }
        ]
        
        # Call the AI
        response = self.chat(messages, tools, task_type="prompt_design")
        
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
                message="AI did not make any tool calls to create the prompt",
                data={"response": text_response}
            )
        
        # Process tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose)
        results = handler.process_tool_calls(tool_calls)
        
        # Check if prompt was created
        created_files = [r.get("filepath") for r in results if r.get("success")]
        
        if not created_files:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to create prompt file",
                data={"results": results}
            )
        
        # Try to register the prompt
        prompt_file = created_files[0]
        
        # Load and register the prompt
        try:
            import json
            full_path = self.project_dir / prompt_file
            
            if full_path.exists():
                with open(full_path, 'r') as f:
                    spec = json.load(f)
                
                # Register with PromptRegistry
                if self.prompt_registry.register_prompt(spec):
                    self.logger.info(f"✅ Successfully registered prompt: {spec['name']}")
                    
                    return PhaseResult(
                        success=True,
                        phase=self.phase_name,
                        message=f"Created and registered prompt: {spec['name']}",
                        files_created=[prompt_file],
                        data={
                            "prompt_name": spec['name'],
                            "purpose": spec.get('purpose', ''),
                            "filepath": prompt_file
                        }
                    )
                else:
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message="Prompt file created but registration failed",
                        files_created=[prompt_file]
                    )
            else:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Prompt file not found: {prompt_file}"
                )
                
        except Exception as e:
            self.logger.error(f"Error registering prompt: {e}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Error registering prompt: {e}",
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
        
        md = f"""# Prompt Design Phase State

## Statistics
- Runs: {phase_state.run_count if phase_state else 0}
- Successes: {phase_state.success_count if phase_state else 0}
- Failures: {phase_state.failure_count if phase_state else 0}

## Registered Prompts
"""
        
        # List registered prompts
        if hasattr(self, 'prompt_registry'):
            prompts = self.prompt_registry.list_prompts()
            if prompts:
                for prompt in prompts:
                    md += f"\n### {prompt['name']}\n"
                    md += f"- **Purpose**: {prompt['purpose']}\n"
                    md += f"- **Registered**: {prompt.get('registered_at', 'unknown')}\n"
                    md += f"- **Version**: {prompt.get('version', '1.0')}\n"
            else:
                md += "\nNo prompts registered yet.\n"
        
        return md