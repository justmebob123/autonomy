#!/usr/bin/env python3
"""
Anomaly Detection System

Detects anomalies in the autonomy pipeline:
- Phase execution anomalies
- Task completion anomalies
- Resource usage anomalies
- Message pattern anomalies
- Objective health anomalies
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import math

@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    anomaly_type: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    description: str
    detected_at: datetime
    affected_component: str
    metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0

@dataclass
class AnomalyPattern:
    """Pattern of related anomalies"""
    pattern_id: str
    anomalies: List[Anomaly]
    pattern_type: str
    frequency: float
    impact_score: float
    root_cause_hypothesis: str

class AnomalyDetector:
    """
    Detects anomalies in pipeline execution.
    
    Uses statistical methods and pattern recognition to identify:
    - Execution time anomalies
    - Success rate anomalies
    - Resource usage anomalies
    - Message flow anomalies
    - Health degradation anomalies
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.phase_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.task_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.resource_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.message_metrics: deque = deque(maxlen=window_size)
        self.objective_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.detected_anomalies: List[Anomaly] = []
        self.anomaly_patterns: List[AnomalyPattern] = []
        
    def record_phase_metric(self, phase_name: str, duration: float, 
                           success: bool, context: Dict[str, Any]):
        """Record phase execution metric"""
        self.phase_metrics[phase_name].append({
            'timestamp': datetime.now(),
            'duration': duration,
            'success': success,
            'context': context
        })
        
    def record_task_metric(self, task_id: str, duration: float, 
                          success: bool, complexity: float):
        """Record task completion metric"""
        self.task_metrics[task_id].append({
            'timestamp': datetime.now(),
            'duration': duration,
            'success': success,
            'complexity': complexity
        })
        
    def record_resource_metric(self, component: str, memory_mb: float, 
                              cpu_percent: float):
        """Record resource usage metric"""
        self.resource_metrics[component].append({
            'timestamp': datetime.now(),
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent
        })
        
    def record_message_metric(self, message_count: int, 
                             message_types: Dict[str, int]):
        """Record message flow metric"""
        self.message_metrics.append({
            'timestamp': datetime.now(),
            'count': message_count,
            'types': message_types
        })
        
    def record_objective_metric(self, objective_id: str, health_score: float, 
                               task_count: int, issue_count: int):
        """Record objective health metric"""
        self.objective_metrics[objective_id].append({
            'timestamp': datetime.now(),
            'health_score': health_score,
            'task_count': task_count,
            'issue_count': issue_count
        })
        
    def detect_phase_anomalies(self, phase_name: str) -> List[Anomaly]:
        """
        Detect anomalies in phase execution.
        
        Checks for:
        - Execution time anomalies (too slow/fast)
        - Success rate drops
        - Repeated failures
        """
        anomalies = []
        metrics = list(self.phase_metrics.get(phase_name, []))
        
        if len(metrics) < 10:
            return anomalies  # Need more data
            
        # Check execution time anomalies
        durations = [m['duration'] for m in metrics]
        mean_duration = statistics.mean(durations)
        stdev_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        
        recent_duration = metrics[-1]['duration']
        
        # Z-score anomaly detection
        if stdev_duration > 0:
            z_score = abs(recent_duration - mean_duration) / stdev_duration
            
            if z_score > 3:  # 3 sigma rule
                severity = 'HIGH' if z_score > 4 else 'MEDIUM'
                anomalies.append(Anomaly(
                    anomaly_type='execution_time_anomaly',
                    severity=severity,
                    description=f'Phase {phase_name} execution time is {z_score:.1f} standard deviations from mean',
                    detected_at=datetime.now(),
                    affected_component=phase_name,
                    metrics={
                        'current_duration': recent_duration,
                        'mean_duration': mean_duration,
                        'z_score': z_score
                    },
                    recommendations=[
                        'Investigate performance bottlenecks',
                        'Check resource availability',
                        'Review recent code changes'
                    ],
                    confidence=min(0.9, z_score / 5)
                ))
                
        # Check success rate anomalies
        recent_window = metrics[-20:]  # Last 20 executions
        recent_success_rate = sum(1 for m in recent_window if m['success']) / len(recent_window)
        overall_success_rate = sum(1 for m in metrics if m['success']) / len(metrics)
        
        if recent_success_rate < overall_success_rate * 0.7:  # 30% drop
            anomalies.append(Anomaly(
                anomaly_type='success_rate_drop',
                severity='HIGH',
                description=f'Phase {phase_name} success rate dropped from {overall_success_rate:.1%} to {recent_success_rate:.1%}',
                detected_at=datetime.now(),
                affected_component=phase_name,
                metrics={
                    'recent_success_rate': recent_success_rate,
                    'overall_success_rate': overall_success_rate,
                    'drop_percentage': (overall_success_rate - recent_success_rate) * 100
                },
                recommendations=[
                    'Review recent failures',
                    'Check input data quality',
                    'Verify dependencies'
                ],
                confidence=0.85
            ))
            
        # Check for repeated failures
        recent_failures = [m for m in metrics[-10:] if not m['success']]
        if len(recent_failures) >= 5:
            anomalies.append(Anomaly(
                anomaly_type='repeated_failures',
                severity='CRITICAL',
                description=f'Phase {phase_name} has {len(recent_failures)} failures in last 10 executions',
                detected_at=datetime.now(),
                affected_component=phase_name,
                metrics={
                    'failure_count': len(recent_failures),
                    'failure_rate': len(recent_failures) / 10
                },
                recommendations=[
                    'Immediate investigation required',
                    'Consider disabling phase temporarily',
                    'Review error logs'
                ],
                confidence=0.95
            ))
            
        return anomalies
        
    def detect_resource_anomalies(self, component: str) -> List[Anomaly]:
        """
        Detect resource usage anomalies.
        
        Checks for:
        - Memory spikes
        - CPU spikes
        - Resource leaks
        """
        anomalies = []
        metrics = list(self.resource_metrics.get(component, []))
        
        if len(metrics) < 10:
            return anomalies
            
        # Check memory anomalies
        memory_values = [m['memory_mb'] for m in metrics]
        mean_memory = statistics.mean(memory_values)
        stdev_memory = statistics.stdev(memory_values) if len(memory_values) > 1 else 0
        
        recent_memory = metrics[-1]['memory_mb']
        
        if stdev_memory > 0:
            z_score = abs(recent_memory - mean_memory) / stdev_memory
            
            if z_score > 3:
                anomalies.append(Anomaly(
                    anomaly_type='memory_spike',
                    severity='HIGH' if recent_memory > mean_memory else 'MEDIUM',
                    description=f'Component {component} memory usage is {z_score:.1f} standard deviations from mean',
                    detected_at=datetime.now(),
                    affected_component=component,
                    metrics={
                        'current_memory_mb': recent_memory,
                        'mean_memory_mb': mean_memory,
                        'z_score': z_score
                    },
                    recommendations=[
                        'Check for memory leaks',
                        'Review object lifecycle',
                        'Consider garbage collection'
                    ],
                    confidence=min(0.9, z_score / 5)
                ))
                
        # Check for memory leak (gradual increase)
        if len(memory_values) >= 20:
            recent_trend = memory_values[-10:]
            older_trend = memory_values[-20:-10]
            
            recent_avg = statistics.mean(recent_trend)
            older_avg = statistics.mean(older_trend)
            
            if recent_avg > older_avg * 1.3:  # 30% increase
                anomalies.append(Anomaly(
                    anomaly_type='memory_leak_suspected',
                    severity='HIGH',
                    description=f'Component {component} shows gradual memory increase',
                    detected_at=datetime.now(),
                    affected_component=component,
                    metrics={
                        'recent_avg_mb': recent_avg,
                        'older_avg_mb': older_avg,
                        'increase_percentage': ((recent_avg - older_avg) / older_avg) * 100
                    },
                    recommendations=[
                        'Investigate memory leak',
                        'Profile memory usage',
                        'Review resource cleanup'
                    ],
                    confidence=0.75
                ))
                
        # Check CPU anomalies
        cpu_values = [m['cpu_percent'] for m in metrics]
        mean_cpu = statistics.mean(cpu_values)
        recent_cpu = metrics[-1]['cpu_percent']
        
        if recent_cpu > 90 and mean_cpu < 70:
            anomalies.append(Anomaly(
                anomaly_type='cpu_spike',
                severity='HIGH',
                description=f'Component {component} CPU usage spiked to {recent_cpu:.1f}%',
                detected_at=datetime.now(),
                affected_component=component,
                metrics={
                    'current_cpu_percent': recent_cpu,
                    'mean_cpu_percent': mean_cpu
                },
                recommendations=[
                    'Check for infinite loops',
                    'Review computational complexity',
                    'Consider optimization'
                ],
                confidence=0.85
            ))
            
        return anomalies
        
    def detect_message_anomalies(self) -> List[Anomaly]:
        """
        Detect message flow anomalies.
        
        Checks for:
        - Message bursts
        - Message droughts
        - Type distribution changes
        """
        anomalies = []
        metrics = list(self.message_metrics)
        
        if len(metrics) < 10:
            return anomalies
            
        # Check for message bursts
        counts = [m['count'] for m in metrics]
        mean_count = statistics.mean(counts)
        stdev_count = statistics.stdev(counts) if len(counts) > 1 else 0
        
        recent_count = metrics[-1]['count']
        
        if stdev_count > 0:
            z_score = abs(recent_count - mean_count) / stdev_count
            
            if z_score > 3 and recent_count > mean_count:
                anomalies.append(Anomaly(
                    anomaly_type='message_burst',
                    severity='MEDIUM',
                    description=f'Message burst detected: {recent_count} messages (mean: {mean_count:.0f})',
                    detected_at=datetime.now(),
                    affected_component='message_bus',
                    metrics={
                        'current_count': recent_count,
                        'mean_count': mean_count,
                        'z_score': z_score
                    },
                    recommendations=[
                        'Check for message loops',
                        'Review message generation logic',
                        'Monitor system load'
                    ],
                    confidence=0.8
                ))
                
        # Check for message drought
        if recent_count < mean_count * 0.3 and mean_count > 10:
            anomalies.append(Anomaly(
                anomaly_type='message_drought',
                severity='MEDIUM',
                description=f'Message drought detected: {recent_count} messages (mean: {mean_count:.0f})',
                detected_at=datetime.now(),
                affected_component='message_bus',
                metrics={
                    'current_count': recent_count,
                    'mean_count': mean_count
                },
                recommendations=[
                    'Check message producers',
                    'Verify system health',
                    'Review phase execution'
                ],
                confidence=0.75
            ))
            
        return anomalies
        
    def detect_objective_anomalies(self, objective_id: str) -> List[Anomaly]:
        """
        Detect objective health anomalies.
        
        Checks for:
        - Rapid health degradation
        - Stalled progress
        - Issue accumulation
        """
        anomalies = []
        metrics = list(self.objective_metrics.get(objective_id, []))
        
        if len(metrics) < 5:
            return anomalies
            
        # Check for rapid health degradation
        health_scores = [m['health_score'] for m in metrics]
        recent_health = health_scores[-1]
        previous_health = health_scores[-5] if len(health_scores) >= 5 else health_scores[0]
        
        health_drop = previous_health - recent_health
        
        if health_drop > 0.3:  # 30% drop
            anomalies.append(Anomaly(
                anomaly_type='health_degradation',
                severity='HIGH',
                description=f'Objective {objective_id} health dropped by {health_drop:.1%}',
                detected_at=datetime.now(),
                affected_component=objective_id,
                metrics={
                    'current_health': recent_health,
                    'previous_health': previous_health,
                    'drop': health_drop
                },
                recommendations=[
                    'Investigate root cause',
                    'Review recent changes',
                    'Consider intervention'
                ],
                confidence=0.9
            ))
            
        # Check for stalled progress
        recent_tasks = [m['task_count'] for m in metrics[-5:]]
        if len(set(recent_tasks)) == 1 and recent_tasks[0] > 0:
            anomalies.append(Anomaly(
                anomaly_type='stalled_progress',
                severity='MEDIUM',
                description=f'Objective {objective_id} shows no task progress',
                detected_at=datetime.now(),
                affected_component=objective_id,
                metrics={
                    'task_count': recent_tasks[0]
                },
                recommendations=[
                    'Check for blocking issues',
                    'Review task dependencies',
                    'Verify phase execution'
                ],
                confidence=0.8
            ))
            
        # Check for issue accumulation
        issue_counts = [m['issue_count'] for m in metrics]
        if len(issue_counts) >= 5:
            recent_issues = issue_counts[-1]
            older_issues = issue_counts[-5]
            
            if recent_issues > older_issues * 2:
                anomalies.append(Anomaly(
                    anomaly_type='issue_accumulation',
                    severity='HIGH',
                    description=f'Objective {objective_id} issues doubled from {older_issues} to {recent_issues}',
                    detected_at=datetime.now(),
                    affected_component=objective_id,
                    metrics={
                        'current_issues': recent_issues,
                        'previous_issues': older_issues
                    },
                    recommendations=[
                        'Prioritize issue resolution',
                        'Allocate debugging resources',
                        'Review quality processes'
                    ],
                    confidence=0.85
                ))
                
        return anomalies
        
    def detect_all_anomalies(self) -> List[Anomaly]:
        """Detect all anomalies across all components"""
        all_anomalies = []
        
        # Phase anomalies
        for phase_name in self.phase_metrics.keys():
            all_anomalies.extend(self.detect_phase_anomalies(phase_name))
            
        # Resource anomalies
        for component in self.resource_metrics.keys():
            all_anomalies.extend(self.detect_resource_anomalies(component))
            
        # Message anomalies
        all_anomalies.extend(self.detect_message_anomalies())
        
        # Objective anomalies
        for objective_id in self.objective_metrics.keys():
            all_anomalies.extend(self.detect_objective_anomalies(objective_id))
            
        # Store detected anomalies
        self.detected_anomalies.extend(all_anomalies)
        
        # Detect patterns
        self._detect_anomaly_patterns()
        
        return all_anomalies
        
    def _detect_anomaly_patterns(self):
        """Detect patterns in anomalies"""
        if len(self.detected_anomalies) < 5:
            return
            
        # Group by type
        by_type = defaultdict(list)
        for anomaly in self.detected_anomalies[-50:]:  # Last 50 anomalies
            by_type[anomaly.anomaly_type].append(anomaly)
            
        # Identify patterns
        for anomaly_type, anomalies in by_type.items():
            if len(anomalies) >= 3:
                pass
                # Calculate frequency
                time_span = (anomalies[-1].detected_at - anomalies[0].detected_at).total_seconds()
                frequency = len(anomalies) / max(time_span / 3600, 1)  # Per hour
                
                # Calculate impact
                severity_scores = {
                    'LOW': 1,
                    'MEDIUM': 2,
                    'HIGH': 3,
                    'CRITICAL': 4
                }
                impact_score = statistics.mean([
                    severity_scores.get(a.severity, 2) for a in anomalies
                ])
                
                # Generate hypothesis
                hypothesis = self._generate_root_cause_hypothesis(anomaly_type, anomalies)
                
                pattern = AnomalyPattern(
                    pattern_id=f"{anomaly_type}_{datetime.now().timestamp()}",
                    anomalies=anomalies,
                    pattern_type=anomaly_type,
                    frequency=frequency,
                    impact_score=impact_score,
                    root_cause_hypothesis=hypothesis
                )
                
                self.anomaly_patterns.append(pattern)
                
    def _generate_root_cause_hypothesis(self, anomaly_type: str, 
                                       anomalies: List[Anomaly]) -> str:
        """Generate root cause hypothesis for anomaly pattern"""
        hypotheses = {
            'execution_time_anomaly': 'Possible performance degradation or resource contention',
            'success_rate_drop': 'Possible code regression or environmental issue',
            'repeated_failures': 'Critical bug or configuration problem',
            'memory_spike': 'Possible memory leak or large data processing',
            'memory_leak_suspected': 'Gradual resource leak requiring investigation',
            'cpu_spike': 'Computational bottleneck or infinite loop',
            'message_burst': 'Message loop or cascading events',
            'message_drought': 'System stall or producer failure',
            'health_degradation': 'Accumulating issues or blocking problems',
            'stalled_progress': 'Dependency deadlock or resource unavailability',
            'issue_accumulation': 'Quality degradation or insufficient debugging'
        }
        
        return hypotheses.get(anomaly_type, 'Unknown root cause - investigation needed')
        
    def get_critical_anomalies(self) -> List[Anomaly]:
        """Get all critical anomalies"""
        return [a for a in self.detected_anomalies if a.severity == 'CRITICAL']
        
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get summary of detected anomalies"""
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        
        for anomaly in self.detected_anomalies:
            by_severity[anomaly.severity] += 1
            by_type[anomaly.anomaly_type] += 1
            
        return {
            'total_anomalies': len(self.detected_anomalies),
            'by_severity': dict(by_severity),
            'by_type': dict(by_type),
            'patterns_detected': len(self.anomaly_patterns),
            'critical_count': by_severity.get('CRITICAL', 0)
        }