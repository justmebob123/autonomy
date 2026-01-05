import re
import time
"""
Prompt Improvement Phase

Improves existing custom prompts by analyzing effectiveness
and creating enhanced versions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from pipeline.logging_setup import get_logger


class PromptImprovementPhase(LoopDetectionMixin, BasePhase):
    """
    Prompt Improvement phase that enhances custom prompts.
    
    Responsibilities:
    - Read custom prompts
    - Analyze effectiveness
    - Create improved versions
    - Test improvements
    - Update registry
    """
    
    phase_name = "prompt_improvement"
    
    def __init__(self, *args, **kwargs):
        BasePhase.__init__(self, *args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        self.custom_prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        self.custom_prompts_dir.mkdir(parents=True, exist_ok=True)
        self.improvement_results_dir = self.project_dir / ".pipeline" / "prompt_improvements"
        self.improvement_results_dir.mkdir(parents=True, exist_ok=True)
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.PHASE_COMPLETED,
                MessageType.TASK_FAILED,
                MessageType.SYSTEM_ALERT,
            ])
            self.logger.info("  📡 Subscribed to 3 message types")
        
        self.logger.info("  ✨ Prompt Improvement phase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute prompt improvement phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Additional arguments
            
        Returns:
            PhaseResult with improvement outcomes
        """
        
        # POLYTOPIC INTEGRATION: Adaptive prompts
        self.update_system_prompt_with_adaptation({
            'phase': self.phase_name,
            'state': state,
            'context': 'prompt_improvement_execution'
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
        
        # IPC INTEGRATION: Read objectives
        objectives = self._read_objectives()
        if objectives:
            pass
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting prompt improvement",
            "action": "start"
        })
        
        # INITIALIZE IPC DOCUMENTS
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS
        prompt_design_output = self.read_phase_output('prompt_design')
        
        self.logger.info("✨ Starting prompt improvement phase...")
        
        # Find all custom prompts
        custom_prompts = self._find_custom_prompts()
        
        if not custom_prompts:
            self.logger.info("  No custom prompts found to improve")
            
            # MESSAGE BUS: Publish phase completion
            self._publish_message('PHASE_COMPLETED', {
                'phase': self.phase_name,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'prompts_found': 0
            })
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No custom prompts to improve"
            )
        
        self.logger.info(f"  Found {len(custom_prompts)} custom prompts to analyze")
        
        # MESSAGE BUS: Publish analysis start
        self._publish_message('ANALYSIS_STARTED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'prompts_count': len(custom_prompts)
        })
        
        # Analyze and improve each prompt
        improvement_results = []
        prompts_improved = []
        
        for prompt_name in custom_prompts:
            self.logger.info(f"\n  📝 Analyzing prompt: {prompt_name}")
            
            # PATTERN RECOGNITION: Record analysis start
            self.record_execution_pattern({
                'phase': self.phase_name,
                'action': 'analyze_prompt',
                'prompt_name': prompt_name,
                'timestamp': datetime.now().isoformat()
            })
            
            result = self._analyze_and_improve_prompt(prompt_name)
            improvement_results.append(result)
            
            if result['improved']:
                prompts_improved.append(prompt_name)
                
                # MESSAGE BUS: Publish improvement event
                self._publish_message('PROMPT_IMPROVED', {
                    'phase': self.phase_name,
                    'prompt_name': prompt_name,
                    'timestamp': datetime.now().isoformat()
                })
                
                # PATTERN RECOGNITION: Record successful improvement
                self.record_execution_pattern({
                    'phase': self.phase_name,
                    'action': 'improve_prompt',
                    'prompt_name': prompt_name,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                # ANALYTICS: Track improvement metric
                self.track_phase_metric({
                    'metric': 'prompt_improved',
                    'prompt_name': prompt_name,
                    'phase': self.phase_name
                })
            else:
                self.logger.info(f"    ℹ️  Prompt already optimal")
                
                # PATTERN RECOGNITION: Record no improvement needed
                self.record_execution_pattern({
                    'phase': self.phase_name,
                    'action': 'analyze_prompt',
                    'prompt_name': prompt_name,
                    'already_optimal': True,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Save improvement results
        self._save_improvement_results(improvement_results)
        
        # Generate summary
        improved = len(prompts_improved)
        unchanged = len(custom_prompts) - improved
        
        message = f"Analyzed {len(custom_prompts)} prompts: {improved} improved, {unchanged} unchanged"
        
        # IPC INTEGRATION: Write completion status
        self._write_status({
            "status": "Prompt improvement completed",
            "action": "complete",
            "total_prompts": len(custom_prompts),
            "improved": improved
        })
        
        # ARCHITECTURE INTEGRATION: Record improvements
        if architecture and prompts_improved:
            self._update_architecture(
                'prompts',
                f"Improved {improved} prompts",
                f"Prompt Improvement: Enhanced {', '.join(prompts_improved)}"
            )
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'total_prompts': len(custom_prompts),
            'improved': improved,
            'unchanged': unchanged
        })
        
        # PATTERN RECOGNITION: Record phase completion
        self.record_execution_pattern({
            'phase': self.phase_name,
            'action': 'phase_complete',
            'total_prompts': len(custom_prompts),
            'improved': improved,
            'success': True,
            'timestamp': datetime.now().isoformat()
        })
        
        # ANALYTICS: Track phase completion metrics
        self.track_phase_metric({
            'metric': 'phase_complete',
            'total_prompts': len(custom_prompts),
            'improved': improved,
            'unchanged': unchanged,
            'success_rate': improved / len(custom_prompts) if len(custom_prompts) > 0 else 0
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=message,
            data={
                'total_prompts': len(custom_prompts),
                'improved': improved,
                'unchanged': unchanged,
                'prompts_improved': prompts_improved,
                'improvement_results': improvement_results
            }
        )
    
    def _find_custom_prompts(self) -> List[str]:
        """Find all custom prompts in the custom prompts directory."""
        prompts = []
        
        if not self.custom_prompts_dir.exists():
            return prompts
        
        for prompt_file in self.custom_prompts_dir.glob("*.json"):
            prompts.append(prompt_file.stem)
        
        return prompts
    
    def _analyze_and_improve_prompt(self, prompt_name: str) -> Dict:
        """
        Analyze and improve a custom prompt.
        
        Args:
            prompt_name: Name of the prompt to improve
            
        Returns:
            Improvement result dictionary
        """
        result = {
            'prompt_name': prompt_name,
            'timestamp': datetime.now().isoformat(),
            'improved': False,
            'analysis': {},
            'improvements': []
        }
        
        # Read current prompt
        prompt_file = self.custom_prompts_dir / f"{prompt_name}.json"
        
        try:
            with open(prompt_file, 'r') as f:
                prompt_data = json.load(f)
            
            current_template = prompt_data.get('template', '')
            
            # Use AI to analyze and improve the prompt
            analysis_prompt = self._get_analysis_prompt(prompt_name, prompt_data)
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "report_prompt_analysis",
                        "description": "Report analysis and improvement for a custom prompt",
                        "parameters": {
                            "type": "object",
                            "required": ["needs_improvement", "analysis", "improved_template"],
                            "properties": {
                                "needs_improvement": {
                                    "type": "boolean",
                                    "description": "Whether the prompt needs improvement"
                                },
                                "analysis": {
                                    "type": "object",
                                    "properties": {
                                        "clarity_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "structure_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "effectiveness_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "strengths": {"type": "array", "items": {"type": "string"}},
                                        "weaknesses": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "description": "Analysis of current prompt"
                                },
                                "improved_template": {
                                    "type": "string",
                                    "description": "Improved prompt template (if needs_improvement is true)"
                                },
                                "improvements_made": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of improvements made"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Reasoning for improvements"
                                }
                            }
                        }
                    }
                }
            ]
            
            # Use reasoning specialist for prompt improvement
            from ..orchestration.specialists.reasoning_specialist import ReasoningTask
            
            self.logger.info(f"  Using ReasoningSpecialist for prompt improvement...")
            reasoning_task = ReasoningTask(
                task_type="prompt_improvement",
                description=analysis_prompt,
                context={'prompt_name': prompt_name}
            )
            
            specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
            
            # Extract tool calls
            tool_calls = specialist_result.get("tool_calls", []) if specialist_result.get("success", False) else []
            
            # Check for loops
            if self.check_for_loops():
                self.logger.warning(f"    Loop detected for prompt {prompt_name}")
                result['error'] = 'Loop detected'
                return result
            
            # Process tool calls
            from ..handlers import ToolCallHandler
            handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
            results = handler.process_tool_calls(tool_calls)
            
            # Track tool calls for loop detection
            self.track_tool_calls(tool_calls, results)
            
            if tool_calls:
                for call in tool_calls:
                    if call.get('tool') == 'report_prompt_analysis':
                        args = call.get('args', {})
                        
                        result['analysis'] = args.get('analysis', {})
                        
                        if args.get('needs_improvement', False):
                            improved_template = args.get('improved_template', '')
                            
                            if improved_template and improved_template != current_template:
                                pass
                                # Save improved version
                                self._save_improved_prompt(prompt_name, prompt_data, improved_template, args)
                                
                                result['improved'] = True
                                result['improvements'] = args.get('improvements_made', [])
                                result['reasoning'] = args.get('reasoning', '')
            
        except Exception as e:
            self.logger.error(f"    Error improving prompt {prompt_name}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_analysis_prompt(self, prompt_name: str, prompt_data: Dict) -> str:
        """Generate analysis prompt for a custom prompt."""
        return f"""# Prompt Improvement Task

You are analyzing a custom prompt to improve its effectiveness.

## Prompt Information

**Name:** {prompt_name}

**Current Template:**
```
{prompt_data.get('template', '')}
```

**Variables:** {', '.join(prompt_data.get('variables', []))}

**Description:** {prompt_data.get('description', 'No description')}

**Type:** {prompt_data.get('type', 'unknown')}

## Analysis Criteria

Evaluate this prompt on:

1. **Clarity (1-10):** Is it clear and unambiguous?
2. **Structure (1-10):** Is it well-organized?
3. **Effectiveness (1-10):** Will it produce good results?
4. **Completeness:** Does it cover all necessary aspects?
5. **Specificity:** Is it specific enough?
6. **Cognitive Load:** Is it easy to understand?
7. **Tool Integration:** Does it guide tool usage well?
8. **Examples:** Does it provide helpful examples?

## Your Task

1. Analyze the prompt against the criteria above
2. Identify strengths and weaknesses
3. If improvements are needed, create an improved version
4. Explain what improvements you made and why

**IMPORTANT:** 
- Only suggest improvements if they will meaningfully enhance effectiveness
- Maintain the original intent and purpose
- Preserve all variable placeholders
- Keep the same general structure unless it's problematic
- Be specific about what you improved and why

Use the `report_prompt_analysis` tool to report your findings.
"""
    
    def _save_improved_prompt(self, prompt_name: str, original_data: Dict, 
                             improved_template: str, analysis: Dict) -> None:
        """
        Save improved prompt version.
        
        Args:
            prompt_name: Name of the prompt
            original_data: Original prompt data
            improved_template: Improved template
            analysis: Analysis results
        """
        # Create new version with improved template
        improved_data = original_data.copy()
        improved_data['template'] = improved_template
        improved_data['version'] = improved_data.get('version', 1) + 1
        improved_data['improved_at'] = datetime.now().isoformat()
        improved_data['improvements'] = analysis.get('improvements_made', [])
        improved_data['reasoning'] = analysis.get('reasoning', '')
        
        # Save improved version
        prompt_file = self.custom_prompts_dir / f"{prompt_name}.json"
        
        # Backup original
        backup_file = self.custom_prompts_dir / f"{prompt_name}_v{original_data.get('version', 1)}_backup.json"
        with open(backup_file, 'w') as f:
            json.dump(original_data, f, indent=2)
        
        # Save improved version
        with open(prompt_file, 'w') as f:
            json.dump(improved_data, f, indent=2)
        
        self.logger.info(f"      💾 Saved improved prompt (v{improved_data['version']})")
        self.logger.info(f"      📦 Original backed up to {backup_file.name}")
    
    def _save_improvement_results(self, results: List[Dict]) -> None:
        """Save improvement results to file."""
        results_file = self.improvement_results_dir / f"improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        
        self.logger.info(f"\n  💾 Improvement results saved to {results_file.name}")
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown content for prompt improvement state."""
        lines = [
            "# Prompt Improvement State",
            "",
            f"**Last Updated:** {self.format_timestamp()}",
            "",
            "## Custom Prompts",
            ""
        ]
        
        custom_prompts = self._find_custom_prompts()
        
        if not custom_prompts:
            lines.append("No custom prompts found.")
        else:
            lines.append(f"**Total Custom Prompts:** {len(custom_prompts)}")
            lines.append("")
            
            for prompt_name in custom_prompts:
                prompt_file = self.custom_prompts_dir / f"{prompt_name}.json"
                
                try:
                    with open(prompt_file, 'r') as f:
                        data = json.load(f)
                    
                    version = data.get('version', 1)
                    lines.append(f"- {prompt_name} (v{version})")
                except:
                    lines.append(f"- {prompt_name}")
        
        lines.extend([
            "",
            "## Recent Improvements",
            ""
        ])
        
        # List recent improvement files
        if self.improvement_results_dir.exists():
            improvement_files = sorted(self.improvement_results_dir.glob("improvement_*.json"), reverse=True)[:5]
            
            if improvement_files:
                for imp_file in improvement_files:
                    lines.append(f"- {imp_file.name}")
            else:
                lines.append("No improvements yet.")
        else:
            lines.append("No improvements yet.")
        
        return "\n".join(lines)