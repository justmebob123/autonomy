"""
Planning Phase

Creates development plans from project specifications.
"""

from datetime import datetime
from typing import Dict, List, Optional

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_planning_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


class PlanningPhase(BasePhase, LoopDetectionMixin):
    """
    Planning phase that creates task plans from MASTER_PLAN.md.
    
    Responsibilities:
    - Parse MASTER_PLAN.md
    - Generate task breakdown
    - Set priorities and dependencies
    - Write PLANNING_STATE.md
    """
    
    phase_name = "planning"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.OBJECTIVE_ACTIVATED,
                MessageType.OBJECTIVE_BLOCKED,
                MessageType.SYSTEM_ALERT,
            ])
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute the planning phase"""
        
        # MESSAGE BUS: Check for relevant messages
        if self.message_bus:
            from ..messaging import MessageType
            messages = self._get_messages(
                message_types=[MessageType.OBJECTIVE_ACTIVATED, MessageType.OBJECTIVE_BLOCKED],
                limit=5
            )
            if messages:
                self.logger.info(f"  📨 Received {len(messages)} messages")
                for msg in messages:
                    self.logger.info(f"    • {msg.message_type.value}: {msg.payload.get('objective_id', 'N/A')}")
                # Clear processed messages
                self._clear_messages([msg.id for msg in messages])
        
        # Check if we have an active objective (strategic mode)
        objective = kwargs.get('objective')
        if objective:
            self.logger.info(f"  🎯 Planning for objective: {objective.title}")
        
        # Load MASTER_PLAN.md
        master_plan = self.read_file("MASTER_PLAN.md")
        if not master_plan:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="MASTER_PLAN.md not found"
            )
        
        self.logger.info(f"  Loaded MASTER_PLAN.md ({len(master_plan)} bytes)")
        
        # Get existing files for context
        existing_files = self._get_existing_files()
        
        # Build messages
        messages = [
            {"role": "system", "content": self._get_system_prompt("planning")},
            {"role": "user", "content": get_planning_prompt(master_plan, existing_files)}
        ]
        
        # Use reasoning specialist for planning
        # Build simple planning message
        user_message = self._build_planning_message(master_plan, existing_files)
        
        # Get tools for planning phase
        tools = get_tools_for_phase("planning")
        
        # Call model with conversation history
        self.logger.info("  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        
        tasks = []
        
        if tool_calls:
            # Process tool calls
            handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
            results = handler.process_tool_calls(tool_calls)
            tasks = handler.tasks
            
            # Track actions for loop detection
            self.track_tool_calls(tool_calls, results, agent="planning")
            
            # Check for loops
            intervention = self.check_for_loops()
            if intervention and intervention.get('requires_user_input'):
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Loop detected - user intervention required",
                    data={'intervention': intervention}
                )
        
        # Fallback: extract from text
        if not tasks and content:
            self.logger.warning("  Model returned text instead of tool call")
            tasks = self.parser.extract_tasks_from_text(content)
            if tasks:
                self.logger.info(f"  Extracted {len(tasks)} tasks from text")
        
        if not tasks:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Could not extract tasks from response"
            )
        
        # Add tasks to state
        for task_data in tasks:
            # Check if task already exists (by description)
            existing = self._find_existing_task(state, task_data)
            
            if not existing:
                target_file = task_data.get("target_file", "").strip()
                
                # Skip tasks with empty filenames
                if not target_file:
                    self.logger.warning(f"  ⚠️ Skipping task with empty filename: {task_data.get('description', 'Unknown')}")
                    continue
                
                # Skip tasks targeting directories
                full_path = self.project_dir / target_file
                if full_path.exists() and full_path.is_dir():
                    self.logger.warning(f"  ⚠️ Skipping task targeting directory: {target_file}")
                    continue
                
                # Get objective info if available
                objective_id = None
                objective_level = None
                objective = kwargs.get('objective')
                if objective:
                    objective_id = objective.id
                    objective_level = objective.level.value if hasattr(objective.level, 'value') else objective.level
                
                # Create task with objective linking
                task = state.add_task(
                    description=task_data.get("description", ""),
                    target_file=target_file,
                    priority=task_data.get("priority", TaskPriority.NEW_TASK),
                    dependencies=task_data.get("dependencies", []),
                    objective_id=objective_id,
                    objective_level=objective_level
                )
                
                # Link task to objective
                if objective and objective_id:
                    if objective_id not in state.objectives.get(objective_level, {}):
                        # Create objective entry if it doesn't exist
                        if objective_level not in state.objectives:
                            state.objectives[objective_level] = {}
                        state.objectives[objective_level][objective_id] = objective.to_dict()
                    
                    # Add task to objective's task list
                    obj_data = state.objectives[objective_level][objective_id]
                    if 'tasks' not in obj_data:
                        obj_data['tasks'] = []
                    if task.task_id not in obj_data['tasks']:
                        obj_data['tasks'].append(task.task_id)
                        obj_data['total_tasks'] = len(obj_data['tasks'])
                
                # MESSAGE BUS: Publish TASK_CREATED event
                from ..messaging import MessageType, MessagePriority
                self._publish_message(
                    message_type=MessageType.TASK_CREATED,
                    payload={
                        'task_id': task.task_id,
                        'description': task.description,
                        'target_file': task.target_file,
                        'priority': task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                    },
                    recipient="broadcast",
                    priority=MessagePriority.NORMAL,
                    task_id=task.task_id,
                    objective_id=objective_id,
                    file_path=task.target_file
                )
        
        # Rebuild queue with current priorities
        state.rebuild_queue()
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Created plan with {len(tasks)} tasks",
            data={"task_count": len(tasks), "tasks": tasks}
        )
    
    def _get_existing_files(self) -> str:
        """Get list of existing Python files"""
        files = []
        for f in self.project_dir.rglob("*.py"):
            if "__pycache__" not in str(f):
                rel = f.relative_to(self.project_dir)
                files.append(f"  - {rel}")
        
        return "\n".join(files[:20]) if files else "(no files yet)"
    
    def _find_existing_task(self, state: PipelineState, 
                            task_data: Dict) -> Optional[TaskState]:
        """Find if a similar task already exists"""
        desc = task_data.get("description", "")[:50]
        target = task_data.get("target_file", "")
        
        for task in state.tasks.values():
            if task.description[:50] == desc or task.target_file == target:
                return task
        return None
    
    def _build_planning_message(self, master_plan: str, existing_files: List[str]) -> str:
        """
        Build a simple, focused planning message.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Master plan
        parts.append(f"Master Plan:\n{master_plan}")
        
        # Existing files context
        if existing_files:
            parts.append(f"\nExisting files in project:\n" + "\n".join(f"- {f}" for f in existing_files[:10]))
            if len(existing_files) > 10:
                parts.append(f"... and {len(existing_files) - 10} more files")
        
        # Instructions
        parts.append("\nPlease create a detailed task plan using the create_task tool for each task needed.")
        parts.append("Break down the master plan into specific, actionable tasks.")
        
        return "\n".join(parts)
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate PLANNING_STATE.md content"""
        lines = [
            "# Planning State",
            f"Generated: {self.format_timestamp()}",
            f"Pipeline Run: {state.pipeline_run_id}",
            "",
            "## Task Queue Summary",
            "",
            f"| Status | Count |",
            f"|--------|-------|",
        ]
        
        # Count by status
        status_counts = {}
        for task in state.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            lines.append(f"| {status} | {count} |")
        
        lines.append("")
        lines.append("## Tasks by Priority")
        lines.append("")
        
        # Group by priority
        by_priority: Dict[int, List[TaskState]] = {}
        for task in state.tasks.values():
            p = task.priority
            if p not in by_priority:
                by_priority[p] = []
            by_priority[p].append(task)
        
        priority_names = {
            1: "CRITICAL_BUG",
            2: "QA_FAILURE", 
            3: "DEBUG_PENDING",
            4: "IN_PROGRESS",
            5: "INCOMPLETE",
            6: "NEW_TASK",
            7: "LOW",
            10: "DEFERRED",
        }
        
        for priority in sorted(by_priority.keys()):
            tasks = by_priority[priority]
            priority_name = priority_names.get(priority, f"PRIORITY_{priority}")
            
            lines.append(f"### Priority {priority}: {priority_name}")
            lines.append("")
            
            if not tasks:
                lines.append("(none)")
            else:
                for task in tasks:
                    status_icon = {
                        TaskStatus.COMPLETED: "[x]",
                        TaskStatus.SKIPPED: "[~]",
                        TaskStatus.IN_PROGRESS: "[>]",
                        TaskStatus.QA_FAILED: "[!]",
                    }.get(task.status, "[ ]")
                    
                    lines.append(f"- {status_icon} `{task.target_file}` - {task.description[:60]}")
                    
                    if task.dependencies:
                        deps = ", ".join(task.dependencies)
                        lines.append(f"  - Depends on: {deps}")
                    
                    if task.attempts > 0:
                        lines.append(f"  - Attempts: {task.attempts}")
                    
                    if task.errors:
                        last_error = task.errors[-1]
                        lines.append(f"  - Last error: {last_error.message[:50]}")
            
            lines.append("")
        
        # Completed tasks
        completed = state.get_tasks_by_status(TaskStatus.COMPLETED)
        if completed:
            lines.append("## Completed Tasks")
            lines.append("")
            for task in completed:
                completed_time = self.format_timestamp(task.completed) if task.completed else "?"
                lines.append(f"- [x] `{task.target_file}` - Completed {completed_time}")
            lines.append("")
        
        return "\n".join(lines)
