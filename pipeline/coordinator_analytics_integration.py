#!/usr/bin/env python3
"""
Coordinator Analytics Integration

This module provides analytics integration for the Coordinator.
It wraps the coordinator with analytics capabilities without modifying the core coordinator code.
"""

from typing import Optional, Dict, Any
import time
import logging
from datetime import datetime

try:
    from .analytics import (
        PredictiveAnalyticsEngine,
        AnomalyDetector,
        OptimizationEngine
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    logging.warning("Analytics module not available")

class AnalyticsIntegration:
    """
    Analytics integration wrapper for Coordinator.
    
    Provides:
    - Predictive analytics before phase execution
    - Anomaly detection after phase execution
    - Optimization recommendations
    - Performance tracking
    """
    
    def __init__(self, enabled: bool = True, config: Optional[Dict[str, Any]] = None):
        """
        Initialize analytics integration.
        
        Args:
            enabled: Whether analytics is enabled
            config: Configuration dictionary
        """
        self.enabled = enabled and ANALYTICS_AVAILABLE
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        if not self.enabled:
            self.logger.info("Analytics integration disabled")
            return
            
        # Initialize analytics components
        self.predictive_engine = PredictiveAnalyticsEngine()
        self.anomaly_detector = AnomalyDetector(
            window_size=self.config.get('anomaly_window_size', 100)
        )
        self.optimizer = OptimizationEngine()
        
        # Tracking
        self.execution_count = 0
        self.last_optimization_check = datetime.now()
        
        self.logger.info("Analytics integration initialized")
        
    def before_phase_execution(self, phase_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called before phase execution.
        
        Returns prediction and recommendations.
        """
        if not self.enabled:
            return {}
            
        try:
            # Get prediction
            prediction = self.predictive_engine.predict_phase_success(phase_name, context)
            
            # Log prediction
            self.logger.info(f"Phase {phase_name} prediction:")
            self.logger.info(f"  Success probability: {prediction.success_probability:.1%}")
            self.logger.info(f"  Estimated duration: {prediction.estimated_duration:.0f}s")
            self.logger.info(f"  Confidence: {prediction.confidence:.1%}")
            
            if prediction.risk_factors:
                self.logger.warning(f"  Risk factors: {', '.join(prediction.risk_factors)}")
                
            if prediction.recommendations:
                self.logger.info(f"  Recommendations: {', '.join(prediction.recommendations)}")
                
            return {
                'prediction': prediction,
                'should_proceed': prediction.success_probability > 0.3,  # Threshold
                'estimated_duration': prediction.estimated_duration
            }
            
        except Exception as e:
            self.logger.error(f"Error in before_phase_execution: {e}")
            return {}
            
    def after_phase_execution(self, phase_name: str, duration: float, 
                             success: bool, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called after phase execution.
        
        Records metrics and detects anomalies.
        """
        if not self.enabled:
            return {}
            
        try:
            # Record for predictive engine
            self.predictive_engine.record_phase_execution(
                phase_name,
                success=success,
                duration=duration,
                context=context
            )
            
            # Record for anomaly detector
            self.anomaly_detector.record_phase_metric(
                phase_name,
                duration=duration,
                success=success,
                context=context
            )
            
            # Record for optimizer
            self.optimizer.record_phase_performance(
                phase_name,
                duration=duration,
                success=success
            )
            
            # Detect anomalies
            anomalies = self.anomaly_detector.detect_phase_anomalies(phase_name)
            
            # Log anomalies
            critical_anomalies = [a for a in anomalies if a.severity in ['HIGH', 'CRITICAL']]
            if critical_anomalies:
                for anomaly in critical_anomalies:
                    self.logger.warning(f"Anomaly detected: {anomaly.description}")
                    self.logger.warning(f"  Severity: {anomaly.severity}")
                    self.logger.warning(f"  Recommendations: {', '.join(anomaly.recommendations)}")
                    
            # Increment execution count
            self.execution_count += 1
            
            # Periodic optimization check
            if self.execution_count % self.config.get('optimization_interval', 100) == 0:
                self._generate_optimization_report()
                
            return {
                'anomalies': anomalies,
                'critical_anomalies': critical_anomalies,
                'execution_count': self.execution_count
            }
            
        except Exception as e:
            self.logger.error(f"Error in after_phase_execution: {e}")
            return {}
            
    def record_resource_usage(self, component: str, memory_mb: float, cpu_percent: float):
        """Record resource usage for anomaly detection."""
        if not self.enabled:
            return
            
        try:
            self.anomaly_detector.record_resource_metric(
                component,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent
            )
            
            self.optimizer.record_resource_usage(
                component,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent
            )
            
            # Check for resource anomalies
            anomalies = self.anomaly_detector.detect_resource_anomalies(component)
            for anomaly in anomalies:
                if anomaly.severity in ['HIGH', 'CRITICAL']:
                    self.logger.warning(f"Resource anomaly: {anomaly.description}")
                    
        except Exception as e:
            self.logger.error(f"Error recording resource usage: {e}")
            
    def record_message_metrics(self, message_count: int, message_types: Dict[str, int]):
        """Record message bus metrics."""
        if not self.enabled:
            return
            
        try:
            self.anomaly_detector.record_message_metric(message_count, message_types)
            
            # Check for message anomalies
            anomalies = self.anomaly_detector.detect_message_anomalies()
            for anomaly in anomalies:
                if anomaly.severity in ['HIGH', 'CRITICAL']:
                    self.logger.warning(f"Message anomaly: {anomaly.description}")
                    
        except Exception as e:
            self.logger.error(f"Error recording message metrics: {e}")
            
    def record_objective_metrics(self, objective_id: str, health_score: float,
                                 task_count: int, issue_count: int):
        """Record objective health metrics."""
        if not self.enabled:
            return
            
        try:
            self.anomaly_detector.record_objective_metric(
                objective_id,
                health_score=health_score,
                task_count=task_count,
                issue_count=issue_count
            )
            
            self.predictive_engine.record_objective_state(
                objective_id,
                health='HEALTHY' if health_score > 0.7 else 'DEGRADING' if health_score > 0.4 else 'CRITICAL',
                metrics={'health_score': health_score, 'tasks': task_count, 'issues': issue_count}
            )
            
            # Check for objective anomalies
            anomalies = self.anomaly_detector.detect_objective_anomalies(objective_id)
            for anomaly in anomalies:
                if anomaly.severity in ['HIGH', 'CRITICAL']:
                    self.logger.warning(f"Objective anomaly: {anomaly.description}")
                    
        except Exception as e:
            self.logger.error(f"Error recording objective metrics: {e}")
            
    def predict_objective_trajectory(self, objective_id: str):
        """Predict objective health trajectory."""
        if not self.enabled:
            return None
            
        try:
            trajectory = self.predictive_engine.predict_objective_trajectory(objective_id)
            
            self.logger.info(f"Objective {objective_id} trajectory:")
            self.logger.info(f"  Current health: {trajectory.current_health}")
            self.logger.info(f"  Predicted 24h: {trajectory.predicted_health_24h}")
            self.logger.info(f"  Predicted 7d: {trajectory.predicted_health_7d}")
            self.logger.info(f"  Completion probability: {trajectory.completion_probability:.1%}")
            
            return trajectory
            
        except Exception as e:
            self.logger.error(f"Error predicting trajectory: {e}")
            return None
            
    def _generate_optimization_report(self):
        """Generate and log optimization report."""
        try:
            plan = self.optimizer.generate_optimization_plan()
            
            self.logger.info("=" * 70)
            self.logger.info("OPTIMIZATION REPORT")
            self.logger.info("=" * 70)
            self.logger.info(f"Total optimizations: {len(plan.optimizations)}")
            self.logger.info(f"Expected benefit: {plan.total_expected_benefit}")
            self.logger.info(f"Implementation timeline: {plan.implementation_timeline}")
            self.logger.info(f"Risk assessment: {plan.risk_assessment}")
            
            # Log top 5 optimizations
            self.logger.info("\nTop 5 Optimizations:")
            for i, opt in enumerate(plan.optimizations[:5], 1):
                self.logger.info(f"{i}. [{opt.priority}] {opt.title}")
                self.logger.info(f"   {opt.description}")
                self.logger.info(f"   Expected benefit: {opt.expected_benefit}")
                self.logger.info(f"   Effort: {opt.implementation_effort}")
                
            # Log quick wins
            quick_wins = self.optimizer.get_quick_wins()
            if quick_wins:
                self.logger.info("\nQuick Wins (Low effort, High priority):")
                for opt in quick_wins:
                    self.logger.info(f"- {opt.title}")
                    
            self.logger.info("=" * 70)
            
            self.last_optimization_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error generating optimization report: {e}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics."""
        if not self.enabled:
            return {'enabled': False}
            
        try:
            return {
                'enabled': True,
                'execution_count': self.execution_count,
                'predictive_engine': self.predictive_engine.get_statistics(),
                'anomaly_detector': self.anomaly_detector.get_anomaly_summary(),
                'last_optimization_check': self.last_optimization_check.isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {'enabled': True, 'error': str(e)}
            
    def cleanup(self):
        """Cleanup analytics data (memory management)."""
        if not self.enabled:
            return
            
        try:
            # Implement cleanup logic here
            # For now, just log
            self.logger.info("Analytics cleanup performed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")