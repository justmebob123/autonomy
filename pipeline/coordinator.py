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
        
        # Minimum time between iterations to prevent spinning
        min_interval = 2.0
        last_iteration_time = 0
        
        while iteration < max_iter:
            # Rate limiting
            elapsed = time.time() - last_iteration_time
            if elapsed < min_interval and last_iteration_time > 0:
                time.sleep(min_interval - elapsed)
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
        
        # 6. ALL tasks complete and docs updated - trigger project planning
        # This is the KEY change: instead of returning None/exiting, we plan expansion
        return {
            "phase": "project_planning",
            "reason": "expand_project"
        }
    
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
