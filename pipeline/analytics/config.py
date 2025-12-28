#!/usr/bin/env python3
"""
Analytics Configuration

Provides configuration management for analytics components.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path

@dataclass
class AnalyticsConfig:
    """Configuration for analytics system"""
    
    # General settings
    enabled: bool = True
    log_level: str = 'INFO'
    
    # Predictive engine settings
    predictive_enabled: bool = True
    predictive_min_history: int = 10  # Minimum history for predictions
    predictive_confidence_threshold: float = 0.5
    
    # Anomaly detector settings
    anomaly_enabled: bool = True
    anomaly_window_size: int = 100
    anomaly_z_score_threshold: float = 3.0
    anomaly_success_rate_threshold: float = 0.7
    
    # Optimizer settings
    optimizer_enabled: bool = True
    optimizer_interval: int = 100  # Check every N executions
    optimizer_quick_win_effort: str = 'LOW'
    optimizer_quick_win_priority: list = field(default_factory=lambda: ['HIGH', 'CRITICAL'])
    
    # Memory management
    max_history_size: int = 1000  # Maximum history records per component
    cleanup_interval: int = 500  # Cleanup every N executions
    
    # Thresholds
    phase_slow_threshold: float = 600.0  # 10 minutes
    memory_high_threshold: float = 2048.0  # 2GB
    cpu_high_threshold: float = 80.0  # 80%
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'enabled': self.enabled,
            'log_level': self.log_level,
            'predictive': {
                'enabled': self.predictive_enabled,
                'min_history': self.predictive_min_history,
                'confidence_threshold': self.predictive_confidence_threshold
            },
            'anomaly': {
                'enabled': self.anomaly_enabled,
                'window_size': self.anomaly_window_size,
                'z_score_threshold': self.anomaly_z_score_threshold,
                'success_rate_threshold': self.anomaly_success_rate_threshold
            },
            'optimizer': {
                'enabled': self.optimizer_enabled,
                'interval': self.optimizer_interval,
                'quick_win_effort': self.optimizer_quick_win_effort,
                'quick_win_priority': self.optimizer_quick_win_priority
            },
            'memory': {
                'max_history_size': self.max_history_size,
                'cleanup_interval': self.cleanup_interval
            },
            'thresholds': {
                'phase_slow': self.phase_slow_threshold,
                'memory_high': self.memory_high_threshold,
                'cpu_high': self.cpu_high_threshold
            }
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsConfig':
        """Create from dictionary"""
        config = cls()
        
        config.enabled = data.get('enabled', True)
        config.log_level = data.get('log_level', 'INFO')
        
        if 'predictive' in data:
            pred = data['predictive']
            config.predictive_enabled = pred.get('enabled', True)
            config.predictive_min_history = pred.get('min_history', 10)
            config.predictive_confidence_threshold = pred.get('confidence_threshold', 0.5)
            
        if 'anomaly' in data:
            anom = data['anomaly']
            config.anomaly_enabled = anom.get('enabled', True)
            config.anomaly_window_size = anom.get('window_size', 100)
            config.anomaly_z_score_threshold = anom.get('z_score_threshold', 3.0)
            config.anomaly_success_rate_threshold = anom.get('success_rate_threshold', 0.7)
            
        if 'optimizer' in data:
            opt = data['optimizer']
            config.optimizer_enabled = opt.get('enabled', True)
            config.optimizer_interval = opt.get('interval', 100)
            config.optimizer_quick_win_effort = opt.get('quick_win_effort', 'LOW')
            config.optimizer_quick_win_priority = opt.get('quick_win_priority', ['HIGH', 'CRITICAL'])
            
        if 'memory' in data:
            mem = data['memory']
            config.max_history_size = mem.get('max_history_size', 1000)
            config.cleanup_interval = mem.get('cleanup_interval', 500)
            
        if 'thresholds' in data:
            thresh = data['thresholds']
            config.phase_slow_threshold = thresh.get('phase_slow', 600.0)
            config.memory_high_threshold = thresh.get('memory_high', 2048.0)
            config.cpu_high_threshold = thresh.get('cpu_high', 80.0)
            
        return config
        
    def save(self, filepath: str):
        """Save configuration to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load(cls, filepath: str) -> 'AnalyticsConfig':
        """Load configuration from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
        
    @classmethod
    def load_or_default(cls, filepath: Optional[str] = None) -> 'AnalyticsConfig':
        """Load configuration or return default"""
        if filepath and Path(filepath).exists():
            try:
                return cls.load(filepath)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return cls()
        return cls()

# Default configuration
DEFAULT_CONFIG = AnalyticsConfig()

def get_default_config() -> AnalyticsConfig:
    """Get default configuration"""
    return AnalyticsConfig()

def create_default_config_file(filepath: str = 'analytics_config.json'):
    """Create default configuration file"""
    config = AnalyticsConfig()
    config.save(filepath)
    print(f"Created default configuration file: {filepath}")

if __name__ == '__main__':
    # Create default config file
    create_default_config_file()
    print("\nDefault configuration:")
    print(json.dumps(DEFAULT_CONFIG.to_dict(), indent=2))