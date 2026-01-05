import re
import time
"""
Role Design Phase

Enables AI to design specialist roles for multi-agent collaboration.
Uses the RoleCreator meta-prompt to guide the design process.
"""

from pathlib import Path
from typing import Dict
from datetime import datetime
import json

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
        
        # ARCHITECTURE CONFIG
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.PHASE_COMPLETED,
                MessageType.TASK_FAILED,
                MessageType.SYSTEM_ALERT,
            ])
            self.logger.info("  📡 Subscribed to 3 message types")
        
        self.logger.info("  🎭 Role Design phase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute role design phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Must include 'role_description' - what role to design
            
        Returns:
            PhaseResult with success status and created role info
        """
        
        # POLYTOPIC INTEGRATION: Adaptive prompts
        self.update_system_prompt_with_adaptation({
            'phase': self.phase_name,
            'state': state,
            'context': 'role_design_execution'
        })
        
        # POLYTOPIC INTEGRATION: Get correlations and optimizations
        correlations = self.get_cross_phase_correlation()
        optimization = self.get_optimization_suggestion()
        
        # MESSAGE BUS: Publish phase start event
        self._publish_message('PHASE_STARTED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'correlations': correlations,
            'optimization': optimization
        })
        
        # ARCHITECTURE INTEGRATION: Read architecture
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives
        objectives = self._read_objectives()
        if objectives:
            pass
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting role design",
            "action": "start",
            "role_description": kwargs.get('role_description')
        })
        
        # INITIALIZE IPC DOCUMENTS
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS
        investigation_output = self.read_phase_output('investigation')
        
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
        
        # Process tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track tool calls for loop detection
        self.track_tool_calls(tool_calls, results)
        
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
                    pass
                    
                    # IPC INTEGRATION: Write completion status
                    self._write_status({
                        "status": "Role design completed",
                        "action": "complete",
                        "role_name": spec['name'],
                        "expertise": spec.get('expertise', '')
                    })
                    
                    # ARCHITECTURE INTEGRATION: Record role
                    if architecture:
                        self._update_architecture(
                            'roles',
                            f"Created role: {spec['name']}",
                            f"Role Design: Added {spec['name']} specialist"
                        )
                    
                    # MESSAGE BUS: Publish phase completion
                    self._publish_message('PHASE_COMPLETED', {
                        'phase': self.phase_name,
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'role_name': spec['name']
                    })
                    
                    # PATTERN RECOGNITION: Record phase completion
                    self.record_execution_pattern({
                        'phase': self.phase_name,
                        'action': 'phase_complete',
                        'role_name': spec['name'],
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # ANALYTICS: Track role creation metric
                    self.track_phase_metric({
                        'metric': 'role_created',
                        'role_name': spec['name'],
                        'expertise': spec.get('expertise', ''),
                        'files_created': len(created_files)
                    })
                    
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
        
        md = f"# Role Design Phase State\n\n"
        md += f"## Statistics\n"
        md += f"- Runs: {phase_state.run_count if phase_state else 0}\n"
        md += f"- Successes: {phase_state.success_count if phase_state else 0}\n"
        md += f"- Failures: {phase_state.failure_count if phase_state else 0}\n\n"
        md += f"## Registered Specialist Roles\n\n"
        
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