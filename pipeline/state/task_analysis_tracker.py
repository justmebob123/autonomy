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
                # Phase 1: Basic File Understanding
                "read_target_files": AnalysisCheckpoint(
                    name="read_target_files",
                    description="Read all target files to understand their content",
                    required_tools={"read_file"}
                ),
                
                # Phase 2: Architectural Context
                "read_architecture": AnalysisCheckpoint(
                    name="read_architecture",
                    description="Read ARCHITECTURE.md to understand design intent",
                    required_tools={"read_file"}
                ),
                "read_master_plan": AnalysisCheckpoint(
                    name="read_master_plan",
                    description="Read MASTER_PLAN.md to understand project goals",
                    required_tools={"read_file"}
                ),
                
                # Phase 3: Codebase Context (NEW - COMPREHENSIVE)
                "list_all_source_files": AnalysisCheckpoint(
                    name="list_all_source_files",
                    description="List all source files to understand codebase structure",
                    required_tools={"list_all_source_files"}
                ),
                "find_all_related_files": AnalysisCheckpoint(
                    name="find_all_related_files",
                    description="Find all files related to the task",
                    required_tools={"find_all_related_files"}
                ),
                "read_all_related_files": AnalysisCheckpoint(
                    name="read_all_related_files",
                    description="Read all related files to understand full context",
                    required_tools={"read_file"}
                ),
                
                # Phase 4: Relationship Mapping (NEW)
                "map_file_relationships": AnalysisCheckpoint(
                    name="map_file_relationships",
                    description="Map imports, dependencies, and relationships between files",
                    required_tools={"map_file_relationships"}
                ),
                "cross_reference_files": AnalysisCheckpoint(
                    name="cross_reference_files",
                    description="Cross-reference files against architecture and master plan",
                    required_tools={"cross_reference_file"}
                ),
                
                # Phase 5: Deep Analysis (NEW)
                "analyze_all_file_purposes": AnalysisCheckpoint(
                    name="analyze_all_file_purposes",
                    description="Analyze the purpose of each related file",
                    required_tools={"analyze_file_purpose"}
                ),
                "compare_all_implementations": AnalysisCheckpoint(
                    name="compare_all_implementations",
                    description="Compare all related implementations to find best approach",
                    required_tools={"compare_file_implementations", "compare_multiple_files"}
                ),
                
                # Phase 6: Integration Analysis (NEW)
                "analyze_integration_points": AnalysisCheckpoint(
                    name="analyze_integration_points",
                    description="Analyze how files integrate with each other",
                    required_tools={"analyze_import_impact", "detect_integration_conflicts"}
                ),
                "validate_design_patterns": AnalysisCheckpoint(
                    name="validate_design_patterns",
                    description="Validate design patterns are consistent across files",
                    required_tools={"analyze_file_purpose", "cross_reference_file"}
                ),
                
                # Phase 7: Decision Making (NEW)
                "identify_superior_implementation": AnalysisCheckpoint(
                    name="identify_superior_implementation",
                    description="Identify which implementation is superior (if applicable)",
                    required_tools={"compare_file_implementations", "analyze_file_purpose"}
                ),
                "plan_integration_strategy": AnalysisCheckpoint(
                    name="plan_integration_strategy",
                    description="Plan how to integrate or refactor the code",
                    required_tools={"analyze_import_impact", "map_file_relationships"}
                ),
                
                # Phase 8: Architecture Validation (NEW)
                "validate_architecture_alignment": AnalysisCheckpoint(
                    name="validate_architecture_alignment",
                    description="Validate changes align with architecture",
                    required_tools={"validate_architecture", "cross_reference_file"}
                ),
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
            
            # Check each checkpoint
            for checkpoint_name, checkpoint in self.checkpoints.items():
                if checkpoint.completed:
                    continue  # Already complete
                
                # Check if this tool call satisfies the checkpoint
                if tool_name in checkpoint.required_tools:
                    # Special handling for read_file (needs specific files)
                    if tool_name == "read_file":
                        file_path = arguments.get("file_path", "")
                        
                        if checkpoint_name == "read_target_files":
                            if any(target in file_path for target in target_files):
                                checkpoint.completed = True
                                checkpoint.completed_at = tool_call["timestamp"]
                        
                        elif checkpoint_name == "read_architecture":
                            if "ARCHITECTURE.md" in file_path:
                                checkpoint.completed = True
                                checkpoint.completed_at = tool_call["timestamp"]
                        
                        elif checkpoint_name == "read_master_plan":
                            if "MASTER_PLAN.md" in file_path:
                                checkpoint.completed = True
                                checkpoint.completed_at = tool_call["timestamp"]
                        
                        elif checkpoint_name == "read_all_related_files":
                            # Mark as complete if we've read multiple related files
                            # (This is a progressive checkpoint)
                            checkpoint.completed = True
                            checkpoint.completed_at = tool_call["timestamp"]
                    
                    else:
                        # For other tools, just check if tool was used
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
        
        CONTINUOUS MODE: No attempt limits - continues until comprehensive analysis complete.
        
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
            # Get completion status
            missing = state.get_missing_checkpoints()
            completed_count = len(state.checkpoints) - len(missing)
            total_count = len(state.checkpoints)
            
            # PROGRESSIVE VALIDATION: Allow resolution after minimum analysis
            # But encourage comprehensive analysis
            minimum_required = ["read_target_files", "read_architecture", "perform_analysis"]
            minimum_complete = all(
                state.checkpoints[cp].completed 
                for cp in minimum_required 
                if cp in state.checkpoints
            )
            
            if not minimum_complete:
                # Block if minimum not met
                next_step = state.get_next_required_step()
                
                error_msg = f"""
🚫 MINIMUM ANALYSIS INCOMPLETE - Cannot proceed yet!

You are trying to take a resolving action but have NOT completed the MINIMUM required analysis.

📋 MINIMUM REQUIRED (must complete):
{chr(10).join(f"  {'✓' if state.checkpoints[cp].completed else '✗'} {state.checkpoints[cp].description}" for cp in minimum_required if cp in state.checkpoints)}

⚠️ NEXT REQUIRED STEP: {next_step}

📊 COMPREHENSIVE ANALYSIS PROGRESS: {completed_count}/{total_count} checkpoints complete

🔄 RECOMMENDED: Complete ALL checkpoints for best results:
{state.format_checklist()}

Attempt {attempt_number}: Complete minimum analysis to proceed, but comprehensive analysis is strongly recommended!
"""
                return False, error_msg
            
            elif len(missing) > 0:
                # Minimum met, but comprehensive analysis incomplete
                # ALLOW but WARN
                next_step = state.get_next_required_step()
                
                warning_msg = f"""
⚠️ COMPREHENSIVE ANALYSIS INCOMPLETE - Proceeding with caution!

You have completed the MINIMUM required analysis, but comprehensive analysis is incomplete.

📊 ANALYSIS PROGRESS: {completed_count}/{total_count} checkpoints complete

📋 REMAINING CHECKPOINTS (recommended):
{chr(10).join(f"  ✗ {state.checkpoints[m].description}" for m in missing)}

💡 RECOMMENDATION: Complete remaining checkpoints for better decisions:
- {next_step}

Attempt {attempt_number}: Proceeding, but comprehensive analysis would improve results!
"""
                # Log warning but allow
                print(warning_msg)
                return True, None  # Allow with warning
        
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