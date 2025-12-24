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


class QAPhase(BasePhase):
    """
    QA phase that reviews generated code.
    
    Responsibilities:
    - Review files pending QA
    - Check for issues
    - Update task priorities based on results
    - Write QA_STATE.md
    """
    
    phase_name = "qa"
    
    def execute(self, state: PipelineState,
                filepath: str = None, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute QA review for a file or task"""
        
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
        elif filepath is None:
            # Find files needing review
            files = state.get_files_needing_qa()
            if not files:
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message="No files need QA review"
                )
            filepath = files[0]
        
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
            {"role": "system", "content": SYSTEM_PROMPTS["qa"]},
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
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
        handler.process_tool_calls(tool_calls)
        
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
