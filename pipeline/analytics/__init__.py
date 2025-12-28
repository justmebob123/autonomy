"""
Analytics Package

Provides analytics capabilities for the autonomy pipeline:
- Predictive analytics
- Anomaly detection
- Optimization recommendations
"""

from .predictive_engine import (
    PredictiveAnalyticsEngine,
    PhasePrediction,
    TaskPrediction,
    IssuePrediction,
    ResourceForecast,
    ObjectiveTrajectory
)

from .anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    AnomalyPattern
)

from .optimizer import (
    OptimizationEngine,
    Optimization,
    OptimizationPlan
)

__all__ = [
    # Predictive Engine
    'PredictiveAnalyticsEngine',
    'PhasePrediction',
    'TaskPrediction',
    'IssuePrediction',
    'ResourceForecast',
    'ObjectiveTrajectory',
    
    # Anomaly Detector
    'AnomalyDetector',
    'Anomaly',
    'AnomalyPattern',
    
    # Optimizer
    'OptimizationEngine',
    'Optimization',
    'OptimizationPlan'
]