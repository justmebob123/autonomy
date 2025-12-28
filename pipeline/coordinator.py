"""
Phase Coordinator

Orchestrates the pipeline phases and determines the next action to take.
This is the main control loop that NEVER exits - it continuously finds work to do.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import PipelineConfig
from .client import OllamaClient
from .state.manager import StateManager, PipelineState, TaskState, TaskStatus
from .logging_setup import get_logger, setup_logging


class PhaseCoordinator:
    """
    Coordinates pipeline phases and manages the main execution loop.
    
    The coordinator NEVER exits on its own - it continuously cycles through:
    1. Initial planning (if no tasks)
    2. Coding (implement tasks)
    3. QA (review code)
    4. Debugging (fix issues)
    5. Documentation (update README/ARCHITECTURE)
    6. Project Planning (expand project when all tasks complete)
    
    The loop only exits via:
    - KeyboardInterrupt (Ctrl+C)
    - max_iterations limit (if set > 0)
    - Unrecoverable error
    """
    
    def __init__(self, config: PipelineConfig, verbose: bool = False):
        self.config = config
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        self.verbose = verbose
        
        # Initialize client
        self.client = OllamaClient(config)
        
        # Initialize shared state manager
        self.state_manager = StateManager(self.project_dir)
        
        # Initialize shared file tracker
        from .state.file_tracker import FileTracker
        self.file_tracker = FileTracker(self.project_dir)
        
        # Initialize shared registries
        from .prompt_registry import PromptRegistry
        from .tool_registry import ToolRegistry
        from .role_registry import RoleRegistry
        self.prompt_registry = PromptRegistry(self.project_dir)
        self.tool_registry = ToolRegistry(self.project_dir)
        self.role_registry = RoleRegistry(self.project_dir, self.client)
        self.logger.info("📚 Shared registries initialized")
        
        # Initialize message bus for phase-to-phase communication
        from .messaging import MessageBus, MessageType
        self.message_bus = MessageBus(state_manager=self.state_manager)
        self.logger.info("📨 Message bus initialized")
        
        # Subscribe coordinator to critical events
        self.message_bus.subscribe("coordinator", [
            MessageType.OBJECTIVE_BLOCKED,
            MessageType.OBJECTIVE_CRITICAL,
            MessageType.PHASE_ERROR,
            MessageType.SYSTEM_ALERT,
            MessageType.HEALTH_DEGRADED,
            MessageType.ISSUE_FOUND,
        ])
        
        # Initialize shared specialists (created once, used by all phases)
        from .orchestration.unified_model_tool import UnifiedModelTool
        from .orchestration.specialists import (
            create_coding_specialist,
            create_reasoning_specialist,
            create_analysis_specialist
        )
        
        # Create unified model tools (using config for server URLs)
        self.coding_tool = UnifiedModelTool("qwen2.5-coder:32b", "http://ollama02:11434")
        self.reasoning_tool = UnifiedModelTool("qwen2.5:32b", "http://ollama02:11434")
        self.analysis_tool = UnifiedModelTool("qwen2.5:14b", "http://ollama01.thiscluster.net:11434")
        
        # Create specialists (shared across all phases)
        self.coding_specialist = create_coding_specialist(self.coding_tool)
        self.reasoning_specialist = create_reasoning_specialist(self.reasoning_tool)
        self.analysis_specialist = create_analysis_specialist(self.analysis_tool)
        self.logger.info("🤖 Shared specialists initialized (coding, reasoning, analysis)")
        
        # Initialize phases (lazy import to avoid circular deps)
        self.phases = self._init_phases()
        
        # NOTE: Arbiter is available but not currently used
        # Using simple direct logic for phase transitions instead
        # To enable: uncomment below and integrate with _determine_next_action
        # from .orchestration.arbiter import ArbiterModel
        # self.arbiter = ArbiterModel(self.project_dir)
        
        # Hyperdimensional polytopic structure
        self.polytope = {
            'vertices': {},  # phase_name -> {type, dimensions}
            'edges': {},     # phase_name -> [adjacent_phases]
            'dimensions': 7,
            'self_awareness_level': 0.0,
            'recursion_depth': 0,
            'max_recursion_depth': 61
        }
        
        # Initialize polytopic structure from phases
        self._initialize_polytopic_structure()
        
        # Correlation engine for cross-phase analysis
        from .correlation_engine import CorrelationEngine
        self.correlation_engine = CorrelationEngine()
        
        # Analytics integration for predictive analytics, anomaly detection, and optimization
        try:
            from .coordinator_analytics_integration import AnalyticsIntegration
            self.analytics = AnalyticsIntegration(
                enabled=True,
                config={
                    'anomaly_window_size': 100,
                    'optimization_interval': 100,
                    'max_history_size': 1000,
                    'cleanup_interval': 500
                }
            )
            self.logger.info("📊 Analytics integration initialized")
        except Exception as e:
            self.logger.warning(f"Analytics integration not available: {e}")
            self.analytics = None
        
        # INTEGRATION: Pattern Recognition System
        from .pattern_recognition import PatternRecognitionSystem
        self.pattern_recognition = PatternRecognitionSystem(self.project_dir)
        self.pattern_recognition.load_patterns()
        self.logger.info("🔍 Pattern recognition system initialized")
        
        # INTEGRATION: Pattern Optimizer
        from .pattern_optimizer import PatternOptimizer
        self.pattern_optimizer = PatternOptimizer(self.project_dir)
        self.execution_count = 0  # Track executions for periodic optimization
        self.logger.info("⚡ Pattern optimizer initialized")
        
        # INTEGRATION: Tool Creator
        from .tool_creator import ToolCreator
        self.tool_creator = ToolCreator(self.project_dir)
        self.logger.info("🔨 Tool creator initialized")
        
        # INTEGRATION: Tool Validator
        from .tool_validator import ToolValidator
        self.tool_validator = ToolValidator(self.project_dir)
        self.logger.info("✅ Tool validator initialized")
        
        # INTEGRATION: Strategic Management System with Polytopic Navigation
        from .polytopic import PolytopicObjectiveManager
        from .issue_tracker import IssueTracker
        
        # Use PolytopicObjectiveManager for 7D hyperdimensional objective management
        self.objective_manager = PolytopicObjectiveManager(self.project_dir, self.state_manager)
        self.issue_tracker = IssueTracker(self.project_dir, self.state_manager)
        self.logger.info("🎯 Strategic management system initialized (polytopic objectives + issues)")
        self.logger.info("📐 7D dimensional navigation enabled")
    
    def _init_phases(self) -> Dict:
        """Initialize all pipeline phases"""
        from .phases import (
            PlanningPhase,
            CodingPhase,
            QAPhase,
            DebuggingPhase,
            ProjectPlanningPhase,
            DocumentationPhase,
        )
        from .phases.investigation import InvestigationPhase
        from .phases.prompt_design import PromptDesignPhase
        from .phases.tool_design import ToolDesignPhase
        from .phases.role_design import RoleDesignPhase
        from .phases.tool_evaluation import ToolEvaluationPhase
        from .phases.prompt_improvement import PromptImprovementPhase
        from .phases.role_improvement import RoleImprovementPhase
        
        # BasePhase.__init__ now accepts shared resources to eliminate duplication
        # This reduces resource usage from 155 objects to 11 objects (14x improvement)
        shared_kwargs = {
            'state_manager': self.state_manager,
            'file_tracker': self.file_tracker,
            'prompt_registry': self.prompt_registry,
            'tool_registry': self.tool_registry,
            'role_registry': self.role_registry,
            'coding_specialist': self.coding_specialist,
            'reasoning_specialist': self.reasoning_specialist,
            'analysis_specialist': self.analysis_specialist,
            'message_bus': self.message_bus,
        }
        
        return {
            "planning": PlanningPhase(self.config, self.client, **shared_kwargs),
            "coding": CodingPhase(self.config, self.client, **shared_kwargs),
            "qa": QAPhase(self.config, self.client, **shared_kwargs),
            "investigation": InvestigationPhase(self.config, self.client, **shared_kwargs),
            "debugging": DebuggingPhase(self.config, self.client, **shared_kwargs),
            "debug": DebuggingPhase(self.config, self.client, **shared_kwargs),  # Alias
            "project_planning": ProjectPlanningPhase(self.config, self.client, **shared_kwargs),
            "documentation": DocumentationPhase(self.config, self.client, **shared_kwargs),
            # Meta-agent phases (Integration Point #1)
            "prompt_design": PromptDesignPhase(self.config, self.client, **shared_kwargs),
            "tool_design": ToolDesignPhase(self.config, self.client, **shared_kwargs),
            "role_design": RoleDesignPhase(self.config, self.client, **shared_kwargs),
            # Self-improvement phases (Integration Point #2)
            "tool_evaluation": ToolEvaluationPhase(self.config, self.client, **shared_kwargs),
            "prompt_improvement": PromptImprovementPhase(self.config, self.client, **shared_kwargs),
            "role_improvement": RoleImprovementPhase(self.config, self.client, **shared_kwargs),
        }
    
    
    def _calculate_initial_dimensions(self, phase_name: str, phase_type: str) -> Dict[str, float]:
        """
        Calculate initial dimensional values based on phase characteristics.
        
        Different phases have different dimensional profiles:
        - Planning phases: high temporal, low error
        - Execution phases: high functional, medium error
        - Validation phases: high context, low temporal
        - Meta phases: high integration, medium functional
        
        Args:
            phase_name: Name of the phase
            phase_type: Type of phase (planning, execution, validation, etc.)
        
        Returns:
            Dictionary of dimension values (0.0 to 1.0)
        """
        # Base dimensions (neutral starting point)
        dims = {
            'temporal': 0.5,
            'functional': 0.5,
            'data': 0.5,
            'state': 0.5,
            'error': 0.5,
            'context': 0.5,
            'integration': 0.5
        }
        
        # Adjust based on phase type
        if phase_type == 'planning':
            dims['temporal'] = 0.7  # Planning takes time
            dims['context'] = 0.8   # Needs lots of context
            dims['error'] = 0.2     # Low error rate
            dims['functional'] = 0.3  # Not much execution
        
        elif phase_type == 'execution':
            dims['functional'] = 0.8  # High functionality
            dims['error'] = 0.5       # Medium error potential
            dims['integration'] = 0.6  # Integrates with system
            dims['temporal'] = 0.4    # Relatively fast
        
        elif phase_type == 'validation':
            dims['context'] = 0.9     # Needs full context
            dims['error'] = 0.3       # Low error rate
            dims['functional'] = 0.6  # Moderate functionality
            dims['temporal'] = 0.3    # Quick validation
        
        elif phase_type == 'correction':
            dims['error'] = 0.9       # High error focus
            dims['context'] = 0.8     # Needs context
            dims['functional'] = 0.7  # Fixes functionality
            dims['temporal'] = 0.6    # Takes time
        
        elif phase_type == 'analysis':
            dims['context'] = 0.9     # Needs full context
            dims['data'] = 0.8        # Data-intensive
            dims['temporal'] = 0.7    # Takes time
            dims['error'] = 0.4       # Medium error focus
        
        elif phase_type == 'meta':
            dims['integration'] = 0.9  # High integration
            dims['context'] = 0.7      # Needs context
            dims['functional'] = 0.6   # Moderate functionality
            dims['temporal'] = 0.5     # Medium time
        
        elif phase_type == 'improvement':
            dims['functional'] = 0.8   # Improves functionality
            dims['integration'] = 0.7  # Integrates improvements
            dims['context'] = 0.6      # Needs some context
            dims['error'] = 0.3        # Low error rate
        
        # Phase-specific adjustments
        if 'debug' in phase_name.lower():
            dims['error'] = 0.9
            dims['context'] = 0.8
        
        if 'investigation' in phase_name.lower():
            dims['context'] = 0.9
            dims['data'] = 0.8
        
        if 'documentation' in phase_name.lower():
            dims['context'] = 0.8
            dims['temporal'] = 0.4
            dims['error'] = 0.2
        
        return dims

    def _initialize_polytopic_structure(self):
        """Initialize hyperdimensional polytopic structure from existing phases."""
        phase_types = {
            'planning': 'planning', 'coding': 'execution', 'qa': 'validation',
            'debugging': 'correction', 'investigation': 'analysis',
            'project_planning': 'planning', 'documentation': 'documentation',
            'prompt_design': 'meta', 'tool_design': 'meta', 'role_design': 'meta',
            'tool_evaluation': 'improvement', 'prompt_improvement': 'improvement',
            'role_improvement': 'improvement'
        }
        
        for phase_name in self.phases.keys():
            self.polytope['vertices'][phase_name] = {
                'type': phase_types.get(phase_name, 'unknown'),
                   'dimensions': self._calculate_initial_dimensions(phase_name, phase_types.get(phase_name, 'unknown'))
            }
        
        self.polytope['edges'] = {
            # Core development flow
            'planning': ['coding'],
            'coding': ['qa', 'documentation'],
            'qa': ['debugging', 'documentation'],
            
            # Error handling triangle
            'debugging': ['investigation', 'coding'],
            'investigation': ['debugging', 'coding', 'prompt_design', 'role_design', 'tool_design'],
            
            # Documentation flow
            'documentation': ['planning', 'qa'],
            
            # Project management
            'project_planning': ['planning'],
            
            # Self-improvement cycles
            'prompt_design': ['prompt_improvement'],
            'prompt_improvement': ['prompt_design', 'planning'],
            'role_design': ['role_improvement'],
            'role_improvement': ['role_design', 'planning'],
            
            # Tool development cycle
            'tool_design': ['tool_evaluation'],
            'tool_evaluation': ['tool_design', 'coding']
        }
        
        self.logger.info(f"Polytopic structure: {len(self.polytope['vertices'])} vertices, 7D")
    
    def _should_force_transition(self, state, current_phase: str, last_result=None) -> bool:
        """
        Check if we should force a phase transition due to lack of progress.
        
        CRITICAL: Only force transition on REPEATED FAILURES or NO PROGRESS.
        NEVER force transition after successful operations.
        Uses run history for intelligent pattern detection.
        
        Returns True if:
        - Phase keeps returning "no updates needed" 3+ times
        - Phase has 3+ consecutive failures
        - Phase is oscillating (unstable)
        - Phase has very low success rate (< 30%) as fallback
        
        Does NOT force transition if:
        - Last result was successful with actual work done
        - Phase is improving (recent success rate > older success rate)
        - Files were created or modified
        - Task was completed
        
        Args:
            state: Pipeline state
            current_phase: Current phase name
            last_result: Last PhaseResult (if available)
            
        Returns:
            True if forced transition needed
        """
        # NEVER force transition after success with actual work
        if last_result and last_result.success:
            # Check if actual work was done
            if last_result.files_created or last_result.files_modified:
                # Reset counters on progress
                if hasattr(state, 'no_update_counts'):
                    state.no_update_counts[current_phase] = 0
                return False
        
        # Check no-update count (only for phases that explicitly report no updates)
        no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
        if no_update_count >= 3:
            self.logger.warning(f"Phase {current_phase} returned 'no updates' {no_update_count} times")
            return True
        
        # Enhanced checks with run history
        if hasattr(state, 'phases') and current_phase in state.phases:
            phase_state = state.phases[current_phase]
            
            # Check if phase is improving - DON'T force transition
            if hasattr(phase_state, 'is_improving') and phase_state.is_improving():
                self.logger.info(f"✅ Phase {current_phase} is improving, continuing")
                return False
            
            # Check for consecutive failures - FORCE transition
            if hasattr(phase_state, 'get_consecutive_failures'):
                consecutive_failures = phase_state.get_consecutive_failures()
                
                # Debug logging to understand what's being counted
                self.logger.debug(f"Phase {current_phase} failure analysis:")
                self.logger.debug(f"  - Consecutive failures: {consecutive_failures}")
                self.logger.debug(f"  - Total runs: {phase_state.runs}")
                self.logger.debug(f"  - Total successes: {phase_state.successes}")
                self.logger.debug(f"  - Total failures: {phase_state.failures}")
                if hasattr(phase_state, 'run_history'):
                    recent_history = phase_state.run_history[-10:] if len(phase_state.run_history) > 10 else phase_state.run_history
                    self.logger.debug(f"  - Recent history (last 10): {recent_history}")
                
                if consecutive_failures >= 20:
                    self.logger.warning(
                        f"⚠️  Phase {current_phase} has {consecutive_failures} consecutive failures"
                    )
                    return True
            
            # Check if oscillating - FORCE transition (unstable)
            if hasattr(phase_state, 'is_oscillating') and phase_state.is_oscillating():
                self.logger.warning(f"⚠️  Phase {current_phase} is oscillating (unstable)")
                return True
            
            # REMOVED: Aggregate success rate check
            # This was causing false positives - phases were punished for old failures
            # even after recent successes. We now rely on:
            # 1. Consecutive failures (20+)
            # 2. No-update count (3+)
            # 3. Oscillation detection
            # These are more accurate indicators of current problems
        
        return False
    
    def _select_next_phase_polytopic(self, state, current_phase: str = None):
        """Select next phase using polytopic adjacency with intelligent situation analysis."""
        from .state.manager import TaskStatus
        
        # Use provided current_phase or get from state
        if current_phase is None:
            current_phase = state.current_phase
        
        # Build context from state
        context = {
            'current_phase': current_phase,
            'tasks': state.tasks,
            'errors': [t for t in state.tasks.values() if t.status == TaskStatus.FAILED],
            'pending': [t for t in state.tasks.values() if t.status in (TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.QA_PENDING, TaskStatus.DEBUG_PENDING)],
            'completed': [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED]
        }
        
        # Analyze situation with intelligence
        situation = self._analyze_situation(context)
        
        # Select path intelligently
        return self._select_intelligent_path(situation, current_phase)
    
    def _analyze_situation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive situation analysis with error severity, complexity, and urgency assessment."""
        situation = {
            'has_errors': len(context.get('errors', [])) > 0,
            'has_pending': len(context.get('pending', [])) > 0,
            'needs_planning': len(context.get('tasks', {})) == 0,
            'error_count': len(context.get('errors', [])),
            'pending_count': len(context.get('pending', [])),
            'completed_count': len(context.get('completed', []))
        }
        
        # Assess error severity
        if situation['has_errors']:
            errors = context.get('errors', [])
            situation['error_severity'] = self._assess_error_severity(errors)
        else:
            situation['error_severity'] = 'none'
        
        # Assess complexity
        situation['complexity'] = self._assess_complexity(context)
        
        # Assess urgency
        situation['urgency'] = self._assess_urgency(situation)
        
        # Determine dimensional focus
        situation['dimensional_focus'] = self._determine_dimensional_focus(situation)
        
        # Determine mode
        if situation['error_severity'] in ['high', 'critical']:
            situation['mode'] = 'error_handling'
        elif situation['complexity'] == 'high':
            situation['mode'] = 'deep_analysis'
        else:
            situation['mode'] = 'development'
        
        return situation
    
    def _assess_error_severity(self, errors: List[Any]) -> str:
        """Assess the severity of errors."""
        if not errors:
            return 'none'
        
        error_count = len(errors)
        
        # Check for repeated errors
        repeated_errors = sum(1 for e in errors if hasattr(e, 'attempts') and e.attempts > 2)
        
        if error_count >= 5 or repeated_errors >= 2:
            return 'critical'
        elif error_count >= 3 or repeated_errors >= 1:
            return 'high'
        elif error_count >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """Assess the complexity of the current situation."""
        total_tasks = len(context.get('tasks', {}))
        errors = len(context.get('errors', []))
        
        if total_tasks > 20 or errors > 5:
            return 'high'
        elif total_tasks > 10 or errors > 2:
            return 'medium'
        else:
            return 'low'
    
    def _assess_urgency(self, situation: Dict[str, Any]) -> str:
        """Assess the urgency of the situation."""
        if situation['error_severity'] in ['critical', 'high']:
            return 'high'
        elif situation['has_errors']:
            return 'medium'
        else:
            return 'low'
    
    def _determine_dimensional_focus(self, situation: Dict[str, Any]) -> List[str]:
        """Determine which dimensions to focus on based on situation."""
        focus = []
        
        if situation['has_errors']:
            focus.extend(['error', 'context'])
        
        if situation['complexity'] == 'high':
            focus.extend(['functional', 'integration'])
        
        if situation['urgency'] == 'high':
            focus.append('temporal')
        
        return list(set(focus))  # Remove duplicates
    
    def _select_intelligent_path(self, situation: Dict[str, Any], current_phase: str) -> str:
        """Select optimal execution path based on situation analysis."""
        adjacent = self.polytope['edges'].get(current_phase, ['planning'])
        best_phase, best_score = None, -1
        
        for phase_name in adjacent:
            if phase_name in self.phases:
                score = self._calculate_phase_priority(phase_name, situation)
                if score > best_score:
                    best_score, best_phase = score, phase_name
        
        # Increase self-awareness
        self.polytope['self_awareness_level'] = min(1.0, self.polytope['self_awareness_level'] + 0.001)
        
        return best_phase if best_phase else 'planning'
    
    def _calculate_phase_priority(self, phase_name: str, situation: Dict[str, Any]) -> float:
        """
        Calculate priority score using dimensional alignment.
        
        This integrates the polytope dimensional profiles into phase selection,
        ensuring that phases with high relevant dimensions are prioritized.
        """
        # Get phase dimensional profile
        phase_vertex = self.polytope['vertices'].get(phase_name, {})
        phase_dims = phase_vertex.get('dimensions', {
            'temporal': 0.5,
            'functional': 0.5,
            'error': 0.5,
            'context': 0.5,
            'integration': 0.5
        })
        
        # Start with base score
        score = 0.3
        
        # Calculate dimensional alignment based on situation
        if situation['has_errors']:
            # High error dimension is good for debugging/investigation
            score += phase_dims.get('error', 0.5) * 0.4
            # High context dimension helps understand errors
            score += phase_dims.get('context', 0.5) * 0.2
            
            # Extra boost for critical errors
            if situation['error_severity'] == 'critical':
                score += phase_dims.get('error', 0.5) * 0.2
        
        # Complexity-based dimensional weighting
        if situation['complexity'] == 'high':
            # High functional dimension for complex work
            score += phase_dims.get('functional', 0.5) * 0.3
            # High integration dimension for cross-cutting concerns
            score += phase_dims.get('integration', 0.5) * 0.2
        
        # Urgency-based dimensional weighting
        if situation['urgency'] == 'high':
            # High temporal dimension for urgent work
            score += phase_dims.get('temporal', 0.5) * 0.3
        
        # Pending work routing
        if situation['has_pending']:
            # High functional dimension for execution
            score += phase_dims.get('functional', 0.5) * 0.2
        
        # Planning routing
        if situation['needs_planning']:
            # High temporal and integration dimensions for planning
            score += phase_dims.get('temporal', 0.5) * 0.2
            score += phase_dims.get('integration', 0.5) * 0.2
        
        # Log dimensional reasoning (debug level)
        self.logger.debug(
            f"Phase {phase_name} dimensional score: {score:.3f} "
            f"(dims: error={phase_dims.get('error', 0.5):.2f}, "
            f"functional={phase_dims.get('functional', 0.5):.2f}, "
            f"temporal={phase_dims.get('temporal', 0.5):.2f})"
        )
        
        return score
    

    def _update_polytope_dimensions(self, phase_name: str, result) -> None:
        """
        Update polytope dimensions based on phase execution results.
        
        This makes the polytope adaptive - dimensions change based on:
        - Success/failure rates
        - Error patterns
        - Execution time
        - Complexity indicators
        """
        if phase_name not in self.polytope['vertices']:
            return
        
        vertex = self.polytope['vertices'][phase_name]
        dims = vertex['dimensions']
        
        # Update temporal dimension based on execution time
        if hasattr(result, 'execution_time'):
            # Normalize to 0-1 range (assuming max 60 seconds)
            temporal_score = min(1.0, result.execution_time / 60.0)
            dims['temporal'] = 0.7 * dims['temporal'] + 0.3 * temporal_score
        
        # Update error dimension based on success/failure
        if hasattr(result, 'success'):
            error_score = 0.0 if result.success else 1.0
            dims['error'] = 0.8 * dims['error'] + 0.2 * error_score
        
        # Update functional dimension based on task completion
        if hasattr(result, 'tasks_completed'):
            functional_score = min(1.0, result.tasks_completed / max(1, result.total_tasks))
            dims['functional'] = 0.7 * dims['functional'] + 0.3 * functional_score
        
        # Update context dimension based on message length (complexity indicator)
        if hasattr(result, 'message') and result.message:
            context_score = min(1.0, len(result.message) / 1000.0)
            dims['context'] = 0.8 * dims['context'] + 0.2 * context_score
        
        # Update integration dimension based on file operations
        if hasattr(result, 'files_modified'):
            integration_score = min(1.0, result.files_modified / 10.0)
            dims['integration'] = 0.7 * dims['integration'] + 0.3 * integration_score
        
        self.logger.debug(f"Updated polytope dimensions for {phase_name}: {dims}")

    def _analyze_correlations(self, state) -> List[Dict[str, Any]]:
        """
        Use CorrelationEngine to find correlations across components.
        
        This is called during investigation/debugging phases to identify
        deeper relationships between errors, changes, and system state.
        
        Returns:
            List of correlation findings with recommendations
        """
        try:
            # Add findings from state to correlation engine
            from .state.manager import TaskStatus
            
            # Add error findings
            for task in state.tasks.values():
                if task.status == TaskStatus.FAILED:
                    self.correlation_engine.add_finding('task_errors', {
                        'type': 'error',
                        'task_id': task.id,
                        'message': task.description,
                        'file': task.target_file,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Run correlation analysis
            correlations = self.correlation_engine.correlate()
            
            # Log high-confidence correlations
            high_confidence = [c for c in correlations if c.get('confidence', 0) > 0.7]
            if high_confidence:
                self.logger.info(f"🔗 Found {len(high_confidence)} high-confidence correlations")
                for corr in high_confidence[:3]:  # Show top 3
                    self.logger.info(f"   • {corr.get('description', 'Unknown correlation')}")
                    if 'recommendation' in corr:
                        self.logger.info(f"     → {corr['recommendation']}")
            
            return correlations
            
        except Exception as e:
            self.logger.debug(f"Correlation analysis failed: {e}")
            return []
       
    
    def run(self, resume: bool = True) -> bool:
        """
        Run the main pipeline loop.
        
        Args:
            resume: If True, resume from saved state. If False, start fresh.
        
        Returns:
            True if completed successfully, False on error
        """
        self._print_banner()
        
        # Discover servers
        self.logger.info("🔍 Discovering Ollama servers...")
        self.client.discover_servers()
        
        # Load or create state
        if resume:
            state = self.state_manager.load()
            self.logger.info(f"  Resumed pipeline run: {state.run_id}")
        else:
            # Start fresh - DELETE old state completely
            self.logger.info("  Starting fresh (deleting all saved state)...")
            
            # Delete state file
            if self.state_manager.state_file.exists():
                self.state_manager.state_file.unlink()
                self.logger.info("  ✓ Deleted state file")
            
            # Delete entire .pipeline directory to ensure clean start
            pipeline_dir = self.project_dir / ".pipeline"
            if pipeline_dir.exists():
                import shutil
                shutil.rmtree(pipeline_dir)
                self.logger.info("  ✓ Deleted .pipeline directory")
            
            # Create fresh state
            state = PipelineState()
            self.logger.info(f"  Starting new pipeline run: {state.run_id}")
            self.state_manager.save(state)
        
        if state.tasks:
            self.logger.info(f"  Resumed pipeline run: {state.run_id}")
            completed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
            self.logger.info(f"  Tasks: {len(state.tasks)} total, {completed} completed")
        else:
            self.logger.info(f"  Starting new pipeline run: {state.run_id}")
        
        # Run the main loop
        try:
            return self._run_loop()
        except KeyboardInterrupt:
            self.logger.info("\n\n⚠️ Pipeline interrupted by user")
            return False
    
    def _develop_tool(self, tool_name: str, tool_args: dict, 
                     usage_context: dict, state: PipelineState) -> 'PhaseResult':
        """
        Develop a new tool through tool_design and tool_evaluation phases.
        
        Args:
            tool_name: Name of the tool to create
            tool_args: Arguments that were passed to the unknown tool
            usage_context: Context about how/where the tool was used
            state: Current pipeline state
            
        Returns:
            PhaseResult from tool_evaluation phase
        """
        from .phases.base import PhaseResult
        
        self.logger.info(f"📐 Designing tool: {tool_name}")
        
        # Step 1: Design the tool
        if 'tool_design' not in self.phases:
            self.logger.error("tool_design phase not available")
            return PhaseResult(
                success=False,
                phase='tool_development',
                message="tool_design phase not available"
            )
        
        design_result = self.phases['tool_design'].execute(
            state,
            tool_name=tool_name,
            tool_args=tool_args,
            usage_context=usage_context
        )
        
        if not design_result.success:
            self.logger.error(f"Tool design failed: {design_result.message}")
            return design_result
        
        self.logger.info(f"✓ Tool designed: {tool_name}")
        
        # Step 2: Evaluate the tool
        if 'tool_evaluation' not in self.phases:
            self.logger.warning("tool_evaluation phase not available, skipping validation")
            return design_result
        
        self.logger.info(f"🧪 Evaluating tool: {tool_name}")
        
        eval_result = self.phases['tool_evaluation'].execute(
            state,
            tool_name=tool_name,
            tool_spec=design_result.data.get('tool_spec')
        )
        
        if eval_result.success:
            self.logger.info(f"✓ Tool validated: {tool_name}")
        else:
            self.logger.warning(f"Tool validation failed: {eval_result.message}")
        
        return eval_result
    
    def _run_loop(self) -> bool:
        """
        Main execution loop - NEVER returns None for next action.
        
        The loop continues until:
        - max_iterations reached (if > 0)
        - KeyboardInterrupt
        - Unrecoverable error
        """
        iteration = 0
        max_iter = self.config.max_iterations if self.config.max_iterations > 0 else float('inf')
        
        # NO RATE LIMITING - run as fast as possible
        min_interval = 0  # UNLIMITED - no delay between iterations
        last_iteration_time = 0
        
        while iteration < max_iter:
            # No rate limiting - removed per user request
            last_iteration_time = time.time()
            
            # Load current state
            state = self.state_manager.load()
            
            # Determine next phase decision (NEVER returns None)
            phase_decision = self._determine_next_action(state)
            
            # Log iteration
            iteration += 1
            phase_name = phase_decision["phase"]
            reason = phase_decision.get("reason", "")
            
            # Special case: specialist consultation completed
            if phase_name == "_specialist_consultation_complete":
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"  ITERATION {iteration} - SPECIALIST CONSULTATION")
                self.logger.info(f"  Reason: {reason}")
                self.logger.info(f"{'='*70}")
                
                # Consultation result is in phase_decision
                consultation_result = phase_decision.get("result", {})
                self.logger.info(f"  Consultation complete, continuing...")
                
                # Continue to next iteration (arbiter will decide next action)
                continue
            
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  ITERATION {iteration} - {phase_name.upper()}")
            self.logger.info(f"  Reason: {reason}")
            
            # Log objective context if present
            objective = phase_decision.get("objective")
            if objective:
                self.logger.info(f"  🎯 Objective: {objective.title} ({objective.completion_percentage:.0f}% complete)")
                
                # Log dimensional metrics if available (polytopic objective)
                if hasattr(objective, 'complexity_score'):
                    self.logger.info(f"  📊 Metrics: Complexity={objective.complexity_score:.2f} Risk={objective.risk_score:.2f} Readiness={objective.readiness_score:.2f}")
                
                # Log dimensional health if available
                dimensional_health = phase_decision.get("dimensional_health")
                if dimensional_health:
                    health_status = dimensional_health.get('overall_health', 'UNKNOWN')
                    self.logger.info(f"  💊 Health: {health_status}")
            
            # Log dimensional space summary every 10 iterations
            if iteration % 10 == 0 and hasattr(self.objective_manager, 'get_space_summary'):
                try:
                    space_summary = self.objective_manager.get_space_summary()
                    total_objs = space_summary.get('total_objectives', 0)
                    if total_objs > 0:
                        self.logger.info(f"  📐 Dimensional Space: {total_objs} objectives in 7D space")
                except Exception as e:
                    pass  # Silently ignore if space summary fails
            
            self.logger.info(f"{'='*70}")
            
            # Get the phase
            phase = self.phases.get(phase_name)
            if not phase:
                self.logger.error(f"Unknown phase: {phase_name}")
                continue
            
            # Track phase in history
            if not hasattr(state, 'phase_history'):
                state.phase_history = []
            state.phase_history.append(phase_name)
            state.current_phase = phase_name
            self.state_manager.save(state)
            
            # Execute the phase
            task = phase_decision.get("task")
            objective = phase_decision.get("objective")
            
            try:
                # Execute the phase with unknown tool detection
                # Run correlation analysis for investigation/debugging phases BEFORE execution
                if phase_name in ['investigation', 'debugging', 'debug']:
                    correlations = self._analyze_correlations(state)
                    if correlations:
                        self.logger.info('Found %d correlations to guide %s' % (len(correlations), phase_name))
                   
                # Pass objective to phase if available
                phase_kwargs = {'task': task}
                if objective:
                    phase_kwargs['objective'] = objective
                
                result = phase.run(**phase_kwargs)
                
                # Check for unknown tool errors
                if not result.success and result.data.get('requires_tool_development'):
                    self.logger.info(f"🔧 Unknown tools detected, initiating tool development")
                    
                    unknown_tools = result.data.get('unknown_tools', [])
                    tool_calls = result.data.get('original_tool_calls', [])
                    
                    # Develop each unknown tool
                    all_tools_developed = True
                    for unknown_tool in unknown_tools:
                        tool_result = self._develop_tool(
                            tool_name=unknown_tool['tool_name'],
                            tool_args=unknown_tool.get('args', {}),
                            usage_context={
                                'phase': phase_name,
                                'original_tool_calls': tool_calls
                            },
                            state=state
                        )
                        
                        if not tool_result.success:
                            self.logger.error(f"Failed to develop tool: {unknown_tool['tool_name']}")
                            all_tools_developed = False
                            break
                    
                    # Retry original phase if all tools were developed
                    if all_tools_developed:
                        self.logger.info(f"🔄 Retrying {phase_name} with newly developed tools")
                        result = phase.run(task=task)

                
                # CRITICAL FIX: Load state ONCE and update both hint and phase stats
                # Don't reload multiple times - phase already saved task changes
                state = self.state_manager.load()
                
                # Check if phase suggests next phase (loop prevention hint)
                if result.next_phase:
                    self.logger.info(f"  💡 Phase suggests next: {result.next_phase}")
                    if not hasattr(state, '_next_phase_hint'):
                        state._next_phase_hint = None
                    state._next_phase_hint = result.next_phase
                
                # Record phase run with full details
                if phase_name in state.phases:
                    state.phases[phase_name].record_run(
                        success=result.success,
                        task_id=result.task_id,
                        files_created=result.files_created,
                        files_modified=result.files_modified
                    )
                
                # Save once with all updates
                self.state_manager.save(state)
                
                # Write phase state markdown
                if hasattr(phase, 'generate_state_markdown'):
                    md_content = phase.generate_state_markdown(state)
                    self.state_manager.write_phase_state(phase_name, md_content)
                
                # Log result
                if result.success:
                    self.logger.info(f"  ✅ {result.message}")
                else:
                    self.logger.warning(f"  ⚠️ {result.message}")
                
                # Show project status
                self._show_project_status(state)
                
                # INTEGRATION: Record execution pattern for learning
                self._record_execution_pattern(phase_name, result, state)
                
                # INTEGRATION: Periodic pattern optimization
                self.execution_count += 1
                if self.execution_count % 50 == 0:  # Every 50 executions
                    self.logger.info("🔧 Running pattern optimization...")
                    self.pattern_optimizer.run_full_optimization()
                
                # Check if we should force transition AFTER execution
                # This allows us to check the actual result for success/progress
                if self._should_force_transition(state, phase_name, result):
                    self.logger.warning(f"⚠️  Forcing transition from {phase_name} due to repeated failures")
                    
                    # Reset counters
                    self.state_manager.reset_no_update_count(state, phase_name)
                    
                    # Select next phase based on adjacency
                    next_phase = self._select_next_phase_polytopic(state, phase_name)
                    
                    self.logger.info(f"🔄 Next iteration will use: {next_phase}")
                    
                    # Store hint for next iteration
                    state = self.state_manager.load()
                    if not hasattr(state, '_next_phase_hint'):
                        state._next_phase_hint = None
                    state._next_phase_hint = next_phase
                    self.state_manager.save(state)
                
            except Exception as e:
                self.logger.error(f"  ❌ Phase error: {e}")
                if self.verbose:
                    import traceback
                    self.logger.debug(traceback.format_exc())
                
                # Record failure
                state = self.state_manager.load()
                if phase_name in state.phases:
                    state.phases[phase_name].record_run(
                        success=False,
                        task_id=task.task_id if task else None
                    )
                self.state_manager.save(state)
        
        # Reached max iterations
        self.logger.info(f"\n✅ Completed {iteration} iterations")
        return self._summarize_run()
    
    def _determine_next_action(self, state: PipelineState) -> Dict:
        """
        Determine the next action using STRATEGIC, OBJECTIVE-DRIVEN logic.
        
        NEW APPROACH: Objectives drive phase selection, not just task status.
        
        Returns:
            Dict with 'phase', 'reason', and optionally 'task' and 'objective'
        """
        
        # MESSAGE BUS: Check for critical messages
        from .messaging import MessageType, MessagePriority
        critical_messages = self.message_bus.get_messages(
            "coordinator",
            priority=MessagePriority.CRITICAL,
            limit=10
        )
        
        if critical_messages:
            self.logger.warning(f"⚠️ {len(critical_messages)} critical messages in queue")
            for msg in critical_messages:
                self.logger.warning(f"  📨 {msg.message_type.value}: {msg.payload}")
        
        # STRATEGIC DECISION-MAKING: Check if we have objectives
        if state.objectives and any(state.objectives.values()):
            # Use strategic decision-making based on objectives
            return self._determine_next_action_strategic(state)
        else:
            # Fall back to tactical decision-making (legacy behavior)
            return self._determine_next_action_tactical(state)
    
    def _determine_next_action_strategic(self, state: PipelineState) -> Dict:
        """
        Strategic decision-making based on objectives with 7D polytopic navigation.
        
        This is the NEW way - objectives drive everything using hyperdimensional intelligence.
        """
        # Load issues into tracker
        self.issue_tracker.load_issues(state)
        
        # Load objectives into polytopic space
        objectives_by_level = self.objective_manager.load_objectives(state)
        
        # Use 7D navigation to find optimal objective
        optimal_objective = self.objective_manager.find_optimal_objective(state)
        
        if not optimal_objective:
            # No active objective - need project planning to create objectives
            self.logger.info("🎯 No active objectives - need project planning")
            return {
                'phase': 'project_planning',
                'reason': 'No active objectives defined',
                'objective': None
            }
        
        # Log polytopic information
        self.logger.info(f"🎯 Optimal objective (7D selection): {optimal_objective.title} ({optimal_objective.level.value})")
        self.logger.info(f"📊 Complexity: {optimal_objective.complexity_score:.2f} | Risk: {optimal_objective.risk_score:.2f} | Readiness: {optimal_objective.readiness_score:.2f}")
        
        # Log dimensional profile
        dominant_dims = optimal_objective.get_dominant_dimensions(threshold=0.6)
        if dominant_dims:
            self.logger.info(f"📐 Dominant dimensions: {', '.join(dominant_dims)}")
        
        # Analyze dimensional health
        health = self.objective_manager.analyze_dimensional_health(optimal_objective)
        self.logger.info(f"💊 Dimensional health: {health['overall_health']}")
        
        if health['concerns']:
            for concern in health['concerns'][:3]:  # Show top 3 concerns
                self.logger.warning(f"  ⚠️ {concern}")
        
        # Get recommended action using base objective manager logic
        # (We still use the base class method for action determination)
        from .objective_manager import ObjectiveHealth, ObjectiveHealthStatus
        
        # Convert dimensional health to ObjectiveHealth format
        base_health = ObjectiveHealth(
            status=ObjectiveHealthStatus[health['overall_health']],
            success_rate=optimal_objective.success_rate,
            consecutive_failures=optimal_objective.failure_count,
            blocking_issues=optimal_objective.critical_issues,
            blocking_dependencies=optimal_objective.depends_on,
            recommendation=health['recommendations'][0] if health['recommendations'] else "Continue with current objective"
        )
        
        action = self.objective_manager.get_objective_action(optimal_objective, state, base_health)
        
        # Log dimensional trajectory if velocity detected
        trajectory_dir = optimal_objective.get_trajectory_direction()
        changing_dims = [dim for dim, direction in trajectory_dir.items() if direction != "stable"]
        if changing_dims:
            self.logger.info(f"📈 Dimensional changes: {', '.join(f'{dim}→{trajectory_dir[dim]}' for dim in changing_dims[:3])}")
        
        # Save updated objective to state
        self.objective_manager.save_objective(optimal_objective, state)
        
        return {
            'phase': action.phase,
            'task': action.task,
            'reason': action.reason,
            'objective': optimal_objective,
            'dimensional_health': health
        }
    
    def _determine_next_action_tactical(self, state: PipelineState) -> Dict:
        """
        Tactical decision-making based on task status (LEGACY).
        
        This is the OLD way - kept for backward compatibility.
        """
        
        # Get current phase
        current_phase = getattr(state, 'current_phase', 
                               state.phase_history[-1] if hasattr(state, 'phase_history') and state.phase_history else None)
        
        # Check for phase hint from previous phase
        phase_hint = getattr(state, '_next_phase_hint', None)
        if phase_hint and phase_hint in self.phases:
            self.logger.info(f"🎯 Following phase hint: {phase_hint}")
            state._next_phase_hint = None  # Clear hint after using
            return {'phase': phase_hint, 'reason': f'Phase {current_phase} suggested {phase_hint}'}
        
        # Count tasks by status
        pending = [t for t in state.tasks.values() if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]]
        qa_pending = [t for t in state.tasks.values() if t.status == TaskStatus.QA_PENDING]
        needs_fixes = [t for t in state.tasks.values() if t.status == TaskStatus.NEEDS_FIXES]
        completed = [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED]
        
        self.logger.info(f"📊 Task Status: {len(pending)} pending, {len(qa_pending)} QA, {len(needs_fixes)} fixes, {len(completed)} done")
        
        # CRITICAL FIX: If no tasks at all, always start with planning (fresh start)
        # This prevents loading stale QA_PENDING state on fresh runs
        if not state.tasks:
            self.logger.info("🆕 Fresh start detected - no tasks in state")
            return {'phase': 'planning', 'reason': 'Fresh start, need to create tasks'}
        
        # INTEGRATION: Get pattern-based recommendations
        recommendations = self.pattern_recognition.get_recommendations({
            'phase': current_phase,
            'state': state
        })
        
        # Apply high-confidence pattern recommendations
        pattern_override = None
        if recommendations:
            for rec in recommendations[:2]:  # Show top 2
                self.logger.debug(f"💡 Pattern insight: {rec['message']} (confidence: {rec['confidence']:.2f})")
                # Use high-confidence recommendations to influence decisions
                if rec['confidence'] > 0.8 and 'suggested_phase' in rec:
                    pattern_override = rec['suggested_phase']
                    self.logger.info(f"🎯 High-confidence pattern suggests: {pattern_override}")
        
        # SIMPLE DECISION TREE (with pattern influence):
        
        # 1. If we have tasks needing fixes, go to debugging
        if needs_fixes:
            # Pass the first task needing fixes
            return {'phase': 'debugging', 'task': needs_fixes[0], 'reason': f'{len(needs_fixes)} tasks need fixes'}
        
        # 2. If we have QA pending tasks, go to QA
        if qa_pending:
            # CRITICAL FIX: Pass the first QA_PENDING task so its status gets updated
            return {'phase': 'qa', 'task': qa_pending[0], 'reason': f'{len(qa_pending)} tasks awaiting QA'}
        
        # 3. If we have pending tasks, stay in coding
        if pending:
            # Pass the first pending task
            return {'phase': 'coding', 'task': pending[0], 'reason': f'{len(pending)} tasks in progress'}
        
        # 4. If no tasks at all, start with planning (unless pattern suggests otherwise)
        if not state.tasks:
            if pattern_override and pattern_override in self.phases:
                return {'phase': pattern_override, 'reason': f'Pattern-based suggestion (confidence > 0.8)'}
            return {'phase': 'planning', 'reason': 'No tasks yet, need to plan'}
        
        # 5. All tasks complete - route to documentation then project_planning
        if len(completed) == len(state.tasks):
            # Check if we've already done documentation
            if current_phase == 'documentation':
                return {'phase': 'project_planning', 'reason': 'Documentation complete, planning next iteration'}
            elif current_phase == 'project_planning':
                return {'phase': 'complete', 'reason': 'All tasks completed and documented!'}
            else:
                return {'phase': 'documentation', 'reason': 'All tasks complete, documenting work'}
        
        # 6. Default: go to planning to create more tasks (or follow pattern)
        if pattern_override and pattern_override in self.phases:
            return {'phase': pattern_override, 'reason': f'Pattern-based suggestion (confidence > 0.8)'}
        return {'phase': 'planning', 'reason': 'Need to plan next steps'}
    
    def _build_arbiter_context_DISABLED(self, state: PipelineState) -> Dict:
        """Build context for arbiter decision-making"""
        # Get task summaries
        pending_tasks = [
            {
                'task_id': t.task_id,
                'description': t.description,
                'status': t.status.value,
                'priority': t.priority,
                'attempts': t.attempts,
                'target_file': t.target_file
            }
            for t in state.tasks.values()
            if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
        ]
        
        qa_pending = [
            {
                'task_id': t.task_id,
                'description': t.description,
                'target_file': t.target_file
            }
            for t in state.tasks.values()
            if t.status == TaskStatus.QA_PENDING
        ]
        
        needs_fixes = [
            {
                'task_id': t.task_id,
                'description': t.description,
                'attempts': t.attempts,
                'errors': t.errors[-3:] if t.errors else []
            }
            for t in state.tasks.values()
            if t.status == TaskStatus.NEEDS_FIXES
        ]
        
        completed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        
        return {
            'needs_planning': state.needs_planning,
            'pending_tasks': pending_tasks,
            'qa_pending_tasks': qa_pending,
            'needs_fixes_tasks': needs_fixes,
            'completed_tasks': completed,
            'total_tasks': len(state.tasks),
            'needs_documentation': state.needs_documentation_update,
            'phase_history': state.phase_history[-10:] if hasattr(state, 'phase_history') else [],
            'available_phases': list(self.phases.keys())
        }
    
    def _convert_arbiter_decision_DISABLED(self, decision: Dict, state: PipelineState) -> Dict:
        """Convert arbiter decision to coordinator action format"""
        action = decision.get('action', 'continue_current_phase')
        
        # Handle different arbiter actions
        if action == 'continue_current_phase':
            # Fallback to simple logic if arbiter says continue
            if state.needs_planning:
                return {"phase": "planning", "reason": "arbiter_continue_planning"}
            
            # Get first pending task
            for task in state.tasks.values():
                if task.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]:
                    return {"phase": "coding", "task": task, "reason": "arbiter_continue_coding"}
            
            return {"phase": "project_planning", "reason": "arbiter_continue_expansion"}
        
        elif action == 'change_phase':
            new_phase = decision.get('parameters', {}).get('new_phase', 'planning')
            reason = decision.get('parameters', {}).get('reason', 'arbiter_decision')
            return {"phase": new_phase, "reason": reason}
        
        elif action == 'consult_specialist':
            # CORRECT: Execute specialist consultation directly
            # This allows model-to-model calling through the application
            specialist_name = decision.get('specialist', '')
            query = decision.get('query', '')
            context = decision.get('context', {})
            
            self.logger.info(f"🔧 Executing specialist consultation: {specialist_name}")
            
            # Execute the consultation
            result = self._execute_specialist_consultation(
                specialist_name, query, context, state
            )
            
            # After consultation, let arbiter decide next action
            # Return a special marker to continue the loop
            return {"phase": "_specialist_consultation_complete", "reason": "specialist_consulted", "result": result}
        
        else:
            # Unknown action, default to planning
            self.logger.warning(f"Unknown arbiter action: {action}, defaulting to planning")
            return {"phase": "planning", "reason": "arbiter_unknown_action"}
    
    def _execute_specialist_consultation_DISABLED(self, specialist_name: str, query: str, 
                                        context: dict, state: PipelineState) -> dict:
        """
        Execute a specialist consultation (model-to-model call).
        
        This is the correct implementation where:
        1. Arbiter calls specialist as a tool
        2. Application executes the specialist (runs the model)
        3. Specialist returns tool_calls
        4. Application executes those tool_calls
        5. Results are available for arbiter's next decision
        
        Args:
            specialist_name: Name of specialist (coding, reasoning, analysis)
            query: Query for the specialist
            context: Additional context
            state: Current pipeline state
            
        Returns:
            Dict with consultation results
        """
        self.logger.info(f"  Consulting {specialist_name} specialist...")
        
        # Add state to context
        context['state'] = {
            'phase': getattr(state, 'current_phase', state.phase_history[-1] if hasattr(state, 'phase_history') and state.phase_history else 'unknown'),
            'tasks': len(state.tasks),
            'pending': sum(1 for t in state.tasks.values() 
                          if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS])
        }
        
        # Call specialist through arbiter (model-to-model call)
        result = self.arbiter.consult_specialist(specialist_name, query, context)
        
        if not result.get('success', False):
            self.logger.error(f"  ✗ Specialist consultation failed")
            return result
        
        # Extract tool calls from specialist
        tool_calls = result.get('tool_calls', [])
        
        if tool_calls:
            self.logger.info(f"  Processing {len(tool_calls)} tool call(s) from specialist...")
            
            # Execute tool calls (application provides the scaffolding)
            from .handlers import ToolCallHandler
            handler = ToolCallHandler(
                self.project_dir, 
                tool_registry=self.tool_registry,
                tool_creator=self.tool_creator,
                tool_validator=self.tool_validator
            )
            tool_results = handler.process_tool_calls(tool_calls)
            
            # Add results to consultation result
            result['tool_results'] = tool_results
            result['files_created'] = handler.files_created
            result['files_modified'] = handler.files_modified
            
            # Update state based on tool results
            for tool_result in tool_results:
                if tool_result.get('success'):
                    # Track file changes
                    filepath = tool_result.get('filepath')
                    if filepath:
                        if tool_result.get('tool') in ['create_file', 'create_python_file']:
                            self.logger.info(f"  ✓ Created: {filepath}")
                        elif tool_result.get('tool') in ['write_file', 'str_replace']:
                            self.logger.info(f"  ✓ Modified: {filepath}")
            
            self.logger.info(f"  ✓ Specialist consultation complete")
        else:
            self.logger.info(f"  ✓ Specialist provided guidance (no tool calls)")
        
        return result
    
    def _should_run_improvement_cycle(self, state: PipelineState) -> bool:
        """
        Determine if we should run self-improvement cycle.
        
        Run improvement cycle when:
        - All tasks are complete
        - Custom tools/prompts/roles exist
        - Haven't run improvement recently
        
        Args:
            state: Current pipeline state
            
        Returns:
            True if should run improvement cycle
        """
        # Check if all tasks are complete
        if not state.tasks:
            return False
        
        all_complete = all(
            task.status == TaskStatus.COMPLETED
            for task in state.tasks.values()
        )
        
        if not all_complete:
            return False
        
        # Check if custom tools/prompts/roles exist
        custom_tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        custom_prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        custom_roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        
        has_custom_tools = custom_tools_dir.exists() and any(custom_tools_dir.glob("*_spec.json"))
        has_custom_prompts = custom_prompts_dir.exists() and any(custom_prompts_dir.glob("*.json"))
        has_custom_roles = custom_roles_dir.exists() and any(custom_roles_dir.glob("*.json"))
        
        return has_custom_tools or has_custom_prompts or has_custom_roles
    
    def _get_next_improvement_phase(self, state: PipelineState) -> Optional[Dict]:
        """
        Get the next improvement phase to run.
        
        Priority order:
        1. Tool evaluation
        2. Prompt improvement
        3. Role improvement
        
        Args:
            state: Current pipeline state
            
        Returns:
            Phase action dict or None
        """
        # Check which improvement phases have been run
        tool_eval_runs = state.phases.get("tool_evaluation", None)
        prompt_imp_runs = state.phases.get("prompt_improvement", None)
        role_imp_runs = state.phases.get("role_improvement", None)
        
        # Check what exists
        custom_tools_dir = self.project_dir / "pipeline" / "tools" / "custom"
        custom_prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        custom_roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        
        has_custom_tools = custom_tools_dir.exists() and any(custom_tools_dir.glob("*_spec.json"))
        has_custom_prompts = custom_prompts_dir.exists() and any(custom_prompts_dir.glob("*.json"))
        has_custom_roles = custom_roles_dir.exists() and any(custom_roles_dir.glob("*.json"))
        
        # Priority 1: Tool evaluation (if tools exist and not recently evaluated)
        if has_custom_tools:
            if not tool_eval_runs or tool_eval_runs.run_count == 0:
                return {
                    "phase": "tool_evaluation",
                    "reason": "evaluate_custom_tools"
                }
        
        # Priority 2: Prompt improvement (if prompts exist and not recently improved)
        if has_custom_prompts:
            if not prompt_imp_runs or prompt_imp_runs.run_count == 0:
                return {
                    "phase": "prompt_improvement",
                    "reason": "improve_custom_prompts"
                }
        
        # Priority 3: Role improvement (if roles exist and not recently improved)
        if has_custom_roles:
            if not role_imp_runs or role_imp_runs.run_count == 0:
                return {
                    "phase": "role_improvement",
                    "reason": "improve_custom_roles"
                }
        
        # All improvement phases have been run at least once
        return None
    
    def _dependencies_met(self, state: PipelineState, task: TaskState) -> bool:
        """Check if all dependencies for a task are completed"""
        if not task.dependencies:
            return True
        
        for dep_file in task.dependencies:
            # Check if any completed task created this file
            dep_met = False
            for other_task in state.tasks.values():
                if other_task.target_file == dep_file:
                    if other_task.status == TaskStatus.COMPLETED:
                        dep_met = True
                        break
            
            # Also check if file already exists
            if not dep_met:
                dep_path = self.project_dir / dep_file
                if dep_path.exists():
                    dep_met = True
            
            if not dep_met:
                return False
        
        return True
    
    def _record_execution_pattern(self, phase_name: str, result, state: PipelineState) -> None:
        """
        Record execution pattern for learning and optimization.
        
        Args:
            phase_name: Name of the phase that executed
            result: PhaseResult from execution
            state: Current pipeline state
        """
        try:
            # Build execution data
            execution_data = {
                'phase': phase_name,
                'success': result.success,
                'duration': getattr(result, 'duration', 0),
                'tool_calls': getattr(result, 'tool_calls', []),
                'files_created': result.files_created,
                'files_modified': result.files_modified,
                'next_phase': result.next_phase,
                'errors': []
            }
            
            # Add error information if failed
            if not result.success:
                execution_data['errors'].append({
                    'type': 'phase_failure',
                    'message': result.message
                })
            
            # Record the execution
            self.pattern_recognition.record_execution(execution_data)
                
            # Update polytope dimensions based on results
            self._update_polytope_dimensions(phase_name, result)
            
            # Get recommendations for current context
            recommendations = self.pattern_recognition.get_recommendations({
                'phase': phase_name,
                'state': state
            })
            
            # Log recommendations if any
            if recommendations:
                self.logger.debug(f"📊 Pattern recommendations: {len(recommendations)} available")
                
        except Exception as e:
            self.logger.debug(f"Failed to record execution pattern: {e}")
    
    def _show_project_status(self, state: PipelineState) -> None:
        """Show current project file status - only files with active tasks"""
        # Only show files that have active tasks (not all files)
        active_files = set()
        for task in state.tasks.values():
            if task.target_file and task.status in [
                TaskStatus.NEW, TaskStatus.IN_PROGRESS, 
                TaskStatus.QA_PENDING, TaskStatus.NEEDS_FIXES
            ]:
                active_files.add(task.target_file)
        
        if not active_files:
            return  # Don't show anything if no active tasks
        
        self.logger.info(f"\n📁 PROJECT: {self.project_dir}")
        self.logger.info("─" * 50)
        
        for file_path in sorted(active_files):
            full_path = self.project_dir / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                
                # Find task for this file
                task = next((t for t in state.tasks.values() if t.target_file == file_path), None)
                if task:
                    status_icon = {
                        TaskStatus.NEW: "○",
                        TaskStatus.IN_PROGRESS: "⋯",
                        TaskStatus.QA_PENDING: "○",
                        TaskStatus.NEEDS_FIXES: "⚠",
                    }.get(task.status, "○")
                    
                    self.logger.info(f"   {status_icon} {file_path} ({size} bytes)")
        
        self.logger.info("─" * 50)
    
    def _print_banner(self) -> None:
        """Print pipeline banner"""
        self.logger.info("=" * 70)
        self.logger.info("  AI DEVELOPMENT PIPELINE v2 - State-Managed Architecture")
        self.logger.info("=" * 70)
        self.logger.info(f"\n  Project: {self.project_dir}")
        self.logger.info(f"  Max retries: {self.config.max_retries_per_task}")
        
        if self.config.max_iterations > 0:
            self.logger.info(f"  Max iterations: {self.config.max_iterations}")
        else:
            self.logger.info(f"  Max iterations: ∞")
        
        if self.verbose:
            self.logger.info(f"  Verbose: ON")
        
        self.logger.info("=" * 70)
    
    def _summarize_run(self) -> bool:
        """Print run summary and return success status"""
        state = self.state_manager.load()
        
        total = len(state.tasks)
        completed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in state.tasks.values() if t.status == TaskStatus.SKIPPED)
        
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"  📊 PIPELINE SUMMARY")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"  Total tasks: {total}")
        self.logger.info(f"  Completed: {completed}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Skipped: {total - completed - failed}")
        
        # Count iterations from phase runs
        total_iterations = sum(p.run_count for p in state.phases.values()) // 2  # Rough estimate
        self.logger.info(f"  Iterations: {total_iterations}")
        
        if state.expansion_count > 0:
            self.logger.info(f"  Expansion cycles: {state.expansion_count}")
        
        self.logger.info(f"{'='*70}")
        
        # Phase statistics
        self.logger.info(f"\n  Phase Statistics:")
        for name, phase in state.phases.items():
            if phase.run_count > 0:
                self.logger.info(f"    {name}: {phase.run_count} runs, {phase.success_count} success, {phase.failure_count} failed")
        
        # Dimensional space summary (if polytopic manager is used)
        if hasattr(self.objective_manager, 'get_space_summary'):
            try:
                space_summary = self.objective_manager.get_space_summary()
                total_objs = space_summary.get('total_objectives', 0)
                
                if total_objs > 0:
                    self.logger.info(f"\n  📐 Dimensional Space Summary:")
                    self.logger.info(f"    Total objectives: {total_objs}")
                    self.logger.info(f"    Dimensions: {space_summary.get('dimensions', 7)}")
                    
                    objs_by_level = space_summary.get('objectives_by_level', {})
                    if objs_by_level:
                        self.logger.info(f"    PRIMARY: {objs_by_level.get('PRIMARY', 0)}")
                        self.logger.info(f"    SECONDARY: {objs_by_level.get('SECONDARY', 0)}")
                        self.logger.info(f"    TERTIARY: {objs_by_level.get('TERTIARY', 0)}")
                    
                    clusters = space_summary.get('clusters', 0)
                    if clusters > 0:
                        self.logger.info(f"    Clusters: {clusters}")
            except Exception as e:
                pass  # Silently ignore if space summary fails
        
        self.logger.info(f"{'='*70}")
        
        return completed > 0 or total == 0
    
    def visualize_dimensional_space(self, visualization_type: str = "2d") -> None:
        """
        Visualize the dimensional space (for debugging/analysis).
        
        Args:
            visualization_type: Type of visualization ("2d", "3d", "health", "clusters", "trajectory", "distribution", "adjacency", "comprehensive")
        
        This method can be called to see the current state of objectives in 7D space.
        """
        if not hasattr(self.objective_manager, 'visualize_dimensional_space'):
            self.logger.warning("Dimensional space visualization not available (not using PolytopicObjectiveManager)")
            return
        
        try:
            if visualization_type == "2d":
                visualization = self.objective_manager.visualize_dimensional_space()
                self.logger.info("\n" + visualization)
            
            elif visualization_type == "3d":
                if hasattr(self.objective_manager, 'visualize_3d_space'):
                    visualization = self.objective_manager.visualize_3d_space()
                    self.logger.info("\n" + visualization)
                else:
                    self.logger.warning("3D visualization not available")
            
            elif visualization_type == "health":
                if hasattr(self.objective_manager, 'visualize_health_heatmap'):
                    visualization = self.objective_manager.visualize_health_heatmap()
                    self.logger.info("\n" + visualization)
                else:
                    self.logger.warning("Health heatmap not available")
            
            elif visualization_type == "clusters":
                if hasattr(self.objective_manager, 'visualize_clusters'):
                    visualization = self.objective_manager.visualize_clusters()
                    self.logger.info("\n" + visualization)
                else:
                    self.logger.warning("Cluster visualization not available")
            
            elif visualization_type == "distribution":
                if hasattr(self.objective_manager, 'visualize_dimensional_distribution'):
                    visualization = self.objective_manager.visualize_dimensional_distribution()
                    self.logger.info("\n" + visualization)
                else:
                    self.logger.warning("Distribution visualization not available")
            
            elif visualization_type == "adjacency":
                if hasattr(self.objective_manager, 'visualize_adjacency_graph'):
                    visualization = self.objective_manager.visualize_adjacency_graph()
                    self.logger.info("\n" + visualization)
                else:
                    self.logger.warning("Adjacency graph not available")
            
            elif visualization_type == "comprehensive":
                if hasattr(self.objective_manager, 'generate_comprehensive_visualization_report'):
                    report = self.objective_manager.generate_comprehensive_visualization_report()
                    self.logger.info("\n" + report)
                else:
                    self.logger.warning("Comprehensive report not available")
            
            else:
                self.logger.warning(f"Unknown visualization type: {visualization_type}")
                self.logger.info("Available types: 2d, 3d, health, clusters, distribution, adjacency, comprehensive")
            
        except Exception as e:
            self.logger.error(f"Failed to visualize dimensional space: {e}")
