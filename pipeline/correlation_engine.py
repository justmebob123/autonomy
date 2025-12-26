"""
Correlation Engine for Cross-Component Analysis

This module correlates findings across all troubleshooting components to identify
deeper relationships and patterns that aren't visible from individual analyses.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re


class CorrelationEngine:
    """
    Correlates findings across all system components.
    
    This engine identifies relationships between:
    - Configuration changes and errors
    - Code changes and failures
    - Performance degradation and architectural issues
    - Error patterns and call chain complexity
    """
    
    def __init__(self):
        """Initialize the correlation engine."""
        self.findings = defaultdict(list)
        self.correlations = []
        self.confidence_threshold = 0.7
        
    def add_finding(self, component: str, finding: Dict[str, Any]):
        """
        Add a finding from any component.
        
        Args:
            component: Name of the component (e.g., 'log_analyzer')
            finding: Finding dictionary with details
        """
        finding['component'] = component
        finding['timestamp'] = finding.get('timestamp', datetime.now().isoformat())
        self.findings[component].append(finding)
    
    def correlate(self) -> List[Dict[str, Any]]:
        """
        Find correlations across all components.
        
        Returns:
            List of correlation dictionaries
        """
        self.correlations = []
        
        # Run all correlation analyses
        self._correlate_config_errors()
        self._correlate_changes_errors()
        self._correlate_architecture_performance()
        self._correlate_call_chain_errors()
        self._correlate_temporal_patterns()
        
        # Sort by confidence
        self.correlations.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return self.correlations
    
    def _correlate_config_errors(self):
        """Correlate configuration changes with errors."""
        config_findings = self.findings.get('config_investigator', [])
        log_findings = self.findings.get('log_analyzer', [])
        
        for config in config_findings:
            if config.get('type') != 'issue':
                continue
                
            for error in log_findings:
                if error.get('type') != 'error':
                    continue
                
                # Check if error message mentions config-related terms
                error_msg = error.get('message', '').lower()
                config_path = config.get('path', '').lower()
                
                if any(term in error_msg for term in ['config', 'configuration', 'setting']):
                    confidence = self._calculate_text_similarity(
                        config_path,
                        error_msg
                    )
                    
                    if confidence > self.confidence_threshold:
                        self.correlations.append({
                            'type': 'config_error_correlation',
                            'config': config,
                            'error': error,
                            'confidence': confidence,
                            'description': f"Configuration issue in {config_path} may be causing errors",
                            'recommendation': f"Review and fix configuration in {config_path}"
                        })
    
    def _correlate_changes_errors(self):
        """Correlate code changes with errors."""
        change_findings = self.findings.get('change_history_analyzer', [])
        log_findings = self.findings.get('log_analyzer', [])
        
        for change in change_findings:
            if change.get('type') != 'risky_change':
                continue
            
            change_time = self._parse_timestamp(change.get('date', ''))
            if not change_time:
                continue
            
            # Find errors that occurred after this change
            related_errors = []
            for error in log_findings:
                error_time = self._parse_timestamp(error.get('timestamp', ''))
                if error_time and error_time > change_time:
                    time_diff = (error_time - change_time).total_seconds()
                    if time_diff < 3600:  # Within 1 hour
                        related_errors.append(error)
            
            if related_errors:
                confidence = min(0.9, 0.5 + len(related_errors) * 0.1)
                
                self.correlations.append({
                    'type': 'change_error_correlation',
                    'change': change,
                    'errors': related_errors,
                    'confidence': confidence,
                    'description': f"Risky change '{change.get('message', '')}' may have introduced {len(related_errors)} errors",
                    'recommendation': f"Consider reverting commit {change.get('commit', '')}"
                })
    
    def _correlate_architecture_performance(self):
        """Correlate architectural issues with performance problems."""
        arch_findings = self.findings.get('architecture_analyzer', [])
        
        for arch_issue in arch_findings:
            if arch_issue.get('type') != 'issue':
                continue
            
            issue_type = arch_issue.get('issue_type', '')
            
            # Map architectural issues to likely performance impacts
            performance_impact = {
                'circular_dependency': 'high',
                'deep_nesting': 'medium',
                'large_file': 'medium',
                'complex_structure': 'low'
            }
            
            impact = performance_impact.get(issue_type, 'unknown')
            
            if impact in ['high', 'medium']:
                confidence = 0.8 if impact == 'high' else 0.6
                
                self.correlations.append({
                    'type': 'architecture_performance_correlation',
                    'architecture_issue': arch_issue,
                    'impact': impact,
                    'confidence': confidence,
                    'description': f"Architectural issue '{issue_type}' likely causing {impact} performance impact",
                    'recommendation': f"Refactor to address {issue_type}"
                })
    
    def _correlate_call_chain_errors(self):
        """Correlate call chain complexity with errors."""
        call_findings = self.findings.get('call_chain_tracer', [])
        log_findings = self.findings.get('log_analyzer', [])
        
        # Find error-prone functions
        error_prone = [f for f in call_findings if f.get('type') == 'error_prone_function']
        
        for func in error_prone:
            func_name = func.get('function', '')
            risk_score = func.get('risk_score', 0)
            
            # Find errors mentioning this function
            related_errors = []
            for error in log_findings:
                error_msg = error.get('message', '')
                if func_name in error_msg:
                    related_errors.append(error)
            
            if related_errors:
                confidence = min(0.95, 0.6 + risk_score * 0.1)
                
                self.correlations.append({
                    'type': 'call_chain_error_correlation',
                    'function': func,
                    'errors': related_errors,
                    'confidence': confidence,
                    'description': f"Error-prone function '{func_name}' (risk score: {risk_score}) is causing {len(related_errors)} errors",
                    'recommendation': f"Refactor or add error handling to {func_name}"
                })
    
    def _correlate_temporal_patterns(self):
        """Correlate temporal patterns across all findings."""
        all_findings = []
        for component, findings in self.findings.items():
            for finding in findings:
                timestamp = self._parse_timestamp(finding.get('timestamp', ''))
                if timestamp:
                    all_findings.append({
                        'component': component,
                        'finding': finding,
                        'timestamp': timestamp
                    })
        
        # Sort by timestamp
        all_findings.sort(key=lambda x: x['timestamp'])
        
        # Look for clusters of events
        if len(all_findings) < 3:
            return
        
        for i in range(len(all_findings) - 2):
            window = all_findings[i:i+3]
            time_span = (window[-1]['timestamp'] - window[0]['timestamp']).total_seconds()
            
            # If 3+ events within 5 minutes, it's a cluster
            if time_span < 300:
                components = [w['component'] for w in window]
                if len(set(components)) >= 2:  # Multiple components involved
                    self.correlations.append({
                        'type': 'temporal_cluster',
                        'events': window,
                        'time_span': time_span,
                        'confidence': 0.75,
                        'description': f"Cluster of {len(window)} events across {len(set(components))} components within {time_span:.0f} seconds",
                        'recommendation': "Investigate cascading failure or common root cause"
                    })
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple word-based similarity
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string to datetime.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Datetime object or None
        """
        if not timestamp_str:
            return None
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%d/%m/%Y %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except:
                continue
        
        return None
    
    def get_high_confidence_correlations(self, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """
        Get high-confidence correlations.
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of high-confidence correlations
        """
        return [c for c in self.correlations if c.get('confidence', 0) >= min_confidence]
    
    def get_correlations_by_type(self, correlation_type: str) -> List[Dict[str, Any]]:
        """
        Get correlations of a specific type.
        
        Args:
            correlation_type: Type of correlation
            
        Returns:
            List of correlations of that type
        """
        return [c for c in self.correlations if c.get('type') == correlation_type]
    
    def format_report(self) -> str:
        """
        Format correlations as a readable report.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("CORRELATION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append(f"Total Correlations Found: {len(self.correlations)}")
        report.append(f"High Confidence (>0.8): {len(self.get_high_confidence_correlations())}")
        report.append("")
        
        # Group by type
        by_type = defaultdict(list)
        for corr in self.correlations:
            by_type[corr.get('type', 'unknown')].append(corr)
        
        for corr_type, correlations in by_type.items():
            report.append(f"{corr_type.upper().replace('_', ' ')}:")
            report.append("-" * 80)
            
            for corr in correlations[:5]:  # Show top 5 of each type
                report.append(f"  • Confidence: {corr.get('confidence', 0):.2f}")
                report.append(f"    {corr.get('description', 'No description')}")
                report.append(f"    Recommendation: {corr.get('recommendation', 'None')}")
                report.append("")
            
            if len(correlations) > 5:
                report.append(f"  ... and {len(correlations) - 5} more")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def clear(self):
        """Clear all findings and correlations."""
        self.findings = defaultdict(list)
        self.correlations = []