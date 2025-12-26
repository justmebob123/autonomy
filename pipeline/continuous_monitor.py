"""
Continuous Monitoring System

This module provides continuous monitoring capabilities for long-running applications,
enabling the system to detect and respond to issues in real-time without timeouts.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import logging
from queue import Queue, Empty

from .runtime_tester import RuntimeTester
from .state.manager import StateManager
from .correlation_engine import CorrelationEngine


class ContinuousMonitor:
    """
    Continuous monitoring system for long-running applications.
    
    This monitor runs indefinitely, checking for errors and triggering
    troubleshooting as needed without any timeouts.
    """
    
    def __init__(
        self,
        runtime_tester: RuntimeTester,
        state_manager: StateManager,
        check_interval: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize continuous monitor.
        
        Args:
            runtime_tester: RuntimeTester instance
            state_manager: StateManager instance (replaces unified_state)
            check_interval: Interval between checks in seconds
            logger: Logger instance
        """
        self.runtime_tester = runtime_tester
        self.state_manager = state_manager
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self.correlation_engine = CorrelationEngine()
        
        self.running = False
        self.monitor_thread = None
        self.error_count = 0
        self.last_error_time = None
        self.troubleshooting_in_progress = False
        
        # Callbacks
        self.on_error_detected = None
        self.on_troubleshooting_complete = None
        
    def start(self):
        """Start continuous monitoring."""
        if self.running:
            self.logger.warning("Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Continuous monitoring started")
    
    def stop(self):
        """Stop continuous monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Continuous monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop - runs continuously."""
        self.logger.info("Entering continuous monitoring loop (no timeout)")
        
        while self.running:
            try:
                # Check for errors
                errors = self._check_for_errors()
                
                if errors:
                    self._handle_errors(errors)
                
                # Check system health
                self._check_system_health()
                
                # Sleep briefly to avoid CPU spinning
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                # Don't stop on errors - keep monitoring
                time.sleep(self.check_interval)
    
    def _check_for_errors(self) -> List[Dict[str, Any]]:
        """
        Check for errors in the running application.
        
        Returns:
            List of detected errors
        """
        errors = []
        
        try:
            # Check if process is still running
            if not self.runtime_tester.is_running():
                exit_code = self.runtime_tester.get_exit_code()
                if exit_code and exit_code != 0:
                    errors.append({
                        'type': 'process_exit',
                        'exit_code': exit_code,
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    })
            
            # Check for errors in error queue
            queued_errors = self.runtime_tester.get_errors()
            for error in queued_errors:
                error['timestamp'] = error.get('timestamp', datetime.now().isoformat())
                errors.append(error)
            
        except Exception as e:
            self.logger.error(f"Error checking for errors: {e}")
        
        return errors
    
    def _handle_errors(self, errors: List[Dict[str, Any]]):
        """
        Handle detected errors.
        
        Args:
            errors: List of errors to handle
        """
        self.error_count += len(errors)
        self.last_error_time = datetime.now()
        
        # Add errors to state (load, modify, save pattern)
        state = self.state_manager.load()
        for error in errors:
            # Add error to task if task_id is available
            if 'task_id' in error and error['task_id'] in state.tasks:
                task = state.tasks[error['task_id']]
                task.add_error(
                    error_type=error.get('type', 'unknown'),
                    message=error.get('message', 'No message'),
                    phase=error.get('phase', 'unknown')
                )
        self.state_manager.save(state)
        
        # Log errors
        self.logger.warning(f"Detected {len(errors)} errors")
        for error in errors:
            self.logger.warning(f"  • {error.get('type', 'unknown')}: {error.get('message', 'No message')}")
        
        # Trigger callback if set
        if self.on_error_detected:
            try:
                self.on_error_detected(errors)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
        
        # Trigger troubleshooting if not already in progress
        if not self.troubleshooting_in_progress:
            self._trigger_troubleshooting(errors)
    
    def _trigger_troubleshooting(self, errors: List[Dict[str, Any]]):
        """
        Trigger application troubleshooting.
        
        Args:
            errors: List of errors that triggered troubleshooting
        """
        self.troubleshooting_in_progress = True
        
        try:
            self.logger.info("Triggering application troubleshooting...")
            
            # Get working directory from runtime tester
            working_dir = Path.cwd()  # Default to current directory
            
            # Run troubleshooting
            results = self.runtime_tester.perform_application_troubleshooting(working_dir)
            
            # Add results to state
            state = self.state_manager.load()
            self.state_manager.update_from_troubleshooting(state, results)
            
            # Add findings to correlation engine
            self._add_findings_to_correlation_engine(results)
            
            # Run correlation analysis
            correlations = self.correlation_engine.correlate()
            
            # Add correlations to state
            state = self.state_manager.load()
            for correlation in correlations:
                self.state_manager.add_correlation(state, correlation)
            
            # Log results
            self.logger.info(f"Troubleshooting complete. Found {len(correlations)} correlations")
            
            # Trigger callback if set
            if self.on_troubleshooting_complete:
                try:
                    self.on_troubleshooting_complete(results, correlations)
                except Exception as e:
                    self.logger.error(f"Error in callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error during troubleshooting: {e}", exc_info=True)
        
        finally:
            self.troubleshooting_in_progress = False
    
    def _add_findings_to_correlation_engine(self, results: Dict[str, Any]):
        """
        Add troubleshooting findings to correlation engine.
        
        Args:
            results: Troubleshooting results
        """
        # Add log analysis findings
        if results.get('log_analysis'):
            log_results = results['log_analysis']
            for error in log_results.get('errors', []):
                self.correlation_engine.add_finding('log_analyzer', {
                    'type': 'error',
                    **error
                })
        
        # Add call chain findings
        if results.get('call_chain_trace'):
            call_results = results['call_chain_trace']
            for func in call_results.get('error_prone_functions', []):
                self.correlation_engine.add_finding('call_chain_tracer', {
                    'type': 'error_prone_function',
                    **func
                })
        
        # Add change history findings
        if results.get('change_history'):
            change_results = results['change_history']
            for change in change_results.get('risky_changes', []):
                self.correlation_engine.add_finding('change_history_analyzer', {
                    'type': 'risky_change',
                    **change
                })
        
        # Add config findings
        if results.get('config_investigation'):
            config_results = results['config_investigation']
            for issue in config_results.get('config_issues', []):
                self.correlation_engine.add_finding('config_investigator', {
                    'type': 'issue',
                    **issue
                })
        
        # Add architecture findings
        if results.get('architecture_analysis'):
            arch_results = results['architecture_analysis']
            for issue in arch_results.get('issues', []):
                self.correlation_engine.add_finding('architecture_analyzer', {
                    'type': 'issue',
                    **issue
                })
    
    def _check_system_health(self):
        """Check overall system health."""
        try:
            # Record performance metrics
            state = self.state_manager.load()
            if self.runtime_tester.is_running():
                self.state_manager.add_performance_metric(state, 'uptime', time.time())
            
            # Check error rate
            if self.last_error_time:
                time_since_error = (datetime.now() - self.last_error_time).total_seconds()
                self.state_manager.add_performance_metric(state, 'time_since_error', time_since_error)
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            Status dictionary
        """
        return {
            'running': self.running,
            'error_count': self.error_count,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'troubleshooting_in_progress': self.troubleshooting_in_progress,
            'process_running': self.runtime_tester.is_running()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.
        
        Returns:
            Statistics dictionary
        """
        state = self.state_manager.load()
        return {
            'total_errors': self.error_count,
            'fix_effectiveness': self.state_manager.get_fix_effectiveness(state),
            'correlations_found': len(self.correlation_engine.correlations),
            'learned_patterns': len(state.learned_patterns),
            'performance_metrics': len(state.performance_metrics)
        }


