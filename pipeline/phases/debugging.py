"""
Debugging Phase

Fixes code issues identified by QA.
"""

from datetime import datetime
from typing import Dict, List, Optional

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus, FileStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_debug_prompt
from ..handlers import ToolCallHandler
from ..utils import validate_python_syntax


class DebuggingPhase(BasePhase):
    """
    Debugging phase that fixes code issues.
    
    Responsibilities:
    - Get issues from QA
    - Apply fixes
    - Validate fixes
    - Update DEBUG_STATE.md
    """
    
    phase_name = "debug"
    
    def execute(self, state: PipelineState,
                issue: Dict = None,
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute debugging for an issue"""
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is not None:
                task = task_from_state
            # If not found, keep the original (might be standalone debugging)
        
        # Find issue to fix
        if issue is None:
            issue = self._get_next_issue(state)
        
        if issue is None:
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No issues to fix"
            )
        
        filepath = issue.get("filepath")
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Issue has no filepath"
            )
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  Fixing: {filepath}")
        self.logger.info(f"  Issue: [{issue.get('type')}] {issue.get('description', '')[:50]}")
        
        # Read current content
        content = self.read_file(filepath)
        if not content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"File not found: {filepath}"
            )
        
        # Build messages
        user_prompt = get_debug_prompt(filepath, content, issue)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["debugging"]},
            {"role": "user", "content": user_prompt}
        ]
        
        # Log prompt in verbose mode
        if hasattr(self, 'config') and self.config.verbose:
            self.logger.info(f"  Prompt length: {len(user_prompt)} chars")
            self.logger.info(f"  Prompt preview: {user_prompt[:300]}...")
        
        # Get tools
        tools = get_tools_for_phase("debugging")
        self.logger.debug(f"  Available tools: {[t['function']['name'] for t in tools]}")
        
        # Send request
        response = self.chat(messages, tools, task_type="debugging")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Debug failed: {response['error']}"
            )
        
        # Parse response
        tool_calls, _ = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No fix applied")
            # Log the actual response for debugging
            if hasattr(self, 'config') and self.config.verbose:
                self.logger.info(f"  AI Response (no tool calls): {response.get('content', '')[:500]}")
            else:
                # Always log a snippet to help debug
                content = response.get('content', '')
                if content:
                    self.logger.warning(f"  AI responded but made no tool calls. Response starts with: {content[:200]}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No fix was applied - AI did not make any tool calls"
            )
        
        # Execute tool calls
        handler = ToolCallHandler(self.project_dir)
        results = handler.process_tool_calls(tool_calls)
        
        if not handler.files_modified:
            # Check for errors
            for result in results:
                if not result.get("success"):
                    error = result.get("error", "Unknown error")
                    self.logger.warning(f"  Fix failed: {error}")
                    
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Fix failed: {error}",
                        errors=[{"type": "fix_failed", "message": error}]
                    )
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No modifications made"
            )
        
        # Success - update state
        self.logger.info(f"  ✓ Fixed: {filepath}")
        
        # Update file hash
        for modified_file in handler.files_modified:
            file_hash = self.file_tracker.update_hash(modified_file)
            full_path = self.project_dir / modified_file
            if full_path.exists():
                state.update_file(modified_file, file_hash, full_path.stat().st_size)
        
        # Update task if provided
        if task:
            task.status = TaskStatus.DEBUG_PENDING
            task.priority = TaskPriority.DEBUG_PENDING
        
        # Mark file for re-review
        if filepath in state.files:
            state.files[filepath].qa_status = FileStatus.PENDING
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Fixed issue in {filepath}",
            files_modified=handler.files_modified,
            data={"issue": issue, "filepath": filepath}
        )
    
    def fix_all_issues(self, state: PipelineState, 
                       max_fixes: int = 10) -> PhaseResult:
        """Attempt to fix all pending issues"""
        fixed = 0
        failed = 0
        all_errors = []
        
        for _ in range(max_fixes):
            issue = self._get_next_issue(state)
            if not issue:
                break
            
            result = self.execute(state, issue=issue)
            
            if result.success:
                fixed += 1
            else:
                failed += 1
                all_errors.extend(result.errors)
        
        return PhaseResult(
            success=failed == 0,
            phase=self.phase_name,
            message=f"Fixed {fixed} issues, {failed} failed",
            errors=all_errors,
            data={"fixed": fixed, "failed": failed}
        )
    
    def _get_next_issue(self, state: PipelineState) -> Optional[Dict]:
        """Get the next issue to fix"""
        # Check rejected files
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.REJECTED and file_state.issues:
                return file_state.issues[0]
        
        # Check task errors
        for task in state.tasks.values():
            if task.status == TaskStatus.QA_FAILED and task.errors:
                last_error = task.errors[-1]
                return {
                    "filepath": task.target_file,
                    "type": last_error.error_type,
                    "description": last_error.message,
                    "line": last_error.line_number,
                }
        
        return None
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate DEBUG_STATE.md content"""
        lines = [
            "# Debug State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Active Issues",
            "",
        ]
        
        # Collect all issues
        issues = []
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.REJECTED:
                for issue in file_state.issues:
                    issues.append({
                        "filepath": file_state.filepath,
                        **issue
                    })
        
        if issues:
            lines.append("| File | Type | Description |")
            lines.append("|------|------|-------------|")
            for issue in issues:
                lines.append(
                    f"| `{issue['filepath']}` | {issue.get('type', '?')} | "
                    f"{issue.get('description', '')[:50]} |"
                )
            lines.append("")
        else:
            lines.append("(no active issues)")
            lines.append("")
        
        # Fix history from tasks
        lines.append("## Recent Fix Attempts")
        lines.append("")
        
        fix_history = []
        for task in state.tasks.values():
            for error in task.errors:
                if error.phase == "debug":
                    fix_history.append((task, error))
        
        if fix_history:
            # Sort by timestamp
            fix_history.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            for task, error in fix_history[:10]:
                lines.append(f"### {task.target_file}")
                lines.append(f"- **Issue:** {error.error_type}")
                lines.append(f"- **Time:** {self.format_timestamp(error.timestamp)}")
                lines.append(f"- **Message:** {error.message}")
                lines.append("")
        else:
            lines.append("(no fix attempts yet)")
            lines.append("")
        
        # Error patterns
        lines.append("## Error Patterns")
        lines.append("")
        
        patterns: Dict[str, int] = {}
        for task in state.tasks.values():
            for error in task.errors:
                patterns[error.error_type] = patterns.get(error.error_type, 0) + 1
        
        if patterns:
            lines.append("| Error Type | Count |")
            lines.append("|------------|-------|")
            for error_type, count in sorted(patterns.items(), key=lambda x: -x[1]):
                lines.append(f"| {error_type} | {count} |")
            lines.append("")
            
            # Recommendations
            lines.append("## Recommendations for Coding Phase")
            lines.append("")
            if patterns.get("SyntaxError", 0) > 2:
                lines.append("- ⚠ Multiple syntax errors detected. Ensure proper indentation.")
            if patterns.get("missing_import", 0) > 0:
                lines.append("- ⚠ Missing imports detected. Include all required imports at top of file.")
            if patterns.get("type_error", 0) > 0:
                lines.append("- ⚠ Type errors detected. Verify type hints match actual types.")
        else:
            lines.append("(no error patterns detected)")
        
        lines.append("")
        
        # Session stats
        lines.append("## Session Stats")
        lines.append("")
        lines.append(f"- Total Runs: {state.phases['debug'].runs}")
        lines.append(f"- Successful Fixes: {state.phases['debug'].successes}")
        lines.append(f"- Failed Fixes: {state.phases['debug'].failures}")
        lines.append("")
        
        return "\n".join(lines)
