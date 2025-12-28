#!/usr/bin/env python3
"""
Predictive Analytics Engine

Provides predictive capabilities for the autonomy pipeline:
- Phase success prediction
- Task completion time estimation
- Issue likelihood prediction
- Resource requirement forecasting
- Objective health trajectory prediction
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math

@dataclass
class PhasePrediction:
    """Prediction for phase execution"""
    phase_name: str
    success_probability: float  # 0.0 to 1.0
    estimated_duration: float  # seconds
    confidence: float  # 0.0 to 1.0
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class TaskPrediction:
    """Prediction for task completion"""
    task_id: str
    completion_probability: float  # 0.0 to 1.0
    estimated_time: float  # seconds
    complexity_score: float  # 0.0 to 1.0
    dependencies_ready: bool
    blocking_issues: List[str] = field(default_factory=list)

@dataclass
class IssuePrediction:
    """Prediction for issue occurrence"""
    issue_type: str
    likelihood: float  # 0.0 to 1.0
    severity_estimate: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    prevention_actions: List[str] = field(default_factory=list)
    early_indicators: List[str] = field(default_factory=list)

@dataclass
class ResourceForecast:
    """Forecast for resource requirements"""
    phase_name: str
    estimated_memory_mb: float
    estimated_cpu_percent: float
    estimated_duration_seconds: float
    peak_usage_time: Optional[datetime] = None

@dataclass
class ObjectiveTrajectory:
    """Predicted trajectory for objective"""
    objective_id: str
    current_health: str
    predicted_health_24h: str
    predicted_health_7d: str
    completion_probability: float
    estimated_completion_date: Optional[datetime] = None
    risk_trajectory: List[Tuple[datetime, float]] = field(default_factory=list)

class PredictiveAnalyticsEngine:
    """
    Predictive analytics engine for the autonomy pipeline.
    
    Uses historical data and pattern analysis to predict:
    - Phase success rates
    - Task completion times
    - Issue likelihood
    - Resource requirements
    - Objective health trajectories
    """
    
    def __init__(self):
        self.phase_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.task_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.issue_history: List[Dict[str, Any]] = []
        self.resource_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.objective_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def record_phase_execution(self, phase_name: str, success: bool, 
                               duration: float, context: Dict[str, Any]):
        """Record phase execution for learning"""
        self.phase_history[phase_name].append({
            'timestamp': datetime.now(),
            'success': success,
            'duration': duration,
            'context': context
        })
        
    def record_task_completion(self, task_id: str, success: bool, 
                               duration: float, complexity: float):
        """Record task completion for learning"""
        self.task_history[task_id].append({
            'timestamp': datetime.now(),
            'success': success,
            'duration': duration,
            'complexity': complexity
        })
        
    def record_issue(self, issue_type: str, severity: str, 
                     context: Dict[str, Any]):
        """Record issue occurrence for learning"""
        self.issue_history.append({
            'timestamp': datetime.now(),
            'type': issue_type,
            'severity': severity,
            'context': context
        })
        
    def record_resource_usage(self, phase_name: str, memory_mb: float, 
                             cpu_percent: float, duration: float):
        """Record resource usage for learning"""
        self.resource_history[phase_name].append({
            'timestamp': datetime.now(),
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'duration': duration
        })
        
    def record_objective_state(self, objective_id: str, health: str, 
                              metrics: Dict[str, Any]):
        """Record objective state for trajectory analysis"""
        self.objective_history[objective_id].append({
            'timestamp': datetime.now(),
            'health': health,
            'metrics': metrics
        })
        
    def predict_phase_success(self, phase_name: str, 
                             context: Dict[str, Any]) -> PhasePrediction:
        """
        Predict phase execution success and duration.
        
        Uses historical data to estimate:
        - Success probability
        - Expected duration
        - Risk factors
        - Recommendations
        """
        history = self.phase_history.get(phase_name, [])
        
        if not history:
            # No history - use defaults
            return PhasePrediction(
                phase_name=phase_name,
                success_probability=0.7,  # Optimistic default
                estimated_duration=300.0,  # 5 minutes default
                confidence=0.3,  # Low confidence
                risk_factors=['No historical data available'],
                recommendations=['Monitor closely', 'Collect metrics']
            )
            
        # Calculate success rate
        successes = sum(1 for h in history if h['success'])
        success_rate = successes / len(history)
        
        # Calculate average duration
        durations = [h['duration'] for h in history]
        avg_duration = statistics.mean(durations)
        
        # Adjust based on context similarity
        similar_contexts = [
            h for h in history 
            if self._context_similarity(h['context'], context) > 0.5
        ]
        
        if similar_contexts:
            similar_success_rate = sum(1 for h in similar_contexts if h['success']) / len(similar_contexts)
            similar_avg_duration = statistics.mean([h['duration'] for h in similar_contexts])
            
            # Weight similar contexts more heavily
            success_probability = 0.7 * similar_success_rate + 0.3 * success_rate
            estimated_duration = 0.7 * similar_avg_duration + 0.3 * avg_duration
            confidence = 0.8
        else:
            success_probability = success_rate
            estimated_duration = avg_duration
            confidence = 0.5
            
        # Identify risk factors
        risk_factors = []
        if success_probability < 0.5:
            risk_factors.append('Low historical success rate')
        if len(history) < 5:
            risk_factors.append('Limited historical data')
        if estimated_duration > 600:  # 10 minutes
            risk_factors.append('Long execution time expected')
            
        # Generate recommendations
        recommendations = []
        if success_probability < 0.7:
            recommendations.append('Consider pre-execution validation')
        if estimated_duration > 300:
            recommendations.append('Allocate sufficient time budget')
        if not similar_contexts:
            recommendations.append('Context differs from history - monitor closely')
            
        return PhasePrediction(
            phase_name=phase_name,
            success_probability=success_probability,
            estimated_duration=estimated_duration,
            confidence=confidence,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
        
    def predict_task_completion(self, task_id: str, 
                               complexity: float,
                               dependencies: List[str]) -> TaskPrediction:
        """
        Predict task completion probability and time.
        
        Considers:
        - Task complexity
        - Historical performance
        - Dependency status
        """
        history = self.task_history.get(task_id, [])
        
        # Base prediction on complexity
        if complexity < 0.3:
            base_probability = 0.9
            base_time = 300  # 5 minutes
        elif complexity < 0.6:
            base_probability = 0.75
            base_time = 900  # 15 minutes
        else:
            base_probability = 0.6
            base_time = 1800  # 30 minutes
            
        # Adjust based on history
        if history:
            successes = sum(1 for h in history if h['success'])
            success_rate = successes / len(history)
            avg_duration = statistics.mean([h['duration'] for h in history])
            
            completion_probability = 0.6 * success_rate + 0.4 * base_probability
            estimated_time = 0.6 * avg_duration + 0.4 * base_time
        else:
            completion_probability = base_probability
            estimated_time = base_time
            
        # Check dependencies
        dependencies_ready = True  # Simplified - would check actual status
        blocking_issues = []
        
        if not dependencies_ready:
            completion_probability *= 0.5
            blocking_issues.append('Dependencies not ready')
            
        return TaskPrediction(
            task_id=task_id,
            completion_probability=completion_probability,
            estimated_time=estimated_time,
            complexity_score=complexity,
            dependencies_ready=dependencies_ready,
            blocking_issues=blocking_issues
        )
        
    def predict_issue_likelihood(self, phase_name: str, 
                                context: Dict[str, Any]) -> List[IssuePrediction]:
        """
        Predict likelihood of issues occurring.
        
        Analyzes historical patterns to identify:
        - Common issue types
        - Likelihood of occurrence
        - Severity estimates
        - Prevention actions
        """
        predictions = []
        
        # Analyze historical issues
        issue_types = defaultdict(int)
        issue_severities = defaultdict(list)
        
        for issue in self.issue_history:
            issue_types[issue['type']] += 1
            issue_severities[issue['type']].append(issue['severity'])
            
        # Generate predictions for common issue types
        total_issues = len(self.issue_history)
        
        for issue_type, count in issue_types.items():
            likelihood = count / max(total_issues, 1)
            
            # Estimate severity
            severities = issue_severities[issue_type]
            severity_counts = defaultdict(int)
            for s in severities:
                severity_counts[s] += 1
            most_common_severity = max(severity_counts.items(), key=lambda x: x[1])[0]
            
            # Generate prevention actions
            prevention_actions = self._generate_prevention_actions(issue_type)
            early_indicators = self._generate_early_indicators(issue_type)
            
            predictions.append(IssuePrediction(
                issue_type=issue_type,
                likelihood=likelihood,
                severity_estimate=most_common_severity,
                prevention_actions=prevention_actions,
                early_indicators=early_indicators
            ))
            
        return sorted(predictions, key=lambda x: x.likelihood, reverse=True)
        
    def forecast_resource_requirements(self, phase_name: str) -> ResourceForecast:
        """
        Forecast resource requirements for phase execution.
        
        Predicts:
        - Memory usage
        - CPU usage
        - Duration
        - Peak usage time
        """
        history = self.resource_history.get(phase_name, [])
        
        if not history:
            # Default estimates
            return ResourceForecast(
                phase_name=phase_name,
                estimated_memory_mb=512.0,
                estimated_cpu_percent=50.0,
                estimated_duration_seconds=300.0
            )
            
        # Calculate averages
        avg_memory = statistics.mean([h['memory_mb'] for h in history])
        avg_cpu = statistics.mean([h['cpu_percent'] for h in history])
        avg_duration = statistics.mean([h['duration'] for h in history])
        
        # Add buffer for safety (20%)
        estimated_memory = avg_memory * 1.2
        estimated_cpu = min(avg_cpu * 1.2, 100.0)
        estimated_duration = avg_duration * 1.2
        
        return ResourceForecast(
            phase_name=phase_name,
            estimated_memory_mb=estimated_memory,
            estimated_cpu_percent=estimated_cpu,
            estimated_duration_seconds=estimated_duration
        )
        
    def predict_objective_trajectory(self, objective_id: str) -> ObjectiveTrajectory:
        """
        Predict objective health trajectory.
        
        Analyzes historical health states to predict:
        - Future health status
        - Completion probability
        - Estimated completion date
        - Risk trajectory
        """
        history = self.objective_history.get(objective_id, [])
        
        if not history:
            return ObjectiveTrajectory(
                objective_id=objective_id,
                current_health='UNKNOWN',
                predicted_health_24h='UNKNOWN',
                predicted_health_7d='UNKNOWN',
                completion_probability=0.5
            )
            
        # Get current health
        current_health = history[-1]['health']
        
        # Analyze trend
        health_scores = {
            'HEALTHY': 1.0,
            'DEGRADING': 0.6,
            'CRITICAL': 0.3,
            'BLOCKED': 0.1
        }
        
        recent_scores = [
            health_scores.get(h['health'], 0.5) 
            for h in history[-10:]
        ]
        
        # Calculate trend
        if len(recent_scores) >= 2:
            trend = recent_scores[-1] - recent_scores[0]
        else:
            trend = 0
            
        # Predict future health
        current_score = health_scores.get(current_health, 0.5)
        predicted_score_24h = max(0.0, min(1.0, current_score + trend * 0.5))
        predicted_score_7d = max(0.0, min(1.0, current_score + trend * 2.0))
        
        predicted_health_24h = self._score_to_health(predicted_score_24h)
        predicted_health_7d = self._score_to_health(predicted_score_7d)
        
        # Estimate completion probability
        completion_probability = predicted_score_7d
        
        # Estimate completion date
        if completion_probability > 0.7:
            days_to_completion = 7 / completion_probability
            estimated_completion_date = datetime.now() + timedelta(days=days_to_completion)
        else:
            estimated_completion_date = None
            
        # Generate risk trajectory
        risk_trajectory = []
        for i in range(7):
            future_date = datetime.now() + timedelta(days=i)
            risk_score = 1.0 - max(0.0, min(1.0, current_score + trend * i * 0.3))
            risk_trajectory.append((future_date, risk_score))
            
        return ObjectiveTrajectory(
            objective_id=objective_id,
            current_health=current_health,
            predicted_health_24h=predicted_health_24h,
            predicted_health_7d=predicted_health_7d,
            completion_probability=completion_probability,
            estimated_completion_date=estimated_completion_date,
            risk_trajectory=risk_trajectory
        )
        
    def _context_similarity(self, context1: Dict[str, Any], 
                           context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
            
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
            
        matches = sum(
            1 for key in common_keys 
            if context1[key] == context2[key]
        )
        
        return matches / len(common_keys)
        
    def _generate_prevention_actions(self, issue_type: str) -> List[str]:
        """Generate prevention actions for issue type"""
        actions = {
            'syntax_error': [
                'Run linter before execution',
                'Use syntax validation tools',
                'Enable IDE syntax checking'
            ],
            'import_error': [
                'Verify dependencies installed',
                'Check import paths',
                'Use virtual environment'
            ],
            'runtime_error': [
                'Add error handling',
                'Validate inputs',
                'Use defensive programming'
            ],
            'test_failure': [
                'Review test cases',
                'Update test data',
                'Check test environment'
            ]
        }
        
        return actions.get(issue_type, ['Monitor closely', 'Review code'])
        
    def _generate_early_indicators(self, issue_type: str) -> List[str]:
        """Generate early indicators for issue type"""
        indicators = {
            'syntax_error': [
                'Linter warnings',
                'IDE error markers',
                'Compilation failures'
            ],
            'import_error': [
                'Missing dependencies',
                'Import warnings',
                'Module not found errors'
            ],
            'runtime_error': [
                'Null pointer warnings',
                'Type mismatches',
                'Boundary condition violations'
            ],
            'test_failure': [
                'Flaky tests',
                'Timeout warnings',
                'Assertion failures'
            ]
        }
        
        return indicators.get(issue_type, ['Unusual behavior', 'Error logs'])
        
    def _score_to_health(self, score: float) -> str:
        """Convert numeric score to health status"""
        if score >= 0.8:
            return 'HEALTHY'
        elif score >= 0.5:
            return 'DEGRADING'
        elif score >= 0.2:
            return 'CRITICAL'
        else:
            return 'BLOCKED'
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'phases_tracked': len(self.phase_history),
            'total_phase_executions': sum(len(h) for h in self.phase_history.values()),
            'tasks_tracked': len(self.task_history),
            'total_task_completions': sum(len(h) for h in self.task_history.values()),
            'issues_recorded': len(self.issue_history),
            'objectives_tracked': len(self.objective_history)
        }