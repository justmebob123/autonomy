"""
Role Design Phase

Enables AI to design specialist roles for multi-agent collaboration.
Uses the RoleCreator meta-prompt to guide the design process.
"""

from pathlib import Path
from typing import Dict

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient
from ..prompts.role_creator import get_role_creator_prompt
from ..tools import get_tools_for_phase


class RoleDesignPhase(LoopDetectionMixin, BasePhase):
    """
    Phase for designing specialist roles.
    
    Process:
    1. Receive role description
    2. Use RoleCreator meta-prompt
    3. AI designs role specification
    4. Validate and register role
    5. Instantiate SpecialistAgent
    6. Make available for consultation
    
    Integration:
    - Uses existing BasePhase infrastructure
    - Leverages RoleRegistry for registration
    - Uses existing SpecialistAgent class
    - Uses create_file tool for persistence
    """
    
    phase_name = "role_design"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient, **kwargs):
        BasePhase.__init__(self, config, client, **kwargs)
        self.init_loop_detection()
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute role design phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Must include 'role_description' - what role to design
            
        Returns:
            PhaseResult with success status and created role info
        """
        role_description = kwargs.get('role_description')
        
        if not role_description:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No role description provided for role design"
            )
        
        self.logger.info(f"👥 Designing specialist role for: {role_description}")
        
        # Get the RoleCreator meta-prompt
        system_prompt = get_role_creator_prompt(role_description)
        
        # Get tools for this phase
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
                "content": f"Design a specialist role for: {role_description}"
            }
        ]
        
        # Use reasoning specialist for role design
        from ..orchestration.specialists.reasoning_specialist import ReasoningTask
        
        self.logger.info("  Using ReasoningSpecialist for role design...")
        reasoning_task = ReasoningTask(
            task_type="role_design",
            description=f"Design a specialist role for: {role_description}",
            context={'role_description': role_description}
        )
        
        specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
        
        if not specialist_result.get("success", False):
            error_msg = specialist_result.get("response", "Specialist role design failed")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Role design failed: {error_msg}"
            )
        
        # Extract tool calls and response
        tool_calls = specialist_result.get("tool_calls", [])
        text_response = specialist_result.get("response", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="AI did not make any tool calls to create the role",
                data={"response": text_response}
            )
        
        # Check for loops before processing
        if self.check_for_loops():
            self.logger.warning("  Loop detected in role design phase")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Loop detected - stopping to prevent infinite cycle"
            )
        
        # Track tool calls for loop detection
        self.track_tool_calls(tool_calls, results)
        
        # Process tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Check if role file was created
        created_files = [r.get("filepath") for r in results if r.get("success")]
        
        if not created_files:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to create role file",
                data={"results": results}
            )
        
        # Find the role file
        role_file = None
        for filepath in created_files:
            if filepath.endswith('.json') and 'roles/custom' in filepath:
                role_file = filepath
                break
        
        if not role_file:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Role file not found in expected location",
                files_created=created_files
            )
        
        # Load and register the role
        try:
            import json
            full_role_path = self.project_dir / role_file
            
            if full_role_path.exists():
                with open(full_role_path, 'r') as f:
                    spec = json.load(f)
                
                # Register with RoleRegistry
                if self.role_registry.register_role(spec):
                    self.logger.info(f"✅ Successfully registered specialist role: {spec['name']}")
                    
                    return PhaseResult(
                        success=True,
                        phase=self.phase_name,
                        message=f"Created and registered specialist role: {spec['name']}",
                        files_created=created_files,
                        data={
                            "role_name": spec['name'],
                            "expertise": spec.get('expertise', ''),
                            "responsibilities": spec.get('responsibilities', []),
                            "model": spec.get('model', ''),
                            "role_file": role_file
                        }
                    )
                else:
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message="Role file created but registration failed",
                        files_created=created_files
                    )
            else:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Role file not found: {role_file}"
                )
                
        except Exception as e:
            self.logger.error(f"Error registering role: {e}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Error registering role: {e}",
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
        
        md = f"""# Role Design Phase State

## Statistics
- Runs: {phase_state.run_count if phase_state else 0}
- Successes: {phase_state.success_count if phase_state else 0}
- Failures: {phase_state.failure_count if phase_state else 0}

## Registered Specialist Roles
"""
        
        # List registered specialists
        if hasattr(self, 'role_registry'):
            specialists = self.role_registry.list_specialists()
            if specialists:
                for specialist in specialists:
                    md += f"\n### {specialist['name']}\n"
                    md += f"- **Expertise**: {specialist['expertise']}\n"
                    md += f"- **Model**: {specialist['model']}\n"
                    
                    if specialist.get('responsibilities'):
                        md += f"- **Responsibilities**:\n"
                        for resp in specialist['responsibilities']:
                            md += f"  - {resp}\n"
                    
                    md += f"- **Registered**: {specialist.get('registered_at', 'unknown')}\n"
                    md += f"- **Version**: {specialist.get('version', '1.0')}\n"
            else:
                md += "\nNo specialist roles registered yet.\n"
        
        return md