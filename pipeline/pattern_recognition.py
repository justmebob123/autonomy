"""
Pattern Recognition System

Analyzes execution patterns to identify:
- Common failure patterns
- Successful approaches
- Tool usage patterns
- Phase transition patterns
- Optimization opportunities
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import json

from .logging_setup import get_logger


class ExecutionPattern:
    """Represents a recognized execution pattern."""
    
    def __init__(self, pattern_type: str, pattern_data: Dict, confidence: float):
        self.pattern_type = pattern_type
        self.pattern_data = pattern_data
        self.confidence = confidence
        self.occurrences = 1
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'pattern_type': self.pattern_type,
            'pattern_data': self.pattern_data,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }


class PatternRecognitionSystem:
    """
    Analyzes execution history to identify patterns and learn from experience.
    
    Tracks:
    - Tool usage patterns (which tools work well together)
    - Failure patterns (what causes failures)
    - Success patterns (what leads to success)
    - Phase transition patterns (when to move between phases)
    - Optimization opportunities (where to improve)
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize pattern recognition system.
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        
        # Pattern storage
        self.patterns = {
            'tool_usage': [],
            'failures': [],
            'successes': [],
            'phase_transitions': [],
            'optimizations': []
        }
        
        # Execution history
        self.execution_history = []
        
        # Statistics
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'tool_calls': Counter(),
            'phase_durations': defaultdict(list)
        }
    
    def record_execution(self, execution_data: Dict):
        """
        Record an execution for pattern analysis.
        
        Args:
            execution_data: Dict with execution details
        """
        execution_data['timestamp'] = datetime.now()
        self.execution_history.append(execution_data)
        
        # Update statistics
        self.stats['total_executions'] += 1
        if execution_data.get('success', False):
            self.stats['successful_executions'] += 1
        else:
            self.stats['failed_executions'] += 1
        
        # Track tool usage
        for tool_call in execution_data.get('tool_calls', []):
            tool_name = tool_call.get('function', {}).get('name', 'unknown')
            self.stats['tool_calls'][tool_name] += 1
        
        # Track phase duration
        phase = execution_data.get('phase', 'unknown')
        duration = execution_data.get('duration', 0)
        self.stats['phase_durations'][phase].append(duration)
        
        # Analyze for patterns
        self._analyze_execution(execution_data)
    
    def _analyze_execution(self, execution_data: Dict):
        """
        Analyze execution for patterns.
        
        Args:
            execution_data: Execution data to analyze
        """
        # Analyze tool usage patterns
        self._analyze_tool_patterns(execution_data)
        
        # Analyze failure patterns
        if not execution_data.get('success', False):
            self._analyze_failure_patterns(execution_data)
        else:
            self._analyze_success_patterns(execution_data)
        
        # Analyze phase transition patterns
        self._analyze_phase_patterns(execution_data)
    
    def _analyze_tool_patterns(self, execution_data: Dict):
        """Analyze tool usage patterns."""
        tool_calls = execution_data.get('tool_calls', [])
        if len(tool_calls) < 2:
            return
        
        # Look for tool sequences
        tool_sequence = [tc.get('function', {}).get('name', 'unknown') 
                        for tc in tool_calls]
        
        # Check if this sequence has been successful before
        success = execution_data.get('success', False)
        
        # Create pattern
        pattern = ExecutionPattern(
            pattern_type='tool_sequence',
            pattern_data={
                'sequence': tool_sequence,
                'success': success,
                'phase': execution_data.get('phase', 'unknown')
            },
            confidence=0.7
        )
        
        # Check if similar pattern exists
        existing = self._find_similar_pattern('tool_usage', pattern)
        if existing:
            existing.occurrences += 1
            existing.last_seen = datetime.now()
            existing.confidence = min(0.95, existing.confidence + 0.05)
        else:
            self.patterns['tool_usage'].append(pattern)
    
    def _analyze_failure_patterns(self, execution_data: Dict):
        """Analyze failure patterns."""
        errors = execution_data.get('errors', [])
        if not errors:
            return
        
        for error in errors:
            error_type = error.get('type', 'unknown')
            error_message = error.get('message', '')
            
            # Create failure pattern
            pattern = ExecutionPattern(
                pattern_type='failure',
                pattern_data={
                    'error_type': error_type,
                    'error_message': error_message[:100],
                    'phase': execution_data.get('phase', 'unknown'),
                    'tool_calls': [tc.get('function', {}).get('name', 'unknown') 
                                  for tc in execution_data.get('tool_calls', [])]
                },
                confidence=0.8
            )
            
            # Check if similar pattern exists
            existing = self._find_similar_pattern('failures', pattern)
            if existing:
                existing.occurrences += 1
                existing.last_seen = datetime.now()
                existing.confidence = min(0.95, existing.confidence + 0.05)
            else:
                self.patterns['failures'].append(pattern)
    
    def _analyze_success_patterns(self, execution_data: Dict):
        """Analyze success patterns."""
        # Create success pattern
        pattern = ExecutionPattern(
            pattern_type='success',
            pattern_data={
                'phase': execution_data.get('phase', 'unknown'),
                'tool_calls': [tc.get('function', {}).get('name', 'unknown') 
                              for tc in execution_data.get('tool_calls', [])],
                'duration': execution_data.get('duration', 0)
            },
            confidence=0.7
        )
        
        # Check if similar pattern exists
        existing = self._find_similar_pattern('successes', pattern)
        if existing:
            existing.occurrences += 1
            existing.last_seen = datetime.now()
            existing.confidence = min(0.95, existing.confidence + 0.05)
        else:
            self.patterns['successes'].append(pattern)
    
    def _analyze_phase_patterns(self, execution_data: Dict):
        """Analyze phase transition patterns."""
        current_phase = execution_data.get('phase', 'unknown')
        next_phase = execution_data.get('next_phase')
        
        if not next_phase:
            return
        
        # Create phase transition pattern
        pattern = ExecutionPattern(
            pattern_type='phase_transition',
            pattern_data={
                'from_phase': current_phase,
                'to_phase': next_phase,
                'success': execution_data.get('success', False),
                'reason': execution_data.get('transition_reason', 'unknown')
            },
            confidence=0.7
        )
        
        # Check if similar pattern exists
        existing = self._find_similar_pattern('phase_transitions', pattern)
        if existing:
            existing.occurrences += 1
            existing.last_seen = datetime.now()
            existing.confidence = min(0.95, existing.confidence + 0.05)
        else:
            self.patterns['phase_transitions'].append(pattern)
    
    def _find_similar_pattern(self, pattern_type: str, pattern: ExecutionPattern) -> Optional[ExecutionPattern]:
        """
        Find similar existing pattern.
        
        Args:
            pattern_type: Type of pattern
            pattern: Pattern to match
        
        Returns:
            Existing pattern if found, None otherwise
        """
        for existing in self.patterns[pattern_type]:
            if self._patterns_similar(existing, pattern):
                return existing
        return None
    
    def _patterns_similar(self, p1: ExecutionPattern, p2: ExecutionPattern) -> bool:
        """Check if two patterns are similar."""
        if p1.pattern_type != p2.pattern_type:
            return False
        
        # Compare based on pattern type
        if p1.pattern_type == 'tool_sequence':
            return p1.pattern_data.get('sequence') == p2.pattern_data.get('sequence')
        elif p1.pattern_type == 'failure':
            return (p1.pattern_data.get('error_type') == p2.pattern_data.get('error_type') and
                   p1.pattern_data.get('phase') == p2.pattern_data.get('phase'))
        elif p1.pattern_type == 'success':
            return (p1.pattern_data.get('phase') == p2.pattern_data.get('phase') and
                   p1.pattern_data.get('tool_calls') == p2.pattern_data.get('tool_calls'))
        elif p1.pattern_type == 'phase_transition':
            return (p1.pattern_data.get('from_phase') == p2.pattern_data.get('from_phase') and
                   p1.pattern_data.get('to_phase') == p2.pattern_data.get('to_phase'))
        
        return False
    
    def get_recommendations(self, context: Dict) -> List[Dict]:
        """
        Get recommendations based on recognized patterns.
        
        Args:
            context: Current execution context
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        current_phase = context.get('phase', 'unknown')
        
        # Check for known failure patterns
        for pattern in self.patterns['failures']:
            if (pattern.pattern_data.get('phase') == current_phase and
                pattern.confidence > 0.7 and
                pattern.occurrences >= 3):
                recommendations.append({
                    'type': 'avoid_failure',
                    'confidence': pattern.confidence,
                    'message': f"Avoid pattern that led to {pattern.pattern_data.get('error_type')} errors",
                    'pattern': pattern.to_dict()
                })
        
        # Check for successful patterns
        for pattern in self.patterns['successes']:
            if (pattern.pattern_data.get('phase') == current_phase and
                pattern.confidence > 0.8 and
                pattern.occurrences >= 5):
                recommendations.append({
                    'type': 'use_success_pattern',
                    'confidence': pattern.confidence,
                    'message': f"Use successful tool sequence: {', '.join(pattern.pattern_data.get('tool_calls', []))}",
                    'pattern': pattern.to_dict()
                })
        
        # Check for phase transition patterns
        for pattern in self.patterns['phase_transitions']:
            if (pattern.pattern_data.get('from_phase') == current_phase and
                pattern.confidence > 0.7):
                recommendations.append({
                    'type': 'phase_transition',
                    'confidence': pattern.confidence,
                    'message': f"Consider transitioning to {pattern.pattern_data.get('to_phase')}",
                    'pattern': pattern.to_dict()
                })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:5]  # Return top 5
    
    def get_statistics(self) -> Dict:
        """Get pattern recognition statistics."""
        return {
            'total_executions': self.stats['total_executions'],
            'success_rate': (self.stats['successful_executions'] / 
                           max(1, self.stats['total_executions'])),
            'patterns_recognized': {
                'tool_usage': len(self.patterns['tool_usage']),
                'failures': len(self.patterns['failures']),
                'successes': len(self.patterns['successes']),
                'phase_transitions': len(self.patterns['phase_transitions'])
            },
            'top_tools': self.stats['tool_calls'].most_common(10),
            'average_phase_durations': {
                phase: sum(durations) / len(durations)
                for phase, durations in self.stats['phase_durations'].items()
                if durations
            }
        }
    
    def save_patterns(self):
        """Save patterns to disk."""
        patterns_file = self.project_dir / '.pipeline' / 'patterns.json'
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'patterns': {
                ptype: [p.to_dict() for p in patterns]
                for ptype, patterns in self.patterns.items()
            },
            'stats': {
                'total_executions': self.stats['total_executions'],
                'successful_executions': self.stats['successful_executions'],
                'failed_executions': self.stats['failed_executions'],
                'tool_calls': dict(self.stats['tool_calls'])
            }
        }
        
        with open(patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"💾 Saved {sum(len(p) for p in self.patterns.values())} patterns")
    
    def load_patterns(self):
        """Load patterns from disk."""
        patterns_file = self.project_dir / '.pipeline' / 'patterns.json'
        
        if not patterns_file.exists():
            return
        
        try:
            with open(patterns_file, 'r') as f:
                data = json.load(f)
            
            # Load patterns
            for ptype, pattern_list in data.get('patterns', {}).items():
                self.patterns[ptype] = [
                    ExecutionPattern(
                        pattern_type=p['pattern_type'],
                        pattern_data=p['pattern_data'],
                        confidence=p['confidence']
                    )
                    for p in pattern_list
                ]
            
            # Load stats
            stats = data.get('stats', {})
            self.stats['total_executions'] = stats.get('total_executions', 0)
            self.stats['successful_executions'] = stats.get('successful_executions', 0)
            self.stats['failed_executions'] = stats.get('failed_executions', 0)
            self.stats['tool_calls'] = Counter(stats.get('tool_calls', {}))
            
            self.logger.info(f"📂 Loaded {sum(len(p) for p in self.patterns.values())} patterns")
            
        except Exception as e:
            self.logger.error(f"Failed to load patterns: {e}")