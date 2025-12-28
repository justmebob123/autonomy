"""
QA Phase

Reviews code for quality issues.
"""

from datetime import datetime
from typing import Dict, List, Tuple

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus, FileStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_qa_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


class QAPhase(BasePhase, LoopDetectionMixin):
    """
    QA phase that reviews generated code.
    
    Responsibilities:
    - Review files pending QA
    - Check for issues
    - Update task priorities based on results
    - Write QA_STATE.md
    """
    
    phase_name = "qa"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_COMPLETED,
                MessageType.FILE_CREATED,
                MessageType.FILE_MODIFIED,
                MessageType.SYSTEM_ALERT,
            ])
    
    def execute(self, state: PipelineState,
                filepath: str = None, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute QA review for a file or task"""
        
        # MESSAGE BUS: Check for relevant messages
        if self.message_bus:
            from ..messaging import MessageType
            messages = self._get_messages(
                message_types=[MessageType.TASK_COMPLETED, MessageType.FILE_MODIFIED],
                limit=5
            )
            if messages:
                self.logger.info(f"  📨 Received {len(messages)} messages")
                for msg in messages:
                    self.logger.info(f"    • {msg.message_type.value}: {msg.payload.get('file', msg.payload.get('task_id', 'N/A'))}")
                # Clear processed messages
                self._clear_messages([msg.id for msg in messages])
        
        # Check no-update count BEFORE processing (loop prevention)
        from ..state.manager import StateManager
        state_manager = StateManager(self.project_dir)
        no_update_count = state_manager.get_no_update_count(state, self.phase_name)
        
        if no_update_count >= 3:
            self.logger.warning(f"  ⚠️ QA phase returned 'no files to review' {no_update_count} times")
            self.logger.info("  🔄 Forcing transition to next phase to prevent loop")
            
            # Reset counter
            state_manager.reset_no_update_count(state, self.phase_name)
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="QA reviewed multiple times - forcing completion to prevent loop",
                next_phase="coding"
            )
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is not None:
                task = task_from_state
            # If not found, keep the original (might be a standalone review)
        
        # Determine what to review
        if filepath is None and task is not None:
            filepath = task.target_file
            
            # Skip tasks with empty target_file
            if not filepath or filepath.strip() == "":
                self.logger.warning(f"  ⚠️ Task {task.task_id} has empty target_file, marking as SKIPPED")
                task.status = TaskStatus.SKIPPED
                state_manager.save(state)
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Skipped task with empty target_file"
                )
        elif filepath is None:
            # Find files needing review
            files = state.get_files_needing_qa()
            if not files:
                # Increment no-update counter
                count = state_manager.increment_no_update_count(state, self.phase_name)
                self.logger.info(f"  No files need QA review (count: {count}/3)")
                
                # After 2 "no files", suggest moving on
                if count >= 2:
                    message = "No files need QA review. Ready to move to next phase."
                    next_phase = "coding"
                else:
                    message = "No files need QA review"
                    next_phase = None
                
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=message,
                    next_phase=next_phase
                )
            filepath = files[0]
            
            # If we got a file to review, reset counter (making progress)
            state_manager.reset_no_update_count(state, self.phase_name)
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  Reviewing: {filepath}")
        
        # Check if it's a directory - skip directories
        full_path = self.project_dir / filepath
        if full_path.is_dir():
            self.logger.warning(f"  ⚠️ Skipping directory: {filepath}")
            # Mark task as completed if provided
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                self.state_manager.save(state)
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Skipped directory: {filepath}",
                next_phase="coding"
            )
        
        # Read file content
        content = self.read_file(filepath)
        if not content:
            # File not found - mark task as complete and move to next task
            self.logger.warning(f"⚠️ File not found, marking task as complete: {filepath}")
            return PhaseResult(
                success=True,  # Mark as success to avoid infinite loop
                phase=self.phase_name,
                message=f"File not found (task marked complete): {filepath}",
                next_phase="coding",  # Move to coding to continue with other tasks
                data={"skipped": True, "reason": "file_not_found"}
            )
        
        # Build simple review message
        user_message = f"Please review this code for quality issues:\n\nFile: {filepath}\n\n```\n{content}\n```\n\nIf you find issues, use the report_qa_issue tool to report them.\nIf the code looks good, just say &quot;APPROVED&quot; (no tool calls needed)."
        
        # Get tools for QA phase
        tools = get_tools_for_phase("qa")
        
        # Call model with conversation history
        self.logger.info(f"  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        text_content = response.get("content", "")
        
        # Debug logging: Show what we got from the model
        self.logger.debug(f"QA Response Analysis:")
        self.logger.debug(f"  - Tool calls found: {len(tool_calls)}")
        self.logger.debug(f"  - Text content length: {len(text_content)}")
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                func = tc.get("function", {})
                self.logger.debug(f"  - Tool[{i}]: name='{func.get('name', '')}', args={list(func.get('arguments', {}).keys())}")
        if text_content and not tool_calls:
            self.logger.debug(f"  - Text content preview: {text_content[:500]}")
        
        if not tool_calls:
            # No tool calls = implicit approval
            self.logger.info("  No issues reported (implicit approval)")
            state.mark_file_reviewed(filepath, approved=True)
            
            # Update task status if applicable
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed = datetime.now().isoformat()
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="File approved (no issues found)"
            )
        
        # Process tool calls
        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
        activity_log = self.project_dir / 'ai_activity.log'
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self.track_tool_calls(tool_calls, results, agent="qa")
        
        # Check for loops
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
        
        # Check results
        if handler.approved:
            self.logger.info(f"  ✓ Approved: {filepath}")
            state.mark_file_reviewed(filepath, approved=True)
            
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed = datetime.now().isoformat()
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"File approved: {filepath}"
            )
        
        if handler.issues:
            self.logger.warning(f"  ⚠ Found {len(handler.issues)} issues")
            
            # Record issues
            state.mark_file_reviewed(filepath, approved=False, issues=handler.issues)
            
            # Create Issue objects in IssueTracker (NEW)
            if hasattr(self, 'coordinator') and hasattr(self.coordinator, 'issue_tracker'):
                from ..issue_tracker import Issue, IssueType, IssueSeverity
                
                for issue_data in handler.issues:
                    # Determine issue type
                    issue_type_str = issue_data.get("type", "other")
                    try:
                        issue_type = IssueType(issue_type_str)
                    except ValueError:
                        issue_type = IssueType.OTHER
                    
                    # Determine severity
                    severity_map = {
                        "syntax_error": IssueSeverity.CRITICAL,
                        "import_error": IssueSeverity.CRITICAL,
                        "incomplete": IssueSeverity.HIGH,
                        "logic_error": IssueSeverity.HIGH,
                        "type_error": IssueSeverity.MEDIUM,
                        "style_violation": IssueSeverity.LOW
                    }
                    severity = severity_map.get(issue_type_str, IssueSeverity.MEDIUM)
                    
                    # Create Issue object
                    issue = Issue(
                        id="",  # Will be generated
                        issue_type=issue_type,
                        severity=severity,
                        file=filepath,
                        line_number=issue_data.get("line"),
                        title=issue_data.get("type", "QA Issue"),
                        description=issue_data.get("description", ""),
                        related_task=task.task_id if task else None,
                        related_objective=task.objective_id if task else None,
                        reported_by="qa"
                    )
                    
                    # Add to tracker
                    issue_id = self.coordinator.issue_tracker.create_issue(issue, state)
                    
                    # MESSAGE BUS: Publish ISSUE_FOUND event
                    from ..messaging import MessageType, MessagePriority
                    msg_priority = MessagePriority.CRITICAL if severity == IssueSeverity.CRITICAL else MessagePriority.HIGH
                    self._publish_message(
                        message_type=MessageType.ISSUE_FOUND,
                        payload={
                            'issue_id': issue_id,
                            'issue_type': issue_type,
                            'severity': severity.value if hasattr(severity, 'value') else str(severity),
                            'file': file_path,
                            'description': description
                        },
                        recipient="broadcast",
                        priority=msg_priority,
                        issue_id=issue_id,
                        task_id=task.task_id if task else None,
                        objective_id=task.objective_id if task else None,
                        file_path=file_path
                    )
                    
                    # Link to objective if present
                    if task and task.objective_id and task.objective_level:
                        obj_level = task.objective_level
                        obj_id = task.objective_id
                        if obj_level in state.objectives and obj_id in state.objectives[obj_level]:
                            obj_data = state.objectives[obj_level][obj_id]
                            if 'open_issues' not in obj_data:
                                obj_data['open_issues'] = []
                            if issue_id not in obj_data['open_issues']:
                                obj_data['open_issues'].append(issue_id)
                            
                            if severity == IssueSeverity.CRITICAL:
                                if 'critical_issues' not in obj_data:
                                    obj_data['critical_issues'] = []
                                if issue_id not in obj_data['critical_issues']:
                                    obj_data['critical_issues'].append(issue_id)
            
            # Update task priority - CRITICAL FIX: Use NEEDS_FIXES to trigger debugging
            if task:
                task.status = TaskStatus.NEEDS_FIXES  # Changed from QA_FAILED
                task.priority = TaskPriority.QA_FAILURE  # Keep same priority
                
                # Add errors to task
                for issue in handler.issues:
                    task.add_error(
                        issue.get("type", "qa_issue"),
                        issue.get("description", "Unknown issue"),
                        line_number=issue.get("line"),
                        phase="qa"
                    )
            
            # Rebuild queue with new priorities
            state.rebuild_queue()
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Found {len(handler.issues)} issues",
                errors=handler.issues,
                data={"issues": handler.issues, "filepath": filepath}
            )
        
        # No explicit approval or issues - this is ambiguous
        # Check if tool calls were actually processed
        successful_tools = sum(1 for r in results if r.get('success', False))
        
        if successful_tools == 0 and len(tool_calls) > 0:
            # Tool calls were made but none succeeded - this is a failure
            self.logger.warning(f"  ⚠️  {len(tool_calls)} tool calls made but none succeeded")
            
            # If this task has failed multiple times, mark it as SKIPPED to prevent infinite loops
            if task:
                task.attempts += 1
                if task.attempts >= 3:
                    self.logger.warning(f"  ⚠️  Task {task.task_id} has failed QA {task.attempts} times, marking as SKIPPED")
                    task.status = TaskStatus.SKIPPED
                    from ..state.manager import StateManager
                    state_manager = StateManager(self.project_dir)
                    state_manager.save(state)
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"QA failed: {len(tool_calls)} tool calls failed",
                errors=[{"type": "tool_failure", "message": "All tool calls failed"}]
            )
        
        # If we got here with successful tool calls but no explicit approval/issues,
        # treat as implicit approval (AI reviewed but didn't find issues)
        self.logger.info("  ✓ Review completed (implicit approval)")
        state.mark_file_reviewed(filepath, approved=True)
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed = datetime.now().isoformat()
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Review completed (implicit approval)"
        )
    
    def review_multiple(self, state: PipelineState, 
                        filepaths: List[str] = None) -> PhaseResult:
        """Review multiple files"""
        if filepaths is None:
            filepaths = state.get_files_needing_qa()
        
        results = []
        all_issues = []
        
        for filepath in filepaths:
            result = self.execute(state, filepath=filepath)
            results.append(result)
            all_issues.extend(result.errors)
        
        approved = sum(1 for r in results if r.success)
        rejected = len(results) - approved
        
        return PhaseResult(
            success=rejected == 0,
            phase=self.phase_name,
            message=f"Reviewed {len(results)} files: {approved} approved, {rejected} rejected",
            errors=all_issues,
            data={"reviewed": len(results), "approved": approved, "rejected": rejected}
        )
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate QA_STATE.md content"""
        lines = [
            "# QA State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Review Summary",
            "",
        ]
        
        # Count by status
        status_counts = {
            "PENDING": 0,
            "APPROVED": 0,
            "REJECTED": 0,
        }
        
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.APPROVED:
                status_counts["APPROVED"] += 1
            elif file_state.qa_status == FileStatus.REJECTED:
                status_counts["REJECTED"] += 1
            else:
                status_counts["PENDING"] += 1
        
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        for status, count in status_counts.items():
            lines.append(f"| {status} | {count} |")
        lines.append("")
        
        # Pending reviews
        pending = [f for f in state.files.values() 
                   if f.qa_status in [FileStatus.UNKNOWN, FileStatus.PENDING]]
        if pending:
            lines.append("## Pending Reviews")
            lines.append("")
            lines.append("| File | Last Modified | Size |")
            lines.append("|------|---------------|------|")
            for f in pending:
                modified = self.format_timestamp(f.last_modified)
                lines.append(f"| `{f.filepath}` | {modified} | {f.size} bytes |")
            lines.append("")
        
        # Recent approvals
        approved = [f for f in state.files.values() 
                    if f.qa_status == FileStatus.APPROVED]
        if approved:
            lines.append("## Approved Files")
            lines.append("")
            for f in sorted(approved, key=lambda x: x.last_qa or "", reverse=True)[:10]:
                qa_time = self.format_timestamp(f.last_qa) if f.last_qa else "?"
                lines.append(f"- ✓ `{f.filepath}` - {qa_time}")
            lines.append("")
        
        # Rejected files with issues
        rejected = [f for f in state.files.values() 
                    if f.qa_status == FileStatus.REJECTED]
        if rejected:
            lines.append("## Rejected Files")
            lines.append("")
            for f in rejected:
                lines.append(f"### `{f.filepath}`")
                lines.append("")
                if f.issues:
                    for issue in f.issues:
                        lines.append(f"- **[{issue.get('type', 'unknown')}]** {issue.get('description', '')}")
                        if issue.get('line'):
                            lines.append(f"  - Line: {issue['line']}")
                        if issue.get('fix'):
                            lines.append(f"  - Suggested fix: {issue['fix']}")
                lines.append("")
        
        # Session stats
        lines.append("## Session Stats")
        lines.append("")
        lines.append(f"- Total Runs: {state.phases['qa'].runs}")
        lines.append(f"- Successful Reviews: {state.phases['qa'].successes}")
        lines.append(f"- Failed Reviews: {state.phases['qa'].failures}")
        lines.append("")
        
        return "\n".join(lines)
