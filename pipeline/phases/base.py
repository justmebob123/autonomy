"""
Base Phase

Abstract base class for all pipeline phases with common state operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..state.manager import StateManager, PipelineState, TaskState, TaskStatus
from ..state.file_tracker import FileTracker
from ..context.error import ErrorContext
from ..context.code import CodeContext
from ..client import OllamaClient, ResponseParser
from ..config import PipelineConfig
from ..logging_setup import get_logger


@dataclass
class PhaseResult:
    """Result of a phase execution"""
    success: bool
    phase: str
    task_id: Optional[str] = None
    message: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "phase": self.phase,
            "task_id": self.task_id,
            "message": self.message,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "errors": self.errors,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class BasePhase(ABC):
    """
    Abstract base class for pipeline phases.
    
    Provides common functionality for:
    - State management (loading, saving, updating)
    - File tracking
    - Error context management
    - LLM communication
    - Markdown state file generation
    """
    
    phase_name: str = "base"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        self.config = config
        self.client = client
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        
        # State management
        self.state_manager = StateManager(self.project_dir)
        self.file_tracker = FileTracker(self.project_dir)
        
        # Context providers
        self.error_context = ErrorContext()
        self.code_context = CodeContext(self.project_dir)
        
        # Response parsing - pass client for functiongemma support
        self.parser = ResponseParser(client)
        
        # Cache tools for functiongemma fallback
        self._tools_cache: Dict[str, List[Dict]] = {}
        
        # Dynamic registries (Integration Point #2)
        from ..prompt_registry import PromptRegistry
        from ..tool_registry import ToolRegistry
        from ..role_registry import RoleRegistry
        self.prompt_registry = PromptRegistry(self.project_dir)
        self.tool_registry = ToolRegistry(self.project_dir)
        self.role_registry = RoleRegistry(self.project_dir, self.client)
        
        # Self-awareness and polytopic integration
        self.dimensional_profile = {
            'temporal': 0.5, 'functional': 0.5, 'data': 0.5,
            'state': 0.5, 'error': 0.5, 'context': 0.5, 'integration': 0.5
        }
        self.self_awareness_level = 0.0
        self.adjacencies = []
        self.experience_count = 0
    
    @abstractmethod
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute the phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Phase-specific arguments
        
        Returns:
            PhaseResult with outcome
        """
        pass
    
    @abstractmethod
    def generate_state_markdown(self, state: PipelineState) -> str:
        """
        Generate markdown content for phase state file.
        
        Args:
            state: Current pipeline state
        
        Returns:
            Markdown string
        """
        pass
    
    
    def adapt_to_situation(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt phase behavior based on current situation with full intelligence."""
        adapted_profile = self.dimensional_profile.copy()
        
        # Determine mode based on situation
        mode = self._determine_mode(situation)
        
        # Extract constraints from situation
        constraints = self._extract_constraints(situation)
        
        # Adapt dimensional profile based on mode and constraints
        adapted_profile = self._adapt_dimensional_profile(adapted_profile, mode, situation)
        
        # Increase self-awareness and experience
        self._increase_self_awareness()
        self.experience_count += 1
        
        # Record adaptation
        self._record_adaptation(situation, mode, adapted_profile)
        
        return {
            'adapted_profile': adapted_profile,
            'self_awareness': self.self_awareness_level,
            'mode': mode,
            'constraints': constraints,
            'experience': self.experience_count
        }
    
    def _determine_mode(self, situation: Dict[str, Any]) -> str:
        """Determine operational mode based on situation."""
        if situation.get('error_severity') in ['high', 'critical']:
            return 'error_handling'
        elif situation.get('complexity') == 'high':
            return 'deep_analysis'
        elif situation.get('urgency') == 'high':
            return 'rapid_response'
        else:
            return 'development'
    
    def _extract_constraints(self, situation: Dict[str, Any]) -> List[str]:
        """Extract operational constraints from situation."""
        constraints = []
        
        if situation.get('has_errors'):
            constraints.append('must_fix_errors')
        
        if situation.get('complexity') == 'high':
            constraints.append('requires_deep_analysis')
        
        if situation.get('urgency') == 'high':
            constraints.append('time_critical')
        
        return constraints
    
    def _adapt_dimensional_profile(
        self, 
        profile: Dict[str, float], 
        mode: str, 
        situation: Dict[str, Any]
    ) -> Dict[str, float]:
        """Adapt dimensional profile based on mode and situation."""
        from datetime import datetime
        adapted = profile.copy()
        
        # Mode-based adaptations
        if mode == 'error_handling':
            adapted['error'] = min(1.0, adapted['error'] * 1.5)
            adapted['context'] = min(1.0, adapted['context'] * 1.3)
        elif mode == 'deep_analysis':
            adapted['functional'] = min(1.0, adapted['functional'] * 1.4)
            adapted['context'] = min(1.0, adapted['context'] * 1.3)
        elif mode == 'rapid_response':
            adapted['temporal'] = min(1.0, adapted['temporal'] * 1.5)
        
        # Situation-based adaptations
        if situation.get('complexity') == 'high':
            adapted['functional'] = min(1.0, adapted['functional'] * 1.4)
            adapted['integration'] = min(1.0, adapted['integration'] * 1.2)
        
        if situation.get('has_errors'):
            adapted['error'] = min(1.0, adapted['error'] * 1.3)
        
        return adapted
    
    def _record_adaptation(self, situation: Dict[str, Any], mode: str, profile: Dict[str, float]):
        """Record adaptation for learning."""
        from datetime import datetime
        if not hasattr(self, '_adaptation_history'):
            self._adaptation_history = []
        
        self._adaptation_history.append({
            'situation': situation,
            'mode': mode,
            'profile': profile,
            'timestamp': datetime.now().isoformat(),
            'experience': self.experience_count
        })
        
        # Keep only last 100 adaptations
        if len(self._adaptation_history) > 100:
            self._adaptation_history = self._adaptation_history[-100:]
    
    def _increase_self_awareness(self):
        """Increase self-awareness level based on experience."""
        # Logarithmic growth: fast at first, slower later
        growth_rate = 0.01 * (1.0 - self.self_awareness_level)
        self.self_awareness_level = min(1.0, self.self_awareness_level + growth_rate)
    
    def record_success(self):
        """Record a successful execution."""
        if not hasattr(self, '_success_count'):
            self._success_count = 0
        self._success_count += 1
    
    def record_failure(self):
        """Record a failed execution."""
        if not hasattr(self, '_failure_count'):
            self._failure_count = 0
        self._failure_count += 1
    
    def get_success_rate(self) -> float:
        """Get the success rate of this phase."""
        if not hasattr(self, '_success_count'):
            self._success_count = 0
        if not hasattr(self, '_failure_count'):
            self._failure_count = 0
        
        total = self._success_count + self._failure_count
        if total == 0:
            return 0.0
        
        return self._success_count / total
    
    def learn_pattern(self, pattern: Dict[str, Any]):
        """Learn a pattern from execution."""
        from datetime import datetime
        if not hasattr(self, '_learned_patterns'):
            self._learned_patterns = []
        
        pattern['timestamp'] = datetime.now().isoformat()
        pattern['phase'] = self.phase_name
        self._learned_patterns.append(pattern)
        
        # Keep only last 50 patterns
        if len(self._learned_patterns) > 50:
            self._learned_patterns = self._learned_patterns[-50:]
    
    def get_adaptive_prompt_context(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with self-awareness and polytopic context."""
        enhancements = []
        
        # Add self-awareness context
        if self.self_awareness_level > 0:
            enhancements.append(f"\n[Self-Awareness Level: {self.self_awareness_level:.3f}]")
            enhancements.append(f"[Experience Count: {self.experience_count}]")
        
        # Add dimensional profile
        dims = ", ".join(f"{k}={v:.2f}" for k, v in self.dimensional_profile.items())
        enhancements.append(f"\n[Dimensional Profile: {dims}]")
        
        # Add adjacency awareness
        if self.adjacencies:
            enhancements.append(f"\n[Adjacent Phases: {', '.join(self.adjacencies)}]")
        
        return base_prompt + "\n".join(enhancements)
    
    def run(self, **kwargs) -> PhaseResult:
        """
        Run the phase with full state management.
        
        This is the main entry point that handles:
        1. Loading state
        2. Executing the phase
        3. Updating state
        4. Writing state files
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"  {self.phase_name.upper()} PHASE")
        self.logger.info(f"{'='*60}")
        
        # Load state
        state = self.state_manager.load()
        
        try:
            # Execute phase
            result = self.execute(state, **kwargs)
            
            # Update phase state
            state.phases[self.phase_name].record_run(result.success)
            
            # Update file hashes for any changed files
            for filepath in result.files_created + result.files_modified:
                self.file_tracker.update_hash(filepath)
            
            # Save state
            self.state_manager.save(state)
            
            # Write markdown state file
            md_content = self.generate_state_markdown(state)
            self.state_manager.write_phase_state(self.phase_name, md_content)
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Phase {self.phase_name} failed: {e}")
            
            # Record failure
            state.phases[self.phase_name].record_run(False)
            self.state_manager.save(state)
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=str(e),
                errors=[{"type": type(e).__name__, "message": str(e)}]
            )
    
    def get_model_for_task(self, task_type: str) -> Optional[tuple]:
        """Get the appropriate model for a task type"""
        return self.client.get_model_for_task(task_type)
    
    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             task_type: str = None) -> Dict:
        """Send a chat request to the LLM"""
        model_info = self.get_model_for_task(task_type or self.phase_name)
        
        if not model_info:
            self.logger.error(f"No model available for {task_type or self.phase_name}")
            return {"error": "No model available"}
        
        host, model = model_info
        self.logger.info(f"  Using: {model} on {host}")
        
        temperature = self.config.temperatures.get(
            task_type or self.phase_name, 0.3
        )
        
        # Get timeout from config (None = no timeout)
        timeout_map = {
            "planning": self.config.planning_timeout,
            "coding": self.config.coding_timeout,
            "qa": self.config.qa_timeout,
            "debug": self.config.debug_timeout,
            "debugging": self.config.debug_timeout,
        }
        timeout = timeout_map.get(task_type or self.phase_name, 
                                   self.config.request_timeout)
        
        # Cache tools for functiongemma fallback in parse_response
        if tools:
            self._tools_cache[task_type or self.phase_name] = tools
        
        return self.client.chat(host, model, messages, tools, temperature, timeout)
    
    def parse_response(self, response: Dict, task_type: str = None) -> tuple:
        """
        Parse response with tools context for functiongemma fallback.
        
        Args:
            response: Raw response from LLM
            task_type: Task type to look up cached tools
        
        Returns:
            Tuple of (tool_calls, content)
        """
        task_type = task_type or self.phase_name
        tools = self._tools_cache.get(task_type, [])
        return self.parser.parse_response(response, tools)
    
    def read_file(self, filepath: str) -> Optional[str]:
        """Read a file from the project"""
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return None
        try:
            return full_path.read_text()
        except IOError as e:
            self.logger.error(f"Failed to read {filepath}: {e}")
            return None
    
    def write_file(self, filepath: str, content: str) -> bool:
        """Write a file to the project"""
        full_path = self.project_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Record previous version
            if full_path.exists():
                old_content = full_path.read_text()
                self.code_context.record_version(filepath, old_content)
            
            full_path.write_text(content)
            self.file_tracker.update_hash(filepath)
            return True
        except IOError as e:
            self.logger.error(f"Failed to write {filepath}: {e}")
            return False
    
    def format_timestamp(self, iso_timestamp: str = None) -> str:
        """Format a timestamp for display"""
        if iso_timestamp:
            try:
                dt = datetime.fromisoformat(iso_timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return iso_timestamp
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_task_context(self, task: TaskState) -> str:
        """Build context string for a task"""
        parts = []
        
        # Error context
        error_ctx = self.error_context.format_for_task(task.task_id)
        if error_ctx:
            parts.append(error_ctx)
        
        # Code context
        code_ctx = self.code_context.get_context_for_task(task.target_file)
        if code_ctx:
            parts.append(code_ctx)
        
        return "\n\n".join(parts)
    
    def _get_system_prompt(self, phase_name: str) -> str:
        """
        Get system prompt from registry or fallback to hardcoded.
        
        This enables custom prompts from PromptArchitect to be used
        when available, while maintaining backward compatibility.
        
        Args:
            phase_name: Name of the phase (e.g., "debugging", "coding")
        
        Returns:
            System prompt string
        """
        from ..prompts import SYSTEM_PROMPTS
        
        # Try custom prompt first
        custom_prompt = self.prompt_registry.get_prompt(f"{phase_name}_system")
        if custom_prompt:
            self.logger.debug(f"  Using custom system prompt for {phase_name}")
            return custom_prompt
        
        # Fallback to hardcoded
        return SYSTEM_PROMPTS.get(phase_name, SYSTEM_PROMPTS.get("base", ""))
