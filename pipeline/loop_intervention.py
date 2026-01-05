"""
Loop Intervention System - Breaks infinite loops with intelligent suggestions

This module provides intervention strategies when loops are detected,
including automatic actions and AI guidance to break out of loops.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .pattern_detector import PatternDetector, LoopDetection
from .action_tracker import ActionTracker


class LoopInterventionSystem:
    """
    Intervenes when loops are detected to break the cycle.
    
    Provides:
    - Automatic interventions (clearing state, resetting)
    - AI guidance with specific suggestions
    - Escalation to user when needed
    """
    
    def __init__(
        self,
        action_tracker: ActionTracker,
        pattern_detector: PatternDetector,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize intervention system.
        
        Args:
            action_tracker: ActionTracker instance
            pattern_detector: PatternDetector instance
            logger: Optional logger
        """
        self.tracker = action_tracker
        self.detector = pattern_detector
        self.logger = logger or logging.getLogger(__name__)
        
        # Track interventions to avoid intervention loops
        self.intervention_count = 0
        self.max_interventions = 3
    
    def check_and_intervene(self) -> Optional[Dict[str, Any]]:
        """
        Check for loops and intervene if necessary.
        
        Returns:
            Intervention result if intervention occurred, None otherwise
        """
        # Detect loops
        detections = self.detector.detect_all_loops()
        
        if not detections:
            pass
            # No loops detected, reset intervention count
            self.intervention_count = 0
            return None
        
        # Check if intervention needed
        if not self.detector.should_intervene(detections):
            pass
            # Loops detected but not severe enough
            self.logger.info(f"Loops detected but not severe enough for intervention: {len(detections)}")
            return None
        
        # Intervention needed
        self.intervention_count += 1
        self.logger.warning(f"Loop intervention #{self.intervention_count}")
        
        # Check if we've intervened too many times
        if self.intervention_count >= self.max_interventions:
            return self._escalate_to_user(detections)
        
        # Perform intervention
        return self._intervene(detections)
    
    def _intervene(self, detections: List[LoopDetection]) -> Dict[str, Any]:
        """
        Perform intervention based on detected loops.
        
        Args:
            detections: List of loop detections
            
        Returns:
            Intervention result
        """
        # Get most severe detection
        most_severe = detections[0]  # Already sorted by severity
        
        # Generate intervention based on loop type
        if most_severe.loop_type == 'action_loop':
            return self._intervene_action_loop(most_severe, detections)
        elif most_severe.loop_type == 'modification_loop':
            return self._intervene_modification_loop(most_severe, detections)
        elif most_severe.loop_type == 'conversation_loop':
            return self._intervene_conversation_loop(most_severe, detections)
        elif most_severe.loop_type == 'circular_dependency':
            return self._intervene_circular_dependency(most_severe, detections)
        elif most_severe.loop_type == 'state_cycle':
            return self._intervene_state_cycle(most_severe, detections)
        elif most_severe.loop_type == 'pattern_repetition':
            return self._intervene_pattern_repetition(most_severe, detections)
        else:
            return self._generic_intervention(detections)
    
    def _intervene_action_loop(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in action loop"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 ACTION LOOP DETECTED - INTERVENTION REQUIRED

{summary}

IMMEDIATE ACTIONS REQUIRED:
1. STOP using the current tool/approach - it's not working
2. READ the current file state to see what actually exists
3. ANALYZE why the action keeps failing
4. TRY a completely different approach:
   - If using str_replace, try full_file_rewrite
   - If modifying code, try reading file first to see exact indentation
   - If searching, try a different search pattern
   - If executing commands, check for errors in output

CRITICAL: Do NOT repeat the same action again. You must try something different.

If you cannot find an alternative approach, use the 'ask' tool to request user guidance.
"""
        
        return {
            'intervention_type': 'action_loop',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['read_file', 'search_code', 'ask'],
            'blocked_tools': [detection.actions_involved[0].tool] if detection.actions_involved else [],
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _intervene_modification_loop(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in modification loop"""
        summary = self.detector.get_loop_summary(all_detections)
        
        # Get the file being modified
        file_path = detection.actions_involved[0].file_path if detection.actions_involved else 'unknown'
        
        guidance = f"""
🛑 MODIFICATION LOOP DETECTED - INTERVENTION REQUIRED

{summary}

The file '{file_path}' has been modified repeatedly without success.

IMMEDIATE ACTIONS REQUIRED:
1. READ the file to see its CURRENT state (not what you think it is)
2. VERIFY the code you're trying to replace actually exists
3. CHECK the exact indentation in the file
4. CONSIDER using full_file_rewrite instead of str_replace
5. CONSULT a specialist (Whitespace Analyst or Syntax Analyst) if needed

CRITICAL INSIGHTS:
- The code may have already been modified by previous attempts
- Indentation may not match what you expect
- The old_str you're searching for may not exist anymore
- You may need to see the bigger picture with full_file_rewrite

If the file is in an inconsistent state, use full_file_rewrite to completely rewrite it.
If you're unsure, use the 'ask' tool to request user guidance.
"""
        
        return {
            'intervention_type': 'modification_loop',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['read_file', 'full_file_rewrite', 'consult_specialist', 'ask'],
            'blocked_tools': ['str_replace'],  # Temporarily block str_replace
            'target_file': file_path,
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _intervene_conversation_loop(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in conversation loop"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 CONVERSATION LOOP DETECTED - INTERVENTION REQUIRED

{summary}

You are repeatedly analyzing the same thing without taking action.

IMMEDIATE ACTIONS REQUIRED:
1. STOP gathering more information - you have enough
2. REVIEW what you've already learned from previous analyses
3. MAKE A DECISION based on the information you have
4. TAKE ACTION to implement a solution

CRITICAL: Analysis paralysis detected. You must move from analysis to action.

If you're uncertain about what action to take, use the 'ask' tool to request user guidance.
Do NOT read the same file or run the same command again.
"""
        
        return {
            'intervention_type': 'conversation_loop',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['str_replace', 'full_file_rewrite', 'create_file', 'ask'],
            'blocked_tools': ['read_file', 'search_code', 'list_directory'],  # Block analysis tools
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _intervene_circular_dependency(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in circular dependency"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 CIRCULAR DEPENDENCY DETECTED - INTERVENTION REQUIRED

{summary}

A circular dependency exists in the code structure.

IMMEDIATE ACTIONS REQUIRED:
1. IDENTIFY the circular dependency chain
2. BREAK the cycle by:
   - Moving shared code to a separate module
   - Using dependency injection
   - Refactoring to remove the circular reference
3. CONSULT the Pattern Analyst specialist for refactoring suggestions

CRITICAL: Circular dependencies prevent proper code organization and testing.

If you need help designing the refactoring, use the 'ask' tool to request user guidance.
"""
        
        return {
            'intervention_type': 'circular_dependency',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['consult_specialist', 'create_file', 'str_replace', 'ask'],
            'blocked_tools': [],
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _intervene_state_cycle(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in state cycle"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 STATE CYCLE DETECTED - INTERVENTION REQUIRED

{summary}

The system is cycling through the same states repeatedly.

IMMEDIATE ACTIONS REQUIRED:
1. BREAK the cycle by trying a fundamentally different approach
2. CONSULT a specialist for a fresh perspective
3. CONSIDER if the current strategy is viable at all
4. RESET your approach and start with a different strategy

CRITICAL: The current execution path is circular. You need to exit the cycle.

Options:
- Try a completely different tool or technique
- Consult the Root Cause Analyst for strategic guidance
- Use the 'ask' tool to request user guidance on a new approach
"""
        
        return {
            'intervention_type': 'state_cycle',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['consult_specialist', 'ask'],
            'blocked_tools': [],
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _intervene_pattern_repetition(
        self,
        detection: LoopDetection,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Intervene in pattern repetition"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 PATTERN REPETITION DETECTED - INTERVENTION REQUIRED

{summary}

A complex multi-step pattern is repeating without making progress.

IMMEDIATE ACTIONS REQUIRED:
1. STOP the current sequence of actions
2. ANALYZE why the pattern isn't working
3. CONSULT a specialist for a different perspective
4. TRY a completely different approach

CRITICAL: Repeating the same pattern won't lead to different results.

You must break out of this pattern by:
- Using different tools
- Approaching the problem from a different angle
- Consulting specialists for fresh insights
- Asking the user for guidance if you're stuck
"""
        
        return {
            'intervention_type': 'pattern_repetition',
            'severity': detection.severity,
            'guidance': guidance,
            'suggested_tools': ['consult_specialist', 'ask'],
            'blocked_tools': [],
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _generic_intervention(
        self,
        all_detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Generic intervention for unknown loop types"""
        summary = self.detector.get_loop_summary(all_detections)
        
        guidance = f"""
🛑 LOOP DETECTED - INTERVENTION REQUIRED

{summary}

IMMEDIATE ACTIONS REQUIRED:
1. STOP the current approach
2. ANALYZE what's not working
3. TRY a different strategy
4. CONSULT a specialist if needed
5. ASK the user for guidance if stuck

CRITICAL: The current approach is not making progress. You must try something different.
"""
        
        return {
            'intervention_type': 'generic',
            'severity': all_detections[0].severity,
            'guidance': guidance,
            'suggested_tools': ['ask', 'consult_specialist'],
            'blocked_tools': [],
            'detections': [d.to_dict() for d in all_detections]
        }
    
    def _escalate_to_user(
        self,
        detections: List[LoopDetection]
    ) -> Dict[str, Any]:
        """Escalate to user after multiple failed interventions"""
        summary = self.detector.get_loop_summary(detections)
        
        guidance = f"""
🚨 ESCALATION TO USER REQUIRED 🚨

Multiple intervention attempts have failed. The system is stuck in a loop.

{summary}

INTERVENTION HISTORY:
- Intervention attempts: {self.intervention_count}
- Maximum attempts reached: {self.max_interventions}

REQUIRED ACTION:
You MUST use the 'ask' tool to request user guidance.

Explain to the user:
1. What you've been trying to do
2. What loops have been detected
3. What interventions you've tried
4. What guidance you need to proceed

DO NOT attempt any more actions without user input.
"""
        
        return {
            'intervention_type': 'escalation',
            'severity': 'critical',
            'guidance': guidance,
            'suggested_tools': ['ask'],
            'blocked_tools': ['str_replace', 'full_file_rewrite', 'create_file', 'execute_command'],
            'requires_user_input': True,
            'detections': [d.to_dict() for d in detections]
        }
    
    def reset_intervention_count(self):
        """Reset intervention counter (call after successful progress)"""
        self.intervention_count = 0
        self.logger.info("Intervention counter reset - progress detected")
    
    def get_intervention_status(self) -> Dict[str, Any]:
        """Get current intervention status"""
        return {
            'intervention_count': self.intervention_count,
            'max_interventions': self.max_interventions,
            'interventions_remaining': self.max_interventions - self.intervention_count,
            'escalation_imminent': self.intervention_count >= self.max_interventions - 1
        }