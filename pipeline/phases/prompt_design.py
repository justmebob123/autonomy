"""
Prompt Design Phase

Enables AI to design custom prompts for specific tasks or roles.
Uses the PromptArchitect meta-prompt to guide the design process.
"""

from pathlib import Path
from typing import Dict, Optional

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient
from ..prompts.prompt_architect import get_prompt_architect_prompt
from ..tools import get_tools_for_phase


class PromptDesignPhase(LoopDetectionMixin, BasePhase):
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
        
        self.logger.info("  ✍️ Prompt Design phase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute prompt design phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Must include 'task_description' - what prompt to design
            
        Returns:
            PhaseResult with success status and created prompt info
        """
        
        # POLYTOPIC INTEGRATION: Adaptive prompts
        self.update_system_prompt_with_adaptation({
            'phase': self.phase_name,
            'state': state,
            'context': 'prompt_design_execution'
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
        
        # ARCHITECTURE INTEGRATION: Read architecture for prompt context
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives for prompt design priorities
        objectives = self._read_objectives()
        if objectives:
            self.logger.info(f"  🎯 Objectives loaded: PRIMARY={bool(objectives.get('primary'))}, SECONDARY={len(objectives.get('secondary', []))}")
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting prompt design",
            "action": "start",
            "task_description": kwargs.get('task_description')
        })
        
        # INITIALIZE IPC DOCUMENTS
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS
        investigation_output = self.read_phase_output('investigation')
        
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
                "content": f"Design a prompt for: {task_description}"
            }
        ]
        
        # Use reasoning specialist for prompt design
        from ..orchestration.specialists.reasoning_specialist import ReasoningTask
        
        self.logger.info("  Using ReasoningSpecialist for prompt design...")
        reasoning_task = ReasoningTask(
            task_type="prompt_design",
            description=f"Design a prompt for: {task_description}",
            context={'task_description': task_description}
        )
        
        specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
        
        if not specialist_result.get("success", False):
            error_msg = specialist_result.get("response", "Specialist prompt design failed")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Prompt design failed: {error_msg}"
            )
        
        # Extract tool calls and response
        tool_calls = specialist_result.get("tool_calls", [])
        text_response = specialist_result.get("response", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="AI did not make any tool calls to create the prompt",
                data={"response": text_response}
            )
        
        # Check for loops before processing
        if self.check_for_loops():
            self.logger.warning("  Loop detected in prompt design phase")
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
                    
                    # IPC INTEGRATION: Write completion status
                    self._write_status({
                        "status": "Prompt design completed",
                        "action": "complete",
                        "prompt_name": spec['name'],
                        "filepath": prompt_file
                    })
                    
                    # ARCHITECTURE INTEGRATION: Record prompt in architecture
                    if architecture:
                        self._update_architecture(
                            'prompts',
                            f"Created prompt: {spec['name']}",
                            f"Prompt Design: Added {spec['name']} for {spec.get('purpose', 'general use')}"
                        )
                    
                    # MESSAGE BUS: Publish phase completion
                    self._publish_message('PHASE_COMPLETED', {
                        'phase': self.phase_name,
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'prompt_name': spec['name']
                    })
                    
                    # PATTERN RECOGNITION: Record phase completion
                    self.record_execution_pattern({
                        'phase': self.phase_name,
                        'action': 'phase_complete',
                        'prompt_name': spec['name'],
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # ANALYTICS: Track prompt creation metric
                    self.track_phase_metric({
                        'metric': 'prompt_created',
                        'prompt_name': spec['name'],
                        'purpose': spec.get('purpose', ''),
                        'files_created': 1
                    })
                    
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