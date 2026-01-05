"""
Action Tracker - Monitors all AI actions for loop detection

This module tracks every action taken by AI agents to detect patterns
that indicate infinite loops or repetitive behavior.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path


@dataclass
class Action:
    """Represents a single AI action"""
    timestamp: float
    phase: str
    agent: str
    tool: str
    args: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    file_path: Optional[str]
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_signature(self) -> str:
        """Get unique signature for this action"""
        # Create signature from tool + key args
        key_args = []
        if self.file_path:
            key_args.append(f"file:{self.file_path}")
        if 'old_str' in self.args:
            pass
            # For str_replace, include first 50 chars of old_str
            old_str = self.args['old_str'][:50]
            key_args.append(f"old:{old_str}")
        if 'content' in self.args:
            pass
            # For file writes, include first 50 chars
            content = str(self.args['content'])[:50]
            key_args.append(f"content:{content}")
        
        return f"{self.tool}({','.join(key_args)})"


class ActionTracker:
    """
    Tracks all AI actions to detect loops and patterns.
    
    Maintains a history of actions with timestamps, allowing detection of:
    - Repeated identical actions
    - Cyclic patterns
    - Modification loops
    - Conversation loops
    """
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize action tracker.
        
        Args:
            history_file: Optional file to persist action history
        """
        self.actions: List[Action] = []
        self.history_file = history_file
        
        # Load existing history if available
        if history_file and history_file.exists():
            self._load_history()
    
    def track_action(
        self,
        phase: str,
        agent: str,
        tool: str,
        args: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        success: bool = True
    ) -> Action:
        """
        Track a new action.
        
        Args:
            phase: Current phase (debugging, coding, etc.)
            agent: Agent name (main, specialist, etc.)
            tool: Tool name (str_replace, read_file, etc.)
            args: Tool arguments
            result: Tool result
            file_path: File being operated on
            success: Whether action succeeded
            
        Returns:
            The tracked Action object
        """
        action = Action(
            timestamp=time.time(),
            phase=phase,
            agent=agent,
            tool=tool,
            args=args,
            result=result,
            file_path=file_path,
            success=success
        )
        
        self.actions.append(action)
        
        # Persist if history file configured
        if self.history_file:
            self._save_action(action)
        
        return action
    
    def get_recent_actions(
        self,
        count: int = 10,
        phase: Optional[str] = None,
        agent: Optional[str] = None,
        tool: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> List[Action]:
        """
        Get recent actions with optional filtering.
        
        Args:
            count: Number of recent actions to return
            phase: Filter by phase
            agent: Filter by agent
            tool: Filter by tool
            file_path: Filter by file path
            
        Returns:
            List of recent actions matching filters
        """
        filtered = self.actions
        
        if phase:
            filtered = [a for a in filtered if a.phase == phase]
        if agent:
            filtered = [a for a in filtered if a.agent == agent]
        if tool:
            filtered = [a for a in filtered if a.tool == tool]
        if file_path:
            filtered = [a for a in filtered if a.file_path == file_path]
        
        return filtered[-count:]
    
    def get_action_sequence(
        self,
        window_size: int = 10
    ) -> List[str]:
        """
        Get sequence of action signatures for pattern detection.
        
        Args:
            window_size: Number of recent actions to include
            
        Returns:
            List of action signatures
        """
        recent = self.actions[-window_size:]
        return [action.get_signature() for action in recent]
    
    def get_file_modifications(
        self,
        file_path: str,
        time_window: Optional[float] = None
    ) -> List[Action]:
        """
        Get all modifications to a specific file.
        
        Args:
            file_path: Path to file
            time_window: Optional time window in seconds (from now)
            
        Returns:
            List of modification actions
        """
        modifications = [
            a for a in self.actions
            if a.file_path == file_path and a.tool in ['str_replace', 'full_file_rewrite', 'create_file']
        ]
        
        if time_window:
            cutoff = time.time() - time_window
            modifications = [a for a in modifications if a.timestamp >= cutoff]
        
        return modifications
    
    def get_action_frequency(
        self,
        time_window: float = 300.0
    ) -> Dict[str, int]:
        """
        Get frequency of each action type in time window.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Dictionary mapping action signatures to counts
        """
        cutoff = time.time() - time_window
        recent = [a for a in self.actions if a.timestamp >= cutoff]
        
        frequency = defaultdict(int)
        for action in recent:
            frequency[action.get_signature()] += 1
        
        return dict(frequency)
    
    def get_conversation_turns(
        self,
        agent: str,
        time_window: Optional[float] = None
    ) -> List[Action]:
        """
        Get conversation turns for an agent.
        
        Args:
            agent: Agent name
            time_window: Optional time window in seconds
            
        Returns:
            List of actions representing conversation turns
        """
        turns = [a for a in self.actions if a.agent == agent]
        
        if time_window:
            cutoff = time.time() - time_window
            turns = [a for a in turns if a.timestamp >= cutoff]
        
        return turns
    
    def detect_immediate_repeat(
        self,
        threshold: int = 3
    ) -> Optional[Tuple[str, int]]:
        """
        Detect if the same action is being repeated immediately.
        
        Args:
            threshold: Number of repeats to trigger detection
            
        Returns:
            Tuple of (action_signature, count) if detected, None otherwise
        """
        if len(self.actions) < threshold:
            return None
        
        recent = self.actions[-threshold:]
        signatures = [a.get_signature() for a in recent]
        
        # Check if all signatures are identical
        if len(set(signatures)) == 1:
            return (signatures[0], threshold)
        
        return None
    
    def detect_alternating_pattern(
        self,
        window_size: int = 10,
        min_cycles: int = 2
    ) -> Optional[Tuple[List[str], int]]:
        """
        Detect alternating patterns (A-B-A-B or A-B-C-A-B-C).
        
        Args:
            window_size: Size of window to analyze
            min_cycles: Minimum number of complete cycles to detect
            
        Returns:
            Tuple of (pattern, cycle_count) if detected, None otherwise
        """
        if len(self.actions) < window_size:
            return None
        
        sequence = self.get_action_sequence(window_size)
        
        # Try pattern lengths from 2 to window_size/2
        for pattern_len in range(2, window_size // 2 + 1):
            pattern = sequence[:pattern_len]
            
            # Check if pattern repeats
            cycles = 0
            for i in range(0, len(sequence) - pattern_len + 1, pattern_len):
                if sequence[i:i+pattern_len] == pattern:
                    cycles += 1
                else:
                    break
            
            if cycles >= min_cycles:
                return (pattern, cycles)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about tracked actions.
        
        Returns:
            Dictionary with statistics
        """
        if not self.actions:
            return {
                'total_actions': 0,
                'time_span': 0,
                'actions_per_minute': 0
            }
        
        time_span = self.actions[-1].timestamp - self.actions[0].timestamp
        
        # Count by phase
        by_phase = defaultdict(int)
        for action in self.actions:
            by_phase[action.phase] += 1
        
        # Count by tool
        by_tool = defaultdict(int)
        for action in self.actions:
            by_tool[action.tool] += 1
        
        # Count by file
        by_file = defaultdict(int)
        for action in self.actions:
            if action.file_path:
                by_file[action.file_path] += 1
        
        return {
            'total_actions': len(self.actions),
            'time_span': time_span,
            'actions_per_minute': len(self.actions) / (time_span / 60) if time_span > 0 else 0,
            'by_phase': dict(by_phase),
            'by_tool': dict(by_tool),
            'by_file': dict(by_file),
            'success_rate': sum(1 for a in self.actions if a.success) / len(self.actions)
        }
    
    def clear_history(self):
        """Clear all tracked actions"""
        self.actions.clear()
        if self.history_file and self.history_file.exists():
            self.history_file.unlink()
    
    def _save_action(self, action: Action):
        """Save action to history file"""
        if not self.history_file:
            return
        
        # Append to file
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(action.to_dict()) + '\n')
    
    def _load_history(self):
        """Load action history from file"""
        if not self.history_file or not self.history_file.exists():
            return
        
        with open(self.history_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    action = Action(**data)
                    self.actions.append(action)