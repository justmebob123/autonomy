#!/usr/bin/env python3
"""
Memory Management for Analytics

Provides memory management and cleanup for analytics components.
"""

from typing import Dict, List, Any
from collections import defaultdict
import logging

class MemoryManager:
    """
    Manages memory for analytics components.
    
    Provides:
    - Size limits for historical data
    - Automatic cleanup
    - Memory usage monitoring
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize memory manager.
        
        Args:
            max_size: Maximum number of records per component
        """
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
        
    def limit_dict_of_lists(self, data: Dict[str, List[Any]], max_size: int = None) -> int:
        """
        Limit size of dictionary of lists.
        
        Args:
            data: Dictionary with list values
            max_size: Maximum size per list (uses self.max_size if None)
            
        Returns:
            Number of items removed
        """
        max_size = max_size or self.max_size
        removed = 0
        
        for key, items in data.items():
            if len(items) > max_size:
                pass
                # Keep only the most recent max_size items
                removed_count = len(items) - max_size
                data[key] = items[-max_size:]
                removed += removed_count
                
        return removed
        
    def limit_list(self, data: List[Any], max_size: int = None) -> int:
        """
        Limit size of list.
        
        Args:
            data: List to limit
            max_size: Maximum size (uses self.max_size if None)
            
        Returns:
            Number of items removed
        """
        max_size = max_size or self.max_size
        
        if len(data) > max_size:
            removed = len(data) - max_size
            # Keep only the most recent max_size items
            del data[:-max_size]
            return removed
            
        return 0
        
    def cleanup_predictive_engine(self, engine) -> Dict[str, int]:
        """
        Cleanup predictive engine memory.
        
        Args:
            engine: PredictiveAnalyticsEngine instance
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'phase_history': 0,
            'task_history': 0,
            'issue_history': 0,
            'resource_history': 0,
            'objective_history': 0
        }
        
        try:
            pass
            # Limit phase history
            stats['phase_history'] = self.limit_dict_of_lists(engine.phase_history)
            
            # Limit task history
            stats['task_history'] = self.limit_dict_of_lists(engine.task_history)
            
            # Limit issue history
            stats['issue_history'] = self.limit_list(engine.issue_history)
            
            # Limit resource history
            stats['resource_history'] = self.limit_dict_of_lists(engine.resource_history)
            
            # Limit objective history
            stats['objective_history'] = self.limit_dict_of_lists(engine.objective_history)
            
            total_removed = sum(stats.values())
            if total_removed > 0:
                self.logger.info(f"Predictive engine cleanup: removed {total_removed} records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up predictive engine: {e}")
            
        return stats
        
    def cleanup_optimizer(self, optimizer) -> Dict[str, int]:
        """
        Cleanup optimizer memory.
        
        Args:
            optimizer: OptimizationEngine instance
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'phase_performance': 0,
            'resource_usage': 0,
            'quality_metrics': 0,
            'task_completion_times': 0
        }
        
        try:
            pass
            # Limit phase performance
            stats['phase_performance'] = self.limit_dict_of_lists(optimizer.phase_performance)
            
            # Limit resource usage
            stats['resource_usage'] = self.limit_dict_of_lists(optimizer.resource_usage)
            
            # Limit quality metrics
            stats['quality_metrics'] = self.limit_dict_of_lists(optimizer.quality_metrics)
            
            # Limit task completion times
            stats['task_completion_times'] = self.limit_dict_of_lists(optimizer.task_completion_times)
            
            total_removed = sum(stats.values())
            if total_removed > 0:
                self.logger.info(f"Optimizer cleanup: removed {total_removed} records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up optimizer: {e}")
            
        return stats
        
    def cleanup_anomaly_detector(self, detector) -> Dict[str, int]:
        """
        Cleanup anomaly detector memory.
        
        Note: Anomaly detector uses deque with maxlen, so it auto-manages memory.
        This method just cleans up detected anomalies and patterns.
        
        Args:
            detector: AnomalyDetector instance
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'detected_anomalies': 0,
            'anomaly_patterns': 0
        }
        
        try:
            pass
            # Limit detected anomalies (keep last 100)
            if len(detector.detected_anomalies) > 100:
                removed = len(detector.detected_anomalies) - 100
                detector.detected_anomalies = detector.detected_anomalies[-100:]
                stats['detected_anomalies'] = removed
                
            # Limit anomaly patterns (keep last 50)
            if len(detector.anomaly_patterns) > 50:
                removed = len(detector.anomaly_patterns) - 50
                detector.anomaly_patterns = detector.anomaly_patterns[-50:]
                stats['anomaly_patterns'] = removed
                
            total_removed = sum(stats.values())
            if total_removed > 0:
                self.logger.info(f"Anomaly detector cleanup: removed {total_removed} records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up anomaly detector: {e}")
            
        return stats
        
    def cleanup_all(self, predictive_engine, anomaly_detector, optimizer) -> Dict[str, Any]:
        """
        Cleanup all analytics components.
        
        Args:
            predictive_engine: PredictiveAnalyticsEngine instance
            anomaly_detector: AnomalyDetector instance
            optimizer: OptimizationEngine instance
            
        Returns:
            Dictionary with all cleanup statistics
        """
        stats = {
            'predictive_engine': self.cleanup_predictive_engine(predictive_engine),
            'anomaly_detector': self.cleanup_anomaly_detector(anomaly_detector),
            'optimizer': self.cleanup_optimizer(optimizer)
        }
        
        total_removed = (
            sum(stats['predictive_engine'].values()) +
            sum(stats['anomaly_detector'].values()) +
            sum(stats['optimizer'].values())
        )
        
        self.logger.info(f"Total cleanup: removed {total_removed} records across all components")
        
        return stats
        
    def get_memory_usage(self, predictive_engine, anomaly_detector, optimizer) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Args:
            predictive_engine: PredictiveAnalyticsEngine instance
            anomaly_detector: AnomalyDetector instance
            optimizer: OptimizationEngine instance
            
        Returns:
            Dictionary with memory usage statistics
        """
        try:
            return {
                'predictive_engine': {
                    'phase_history': sum(len(v) for v in predictive_engine.phase_history.values()),
                    'task_history': sum(len(v) for v in predictive_engine.task_history.values()),
                    'issue_history': len(predictive_engine.issue_history),
                    'resource_history': sum(len(v) for v in predictive_engine.resource_history.values()),
                    'objective_history': sum(len(v) for v in predictive_engine.objective_history.values())
                },
                'anomaly_detector': {
                    'phase_metrics': sum(len(v) for v in anomaly_detector.phase_metrics.values()),
                    'task_metrics': sum(len(v) for v in anomaly_detector.task_metrics.values()),
                    'resource_metrics': sum(len(v) for v in anomaly_detector.resource_metrics.values()),
                    'message_metrics': len(anomaly_detector.message_metrics),
                    'objective_metrics': sum(len(v) for v in anomaly_detector.objective_metrics.values()),
                    'detected_anomalies': len(anomaly_detector.detected_anomalies),
                    'anomaly_patterns': len(anomaly_detector.anomaly_patterns)
                },
                'optimizer': {
                    'phase_performance': sum(len(v) for v in optimizer.phase_performance.values()),
                    'resource_usage': sum(len(v) for v in optimizer.resource_usage.values()),
                    'quality_metrics': sum(len(v) for v in optimizer.quality_metrics.values()),
                    'task_completion_times': sum(len(v) for v in optimizer.task_completion_times.values())
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return {}