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
