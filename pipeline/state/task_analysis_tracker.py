"""
Task Analysis Tracker - Tracks tool usage per task to enforce comprehensive analysis.

This module ensures AI completes all required analysis steps before taking resolving actions.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AnalysisCheckpoint:
    """Represents a required analysis checkpoint."""
    name: str
    description: str
    required_tools: Set[str]
    completed: bool = False
    completed_at: Optional[datetime] = None


@dataclass
class TaskAnalysisState:
    """Tracks analysis state for a single task."""
    task_id: str
    attempt_number: int = 1
    tool_calls_history: List[Dict] = field(default_factory=list)
    checkpoints: Dict[str, AnalysisCheckpoint] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize checkpoints if not provided."""
        if not self.checkpoints:
            self.checkpoints = {
                "read_target_files": AnalysisCheckpoint(
                    name="read_target_files",
                    description="Read all target files to understand their content",
                    required_tools={"read_file"}
                ),
                "read_architecture": AnalysisCheckpoint(
                    name="read_architecture",
                    description="Read ARCHITECTURE.md to understand design intent",
                    required_tools={"read_file"}
                ),
                "perform_analysis": AnalysisCheckpoint(
                    name="perform_analysis",
                    description="Perform appropriate analysis (compare, analyze complexity, etc.)",
                    required_tools={"compare_file_implementations", "analyze_complexity", 
                                   "detect_dead_code", "analyze_import_impact"}
                )
            }
    
    def record_tool_call(self, tool_name: str, arguments: Dict, result: Dict) -> None:
        """Record a tool call in history."""
        self.tool_calls_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.now()
        })
    
    def update_checkpoints(self, target_files: List[str]) -> None:
        """Update checkpoint completion status based on tool call history."""
        for tool_call in self.tool_calls_history:
            tool_name = tool_call["tool"]
            arguments = tool_call.get("arguments", {})
            
            # Check read_target_files checkpoint
            if tool_name == "read_file":
                file_path = arguments.get("file_path", "")
                
                # Check if reading target files
                if any(target in file_path for target in target_files):
                    checkpoint = self.checkpoints["read_target_files"]
                    if not checkpoint.completed:
                        checkpoint.completed = True
                        checkpoint.completed_at = tool_call["timestamp"]
                
                # Check if reading ARCHITECTURE.md
                if "ARCHITECTURE.md" in file_path:
                    checkpoint = self.checkpoints["read_architecture"]
                    if not checkpoint.completed:
                        checkpoint.completed = True
                        checkpoint.completed_at = tool_call["timestamp"]
            
            # Check perform_analysis checkpoint
            if tool_name in self.checkpoints["perform_analysis"].required_tools:
                checkpoint = self.checkpoints["perform_analysis"]
                if not checkpoint.completed:
                    checkpoint.completed = True
                    checkpoint.completed_at = tool_call["timestamp"]
    
    def get_completion_status(self) -> Dict[str, bool]:
        """Get completion status of all checkpoints."""
        return {name: cp.completed for name, cp in self.checkpoints.items()}
    
    def get_missing_checkpoints(self) -> List[str]:
        """Get list of incomplete checkpoint names."""
        return [name for name, cp in self.checkpoints.items() if not cp.completed]
    
    def is_analysis_complete(self) -> bool:
        """Check if all required analysis is complete."""
        return all(cp.completed for cp in self.checkpoints.values())
    
    def get_next_required_step(self) -> Optional[str]:
        """Get description of next required step."""
        for checkpoint in self.checkpoints.values():
            if not checkpoint.completed:
                return checkpoint.description
        return None
    
    def format_checklist(self) -> str:
        """Format checklist for display in prompt."""
        lines = []
        for name, checkpoint in self.checkpoints.items():
            status = "✓" if checkpoint.completed else "✗"
            lines.append(f"{status} {checkpoint.description}")
        return "\n".join(lines)


