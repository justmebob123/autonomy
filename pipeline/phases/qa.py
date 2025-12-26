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
    
    def execute(self, state: PipelineState,
                filepath: str = None, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute QA review for a file or task"""
        
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
        
        # Read file content
        content = self.read_file(filepath)
        if not content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"File not found: {filepath}",
                errors=[{"type": "file_not_found", "filepath": filepath}]
            )
        
        # Build messages
        messages = [
            {"role": "system", "content": self._get_system_prompt("qa")},
            {"role": "user", "content": get_qa_prompt(filepath, content)}
        ]
        
        # Get tools
        tools = get_tools_for_phase("qa")
        
        # Send request
        response = self.chat(messages, tools, task_type="qa")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"QA failed: {response['error']}",
                errors=[{"type": "api_error", "message": response["error"]}]
            )
        
        # Parse response
        tool_calls, text_content = self.parser.parse_response(response)
        
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
            
            # Update task priority
            if task:
                task.status = TaskStatus.QA_FAILED
                task.priority = TaskPriority.QA_FAILURE
                
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
        
        # No explicit approval or issues - treat as pass
        state.mark_file_reviewed(filepath, approved=True)
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed = datetime.now().isoformat()
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Review completed"
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