class ContinuousMonitorManager:
    """
    Manager for multiple continuous monitors.
    
    Allows monitoring multiple applications simultaneously.
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize monitor manager.
        
        Args:
            unified_state: Shared unified state
        """
        self.state_manager = unified_state
        self.monitors = {}
        self.logger = logging.getLogger(__name__)
    
    def add_monitor(self, name: str, monitor: ContinuousMonitor):
        """
        Add a monitor.
        
        Args:
            name: Monitor name
            monitor: ContinuousMonitor instance
        """
        self.monitors[name] = monitor
        self.logger.info(f"Added monitor: {name}")
    
    def start_all(self):
        """Start all monitors."""
        for name, monitor in self.monitors.items():
            try:
                monitor.start()
                self.logger.info(f"Started monitor: {name}")
            except Exception as e:
                self.logger.error(f"Failed to start monitor {name}: {e}")
    
    def stop_all(self):
        """Stop all monitors."""
        for name, monitor in self.monitors.items():
            try:
                monitor.stop()
                self.logger.info(f"Stopped monitor: {name}")
            except Exception as e:
                self.logger.error(f"Failed to stop monitor {name}: {e}")
    
    def get_status_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all monitors.
        
        Returns:
            Dictionary of monitor statuses
        """
        return {
            name: monitor.get_status()
            for name, monitor in self.monitors.items()
        }
    
    def get_statistics_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all monitors.
        
        Returns:
            Dictionary of monitor statistics
        """
        return {
            name: monitor.get_statistics()
            for name, monitor in self.monitors.items()
        }