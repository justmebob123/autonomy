"""
Loop Detection Mixin

Provides loop detection capabilities to any phase.
"""

from typing import List, Dict, Optional
from pathlib import Path

from ..action_tracker import ActionTracker
from ..pattern_detector import PatternDetector
from ..loop_intervention import LoopInterventionSystem


class LoopDetectionMixin:
    """
    Mixin to add loop detection to any phase.
    
    Usage:
        class MyPhase(BasePhase, LoopDetectionMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.init_loop_detection()
    """
    
    def init_loop_detection(self):
        """Initialize loop detection components"""
        logs_dir = self.project_dir / ".autonomous_logs"
        logs_dir.mkdir(exist_ok=True)
        
        history_file = logs_dir / "action_history.jsonl"
        
        # CRITICAL FIX: Clear old action history to prevent false positives
        # Old actions from previous runs cause loop detector to flag normal work
        if history_file.exists():
            # Archive old history with timestamp
            import time
            archive_file = logs_dir / f"action_history_{int(time.time())}.jsonl"
            try:
                history_file.rename(archive_file)
                self.logger.info(f"  Archived old action history to {archive_file.name}")
            except Exception as e:
                self.logger.warning(f"  Could not archive old history: {e}")
                # If rename fails, just delete it
                try:
                    history_file.unlink()
                except FileNotFoundError:
                    # Already deleted
                    pass
                except PermissionError as e:
                    self.logger.error(f"Permission denied deleting history file: {e}")
                except Exception as e:
                    self.logger.error(f"Failed to delete history file: {e}")
        
        self.action_tracker = ActionTracker(
            history_file=history_file
        )
        self.pattern_detector = PatternDetector(self.action_tracker)
        self.loop_intervention = LoopInterventionSystem(
            self.action_tracker,
            self.pattern_detector,
            self.logger
        )
    
    def track_tool_calls(self, tool_calls: List[Dict], results: List[Dict], agent: str = "main"):
        """Track tool calls for loop detection"""
        for tool_call, result in zip(tool_calls, results):
            # FIX: Ensure tool name is never "unknown"
            tool_name = tool_call.get('tool') or tool_call.get('name') or 'unspecified_tool'
            
            # Don't track if tool name is still unknown/unspecified
            # This prevents false positives from improperly tracked tools
            if tool_name in ['unknown', 'unspecified_tool', '']:
                self.logger.debug(f"Skipping tracking of unknown tool: {tool_call}")
                continue
            
            args = tool_call.get('args', {})
            
            # Extract file path if present
            file_path = None
            if 'file_path' in args:
                file_path = args['file_path']
            elif 'filepath' in args:
                file_path = args['filepath']
            
            # Track the action
            self.action_tracker.track_action(
                phase=self.phase_name,
                agent=agent,
                tool=tool_name,
                args=args,
                result=result,
                file_path=file_path,
                success=result.get('success', False)
            )
    
    def check_for_loops(self) -> Optional[Dict]:
        """Check for loops and intervene if necessary"""
        
        # CRITICAL FIX: Coding phase creating multiple files is NORMAL, not a loop!
        if self.phase_name == 'coding':
            # Get recent actions for this phase
            recent = self.action_tracker.get_recent_actions(10)
            coding_actions = [a for a in recent if a.phase == 'coding']
            
            # Check if working on different files (NORMAL DEVELOPMENT)
            files = set(a.file_path for a in coding_actions if a.file_path)
            if len(files) > 1:
                # Working on multiple different files = NORMAL DEVELOPMENT
                # This is NOT a loop, it's implementing multiple tasks!
                return None
            
            # Only check for loops if working on SAME file repeatedly
            if len(files) == 1:
                same_file_actions = [a for a in coding_actions if a.file_path == list(files)[0]]
                if len(same_file_actions) < 5:
                    # Less than 5 modifications to same file = still normal
                    return None
                # Fall through to standard loop detection for same-file loops
        
        intervention = self.loop_intervention.check_and_intervene()
        
        if intervention:
            # Log the intervention
            self.logger.warning("=" * 80)
            self.logger.warning("LOOP DETECTED - INTERVENTION REQUIRED")
            self.logger.warning("=" * 80)
            self.logger.warning(intervention['guidance'])
            self.logger.warning("=" * 80)
            
            # Return intervention for AI to see
            return intervention
        
        return None