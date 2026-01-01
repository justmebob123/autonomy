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
        
        self.logger.info("  🔧 Refactoring phase initialized with analysis capabilities")
    
    def execute(self, state: PipelineState, 
                refactoring_type: str = None,
                target_files: List[str] = None,
                **kwargs) -> PhaseResult:
        """
        Execute the refactoring phase with multi-iteration support.
        
        NEW DESIGN (Phase 2+3):
        - Uses task system for tracking work
        - Runs for multiple iterations until complete
        - Maintains conversation continuity
        - Tracks progress
        """
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # PHASE 2: Initialize refactoring task manager
        self._initialize_refactoring_manager(state)
        
        # CRITICAL FIX: Clean up broken tasks from before recent fixes
        self._cleanup_broken_tasks(state.refactoring_manager)
        
        # PHASE 3: Check for pending refactoring tasks
        pending_tasks = self._get_pending_refactoring_tasks(state)
        
        if not pending_tasks:
            # No pending tasks - run analysis to find issues
            self.logger.info(f"  🔍 No pending tasks, analyzing codebase...")
            return self._analyze_and_create_tasks(state)
        
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
        if not hasattr(self, '_analysis_tracker'):
            from pipeline.state.task_analysis_tracker import TaskAnalysisTracker
            self._analysis_tracker = TaskAnalysisTracker()
            self.logger.debug(f"  📋 Initialized task analysis tracker")
    
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
        
        # Use existing comprehensive refactoring handler for analysis
        result = self._handle_comprehensive_refactoring(state)
        
        # CRITICAL FIX: Auto-create tasks from analysis results
        # The LLM often detects issues but doesn't create tasks
        # We need to auto-create tasks when issues are found
        tasks_created = self._auto_create_tasks_from_analysis(state, result)
        
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
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Analysis complete, {len(pending)} issues found",
                next_phase="refactoring"  # Continue to work on tasks
            )
        else:
            self.logger.info(f"  ✅ Analysis complete, no issues found")
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
                    issue_type=RefactoringIssueType.MISPLACED_FILE,
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
        is_valid, error_message = self._analysis_tracker.validate_tool_calls(
            task_id=task.task_id,
            tool_calls=tool_calls,
            target_files=task.target_files,
            attempt_number=task.attempts,
            analysis_data=task.analysis_data
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
        
        for result in results:
            if result.get("success"):
                tool_name = result.get("tool", "")
                if tool_name in resolving_tools:
                    task_resolved = True
                    break
        
        if task_resolved:
            # Task actually resolved
            task.complete(content)
            self.logger.info(f"  ✅ Task {task.task_id} completed successfully")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Task {task.task_id} completed"
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
        
        Args:
            issue_type: Type of refactoring issue
            data: Raw analysis data dictionary
            
        Returns:
            Formatted string with clear action items
        """
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        if issue_type == RefactoringIssueType.DUPLICATE:
            files = data.get('files', [])
            similarity = data.get('similarity', 0)
            file1 = files[0] if len(files) > 0 else 'unknown'
            file2 = files[1] if len(files) > 1 else 'unknown'
            
            return f"""
DUPLICATE FILES DETECTED:
- File 1: {file1}
- File 2: {file2}
- Similarity: {similarity:.0%}

ACTION REQUIRED:
Use merge_file_implementations to merge these duplicate files into one.

EXAMPLE:
merge_file_implementations(
    source_files=["{file1}", "{file2}"],
    target_file="{file1}",
    strategy="ai_merge"
)

OPTIONAL: If you want to understand the differences first, you CAN compare:
compare_file_implementations(file1="{file1}", file2="{file2}")
BUT you MUST still call merge_file_implementations after comparing!

The merge tool will:
- Automatically handle imports
- Preserve all functionality
- Remove duplicates
- Create backups
"""
        
        elif issue_type == RefactoringIssueType.COMPLEXITY:
            func_name = data.get('name', 'unknown')
            complexity = data.get('complexity', 0)
            file_path = data.get('file', 'unknown')
            
            return f"""
HIGH COMPLEXITY DETECTED:
- Function: {func_name}
- File: {file_path}
- Complexity: {complexity}

ACTION REQUIRED:
1. Review the function to understand its logic
2. Break it down into smaller, focused functions
3. Use create_issue_report if refactoring requires major changes
"""
        
        elif issue_type == RefactoringIssueType.INTEGRATION or issue_type == RefactoringIssueType.CONFLICT:
            # Check if this is an unused class/function issue
            issue_desc = str(data).lower()
            if 'unused' in issue_desc or 'never instantiated' in issue_desc or 'dead code' in issue_desc:
                # Extract file path if available
                file_path = data.get('file', 'unknown') if isinstance(data, dict) else 'unknown'
                class_name = data.get('class', 'unknown') if isinstance(data, dict) else 'unknown'
                
                # Perform comprehensive analysis of unused code
                from pipeline.analysis.unused_code_analyzer import UnusedCodeAnalyzer, UnusedCodeDecision
                
                analyzer = UnusedCodeAnalyzer(str(self.project_dir), self.logger)
                analysis = analyzer.analyze(file_path, class_name, 'class')
                
                decision_actions = {
                    UnusedCodeDecision.INTEGRATE: f"""
UNUSED CODE ANALYSIS - INTEGRATION RECOMMENDED:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Architecture Alignment: {analysis.architecture_alignment}
- Decision: INTEGRATE (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

INTEGRATION PLAN:
{analysis.integration_plan}

ACTION REQUIRED:
This unused code appears to be a SUPERIOR implementation that should be integrated.

Use create_issue_report to document the integration plan:

EXAMPLE:
create_issue_report(
    task_id="current_task_id",
    title="Integrate superior implementation: {class_name}",
    description="{analysis.reasoning}

Integration Plan:
{analysis.integration_plan}

Related files that may need refactoring:
{chr(10).join('- ' + f for f in analysis.related_files[:5])}",
    severity="medium",
    recommended_approach="Refactor related files to use this superior implementation",
    files_affected=["{file_path}"] + {analysis.related_files[:5]}
)

✅ This code should be INTEGRATED, not removed!
""",
                    UnusedCodeDecision.KEEP: f"""
UNUSED CODE ANALYSIS - KEEP FOR FUTURE USE:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Architecture Alignment: {analysis.architecture_alignment}
- Decision: KEEP (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

ACTION REQUIRED:
Mark this task as complete - this code should be KEPT for future integration.

Use update_refactoring_task to mark as resolved:

EXAMPLE:
update_refactoring_task(
    task_id="current_task_id",
    status="COMPLETED",
    notes="Analysis shows this code aligns with architecture and should be kept for future integration. Project is in {analysis.project_stage} stage."
)

✅ This code is part of planned architecture - KEEP IT!
""",
                    UnusedCodeDecision.REPORT: f"""
UNUSED CODE ANALYSIS - DEVELOPER REVIEW REQUIRED:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Architecture Alignment: {analysis.architecture_alignment}
- Decision: REPORT (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

Related files found:
{chr(10).join('- ' + f for f in analysis.related_files[:5]) if analysis.related_files else '(none)'}

ACTION REQUIRED:
Create an issue report for developer review:

EXAMPLE:
create_issue_report(
    task_id="current_task_id",
    title="Review unused code: {class_name}",
    description="{analysis.reasoning}

Related files:
{chr(10).join('- ' + f for f in analysis.related_files[:5]) if analysis.related_files else '(none)'}

Developer should determine:
1. Is this part of planned architecture?
2. Should it be integrated into existing code?
3. Is it truly redundant and safe to remove?",
    severity="low",
    recommended_approach="Manual review and decision required",
    files_affected=["{file_path}"]
)

⚠️ Requires developer review to make final decision
"""
                }
                
                return decision_actions.get(analysis.decision, decision_actions[UnusedCodeDecision.REPORT])
            else:
                # Regular integration conflict - extract specific details
                files = data.get('files', []) if isinstance(data, dict) else []
                description = data.get('description', 'Unknown conflict') if isinstance(data, dict) else str(data)
                conflict_type = data.get('type', 'unknown') if isinstance(data, dict) else 'unknown'
                
                # Build specific file list
                file_list = "\n".join(f"- {f}" for f in files) if files else "- (files not specified)"
                
                return f"""
INTEGRATION CONFLICT DETECTED:
Type: {conflict_type}
Description: {description}

FILES INVOLVED:
{file_list}

SPECIFIC ACTIONS TO TAKE:

Step 1: READ the conflicting files to understand what they do
{chr(10).join(f'read_file(filepath="{f}")' for f in files[:3]) if files else 'read_file(filepath="<file>")'}

Step 2: READ ARCHITECTURE.md to understand where they should be
read_file(filepath="ARCHITECTURE.md")

Step 3: COMPARE the implementations to see if they're duplicates
{f'compare_file_implementations(file1="{files[0]}", file2="{files[1]}")' if len(files) >= 2 else 'compare_file_implementations(file1="<file1>", file2="<file2>")'}

Step 4: MAKE A DECISION based on what you found:
- If files are >80% similar → merge_file_implementations
- If one is misplaced → move_file to correct location
- If both are misplaced → move both files
- If names conflict → rename_file to clarify

Step 5: EXECUTE your decision (merge, move, or rename)

⚠️ DO NOT just analyze and stop - you MUST take action to resolve the conflict!
"""
        
        elif issue_type == RefactoringIssueType.DEAD_CODE:
            # Dead code - perform comprehensive analysis
            item_name = data.get('name', 'unknown') if isinstance(data, dict) else 'unknown'
            item_file = data.get('file', 'unknown') if isinstance(data, dict) else 'unknown'
            item_type = data.get('type', 'function') if isinstance(data, dict) else 'function'
            
            # Perform comprehensive analysis
            from pipeline.analysis.unused_code_analyzer import UnusedCodeAnalyzer, UnusedCodeDecision
            
            analyzer = UnusedCodeAnalyzer(str(self.project_dir), self.logger)
            analysis = analyzer.analyze(item_file, item_name, item_type)
            
            # Generate response based on analysis decision
            if analysis.decision == UnusedCodeDecision.INTEGRATE:
                action_text = f"""
DEAD CODE ANALYSIS - INTEGRATION RECOMMENDED:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: INTEGRATE (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

INTEGRATION PLAN:
{analysis.integration_plan}

ACTION: Create issue report with integration plan
"""
            elif analysis.decision == UnusedCodeDecision.KEEP:
                action_text = f"""
DEAD CODE ANALYSIS - KEEP FOR FUTURE:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: KEEP (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

ACTION: Mark task complete - code should be kept
"""
            else:
                action_text = f"""
DEAD CODE ANALYSIS - REVIEW REQUIRED:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: REPORT (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

Related files: {', '.join(analysis.related_files[:3]) if analysis.related_files else 'none'}

ACTION: Create issue report for developer review
"""
            
            return action_text
        
        elif issue_type == RefactoringIssueType.ARCHITECTURE:
            # Check what type of architecture issue this is
            data_type = data.get('type', '') if isinstance(data, dict) else ''
            
            # Check if this is a dictionary key error
            if 'key_path' in data:
                # This is a dictionary key error from validate_dict_structure
                key_path = data.get('key_path', 'unknown')
                file_path = data.get('file', 'unknown')
                line = data.get('line', '?')
                message = data.get('message', 'Dictionary key error')
                suggestion = data.get('suggestion', 'Add default value or check if key exists')
                
                return f"""
DICTIONARY KEY ERROR DETECTED:
- Key path: {key_path}
- File: {file_path}
- Line: {line}
- Error: {message}
- Suggestion: {suggestion}

ACTION REQUIRED:
1. Read the file to understand the context
2. Fix the dictionary access to handle missing keys
3. If the fix is complex, create an issue report

EXAMPLE (simple fix):
read_file(filepath="{file_path}")
# Then use modify_file or replace_between to add:
# - .get() with default value: dict.get('key', default_value)
# - Check if key exists: if 'key' in dict:
# - Try/except: try: value = dict['key'] except KeyError: value = default

EXAMPLE (complex fix):
create_issue_report(
    title="Dictionary key error: {key_path}",
    description="Line {line} in {file_path}: {message}",
    severity="high",
    suggested_fix="{suggestion}",
    files_affected=["{file_path}"]
)

⚠️ DO NOT try to fix errors in files that don't exist - verify file path first!
"""
            
            # Check if this is a missing method error
            elif 'method_name' in data and 'class_name' in data:
                # This is a missing method from validate_method_existence
                method_name = data.get('method_name', 'unknown')
                class_name = data.get('class_name', 'unknown')
                file_path = data.get('file', 'unknown')
                line = data.get('line', '?')
                message = data.get('message', 'Method not found')
                
                return f"""
MISSING METHOD DETECTED:
- Class: {class_name}
- Method: {method_name}
- File: {file_path}
- Line: {line}
- Error: {message}

ACTION REQUIRED:
1. Read the file to see the class definition
2. Implement the missing method in the class
3. If implementation requires domain knowledge, create an issue report

EXAMPLE (implement method):
read_file(filepath="{file_path}")
# Then use insert_after or modify_file to add the method to the class

EXAMPLE (if complex):
create_issue_report(
    title="Missing method: {class_name}.{method_name}",
    description="Method {method_name} is called but not defined in {class_name} at line {line}",
    severity="critical",
    suggested_fix="Implement the {method_name} method in {class_name} class",
    files_affected=["{file_path}"]
)

✅ PREFER implementing the method if it's straightforward (e.g., getter/setter, simple utility)
⚠️ CREATE REPORT only if implementation requires business logic or domain knowledge
"""
            
            # Check if this is a bug (bugs are categorized as ARCHITECTURE issues)
            elif 'message' in data and 'line' in data and 'file' in data and 'type' in data:
                # This is a bug from find_bugs tool
                bug_type = data.get('type', 'unknown')
                bug_message = data.get('message', 'Unknown error')
                bug_file = data.get('file', 'unknown')
                bug_line = data.get('line', '?')
                bug_suggestion = data.get('suggestion', 'Fix the issue')
                
                return f"""
BUG DETECTED:
- Type: {bug_type}
- File: {bug_file}
- Line: {bug_line}
- Error: {bug_message}
- Suggestion: {bug_suggestion}

ACTION REQUIRED:
1. Read the file to understand the context
2. Fix the bug using appropriate file modification tools
3. If the bug is complex, create an issue report

EXAMPLE (simple fix):
read_file(filepath="{bug_file}")
# Then use modify_file, replace_between, or str_replace to fix the issue

EXAMPLE (complex fix):
create_issue_report(
    title="Bug: {bug_type}",
    description="Line {bug_line} in {bug_file}: {bug_message}",
    severity="high",
    suggested_fix="{bug_suggestion}",
    files_affected=["{bug_file}"]
)

⚠️ DO NOT try to fix bugs in files that don't exist - verify file path first!
"""
            
            elif data_type == 'antipattern':
                pattern_name = data.get('pattern_name', 'Unknown')
                pattern_file = data.get('file', 'unknown')
                pattern_desc = data.get('description', '')
                pattern_suggestion = data.get('suggestion', '')
                
                return f"""
ANTI-PATTERN DETECTED:
- Pattern: {pattern_name}
- File: {pattern_file}
- Description: {pattern_desc}
- Suggestion: {pattern_suggestion}

ACTION REQUIRED:
Create a detailed issue report for developer review:

EXAMPLE:
create_issue_report(
    title="Anti-pattern: {pattern_name}",
    description="Detected {pattern_name} in {pattern_file}. {pattern_desc}",
    severity="medium",
    suggested_fix="{pattern_suggestion}",
    files_affected=["{pattern_file}"]
)

⚠️ Anti-patterns usually require careful refactoring - create a detailed report.
"""
            
            elif data_type == 'architecture_violation':
                violation_type = data.get('violation_type', 'unknown')
                violation_file = data.get('file', 'unknown')
                violation_desc = data.get('description', '')
                violation_suggestion = data.get('suggestion', '')
                
                return f"""
ARCHITECTURE VIOLATION DETECTED:
- Type: {violation_type}
- File: {violation_file}
- Description: {violation_desc}
- Suggestion: {violation_suggestion}

ACTION REQUIRED:
1. If file is in wrong location → use move_file
2. If violation is complex → use create_issue_report

EXAMPLE (if file misplaced):
move_file(
    file_path="{violation_file}",
    new_path="correct/location/file.py",
    reason="Fix architecture violation: {violation_type}"
)

EXAMPLE (if complex):
create_issue_report(
    title="Architecture violation: {violation_type}",
    description="{violation_desc}",
    suggested_fix="{violation_suggestion}"
)
"""
            
            elif data_type == 'circular_import':
                cycle_path = data.get('cycle', [])
                cycle_files = data.get('files', [])
                cycle_desc = data.get('description', '')
                
                return f"""
CIRCULAR IMPORT DETECTED:
- Cycle: {' → '.join(cycle_path)}
- Files involved: {', '.join(cycle_files)}

ACTION REQUIRED:
Create a detailed issue report - circular imports require careful analysis:

EXAMPLE:
create_issue_report(
    title="Circular import: {len(cycle_files)} files",
    description="{cycle_desc}",
    severity="high",
    suggested_fix="Restructure imports or move shared code to separate module",
    files_affected={cycle_files}
)

⚠️ Circular imports are complex - create a detailed report for developer review.
"""
            
            else:
                # Generic architecture issue
                return f"""
ARCHITECTURE ISSUE DETECTED:
{data}

ACTION REQUIRED:
Analyze the issue and use appropriate tools:
- move_file: If files are in wrong locations
- create_issue_report: If issue requires developer decision
"""
        
        else:
            return f"""
ISSUE DETECTED:
{data}

ACTION REQUIRED:
Review the issue and use appropriate refactoring tools to resolve it.
"""
    
    def _build_task_prompt(self, task: Any, context: str) -> str:
        """Build prompt for working on a specific task"""
        from pipeline.state.refactoring_task import RefactoringIssueType
        
        # CRITICAL FIX: Use task-type-specific prompts instead of generic one-size-fits-all
        # Different task types need different workflows
        
        if task.issue_type == RefactoringIssueType.ARCHITECTURE:
            # Check if this is a missing method task
            if "Missing method:" in task.title or ("method_name" in task.analysis_data and "class_name" in task.analysis_data):
                return self._get_missing_method_prompt(task, context)
            # Check if this is a dictionary key error
            elif "Dictionary key error" in task.title or "key_path" in task.analysis_data:
                return self._get_bug_fix_prompt(task, context)
            # Generic architecture issue
            else:
                return self._get_architecture_violation_prompt(task, context)
        
        elif task.issue_type == RefactoringIssueType.DUPLICATE:
            return self._get_duplicate_code_prompt(task, context)
        
        elif task.issue_type == RefactoringIssueType.INTEGRATION or task.issue_type == RefactoringIssueType.CONFLICT:
            return self._get_integration_conflict_prompt(task, context)
        
        elif task.issue_type == RefactoringIssueType.DEAD_CODE:
            return self._get_dead_code_prompt(task, context)
        
        elif task.issue_type == RefactoringIssueType.COMPLEXITY:
            return self._get_complexity_prompt(task, context)
        
        # Fallback to generic prompt
        return self._get_generic_task_prompt(task, context)
    
    def _get_missing_method_prompt(self, task: Any, context: str) -> str:
        """Prompt for missing method tasks - simple and direct"""
        return f"""🎯 MISSING METHOD TASK - IMPLEMENT THE METHOD

⚠️ CRITICAL: This is a SIMPLE task - just implement the missing method!

{context}

📋 SIMPLE WORKFLOW (2-3 steps):

1️⃣ **Read the file** to see the class definition:
   read_file(filepath="<file_path>")

2️⃣ **Implement the method** OR create issue report:
   
   **Option A - Implement directly** (PREFERRED if straightforward):
   - If it's a simple method (getter, setter, utility), implement it
   - Use modify_file or insert_after to add the method
   - Example: Adding a generate_risk_chart method that creates a chart
   
   **Option B - Create issue report** (if requires domain knowledge):
   - Use create_issue_report if you need to understand business logic
   - Provide clear description of what the method should do
   - Include code examples and suggestions

⚠️ DO NOT:
- List all source files (you already know which file)
- Find related files (not needed for adding a method)
- Map relationships (not needed for this task)
- Compare implementations (nothing to compare)

✅ JUST:
- Read the file
- Implement the method OR create report
- Done!

🎯 TAKE ACTION NOW - This should take 1-2 tool calls, not 10+!
"""
    
    def _get_duplicate_code_prompt(self, task: Any, context: str) -> str:
        """Prompt for duplicate code tasks - compare then merge"""
        return f"""🎯 DUPLICATE CODE TASK - MERGE THE FILES

{context}

📋 SIMPLE WORKFLOW (2-3 steps):

1️⃣ **OPTIONAL: Compare files** to understand differences:
   compare_file_implementations(file1="<file1>", file2="<file2>")
   
2️⃣ **Merge the files** (REQUIRED - this resolves the task):
   merge_file_implementations(
       source_files=["<file1>", "<file2>"],
       target_file="<file1>",
       strategy="ai_merge"
   )

⚠️ DO NOT:
- List all source files (you already know which files to merge)
- Find related files (task specifies the files)
- Map relationships (not needed for merging)
- Just compare and stop (that's analysis, not resolution)

✅ WORKFLOW:
- Compare (optional, for understanding)
- Merge (required, resolves the task)
- Done!

🎯 TAKE ACTION NOW - Merge the files to complete this task!
"""
    
    def _get_integration_conflict_prompt(self, task: Any, context: str) -> str:
        """Prompt for integration conflicts - STEP-AWARE to prevent multiple tool outputs"""
        
        # Get target files from task
        target_files = task.target_files if task.target_files else []
        file1 = target_files[0] if len(target_files) > 0 else "file1"
        file2 = target_files[1] if len(target_files) > 1 else "file2"
        
        # FIXED: Use TaskAnalysisTracker to check actual tool executions
        # instead of checking assistant message content
        state = self.analysis_tracker.get_or_create_state(task.task_id)
        
        # Count what's been done by looking at ACTUAL tool executions
        files_read = set()
        architecture_read = state.checkpoints['read_architecture'].completed
        comparison_done = False
        
        for tool_call in state.tool_calls_history:
            tool_name = tool_call['tool']
            arguments = tool_call.get('arguments', {})
            
            if tool_name == 'read_file':
                filepath = arguments.get('filepath') or arguments.get('file_path', '')
                # Check if target files were read
                if file1 in filepath:
                    files_read.add(file1)
                if file2 in filepath:
                    files_read.add(file2)
            
            if tool_name == 'compare_file_implementations':
                comparison_done = True
        
        # Determine next step
        if file1 not in files_read:
            # Step 1: Read first file
            step_num = 1
            next_tool = f'read_file(filepath="{file1}")'
            step_description = f"READ THE FIRST FILE: {file1}"
            
        elif file2 not in files_read:
            # Step 2: Read second file
            step_num = 2
            next_tool = f'read_file(filepath="{file2}")'
            step_description = f"READ THE SECOND FILE: {file2}"
            
        elif not architecture_read:
            # Step 3: Read architecture
            step_num = 3
            next_tool = 'read_file(filepath="ARCHITECTURE.md")'
            step_description = "READ ARCHITECTURE.md to see where files should be"
            
        elif not comparison_done:
            # Step 4: Compare
            step_num = 4
            next_tool = f'compare_file_implementations(file1="{file1}", file2="{file2}")'
            step_description = "COMPARE the two implementations"
            
        else:
            # Step 5: Make decision and resolve
            step_num = 5
            next_tool = "merge_file_implementations(...) OR move_file(...) OR rename_file(...)"
            step_description = "MAKE A DECISION and RESOLVE the conflict"
        
        return f"""🎯 INTEGRATION CONFLICT - STEP {step_num} OF 5

{context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL SYSTEM CONSTRAINT ⚠️

THE SYSTEM CAN ONLY EXECUTE **ONE** TOOL CALL PER ITERATION.

If you output multiple tool calls, ONLY THE FIRST ONE will execute.
The rest will be IGNORED and you'll be stuck in an infinite loop.

YOU MUST OUTPUT EXACTLY ONE TOOL CALL. THEN STOP.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 YOU ARE ON STEP {step_num} OF 5

🎯 YOUR NEXT ACTION:
{step_description}

💻 CALL THIS ONE TOOL:
{next_tool}

⛔ DO NOT:
- Output multiple tool calls
- Call any other tools
- Plan ahead for future steps
- Output JSON arrays

✅ DO:
- Output EXACTLY ONE tool call
- Use the exact tool shown above
- Then STOP and wait

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PROGRESS TRACKER:
Step 1: Read {file1} {'✅' if file1 in files_read else '⏳ ← YOU ARE HERE' if step_num == 1 else '⬜'}
Step 2: Read {file2} {'✅' if file2 in files_read else '⏳ ← YOU ARE HERE' if step_num == 2 else '⬜'}
Step 3: Read ARCHITECTURE.md {'✅' if architecture_read else '⏳ ← YOU ARE HERE' if step_num == 3 else '⬜'}
Step 4: Compare implementations {'✅' if comparison_done else '⏳ ← YOU ARE HERE' if step_num == 4 else '⬜'}
Step 5: Resolve conflict {'⏳ ← YOU ARE HERE' if step_num == 5 else '⬜'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 OUTPUT YOUR ONE TOOL CALL NOW:
"""
    
    
    def _get_dead_code_prompt(self, task: Any, context: str) -> str:
        """Prompt for dead code tasks - check usage then decide"""
        return f"""🎯 DEAD CODE TASK - ANALYZE AND REPORT

⚠️ CRITICAL: This is an EARLY-STAGE project - DO NOT auto-remove code!

{context}

📋 SIMPLE WORKFLOW (2-3 steps):

1️⃣ **Search for usages** of the code:
   search_code(pattern="<class_name>", file_types=["py"])

2️⃣ **Create issue report** (REQUIRED for early-stage projects):
   create_issue_report(
       task_id="{task.task_id}",
       severity="low",
       impact_analysis="Unused code may be part of planned architecture",
       recommended_approach="Review MASTER_PLAN to determine if needed",
       estimated_effort="30 minutes"
   )

⚠️ DO NOT:
- Remove the code automatically (early-stage project!)
- List all source files (not needed)
- Do comprehensive analysis (just check if used)

✅ WORKFLOW:
- Search for usages
- Create report for developer review
- Done!

🎯 TAKE ACTION NOW - Create the report to complete this task!
"""
    
    def _get_complexity_prompt(self, task: Any, context: str) -> str:
        """Prompt for complexity tasks - try to refactor or report"""
        return f"""🎯 COMPLEXITY TASK - REFACTOR OR REPORT

{context}

📋 WORKFLOW (try to fix first):

1️⃣ **Read the file** to understand the complex function:
   read_file(filepath="<file_path>")

2️⃣ **Try to refactor** if straightforward:
   - Break into smaller functions
   - Extract common logic
   - Simplify conditionals
   
   OR **Create issue report** if too complex:
   create_issue_report(
       task_id="{task.task_id}",
       severity="medium",
       impact_analysis="High complexity makes code hard to maintain",
       recommended_approach="Break function into smaller pieces",
       estimated_effort="2 hours"
   )

🎯 TAKE ACTION NOW - Try to refactor, or create report!
"""
    
    def _get_architecture_violation_prompt(self, task: Any, context: str) -> str:
        """Prompt for architecture violations - move or rename"""
        return f"""🎯 ARCHITECTURE VIOLATION TASK - FIX THE STRUCTURE

{context}

📋 WORKFLOW:

1️⃣ **Check architecture** to understand correct location:
   read_file(filepath="ARCHITECTURE.md")

2️⃣ **Fix the violation**:
   - Use move_file to relocate misplaced files
   - Use rename_file to fix naming issues
   - Use restructure_directory for large changes

🎯 TAKE ACTION NOW - Align code with architecture!
"""
    
    def _get_bug_fix_prompt(self, task: Any, context: str) -> str:
        """Prompt for bug fix tasks - read, understand, fix"""
        return f"""🎯 BUG FIX TASK - FIX THE BUG

{context}

📋 SIMPLE WORKFLOW:

1️⃣ **Read the file** to see the bug:
   read_file(filepath="<file_path>")

2️⃣ **Fix the bug** OR create report:
   - If simple (missing check, wrong key), fix it directly
   - If complex (requires domain knowledge), create report

🎯 TAKE ACTION NOW - Fix it or report it!
"""
    
    def _get_generic_task_prompt(self, task: Any, context: str) -> str:
        """Generic prompt for unknown task types"""
        # Get checklist status from analysis tracker
        checklist_status = self._analysis_tracker.get_checklist_status(
            task_id=task.task_id,
            target_files=task.target_files
        )
        
        next_step = self._analysis_tracker.get_next_step(
            task_id=task.task_id,
            target_files=task.target_files
        )
        
        is_complete = self._analysis_tracker.is_analysis_complete(
            task_id=task.task_id,
            target_files=task.target_files
        )
        
        # Build checklist section
        checklist_section = f"""
📋 MANDATORY ANALYSIS CHECKLIST (Attempt {task.attempts}/{task.max_attempts}):

{checklist_status}

{'✅ Analysis complete! You can now take resolving action.' if is_complete else f'⚠️ NEXT REQUIRED STEP: {next_step}'}

{'🔓 You may now use resolving tools (merge, report, etc.)' if is_complete else '🔒 You CANNOT use resolving tools until ALL checklist items are complete!'}
"""
        
        return f"""🎯 REFACTORING TASK - YOU MUST FIX THIS ISSUE

⚠️ CRITICAL: YOUR JOB IS TO FIX ISSUES, NOT JUST DOCUMENT THEM!

{checklist_section}

🚨 EXCEPTION: This is an EARLY-STAGE project. DO NOT remove unused/dead code automatically!
   - Unused code may be part of planned architecture not yet integrated
   - Create issue reports for unused code instead of removing it
   - Only merge duplicates or fix actual bugs

This is NOT a documentation task. This is a FIXING task.
- If you can fix it safely → FIX IT NOW using the tools
- Only create reports if the fix is genuinely too complex or risky
- "Too complex" means requires major architectural changes, not just merging files
- UNUSED CODE = create report (don't remove in early-stage projects)

🔬 COMPREHENSIVE ANALYSIS REQUIRED (CONTINUOUS MODE):

This system operates in CONTINUOUS MODE with NO ATTEMPT LIMITS. You will continue working on this task until it is ACTUALLY RESOLVED.

Before taking ANY resolving action, you MUST complete comprehensive analysis:

**REQUIRED ANALYSIS TOOLS** (use ALL of these):
1. list_all_source_files - See the entire codebase structure
2. find_all_related_files - Find ALL files related to this issue
3. read_file - Read ALL target and related files
4. map_file_relationships - Understand dependencies and imports
5. cross_reference_file - Validate against ARCHITECTURE.md
6. compare_file_implementations - Compare implementations
7. analyze_file_purpose - Understand purpose of each file

**DO NOT** create reports or make decisions until you have used these tools!

The system will BLOCK you and force retry if you skip comprehensive analysis.

🧠 INTELLIGENT CONFLICT RESOLUTION (CRITICAL FOR INTEGRATION CONFLICTS):

When you see files with similar names in different locations:

1️⃣ **READ BOTH FILES FIRST** - Don't just compare, UNDERSTAND them:
   - Use read_file to see what each file actually does
   - Understand their purpose, not just their similarity score
   - 0% similarity doesn't mean "manual review" - it means they might be intentionally different!

2️⃣ **CHECK ARCHITECTURE.MD** - Understand the intended design:
   - Read ARCHITECTURE.md to see where files should be
   - Check if this separation is intentional
   - See if the architecture explains why both exist

3️⃣ **MAKE AN INTELLIGENT DECISION** - Think, don't just report:
   
   **If files serve DIFFERENT purposes:**
   - Keep both files
   - Update ARCHITECTURE.md to clarify why both exist
   - Document: "X handles A, Y handles B"
   
   **If one is MISPLACED:**
   - Use move_file to relocate to correct location
   - Update imports automatically
   
   **If they're TRUE DUPLICATES:**
   - Use merge_file_implementations
   - Keep the better implementation
   
   **If architecture is UNCLEAR:**
   - Update ARCHITECTURE.md to document the design decision
   - Then decide based on the clarified architecture

4️⃣ **ONLY REPORT IF TRULY UNCLEAR** - Last resort only:
   - You've read both files
   - You've checked the architecture
   - You still can't determine the right action
   - Then and only then create an issue report

❌ WRONG APPROACH:
- compare_file_implementations → see 0% similarity → create report
- This is LAZY and doesn't help anyone

✅ RIGHT APPROACH:
- read_file(file1) → understand purpose
- read_file(file2) → understand purpose  
- read_file("ARCHITECTURE.md") → understand design
- Make intelligent decision based on understanding
- Update architecture if needed to clarify design

{context}

🔧 YOUR MISSION: ACTUALLY FIX THE ISSUE

You must RESOLVE this issue by TAKING ACTION, not just analyzing it.

RESOLVING means taking ONE of these actions:

1️⃣ **FIX AUTOMATICALLY** (PREFERRED) - If you can resolve this safely:
   - Use merge_file_implementations to merge duplicate code
   - Use move_file to relocate misplaced files
   - Use rename_file to fix naming issues
   - Use cleanup_redundant_files to remove dead code
   - Use restructure_directory for large reorganizations
   - Verify changes are safe and correct
   - These tools RESOLVE the issue by FIXING it

2️⃣ **CREATE DETAILED DEVELOPER REPORT** - If issue is complex:
   - Use create_issue_report tool with these EXACT parameters:
     * task_id: (required) The task ID
     * severity: (required) "critical", "high", "medium", or "low"
     * impact_analysis: What breaks or degrades if not fixed
     * recommended_approach: How to fix it (step-by-step)
     * code_examples: Before/after code snippets
     * estimated_effort: Time estimate (e.g., "2 hours", "1 day")
     * alternatives: Other approaches to consider
   - Example:
     create_issue_report(
         task_id="refactor_0294",
         severity="medium",
         impact_analysis="Unused ResourceEstimation class may be needed for future features",
         recommended_approach="Review MASTER_PLAN to determine if this is planned functionality",
         code_examples="class ResourceEstimation in timeline/resource_estimation.py",
         estimated_effort="30 minutes"
     )
   - This tool RESOLVES the issue by documenting it

3️⃣ **REQUEST DEVELOPER INPUT** - If you need guidance:
   - Use request_developer_review tool
   - Ask specific questions with clear options
   - Provide context to help developer decide
   - This tool RESOLVES the issue by escalating it

📋 WORKFLOW:
1. **Understand the issue**: What's wrong? Why is it a problem?
2. **Check MASTER_PLAN & ARCHITECTURE**: What's the intended design?
3. **Analyze if needed**: Use compare_file_implementations to understand
4. **TAKE ACTION**: Based on analysis, use a RESOLVING tool (merge, report, or ask)

❌ WRONG APPROACH:
- Calling compare_file_implementations and stopping
- Only analyzing without taking action
- Marking task complete without using a resolving tool

✅ RIGHT APPROACH:
- Compare files to understand the issue
- Then use merge_file_implementations to fix
- OR use create_issue_report to document
- OR use request_developer_review to ask

🛠️ TOOL SELECTION GUIDE:
- **Dead code / Unused code**: create_issue_report (EARLY-STAGE PROJECT - do NOT auto-remove!)
- **Duplicates**: merge_file_implementations (RESOLVES by merging) - compare first if needed, but MUST merge
- **Integration conflicts**: 
  * Read files to understand what they do
  * Read ARCHITECTURE.md to understand intended design
  * Compare implementations to see which is better
  * MAKE A DECISION: merge the better one, or move files to correct locations
  * DO NOT create reports - you have all the information you need to decide
  * If files are duplicates → merge them
  * If files conflict → keep the one that matches ARCHITECTURE.md, update the other
- **Architecture violations**: move_file/rename_file to align with ARCHITECTURE.md (RESOLVES by restructuring)
- **Complexity issues**: Refactor code to reduce complexity OR create_issue_report if too complex (TRY TO FIX FIRST)

⚠️ CRITICAL: This is an EARLY-STAGE project. Unused code may be part of planned architecture.
DO NOT remove unused/dead code automatically - create issue reports for developer review instead!

⚠️ REMEMBER: compare_file_implementations is for UNDERSTANDING, not RESOLVING. Always follow it with a resolving tool!

📋 CONCRETE EXAMPLE - DUPLICATE CODE:
Task: Merge duplicates: resources.py ↔ resource_estimator.py
Files: api/resources.py and resources/resource_estimator.py (85% similar)

CORRECT APPROACH:
merge_file_implementations(
    source_files=["api/resources.py", "resources/resource_estimator.py"],
    target_file="api/resources.py",
    strategy="ai_merge"
)
Result: ✅ Files merged, duplicate removed, imports updated, task RESOLVED

ALSO ACCEPTABLE (if you want to understand first):
Step 1: compare_file_implementations(file1="api/resources.py", file2="resources/resource_estimator.py")
Step 2: merge_file_implementations(source_files=["api/resources.py", "resources/resource_estimator.py"], target_file="api/resources.py", strategy="ai_merge")
Result: ✅ Task RESOLVED

WRONG APPROACH:
compare_file_implementations(...) and then STOP
Result: ❌ Task FAILED - only analysis, no action taken

📋 CONCRETE EXAMPLE - INTEGRATION CONFLICT:
Task: Integration conflict
Files: resources/resource_estimator.py and core/resource/resource_estimator.py

CORRECT APPROACH:
Step 1: read_file("resources/resource_estimator.py") - understand what it does
Step 2: read_file("core/resource/resource_estimator.py") - understand what it does
Step 3: read_file("ARCHITECTURE.md") - understand where ResourceEstimator should live
Step 4: compare_file_implementations - see if they're duplicates or different
Step 5: MAKE DECISION based on findings:
  - If duplicates (>80% similar) → merge_file_implementations
  - If different but one matches architecture → move the misplaced one
  - If both wrong location → move both to correct location per ARCHITECTURE.md
Step 6: Execute the decision (merge or move)
Result: ✅ Task RESOLVED by fixing the conflict

EXAMPLE DECISION PROCESS:
After analysis, you find:
- Both files implement ResourceEstimator class
- They're 95% similar (duplicates)
- ARCHITECTURE.md says: "Resource estimation in core/resource/"
- Decision: Merge both into core/resource/resource_estimator.py, delete resources/resource_estimator.py
- Action: merge_file_implementations(source_files=[...], target_file="core/resource/resource_estimator.py")
Result: ✅ Conflict resolved, duplicates merged, correct location

WRONG APPROACH:
Step 1: list_all_source_files
Step 2: find_all_related_files
Step 3: map_file_relationships
Step 4: create_issue_report "I found a conflict, please review"
Result: ❌ Task FAILED - you had all the info to decide, but didn't take action

⚠️ CRITICAL: You have ALL the tools to resolve integration conflicts:
- read_file: understand what files do
- ARCHITECTURE.md: understand where they should be
- compare_file_implementations: see if they're duplicates
- merge_file_implementations: merge duplicates
- move_file: move to correct location

DO NOT create reports for integration conflicts - you can resolve them yourself!

⚠️ CRITICAL RULES:
- NEVER stop after just analyzing (like calling detect_duplicate_implementations or compare_file_implementations alone)
- ALWAYS use a RESOLVING tool (merge, cleanup, report, or review)
- Analysis tools (detect, compare) are for understanding, not resolving
- Task is only complete when you use a resolving tool
- If unsure, create detailed report rather than skip

🎯 TAKE ACTION NOW - Analyze if needed, then RESOLVE with appropriate tool!
"""
    
    def _auto_create_tasks_from_analysis(self, state: PipelineState, analysis_result: PhaseResult) -> int:
        """
        Auto-create refactoring tasks from analysis results.
        
        When the LLM detects issues but does not create tasks, we auto-create them.
        This prevents infinite loops where issues are detected but never fixed.
        
        Args:
            state: Pipeline state
            analysis_result: Result from comprehensive analysis
            
        Returns:
            Number of tasks created
        """
        from pipeline.state.refactoring_task import (
            RefactoringTask, RefactoringIssueType, RefactoringPriority, RefactoringApproach
        )
        
        tasks_created = 0
        
        # Get the refactoring manager
        if not hasattr(state, 'refactoring_manager') or not state.refactoring_manager:
            return 0
        
        manager = state.refactoring_manager
        
        # Check if analysis found duplicates
        # The tool results are stored in the handler's activity log
        # We need to check the last tool execution results
        if hasattr(self, '_last_tool_results'):
            for tool_result in self._last_tool_results:
                tool_name = tool_result.get('tool', '')
                
                # Handle duplicate detection results
                if tool_name == 'detect_duplicate_implementations':
                    # CRITICAL FIX: Handler returns nested structure
                    # {"success": True, "result": {"duplicate_sets": [...], "total_duplicates": N}}
                    result_data = tool_result.get('result', {})
                    duplicates = result_data.get('duplicate_sets', [])
                    
                    if duplicates:
                        self.logger.info(f"  🔍 Found {len(duplicates)} duplicate sets, creating tasks...")
                        
                        for dup in duplicates:
                            # ENHANCED: Create task with specific file names and clear action
                            files = dup.get('files', [])
                            similarity = dup.get('similarity', 0)
                            
                            # Extract file paths for title (use relative paths, not just names)
                            from pathlib import Path
                            file1_path = files[0] if len(files) > 0 else 'unknown'
                            file2_path = files[1] if len(files) > 1 else 'unknown'
                            
                            # Use short paths for title (parent/filename)
                            file1_short = f"{Path(file1_path).parent.name}/{Path(file1_path).name}" if file1_path != 'unknown' else 'unknown'
                            file2_short = f"{Path(file2_path).parent.name}/{Path(file2_path).name}" if file2_path != 'unknown' else 'unknown'
                            
                            # Create task with specific, actionable information
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.DUPLICATE,
                                title=f"Merge duplicates: {file1_short} ↔ {file2_short}",
                                description=f"Merge duplicate files: {files[0] if len(files) > 0 else 'unknown'} and {files[1] if len(files) > 1 else 'unknown'} ({similarity:.0%} similar)",
                                target_files=files,
                                priority=RefactoringPriority.MEDIUM,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=30,
                                analysis_data=dup,
                            )
                            tasks_created += 1
                
                # Handle complexity analysis results
                elif tool_name == 'analyze_complexity':
                    # CRITICAL FIX: Handler returns nested structure
                    result_data = tool_result.get('result', {})
                    critical_functions = result_data.get('critical_functions', [])
                    
                    if critical_functions:
                        self.logger.info(f"  🔍 Found {len(critical_functions)} critical complexity issues, creating tasks...")
                        
                        for func_info in critical_functions[:5]:  # Limit to top 5
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.COMPLEXITY,
                                title=f"High complexity in {func_info.get('name', 'unknown')}",
                                description=f"High complexity: {func_info.get('name', 'unknown')} (complexity: {func_info.get('complexity', 0)})",
                                target_files=[func_info.get('file', '')],
                                priority=RefactoringPriority.HIGH,
                                fix_approach=RefactoringApproach.AUTONOMOUS,  # Let AI decide if it needs developer
                                estimated_effort=60,
                                analysis_data=func_info,
                            )
                            tasks_created += 1
                
                # Handle dead code detection results
                elif tool_name == 'detect_dead_code':
                    # CRITICAL FIX: Handler returns nested structure
                    result_data = tool_result.get('result', {})
                    unused_functions = result_data.get('unused_functions', [])
                    unused_methods = result_data.get('unused_methods', [])
                    dead_code = unused_functions + unused_methods
                    
                    if dead_code:
                        self.logger.info(f"  🔍 Found {len(dead_code)} dead code items, creating tasks...")
                        
                        for item in dead_code[:10]:  # Limit to top 10
                            # ENHANCED: Add analysis_data for dead code
                            item_name = item.get('name', 'unknown')
                            item_file = item.get('file', '')
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.DEAD_CODE,
                                title=f"Remove dead code: {item_name}",
                                description=f"Remove dead code {item_name} from {item_file} (unused in project)",
                                target_files=[item_file],
                                priority=RefactoringPriority.LOW,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=15,
                                analysis_data={
                                    'type': 'dead_code',
                                    'name': item_name,
                                    'file': item_file,
                                    'reason': item.get('reason', 'unused'),
                                    'action': 'cleanup_redundant_files'
                                }
                            )
                            tasks_created += 1
                
                # Handle architecture validation results
                elif tool_name == 'validate_architecture':
                    result_data = tool_result.get('result', {})
                    violations = result_data.get('violations', [])
                    
                    if violations:
                        self.logger.info(f"  🔍 Found {len(violations)} architecture violations, creating tasks...")
                        
                        for violation in violations[:15]:
                            issue_type_map = {
                                'location': RefactoringIssueType.STRUCTURE,
                                'naming': RefactoringIssueType.NAMING,
                                'missing': RefactoringIssueType.ARCHITECTURE,
                                'extra': RefactoringIssueType.ARCHITECTURE,
                                'implementation': RefactoringIssueType.ARCHITECTURE
                            }
                            
                            priority_map = {
                                'critical': RefactoringPriority.CRITICAL,
                                'high': RefactoringPriority.HIGH,
                                'medium': RefactoringPriority.MEDIUM,
                                'low': RefactoringPriority.LOW
                            }
                            
                            # ENHANCED: Add analysis_data for architecture violations
                            violation_type = violation['type']
                            violation_file = violation['file']
                            violation_desc = violation['description']
                            violation_severity = violation.get('severity', 'medium')
                            
                            task = manager.create_task(
                                issue_type=issue_type_map.get(violation_type, RefactoringIssueType.ARCHITECTURE),
                                title=f"Fix architecture violation: {violation_type}",
                                description=f"Architecture violation in {violation_file}: {violation_desc}",
                                target_files=[violation_file],
                                priority=priority_map.get(violation_severity, RefactoringPriority.MEDIUM),
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=30,
                                analysis_data={
                                    'type': 'architecture_violation',
                                    'violation_type': violation_type,
                                    'file': violation_file,
                                    'description': violation_desc,
                                    'severity': violation_severity,
                                    'suggestion': violation.get('suggestion', ''),
                                    'action': 'move_file or create_issue_report'
                                }
                            )
                            tasks_created += 1
                
                elif tool_name == 'find_integration_gaps':
                    result_data = tool_result.get('result', {})
                    
                    # CRITICAL FIX: Handler returns 'unused_classes' and 'classes_with_unused_methods', not 'gaps'
                    unused_classes = result_data.get('unused_classes', [])
                    classes_with_gaps = result_data.get('classes_with_unused_methods', {})
                    
                    if unused_classes:
                        self.logger.info(f"  🔍 Found {len(unused_classes)} unused classes, creating tasks...")
                        for unused_class in unused_classes[:10]:
                            # ENHANCED: Add analysis_data and better description
                            class_name = unused_class['name']
                            file_path = unused_class['file']
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.INTEGRATION,
                                title=f"Remove unused class: {class_name}",
                                description=f"Remove unused class {class_name} from {file_path} (never instantiated anywhere in project)",
                                target_files=[file_path],
                                priority=RefactoringPriority.MEDIUM,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=30,
                                analysis_data={
                                    'type': 'unused_class',
                                    'class': class_name,
                                    'file': file_path,
                                    'reason': 'never instantiated',
                                    'action': 'cleanup_redundant_files'
                                }
                            )
                            tasks_created += 1
                    
                    if classes_with_gaps:
                        self.logger.info(f"  🔍 Found {len(classes_with_gaps)} classes with unused methods, creating tasks...")
                        for class_name, methods in list(classes_with_gaps.items())[:10]:
                            # ENHANCED: Add analysis_data and better description
                            methods_list = methods[:3]
                            methods_str = ', '.join(methods_list)
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.INTEGRATION,
                                title=f"Remove unused methods in {class_name}",
                                description=f"Class {class_name} has {len(methods)} unused methods: {methods_str}",
                                target_files=[],  # File info not available in this structure
                                priority=RefactoringPriority.LOW,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=20,
                                analysis_data={
                                    'type': 'unused_methods',
                                    'class': class_name,
                                    'methods': methods,
                                    'count': len(methods),
                                    'action': 'create_issue_report'  # Methods require careful review
                                }
                            )
                            tasks_created += 1
                
                elif tool_name == 'detect_integration_conflicts':
                    result_data = tool_result.get('result', {})
                    conflicts = result_data.get('conflicts', [])
                    if conflicts:
                        self.logger.info(f"  🔍 Found {len(conflicts)} integration conflicts, creating tasks...")
                        from dataclasses import asdict
                        for conflict in conflicts[:10]:
                            # CRITICAL FIX: IntegrationConflict is a dataclass, need to convert to dict
                            conflict_dict = asdict(conflict) if hasattr(conflict, '__dataclass_fields__') else conflict
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.CONFLICT,
                                title=f"Integration conflict",
                                description=f"Integration conflict: {conflict_dict['description']}",
                                target_files=conflict_dict['files'],
                                priority=RefactoringPriority.CRITICAL,
                                fix_approach=RefactoringApproach.AUTONOMOUS,  # Let AI analyze and decide
                                estimated_effort=60,
                                analysis_data=conflict_dict,
                            )
                            tasks_created += 1
                
                elif tool_name == 'find_bugs':
                    result_data = tool_result.get('result', {})
                    bugs = result_data.get('bugs', [])
                    if bugs:
                        self.logger.info(f"  🔍 Found {len(bugs)} potential bugs, creating tasks...")
                        priority_map = {'critical': RefactoringPriority.CRITICAL, 'high': RefactoringPriority.HIGH, 'medium': RefactoringPriority.MEDIUM, 'low': RefactoringPriority.LOW}
                        for bug in bugs[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Bug: {bug.get('type', 'Unknown')}",
                                description=f"{bug.get('message', 'Unknown')} at line {bug.get('line', '?')} in {bug.get('file', '?')}. Suggestion: {bug.get('suggestion', 'Fix the issue')}",
                                target_files=[bug.get('file', '')],
                                priority=priority_map.get(bug.get('severity', 'medium'), RefactoringPriority.HIGH),
                                fix_approach=RefactoringApproach.AUTONOMOUS,  # Let AI analyze and decide
                                estimated_effort=45,
                                analysis_data=bug,
                            )
                            tasks_created += 1
                
                elif tool_name == 'detect_antipatterns':
                    result_data = tool_result.get('result', {})
                    antipatterns = result_data.get('antipatterns', [])
                    if antipatterns:
                        self.logger.info(f"  🔍 Found {len(antipatterns)} anti-patterns, creating tasks...")
                        for pattern in antipatterns[:10]:
                            # ENHANCED: Add analysis_data for anti-patterns
                            pattern_name = pattern.get('name', 'Unknown')
                            pattern_file = pattern.get('file', '')
                            pattern_desc = pattern.get('description', '')
                            pattern_severity = pattern.get('severity', 'medium')
                            pattern_suggestion = pattern.get('suggestion', '')
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Fix anti-pattern: {pattern_name}",
                                description=f"Anti-pattern '{pattern_name}' detected in {pattern_file}: {pattern_desc}",
                                target_files=[pattern_file],
                                priority=RefactoringPriority.MEDIUM,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=30,
                                analysis_data={
                                    'type': 'antipattern',
                                    'pattern_name': pattern_name,
                                    'file': pattern_file,
                                    'description': pattern_desc,
                                    'severity': pattern_severity,
                                    'suggestion': pattern_suggestion,
                                    'action': 'create_issue_report'
                                }
                            )
                            tasks_created += 1
                
                elif tool_name == 'validate_function_calls':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} function call errors, creating tasks...")
                        priority_map = {
                            'missing_required': RefactoringPriority.CRITICAL,
                            'unexpected_kwarg': RefactoringPriority.CRITICAL,
                            'wrong_param_name': RefactoringPriority.HIGH
                        }
                        for error in errors[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Function call error: {error.get('error_type', 'unknown')}",
                                description=f"{error.get('function', 'unknown')}: {error.get('message', 'Unknown')}",
                                target_files=[error.get('file', '')],
                                priority=priority_map.get(error.get('error_type'), RefactoringPriority.HIGH),
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=25,
                                analysis_data=error,
                            )
                            tasks_created += 1
                
                elif tool_name == 'validate_method_existence':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} method existence errors, creating tasks...")
                        for error in errors[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Missing method: {error.get('class_name', 'unknown')}.{error.get('method_name', 'unknown')}",
                                description=error.get('message', 'Unknown'),
                                target_files=[error.get('file', '')],
                                priority=RefactoringPriority.CRITICAL,
                                fix_approach=RefactoringApproach.AUTONOMOUS,  # Let AI analyze and decide
                                estimated_effort=30,
                                analysis_data=error,
                            )
                            tasks_created += 1
                
                elif tool_name == 'validate_dict_structure':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} dictionary structure errors, creating tasks...")
                        for error in errors[:15]:
                            # Validate error data before creating task
                            key_path = error.get('key_path', '')
                            file_path = error.get('file', '')
                            
                            # Skip if key_path is invalid (just a number, empty, or 'unknown')
                            if not key_path or key_path.isdigit() or key_path == 'unknown':
                                self.logger.debug(f"  ⚠️  Skipping dict error with invalid key_path: {key_path}")
                                continue
                            
                            # Skip if file path is invalid
                            if not file_path or file_path == 'unknown':
                                self.logger.debug(f"  ⚠️  Skipping dict error with invalid file: {file_path}")
                                continue
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Dictionary key error: {key_path}",
                                description=error.get('message', 'Unknown'),
                                target_files=[file_path],
                                priority=RefactoringPriority.HIGH,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=20,
                                analysis_data=error,
                            )
                            if task:  # Only count if task was created
                                tasks_created += 1
                
                elif tool_name == 'validate_type_usage':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} type usage errors, creating tasks...")
                        for error in errors[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Type usage error: {error.get('attempted_operation', 'unknown')}",
                                description=error.get('message', 'Unknown'),
                                target_files=[error.get('file', '')],
                                priority=RefactoringPriority.CRITICAL,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=25,
                                analysis_data=error,
                            )
                            tasks_created += 1
                
                elif tool_name == 'validate_all_imports':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} import errors, creating tasks...")
                        for error in errors[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Import error in {error.get('file', 'unknown')}",
                                description=f"Import error: {error.get('error', 'Unknown')}",
                                target_files=[error.get('file', '')],
                                priority=RefactoringPriority.HIGH,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=20,
                                analysis_data=error,
                            )
                            tasks_created += 1
                
                elif tool_name == 'validate_syntax':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} syntax errors, creating tasks...")
                        for error in errors[:15]:
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Syntax error in {error.get('file', 'unknown')}",
                                description=f"Syntax error: {error.get('message', 'Unknown')}",
                                target_files=[error.get('file', '')],
                                priority=RefactoringPriority.CRITICAL,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=15,
                                analysis_data=error,
                            )
                            tasks_created += 1
                
                elif tool_name == 'detect_circular_imports':
                    result_data = tool_result.get('result', {})
                    cycles = result_data.get('cycles', [])
                    if cycles:
                        self.logger.info(f"  🔍 Found {len(cycles)} circular import cycles, creating tasks...")
                        for cycle in cycles[:10]:
                            # ENHANCED: Add analysis_data for circular imports
                            cycle_path = cycle.get('cycle', [])
                            cycle_files = cycle.get('files', [])
                            cycle_desc = f"Circular import: {' → '.join(cycle_path)}"
                            
                            task = manager.create_task(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                title=f"Fix circular import: {len(cycle_path)} files",
                                description=cycle_desc,
                                target_files=cycle_files,
                                priority=RefactoringPriority.HIGH,
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort=45,
                                analysis_data={
                                    'type': 'circular_import',
                                    'cycle': cycle_path,
                                    'files': cycle_files,
                                    'description': cycle_desc,
                                    'action': 'move_file or restructure_directory'
                                }
                            )
                            tasks_created += 1
        
        return tasks_created
    
    def _check_completion(self, state: PipelineState) -> PhaseResult:
        """
        Check if refactoring is complete.
        
        Re-analyzes codebase to see if new issues emerged.
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
        
        # Re-analyze to find new issues
        self.logger.info(f"  🔍 Re-analyzing codebase for new issues...")
        
        # Run analysis again
        return self._analyze_and_create_tasks(state)
    
    def _generate_refactoring_report(self, state: PipelineState) -> None:
        """
        Generate comprehensive REFACTORING_REPORT.md.
        
        Includes all tasks, issues, and recommendations.
        """
        if not state.refactoring_manager:
            return
        
        from pipeline.state.refactoring_task import RefactoringPriority, TaskStatus
        
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