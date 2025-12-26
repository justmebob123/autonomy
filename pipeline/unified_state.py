"""
Unified State Management System

This module provides centralized state management across all pipeline components,
enabling deep integration and context sharing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import pickle
from collections import defaultdict


class UnifiedState:
    """
    Unified state management across all components.
    
    This class maintains a complete view of the system state including:
    - Phase states and transitions
    - Error history and patterns
    - Fix history and effectiveness
    - Performance metrics
    - Learned patterns
    - Troubleshooting results
    - Cross-component correlations
    """
    
    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize unified state.
        
        Args:
            state_file: Optional path to persist state
        """
        self.state_file = state_file
        
        # Core state components
        self.phase_states = {}
        self.error_history = []
        self.fix_history = []
        self.performance_metrics = defaultdict(list)
        self.learned_patterns = {}
        self.troubleshooting_results = []
        self.correlations = []
        
        # Metadata
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.version = "1.0.0"
        
        # Load existing state if available
        if state_file and state_file.exists():
            self.load()
    
    def update_from_phase(self, phase_name: str, state: Dict[str, Any]):
        """
        Update state from a phase.
        
        Args:
            phase_name: Name of the phase
            state: State dictionary from the phase
        """
        self.phase_states[phase_name] = {
            'state': state,
            'timestamp': datetime.now().isoformat(),
            'version': self.version
        }
        self.last_updated = datetime.now()
        self._auto_save()
    
    def add_error(self, error: Dict[str, Any]):
        """
        Add an error to history.
        
        Args:
            error: Error dictionary with details
        """
        error['timestamp'] = datetime.now().isoformat()
        error['id'] = len(self.error_history)
        self.error_history.append(error)
        self.last_updated = datetime.now()
        self._auto_save()
    
    def add_fix(self, fix: Dict[str, Any]):
        """
        Add a fix to history.
        
        Args:
            fix: Fix dictionary with details
        """
        fix['timestamp'] = datetime.now().isoformat()
        fix['id'] = len(self.fix_history)
        self.fix_history.append(fix)
        self.last_updated = datetime.now()
        self._auto_save()
    
    def add_performance_metric(self, metric_name: str, value: float):
        """
        Add a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        self.performance_metrics[metric_name].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
        self._auto_save()
    
    def learn_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """
        Learn a new pattern.
        
        Args:
            pattern_name: Name of the pattern
            pattern_data: Pattern data
        """
        if pattern_name not in self.learned_patterns:
            self.learned_patterns[pattern_name] = []
        
        pattern_data['timestamp'] = datetime.now().isoformat()
        pattern_data['id'] = len(self.learned_patterns[pattern_name])
        self.learned_patterns[pattern_name].append(pattern_data)
        self.last_updated = datetime.now()
        self._auto_save()
    
    def update_from_troubleshooting(self, results: Dict[str, Any]):
        """
        Update state from troubleshooting.
        
        Args:
            results: Troubleshooting results dictionary
        """
        results['timestamp'] = datetime.now().isoformat()
        results['id'] = len(self.troubleshooting_results)
        self.troubleshooting_results.append(results)
        self.last_updated = datetime.now()
        self._auto_save()
    
    def add_correlation(self, correlation: Dict[str, Any]):
        """
        Add a correlation between components.
        
        Args:
            correlation: Correlation data
        """
        correlation['timestamp'] = datetime.now().isoformat()
        correlation['id'] = len(self.correlations)
        self.correlations.append(correlation)
        self.last_updated = datetime.now()
        self._auto_save()
    
    def get_full_context(self) -> Dict[str, Any]:
        """
        Get complete system context.
        
        Returns:
            Dictionary containing all state information
        """
        return {
            'metadata': {
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'version': self.version
            },
            'phases': self.phase_states,
            'errors': self.error_history,
            'fixes': self.fix_history,
            'metrics': dict(self.performance_metrics),
            'patterns': self.learned_patterns,
            'troubleshooting': self.troubleshooting_results,
            'correlations': self.correlations
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent errors
        """
        return self.error_history[-limit:]
    
    def get_recent_fixes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent fixes.
        
        Args:
            limit: Maximum number of fixes to return
            
        Returns:
            List of recent fixes
        """
        return self.fix_history[-limit:]
    
    def get_error_patterns(self) -> Dict[str, int]:
        """
        Get error patterns and their frequencies.
        
        Returns:
            Dictionary of error types and counts
        """
        patterns = defaultdict(int)
        for error in self.error_history:
            error_type = error.get('type', 'unknown')
            patterns[error_type] += 1
        return dict(patterns)
    
    def get_fix_effectiveness(self) -> Dict[str, float]:
        """
        Calculate fix effectiveness.
        
        Returns:
            Dictionary of fix types and their success rates
        """
        effectiveness = defaultdict(lambda: {'total': 0, 'successful': 0})
        
        for fix in self.fix_history:
            fix_type = fix.get('type', 'unknown')
            effectiveness[fix_type]['total'] += 1
            if fix.get('successful', False):
                effectiveness[fix_type]['successful'] += 1
        
        return {
            fix_type: stats['successful'] / stats['total'] if stats['total'] > 0 else 0
            for fix_type, stats in effectiveness.items()
        }
    
    def get_performance_trends(self, metric_name: str) -> List[float]:
        """
        Get performance trends for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            List of metric values over time
        """
        return [m['value'] for m in self.performance_metrics.get(metric_name, [])]
    
    def save(self):
        """Save state to disk."""
        if not self.state_file:
            return
        
        try:
            # Save as JSON for human readability
            json_file = self.state_file.with_suffix('.json')
            with open(json_file, 'w') as f:
                json.dump(self.get_full_context(), f, indent=2)
            
            # Also save as pickle for complete state preservation
            pickle_file = self.state_file.with_suffix('.pkl')
            with open(pickle_file, 'wb') as f:
                pickle.dump(self, f)
                
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")
    
    def load(self):
        """Load state from disk."""
        if not self.state_file:
            return
        
        try:
            # Try to load from pickle first (complete state)
            pickle_file = self.state_file.with_suffix('.pkl')
            if pickle_file.exists():
                with open(pickle_file, 'rb') as f:
                    loaded_state = pickle.load(f)
                    self.__dict__.update(loaded_state.__dict__)
                return
            
            # Fall back to JSON
            json_file = self.state_file.with_suffix('.json')
            if json_file.exists():
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    self.phase_states = data.get('phases', {})
                    self.error_history = data.get('errors', [])
                    self.fix_history = data.get('fixes', [])
                    self.performance_metrics = defaultdict(list, data.get('metrics', {}))
                    self.learned_patterns = data.get('patterns', {})
                    self.troubleshooting_results = data.get('troubleshooting', [])
                    self.correlations = data.get('correlations', [])
                    
        except Exception as e:
            print(f"Warning: Failed to load state: {e}")
    
    def _auto_save(self):
        """Automatically save state if configured."""
        if self.state_file:
            self.save()
    
    def clear(self):
        """Clear all state."""
        self.phase_states = {}
        self.error_history = []
        self.fix_history = []
        self.performance_metrics = defaultdict(list)
        self.learned_patterns = {}
        self.troubleshooting_results = []
        self.correlations = []
        self.last_updated = datetime.now()
        self._auto_save()
    
    def export_summary(self) -> str:
        """
        Export a human-readable summary.
        
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("=" * 80)
        summary.append("UNIFIED STATE SUMMARY")
        summary.append("=" * 80)
        summary.append("")
        
        summary.append(f"Created: {self.created_at}")
        summary.append(f"Last Updated: {self.last_updated}")
        summary.append(f"Version: {self.version}")
        summary.append("")
        
        summary.append(f"Phases Tracked: {len(self.phase_states)}")
        summary.append(f"Total Errors: {len(self.error_history)}")
        summary.append(f"Total Fixes: {len(self.fix_history)}")
        summary.append(f"Metrics Tracked: {len(self.performance_metrics)}")
        summary.append(f"Patterns Learned: {sum(len(p) for p in self.learned_patterns.values())}")
        summary.append(f"Troubleshooting Sessions: {len(self.troubleshooting_results)}")
        summary.append(f"Correlations Found: {len(self.correlations)}")
        summary.append("")
        
        # Error patterns
        if self.error_history:
            summary.append("Error Patterns:")
            patterns = self.get_error_patterns()
            for error_type, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary.append(f"  • {error_type}: {count} occurrences")
            summary.append("")
        
        # Fix effectiveness
        if self.fix_history:
            summary.append("Fix Effectiveness:")
            effectiveness = self.get_fix_effectiveness()
            for fix_type, rate in sorted(effectiveness.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary.append(f"  • {fix_type}: {rate*100:.1f}% success rate")
            summary.append("")
        
        summary.append("=" * 80)
        
        return "\n".join(summary)