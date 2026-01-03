"""
Base orchestrator for all phases.

This module provides a base class for phase-specific orchestrators,
helping to break down massive execute() methods into manageable pieces.
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging


class ExecutionStage(Enum):
    """Stages of phase execution."""
    INITIALIZATION = "initialization"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"


class BaseOrchestrator:
    """
    Base class for phase-specific orchestrators.
    
    Provides common patterns for orchestrating complex phase execution,
    including stage management, error handling, and state transitions.
    """
    
    def __init__(self, phase_name: str, logger: logging.Logger = None):
        """
        Initialize the orchestrator.
        
        Args:
            phase_name: Name of the phase being orchestrated
            logger: Optional logger instance
        """
        self.phase_name = phase_name
        self.logger = logger or logging.getLogger(f"{phase_name}Orchestrator")
        self.current_stage = None
        self.execution_history = []
    
    def log_stage(self, stage: ExecutionStage, message: str):
        """
        Log a stage transition or event.
        
        Args:
            stage: The execution stage
            message: Log message
        """
        self.current_stage = stage
        self.execution_history.append({
            'stage': stage.value,
            'message': message
        })
        self.logger.info(f"[{stage.value}] {message}")
    
    def execute_stage(
        self,
        stage: ExecutionStage,
        stage_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a stage with error handling and logging.
        
        Args:
            stage: The execution stage
            stage_func: Function to execute for this stage
            *args: Positional arguments for stage_func
            **kwargs: Keyword arguments for stage_func
            
        Returns:
            Result from stage_func
            
        Raises:
            Exception: Re-raises any exception after logging
        """
        self.log_stage(stage, f"Starting {stage.value}")
        
        try:
            result = stage_func(*args, **kwargs)
            self.log_stage(stage, f"Completed {stage.value}")
            return result
        except Exception as e:
            self.logger.error(f"[{stage.value}] Error: {str(e)}")
            raise
    
    def should_continue_execution(self, condition: bool, reason: str = "") -> bool:
        """
        Check if execution should continue.
        
        Args:
            condition: Boolean condition to check
            reason: Reason for stopping (if condition is False)
            
        Returns:
            True if execution should continue, False otherwise
        """
        if not condition:
            self.logger.info(f"Stopping execution: {reason}")
            return False
        return True
    
    def handle_task_batch(
        self,
        tasks: List[Any],
        task_handler: Callable,
        batch_size: Optional[int] = None
    ) -> List[Any]:
        """
        Handle a batch of tasks with optional batching.
        
        Args:
            tasks: List of tasks to process
            task_handler: Function to handle each task
            batch_size: Optional batch size for processing
            
        Returns:
            List of results from task_handler
        """
        results = []
        
        if batch_size:
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} tasks)")
                for task in batch:
                    results.append(task_handler(task))
        else:
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"Processing task {i}/{len(tasks)}")
                results.append(task_handler(task))
        
        return results
    
    def collect_execution_metrics(self) -> Dict:
        """
        Collect metrics about the execution.
        
        Returns:
            Dictionary containing execution metrics
        """
        return {
            'phase': self.phase_name,
            'current_stage': self.current_stage.value if self.current_stage else None,
            'stages_completed': len(self.execution_history),
            'history': self.execution_history
        }
    
    def validate_prerequisites(self, prerequisites: Dict[str, Any]) -> bool:
        """
        Validate that all prerequisites are met.
        
        Args:
            prerequisites: Dictionary of prerequisite checks
            
        Returns:
            True if all prerequisites are met, False otherwise
        """
        for name, condition in prerequisites.items():
            if not condition:
                self.logger.error(f"Prerequisite not met: {name}")
                return False
        
        self.logger.info("All prerequisites validated")
        return True
    
    def handle_state_transition(
        self,
        from_state: str,
        to_state: str,
        state_object: Any,
        transition_func: Optional[Callable] = None
    ) -> bool:
        """
        Handle a state transition with optional custom logic.
        
        Args:
            from_state: Current state
            to_state: Target state
            state_object: Object whose state is being transitioned
            transition_func: Optional function to execute during transition
            
        Returns:
            True if transition was successful, False otherwise
        """
        self.logger.info(f"State transition: {from_state} -> {to_state}")
        
        try:
            if transition_func:
                transition_func(state_object, from_state, to_state)
            
            if hasattr(state_object, 'status'):
                state_object.status = to_state
            
            return True
        except Exception as e:
            self.logger.error(f"State transition failed: {str(e)}")
            return False
    
    def aggregate_results(
        self,
        results: List[Any],
        aggregator: Callable[[List[Any]], Any]
    ) -> Any:
        """
        Aggregate results from multiple operations.
        
        Args:
            results: List of results to aggregate
            aggregator: Function to aggregate results
            
        Returns:
            Aggregated result
        """
        self.logger.info(f"Aggregating {len(results)} results")
        return aggregator(results)
    
    def retry_with_backoff(
        self,
        operation: Callable,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            max_attempts: Maximum number of attempts
            backoff_factor: Backoff multiplier between attempts
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result from operation
            
        Raises:
            Exception: Re-raises the last exception if all attempts fail
        """
        import time
        
        last_exception = None
        wait_time = 1.0
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Attempt {attempt}/{max_attempts}")
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt} failed: {str(e)}")
                
                if attempt < max_attempts:
                    self.logger.info(f"Waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    wait_time *= backoff_factor
        
        self.logger.error(f"All {max_attempts} attempts failed")
        raise last_exception