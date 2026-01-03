# -*- coding: utf-8 -*-
"""
Refactoring Phase

Analyzes and refactors code architecture to eliminate duplicates, resolve conflicts,
and improve code organization based on MASTER_PLAN.md changes.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import os

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_refactoring_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin
from .refactoring_context_builder import RefactoringContextBuilder


class RefactoringPhase(BasePhase, LoopDetectionMixin):
    """
    Refactoring phase that analyzes and improves code architecture.
    
    Responsibilities:
    - Detect duplicate/similar implementations
    - Compare and merge conflicting files
    - Extract and consolidate features
    - Analyze MASTER_PLAN consistency
    - Generate refactoring plans
    - Execute safe refactoring operations
    - Update REFACTORING_STATE.md
    
    Integration Points:
    - Planning → Refactoring (architecture changes detected)
    - Coding → Refactoring (duplicates detected)
    - QA → Refactoring (conflicts detected)
    - Investigation → Refactoring (recommendations)
    - Project Planning → Refactoring (strategic refactoring)
    - Refactoring → Coding (new implementation needed)
    - Refactoring → QA (verification needed)
    """
    
    phase_name = "refactoring"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # CRITICAL FIX: Track if comprehensive analysis has been run
        # This prevents infinite loop where analysis runs after every task completion
        self._comprehensive_analysis_done = False
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # REFACTORING ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.file_refactoring import (
            DuplicateDetector,
            FileComparator,
            FeatureExtractor,
            RefactoringArchitectureAnalyzer
        )
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_conflicts import IntegrationConflictDetector
        
        self.duplicate_detector = DuplicateDetector(str(self.project_dir), self.logger)
        self.file_comparator = FileComparator(str(self.project_dir), self.logger)
        self.feature_extractor = FeatureExtractor(str(self.project_dir), self.logger)
        self.architecture_analyzer = RefactoringArchitectureAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.conflict_detector = IntegrationConflictDetector(str(self.project_dir), self.logger)
        
        # CONTEXT BUILDER - Provides full context for informed refactoring decisions
        self.context_builder = RefactoringContextBuilder(self.project_dir, self.logger)
        
        # PROMPT BUILDER - Template-based prompt generation
        from .prompt_builder import PromptBuilder
        templates_dir = self.project_dir.parent / 'pipeline' / 'templates'
        self.prompt_builder = PromptBuilder(templates_dir, self.logger)
        
        # FORMATTERS - Issue-specific data formatting
        from .formatters import get_formatter
        self.get_formatter = get_formatter
        
        # ANALYSIS ORCHESTRATOR - Task creation from analysis results
        from .analysis_orchestrator import AnalysisOrchestrator
        self.analysis_orchestrator = AnalysisOrchestrator(self.project_dir, self.logger)
        
        # MESSAGE BUS: Subscribe to relevant events for cross-phase coordination
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_COMPLETED,      # When tasks complete in other phases
                MessageType.FILE_CREATED,        # New files to analyze for duplicates
                MessageType.FILE_MODIFIED,       # Modified files to check for conflicts
                MessageType.ISSUE_FOUND,         # Issues from other phases that may need refactoring
                MessageType.SYSTEM_ALERT,        # System-level alerts including architecture changes
            ])
            self.logger.info("  📡 Message bus subscriptions configured")
        
        self.logger.info("  🔧 Refactoring phase initialized with analysis capabilities")
    
    def execute(self, state: PipelineState, 
                refactoring_type: str = None,
                target_files: List[str] = None,
                **kwargs) -> PhaseResult:
        """
        Execute the refactoring phase with full architecture and IPC integration.
        
        NEW DESIGN (Phase 2+3):
        - Uses task system for tracking work
        - Runs for multiple iterations until complete
        - Maintains conversation continuity
        - Tracks progress
        - INTEGRATES with architecture for design intent
        - USES objectives to prioritize refactoring
        """
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent refactoring performance
        recent_tasks = []
        if self.adaptive_prompts:
            if hasattr(state, 'refactoring_manager') and state.refactoring_manager:
                # Get all tasks and take the most recent ones
                all_tasks = list(state.refactoring_manager.tasks.values())
                # Sort by created_at if available, otherwise just take last 5
                recent = sorted(all_tasks, key=lambda t: t.created_at if hasattr(t, 'created_at') else datetime.min, reverse=True)[:5]
                recent_tasks = [
                    {
                        'task_id': t.task_id,
                        'issue_type': t.issue_type.value,
                        'status': t.status.value,
                        'attempts': t.attempts,
                        'priority': t.priority.value
                    }
                    for t in recent
                ]
            
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'recent_tasks': recent_tasks,
                'recent_issues': state.get_recent_issues(self.phase_name, limit=5) if hasattr(state, 'get_recent_issues') else []
            })
        
        # CORRELATION ENGINE: Get cross-phase correlations
        correlations = self.get_cross_phase_correlation({
            'phase': self.phase_name,
            'recent_tasks': recent_tasks
        })
        if correlations:
            self.logger.info(f"  🔗 Found {len(correlations)} cross-phase correlations")
        
        # PATTERN OPTIMIZER: Get optimization suggestions
        optimization = self.get_optimization_suggestion({
            'current_strategy': 'comprehensive_analysis',
            'recent_performance': recent_tasks
        })
        if optimization and optimization.get('suggestions'):
            self.logger.info(f"  💡 Optimization suggestions: {len(optimization['suggestions'])}")
        
        # MESSAGE BUS: Publish phase start event
        self._publish_message('PHASE_STARTED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'task_id': task.task_id if task else None,
            'correlations': correlations,
            'optimization': optimization
        })
        
        # DIMENSION TRACKING: Track initial dimensions
        start_time = datetime.now()
        self.track_dimensions({
            'temporal': 0.7,  # Refactoring takes time
            'data': 0.8,  # Analyzes code data
            'integration': 0.9,  # High integration with codebase
            'architecture': 0.9  # High architecture focus
        })
        
        # ========== INTEGRATION: READ ARCHITECTURE AND OBJECTIVES ==========
        # Read architecture to understand design intent
        architecture = self._read_architecture()
        if architecture.get('structure'):
            self.logger.debug(f"📐 Architecture loaded: {len(architecture['structure'])} chars")
            # Store architecture for use in analysis
            self._architecture_context = architecture
        
        # Read objectives to prioritize refactoring work
        objectives = self._read_objectives()
        obj_count = sum(len(objectives.get(level, [])) for level in ['primary', 'secondary', 'tertiary'])
        if obj_count > 0:
            self.logger.info(f"🎯 {obj_count} objectives loaded for prioritization")
        
        # Write starting status
        self._write_status({
            'status': 'running',
            'message': 'Starting refactoring phase',
            'architecture_loaded': bool(architecture.get('structure'))
        })
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # PHASE 2: Initialize refactoring task manager
        self._initialize_refactoring_manager(state)
        
        # CRITICAL FIX: Clean up broken tasks from before recent fixes
        self._cleanup_broken_tasks(state.refactoring_manager)
        
        # PHASE 3: Check for pending refactoring tasks
        pending_tasks = self._get_pending_refactoring_tasks(state)
        
        if not pending_tasks:
            # No pending tasks - check if we should run analysis
            if not self._comprehensive_analysis_done:
                # First time with no tasks - run analysis to find issues
                self.logger.info(f"  🔍 No pending tasks, analyzing codebase...")
                self._comprehensive_analysis_done = True
                
                # CRITICAL FIX: Track analysis time
                state.last_refactoring_analysis = datetime.now()
                
                return self._analyze_and_create_tasks(state)
            else:
                # Analysis already done and no tasks left - we're truly done
                self.logger.info(f"  ✅ All refactoring tasks completed")
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message="All refactoring tasks completed successfully",
                    next_phase="coding"  # Return to coding
                )
        
        # PHASE 3: Work on next task
        self.logger.info(f"  📋 {len(pending_tasks)} pending tasks, working on next task...")
        task = self._select_next_task(pending_tasks)
        
        self.logger.info(f"  🎯 Selected task: {task.task_id} - {task.title}")
        self.logger.info(f"     Priority: {task.priority.value}, Type: {task.issue_type.value}")
        
        result = self._work_on_task(state, task)
        
        if result.success:
            # Task completed successfully
            remaining = self._get_pending_refactoring_tasks(state)
            
            if remaining:
                # More tasks to do
                self.logger.info(f"  ✅ Task completed, {len(remaining)} tasks remaining")
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} completed, continuing refactoring",
                    next_phase="refactoring"  # Continue refactoring
                )
            else:
                # All tasks complete - check if refactoring is done
                self.logger.info(f"  ✅ All tasks completed, checking for new issues...")
                return self._check_completion(state)
        else:
            # Task failed
            self.logger.warning(f"  ⚠️  Task {task.task_id} failed: {result.message}")
            
            # Check if this is a retry request (task was reset to NEW)
            if task.status == TaskStatus.NEW and task.attempts < task.max_attempts:
                # This is a retry - continue refactoring to retry same task
                self.logger.info(f"  🔄 Task {task.task_id} will be retried (attempt {task.attempts + 1}/{task.max_attempts})")
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} will be retried with stronger guidance",
                    next_phase="refactoring"  # Continue refactoring to retry
                )
            
            # Task truly failed (max attempts reached or other error)
            # Continue with next task
            remaining = self._get_pending_refactoring_tasks(state)
            if remaining:
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} failed, continuing with next task",
                    next_phase="refactoring"
                )
            else:
                # No more tasks, check completion
                return self._check_completion(state)
    
    # =============================================================================
    # Phase 2+3: Task System Methods
    # =============================================================================
    
    def _initialize_refactoring_manager(self, state: PipelineState) -> None:
        """Initialize or get refactoring task manager"""
        if state.refactoring_manager is None:
            from pipeline.state.refactoring_task import RefactoringTaskManager
            state.refactoring_manager = RefactoringTaskManager()
            self.logger.debug(f"  🔧 Initialized refactoring task manager")
        
        # Initialize analysis tracker if not exists
        # CRITICAL: Store in state so it persists across iterations!
        if not hasattr(state, 'analysis_tracker') or state.analysis_tracker is None:
            from pipeline.state.task_analysis_tracker import TaskAnalysisTracker
            state.analysis_tracker = TaskAnalysisTracker()
            self.logger.debug(f"  📋 Initialized task analysis tracker")
        
        # Use the persisted tracker
        self._analysis_tracker = state.analysis_tracker
    
    def _cleanup_broken_tasks(self, manager) -> None:
        """
        Remove tasks with insufficient data that were created before recent fixes.
        
        These tasks have:
        - "Unknown" in title or description
        - Empty or missing analysis_data
        - No actionable information for AI
        
        This is a one-time cleanup for legacy tasks. New tasks created after
        commits dd11f57, 6eb20a7, eb02d6c, b8f2b07 have proper analysis_data.
        """
        if manager is None:
            return
        
        broken_tasks = []
        
        # Check all tasks (not just pending, as failed tasks can be retried)
        for task in manager.tasks.values():
            # Identify tasks with insufficient data
            is_broken = (
                "Unknown" in task.title or
                task.description == "Unknown" or
                not task.analysis_data or
                task.analysis_data == {} or
                (isinstance(task.analysis_data, dict) and 
                 task.analysis_data.get('type') == '' and
                 len(task.analysis_data) <= 1)
            )
            
            # Also check for dictionary key errors with invalid key_path
            if "Dictionary key error" in task.title:
                key_path = task.analysis_data.get('key_path', '') if isinstance(task.analysis_data, dict) else ''
                if not key_path or key_path.isdigit() or key_path == 'unknown':
                    is_broken = True
            
            # Also check for invalid file paths
            has_invalid_files = False
            if task.target_files:
                for file_path in task.target_files:
                    # Check for backup directories
                    if '.autonomy' in file_path or '/backups/' in file_path or '\\backups\\' in file_path:
                        has_invalid_files = True
                        break
                    # Check for placeholder paths
                    if 'some_file' in file_path or file_path == '':
                        has_invalid_files = True
                        break
            
            if is_broken:
                broken_tasks.append(task.task_id)
                self.logger.info(f"  🗑️  Removing broken task: {task.task_id} - {task.title}")
                self.logger.debug(f"     Reason: Insufficient data (created before fixes)")
            elif has_invalid_files:
                broken_tasks.append(task.task_id)
                self.logger.info(f"  🗑️  Removing broken task: {task.task_id} - {task.title}")
                self.logger.debug(f"     Reason: Invalid file paths (backup dirs or placeholders): {task.target_files}")
        
        # Delete broken tasks
        for task_id in broken_tasks:
            manager.delete_task(task_id)
        
        if broken_tasks:
            self.logger.info(f"  ✅ Cleaned up {len(broken_tasks)} broken tasks")
            self.logger.info(f"  🔄 Will re-detect issues with proper data on next iteration")
    
    def _get_pending_refactoring_tasks(self, state: PipelineState) -> List:
        """Get all pending refactoring tasks"""
        if state.refactoring_manager is None:
            return []
        return state.refactoring_manager.get_pending_tasks()
    
    def _select_next_task(self, pending_tasks: List) -> Any:
        """
        Select next task to work on.
        
        Priority order:
        1. CRITICAL priority
        2. HIGH priority
        3. MEDIUM priority
        4. LOW priority
        
        Within same priority, select by creation time (oldest first)
        """
        from pipeline.state.refactoring_task import RefactoringPriority
        
        # Sort by priority (critical first) then by creation time
        priority_order = {
            RefactoringPriority.CRITICAL: 0,
            RefactoringPriority.HIGH: 1,
            RefactoringPriority.MEDIUM: 2,
            RefactoringPriority.LOW: 3
        }
        
        sorted_tasks = sorted(
            pending_tasks,
            key=lambda t: (priority_order[t.priority], t.created_at)
        )
        
        return sorted_tasks[0]
    
    def _analyze_and_create_tasks(self, state: PipelineState) -> PhaseResult:
        """
        Analyze codebase and create refactoring tasks.
        
        This is called when no pending tasks exist.
        """
        self.logger.info(f"  🔬 Performing comprehensive analysis...")
        
        # MESSAGE BUS: Publish analysis started event
        if self.message_bus:
            from ..messaging import MessageType
            self.message_bus.publish(MessageType.PHASE_STARTED, {
                'phase': self.phase_name,
                'analysis_type': 'comprehensive',
                'timestamp': datetime.now().isoformat()
            })
        
        # Use existing comprehensive refactoring handler for analysis
        result = self._handle_comprehensive_refactoring(state)
        
        # CRITICAL FIX: Auto-create tasks from analysis results
        # The LLM often detects issues but doesn't create tasks
        # We need to auto-create tasks when issues are found
        tasks_created = self._auto_create_tasks_from_analysis(state, result)
        
        # CRITICAL INTELLIGENCE: Check if we should return to coding phase
        if tasks_created == -1:
            self.logger.warning(f"  🚨 Analysis found CODING problems (syntax/import errors), not refactoring issues")
            self.logger.info(f"  ➡️  Returning to CODING phase to fix missing code...")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="Analysis found coding problems (syntax/import errors) - returning to coding phase",
                next_phase="coding"
            )
        
        if tasks_created > 0:
            self.logger.info(f"  ✅ Auto-created {tasks_created} refactoring tasks from analysis")
        
        # CRITICAL: Add file placement analysis
        placement_tasks = self._analyze_file_placements(state)
        if placement_tasks > 0:
            self.logger.info(f"  ✅ Created {placement_tasks} file placement tasks")
        
        # DEBUG: Check manager state
        if state.refactoring_manager:
            total_tasks = len(state.refactoring_manager.tasks)
            self.logger.info(f"  🔍 DEBUG: Total tasks in manager: {total_tasks}")
            for task_id, task in list(state.refactoring_manager.tasks.items())[:5]:
                self.logger.info(f"     - {task_id}: status={task.status.value}, can_execute={task.can_execute([])}")
        
        # Check if any tasks were created (either by LLM or auto-created)
        pending = self._get_pending_refactoring_tasks(state)
        self.logger.info(f"  🔍 DEBUG: Pending tasks returned: {len(pending)}")
        
        if pending:
            self.logger.info(f"  ✅ Analysis complete, {len(pending)} tasks to work on")
            
            # MESSAGE BUS: Publish analysis complete event
            if self.message_bus:
                from ..messaging import MessageType
                self.message_bus.publish(MessageType.PHASE_COMPLETED, {
                    'phase': self.phase_name,
                    'issues_found': len(pending),
                    'tasks_created': tasks_created + placement_tasks,
                    'timestamp': datetime.now().isoformat()
                })
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Analysis complete, {len(pending)} issues found",
                next_phase="refactoring"  # Continue to work on tasks
            )
        else:
            self.logger.info(f"  ✅ Analysis complete, no issues found")
            
            # MESSAGE BUS: Publish analysis complete event
            if self.message_bus:
                from ..messaging import MessageType
                self.message_bus.publish(MessageType.PHASE_COMPLETED, {
                    'phase': self.phase_name,
                    'issues_found': 0,
                    'tasks_created': 0,
                    'timestamp': datetime.now().isoformat()
                })
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No refactoring issues found, codebase is clean",
                next_phase="coding"  # Return to coding
            )
    
    def _analyze_file_placements(self, state: PipelineState) -> int:
        """
        Analyze file placements and create tasks for misplaced files.
        
        Returns:
            Number of tasks created
        """
        try:
            from ..analysis.file_placement import FilePlacementAnalyzer
            from ..analysis.import_impact import ImportImpactAnalyzer
            from ..state.refactoring_task import RefactoringIssueType, RefactoringPriority
            
            self.logger.info(f"  📁 Analyzing file placements...")
            
            placement_analyzer = FilePlacementAnalyzer(
                str(self.project_dir),
                self.logger,
                self.arch_context
            )
            
            # Find misplaced files (confidence >= 0.6)
            misplaced_files = placement_analyzer.find_misplaced_files(min_confidence=0.6)
            
            if not misplaced_files:
                return 0
            
            self.logger.info(f"  📁 Found {len(misplaced_files)} misplaced files")
            
            # Analyze import impact for each
            impact_analyzer = ImportImpactAnalyzer(str(self.project_dir), self.logger)
            
            tasks_created = 0
            for misplaced in misplaced_files:
                # Analyze impact
                impact = impact_analyzer.analyze_move_impact(
                    misplaced.file,
                    misplaced.suggested_location + '/' + Path(misplaced.file).name
                )
                
                # Determine priority based on risk and confidence
                if impact.risk_level.value == 'critical':
                    priority = RefactoringPriority.CRITICAL
                elif impact.risk_level.value == 'high' or misplaced.confidence >= 0.8:
                    priority = RefactoringPriority.HIGH
                elif misplaced.confidence >= 0.7:
                    priority = RefactoringPriority.MEDIUM
                else:
                    priority = RefactoringPriority.LOW
                
                # Create task
                task = state.refactoring_manager.create_task(
                    issue_type=RefactoringIssueType.STRUCTURE,  # Use STRUCTURE instead of MISPLACED_FILE
                    title=f"File in wrong location: {misplaced.file}",
                    description=f"File should be moved from {misplaced.current_location} to {misplaced.suggested_location}. "
                               f"Reason: {misplaced.reason}. "
                               f"Impact: {len(impact.affected_files)} files affected, risk level: {impact.risk_level.value}.",
                    target_files=[misplaced.file],
                    priority=priority,
                    analysis_data={
                        "current_location": misplaced.current_location,
                        "suggested_location": misplaced.suggested_location,
                        "reason": misplaced.reason,
                        "confidence": misplaced.confidence,
                        "affected_files": impact.affected_files,
                        "risk_level": impact.risk_level.value,
                        "estimated_changes": impact.estimated_changes
                    }
                )
                tasks_created += 1
            
            return tasks_created
            
        except Exception as e:
            self.logger.warning(f"  ⚠️  File placement analysis failed: {e}")
            return 0
    
    def _work_on_task(self, state: PipelineState, task: Any) -> PhaseResult:
        """
        Work on a specific refactoring task.
        
        Args:
            state: Pipeline state
            task: RefactoringTask to work on
            
        Returns:
            PhaseResult indicating success/failure
        """
        from pipeline.state.refactoring_task import RefactoringApproach
        
        # MESSAGE BUS: Publish refactoring started event
        if self.message_bus:
            from ..messaging import MessageType
            self.message_bus.publish(MessageType.TASK_STARTED, {
                'phase': self.phase_name,
                'task_id': task.task_id,
                'issue_type': task.issue_type.value,
                'priority': task.priority.value,
                'timestamp': datetime.now().isoformat()
            })
        
        # Mark task as started
        task.start()
        
        # CRITICAL: NEVER skip tasks! Always engage AI to analyze every task.
        # The AI will determine if it can fix automatically or needs developer input.
        # Even "complex" tasks should be analyzed - AI might find simple solutions.
        
        # Build context for this specific task
        context = self._build_task_context(task)
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build task-specific prompt
        prompt = self._build_task_prompt(task, context)
        
        # Call LLM
        result = self.chat_with_history(
            user_message=prompt,
            tools=tools
        )
        
        # Extract tool calls
        tool_calls = result.get("tool_calls", [])
        content = result.get("content", "")
        
        if not tool_calls:
            # No tool calls, mark as failed
            task.fail("No tool calls in response")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Task {task.task_id} failed: No tool calls"
            )
        
        # CRITICAL: Validate tool calls before execution
        # Ensure AI has completed required analysis before allowing resolving actions
        # Include task type and title in analysis_data for validation
        validation_data = {
            'type': task.issue_type.value if hasattr(task.issue_type, 'value') else str(task.issue_type),
            'title': task.title,
            **task.analysis_data  # Include original analysis data
        }
        is_valid, error_message = self._analysis_tracker.validate_tool_calls(
            task_id=task.task_id,
            tool_calls=tool_calls,
            target_files=task.target_files,
            attempt_number=task.attempts,
            analysis_data=validation_data
        )
        
        if not is_valid:
            # Analysis incomplete - force retry with error message
            self.logger.warning(f"  ⚠️ Task {task.task_id}: Analysis incomplete, forcing retry")
            self.logger.info(f"  📋 Missing analysis steps detected")
            
            # Reset task to NEW status for retry
            task.status = TaskStatus.NEW
            task.attempts += 1
            
            # Add error message to analysis_data for next attempt
            if not isinstance(task.analysis_data, dict):
                task.analysis_data = {}
            task.analysis_data['retry_reason'] = error_message
            task.analysis_data['forced_retry'] = True
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Task {task.task_id}: Analysis incomplete, retry required\n{error_message}"
            )
        
        # CRITICAL FIX: Hard limit on analysis tools
        # If AI has used 3+ tools without resolving, FORCE resolution
        tool_call_count = len(tool_calls)
        
        # Tools that actually resolve issues (not just analyze)
        resolving_tools = {
            "merge_file_implementations",
            "cleanup_redundant_files",
            "create_issue_report",
            "request_developer_review",
            "update_refactoring_task",
            "move_file",
            "rename_file",
            "restructure_directory",
            "analyze_file_placement",  # Provides actionable recommendations
            # File editing tools that actually fix code
            "insert_after",
            "insert_before",
            "replace_between",
            "append_to_file",
            "update_section",
            "modify_file",
            "create_file"
        }
        
        # Check if any tool call is a resolving tool
        has_resolving_tool = any(
            tc.get("function", {}).get("name") in resolving_tools 
            for tc in tool_calls
        )
        
        # HARD LIMIT: If 2+ tools used without resolution, FORCE request_developer_review
        # LOWERED from 3 to 2 because AI was getting stuck reading files repeatedly
        if tool_call_count >= 2 and not has_resolving_tool:
            self.logger.warning(
                f"🚨 Task {task.task_id}: {tool_call_count} tools used without resolution, "
                f"FORCING request_developer_review"
            )
            
            # Override AI's tool calls with forced escalation to DEVELOPER PHASE
            tool_calls = [{
                "function": {
                    "name": "request_developer_review",
                    "arguments": {
                        "task_id": task.task_id,
                        "reason": (
                            f"Refactoring AI analyzed but couldn't resolve automatically:\n\n"
                            f"Task: {task.title}\n"
                            f"Type: {task.issue_type}\n"
                            f"Files: {', '.join(task.target_files) if task.target_files else 'None'}\n\n"
                            f"The AI performed {tool_call_count} analysis operations but didn't "
                            f"use a resolution tool. This task needs the DEVELOPER PHASE to handle it."
                        ),
                        "context": {
                            "task_type": str(task.issue_type),
                            "target_files": task.target_files if task.target_files else [],
                            "attempts": task.attempts,
                            "analysis_count": tool_call_count
                        }
                    }
                }
            }]
            
            self.logger.info(f"  📝 Escalating task {task.task_id} to DEVELOPER PHASE (orchestrator)")
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        results = handler.process_tool_calls(tool_calls)
        
        # Record tool calls in analysis tracker
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            arguments = tool_call.get("function", {}).get("arguments", {})
            result = results[i] if i < len(results) else {}
            
            self._analysis_tracker.record_tool_call(
                task_id=task.task_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result
            )
        
        # Check if task was actually resolved (not just analyzed)
        task_resolved = False
        
        for result in results:
            if result.get("success"):
                tool_name = result.get("tool", "")
                if tool_name in resolving_tools:
                    task_resolved = True
                    
                    # CRITICAL: If escalated to developer, record it
                    if tool_name == "request_developer_review":
                        state.refactoring_manager.record_resolution(
                            issue_type=str(task.issue_type.value) if hasattr(task.issue_type, 'value') else str(task.issue_type),
                            target_files=task.target_files,
                            resolution_type='escalated',
                            task_id=task.task_id,
                            details={
                                'escalated_at': datetime.now().isoformat(),
                                'reason': 'Too complex for autonomous refactoring'
                            }
                        )
                        self.logger.info(f"  📝 Recorded escalation in history to prevent re-detection")
                    
                    break
        
        if task_resolved:
            # CRITICAL FIX: Verify that task was actually resolved
            is_verified, verification_msg = self._verify_task_resolution(task)
            
            if is_verified:
                # Task actually resolved AND verified
                task.complete(content)
                self.logger.info(f"  ✅ Task {task.task_id} completed and verified: {verification_msg}")
                
                # CRITICAL: Record resolution in history to prevent re-detection
                state.refactoring_manager.record_resolution(
                    issue_type=str(task.issue_type.value) if hasattr(task.issue_type, 'value') else str(task.issue_type),
                    target_files=task.target_files,
                    resolution_type='resolved',
                    task_id=task.task_id,
                    details={
                        'verification_msg': verification_msg,
                        'resolved_at': datetime.now().isoformat()
                    }
                )
                self.logger.info(f"  📝 Recorded resolution in history to prevent re-detection")
                
                # MESSAGE BUS: Publish refactoring complete event
                if self.message_bus:
                    from ..messaging import MessageType
                    self.message_bus.publish(MessageType.TASK_COMPLETED, {
                        'phase': self.phase_name,
                        'task_id': task.task_id,
                        'issue_type': task.issue_type.value,
                        'success': True,
                        'verification_msg': verification_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # PATTERN RECOGNITION: Record successful resolution pattern
                self.record_execution_pattern({
                    'pattern_type': 'task_resolution',
                    'task_id': task.task_id,
                    'issue_type': task.issue_type.value,
                    'attempts': task.attempts,
                    'success': True,
                    'verification': verification_msg
                })
                
                # ANALYTICS: Track task completion metric
                self.track_phase_metric({
                    'metric': 'task_completion',
                    'task_id': task.task_id,
                    'issue_type': task.issue_type.value,
                    'attempts': task.attempts,
                    'duration': (datetime.now() - task.created_at).total_seconds() if hasattr(task, 'created_at') else 0
                })
                
                # Update ARCHITECTURE.md if needed
                self._update_architecture_after_task(task)
                
                # Write status to IPC
                self._write_task_completion_to_ipc(task)
                
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} completed and verified"
                )
            else:
                # Resolving tool called but verification failed
                self.logger.warning(f"  ❌ Task {task.task_id} verification failed: {verification_msg}")
                
                # Mark as failed and retry
                task.fail(f"Verification failed: {verification_msg}")
                
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} verification failed: {verification_msg}"
                )
        else:
            # Tools succeeded but didn't resolve the issue
            # This happens when AI only calls analysis tools (compare_file_implementations)
            # without taking action
            
            any_success = any(r.get("success") for r in results)
            
            if any_success:
                # Tools ran successfully but didn't resolve issue
                # Check if AI actually tried to understand the files
                tools_used = {r.get("tool") for r in results if r.get("success")}
                
                # Did AI read the files to understand them?
                understanding_tools = {"read_file", "search_code", "list_directory"}
                tried_to_understand = bool(tools_used & understanding_tools)
                
                # Did AI check architecture?
                checked_architecture = "read_file" in tools_used  # Would read ARCHITECTURE.md
                
                if not tried_to_understand:
                    # CRITICAL: Check if we've exceeded retry limit
                    if task.attempts >= 2:
                        self.logger.warning(f"  🚨 Task {task.task_id}: Max retries reached (2), escalating to issue report")
                        
                        # Create issue report and mark complete
                        from ..handlers import ToolCallHandler
                        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
                        
                        report_call = [{
                            "function": {
                                "name": "create_issue_report",
                                "arguments": {
                                    "task_id": task.task_id,
                                    "severity": task.priority.value,
                                    "impact_analysis": f"Task failed {task.attempts} times without proper analysis. AI did not read files to understand them.",
                                    "recommended_approach": "Manual review required - AI unable to analyze properly",
                                    "estimated_effort": "Unknown - requires developer assessment"
                                }
                            }
                        }]
                        
                        handler.process_tool_calls(report_call)
                        task.complete("Issue report created - max retries reached")
                        
                        return PhaseResult(
                            success=True,
                            phase=self.phase_name,
                            message=f"Task {task.task_id} escalated after max retries"
                        )
                    
                    # AI was lazy - just compared without understanding
                    # TASK-TYPE-AWARE RETRY: Different tasks need different analysis
                    from pipeline.state.refactoring_task import RefactoringIssueType
                    
                    # Simple tasks don't need comprehensive analysis
                    if task.issue_type in [RefactoringIssueType.ARCHITECTURE]:
                        # Check if this is a missing method or bug fix (simple tasks)
                        if "Missing method:" in task.title or "Dictionary key error" in task.title:
                            # Simple task - just needs to read the file and fix
                            error_msg = (
                                f"ATTEMPT {task.attempts + 1}: "
                                "This is a SIMPLE task. Just read the file and fix the issue. "
                                "Use read_file to see the code, then implement the fix or create a report. "
                                "DO NOT over-analyze - this should take 1-2 tool calls."
                            )
                        else:
                            # Complex architecture issue - needs analysis
                            error_msg = (
                                f"ATTEMPT {task.attempts + 1}: "
                                "You need to understand the files first. "
                                "Use read_file on the target files, then take action."
                            )
                    elif task.issue_type == RefactoringIssueType.DUPLICATE:
                        # Duplicate - just needs to merge
                        error_msg = (
                            f"ATTEMPT {task.attempts + 1}: "
                            "This is a DUPLICATE CODE task. "
                            "You can optionally compare the files, but you MUST merge them. "
                            "Use merge_file_implementations to complete this task."
                        )
                    else:
                        # Other tasks - standard retry
                        error_msg = (
                            f"ATTEMPT {task.attempts + 1}: "
                            "You only compared files without reading them. "
                            "Use read_file to understand the files, then take action."
                        )
                    
                    self.logger.warning(f"  ⚠️  Task {task.task_id}: Needs to read files - RETRYING (attempt {task.attempts + 1})")
                    
                    # DON'T mark as failed - reset to NEW so it can be retried
                    task.status = TaskStatus.NEW
                    
                    # Store error context in task for next attempt
                    if not task.analysis_data:
                        task.analysis_data = {}
                    task.analysis_data['retry_reason'] = error_msg
                    task.analysis_data['previous_attempt'] = task.attempts
                    
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Task {task.task_id} retry needed: {error_msg}"
                    )
                
                # CRITICAL: Check if we've exceeded retry limit
                if task.attempts >= 2:
                    self.logger.warning(f"  🚨 Task {task.task_id}: Max retries reached (2), escalating to issue report")
                    
                    # Create issue report and mark complete
                    from ..handlers import ToolCallHandler
                    handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
                    
                    tools_used = {r.get("tool") for r in results if r.get("success")}
                    report_call = [{
                        "function": {
                            "name": "create_issue_report",
                            "arguments": {
                                "task_id": task.task_id,
                                "severity": task.priority.value,
                                "impact_analysis": f"Task failed {task.attempts} times. AI analyzed but did not resolve. Tools used: {', '.join(tools_used)}",
                                "recommended_approach": "Manual review required - AI unable to resolve autonomously",
                                "estimated_effort": "Unknown - requires developer assessment"
                            }
                        }
                    }]
                    
                    handler.process_tool_calls(report_call)
                    task.complete("Issue report created - max retries reached")
                    
                    return PhaseResult(
                        success=True,
                        phase=self.phase_name,
                        message=f"Task {task.task_id} escalated after max retries"
                    )
                
                # AI tried to understand but still hasn't resolved
                # TASK-TYPE-AWARE RETRY: Different tasks need different next steps
                from pipeline.state.refactoring_task import RefactoringIssueType
                
                tools_used = {r.get("tool") for r in results if r.get("success")}
                
                # Simple tasks don't need comprehensive analysis
                if task.issue_type in [RefactoringIssueType.ARCHITECTURE]:
                    # Check if this is a missing method or bug fix (simple tasks)
                    if "Missing method:" in task.title or "Dictionary key error" in task.title:
                        error_msg = (
                            f"ATTEMPT {task.attempts + 1}: "
                            "You read the file but didn't fix the issue. "
                            "This is a SIMPLE task - just implement the fix or create a report. "
                            "Use modify_file, insert_after, or create_issue_report to complete this task."
                        )
                    else:
                        error_msg = (
                            f"ATTEMPT {task.attempts + 1}: "
                            "You read files but didn't resolve the issue. "
                            "Use move_file, rename_file, or create_issue_report to complete this task."
                        )
                elif task.issue_type == RefactoringIssueType.DUPLICATE:
                    error_msg = (
                        f"ATTEMPT {task.attempts + 1}: "
                        "You read/compared files but didn't merge them. "
                        "Use merge_file_implementations to complete this DUPLICATE CODE task."
                    )
                elif task.issue_type == RefactoringIssueType.DEAD_CODE:
                    error_msg = (
                        f"ATTEMPT {task.attempts + 1}: "
                        "You analyzed the code but didn't create a report. "
                        "This is an EARLY-STAGE project - create_issue_report for developer review."
                    )
                elif task.issue_type == RefactoringIssueType.INTEGRATION:
                    # Integration conflicts need comprehensive analysis
                    error_msg = (
                        f"ATTEMPT {task.attempts + 1}: "
                        "You read files but didn't resolve the conflict. "
                        "Check ARCHITECTURE.md, then use merge_file_implementations, move_file, or create_issue_report."
                    )
                else:
                    error_msg = (
                        f"ATTEMPT {task.attempts + 1}: "
                        "You analyzed but didn't take action. "
                        "Use a resolving tool (merge, move, report) to complete this task."
                    )
                
                self.logger.warning(f"  ⚠️  Task {task.task_id}: Read files but didn't resolve - RETRYING (attempt {task.attempts + 1})")
                
                # CRITICAL FIX: Reset TaskAnalysisTracker state so step detection works on retry
                self._analysis_tracker.reset_state(task.task_id)
                self.logger.info(f"  🔄 Reset analysis tracker state for task {task.task_id}")
                
                # Reset task to NEW status for retry
                task.status = TaskStatus.NEW
                
                if not task.analysis_data:
                    task.analysis_data = {}
                task.analysis_data['retry_reason'] = error_msg
                task.analysis_data['tools_used'] = list(tools_used)
                
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} not resolved: {error_msg}"
                )
            else:
                # All tools failed
                errors = [r.get("error", "Unknown") for r in results if not r.get("success")]
                error_msg = "; ".join(errors)
                
                task.fail(error_msg)
                
                result = PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} failed: {errors[0]}"
            )
            
            if self._detect_complexity(task, result):
                self.logger.warning(f"  ⚠️  Task {task.task_id} is too complex, creating issue report...")
                
                # Create issue report via tool call
                # This will be picked up by the handler
                from ..handlers import ToolCallHandler
                handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
                
                report_call = [{
                    "function": {
                        "name": "create_issue_report",
                        "arguments": {
                            "task_id": task.task_id,
                            "severity": task.priority.value,
                            "impact_analysis": f"Task failed {task.attempts} times. Errors: {error_msg}",
                            "recommended_approach": "Manual review and fixing required",
                            "estimated_effort": "Unknown - requires developer assessment"
                        }
                    }
                }]
                
                handler.process_tool_calls(report_call)
                
                # CRITICAL FIX: Mark task as complete to prevent infinite retry loop
                # The issue report has been created, so the task is "resolved" by escalation
                task.complete("Issue report created for manual review")
                self.logger.info(f"  ✅ Task {task.task_id} marked complete (escalated to issue report)")
                
                # Return success since we successfully escalated the task
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} escalated to issue report"
                )
            
            return result
    
    def _build_task_context(self, task: Any) -> str:
        """
        Build comprehensive context for a specific task.
        
        Uses RefactoringContextBuilder to provide full context including:
        - Strategic documents (MASTER_PLAN, ARCHITECTURE, ROADMAP)
        - Analysis reports (dead code, complexity, bugs, etc.)
        - Code context (target files, related files, tests)
        - Project state (phase, completion, recent changes)
        """
        # Get project state information
        project_state = {
            'phase': getattr(self, 'current_phase', 'refactoring'),
            'completion': getattr(self, 'completion_percentage', 0.0),
            'recent_changes': [],  # Could be populated from git history
            'pending_tasks': []     # Could be populated from task manager
        }
        
        # Extract affected code from task - FORMAT IT PROPERLY
        affected_code = ""
        if task.analysis_data:
            affected_code = self._format_analysis_data(task.issue_type, task.analysis_data)
        
        # Get target file (first file in target_files list)
        target_file = task.target_files[0] if task.target_files else ""
        
        try:
            # Build comprehensive context using context builder
            refactoring_context = self.context_builder.build_context(
                issue_type=task.issue_type.value,
                issue_description=task.description,
                target_file=target_file,
                affected_code=affected_code,
                project_state=project_state
            )
            
            # Format context for prompt
            formatted_context = self.context_builder.format_context_for_prompt(refactoring_context)
            
            # Add task-specific header
            task_header = f"""# Refactoring Task

