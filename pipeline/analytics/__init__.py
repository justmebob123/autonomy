"""
Analytics Package

Provides analytics capabilities for the autonomy pipeline:
- Predictive analytics
- Anomaly detection
- Optimization recommendations
- Configuration management
- Memory management
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

from .config import (
    AnalyticsConfig,
    get_default_config,
    create_default_config_file
)

from .memory_manager import MemoryManager

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
    'OptimizationPlan',
    
    # Configuration
    'AnalyticsConfig',
    'get_default_config',
    'create_default_config_file',
    
    # Memory Management
    'MemoryManager'
]