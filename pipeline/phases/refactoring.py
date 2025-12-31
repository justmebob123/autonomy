"""
Refactoring Phase

Analyzes and refactors code architecture to eliminate duplicates, resolve conflicts,
and improve code organization based on MASTER_PLAN.md changes.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_refactoring_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


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
            ArchitectureAnalyzer
        )
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_conflicts import IntegrationConflictDetector
        
        self.duplicate_detector = DuplicateDetector(str(self.project_dir), self.logger)
        self.file_comparator = FileComparator(str(self.project_dir), self.logger)
        self.feature_extractor = FeatureExtractor(str(self.project_dir), self.logger)
        self.architecture_analyzer = ArchitectureAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.conflict_detector = IntegrationConflictDetector(str(self.project_dir), self.logger)
        
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
        
        # Check if any tasks were created (either by LLM or auto-created)
        pending = self._get_pending_refactoring_tasks(state)
        
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
        
        # Check fix approach
        if task.fix_approach == RefactoringApproach.DEVELOPER_REVIEW:
            # Task needs developer review, skip for now
            self.logger.info(f"  ⚠️  Task requires developer review, skipping")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Task {task.task_id} requires developer review"
            )
        
        if task.fix_approach == RefactoringApproach.NEEDS_NEW_CODE:
            # Task needs new code, route to coding
            self.logger.info(f"  ⚠️  Task requires new code implementation")
            task.needs_review("Requires new code implementation")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Task {task.task_id} requires new code",
                next_phase="coding"
            )
        
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
        
        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Check if any tools succeeded
        any_success = any(r.get("success") for r in results)
        
        if any_success:
            # Task succeeded
            task.complete(content)
            self.logger.info(f"  ✅ Task {task.task_id} completed successfully")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Task {task.task_id} completed"
            )
        else:
            # All tools failed
            errors = [r.get("error", "Unknown") for r in results if not r.get("success")]
            error_msg = "; ".join(errors)
            
            # Check if task is too complex
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
                handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
                
                report_call = [{
                    "name": "create_issue_report",
                    "arguments": {
                        "task_id": task.task_id,
                        "severity": task.priority.value,
                        "impact_analysis": f"Task failed {task.attempts} times. Errors: {error_msg}",
                        "recommended_approach": "Manual review and fixing required",
                        "estimated_effort": "Unknown - requires developer assessment"
                    }
                }]
                
                handler.process_tool_calls(report_call)
            
            return result
    
    def _build_task_context(self, task: Any) -> str:
        """Build context for a specific task"""
        context_parts = []
        
        context_parts.append(f"# Task: {task.title}\n")
        context_parts.append(f"**Type**: {task.issue_type.value}\n")
        context_parts.append(f"**Priority**: {task.priority.value}\n")
        context_parts.append(f"**Description**: {task.description}\n\n")
        
        context_parts.append(f"## Affected Files\n")
        for file in task.target_files:
            context_parts.append(f"- {file}\n")
        
        if task.analysis_data:
            context_parts.append(f"\n## Analysis Data\n")
            for key, value in task.analysis_data.items():
                context_parts.append(f"**{key}**: {value}\n")
        
        return "".join(context_parts)
    
    def _build_task_prompt(self, task: Any, context: str) -> str:
        """Build prompt for working on a specific task"""
        return f"""You are working on a specific refactoring task.

{context}

Your goal is to FIX this issue using the available tools.

Steps:
1. Review the task description and affected files
2. Use appropriate tools to fix the issue
3. Verify the fix is correct
4. Update the task status

Available approaches:
- For duplicates: Use merge_file_implementations or cleanup_redundant_files
- For complexity: Refactor code to simplify
- For dead code: Use cleanup_redundant_files
- For architecture: Align with MASTER_PLAN

IMPORTANT: After fixing, use update_refactoring_task to mark the task as completed.

