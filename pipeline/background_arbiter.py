"""
Background Arbiter Observer

Runs in a separate thread, watches conversation streams, and only
intercedes when detecting problems or confusion.

The arbiter does NOT make phase decisions - it observes and assists.
"""

import threading
import time
import queue
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .logging_setup import get_logger


class ConversationEvent:
    """Represents an event in a conversation."""
    
    def __init__(self, phase: str, role: str, content: str, metadata: Dict = None):
        self.phase = phase
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class BackgroundArbiter:
    """
    Background arbiter that watches conversations and intercedes when needed.
    
    Runs in a separate thread and monitors conversation streams for:
    - Overly complex prompts that need simplification
    - Confusion or unclear communication
    - Repeated failures indicating need for intervention
    - Requests for clarification
    
    Does NOT:
    - Make phase transition decisions
    - Control the workflow
    - Replace the coordinator
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize background arbiter.
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        
        # Event queue for conversation monitoring
        self.event_queue = queue.Queue()
        
        # Monitoring state
        self.running = False
        self.thread = None
        
        # Conversation history per phase
        self.phase_conversations = {}
        
        # Intervention tracking
        self.interventions = []
        
        # Pattern detection
        self.confusion_patterns = [
            r'(?:i don\'t understand|unclear|confusing|not sure what)',
            r'(?:what do you mean|can you clarify|please explain)',
            r'(?:i\'m confused|this is confusing|unclear instructions)',
        ]
        
        self.complexity_indicators = [
            r'(?:too complex|overly complicated|too much information)',
            r'(?:simplify|make it simpler|break it down)',
            r'(?:overwhelming|too many|can\'t process)',
        ]
        
        self.failure_patterns = [
            r'(?:failed again|still failing|keeps failing)',
            r'(?:same error|repeated error|error persists)',
            r'(?:not working|doesn\'t work|won\'t work)',
        ]
    
    def start(self):
        """Start the background arbiter thread."""
        if self.running:
            self.logger.warning("Background arbiter already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info("🔍 Background arbiter started")
    
    def stop(self):
        """Stop the background arbiter thread."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("🛑 Background arbiter stopped")
    
    def add_event(self, event: ConversationEvent):
        """
        Add a conversation event for monitoring.
        
        Args:
            event: ConversationEvent to monitor
        """
        self.event_queue.put(event)
    
    def _monitor_loop(self):
        """Main monitoring loop running in background thread."""
        self.logger.info("🔍 Arbiter monitoring loop started")
        
        while self.running:
            try:
                # Get events from queue (with timeout to allow checking self.running)
                try:
                    event = self.event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the event
                self._process_event(event)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in arbiter monitoring loop: {e}")
                time.sleep(1)
        
        self.logger.info("🔍 Arbiter monitoring loop stopped")
    
    def _process_event(self, event: ConversationEvent):
        """
        Process a conversation event and check for intervention needs.
        
        Args:
            event: ConversationEvent to process
        """
        # Add to phase conversation history
        if event.phase not in self.phase_conversations:
            self.phase_conversations[event.phase] = []
        self.phase_conversations[event.phase].append(event)
        
        # Check for intervention needs
        intervention = self._check_for_intervention(event)
        
        if intervention:
            self._record_intervention(intervention)
            self.logger.info(f"🚨 Arbiter intervention: {intervention['type']}")
    
    def _check_for_intervention(self, event: ConversationEvent) -> Optional[Dict]:
        """
        Check if intervention is needed based on the event.
        
        Args:
            event: ConversationEvent to check
        
        Returns:
            Dict with intervention details if needed, None otherwise
        """
        import re
        
        content_lower = event.content.lower()
        
        # Check for confusion
        for pattern in self.confusion_patterns:
            if re.search(pattern, content_lower):
                return {
                    'type': 'confusion_detected',
                    'phase': event.phase,
                    'event': event,
                    'pattern': pattern,
                    'suggestion': 'Rephrase or clarify the previous message'
                }
        
        # Check for complexity
        for pattern in self.complexity_indicators:
            if re.search(pattern, content_lower):
                return {
                    'type': 'complexity_detected',
                    'phase': event.phase,
                    'event': event,
                    'pattern': pattern,
                    'suggestion': 'Simplify the prompt or break into smaller steps'
                }
        
        # Check for repeated failures
        for pattern in self.failure_patterns:
            if re.search(pattern, content_lower):
                # Check recent history for repeated failures
                recent_events = self._get_recent_events(event.phase, limit=5)
                failure_count = sum(1 for e in recent_events 
                                   if any(re.search(p, e.content.lower()) 
                                         for p in self.failure_patterns))
                
                if failure_count >= 2:
                    return {
                        'type': 'repeated_failures',
                        'phase': event.phase,
                        'event': event,
                        'failure_count': failure_count,
                        'suggestion': 'Consider alternative approach or request specialist help'
                    }
        
        return None
    
    def _get_recent_events(self, phase: str, limit: int = 10) -> List[ConversationEvent]:
        """
        Get recent events for a phase.
        
        Args:
            phase: Phase name
            limit: Maximum number of events to return
        
        Returns:
            List of recent ConversationEvents
        """
        if phase not in self.phase_conversations:
            return []
        
        return self.phase_conversations[phase][-limit:]
    
    def _record_intervention(self, intervention: Dict):
        """
        Record an intervention.
        
        Args:
            intervention: Intervention details
        """
        intervention['timestamp'] = datetime.now()
        self.interventions.append(intervention)
        
        # Keep only last 100 interventions
        if len(self.interventions) > 100:
            self.interventions = self.interventions[-100:]
    
    def get_intervention_summary(self) -> Dict[str, Any]:
        """
        Get summary of interventions.
        
        Returns:
            Dict with intervention statistics
        """
        if not self.interventions:
            return {
                'total': 0,
                'by_type': {},
                'by_phase': {}
            }
        
        by_type = {}
        by_phase = {}
        
        for intervention in self.interventions:
            # Count by type
            itype = intervention['type']
            by_type[itype] = by_type.get(itype, 0) + 1
            
            # Count by phase
            phase = intervention['phase']
            by_phase[phase] = by_phase.get(phase, 0) + 1
        
        return {
            'total': len(self.interventions),
            'by_type': by_type,
            'by_phase': by_phase,
            'recent': self.interventions[-5:]
        }
    
    def should_intervene(self, phase: str) -> Optional[Dict]:
        """
        Check if arbiter should intervene in a phase.
        
        Args:
            phase: Phase name
        
        Returns:
            Dict with intervention recommendation if needed, None otherwise
        """
        # Get recent interventions for this phase
        recent = [i for i in self.interventions[-10:] if i['phase'] == phase]
        
        if not recent:
            return None
        
        # If multiple interventions in short time, recommend action
        if len(recent) >= 3:
            return {
                'should_intervene': True,
                'reason': f'{len(recent)} interventions detected in recent history',
                'interventions': recent,
                'recommendation': 'Consider pausing for user input or changing approach'
            }
        
        return None