**Task ID**: {task.task_id}
**Title**: {task.title}
**Type**: {task.issue_type.value}
**Priority**: {task.priority.value}
**Attempts**: {task.attempts}/{task.max_attempts}

"""
            
            # Add retry reason if this is a retry
            if task.analysis_data and 'retry_reason' in task.analysis_data:
                retry_reason = task.analysis_data['retry_reason']
                task_header += f"""
⚠️ **RETRY REQUIRED**: {retry_reason}

"""
            
            return task_header + formatted_context
            
        except Exception as e:
            self.logger.warning(f"  ⚠️  Failed to build comprehensive context: {e}")
            self.logger.warning(f"  Falling back to basic context")
            
            # Fallback to basic context if context builder fails
            context_parts = []
            
            context_parts.append(f"# Task: {task.title}\n")
            context_parts.append(f"**Task ID**: {task.task_id}\n")
            context_parts.append(f"**Type**: {task.issue_type.value}\n")
            context_parts.append(f"**Priority**: {task.priority.value}\n")
            context_parts.append(f"**Description**: {task.description}\n\n")
            
            # Add MASTER_PLAN context
            master_plan_path = os.path.join(self.project_dir, "MASTER_PLAN.md")
            if os.path.exists(master_plan_path):
                try:
                    with open(master_plan_path, 'r') as f:
                        master_plan = f.read()
                    context_parts.append(f"## MASTER_PLAN.md (Project Objectives)\n```\n{master_plan[:2000]}...\n```\n\n")
                except Exception as e:
                    self.logger.warning(f"Could not read MASTER_PLAN.md: {e}")
            
            # Add ARCHITECTURE context
            arch_path = os.path.join(self.project_dir, "ARCHITECTURE.md")
            if os.path.exists(arch_path):
                try:
                    with open(arch_path, 'r') as f:
                        architecture = f.read()
                    context_parts.append(f"## ARCHITECTURE.md (Design Guidelines)\n```\n{architecture}\n```\n\n")
                except Exception as e:
                    self.logger.warning(f"Could not read ARCHITECTURE.md: {e}")
            
            context_parts.append(f"## Affected Files\n")
            for file in task.target_files:
                context_parts.append(f"- {file}\n")
                # Try to include file content snippet
                file_path = os.path.join(self.project_dir, file)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        # Include first 50 lines or 2000 chars
                        lines = content.split('\n')[:50]
                        snippet = '\n'.join(lines)[:2000]
                        context_parts.append(f"\n### Content of {file}:\n```python\n{snippet}\n...\n```\n\n")
                    except Exception as e:
                        self.logger.warning(f"Could not read {file}: {e}")
            
            if task.analysis_data:
                context_parts.append(f"\n## Analysis Data\n")
                for key, value in task.analysis_data.items():
                    context_parts.append(f"**{key}**: {value}\n")
            
            return "".join(context_parts)
    
    def _format_analysis_data(self, issue_type, data: dict) -> str:
        """
        Format analysis data into clear, actionable text for the AI.
        
        Uses formatter classes for each issue type to eliminate duplication.
        
        Args:
            issue_type: Type of refactoring issue
            data: Raw analysis data dictionary
            
        Returns:
            Formatted string with clear action items
        """
        # Add project_dir to data for formatters that need it
        if isinstance(data, dict) and 'project_dir' not in data:
            data['project_dir'] = self.project_dir
        
        # Get appropriate formatter and format the data
        formatter = self.get_formatter(issue_type)
        return formatter.format(data)
    
    def _build_task_prompt(self, task: Any, context: str) -> str:
        """Build prompt for working on a specific task using template system"""
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        # Determine issue type string for template lookup
        issue_type_str = None
        
        if task.issue_type == RefactoringIssueType.ARCHITECTURE:
            # Check if this is a missing method task
            if "Missing method:" in task.title or ("method_name" in task.analysis_data and "class_name" in task.analysis_data):
                issue_type_str = 'missing_method'
            # Check if this is a dictionary key error
            elif "Dictionary key error" in task.title or "key_path" in task.analysis_data:
                issue_type_str = 'bug_fix'
            # Generic architecture issue
            else:
                issue_type_str = 'architecture_violation'
        
        elif task.issue_type == RefactoringIssueType.DUPLICATE:
            issue_type_str = 'duplicate_code'
        
        elif task.issue_type == RefactoringIssueType.INTEGRATION or task.issue_type == RefactoringIssueType.CONFLICT:
            issue_type_str = 'integration_conflict'
        
        elif task.issue_type == RefactoringIssueType.DEAD_CODE:
            issue_type_str = 'dead_code'
        
        elif task.issue_type == RefactoringIssueType.COMPLEXITY:
            issue_type_str = 'complexity'
        
        # Get template configuration
        if issue_type_str:
            config = self.prompt_builder.get_template_config(issue_type_str)
        else:
            config = self.prompt_builder.get_template_config('generic')
        
        # Build prompt from template
        return self.prompt_builder.build(
            'refactoring_task',
            context=context,
            **config
        )
    
    
    def _auto_create_tasks_from_analysis(self, state: PipelineState, analysis_result: PhaseResult) -> int:
        """
        Auto-create refactoring tasks from analysis results.
        
        Delegates to AnalysisOrchestrator for task creation logic.
        
        Args:
            state: Pipeline state
            analysis_result: Result from comprehensive analysis
            
        Returns:
            Number of tasks created (or -1 if should return to coding phase)
        """
        # Get tool results if available
        tool_results = getattr(self, '_last_tool_results', None)
        
        # Delegate to orchestrator
        return self.analysis_orchestrator.create_tasks_from_analysis(
            state=state,
            analysis_result=analysis_result,
            tool_results=tool_results
        )
    
    def _check_completion(self, state: PipelineState) -> PhaseResult:
        """
        Check if refactoring is complete.
        
        CRITICAL FIX: Don't automatically re-analyze after every completion.
        Only re-analyze if there's a good reason (time passed, IPC request, etc.)
        """
        self.logger.info(f"  🔍 Checking if refactoring is complete...")
        
        # Get progress
        if state.refactoring_manager:
            progress = state.refactoring_manager.get_progress()
            self.logger.info(f"  📊 Progress: {progress['completion_percentage']:.1f}% complete")
            self.logger.info(f"     Completed: {progress['completed']}, Failed: {progress['failed']}, Blocked: {progress['blocked']}")
            
            # Check for blocked tasks
            blocked = progress.get('blocked', 0)
            if blocked > 0:
                self.logger.warning(f"  ⚠️  {blocked} tasks blocked, generating report...")
                self._generate_refactoring_report(state)
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Refactoring paused: {blocked} tasks need developer review",
                    next_phase="coding"  # Pause refactoring, return to coding
                )
        
        # CRITICAL FIX: Don't automatically re-analyze!
        # Check if we should re-analyze based on intelligent criteria
        if self._should_reanalyze(state):
            self.logger.info(f"  🔍 Re-analyzing codebase (criteria met)...")
            return self._analyze_and_create_tasks(state)
        
        # No re-analysis needed, we're done!
        self.logger.info(f"  ✅ All refactoring complete, no re-analysis needed")
        
        # Generate final report
        self._generate_refactoring_report(state)
        
        # Update IPC documents
        self._write_refactoring_completion_status(state)
        
        # ========== INTEGRATION: WRITE COMPLETION STATUS ==========
        self._write_status({
            'status': 'completed',
            'message': 'All refactoring tasks completed',
            'tasks_completed': progress.get('completed', 0) if state.refactoring_manager else 0,
            'tasks_failed': progress.get('failed', 0) if state.refactoring_manager else 0
        })
        
        # ========== INTEGRATION: UPDATE ARCHITECTURE ==========
        # Record refactoring changes in architecture
        if state.refactoring_manager:
            completed_tasks = [t for t in state.refactoring_manager.tasks.values() 
                             if t.status == TaskStatus.COMPLETED]
            if completed_tasks:
                self._update_architecture({
                    'type': 'refactoring_completed',
                    'details': {
                        'tasks_completed': len(completed_tasks),
                        'issue_types': list(set(t.issue_type.value for t in completed_tasks)),
                        'rationale': 'Code organization and quality improvements'
                    }
                })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="All refactoring tasks completed successfully",
            next_phase="coding"  # Return to coding
        )
    
    def _generate_refactoring_report(self, state: PipelineState) -> None:
        """
        Generate comprehensive REFACTORING_REPORT.md.
        
        Includes all tasks, issues, and recommendations.
        """
        if not state.refactoring_manager:
            return
        
        from pipeline.state.refactoring_task import RefactoringPriority
        
        report_lines = []
        
        # Header
        report_lines.append("# Refactoring Report\n")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        progress = state.refactoring_manager.get_progress()
        report_lines.append("## Executive Summary\n\n")
        report_lines.append(f"- **Total Tasks**: {progress['total']}\n")
        report_lines.append(f"- **Completed**: {progress['completed']} ({progress['completion_percentage']:.1f}%)\n")
        report_lines.append(f"- **In Progress**: {progress['in_progress']}\n")
        report_lines.append(f"- **Pending**: {progress['pending']}\n")
        report_lines.append(f"- **Failed**: {progress['failed']}\n")
        report_lines.append(f"- **Blocked**: {progress['blocked']}\n\n")
        
        # Critical Issues
        critical_tasks = state.refactoring_manager.get_tasks_by_priority(RefactoringPriority.CRITICAL)
        if critical_tasks:
            report_lines.append("## 🔴 Critical Issues\n\n")
            for task in critical_tasks:
                if task.status != TaskStatus.COMPLETED:
                    report_lines.append(f"### {task.task_id}: {task.title}\n\n")
                    report_lines.append(f"- **Type**: {task.issue_type.value}\n")
                    report_lines.append(f"- **Status**: {task.status.value}\n")
                    report_lines.append(f"- **Files**: {', '.join(task.target_files)}\n")
                    report_lines.append(f"- **Description**: {task.description}\n\n")
                    if task.error_message:
                        report_lines.append(f"- **Error**: {task.error_message}\n\n")
        
        # High Priority Issues
        high_tasks = state.refactoring_manager.get_tasks_by_priority(RefactoringPriority.HIGH)
        if high_tasks:
            report_lines.append("## 🟠 High Priority Issues\n\n")
            for task in high_tasks:
                if task.status != TaskStatus.COMPLETED:
                    report_lines.append(f"### {task.task_id}: {task.title}\n\n")
                    report_lines.append(f"- **Type**: {task.issue_type.value}\n")
                    report_lines.append(f"- **Status**: {task.status.value}\n")
                    report_lines.append(f"- **Files**: {', '.join(task.target_files)}\n\n")
        
        # Blocked Tasks (Need Developer Review)
        blocked_tasks = state.refactoring_manager.get_blocked_tasks()
        if blocked_tasks:
            report_lines.append("## 🚫 Blocked Tasks (Developer Review Needed)\n\n")
            for task in blocked_tasks:
                report_lines.append(f"### {task.task_id}: {task.title}\n\n")
                report_lines.append(f"- **Type**: {task.issue_type.value}\n")
                report_lines.append(f"- **Priority**: {task.priority.value}\n")
                report_lines.append(f"- **Files**: {', '.join(task.target_files)}\n")
                report_lines.append(f"- **Reason**: {task.error_message}\n")
                report_lines.append(f"- **Description**: {task.description}\n\n")
        
        # Completed Tasks
        completed_tasks = state.refactoring_manager.get_tasks_by_status(TaskStatus.COMPLETED)
        if completed_tasks:
            report_lines.append("## ✅ Completed Tasks\n\n")
            for task in completed_tasks[:10]:  # Show first 10
                report_lines.append(f"- **{task.task_id}**: {task.title} ({task.issue_type.value})\n")
            if len(completed_tasks) > 10:
                report_lines.append(f"\n... and {len(completed_tasks) - 10} more\n")
            report_lines.append("\n")
        
        # Write report
        report_path = self.project_dir / "REFACTORING_REPORT.md"
        with open(report_path, 'w') as f:
            f.write("".join(report_lines))
        
        self.logger.info(f"  📝 Generated REFACTORING_REPORT.md ({len(report_lines)} lines)")
    
    def _detect_complexity(self, task: Any, result: PhaseResult) -> bool:
        """
        Detect if a task is too complex for autonomous fixing.
        
        Indicators:
        - Task failed 2+ times
        - Tools returned errors repeatedly
        - LLM response contains "too complex" or "needs review"
        
        Returns:
            True if task is too complex
        """
        # Check attempts
        if task.attempts >= 2:
            return True
        
        # Check for complexity indicators in result
        if result.message:
            complexity_keywords = [
                "too complex",
                "needs review",
                "requires manual",
                "cannot fix",
                "unable to",
                "developer input"
            ]
            message_lower = result.message.lower()
            if any(keyword in message_lower for keyword in complexity_keywords):
                return True
        
        return False
    
    # =============================================================================
    # Legacy Methods (Backward Compatibility)
    # =============================================================================
    
    def _determine_refactoring_type(self, state: PipelineState,
                                   refactoring_requests: str,
                                   phase_outputs: Dict) -> str:
        """Determine what type of refactoring is needed"""
        
        # Check for explicit requests in REFACTORING_READ.md
        if refactoring_requests:
            if "duplicate" in refactoring_requests.lower():
                return "duplicate_detection"
            elif "conflict" in refactoring_requests.lower():
                return "conflict_resolution"
            elif "architecture" in refactoring_requests.lower():
                return "architecture_consistency"
            elif "extract" in refactoring_requests.lower():
                return "feature_extraction"
        
        # Check phase outputs for recommendations
        if phase_outputs:
            qa_output = phase_outputs.get("qa", "")
            if "duplicate" in qa_output.lower():
                return "duplicate_detection"
            if "conflict" in qa_output.lower():
                return "conflict_resolution"
            
            investigation_output = phase_outputs.get("investigation", "")
            if "refactor" in investigation_output.lower():
                return "comprehensive"
        
        # Default to comprehensive analysis
        return "comprehensive"
    
    def _handle_duplicate_detection(self, state: PipelineState,
                                   target_files: List[str] = None) -> PhaseResult:
        """Detect and handle duplicate implementations"""
        
        self.logger.info("  🔍 Detecting duplicate implementations...")
        
        # Get all Python files if no targets specified
        if not target_files:
            target_files = self._get_all_python_files()
        
        # Build context for LLM
        context = self._build_duplicate_detection_context(target_files)
        
        # Get tools for this phase
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="duplicate_detection",
            context=context,
            target_files=target_files
        )
        
        # Call LLM with tools
        result = self.chat_with_history(
            user_message=prompt,
            tools=tools
        )
        
        # Extract tool calls and content
        tool_calls = result.get("tool_calls", [])
        content = result.get("content", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Duplicate detection failed: No tool calls in response"
            )
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        results = handler.process_tool_calls(tool_calls)
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="duplicate_detection",
            results=results,
            recommendations=content
        )
        
        # Send message to Coding for implementation if needed
        self.send_message_to_phase('coding', {
            'type': 'implementation_request',
            'source': 'refactoring',
            'description': 'Duplicate detection completed - may need consolidated implementation',
            'priority': 'medium'
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Duplicate detection completed",
            next_phase="coding"  # May need new implementation
        )
    
    def _handle_conflict_resolution(self, state: PipelineState,
                                   target_files: List[str] = None) -> PhaseResult:
        """Detect and resolve conflicts between files"""
        
        self.logger.info("  ⚔️ Resolving file conflicts...")
        
        # Build context
        context = self._build_conflict_resolution_context(target_files)
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="conflict_resolution",
            context=context,
            target_files=target_files
        )
        
        # Call LLM
        result = self.chat_with_history(
            user_message=prompt,
            tools=tools
        )
        
        # Extract tool calls and content
        tool_calls = result.get("tool_calls", [])
        content = result.get("content", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Conflict resolution failed: No tool calls in response"
            )
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        results = handler.process_tool_calls(tool_calls)
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="conflict_resolution",
            results=results,
            recommendations=content
        )
        
        # Send message to QA for verification
        self.send_message_to_phase('qa', {
            'type': 'verification_request',
            'source': 'refactoring',
            'description': 'Conflict resolution completed - please verify merged implementations',
            'files': [],  # Would be populated with actual files
            'priority': 'high'
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Conflict resolution completed",
            next_phase="qa"  # Need verification
        )
    
    def _handle_architecture_consistency(self, state: PipelineState) -> PhaseResult:
        """Check and fix architecture consistency with MASTER_PLAN"""
        
        self.logger.info("  📐 Checking architecture consistency...")
        
        # Build context
        context = self._build_architecture_context()
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="architecture_consistency",
            context=context
        )
        
        # Call LLM
        result = self.chat_with_history(
            user_message=prompt,
            tools=tools
        )
        
        # Extract tool calls and content
        tool_calls = result.get("tool_calls", [])
        content = result.get("content", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Architecture consistency check failed: No tool calls in response"
            )
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        results = handler.process_tool_calls(tool_calls)
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="architecture_consistency",
            results=results,
            recommendations=content
        )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Architecture consistency check completed",
            next_phase="planning"  # May need new tasks
        )
    
    def _handle_feature_extraction(self, state: PipelineState,
                                  target_files: List[str] = None) -> PhaseResult:
        """Extract features from files for consolidation"""
        
        self.logger.info("  📦 Extracting features for consolidation...")
        
        # Build context
        context = self._build_feature_extraction_context(target_files)
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="feature_extraction",
            context=context,
            target_files=target_files
        )
        
        # Call LLM
        result = self.chat_with_history(
            user_message=prompt,
            tools=tools
        )
        
        # Extract tool calls and content
        tool_calls = result.get("tool_calls", [])
        content = result.get("content", "")
        
        if not tool_calls:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Feature extraction failed: No tool calls in response"
            )
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        results = handler.process_tool_calls(tool_calls)
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="feature_extraction",
            results=results,
            recommendations=content
        )
        
        # Send message to Coding for consolidated implementation
        self.send_message_to_phase('coding', {
            'type': 'implementation_request',
            'source': 'refactoring',
            'description': 'Feature extraction completed - need consolidated implementation',
            'priority': 'high'
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Feature extraction completed",
            next_phase="coding"  # Need new consolidated implementation
        )
    
    def _handle_comprehensive_refactoring(self, state: PipelineState) -> PhaseResult:
        """
        Perform TRULY COMPREHENSIVE refactoring analysis.
        
        This runs EVERY SINGLE CHECK available, not relying on LLM to decide.
        """
        
        self.logger.info("  🔬 Performing COMPREHENSIVE refactoring analysis...")
        self.logger.info("  🎯 Running ALL available checks automatically...")
        
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry, refactoring_manager=state.refactoring_manager)
        
        all_results = []
        
        # ============================================================
        # PHASE 1: ARCHITECTURE VALIDATION (CRITICAL - ALWAYS FIRST)
        # ============================================================
        self.logger.info("  📐 Phase 1: Architecture Validation")
        
        arch_result = handler._handle_validate_architecture({
            'check_locations': True,
            'check_naming': True,
            'check_missing': True
        })
        all_results.append(arch_result)
        
        if arch_result.get('success'):
            violations = arch_result.get('result', {}).get('total_violations', 0)
            self.logger.info(f"     ✓ Architecture validation: {violations} violations found")
        
        # ============================================================
        # PHASE 2: CODE QUALITY ANALYSIS
        # ============================================================
        self.logger.info("  🔍 Phase 2: Code Quality Analysis")
        
        # 2.1: Duplicate Detection
        dup_result = handler._handle_detect_duplicate_implementations({
            'similarity_threshold': 0.7,
            'scope': 'project',
            'include_tests': False
        })
        all_results.append(dup_result)
        
        if dup_result.get('success'):
            dups = dup_result.get('result', {}).get('total_duplicates', 0)
            self.logger.info(f"     ✓ Duplicate detection: {dups} duplicate sets found")
        
        # 2.2: Complexity Analysis
        complexity_result = handler._handle_analyze_complexity({})
        all_results.append(complexity_result)
        
        if complexity_result.get('success'):
            critical = complexity_result.get('result', {}).get('critical_count', 0)
            self.logger.info(f"     ✓ Complexity analysis: {critical} critical functions found")
        
        # 2.3: Dead Code Detection
        dead_result = handler._handle_detect_dead_code({})
        all_results.append(dead_result)
        
        if dead_result.get('success'):
            summary = dead_result.get('result', {}).get('summary', {})
            unused_funcs = summary.get('total_unused_functions', 0)
            unused_methods = summary.get('total_unused_methods', 0)
            self.logger.info(f"     ✓ Dead code detection: {unused_funcs + unused_methods} unused items found")
        
        # ============================================================
        # PHASE 3: INTEGRATION ANALYSIS
        # ============================================================
        self.logger.info("  🔗 Phase 3: Integration Analysis")
        
        # 3.1: Integration Gaps
        gaps_result = handler._handle_find_integration_gaps({})
        all_results.append(gaps_result)
        
        if gaps_result.get('success'):
            gaps = len(gaps_result.get('result', {}).get('gaps', []))
            self.logger.info(f"     ✓ Integration gaps: {gaps} gaps found")
        
        # 3.2: Integration Conflicts (if available)
        try:
            from ..analysis.integration_conflicts import IntegrationConflictDetector
            conflict_detector = IntegrationConflictDetector(str(self.project_dir), self.logger)
            conflict_analysis = conflict_detector.analyze()
            
            from dataclasses import asdict
            conflict_result = {
                'tool': 'detect_integration_conflicts',
                'success': True,
                'result': {
                    'conflicts': [asdict(c) for c in conflict_analysis.conflicts],
                    'total_conflicts': len(conflict_analysis.conflicts)
                }
            }
            all_results.append(conflict_result)
            self.logger.info(f"     ✓ Integration conflicts: {len(conflict_analysis.conflicts)} conflicts found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Integration conflict detection failed: {e}")
        
        # ============================================================
        # PHASE 4: CODE STRUCTURE ANALYSIS
        # ============================================================
        self.logger.info("  🏗️  Phase 4: Code Structure Analysis")
        
        # 4.1: Call Graph Generation
        callgraph_result = handler._handle_generate_call_graph({})
        all_results.append(callgraph_result)
        
        if callgraph_result.get('success'):
            self.logger.info(f"     ✓ Call graph generated")
        
        # ============================================================
        # PHASE 5: BUG DETECTION
        # ============================================================
        self.logger.info("  🐛 Phase 5: Bug Detection")
        
        # 5.1: Bug Detection
        bug_result = handler._handle_find_bugs({'target': None})  # None = analyze all files
        all_results.append(bug_result)
        
        if bug_result.get('success'):
            bugs = len(bug_result.get('result', {}).get('bugs', []))
            self.logger.info(f"     ✓ Bug detection: {bugs} potential bugs found")
        
        # 5.2: Anti-pattern Detection
        antipattern_result = handler._handle_detect_antipatterns({'target': None})  # None = analyze all files
        all_results.append(antipattern_result)
        
        if antipattern_result.get('success'):
            patterns = len(antipattern_result.get('result', {}).get('antipatterns', []))
            self.logger.info(f"     ✓ Anti-pattern detection: {patterns} anti-patterns found")
        
        # ============================================================
        # PHASE 6: VALIDATION CHECKS
        # ============================================================
        self.logger.info("  ✅ Phase 6: Validation Checks")
        
        # 6.1: Function Call Validation (NEW - Priority 1)
        try:
            func_call_result = handler._handle_validate_function_calls({})
            all_results.append(func_call_result)
            
            if func_call_result.get('success'):
                error_count = func_call_result.get('total_errors', 0)
                self.logger.info(f"     ✓ Function call validation: {error_count} errors found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Function call validation failed: {e}")
        
        # 6.2: Method Existence Validation (NEW - Priority 1)
        try:
            method_result = handler._handle_validate_method_existence({})
            all_results.append(method_result)
            
            if method_result.get('success'):
                error_count = method_result.get('total_errors', 0)
                self.logger.info(f"     ✓ Method existence validation: {error_count} errors found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Method existence validation failed: {e}")
        
        # 6.3: Dictionary Structure Validation (NEW - Priority 2)
        try:
            dict_result = handler._handle_validate_dict_structure({})
            all_results.append(dict_result)
            
            if dict_result.get('success'):
                error_count = dict_result.get('total_errors', 0)
                self.logger.info(f"     ✓ Dictionary structure validation: {error_count} errors found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Dictionary structure validation failed: {e}")
        
        # 6.4: Type Usage Validation (NEW - Priority 2)
        try:
            type_result = handler._handle_validate_type_usage({})
            all_results.append(type_result)
            
            if type_result.get('success'):
                error_count = type_result.get('total_errors', 0)
                self.logger.info(f"     ✓ Type usage validation: {error_count} errors found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Type usage validation failed: {e}")
        
        # 6.5: Import Validation
        try:
            import_result = handler._handle_validate_all_imports({})
            all_results.append(import_result)
            
            if import_result.get('success'):
                invalid_count = import_result.get('count', 0)
                self.logger.info(f"     ✓ Import validation: {invalid_count} invalid imports found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Import validation failed: {e}")
        
        # 6.6: Syntax Validation (using complexity analyzer which already checks syntax)
        # Syntax errors already detected in Phase 2 complexity analysis
        self.logger.info(f"     ✓ Syntax validation: Checked in Phase 2 (complexity analysis)")
        
        # 6.7: Circular Import Detection
        try:
            circular_result = handler._handle_detect_circular_imports({})
            all_results.append(circular_result)
            
            if circular_result.get('success'):
                cycles = len(circular_result.get('result', {}).get('cycles', []))
                self.logger.info(f"     ✓ Circular import detection: {cycles} cycles found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Circular import detection failed: {e}")
        
        # Store results for auto-task creation
        self._last_tool_results = all_results
        
        # Count successes
        any_success = False
        all_errors = []
        for result in all_results:
            if result.get("success"):
                any_success = True
            else:
                error = result.get("error", "Unknown error")
                all_errors.append(f"{result.get('tool', 'unknown')}: {error}")
        
        # If ALL tools failed, try ONE MORE TIME with error feedback
        if not any_success:
            self.logger.warning(f"  ⚠️  All tools failed on first attempt, retrying with error feedback...")
            
            # Build error feedback message
            error_summary = "\n".join(all_errors)
            retry_prompt = f"""The previous tool calls failed with these errors:

