#!/usr/bin/env python3
"""
Optimization Recommendations Engine

Provides optimization recommendations for the autonomy pipeline:
- Phase execution optimization
- Resource allocation optimization
- Task scheduling optimization
- Issue resolution prioritization
- Objective planning optimization
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import statistics

@dataclass
class Optimization:
    """Represents an optimization recommendation"""
    optimization_id: str
    category: str  # 'performance', 'resource', 'quality', 'scheduling'
    priority: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    title: str
    description: str
    expected_benefit: str
    implementation_effort: str  # 'LOW', 'MEDIUM', 'HIGH'
    steps: List[str] = field(default_factory=list)
    metrics_to_track: List[str] = field(default_factory=list)
    estimated_impact: Dict[str, float] = field(default_factory=dict)

@dataclass
class OptimizationPlan:
    """Complete optimization plan"""
    plan_id: str
    created_at: datetime
    optimizations: List[Optimization]
    total_expected_benefit: str
    implementation_timeline: str
    risk_assessment: str

class OptimizationEngine:
    """
    Generates optimization recommendations for the pipeline.
    
    Analyzes:
    - Performance bottlenecks
    - Resource inefficiencies
    - Quality issues
    - Scheduling problems
    - Strategic planning gaps
    """
    
    def __init__(self):
        self.phase_performance: Dict[str, List[float]] = defaultdict(list)
        self.resource_usage: Dict[str, List[Dict[str, float]]] = defaultdict(list)
        self.quality_metrics: Dict[str, List[float]] = defaultdict(list)
        self.task_completion_times: Dict[str, List[float]] = defaultdict(list)
        self.optimization_history: List[Optimization] = []
        
    def record_phase_performance(self, phase_name: str, duration: float, 
                                success: bool):
        """Record phase performance for analysis"""
        self.phase_performance[phase_name].append(duration)
        
    def record_resource_usage(self, component: str, memory_mb: float, 
                            cpu_percent: float):
        """Record resource usage for analysis"""
        self.resource_usage[component].append({
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'timestamp': datetime.now()
        })
        
    def record_quality_metric(self, metric_name: str, value: float):
        """Record quality metric for analysis"""
        self.quality_metrics[metric_name].append(value)
        
    def record_task_completion(self, task_type: str, duration: float):
        """Record task completion time for analysis"""
        self.task_completion_times[task_type].append(duration)
        
    def generate_performance_optimizations(self) -> List[Optimization]:
        """Generate performance optimization recommendations"""
        optimizations = []
        
        # Analyze phase performance
        for phase_name, durations in self.phase_performance.items():
            if len(durations) < 10:
                continue
                
            avg_duration = statistics.mean(durations)
            
            # Check for slow phases
            if avg_duration > 600:  # 10 minutes
                optimizations.append(Optimization(
                    optimization_id=f"perf_slow_phase_{phase_name}",
                    category='performance',
                    priority='HIGH',
                    title=f"Optimize {phase_name} Phase Performance",
                    description=f"Phase {phase_name} takes an average of {avg_duration:.0f} seconds. This is significantly longer than optimal.",
                    expected_benefit="30-50% reduction in execution time",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Profile phase execution to identify bottlenecks",
                        "Optimize database queries if applicable",
                        "Consider parallel processing for independent operations",
                        "Cache frequently accessed data",
                        "Review algorithm complexity"
                    ],
                    metrics_to_track=[
                        'phase_duration',
                        'cpu_usage',
                        'memory_usage'
                    ],
                    estimated_impact={
                        'time_saved_seconds': avg_duration * 0.4,
                        'throughput_increase_percent': 40
                    }
                ))
                
            # Check for high variance
            if len(durations) > 1:
                stdev = statistics.stdev(durations)
                cv = stdev / avg_duration  # Coefficient of variation
                
                if cv > 0.5:  # High variance
                    optimizations.append(Optimization(
                        optimization_id=f"perf_variance_{phase_name}",
                        category='performance',
                        priority='MEDIUM',
                        title=f"Reduce {phase_name} Phase Execution Variance",
                        description=f"Phase {phase_name} has high execution time variance (CV: {cv:.2f}). This indicates inconsistent performance.",
                        expected_benefit="More predictable execution times",
                        implementation_effort='MEDIUM',
                        steps=[
                            "Identify causes of variance",
                            "Standardize input data processing",
                            "Implement consistent resource allocation",
                            "Add execution time limits",
                            "Consider workload balancing"
                        ],
                        metrics_to_track=[
                            'execution_time_stdev',
                            'coefficient_of_variation'
                        ],
                        estimated_impact={
                            'variance_reduction_percent': 50
                        }
                    ))
                    
        return optimizations
        
    def generate_resource_optimizations(self) -> List[Optimization]:
        """Generate resource optimization recommendations"""
        optimizations = []
        
        # Analyze resource usage
        for component, usage_records in self.resource_usage.items():
            if len(usage_records) < 10:
                continue
                
            memory_values = [r['memory_mb'] for r in usage_records]
            cpu_values = [r['cpu_percent'] for r in usage_records]
            
            avg_memory = statistics.mean(memory_values)
            avg_cpu = statistics.mean(cpu_values)
            max_memory = max(memory_values)
            max_cpu = max(cpu_values)
            
            # Check for high memory usage
            if avg_memory > 2048:  # 2GB
                optimizations.append(Optimization(
                    optimization_id=f"resource_memory_{component}",
                    category='resource',
                    priority='HIGH',
                    title=f"Optimize Memory Usage in {component}",
                    description=f"Component {component} uses an average of {avg_memory:.0f}MB memory. Consider optimization.",
                    expected_benefit="20-40% reduction in memory usage",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Profile memory usage patterns",
                        "Implement object pooling",
                        "Use generators instead of lists where possible",
                        "Clear caches periodically",
                        "Review data structure choices"
                    ],
                    metrics_to_track=[
                        'memory_usage_mb',
                        'memory_peak_mb',
                        'gc_collections'
                    ],
                    estimated_impact={
                        'memory_saved_mb': avg_memory * 0.3,
                        'cost_reduction_percent': 30
                    }
                ))
                
            # Check for CPU bottlenecks
            if avg_cpu > 80:
                optimizations.append(Optimization(
                    optimization_id=f"resource_cpu_{component}",
                    category='resource',
                    priority='HIGH',
                    title=f"Reduce CPU Usage in {component}",
                    description=f"Component {component} uses an average of {avg_cpu:.0f}% CPU. This may cause performance issues.",
                    expected_benefit="30-50% reduction in CPU usage",
                    implementation_effort='HIGH',
                    steps=[
                        "Profile CPU-intensive operations",
                        "Optimize algorithms",
                        "Use caching for expensive computations",
                        "Consider async/parallel processing",
                        "Review loop optimizations"
                    ],
                    metrics_to_track=[
                        'cpu_usage_percent',
                        'cpu_peak_percent',
                        'operation_throughput'
                    ],
                    estimated_impact={
                        'cpu_reduction_percent': 40,
                        'throughput_increase_percent': 50
                    }
                ))
                
            # Check for resource spikes
            if max_memory > avg_memory * 2:
                optimizations.append(Optimization(
                    optimization_id=f"resource_spike_{component}",
                    category='resource',
                    priority='MEDIUM',
                    title=f"Smooth Resource Usage in {component}",
                    description=f"Component {component} shows memory spikes up to {max_memory:.0f}MB (avg: {avg_memory:.0f}MB).",
                    expected_benefit="More stable resource usage",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Identify spike triggers",
                        "Implement resource throttling",
                        "Use streaming for large data",
                        "Add memory limits",
                        "Implement backpressure"
                    ],
                    metrics_to_track=[
                        'memory_peak_mb',
                        'spike_frequency',
                        'spike_duration'
                    ],
                    estimated_impact={
                        'spike_reduction_percent': 60
                    }
                ))
                
        return optimizations
        
    def generate_quality_optimizations(self) -> List[Optimization]:
        """Generate quality optimization recommendations"""
        optimizations = []
        
        # Analyze quality metrics
        for metric_name, values in self.quality_metrics.items():
            if len(values) < 5:
                continue
                
            avg_value = statistics.mean(values)
            recent_value = values[-1]
            
            # Check for declining quality
            if recent_value < avg_value * 0.8:
                optimizations.append(Optimization(
                    optimization_id=f"quality_{metric_name}",
                    category='quality',
                    priority='HIGH',
                    title=f"Improve {metric_name}",
                    description=f"Quality metric {metric_name} has declined from {avg_value:.2f} to {recent_value:.2f}.",
                    expected_benefit="Restore quality to baseline levels",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Identify root cause of quality decline",
                        "Review recent code changes",
                        "Enhance testing coverage",
                        "Add quality gates",
                        "Implement continuous monitoring"
                    ],
                    metrics_to_track=[
                        metric_name,
                        'test_coverage',
                        'defect_rate'
                    ],
                    estimated_impact={
                        'quality_improvement_percent': 25
                    }
                ))
                
        return optimizations
        
    def generate_scheduling_optimizations(self) -> List[Optimization]:
        """Generate task scheduling optimization recommendations"""
        optimizations = []
        
        # Analyze task completion times
        for task_type, durations in self.task_completion_times.items():
            if len(durations) < 10:
                continue
                
            avg_duration = statistics.mean(durations)
            
            # Check for long-running tasks
            if avg_duration > 1800:  # 30 minutes
                optimizations.append(Optimization(
                    optimization_id=f"schedule_long_task_{task_type}",
                    category='scheduling',
                    priority='MEDIUM',
                    title=f"Optimize {task_type} Task Scheduling",
                    description=f"Task type {task_type} takes an average of {avg_duration/60:.0f} minutes. Consider breaking into smaller tasks.",
                    expected_benefit="Better parallelization and progress tracking",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Break task into smaller subtasks",
                        "Implement task checkpointing",
                        "Enable parallel execution where possible",
                        "Add progress reporting",
                        "Implement task prioritization"
                    ],
                    metrics_to_track=[
                        'task_duration',
                        'subtask_count',
                        'parallelization_factor'
                    ],
                    estimated_impact={
                        'throughput_increase_percent': 40,
                        'progress_visibility_improvement': 'HIGH'
                    }
                ))
                
        return optimizations
        
    def generate_strategic_optimizations(self, 
                                        objective_metrics: Dict[str, Any]) -> List[Optimization]:
        """Generate strategic planning optimization recommendations"""
        optimizations = []
        
        # Analyze objective completion rates
        if 'completion_rate' in objective_metrics:
            completion_rate = objective_metrics['completion_rate']
            
            if completion_rate < 0.7:
                optimizations.append(Optimization(
                    optimization_id="strategic_completion_rate",
                    category='strategic',
                    priority='HIGH',
                    title="Improve Objective Completion Rate",
                    description=f"Current objective completion rate is {completion_rate:.1%}. This is below target.",
                    expected_benefit="20-30% increase in completion rate",
                    implementation_effort='HIGH',
                    steps=[
                        "Review objective scoping and sizing",
                        "Improve task breakdown",
                        "Enhance dependency management",
                        "Add early risk detection",
                        "Implement adaptive planning"
                    ],
                    metrics_to_track=[
                        'completion_rate',
                        'objective_health',
                        'task_success_rate'
                    ],
                    estimated_impact={
                        'completion_rate_increase_percent': 25
                    }
                ))
                
        # Analyze issue resolution
        if 'avg_issue_resolution_time' in objective_metrics:
            resolution_time = objective_metrics['avg_issue_resolution_time']
            
            if resolution_time > 3600:  # 1 hour
                optimizations.append(Optimization(
                    optimization_id="strategic_issue_resolution",
                    category='strategic',
                    priority='HIGH',
                    title="Accelerate Issue Resolution",
                    description=f"Average issue resolution time is {resolution_time/60:.0f} minutes. This slows progress.",
                    expected_benefit="40-60% faster issue resolution",
                    implementation_effort='MEDIUM',
                    steps=[
                        "Implement automated issue triage",
                        "Enhance debugging tools",
                        "Add issue pattern recognition",
                        "Improve error messages",
                        "Create issue resolution playbooks"
                    ],
                    metrics_to_track=[
                        'issue_resolution_time',
                        'first_time_fix_rate',
                        'issue_recurrence_rate'
                    ],
                    estimated_impact={
                        'resolution_time_reduction_percent': 50
                    }
                ))
                
        return optimizations
        
    def generate_optimization_plan(self, 
                                   objective_metrics: Optional[Dict[str, Any]] = None) -> OptimizationPlan:
        """
        Generate comprehensive optimization plan.
        
        Combines all optimization recommendations into a prioritized plan.
        """
        all_optimizations = []
        
        # Collect all optimizations
        all_optimizations.extend(self.generate_performance_optimizations())
        all_optimizations.extend(self.generate_resource_optimizations())
        all_optimizations.extend(self.generate_quality_optimizations())
        all_optimizations.extend(self.generate_scheduling_optimizations())
        
        if objective_metrics:
            all_optimizations.extend(self.generate_strategic_optimizations(objective_metrics))
            
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_optimizations.sort(key=lambda x: priority_order.get(x.priority, 4))
        
        # Calculate total expected benefit
        total_benefit = self._calculate_total_benefit(all_optimizations)
        
        # Estimate implementation timeline
        timeline = self._estimate_timeline(all_optimizations)
        
        # Assess risks
        risk_assessment = self._assess_risks(all_optimizations)
        
        plan = OptimizationPlan(
            plan_id=f"opt_plan_{datetime.now().timestamp()}",
            created_at=datetime.now(),
            optimizations=all_optimizations,
            total_expected_benefit=total_benefit,
            implementation_timeline=timeline,
            risk_assessment=risk_assessment
        )
        
        return plan
        
    def _calculate_total_benefit(self, optimizations: List[Optimization]) -> str:
        """Calculate total expected benefit"""
        categories = defaultdict(int)
        
        for opt in optimizations:
            categories[opt.category] += 1
            
        benefits = []
        if categories['performance'] > 0:
            benefits.append(f"{categories['performance']} performance improvements")
        if categories['resource'] > 0:
            benefits.append(f"{categories['resource']} resource optimizations")
        if categories['quality'] > 0:
            benefits.append(f"{categories['quality']} quality enhancements")
        if categories['scheduling'] > 0:
            benefits.append(f"{categories['scheduling']} scheduling improvements")
            
        return ", ".join(benefits) if benefits else "No optimizations identified"
        
    def _estimate_timeline(self, optimizations: List[Optimization]) -> str:
        """Estimate implementation timeline"""
        effort_days = {
            'LOW': 1,
            'MEDIUM': 3,
            'HIGH': 7
        }
        
        total_days = sum(
            effort_days.get(opt.implementation_effort, 3) 
            for opt in optimizations
        )
        
        if total_days <= 7:
            return "1 week"
        elif total_days <= 14:
            return "2 weeks"
        elif total_days <= 30:
            return "1 month"
        else:
            return f"{total_days // 30} months"
            
    def _assess_risks(self, optimizations: List[Optimization]) -> str:
        """Assess implementation risks"""
        high_effort_count = sum(
            1 for opt in optimizations 
            if opt.implementation_effort == 'HIGH'
        )
        
        if high_effort_count > 5:
            return "HIGH - Many complex optimizations requiring significant effort"
        elif high_effort_count > 2:
            return "MEDIUM - Some complex optimizations requiring careful planning"
        else:
            return "LOW - Mostly straightforward optimizations"
            
    def get_top_optimizations(self, n: int = 5) -> List[Optimization]:
        """Get top N priority optimizations"""
        plan = self.generate_optimization_plan()
        return plan.optimizations[:n]
        
    def get_quick_wins(self) -> List[Optimization]:
        """Get quick win optimizations (high benefit, low effort)"""
        plan = self.generate_optimization_plan()
        
        return [
            opt for opt in plan.optimizations
            if opt.implementation_effort == 'LOW' and opt.priority in ['HIGH', 'CRITICAL']
        ]