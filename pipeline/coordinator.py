"""
Phase Coordinator

Orchestrates the pipeline phases and determines the next action to take.
This is the main control loop that NEVER exits - it continuously finds work to do.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import PipelineConfig
from .client import OllamaClient
from .state.manager import StateManager, PipelineState, TaskState, TaskStatus
from .logging_setup import get_logger, setup_logging


class PhaseCoordinator:
    """
    Coordinates pipeline phases and manages the main execution loop.
    
    The coordinator NEVER exits on its own - it continuously cycles through:
    1. Initial planning (if no tasks)
    2. Coding (implement tasks)
    3. QA (review code)
    4. Debugging (fix issues)
    5. Documentation (update README/ARCHITECTURE)
    6. Project Planning (expand project when all tasks complete)
    
    The loop only exits via:
    - KeyboardInterrupt (Ctrl+C)
    - max_iterations limit (if set > 0)
    - Unrecoverable error
    """
    
    def __init__(self, config: PipelineConfig, verbose: bool = False):
        self.config = config
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        self.verbose = verbose
        
        # Initialize client
        self.client = OllamaClient(config)
        
        # Initialize state manager
        self.state_manager = StateManager(self.project_dir)
        
        # Initialize phases (lazy import to avoid circular deps)
        self.phases = self._init_phases()
        
        # Hyperdimensional polytopic structure
        self.polytope = {
            'vertices': {},  # phase_name -> {type, dimensions}
            'edges': {},     # phase_name -> [adjacent_phases]
            'dimensions': 7,
            'self_awareness_level': 0.0,
            'recursion_depth': 0,
            'max_recursion_depth': 61
        }
        
        # Initialize polytopic structure from phases
        self._initialize_polytopic_structure()
        
        # Correlation engine for cross-phase analysis
        from .correlation_engine import CorrelationEngine
        self.correlation_engine = CorrelationEngine()
    
    def _init_phases(self) -> Dict:
        """Initialize all pipeline phases"""
        from .phases import (
            PlanningPhase,
            CodingPhase,
            QAPhase,
            DebuggingPhase,
            ProjectPlanningPhase,
            DocumentationPhase,
        )
        from .phases.investigation import InvestigationPhase
        from .phases.prompt_design import PromptDesignPhase
        from .phases.tool_design import ToolDesignPhase
        from .phases.role_design import RoleDesignPhase
        from .phases.tool_evaluation import ToolEvaluationPhase
        from .phases.prompt_improvement import PromptImprovementPhase
        from .phases.role_improvement import RoleImprovementPhase
        
        # BasePhase.__init__ takes (config, client) - project_dir comes from config
        return {
            "planning": PlanningPhase(self.config, self.client),
            "coding": CodingPhase(self.config, self.client),
            "qa": QAPhase(self.config, self.client),
            "investigation": InvestigationPhase(self.config, self.client),
            "debugging": DebuggingPhase(self.config, self.client),
            "debug": DebuggingPhase(self.config, self.client),  # Alias
            "project_planning": ProjectPlanningPhase(self.config, self.client),
            "documentation": DocumentationPhase(self.config, self.client),
            # Meta-agent phases (Integration Point #1)
            "prompt_design": PromptDesignPhase(self.config, self.client),
            "tool_design": ToolDesignPhase(self.config, self.client),
            "role_design": RoleDesignPhase(self.config, self.client),
            # Self-improvement phases (Integration Point #2)
            "tool_evaluation": ToolEvaluationPhase(self.config, self.client),
            "prompt_improvement": PromptImprovementPhase(self.config, self.client),
            "role_improvement": RoleImprovementPhase(self.config, self.client),
        }
    
    def _initialize_polytopic_structure(self):
        """Initialize hyperdimensional polytopic structure from existing phases."""
        phase_types = {
            'planning': 'planning', 'coding': 'execution', 'qa': 'validation',
            'debugging': 'correction', 'investigation': 'analysis',
            'project_planning': 'planning', 'documentation': 'documentation',
            'prompt_design': 'meta', 'tool_design': 'meta', 'role_design': 'meta',
            'tool_evaluation': 'improvement', 'prompt_improvement': 'improvement',
            'role_improvement': 'improvement'
        }
        
        for phase_name in self.phases.keys():
            self.polytope['vertices'][phase_name] = {
                'type': phase_types.get(phase_name, 'unknown'),
                'dimensions': {'temporal': 0.5, 'functional': 0.5, 'data': 0.5,
                              'state': 0.5, 'error': 0.5, 'context': 0.5, 'integration': 0.5}
            }
        
        self.polytope['edges'] = {
            # Core development flow
            'planning': ['coding'],
            'coding': ['qa', 'documentation'],
            'qa': ['debugging', 'documentation', 'application_troubleshooting'],
            
            # Error handling triangle
            'debugging': ['investigation', 'coding', 'application_troubleshooting'],
            'investigation': ['debugging', 'coding', 'application_troubleshooting',
                              'prompt_design', 'role_design', 'tool_design'],
            'application_troubleshooting': ['debugging', 'investigation', 'coding'],
            
            # Documentation flow
            'documentation': ['planning', 'qa'],
            
            # Project management
            'project_planning': ['planning'],
            
            # Self-improvement cycles
            'prompt_design': ['prompt_improvement'],
            'prompt_improvement': ['prompt_design', 'planning'],
            'role_design': ['role_improvement'],
            'role_improvement': ['role_design', 'planning'],
            
            # Tool development cycle
            'tool_design': ['tool_evaluation'],
            'tool_evaluation': ['tool_design', 'coding']
        }
        
        self.logger.info(f"Polytopic structure: {len(self.polytope['vertices'])} vertices, 7D")
    
    def _select_next_phase_polytopic(self, state):
        """Select next phase using polytopic adjacency with intelligent situation analysis."""
        from .state.manager import TaskStatus
        
        # Build context from state
        context = {
            'current_phase': state.current_phase,
            'tasks': state.tasks,
            'errors': [t for t in state.tasks.values() if t.status == TaskStatus.FAILED],
            'pending': [t for t in state.tasks.values() if t.status == TaskStatus.PENDING],
            'completed': [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED]
        }
        
        # Analyze situation with intelligence
        situation = self._analyze_situation(context)
        
        # Select path intelligently
        return self._select_intelligent_path(situation, state.current_phase)
    
    def _analyze_situation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive situation analysis with error severity, complexity, and urgency assessment."""
        situation = {
            'has_errors': len(context.get('errors', [])) > 0,
            'has_pending': len(context.get('pending', [])) > 0,
            'needs_planning': len(context.get('tasks', {})) == 0,
            'error_count': len(context.get('errors', [])),
            'pending_count': len(context.get('pending', [])),
            'completed_count': len(context.get('completed', []))
        }
        
        # Assess error severity
        if situation['has_errors']:
            errors = context.get('errors', [])
            situation['error_severity'] = self._assess_error_severity(errors)
        else:
            situation['error_severity'] = 'none'
        
        # Assess complexity
        situation['complexity'] = self._assess_complexity(context)
        
        # Assess urgency
        situation['urgency'] = self._assess_urgency(situation)
        
        # Determine dimensional focus
        situation['dimensional_focus'] = self._determine_dimensional_focus(situation)
        
        # Determine mode
        if situation['error_severity'] in ['high', 'critical']:
            situation['mode'] = 'error_handling'
        elif situation['complexity'] == 'high':
            situation['mode'] = 'deep_analysis'
        else:
            situation['mode'] = 'development'
        
        return situation
    
    def _assess_error_severity(self, errors: List[Any]) -> str:
        """Assess the severity of errors."""
        if not errors:
            return 'none'
        
        error_count = len(errors)
        
        # Check for repeated errors
        repeated_errors = sum(1 for e in errors if hasattr(e, 'attempts') and e.attempts > 2)
        
        if error_count >= 5 or repeated_errors >= 2:
            return 'critical'
        elif error_count >= 3 or repeated_errors >= 1:
            return 'high'
        elif error_count >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """Assess the complexity of the current situation."""
        total_tasks = len(context.get('tasks', {}))
        errors = len(context.get('errors', []))
        
        if total_tasks > 20 or errors > 5:
            return 'high'
        elif total_tasks > 10 or errors > 2:
            return 'medium'
        else:
            return 'low'
    
    def _assess_urgency(self, situation: Dict[str, Any]) -> str:
        """Assess the urgency of the situation."""
        if situation['error_severity'] in ['critical', 'high']:
            return 'high'
        elif situation['has_errors']:
            return 'medium'
        else:
            return 'low'
    
    def _determine_dimensional_focus(self, situation: Dict[str, Any]) -> List[str]:
        """Determine which dimensions to focus on based on situation."""
        focus = []
        
        if situation['has_errors']:
            focus.extend(['error', 'context'])
        
        if situation['complexity'] == 'high':
            focus.extend(['functional', 'integration'])
        
        if situation['urgency'] == 'high':
            focus.append('temporal')
        
        return list(set(focus))  # Remove duplicates
    
    def _select_intelligent_path(self, situation: Dict[str, Any], current_phase: str) -> str:
        """Select optimal execution path based on situation analysis."""
        adjacent = self.polytope['edges'].get(current_phase, ['planning'])
        best_phase, best_score = None, -1
        
        for phase_name in adjacent:
            if phase_name in self.phases:
                score = self._calculate_phase_priority(phase_name, situation)
                if score > best_score:
                    best_score, best_phase = score, phase_name
        
        # Increase self-awareness
        self.polytope['self_awareness_level'] = min(1.0, self.polytope['self_awareness_level'] + 0.001)
        
        return best_phase if best_phase else 'planning'
    
    def _calculate_phase_priority(self, phase_name: str, situation: Dict[str, Any]) -> float:
        """Calculate priority score for a phase based on situation."""
        score = 0.5  # Base score
        
        # Error-driven routing
        if situation['has_errors']:
            if phase_name in ['debugging', 'investigation']:
                score += 0.4
            if situation['error_severity'] == 'critical' and phase_name == 'investigation':
                score += 0.3
        
        # Complexity-based routing
        if situation['complexity'] == 'high':
            if phase_name in ['investigation', 'debugging']:
                score += 0.2
        
        # Pending work routing
        if situation['has_pending']:
            if phase_name == 'coding':
                score += 0.3
        
        # Planning routing
        if situation['needs_planning']:
            if phase_name == 'planning':
                score += 0.4
        
        return score
    
    def expand_dimensions(self, new_dimension: str, description: str):
        """Dynamically expand the dimensional space."""
        self.polytope['dimensions'] += 1
        
        # Add new dimension to all vertices
        for vertex_name in self.polytope['vertices']:
            if 'dimensions' in self.polytope['vertices'][vertex_name]:
                self.polytope['vertices'][vertex_name]['dimensions'][new_dimension] = 0.5
        
        self.logger.info(f"Expanded to {self.polytope['dimensions']} dimensions: added '{new_dimension}' - {description}")
       
    
    def run(self, resume: bool = True) -> bool:
        """
        Run the main pipeline loop.
        
        Args:
            resume: If True, resume from saved state. If False, start fresh.
        
        Returns:
            True if completed successfully, False on error
        """
        self._print_banner()
        
        # Discover servers
        self.logger.info("🔍 Discovering Ollama servers...")
        self.client.discover_servers()
        
        # Load or create state
        if resume:
            state = self.state_manager.load()
        else:
            # Start fresh - create new state
            self.logger.info("  Starting fresh (ignoring saved state)...")
            state = PipelineState()
            self.state_manager.save(state)
        
        if state.tasks:
            self.logger.info(f"  Resumed pipeline run: {state.run_id}")
            completed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
            self.logger.info(f"  Tasks: {len(state.tasks)} total, {completed} completed")
        else:
            self.logger.info(f"  Starting new pipeline run: {state.run_id}")
        
        # Run the main loop
        try:
            return self._run_loop()
        except KeyboardInterrupt:
            self.logger.info("\n\n⚠️ Pipeline interrupted by user")
            return False
    
    def _develop_tool(self, tool_name: str, tool_args: dict, 
                     usage_context: dict, state: PipelineState) -> 'PhaseResult':
        """
        Develop a new tool through tool_design and tool_evaluation phases.
        
        Args:
            tool_name: Name of the tool to create
            tool_args: Arguments that were passed to the unknown tool
            usage_context: Context about how/where the tool was used
            state: Current pipeline state
            
        Returns:
            PhaseResult from tool_evaluation phase
        """
        from .phases.base import PhaseResult
        
        self.logger.info(f"📐 Designing tool: {tool_name}")
        
        # Step 1: Design the tool
        if 'tool_design' not in self.phases:
            self.logger.error("tool_design phase not available")
            return PhaseResult(
                success=False,
                phase='tool_development',
                message="tool_design phase not available"
            )
        
        design_result = self.phases['tool_design'].execute(
            state,
            tool_name=tool_name,
            tool_args=tool_args,
            usage_context=usage_context
        )
        
        if not design_result.success:
            self.logger.error(f"Tool design failed: {design_result.message}")
            return design_result
        
        self.logger.info(f"✓ Tool designed: {tool_name}")
        
        # Step 2: Evaluate the tool
        if 'tool_evaluation' not in self.phases:
            self.logger.warning("tool_evaluation phase not available, skipping validation")
            return design_result
        
        self.logger.info(f"🧪 Evaluating tool: {tool_name}")
        
        eval_result = self.phases['tool_evaluation'].execute(
            state,
            tool_name=tool_name,
            tool_spec=design_result.data.get('tool_spec')
        )
        
        if eval_result.success:
            self.logger.info(f"✓ Tool validated: {tool_name}")
        else:
            self.logger.warning(f"Tool validation failed: {eval_result.message}")
        
        return eval_result
    
    def _run_loop(self) -> bool:
        """
        Main execution loop - NEVER returns None for next action.
        
        The loop continues until:
        - max_iterations reached (if > 0)
        - KeyboardInterrupt
        - Unrecoverable error
        """
        iteration = 0
        max_iter = self.config.max_iterations if self.config.max_iterations > 0 else float('inf')
        
        # NO RATE LIMITING - run as fast as possible
        min_interval = 0  # UNLIMITED - no delay between iterations
        last_iteration_time = 0
        
        while iteration < max_iter:
            # No rate limiting - removed per user request
            last_iteration_time = time.time()
            
            # Load current state
            state = self.state_manager.load()
            
            # Determine next action (NEVER returns None)
            action = self._determine_next_action(state)
            
            # Log iteration
            iteration += 1
            phase_name = action["phase"]
            reason = action.get("reason", "")
            
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  ITERATION {iteration} - {phase_name.upper()}")
            self.logger.info(f"  Reason: {reason}")
            self.logger.info(f"{'='*70}")
            
            # Get the phase
            phase = self.phases.get(phase_name)
            if not phase:
                self.logger.error(f"Unknown phase: {phase_name}")
                continue
            
            # Execute the phase
            task = action.get("task")
            
            try:
                # Execute the phase with unknown tool detection
                result = phase.run(task=task)
                
                # Check for unknown tool errors
                if not result.success and result.data.get('requires_tool_development'):
                    self.logger.info(f"🔧 Unknown tools detected, initiating tool development")
                    
                    unknown_tools = result.data.get('unknown_tools', [])
                    tool_calls = result.data.get('original_tool_calls', [])
                    
                    # Develop each unknown tool
                    all_tools_developed = True
                    for unknown_tool in unknown_tools:
                        tool_result = self._develop_tool(
                            tool_name=unknown_tool['tool_name'],
                            tool_args=unknown_tool.get('args', {}),
                            usage_context={
                                'phase': phase_name,
                                'original_tool_calls': tool_calls
                            },
                            state=state
                        )
                        
                        if not tool_result.success:
                            self.logger.error(f"Failed to develop tool: {unknown_tool['tool_name']}")
                            all_tools_developed = False
                            break
                    
                    # Retry original phase if all tools were developed
                    if all_tools_developed:
                        self.logger.info(f"🔄 Retrying {phase_name} with newly developed tools")
                        result = phase.run(task=task)

                
                # Record phase run
                state = self.state_manager.load()  # Reload in case phase modified it
                if phase_name in state.phases:
                    state.phases[phase_name].record_run(result.success)
                self.state_manager.save(state)
                
                # Write phase state markdown
                if hasattr(phase, 'generate_state_markdown'):
                    md_content = phase.generate_state_markdown(state)
                    self.state_manager.write_phase_state(phase_name, md_content)
                
                # Log result
                if result.success:
                    self.logger.info(f"  ✅ {result.message}")
                else:
                    self.logger.warning(f"  ⚠️ {result.message}")
                
                # Show project status
                self._show_project_status(state)
                
            except Exception as e:
                self.logger.error(f"  ❌ Phase error: {e}")
                if self.verbose:
                    import traceback
                    self.logger.debug(traceback.format_exc())
                
                # Record failure
                state = self.state_manager.load()
                if phase_name in state.phases:
                    state.phases[phase_name].record_run(False)
                self.state_manager.save(state)
        
        # Reached max iterations
        self.logger.info(f"\n✅ Completed {iteration} iterations")
        return self._summarize_run()
    
    def _determine_next_action(self, state: PipelineState) -> Dict:
        """
        Determine the next action to take based on current state.
        
        IMPORTANT: This method NEVER returns None. It always finds work to do.
        
        Priority order:
        1. Initial planning if no tasks exist
        2. QA for code awaiting review
        3. Debugging for code needing fixes
        4. Coding for new/in-progress tasks
        5. Documentation update if tasks recently completed
        6. Project planning if ALL tasks complete (creates new tasks)
        
        Returns:
            Dict with 'phase', 'reason', and optionally 'task'
        """
        
        # 1. Initial planning needed (no tasks at all)
        if state.needs_planning:
            return {
                "phase": "planning",
                "reason": "initial_planning"
            }
        
        # 2. Tasks awaiting QA review
        for task in state.tasks.values():
            if task.status == TaskStatus.QA_PENDING:
                return {
                    "phase": "qa",
                    "task": task,
                    "reason": "review_new_code"
                }
        
        # 3. Tasks needing fixes (from QA issues)
        for task in state.tasks.values():
            if task.status == TaskStatus.NEEDS_FIXES:
                if task.attempts < self.config.max_retries_per_task:
                    return {
                        "phase": "debugging",
                        "task": task,
                        "reason": "fix_issues"
                    }
                else:
                    # Max retries exceeded, skip this task
                    task.status = TaskStatus.SKIPPED
                    task.updated_at = datetime.now().isoformat()
                    self.state_manager.save(state)
                    self.logger.warning(f"  Skipping task {task.task_id} after {task.attempts} attempts")
        
        # 4. New or in-progress tasks (sorted by priority)
        pending_tasks = [
            t for t in state.tasks.values()
            if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
            and t.attempts < self.config.max_retries_per_task
        ]
        
        if pending_tasks:
            # Sort by priority (lower = higher priority)
            pending_tasks.sort(key=lambda t: (t.priority, t.task_id))
            
            for task in pending_tasks:
                if self._dependencies_met(state, task):
                    return {
                        "phase": "coding",
                        "task": task,
                        "reason": "implement_new"
                    }
            
            # If we have pending tasks but dependencies not met, wait
            self.logger.debug("  Pending tasks waiting on dependencies")
        
        # 5. All tasks complete - check if documentation needs update
        if state.needs_documentation_update:
            return {
                "phase": "documentation",
                "reason": "update_docs_after_completion"
            }
        
        # 6. Self-improvement cycle - evaluate and improve custom tools/prompts/roles
        # Check if we should run improvement phases
        if self._should_run_improvement_cycle(state):
            # Determine which improvement phase to run
            improvement_phase = self._get_next_improvement_phase(state)
            if improvement_phase:
                return improvement_phase
        
        # 7. ALL tasks complete and docs updated - trigger project planning
        # This is the KEY change: instead of returning None/exiting, we plan expansion
        return {
            "phase": "project_planning",
            "reason": "expand_project"
        }
    
    def _should_run_improvement_cycle(self, state: PipelineState) -> bool:
        """
        Determine if we should run self-improvement cycle.
        
        Run improvement cycle when:
        - All tasks are complete
        - Custom tools/prompts/roles exist
        - Haven't run improvement recently
        
        Args:
            state: Current pipeline state
            
        Returns:
            True if should run improvement cycle
        """
        # Check if all tasks are complete
        if not state.tasks:
            return False
        
        all_complete = all(
            task.status == TaskStatus.COMPLETED
            for task in state.tasks.values()
        )
        
        if not all_complete:
            return False
        
        # Check if custom tools/prompts/roles exist
        custom_tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        custom_prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        custom_roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        
        has_custom_tools = custom_tools_dir.exists() and any(custom_tools_dir.glob("*_spec.json"))
        has_custom_prompts = custom_prompts_dir.exists() and any(custom_prompts_dir.glob("*.json"))
        has_custom_roles = custom_roles_dir.exists() and any(custom_roles_dir.glob("*.json"))
        
        return has_custom_tools or has_custom_prompts or has_custom_roles
    
    def _get_next_improvement_phase(self, state: PipelineState) -> Optional[Dict]:
        """
        Get the next improvement phase to run.
        
        Priority order:
        1. Tool evaluation
        2. Prompt improvement
        3. Role improvement
        
        Args:
            state: Current pipeline state
            
        Returns:
            Phase action dict or None
        """
        # Check which improvement phases have been run
        tool_eval_runs = state.phases.get("tool_evaluation", None)
        prompt_imp_runs = state.phases.get("prompt_improvement", None)
        role_imp_runs = state.phases.get("role_improvement", None)
        
        # Check what exists
        custom_tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        custom_prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        custom_roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        
        has_custom_tools = custom_tools_dir.exists() and any(custom_tools_dir.glob("*_spec.json"))
        has_custom_prompts = custom_prompts_dir.exists() and any(custom_prompts_dir.glob("*.json"))
        has_custom_roles = custom_roles_dir.exists() and any(custom_roles_dir.glob("*.json"))
        
        # Priority 1: Tool evaluation (if tools exist and not recently evaluated)
        if has_custom_tools:
            if not tool_eval_runs or tool_eval_runs.run_count == 0:
                return {
                    "phase": "tool_evaluation",
                    "reason": "evaluate_custom_tools"
                }
        
        # Priority 2: Prompt improvement (if prompts exist and not recently improved)
        if has_custom_prompts:
            if not prompt_imp_runs or prompt_imp_runs.run_count == 0:
                return {
                    "phase": "prompt_improvement",
                    "reason": "improve_custom_prompts"
                }
        
        # Priority 3: Role improvement (if roles exist and not recently improved)
        if has_custom_roles:
            if not role_imp_runs or role_imp_runs.run_count == 0:
                return {
                    "phase": "role_improvement",
                    "reason": "improve_custom_roles"
                }
        
        # All improvement phases have been run at least once
        return None
    
    def _dependencies_met(self, state: PipelineState, task: TaskState) -> bool:
        """Check if all dependencies for a task are completed"""
        if not task.dependencies:
            return True
        
        for dep_file in task.dependencies:
            # Check if any completed task created this file
            dep_met = False
            for other_task in state.tasks.values():
                if other_task.target_file == dep_file:
                    if other_task.status == TaskStatus.COMPLETED:
                        dep_met = True
                        break
            
            # Also check if file already exists
            if not dep_met:
                dep_path = self.project_dir / dep_file
                if dep_path.exists():
                    dep_met = True
            
            if not dep_met:
                return False
        
        return True
    
    def _show_project_status(self, state: PipelineState) -> None:
        """Show current project file status"""
        self.logger.info(f"\n📁 PROJECT: {self.project_dir}")
        self.logger.info("─" * 50)
        
        # List project files
        py_files = sorted(self.project_dir.rglob("*.py"))
        
        for py_file in py_files:
            if ".pipeline" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            rel_path = py_file.relative_to(self.project_dir)
            size = py_file.stat().st_size
            
            # Check if this file has a completed task
            completed = any(
                t.target_file == str(rel_path) and t.status == TaskStatus.COMPLETED
                for t in state.tasks.values()
            )
            
            # Check if it's new (QA pending or just created)
            is_new = any(
                t.target_file == str(rel_path) and t.status == TaskStatus.QA_PENDING
                for t in state.tasks.values()
            )
            
            icon = "✓" if completed else ("○" if is_new else "✓")
            self.logger.info(f"   {icon} {rel_path} ({size} bytes)")
        
        self.logger.info("─" * 50)
    
    def _print_banner(self) -> None:
        """Print pipeline banner"""
        self.logger.info("=" * 70)
        self.logger.info("  AI DEVELOPMENT PIPELINE v2 - State-Managed Architecture")
        self.logger.info("=" * 70)
        self.logger.info(f"\n  Project: {self.project_dir}")
        self.logger.info(f"  Max retries: {self.config.max_retries_per_task}")
        
        if self.config.max_iterations > 0:
            self.logger.info(f"  Max iterations: {self.config.max_iterations}")
        else:
            self.logger.info(f"  Max iterations: ∞")
        
        if self.verbose:
            self.logger.info(f"  Verbose: ON")
        
        self.logger.info("=" * 70)
    
    def _summarize_run(self) -> bool:
        """Print run summary and return success status"""
        state = self.state_manager.load()
        
        total = len(state.tasks)
        completed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.SKIPPED)
        
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"  📊 PIPELINE SUMMARY")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"  Total tasks: {total}")
        self.logger.info(f"  Completed: {completed}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Skipped: {total - completed - failed}")
        
        # Count iterations from phase runs
        total_iterations = sum(p.run_count for p in state.phases.values()) // 2  # Rough estimate
        self.logger.info(f"  Iterations: {total_iterations}")
        
        if state.expansion_count > 0:
            self.logger.info(f"  Expansion cycles: {state.expansion_count}")
        
        self.logger.info(f"{'='*70}")
        
        # Phase statistics
        self.logger.info(f"\n  Phase Statistics:")
        for name, phase in state.phases.items():
            if phase.run_count > 0:
                self.logger.info(f"    {name}: {phase.run_count} runs, {phase.success_count} success, {phase.failure_count} failed")
        
        self.logger.info(f"{'='*70}")
        
        return completed > 0 or total == 0
