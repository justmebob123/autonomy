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
    next_phase: Optional[str] = None  # Hint for coordinator about which phase to run next
    
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
            "next_phase": self.next_phase,
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
    
    def __init__(self, config: PipelineConfig, client: OllamaClient,
                 state_manager=None, file_tracker=None,
                 prompt_registry=None, tool_registry=None, role_registry=None,
                 coding_specialist=None, reasoning_specialist=None, analysis_specialist=None):
        self.config = config
        self.client = client
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        
        # State management - use shared instances if provided
        self.state_manager = state_manager or StateManager(self.project_dir)
        self.file_tracker = file_tracker or FileTracker(self.project_dir)
        
        # Context providers
        self.error_context = ErrorContext()
        self.code_context = CodeContext(self.project_dir)
        
        # Response parsing - pass client for functiongemma support
        self.parser = ResponseParser(client)
        
        # Conversation thread for maintaining history with auto-pruning
        from ..orchestration.conversation_manager import ConversationThread
        from ..orchestration.conversation_pruning import (
            AutoPruningConversationThread,
            PruningConfig
        )
        
        # Get model for this phase from config
        phase_model = "qwen2.5:14b"  # default
        if hasattr(config, 'model_assignments') and self.phase_name in config.model_assignments:
            phase_model = config.model_assignments[self.phase_name][0]
        
        # Get context window (default 8192)
        context_window = getattr(config, 'context_window', 8192)
        
        # Create base conversation thread
        thread = ConversationThread(
            model=phase_model,
            role=self.phase_name,
            max_context_tokens=context_window
        )
        
        # Wrap with auto-pruning for memory management
        from ..orchestration.conversation_pruning import ConversationPruner
        
        pruning_config = PruningConfig(
            max_messages=50,  # Keep max 50 messages
            preserve_first_n=5,  # Keep first 5 (initial context)
            preserve_last_n=20,  # Keep last 20 (recent context)
            preserve_errors=True,  # Always keep errors
            preserve_decisions=True,  # Keep decision points
            summarize_pruned=True,  # Create summaries
            min_prune_age_minutes=30  # Only prune messages >30 min old
        )
        
        pruner = ConversationPruner(pruning_config)
        self.conversation = AutoPruningConversationThread(thread, pruner)
        
        # Cache tools for functiongemma fallback
        
        
        # Dynamic registries - use shared instances if provided
        if prompt_registry is None or tool_registry is None or role_registry is None:
            from ..prompt_registry import PromptRegistry
            from ..tool_registry import ToolRegistry
            from ..role_registry import RoleRegistry
            self.prompt_registry = prompt_registry or PromptRegistry(self.project_dir)
            self.tool_registry = tool_registry or ToolRegistry(self.project_dir)
            self.role_registry = role_registry or RoleRegistry(self.project_dir, self.client)
        else:
            self.prompt_registry = prompt_registry
            self.tool_registry = tool_registry
            self.role_registry = role_registry
        
        # INTEGRATION: Use shared specialists if provided
        if coding_specialist is None or reasoning_specialist is None or analysis_specialist is None:
            from ..orchestration.unified_model_tool import UnifiedModelTool
            from ..orchestration.specialists import (
                create_coding_specialist,
                create_reasoning_specialist,
                create_analysis_specialist
            )
            
            # Create unified model tools for specialists (fallback)
            self.coding_tool = UnifiedModelTool("qwen2.5-coder:32b", "http://ollama02:11434")
            self.reasoning_tool = UnifiedModelTool("qwen2.5:32b", "http://ollama02:11434")
            self.analysis_tool = UnifiedModelTool("qwen2.5:14b", "http://ollama01.thiscluster.net:11434")
            
            # Create specialists (fallback)
            self.coding_specialist = coding_specialist or create_coding_specialist(self.coding_tool)
            self.reasoning_specialist = reasoning_specialist or create_reasoning_specialist(self.reasoning_tool)
            self.analysis_specialist = analysis_specialist or create_analysis_specialist(self.analysis_tool)
        else:
            self.coding_specialist = coding_specialist
            self.reasoning_specialist = reasoning_specialist
            self.analysis_specialist = analysis_specialist
        
        # Initialize specialist request handler
        from ..specialist_request_handler import SpecialistRequestHandler
        self.specialist_request_handler = SpecialistRequestHandler({
            'coding': self.coding_specialist,
            'reasoning': self.reasoning_specialist,
            'analysis': self.analysis_specialist
        })
        
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
    
    def check_for_unknown_tools(self, results: List[Dict]) -> Optional[List[Dict]]:
        """
        Check tool call results for unknown tools.
        
        Args:
            results: List of tool call results
            
        Returns:
            List of unknown tool errors if any, None otherwise
        """
        unknown_tools = [r for r in results if r.get('error_type') == 'unknown_tool']
        return unknown_tools if unknown_tools else None
    
    def create_unknown_tool_result(self, unknown_tools: List[Dict], 
                                    tool_calls: List[Dict]) -> PhaseResult:
        """
        Create a PhaseResult for unknown tool errors.
        
        Args:
            unknown_tools: List of unknown tool errors
            tool_calls: Original tool calls
            
        Returns:
            PhaseResult indicating unknown tools need development
        """
        tool_names = [t['tool_name'] for t in unknown_tools]
        return PhaseResult(
            success=False,
            phase=self.phase_name,
            message=f"Unknown tools detected: {tool_names}",
            data={
                'unknown_tools': unknown_tools,
                'requires_tool_development': True,
                'original_tool_calls': tool_calls
            }
        )
    
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
    
    def chat_with_history(self, user_message: str, tools: List[Dict] = None, task_context: Dict = None) -> Dict:
        """
        Call model with conversation history.
        
        This maintains conversation context so the model can reference
        previous exchanges and learn from history.
        
        Optionally detects and handles specialist requests in the conversation.
        
        Args:
            user_message: The user message to send
            tools: Optional tools for the model to use
            task_context: Optional context about current task (for specialist requests)
        
        Returns:
            Dict with 'content' and optionally 'tool_calls'
        """
        # Add user message to conversation
        self.conversation.add_message("user", user_message)
        
        # Get conversation context (respects token limits)
        messages = self.conversation.get_context()
        
        # Call model with conversation history
        response = self.client.chat(
            messages=messages,
            tools=tools
        )
        
        # Add assistant response to conversation
        content = response.get("message", {}).get("content", "")
        self.conversation.add_message("assistant", content)
        
        # Check if model is requesting specialist help
        if hasattr(self, 'specialist_request_handler') and task_context:
            request = self.specialist_request_handler.detect_request(content)
            if request:
                # Handle specialist request
                specialist_result = self.specialist_request_handler.handle_request(request, task_context)
                
                # Format and add specialist response to conversation
                specialist_response = self.specialist_request_handler.format_specialist_response(
                    request['specialist'],
                    specialist_result
                )
                self.conversation.add_message("assistant", specialist_response)
                
                # Update content to include specialist response
                content = f"{content}\n\n{specialist_response}"
        
        # Parse response for tool calls
        parsed = self.parser.parse_response(response, tools or [])
        
        return {
            "content": content,
            "tool_calls": parsed.get("tool_calls", []),
            "raw_response": response
        }