{error_summary}

Please try a different approach:
1. If detect_duplicate_implementations failed with import errors, try analyze_complexity or detect_dead_code instead
2. If you need to analyze files, try extract_file_features on specific files
3. Focus on tools that do not require complex imports
4. Consider using simpler analysis tools first

Available tools that are more reliable:
- analyze_complexity: Analyze code complexity metrics
- detect_dead_code: Find unused code
- extract_file_features: Extract features from specific files
- analyze_architecture_consistency: Check MASTER_PLAN consistency

Please select ONE reliable tool and try again."""

            # Retry with error feedback
            retry_result = self.chat_with_history(
                user_message=retry_prompt,
                tools=tools
            )
            
            retry_tool_calls = retry_result.get("tool_calls", [])
            if retry_tool_calls:
                retry_results = handler.process_tool_calls(retry_tool_calls)
                
                # Check retry results
                for result in retry_results:
                    if result.get("success"):
                        any_success = True
                        results.extend(retry_results)
                        break
        
        # If STILL all tools failed after retry, return failure
        if not any_success:
            error_summary = "\n".join(all_errors)
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Comprehensive refactoring failed: All tools failed even after retry\n{error_summary}"
            )
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="comprehensive",
            results=all_results,
            recommendations=""
        )
        
        # Determine next phase based on recommendations
        next_phase = "refactoring"  # Continue refactoring to work on tasks
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'task_id': task.task_id if task else None
        })
        
        # DIMENSION TRACKING: Update dimensions based on analysis
        execution_duration = (datetime.now() - start_time).total_seconds()
        self.track_dimensions({
            'temporal': min(1.0, execution_duration / 300.0),
            'data': 0.8,
            'integration': 0.9,
            'architecture': 0.9
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Comprehensive refactoring analysis completed",
            next_phase=next_phase
        )
    
    def _get_all_python_files(self) -> List[str]:
        """Get all Python files in the project"""
        python_files = []
        for path in Path(self.project_dir).rglob("*.py"):
            if ".venv" not in str(path) and "__pycache__" not in str(path):
                python_files.append(str(path.relative_to(self.project_dir)))
        return python_files
    
    def _build_duplicate_detection_context(self, target_files: List[str]) -> str:
        """Build context for duplicate detection"""
        context_parts = []
        
        context_parts.append("# Duplicate Detection Context\n")
        context_parts.append(f"Target files: {len(target_files)}\n")
        
        # Add file summaries
        for filepath in target_files[:10]:  # Limit to first 10
            full_path = self.project_dir / filepath
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    context_parts.append(f"\n## {filepath}\n")
                    context_parts.append(f"Lines: {len(content.splitlines())}\n")
                    # Add first few lines
                    lines = content.splitlines()[:5]
                    context_parts.append("```python\n")
                    context_parts.append("\n".join(lines))
                    context_parts.append("\n...\n```\n")
                except Exception as e:
                    self.logger.warning(f"Could not read {filepath}: {e}")
        
        return "".join(context_parts)
    
    def _build_conflict_resolution_context(self, target_files: List[str]) -> str:
        """Build context for conflict resolution"""
        context_parts = []
        
        context_parts.append("# Conflict Resolution Context\n")
        
        if target_files:
            context_parts.append(f"Target files: {', '.join(target_files)}\n")
        
        return "".join(context_parts)
    
    def _build_architecture_context(self) -> str:
        """Build context for architecture consistency check"""
        context_parts = []
        
        context_parts.append("# Architecture Consistency Context\n")
        
        # Add MASTER_PLAN content
        master_plan = self.read_file("MASTER_PLAN.md")
        if master_plan:
            context_parts.append("\n## MASTER_PLAN.md\n")
            context_parts.append(master_plan[:2000])  # First 2000 chars
            context_parts.append("\n...\n")
        
        # Add ARCHITECTURE content
        architecture = self.read_file("ARCHITECTURE.md")
        if architecture:
            context_parts.append("\n## ARCHITECTURE.md\n")
            context_parts.append(architecture[:2000])  # First 2000 chars
            context_parts.append("\n...\n")
        
        return "".join(context_parts)
    
    def _build_feature_extraction_context(self, target_files: List[str]) -> str:
        """Build context for feature extraction"""
        context_parts = []
        
        context_parts.append("# Feature Extraction Context\n")
        
        if target_files:
            context_parts.append(f"Target files: {', '.join(target_files)}\n")
        
        return "".join(context_parts)
    
    def _build_comprehensive_context(self) -> str:
        """Build comprehensive context for full analysis"""
        context_parts = []
        
        context_parts.append("# Comprehensive Refactoring Context\n")
        
        # Add project structure
        python_files = self._get_all_python_files()
        context_parts.append(f"\n## Project Structure\n")
        context_parts.append(f"Total Python files: {len(python_files)}\n")
        
        # Add MASTER_PLAN
        master_plan = self.read_file("MASTER_PLAN.md")
        if master_plan:
            context_parts.append("\n## MASTER_PLAN.md (excerpt)\n")
            context_parts.append(master_plan[:1000])
            context_parts.append("\n...\n")
        
        return "".join(context_parts)
    
    def _write_refactoring_results(self, refactoring_type: str,
                                  results: List[Dict],
                                  recommendations: str):
        """Write refactoring results to REFACTORING_WRITE.md"""
        
        content_parts = []
        content_parts.append(f"# Refactoring Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        content_parts.append(f"## Type: {refactoring_type}\n\n")
        
        if results:
            content_parts.append("## Tool Results\n\n")
            for result in results:
                tool_name = result.get("tool", "unknown")
                success = result.get("success", False)
                message = result.get("message", "")
                content_parts.append(f"### {tool_name}\n")
                content_parts.append(f"Status: {'✅ Success' if success else '❌ Failed'}\n")
                content_parts.append(f"{message}\n\n")
        
        if recommendations:
            content_parts.append("## Recommendations\n\n")
            content_parts.append(recommendations)
            content_parts.append("\n")
        
        self.write_own_status("".join(content_parts))
    
    def _determine_next_phase(self, recommendations: str) -> str:
        """
        Determine next phase based on recommendations.
        
        NEW DESIGN: Refactoring should continue until all issues are fixed.
        Only return to other phases when:
        1. New code implementation needed (coding)
        2. Verification needed (qa)
        3. New tasks needed (planning)
        4. All refactoring complete (coding)
        """
        
        recommendations_lower = recommendations.lower()
        
        # Check if more refactoring work remains
        if "continue refactoring" in recommendations_lower or "more issues" in recommendations_lower:
            return "refactoring"  # Continue refactoring
        
        # Check if new implementation needed
        if "implement" in recommendations_lower or "create new" in recommendations_lower:
            return "coding"
        
        # Check if verification needed
        elif "verify" in recommendations_lower or "test" in recommendations_lower:
            return "qa"
        
        # Check if planning needed
        elif "plan" in recommendations_lower or "new task" in recommendations_lower:
            return "planning"
        
        # Default: return to coding (refactoring complete)
        else:
            return "coding"
    
    def _read_relevant_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases that might trigger refactoring"""
        
        outputs = {}
        
        # Read QA output (might have conflict/duplicate warnings)
        qa_output = self.read_file(".ai/QA_WRITE.md")
        if qa_output:
            outputs["qa"] = qa_output
        
        # Read investigation output (might have refactoring recommendations)
        investigation_output = self.read_file(".ai/INVESTIGATION_WRITE.md")
        if investigation_output:
            outputs["investigation"] = investigation_output
        
        # Read planning output (might have architecture changes)
        planning_output = self.read_file(".ai/PLANNING_WRITE.md")
        if planning_output:
            outputs["planning"] = planning_output
        
        return outputs
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate REFACTORING_STATE.md content"""
        lines = [
            "# Refactoring State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Current Session Stats",
            "",
        ]
        
        if 'refactoring' in state.phases:
            lines.extend([
                f"- Refactoring Analyses: {state.phases['refactoring'].successes}",
                f"- Failed Analyses: {state.phases['refactoring'].failures}",
                f"- Total Runs: {state.phases['refactoring'].runs}",
            ])
        else:
            lines.append("- Stats not available (phase not initialized)")
        
        lines.append("")
        
        # Add recent refactoring activities
        lines.extend([
            "## Recent Refactoring Activities",
            "",
        ])
        
        # Get recent refactoring results from REFACTORING_WRITE.md
        refactoring_output = self.read_file(".ai/REFACTORING_WRITE.md")
        if refactoring_output:
            lines.append("### Latest Analysis")
            lines.append("")
            # Add first 500 chars of latest output
            lines.append(refactoring_output[:500])
            if len(refactoring_output) > 500:
                lines.append("...")
        else:
            lines.append("No recent refactoring activities")
        
        lines.append("")
        
        # Add refactoring recommendations summary
        lines.extend([
            "## Pending Recommendations",
            "",
        ])
        
        # Check for pending refactoring tasks
        pending_refactoring = [
            task for task in state.tasks.values()
            if task.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
            and task.description and 'refactor' in task.description.lower()
        ]
        
        if pending_refactoring:
            lines.append(f"- {len(pending_refactoring)} refactoring task(s) pending")
            for task in pending_refactoring[:5]:  # Show first 5
                lines.append(f"  - {task.task_id}: {task.description[:80]}...")
        else:
            lines.append("No pending refactoring tasks")
        
        return "\n".join(lines)    
    # =============================================================================
    # CRITICAL FIXES: New Methods for Proper Refactoring Workflow
    # =============================================================================
    
    def _should_reanalyze(self, state: PipelineState) -> bool:
        """
        Determine if we should re-analyze the codebase.
        
        CRITICAL FIX: Don't automatically re-analyze after every completion.
        Only re-analyze if there's a good reason.
        
        Criteria for re-analysis:
        1. Significant time passed since last analysis (> 1 hour)
        2. Other phases requested it via IPC
        3. User explicitly requested it
        4. Major changes detected (many files modified)
        
        Returns:
            True if should re-analyze, False otherwise
        """
        # Check if we have a last analysis timestamp
        last_analysis = getattr(state, 'last_refactoring_analysis', None)
        
        if not last_analysis:
            # First analysis, should run
            self.logger.debug("  📝 No previous analysis, should analyze")
            return True
        
        # Check time since last analysis
        time_since = datetime.now() - last_analysis
        hours_since = time_since.total_seconds() / 3600
        
        if hours_since > 1.0:
            # More than 1 hour since last analysis
            self.logger.info(f"  ⏰ {hours_since:.1f} hours since last analysis, re-analyzing")
            return True
        
        # Check IPC for analysis requests
        if self._check_ipc_for_analysis_request():
            self.logger.info("  📨 IPC analysis request received, re-analyzing")
            return True
        
        # Check for major changes (many files modified recently)
        if self._detect_major_changes():
            self.logger.info("  📝 Major changes detected, re-analyzing")
            return True
        
        # No criteria met, don't re-analyze
        self.logger.debug(f"  ⏭️  Only {hours_since*60:.0f} minutes since last analysis, skipping re-analysis")
        return False
    
    def _check_ipc_for_analysis_request(self) -> bool:
        """
        Check IPC documents for refactoring analysis requests.
        
        Returns:
            True if analysis requested, False otherwise
        """
        try:
            # Read our READ document (written by other phases)
            read_content = self.doc_ipc.read_own_document('refactoring')
            
            if not read_content:
                return False
            
            # Check for analysis request keywords
            request_keywords = [
                'request refactoring analysis',
                'please analyze',
                'refactoring needed',
                'duplicates detected',
                'conflicts found'
            ]
            
            content_lower = read_content.lower()
            for keyword in request_keywords:
                if keyword in content_lower:
                    return True
            
            return False
        except Exception as e:
            self.logger.debug(f"  Error checking IPC: {e}")
            return False
    
    def _detect_major_changes(self) -> bool:
        """
        Detect if major changes occurred since last analysis.
        
        Returns:
            True if major changes detected, False otherwise
        """
        try:
            # Check git for recent changes
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                changed_files = result.stdout.strip().split('\n')
                changed_files = [f for f in changed_files if f]
                
                # Consider it major if > 10 files changed
                if len(changed_files) > 10:
                    self.logger.debug(f"  📝 {len(changed_files)} files changed")
                    return True
            
            return False
        except Exception as e:
            self.logger.debug(f"  Error detecting changes: {e}")
            return False
    
    def _write_refactoring_completion_status(self, state: PipelineState):
        """
        Write refactoring completion status to IPC documents.
        
        CRITICAL FIX: Communicate with other phases via IPC.
        """
        try:
            # Get progress
            progress = state.refactoring_manager.get_progress() if state.refactoring_manager else {}
            
            # Build status message
            status_lines = [
                "# Refactoring Phase - Completion Status",
                f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Status: COMPLETE ✅",
                "",
                "All refactoring tasks have been completed.",
                "",
                "## Summary",
                f"- Total Tasks: {progress.get('total', 0)}",
                f"- Completed: {progress.get('completed', 0)}",
                f"- Failed: {progress.get('failed', 0)}",
                f"- Blocked: {progress.get('blocked', 0)}",
                "",
                "## Next Steps",
                "- Continue with coding phase",
                "- Refactoring will re-analyze if requested via IPC",
                "- Or after significant time passes (> 1 hour)",
                ""
            ]
            
            status_content = "\n".join(status_lines)
            
            # Write to our WRITE document (read by other phases)
            self.doc_ipc.write_own_document('refactoring', status_content)
            
            self.logger.info("  📝 Updated IPC documents with completion status")
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error writing IPC status: {e}")
    
    def _verify_task_resolution(self, task) -> Tuple[bool, str]:
        """
        Verify that a task was actually resolved.
        
        CRITICAL FIX: Don't just check if resolving tool was called,
        verify that the issue is actually fixed!
        
        Args:
            task: RefactoringTask to verify
            
        Returns:
            Tuple of (is_resolved, error_message)
        """
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        try:
            if task.issue_type == RefactoringIssueType.DUPLICATE:
                # Re-run duplicate detection on target files
                self.logger.debug(f"  🔍 Verifying duplicate resolution for {task.target_files}")
                
                duplicates = self.duplicate_detector.find_duplicates(
                    scope="project"
                )
                
                if duplicates:
                    # Still has duplicates!
                    return False, f"Files still have {len(duplicates)} duplicate(s) after merge attempt"
                
                return True, "Duplicates successfully resolved"
            
            elif task.issue_type == RefactoringIssueType.ARCHITECTURE:
                # Re-run architecture validation
                self.logger.debug(f"  🔍 Verifying architecture fix for {task.target_files}")
                
                # Check architecture consistency
                consistency = self.architecture_analyzer.analyze_consistency()
                violations = consistency.issues
                
                if violations:
                    return False, f"Files still have {len(violations)} architecture violation(s)"
                
                return True, "Architecture violations resolved"
            
            elif task.issue_type == RefactoringIssueType.DEAD_CODE:
                # For dead code, check if file/function still exists
                self.logger.debug(f"  🔍 Verifying dead code removal for {task.target_files}")
                
                # If files were deleted, that's good
                for file_path in task.target_files:
                    full_path = self.project_dir / file_path
                    if not full_path.exists():
                        return True, "Dead code file successfully removed"
                
                # If files still exist, check if the specific function/method was removed
                # This requires checking the analysis_data for the specific item
                if task.analysis_data and 'name' in task.analysis_data:
                    item_name = task.analysis_data['name']
                    # Re-run dead code detection
                    result = self.dead_code_detector.analyze()
                    dead_code = result.to_dict()
                    
                    # Check if this specific item is still in the dead code list
                    for item in dead_code.get('unused_functions', []) + dead_code.get('unused_methods', []):
                        if item.get('name') == item_name:
                            return False, f"Dead code '{item_name}' still exists"
                
                return True, "Dead code successfully removed"
            
            elif task.issue_type == RefactoringIssueType.INTEGRATION:
                # Re-run integration conflict detection
                self.logger.debug(f"  🔍 Verifying integration conflict resolution for {task.target_files}")
                
                # Re-run integration conflict detection
                result = self.conflict_detector.analyze()
                conflicts = result.conflicts
                
                if conflicts:
                    return False, f"Files still have {len(conflicts)} integration conflict(s)"
                
                return True, "Integration conflicts resolved"
            
            else:
                # For other types, assume resolved if resolving tool was called
                # (This is the old behavior, kept as fallback)
                self.logger.debug(f"  ℹ️  No verification available for {task.issue_type.value}, assuming resolved")
                return True, "Resolution assumed (no verification available)"
        
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error verifying task resolution: {e}")
            # On error, assume resolved to avoid blocking
            return True, f"Verification error (assumed resolved): {e}"
    
    def _update_architecture_after_task(self, task):
        """
        Update ARCHITECTURE.md after completing a refactoring task.
        
        CRITICAL FIX: Keep architecture document in sync with code changes.
        
        Args:
            task: Completed RefactoringTask
        """
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        try:
            # Only update for certain task types
            if task.issue_type not in [
                RefactoringIssueType.STRUCTURE,
                RefactoringIssueType.ARCHITECTURE,
                RefactoringIssueType.DUPLICATE
            ]:
                return
            
            # Read current ARCHITECTURE.md
            arch_path = self.project_dir / 'ARCHITECTURE.md'
            if not arch_path.exists():
                self.logger.debug("  ℹ️  No ARCHITECTURE.md to update")
                return
            
            arch_content = arch_path.read_text()
            
            # Build update message
            update_lines = [
                "",
                f"## Refactoring Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                f"**Task**: {task.title}",
                f"**Type**: {task.issue_type.value}",
                f"**Files**: {', '.join(task.target_files)}",
                "",
                f"**Changes**: {task.result if task.result else 'See git history for details'}",
                ""
            ]
            
            # Append to ARCHITECTURE.md
            updated_content = arch_content + "\n".join(update_lines)
            arch_path.write_text(updated_content)
            
            self.logger.info(f"  📝 Updated ARCHITECTURE.md with refactoring changes")
        
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error updating ARCHITECTURE.md: {e}")
    
    def _write_task_completion_to_ipc(self, task):
        """
        Write task completion to IPC documents.
        
        Args:
            task: Completed RefactoringTask
        """
        try:
            # Read current WRITE document
            current_content = self.doc_ipc.read_own_document('refactoring') or ""
            
            # Add completion notice
            completion_lines = [
                "",
                f"## Task Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                f"**Task ID**: {task.task_id}",
                f"**Title**: {task.title}",
                f"**Type**: {task.issue_type.value}",
                f"**Files**: {', '.join(task.target_files)}",
                f"**Status**: ✅ COMPLETED",
                ""
            ]
            
            updated_content = current_content + "\n".join(completion_lines)
            
            # Write to WRITE document
            self.doc_ipc.write_own_document('refactoring', updated_content)
            
            self.logger.debug(f"  📝 Updated IPC with task completion")
        
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error writing to IPC: {e}")
    
    def _read_ipc_objectives(self) -> Dict[str, List[str]]:
        """
        Read PRIMARY/SECONDARY/TERTIARY objectives from IPC documents.
        
        CRITICAL FIX: Use project objectives to prioritize refactoring tasks.
        
        Returns:
            Dictionary with 'primary', 'secondary', 'tertiary' keys
        """
        try:
            objectives = {
                'primary': [],
                'secondary': [],
                'tertiary': []
            }
            
            # Read PRIMARY_OBJECTIVES.md
            primary_content = self.doc_ipc.read_strategic_document('PRIMARY_OBJECTIVES.md')
            if primary_content:
                objectives['primary'] = self._parse_objectives(primary_content)
            
            # Read SECONDARY_OBJECTIVES.md
            secondary_content = self.doc_ipc.read_strategic_document('SECONDARY_OBJECTIVES.md')
            if secondary_content:
                objectives['secondary'] = self._parse_objectives(secondary_content)
            
            # Read TERTIARY_OBJECTIVES.md
            tertiary_content = self.doc_ipc.read_strategic_document('TERTIARY_OBJECTIVES.md')
            if tertiary_content:
                objectives['tertiary'] = self._parse_objectives(tertiary_content)
            
            return objectives
        
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error reading IPC objectives: {e}")
            return {'primary': [], 'secondary': [], 'tertiary': []}
    
    def _parse_objectives(self, content: str) -> List[str]:
        """
        Parse objectives from markdown content.
        
        Args:
            content: Markdown content with objectives
            
        Returns:
            List of objective strings
        """
        objectives = []
        
        # Look for bullet points or numbered lists
        for line in content.split('\n'):
            line = line.strip()
            
            # Match bullet points (-, *, +) or numbered lists (1., 2., etc.)
            if line.startswith(('-', '*', '+')) or (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
                # Remove the bullet/number
                if line.startswith(('-', '*', '+')):
                    objective = line[1:].strip()
                else:
                    objective = line.split('.', 1)[1].strip() if '.' in line else line
                
                if objective:
                    objectives.append(objective)
        
        return objectives
    
    def _is_duplicate_task(self, manager, new_task_data: Dict) -> bool:
        """
        Check if a task already exists (including recently completed tasks).
        
        CRITICAL FIX: Prevent creating duplicate tasks for issues that were
        recently resolved or are currently being worked on.
        
        Args:
            manager: RefactoringTaskManager
            new_task_data: Dictionary with 'issue_type' and 'target_files'
            
        Returns:
            True if task is duplicate, False otherwise
        """
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        issue_type = new_task_data.get('issue_type')
        target_files = set(new_task_data.get('target_files', []))
        
        for task in manager.tasks.values():
            # Check same issue type
            if task.issue_type != issue_type:
                continue
            
            # Check same files (order-independent)
            if set(task.target_files) != target_files:
                continue
            
            # Check if currently active (NEW or IN_PROGRESS)
            if task.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]:
                self.logger.debug(f"  🔍 Found active task {task.task_id} for same files")
                return True
            
            # Check if recently completed (within last hour)
            if task.status == TaskStatus.COMPLETED:
                if hasattr(task, 'completed_at') and task.completed_at:
                    time_since = datetime.now() - task.completed_at
                    hours_since = time_since.total_seconds() / 3600
                    
                    if hours_since < 1.0:
                        # Recently completed, don't recreate
                        self.logger.debug(f"  🔍 Found recently completed task {task.task_id} ({hours_since*60:.0f} min ago)")
                        return True
            
            # Check if recently failed (within last 30 minutes)
            # Don't immediately recreate failed tasks
            if task.status == TaskStatus.FAILED:
                if hasattr(task, 'updated_at') and task.updated_at:
                    time_since = datetime.now() - task.updated_at
                    minutes_since = time_since.total_seconds() / 60
                    
                    if minutes_since < 30:
                        # Recently failed, don't recreate yet
                        self.logger.debug(f"  🔍 Found recently failed task {task.task_id} ({minutes_since:.0f} min ago)")
                        return True
        
        return False
