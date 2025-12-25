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
        
        self.action_tracker = ActionTracker(
            history_file=logs_dir / "action_history.jsonl"
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
            tool_name = tool_call.get('tool', 'unknown')
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