Use the refactoring tools NOW to fix this issue."""
    
    def _auto_create_tasks_from_analysis(self, state: PipelineState, analysis_result: PhaseResult) -> int:
        """
        Auto-create refactoring tasks from analysis results.
        
        When the LLM detects issues but doesn't create tasks, we auto-create them.
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
                            # Create task for this duplicate
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.DUPLICATE,
                                priority=RefactoringPriority.MEDIUM,
                                description=f"Duplicate code: {dup.get('similarity', 0):.0%} similar",
                                affected_files=dup.get('files', []),
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=30
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                # Handle complexity analysis results
                elif tool_name == 'analyze_complexity':
                    # CRITICAL FIX: Handler returns nested structure
                    result_data = tool_result.get('result', {})
                    critical_functions = result_data.get('critical_functions', [])
                    
                    if critical_functions:
                        self.logger.info(f"  🔍 Found {len(critical_functions)} critical complexity issues, creating tasks...")
                        
                        for func_info in critical_functions[:5]:  # Limit to top 5
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.COMPLEXITY,
                                priority=RefactoringPriority.HIGH,
                                description=f"High complexity: {func_info.get('name', 'unknown')} (complexity: {func_info.get('complexity', 0)})",
                                affected_files=[func_info.get('file', '')],
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW,
                                estimated_effort_minutes=60
                            )
                            manager.add_task(task)
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
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.DEAD_CODE,
                                priority=RefactoringPriority.LOW,
                                description=f"Dead code: {item.get('name', 'unknown')}",
                                affected_files=[item.get('file', '')],
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=15
                            )
                            manager.add_task(task)
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
                            
                            task = RefactoringTask(
                                issue_type=issue_type_map.get(violation['type'], RefactoringIssueType.ARCHITECTURE),
                                priority=priority_map.get(violation['severity'], RefactoringPriority.MEDIUM),
                                description=violation['description'],
                                affected_files=[violation['file']],
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW if violation['severity'] in ['critical', 'high'] else RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=30
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'find_integration_gaps':
                    result_data = tool_result.get('result', {})
                    gaps = result_data.get('gaps', [])
                    if gaps:
                        self.logger.info(f"  🔍 Found {len(gaps)} integration gaps, creating tasks...")
                        for gap in gaps[:10]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.INTEGRATION,
                                priority=RefactoringPriority.HIGH,
                                description=f"Integration gap: {gap.get('description', 'Unknown')}",
                                affected_files=gap.get('files', []),
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW,
                                estimated_effort_minutes=45
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'detect_integration_conflicts':
                    result_data = tool_result.get('result', {})
                    conflicts = result_data.get('conflicts', [])
                    if conflicts:
                        self.logger.info(f"  🔍 Found {len(conflicts)} integration conflicts, creating tasks...")
                        for conflict in conflicts[:10]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.CONFLICT,
                                priority=RefactoringPriority.CRITICAL,
                                description=f"Integration conflict: {conflict.get('description', 'Unknown')}",
                                affected_files=conflict.get('files', []),
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW,
                                estimated_effort_minutes=60
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'find_bugs':
                    result_data = tool_result.get('result', {})
                    bugs = result_data.get('bugs', [])
                    if bugs:
                        self.logger.info(f"  🔍 Found {len(bugs)} potential bugs, creating tasks...")
                        priority_map = {'critical': RefactoringPriority.CRITICAL, 'high': RefactoringPriority.HIGH, 'medium': RefactoringPriority.MEDIUM, 'low': RefactoringPriority.LOW}
                        for bug in bugs[:15]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                priority=priority_map.get(bug.get('severity', 'medium'), RefactoringPriority.HIGH),
                                description=f"Bug: {bug.get('description', 'Unknown')}",
                                affected_files=[bug.get('file', '')],
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW,
                                estimated_effort_minutes=45
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'detect_antipatterns':
                    result_data = tool_result.get('result', {})
                    antipatterns = result_data.get('antipatterns', [])
                    if antipatterns:
                        self.logger.info(f"  🔍 Found {len(antipatterns)} anti-patterns, creating tasks...")
                        for pattern in antipatterns[:10]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                priority=RefactoringPriority.MEDIUM,
                                description=f"Anti-pattern: {pattern.get('name', 'Unknown')}",
                                affected_files=[pattern.get('file', '')],
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=30
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'validate_all_imports':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} import errors, creating tasks...")
                        for error in errors[:15]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                priority=RefactoringPriority.HIGH,
                                description=f"Import error: {error.get('error', 'Unknown')}",
                                affected_files=[error.get('file', '')],
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=20
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'validate_syntax':
                    result_data = tool_result.get('result', {})
                    errors = result_data.get('errors', [])
                    if errors:
                        self.logger.info(f"  🔍 Found {len(errors)} syntax errors, creating tasks...")
                        for error in errors[:15]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                priority=RefactoringPriority.CRITICAL,
                                description=f"Syntax error: {error.get('message', 'Unknown')}",
                                affected_files=[error.get('file', '')],
                                fix_approach=RefactoringApproach.AUTONOMOUS,
                                estimated_effort_minutes=15
                            )
                            manager.add_task(task)
                            tasks_created += 1
                
                elif tool_name == 'detect_circular_imports':
                    result_data = tool_result.get('result', {})
                    cycles = result_data.get('cycles', [])
                    if cycles:
                        self.logger.info(f"  🔍 Found {len(cycles)} circular import cycles, creating tasks...")
                        for cycle in cycles[:10]:
                            task = RefactoringTask(
                                issue_type=RefactoringIssueType.ARCHITECTURE,
                                priority=RefactoringPriority.HIGH,
                                description=f"Circular import: {' → '.join(cycle.get('cycle', []))}",
                                affected_files=cycle.get('files', []),
                                fix_approach=RefactoringApproach.DEVELOPER_REVIEW,
                                estimated_effort_minutes=45
                            )
                            manager.add_task(task)
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
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
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
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
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
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
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
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
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
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
        
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
            
            conflict_result = {
                'tool': 'detect_integration_conflicts',
                'success': True,
                'result': {
                    'conflicts': [c.to_dict() for c in conflict_analysis.conflicts],
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
        
        # 6.1: Import Validation
        try:
            import_result = handler._handle_validate_all_imports({})
            all_results.append(import_result)
            
            if import_result.get('success'):
                invalid_count = import_result.get('count', 0)
                self.logger.info(f"     ✓ Import validation: {invalid_count} invalid imports found")
        except Exception as e:
            self.logger.warning(f"     ⚠️  Import validation failed: {e}")
        
        # 6.2: Syntax Validation (using complexity analyzer which already checks syntax)
        # Syntax errors already detected in Phase 2 complexity analysis
        self.logger.info(f"     ✓ Syntax validation: Checked in Phase 2 (complexity analysis)")
        
        # 6.3: Circular Import Detection
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
3. Focus on tools that don't require complex imports
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