"""
Role Improvement Phase

Improves existing custom roles by analyzing performance
and requesting improved prompts and tools.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from pipeline.logging_setup import get_logger


class RoleImprovementPhase(LoopDetectionMixin, BasePhase):
    """
    Role Improvement phase that enhances custom roles.
    
    Responsibilities:
    - Read custom roles
    - Analyze performance
    - Request improved prompts
    - Request improved tools
    - Create enhanced role specifications
    - Validate role effectiveness
    """
    
    phase_name = "role_improvement"
    
    def __init__(self, *args, **kwargs):
        BasePhase.__init__(self, *args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        self.custom_roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        self.custom_roles_dir.mkdir(parents=True, exist_ok=True)
        self.improvement_results_dir = self.project_dir / ".pipeline" / "role_improvements"
        self.improvement_results_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("  🌟 Role Improvement phase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute role improvement phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Additional arguments
            
        Returns:
            PhaseResult with improvement outcomes
        """
        
        # INITIALIZE IPC DOCUMENTS
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS
        role_design_output = self.read_phase_output('role_design')
        
        self.logger.info("🎭 Starting role improvement phase...")
        
        # Find all custom roles
        custom_roles = self._find_custom_roles()
        
        if not custom_roles:
            self.logger.info("  No custom roles found to improve")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No custom roles to improve"
            )
        
        self.logger.info(f"  Found {len(custom_roles)} custom roles to analyze")
        
        # Analyze and improve each role
        improvement_results = []
        roles_improved = []
        
        for role_name in custom_roles:
            self.logger.info(f"\n  🎭 Analyzing role: {role_name}")
            
            result = self._analyze_and_improve_role(role_name)
            improvement_results.append(result)
            
            if result['improved']:
                roles_improved.append(role_name)
                self.logger.info(f"    ✅ Role improved")
            else:
                self.logger.info(f"    ℹ️  Role already optimal")
        
        # Save improvement results
        self._save_improvement_results(improvement_results)
        
        # Generate summary
        improved = len(roles_improved)
        unchanged = len(custom_roles) - improved
        
        message = f"Analyzed {len(custom_roles)} roles: {improved} improved, {unchanged} unchanged"
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=message,
            data={
                'total_roles': len(custom_roles),
                'improved': improved,
                'unchanged': unchanged,
                'roles_improved': roles_improved,
                'improvement_results': improvement_results
            }
        )
    
    def _find_custom_roles(self) -> List[str]:
        """Find all custom roles in the custom roles directory."""
        roles = []
        
        if not self.custom_roles_dir.exists():
            return roles
        
        for role_file in self.custom_roles_dir.glob("*.json"):
            roles.append(role_file.stem)
        
        return roles
    
    def _analyze_and_improve_role(self, role_name: str) -> Dict:
        """
        Analyze and improve a custom role.
        
        Args:
            role_name: Name of the role to improve
            
        Returns:
            Improvement result dictionary
        """
        result = {
            'role_name': role_name,
            'timestamp': datetime.now().isoformat(),
            'improved': False,
            'analysis': {},
            'improvements': [],
            'prompt_requests': [],
            'tool_requests': []
        }
        
        # Read current role
        role_file = self.custom_roles_dir / f"{role_name}.json"
        
        try:
            with open(role_file, 'r') as f:
                role_data = json.load(f)
            
            # Use AI to analyze and improve the role
            analysis_prompt = self._get_analysis_prompt(role_name, role_data)
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "report_role_analysis",
                        "description": "Report analysis and improvement for a custom role",
                        "parameters": {
                            "type": "object",
                            "required": ["needs_improvement", "analysis"],
                            "properties": {
                                "needs_improvement": {
                                    "type": "boolean",
                                    "description": "Whether the role needs improvement"
                                },
                                "analysis": {
                                    "type": "object",
                                    "properties": {
                                        "effectiveness_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "clarity_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "completeness_score": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "strengths": {"type": "array", "items": {"type": "string"}},
                                        "weaknesses": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "description": "Analysis of current role"
                                },
                                "improved_role": {
                                    "type": "object",
                                    "description": "Improved role specification"
                                },
                                "improvements_made": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of improvements made"
                                },
                                "prompt_requests": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "prompt_name": {"type": "string"},
                                            "purpose": {"type": "string"},
                                            "requirements": {"type": "string"}
                                        }
                                    },
                                    "description": "Requests for new/improved prompts"
                                },
                                "tool_requests": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "tool_name": {"type": "string"},
                                            "purpose": {"type": "string"},
                                            "requirements": {"type": "string"}
                                        }
                                    },
                                    "description": "Requests for new/improved tools"
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
            
            # Use reasoning specialist for role improvement
            from ..orchestration.specialists.reasoning_specialist import ReasoningTask
            
            self.logger.info(f"  Using ReasoningSpecialist for role improvement...")
            reasoning_task = ReasoningTask(
                task_type="role_improvement",
                description=analysis_prompt,
                context={'role_name': role_name}
            )
            
            specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
            
            # Extract tool calls
            tool_calls = specialist_result.get("tool_calls", []) if specialist_result.get("success", False) else []
            
            # Check for loops
            if self.check_for_loops():
                self.logger.warning(f"    Loop detected for role {role_name}")
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
                    if call.get('tool') == 'report_role_analysis':
                        args = call.get('args', {})
                        
                        result['analysis'] = args.get('analysis', {})
                        result['prompt_requests'] = args.get('prompt_requests', [])
                        result['tool_requests'] = args.get('tool_requests', [])
                        
                        if args.get('needs_improvement', False):
                            improved_role = args.get('improved_role', {})
                            
                            if improved_role:
                                # Save improved version
                                self._save_improved_role(role_name, role_data, improved_role, args)
                                
                                result['improved'] = True
                                result['improvements'] = args.get('improvements_made', [])
                                result['reasoning'] = args.get('reasoning', '')
                        
                        # Process prompt and tool requests
                        if result['prompt_requests']:
                            self._process_prompt_requests(role_name, result['prompt_requests'])
                        
                        if result['tool_requests']:
                            self._process_tool_requests(role_name, result['tool_requests'])
            
        except Exception as e:
            self.logger.error(f"    Error improving role {role_name}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_analysis_prompt(self, role_name: str, role_data: Dict) -> str:
        """Generate analysis prompt for a custom role."""
        return f"""# Role Improvement Task

You are analyzing a custom role to improve its effectiveness.

## Role Information

**Name:** {role_name}

**Current Specification:**
```json
{json.dumps(role_data, indent=2)}
```

## Analysis Criteria

Evaluate this role on:

1. **Effectiveness (1-10):** How well does it perform its function?
2. **Clarity (1-10):** Is the role definition clear?
3. **Completeness (1-10):** Does it have everything needed?
4. **Responsibilities:** Are they well-defined?
5. **Capabilities:** Are they sufficient?
6. **Tools:** Does it have the right tools?
7. **Prompts:** Are the prompts effective?
8. **Collaboration:** Does it work well with other roles?

## Your Task

1. Analyze the role against the criteria above
2. Identify strengths and weaknesses
3. If improvements are needed, create an improved version
4. Identify any missing prompts or tools needed
5. Explain what improvements you made and why

**IMPORTANT:**
- Consider if this role needs better prompts to be more effective
- Consider if this role needs additional tools to accomplish its goals
- Think about how this role collaborates with other specialists
- Maintain backward compatibility
- Be specific about improvements

Use the `report_role_analysis` tool to report your findings.

**Prompt Requests:** If this role would benefit from custom prompts, specify:
- What prompt is needed
- What purpose it serves
- What requirements it should meet

**Tool Requests:** If this role would benefit from custom tools, specify:
- What tool is needed
- What purpose it serves
- What requirements it should meet
"""
    
    def _save_improved_role(self, role_name: str, original_data: Dict,
                           improved_role: Dict, analysis: Dict) -> None:
        """
        Save improved role version.
        
        Args:
            role_name: Name of the role
            original_data: Original role data
            improved_role: Improved role specification
            analysis: Analysis results
        """
        # Merge improved data with original
        improved_data = original_data.copy()
        improved_data.update(improved_role)
        improved_data['version'] = improved_data.get('version', 1) + 1
        improved_data['improved_at'] = datetime.now().isoformat()
        improved_data['improvements'] = analysis.get('improvements_made', [])
        improved_data['reasoning'] = analysis.get('reasoning', '')
        
        # Save improved version
        role_file = self.custom_roles_dir / f"{role_name}.json"
        
        # Backup original
        backup_file = self.custom_roles_dir / f"{role_name}_v{original_data.get('version', 1)}_backup.json"
        with open(backup_file, 'w') as f:
            json.dump(original_data, f, indent=2)
        
        # Save improved version
        with open(role_file, 'w') as f:
            json.dump(improved_data, f, indent=2)
        
        self.logger.info(f"      💾 Saved improved role (v{improved_data['version']})")
        self.logger.info(f"      📦 Original backed up to {backup_file.name}")
    
    def _process_prompt_requests(self, role_name: str, requests: List[Dict]) -> None:
        """
        Process requests for new/improved prompts.
        
        Args:
            role_name: Name of the role requesting prompts
            requests: List of prompt requests
        """
        self.logger.info(f"      📝 Processing {len(requests)} prompt requests...")
        
        requests_file = self.improvement_results_dir / f"{role_name}_prompt_requests.json"
        
        with open(requests_file, 'w') as f:
            json.dump({
                'role_name': role_name,
                'timestamp': datetime.now().isoformat(),
                'requests': requests
            }, f, indent=2)
        
        for req in requests:
            self.logger.info(f"         - {req.get('prompt_name', 'unnamed')}: {req.get('purpose', 'no purpose')}")
    
    def _process_tool_requests(self, role_name: str, requests: List[Dict]) -> None:
        """
        Process requests for new/improved tools.
        
        Args:
            role_name: Name of the role requesting tools
            requests: List of tool requests
        """
        self.logger.info(f"      🔧 Processing {len(requests)} tool requests...")
        
        requests_file = self.improvement_results_dir / f"{role_name}_tool_requests.json"
        
        with open(requests_file, 'w') as f:
            json.dump({
                'role_name': role_name,
                'timestamp': datetime.now().isoformat(),
                'requests': requests
            }, f, indent=2)
        
        for req in requests:
            self.logger.info(f"         - {req.get('tool_name', 'unnamed')}: {req.get('purpose', 'no purpose')}")
    
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
        """Generate markdown content for role improvement state."""
        lines = [
            "# Role Improvement State",
            "",
            f"**Last Updated:** {self.format_timestamp()}",
            "",
            "## Custom Roles",
            ""
        ]
        
        custom_roles = self._find_custom_roles()
        
        if not custom_roles:
            lines.append("No custom roles found.")
        else:
            lines.append(f"**Total Custom Roles:** {len(custom_roles)}")
            lines.append("")
            
            for role_name in custom_roles:
                role_file = self.custom_roles_dir / f"{role_name}.json"
                
                try:
                    with open(role_file, 'r') as f:
                        data = json.load(f)
                    
                    version = data.get('version', 1)
                    lines.append(f"- {role_name} (v{version})")
                except:
                    lines.append(f"- {role_name}")
        
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