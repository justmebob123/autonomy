"""
Coding Phase

Implements code based on task descriptions.
"""

from datetime import datetime
from typing import Dict, List, Tuple

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_coding_prompt
from ..handlers import ToolCallHandler
from ..utils import validate_python_syntax


class CodingPhase(BasePhase):
    """
    Coding phase that implements tasks.
    
    Responsibilities:
    - Get next task from queue
    - Build context with error history
    - Generate code via LLM
    - Validate syntax
    - Write files
    - Update CODING_STATE.md
    """
    
    phase_name = "coding"
    
    def execute(self, state: PipelineState, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute the coding phase for a task"""
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is None:
                self.logger.error(f"Task {task.task_id} not found in loaded state")
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    task_id=task.task_id,
                    message=f"Task {task.task_id} not found in state"
                )
            task = task_from_state
        else:
            task = state.get_next_task()
        
        if task is None:
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No tasks to implement"
            )
        
        self.logger.info(f"  Task: {task.description[:60]}...")
        self.logger.info(f"  Target: {task.target_file}")
        self.logger.info(f"  Attempt: {task.attempts + 1}")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.attempts += 1
        
        # Build context
        context = self._build_context(state, task)
        error_context = task.get_error_context()
        
        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["coding"]},
            {"role": "user", "content": get_coding_prompt(
                task.description,
                task.target_file,
                context,
                error_context
            )}
        ]
        
        # Get tools
        tools = get_tools_for_phase("coding")
        
        # Send request
        response = self.chat(messages, tools, task_type="coding")
        
        if "error" in response:
            task.add_error("api_error", response["error"], phase="coding")
            task.status = TaskStatus.FAILED
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message=f"API error: {response['error']}",
                errors=[{"type": "api_error", "message": response["error"]}]
            )
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if not tool_calls:
            task.add_error("no_tool_call", "Model did not use tools", phase="coding")
            task.status = TaskStatus.FAILED
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message="No tool calls in response"
            )
        
        # Execute tool calls
        handler = ToolCallHandler(self.project_dir)
        results = handler.process_tool_calls(tool_calls)
        
        # Check results
        files_created = handler.files_created
        files_modified = handler.files_modified
        
        if not files_created and not files_modified:
            # Check for syntax errors in results
            for result in results:
                if not result.get("success") and "Syntax error" in result.get("error", ""):
                    error_msg = result["error"]
                    filepath = result.get("filepath", task.target_file)
                    
                    task.add_error(
                        "syntax_error",
                        error_msg,
                        phase="coding"
                    )
                    
                    # Add to error context for next attempt
                    self.error_context.add_syntax_error(
                        error_msg,
                        filepath=filepath,
                        task_id=task.task_id,
                        phase="coding"
                    )
                elif not result.get("success"):
                    # Record other errors too
                    task.add_error(
                        result.get("error_type", "tool_error"),
                        result.get("error", "Unknown error"),
                        phase="coding"
                    )
            
            task.status = TaskStatus.FAILED
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message="Failed to create/modify files",
                errors=[{"type": "file_error", "message": handler.get_error_summary()}]
            )
        
        # Success - update state
        task.status = TaskStatus.QA_PENDING
        
        # Update file tracking in state
        for filepath in files_created + files_modified:
            file_hash = self.file_tracker.update_hash(filepath)
            full_path = self.project_dir / filepath
            if full_path.exists():
                state.update_file(filepath, file_hash, full_path.stat().st_size)
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            task_id=task.task_id,
            message=f"Created {len(files_created)} files, modified {len(files_modified)}",
            files_created=files_created,
            files_modified=files_modified
        )
    
    def _build_context(self, state: PipelineState, task: TaskState) -> str:
        """Build code context for the task"""
        parts = []
        
        # Get related files
        code_ctx = self.code_context.get_context_for_task(
            task.target_file,
            task.description,
            max_context_chars=3000
        )
        if code_ctx:
            parts.append(code_ctx)
        
        # Add dependency file contents
        for dep in task.dependencies[:3]:
            dep_content = self.read_file(dep)
            if dep_content:
                parts.append(f"=== DEPENDENCY: {dep} ===")
                parts.append(dep_content[:1000])
        
        return "\n\n".join(parts)
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate CODING_STATE.md content"""
        lines = [
            "# Coding State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Current Session Stats",
            "",
            f"- Files Created: {state.phases['coding'].successes}",
            f"- Failed Attempts: {state.phases['coding'].failures}",
            f"- Total Runs: {state.phases['coding'].runs}",
            "",
        ]
        
        # In-progress tasks
        in_progress = state.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        if in_progress:
            lines.append("## In Progress")
            lines.append("")
            for task in in_progress:
                lines.append(f"### {task.target_file}")
                lines.append(f"- Description: {task.description[:100]}")
                lines.append(f"- Attempt: {task.attempts}")
                lines.append("")
        
        # Recent errors
        recent_errors = []
        for task in state.tasks.values():
            for error in task.errors[-3:]:
                recent_errors.append((task, error))
        
        if recent_errors:
            lines.append("## Recent Errors")
            lines.append("")
            
            # Sort by timestamp
            recent_errors.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            for task, error in recent_errors[:10]:
                lines.append(f"### {task.target_file} - Attempt {error.attempt}")
                lines.append(f"- **Type:** {error.error_type}")
                lines.append(f"- **Message:** {error.message}")
                lines.append(f"- **Time:** {self.format_timestamp(error.timestamp)}")
                if error.line_number:
                    lines.append(f"- **Line:** {error.line_number}")
                if error.code_snippet:
                    lines.append("- **Code:**")
                    lines.append("```python")
                    lines.append(error.code_snippet)
                    lines.append("```")
                lines.append("")
        
        # QA Pending
        qa_pending = state.get_tasks_by_status(TaskStatus.QA_PENDING)
        if qa_pending:
            lines.append("## Awaiting QA Review")
            lines.append("")
            for task in qa_pending:
                lines.append(f"- `{task.target_file}`")
            lines.append("")
        
        # Error patterns
        patterns = self.error_context.get_error_patterns()
        if patterns:
            lines.append("## Error Patterns")
            lines.append("")
            lines.append("| Error Type | Count |")
            lines.append("|------------|-------|")
            for error_type, count in sorted(patterns.items(), key=lambda x: -x[1]):
                lines.append(f"| {error_type} | {count} |")
            lines.append("")
        
        return "\n".join(lines)