class TaskAnalysisTracker:
    """
    Tracks analysis state for all refactoring tasks.
    
    Ensures AI completes comprehensive analysis before taking resolving actions.
    """
    
    def __init__(self):
        self.task_states: Dict[str, TaskAnalysisState] = {}
    
    def get_or_create_state(self, task_id: str) -> TaskAnalysisState:
        """Get or create analysis state for a task."""
        if task_id not in self.task_states:
            self.task_states[task_id] = TaskAnalysisState(task_id=task_id)
        return self.task_states[task_id]
    
    def record_tool_call(self, task_id: str, tool_name: str, arguments: Dict, result: Dict) -> None:
        """Record a tool call for a task."""
        state = self.get_or_create_state(task_id)
        state.record_tool_call(tool_name, arguments, result)
    
    def update_checkpoints(self, task_id: str, target_files: List[str]) -> None:
        """Update checkpoint status for a task."""
        state = self.get_or_create_state(task_id)
        state.update_checkpoints(target_files)
    
    def validate_tool_calls(self, task_id: str, tool_calls: List[Dict], 
                          target_files: List[str], attempt_number: int) -> tuple[bool, Optional[str]]:
        """
        Validate that required analysis is complete before allowing resolving actions.
        
        Args:
            task_id: Task identifier
            tool_calls: Proposed tool calls
            target_files: Target files for this task
            attempt_number: Current attempt number
            
        Returns:
            (is_valid, error_message)
        """
        state = self.get_or_create_state(task_id)
        state.attempt_number = attempt_number
        
        # Update checkpoints based on current history
        state.update_checkpoints(target_files)
        
        # Check if AI is trying to use resolving tools
        resolving_tools = {
            "merge_file_implementations",
            "cleanup_redundant_files",
            "create_issue_report",
            "request_developer_review",
            "move_file",
            "rename_file",
            "restructure_directory"
        }
        
        is_resolving = any(
            tc.get("function", {}).get("name") in resolving_tools 
            for tc in tool_calls
        )
        
        if is_resolving:
            # Check if analysis is complete
            if not state.is_analysis_complete():
                missing = state.get_missing_checkpoints()
                next_step = state.get_next_required_step()
                
                error_msg = f"""
🚫 ANALYSIS INCOMPLETE - Cannot proceed with resolving action yet!

You are trying to take a resolving action (merge, report, etc.) but you have NOT completed the required analysis.

📋 MISSING CHECKPOINTS:
{chr(10).join(f"  ✗ {state.checkpoints[m].description}" for m in missing)}

⚠️ NEXT REQUIRED STEP: {next_step}

🔄 WHAT TO DO NOW:
1. Complete the missing analysis steps listed above
2. THEN you can take resolving action

Example for this attempt:
- First: read_file(file_path="{target_files[0] if target_files else 'target_file.py'}")
- Then: read_file(file_path="ARCHITECTURE.md")
- Then: compare_file_implementations(...) or other analysis
- Finally: merge_file_implementations(...) or create_issue_report(...)

📊 CURRENT CHECKLIST STATUS:
{state.format_checklist()}

Attempt {attempt_number}: You MUST complete analysis before resolving!
"""
                return False, error_msg
        
        return True, None
    
    def get_checklist_status(self, task_id: str, target_files: List[str]) -> str:
        """Get formatted checklist status for prompt."""
        state = self.get_or_create_state(task_id)
        state.update_checkpoints(target_files)
        return state.format_checklist()
    
    def is_analysis_complete(self, task_id: str, target_files: List[str]) -> bool:
        """Check if analysis is complete for a task."""
        state = self.get_or_create_state(task_id)
        state.update_checkpoints(target_files)
        return state.is_analysis_complete()
    
    def get_next_step(self, task_id: str, target_files: List[str]) -> Optional[str]:
        """Get next required step for a task."""
        state = self.get_or_create_state(task_id)
        state.update_checkpoints(target_files)
        return state.get_next_required_step()
    
    def reset_task(self, task_id: str) -> None:
        """Reset analysis state for a task (when task is retried)."""
        if task_id in self.task_states:
            del self.task_states[task_id]
    
    def clear_completed_tasks(self, completed_task_ids: List[str]) -> None:
        """Clear analysis state for completed tasks."""
        for task_id in completed_task_ids:
            if task_id in self.task_states:
                del self.task_states[task_id]