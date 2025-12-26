"""
Loop Detection System

Consolidated module for loop detection functionality.
Combines ActionTracker, PatternDetector, and LoopInterventionSystem.
"""

from typing import Dict, List, Optional
from pathlib import Path
import logging

from .action_tracker import ActionTracker
from .pattern_detector import PatternDetector
from .loop_intervention import LoopInterventionSystem


class LoopDetectionFacade:
    """
    Facade for loop detection system.
    Simplifies initialization and usage of the three-component system.
    """
    
    def __init__(self, project_dir: Path, logger: logging.Logger):
        """
        Initialize the loop detection system.
        
        Args:
            project_dir: Project directory for logs
            logger: Logger instance
        """
        # Create logs directory
        logs_dir = project_dir / ".autonomous_logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.action_tracker = ActionTracker(
            history_file=logs_dir / "action_history.jsonl"
        )
        self.pattern_detector = PatternDetector(self.action_tracker)
        self.loop_intervention = LoopInterventionSystem(
            self.action_tracker,
            self.pattern_detector,
            logger
        )
    
    def track_action(self, phase: str, agent: str, tool: str, 
                    args: Dict, result: Dict, file_path: Optional[str] = None,
                    success: bool = False):
        """Track an action for loop detection."""
        self.action_tracker.track_action(
            phase=phase,
            agent=agent,
            tool=tool,
            args=args,
            result=result,
            file_path=file_path,
            success=success
        )
    
    def check_and_intervene(self) -> Optional[Dict]:
        """Check for loops and intervene if necessary."""
        return self.loop_intervention.check_and_intervene()
    
    def get_recent_actions(self, count: int = 10) -> List[Dict]:
        """Get recent actions for context."""
        return self.action_tracker.get_recent_actions(count)