import re
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
from pipeline.logging_setup import get_logger


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
                 coding_specialist=None, reasoning_specialist=None, analysis_specialist=None,
                 message_bus=None, adaptive_prompts=None,
                 pattern_recognition=None, correlation_engine=None, analytics=None, pattern_optimizer=None):
        self.config = config
        self.client = client
        self.project_dir = Path(config.project_dir)
        self.logger = get_logger()
        
        # State management - use shared instances if provided
        self.state_manager = state_manager or StateManager(self.project_dir)
        self.file_tracker = file_tracker or FileTracker(self.project_dir)
        
        # Message bus for phase-to-phase communication
        self.message_bus = message_bus
        
        # Context providers
        self.error_context = ErrorContext()
        self.code_context = CodeContext(self.project_dir)
        
        # Response parsing - pass client for functiongemma support
        self.parser = ResponseParser(client)
        
        # Conversation thread for maintaining history with auto-pruning
        from ..orchestration.conversation_manager import OrchestrationConversationThread
        from ..orchestration.conversation_pruning import (
            AutoPruningConversationThread,
            PruningConfig
        )
        
        # Get model for this phase from config
        phase_model = "qwen2.5:14b"  # default
        if hasattr(config, 'model_assignments') and self.phase_name in config.model_assignments:
            phase_model = config.model_assignments[self.phase_name][0]
        
        # Get context window (default 8192, but much higher for refactoring)
        context_window = getattr(config, 'context_window', 8192)
        
        # CRITICAL: Refactoring phase needs MASSIVE context window for continuous operation
        # With 500 messages and ~7k tokens per message, we need ~3.5M tokens
        # Set to 1M tokens for refactoring (enough for ~140 messages at 7k each)
        if self.phase_name == 'refactoring':
            context_window = 1_000_000  # 1 million tokens for continuous refactoring
        
        # Create base conversation thread
        thread = OrchestrationConversationThread(
            model=phase_model,
            role=self.phase_name,
            max_context_tokens=context_window
        )
        
        # Wrap with auto-pruning for memory management
        from ..orchestration.conversation_pruning import ConversationPruner
        
        pruning_config = PruningConfig(
            max_messages=500,  # Keep max 500 messages for substantial context (was 50)
            preserve_first_n=10,  # Keep first 10 (initial context)
            preserve_last_n=100,  # Keep last 100 (recent context)
            preserve_errors=True,  # Always keep errors
            preserve_decisions=True,  # Keep decision points
            summarize_pruned=True,  # Create summaries
            min_prune_age_minutes=120  # Only prune messages >2 hours old (was 30 min)
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
        
        # Initialize adaptive prompts (passed from coordinator)
        self.adaptive_prompts = adaptive_prompts
        
        # Initialize the 6 core engines (passed from coordinator)
        self.pattern_recognition = pattern_recognition
        self.correlation_engine = correlation_engine
        self.analytics = analytics
        self.pattern_optimizer = pattern_optimizer
        
        # Initialize pattern feedback system for self-correcting behavior
        from ..pattern_feedback import PromptFeedbackSystem
        self.pattern_feedback = PromptFeedbackSystem(self.project_dir)
        
        # CRITICAL: Initialize Architecture Manager and IPC Integration
        from ..architecture_manager import ArchitectureManager
        from ..ipc_integration import ObjectiveReader, StatusWriter, StatusReader
        from ..document_updater import DocumentUpdater
        
        self.arch_manager = ArchitectureManager(self.project_dir, self.logger)
        self.objective_reader = ObjectiveReader(self.project_dir, self.logger)
        self.status_writer = StatusWriter(self.project_dir, self.logger)
        self.status_reader = StatusReader(self.project_dir, self.logger)
        self.doc_updater = DocumentUpdater(self.project_dir, self.logger)
        
        # CRITICAL FIX: Add system prompt to conversation at initialization
        # This ensures the model always sees the system prompt with tool calling instructions
        # MUST be done AFTER prompt_registry is set!
        # Note: We'll add the adapted prompt later when adaptive_prompts is available
        system_prompt = self._get_system_prompt(self.phase_name)
        if system_prompt:
            self.conversation.add_message("system", system_prompt)
        else:
            pass
        
        # INTEGRATION: Use shared specialists if provided
        if coding_specialist is None or reasoning_specialist is None or analysis_specialist is None:
            from ..orchestration.unified_model_tool import UnifiedModelTool
            from ..orchestration.specialists import (
                create_coding_specialist,
                create_reasoning_specialist,
                create_analysis_specialist
            )
            
            # Get server URLs from config instead of hardcoding
            coding_model, coding_server = config.model_assignments.get('coding', ('qwen2.5-coder:32b', 'ollama02.thiscluster.net'))
            reasoning_model = 'qwen2.5:32b'  # Reasoning uses larger model
            reasoning_server = coding_server  # Same server as coding
            analysis_model, analysis_server = config.model_assignments.get('planning', ('qwen2.5:14b', 'ollama01.thiscluster.net'))
            
            # Create unified model tools for specialists (fallback)
            self.coding_tool = UnifiedModelTool(coding_model, f"http://{coding_server}:11434")
            self.reasoning_tool = UnifiedModelTool(reasoning_model, f"http://{reasoning_server}:11434")
            self.analysis_tool = UnifiedModelTool(analysis_model, f"http://{analysis_server}:11434")
            
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
        
        # Document-based IPC system
        from ..document_ipc import DocumentIPC
        self.doc_ipc = DocumentIPC(self.project_dir, self.logger)
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
            pass
            # Execute phase
            result = self.execute(state, **kwargs)
            
            # Update phase state (with defensive check)
            if self.phase_name in state.phases:
                state.phases[self.phase_name].record_run(result.success)
            else:
                pass
                # Phase not registered in state - log warning and create it
                from pipeline.state.manager import PhaseState
                self.logger.warning(f"Phase '{self.phase_name}' not found in state.phases, creating it now")
                state.phases[self.phase_name] = PhaseState()
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
        # Check if it's a directory
        if full_path.is_dir():
            self.logger.warning(f"Cannot read {filepath}: it's a directory, not a file")
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
            pass
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
    
    # Document IPC Methods
    
    def read_own_tasks(self) -> str:
        """Read tasks from own READ document."""
        return self.doc_ipc.read_own_document(self.phase_name)
    
    def write_own_status(self, status: str):
        """Write status to own WRITE document."""
        self.doc_ipc.write_own_document(self.phase_name, status)
    
    def send_message_to_phase(self, to_phase: str, message: str):
        """Send message to another phase's READ document."""
        self.doc_ipc.write_to_phase(self.phase_name, to_phase, message)
    
    def read_phase_output(self, phase: str) -> str:
        """Read another phase's WRITE document."""
        return self.doc_ipc.read_phase_output(phase)
    
    def read_strategic_docs(self) -> Dict[str, str]:
        """Read all strategic documents."""
        return self.doc_ipc.read_all_strategic_documents()
    
    def initialize_ipc_documents(self):
        """Initialize IPC documents if they don't exist."""
        self.doc_ipc.initialize_documents()
    
    def format_timestamp(self, iso_timestamp: str = None) -> str:
        """Format a timestamp for display"""
        if iso_timestamp:
            try:
                dt = datetime.fromisoformat(iso_timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return iso_timestamp
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    # ==================== ARCHITECTURE & IPC METHODS ====================
    
    def _read_architecture(self) -> Dict[str, Any]:
        """
        Read ARCHITECTURE.md before making decisions.
        
        All phases MUST call this before execution to understand:
        - Project structure and organization
        - Component definitions and locations
        - Naming conventions
        - Integration guidelines
        
        Returns:
            Dict with architecture information
        """
        return self.arch_manager.read_architecture()
    
    def _update_architecture(self, changes: Dict[str, Any]):
        """
        Update ARCHITECTURE.md after making structural changes.
        
        Args:
            changes: Dict with:
                - type: Type of change (e.g., 'component_added', 'structure_modified')
                - details: Change details
        """
        self.arch_manager.record_change(
            phase=self.phase_name,
            change_type=changes.get('type', 'unknown'),
            details=changes.get('details', {})
        )
    
    def _read_objectives(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Read objectives from PRIMARY/SECONDARY/TERTIARY_OBJECTIVES.md.
        
        All phases MUST call this to understand:
        - What needs to be built (PRIMARY)
        - What needs to be fixed (SECONDARY)
        - What optimizations are needed (TERTIARY)
        
        Returns:
            Dict with 'primary', 'secondary', 'tertiary' objectives
        """
        return self.objective_reader.get_all_objectives()
    
    def _write_status(self, status: Dict[str, Any]):
        """
        Write status update to this phase's WRITE document.
        
        Args:
            status: Status dict with:
                - status: 'running', 'completed', 'failed'
                - message: Status message
                - files_modified: List of modified files
        """
        self.status_writer.write_phase_status(self.phase_name, status)
    
    def _read_other_phase_status(self, phase: str) -> List[Dict[str, Any]]:
        """
        Read status updates from another phase.
        
        Args:
            phase: Phase name to read from
            
        Returns:
            List of status updates from that phase
        """
        return self.status_reader.read_phase_status(phase)
    
    def _request_from_phase(self, target_phase: str, action: str, reason: str, details: str = ""):
        """
        Request an action from another phase.
        
        Args:
            target_phase: Phase to request from
            action: What action is requested
            reason: Why it's needed
            details: Additional details
        """
        self.status_writer.write_request(
            from_phase=self.phase_name,
            to_phase=target_phase,
            request={
                'action': action,
                'reason': reason,
                'details': details
            }
        )
    
    # ==================== SYSTEM PROMPT METHODS ====================
    
    def _get_system_prompt(self, phase_name: str, context: Dict = None) -> str:
        """
        Get system prompt with adaptive enhancements.
        
        ENHANCED: Now uses adaptive prompt system to customize prompts based on:
        - Learned patterns from execution history
        - Self-awareness level
        - Current context and state
        - Pattern feedback (violation-based reminders)
        
        Args:
            phase_name: Name of the phase (e.g., "debugging", "coding")
            context: Optional context for adaptation
        
        Returns:
            Adapted system prompt string
        """
        from ..prompts import SYSTEM_PROMPTS
        
        # Try custom prompt first
        custom_prompt = self.prompt_registry.get_prompt(f"{phase_name}_system")
        if custom_prompt:
            self.logger.debug(f"  Using custom system prompt for {phase_name}")
            base_prompt = custom_prompt
        else:
            pass
            # Fallback to hardcoded
            base_prompt = SYSTEM_PROMPTS.get(phase_name, SYSTEM_PROMPTS.get("base", ""))
        
        # WEEK 2 ENHANCEMENT: Add pattern feedback additions
        # These are dynamic reminders based on detected workflow violations
        if hasattr(self, 'pattern_feedback') and self.pattern_feedback:
            try:
                feedback_additions = self.pattern_feedback.get_prompt_additions(phase_name)
                if feedback_additions:
                    self.logger.info(f"  📋 Adding pattern feedback reminders to {phase_name} prompt")
                    base_prompt = base_prompt + feedback_additions
            except Exception as e:
                pass
        
        # CRITICAL FIX: Apply adaptive prompt system if available
        if hasattr(self, 'adaptive_prompts') and self.adaptive_prompts and context:
            try:
                adapted_prompt = self.adaptive_prompts.adapt_prompt(
                    phase=phase_name,
                    base_prompt=base_prompt,
                    context=context
                )
                return adapted_prompt
            except Exception as e:
                return base_prompt
        
        return base_prompt
    
    # ==================== MESSAGE BUS METHODS ====================
    
    def _publish_message(self, message_type, payload: Dict, 
                        recipient: str = "broadcast",
                        priority=None,
                        **kwargs):
        """
        Publish a message to the message bus.
        
        Args:
            message_type: MessageType enum value
            payload: Message payload dictionary
            recipient: Recipient phase name or "broadcast"
            priority: MessagePriority enum value (optional)
            **kwargs: Additional message fields (objective_id, task_id, etc.)
        """
        if not self.message_bus:
            return
        
        from ..messaging import MessagePriority, MessageType
        
        # Convert string to MessageType enum if needed
        if isinstance(message_type, str):
            try:
                message_type = MessageType(message_type.lower())
            except ValueError:
                pass
                # If not a valid enum value, try to find it by name
                try:
                    message_type = MessageType[message_type.upper()]
                except KeyError:
                    self.logger.warning(f"Unknown message type: {message_type}, using as-is")
        
        if priority is None:
            priority = MessagePriority.NORMAL
        
        if recipient == "broadcast":
            self.message_bus.broadcast(
                sender=self.phase_name,
                message_type=message_type,
                payload=payload,
                priority=priority,
                **kwargs
            )
        else:
            self.message_bus.send_direct(
                sender=self.phase_name,
                recipient=recipient,
                message_type=message_type,
                payload=payload,
                priority=priority,
                **kwargs
            )
    
    def _subscribe_to_messages(self, message_types: List):
        """
        Subscribe this phase to specific message types.
        
        Args:
            message_types: List of MessageType enum values
        """
        if not self.message_bus:
            return
        
        self.message_bus.subscribe(self.phase_name, message_types)
    
    def _get_messages(self, **kwargs):
        """
        Get messages for this phase.
        
        Args:
            **kwargs: Filtering options (since, message_types, priority, limit)
        
        Returns:
            List of Message objects
        """
        if not self.message_bus:
            return []
        
        return self.message_bus.get_messages(self.phase_name, **kwargs)
    
    def _clear_messages(self, message_ids=None):
        """
        Clear messages from this phase's queue.
        
        Args:
            message_ids: Specific message IDs to clear, or None for all
        
        Returns:
            Number of messages cleared
        """
        if not self.message_bus:
            return 0
        
        return self.message_bus.clear_messages(self.phase_name, message_ids)
    
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
        
        # Get model and host for this phase using intelligent selection with fallbacks
        result = self.client.get_model_for_task(self.phase_name)
        if result:
            host, model_name = result
            self.logger.debug(f"  Selected model: {model_name} on {host}")
        else:
            pass
            # Fallback to conversation model and first available server
            model_name = self.conversation.thread.model
            host = self.config.servers[0].host if self.config.servers else "localhost"
            self.logger.warning(f"  No model found via get_model_for_task, using fallback: {model_name} on {host}")
        
        # ENHANCED: Detailed pre-call logging
        import time
        from ..progress_indicator import ProgressIndicator
        
        self.logger.info(f"")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"🤖 CALLING MODEL: {model_name}")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"  📡 Server: {host}")
        self.logger.info(f"  💬 Messages in conversation: {len(messages)}")
        self.logger.info(f"  🔧 Tools available: {len(tools) if tools else 0}")
        if tools:
            tool_names = [t.get('function', {}).get('name', 'unknown') for t in tools]
            self.logger.info(f"  🛠️  Tool names: {', '.join(tool_names[:10])}{' ...' if len(tool_names) > 10 else ''}")
        total_chars = sum(len(str(m.get('content', ''))) for m in messages)
        approx_tokens = total_chars // 4
        self.logger.info(f"  ⏱️  Waiting for response...")
        self.logger.info(f"{'='*70}")
        start_time = time.time()
        
        # Call model with conversation history and progress indicator
        with ProgressIndicator(self.logger, f"Model {model_name} thinking"):
            response = self.client.chat(
                host=host,
                model=model_name,
                messages=messages,
                tools=tools
            )
        
        # ENHANCED: Detailed post-call logging
        duration = time.time() - start_time
        self.logger.info(f"")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"  ⏱️  Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        message_obj = response.get("message", {})
        content = message_obj.get("content", "")
        tool_calls_raw = message_obj.get("tool_calls", [])
        self.logger.info(f"  📝 Response length: {len(content):,} characters")
        if tool_calls_raw:
            self.logger.info(f"  🔧 Tool calls: {len(tool_calls_raw)}")
            for i, tc in enumerate(tool_calls_raw[:5], 1):
                func = tc.get('function', {})
                self.logger.info(f"     {i}. {func.get('name', 'unknown')}")
        else:
            self.logger.info(f"  🔧 Tool calls: None")
        if content:
            preview = content[:200].replace('\n', ' ')
            self.logger.info(f"  💬 Preview: {preview}{'...' if len(content) > 200 else ''}")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"")
        
        # Add assistant response to conversation
        content = response.get("message", {}).get("content", "")
        self.conversation.add_message("assistant", content)
        
        # Check if model is requesting specialist help
        if hasattr(self, 'specialist_request_handler') and task_context:
            request = self.specialist_request_handler.detect_request(content)
            if request:
                pass
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
        tool_calls_parsed, _ = self.parser.parse_response(response, tools or [])
        
        return {
            "content": content,
            "tool_calls": tool_calls_parsed,
            "raw_response": response
        }
    
    def update_system_prompt_with_adaptation(self, context: Dict = None):
        """
        Update system prompt with adaptive enhancements.
        
        Called after adaptive_prompts is set to replace the base prompt
        with an adapted version.
        
        Args:
            context: Context for adaptation (state, self_awareness, etc.)
        """
        if not self.adaptive_prompts:
            return
        
        try:
            pass
            # Get adapted prompt
            adapted_prompt = self._get_system_prompt(self.phase_name, context)
            
            # Replace system message in conversation
            # Find and replace the first system message
            for i, msg in enumerate(self.conversation.thread.messages):
                if msg.get('role') == 'system':
                    self.conversation.thread.messages[i]['content'] = adapted_prompt
                    break
        except Exception as e:
            pass
    
    def record_execution_pattern(self, pattern_data: Dict):
        """Record execution pattern for learning."""
        if not self.pattern_recognition:
            return
        try:
            from datetime import datetime
            self.pattern_recognition.record_execution({
                'phase': self.phase_name,
                'timestamp': datetime.now().isoformat(),
                **pattern_data
            })
        except Exception as e:
            pass
    
    def get_cross_phase_correlation(self, correlation_data: Dict) -> Dict:
        """Get cross-phase correlations."""
        if not self.correlation_engine:
            return {}
        try:
            pass
            # correlate() takes no arguments, just returns all correlations
            return self.correlation_engine.correlate()
        except Exception as e:
            return {}
    
    def track_phase_metric(self, metric_data: Dict):
        """Track phase metric for analytics."""
        if not self.analytics:
            return
        try:
            pass
            # Analytics doesn't have track_metric, it has specific methods
            # For now, just log the metric
        except Exception as e:
            pass
    
    def get_optimization_suggestion(self, context: Dict) -> Dict:
        """Get optimization suggestion from pattern optimizer."""
        if not self.pattern_optimizer:
            return {}
        try:
            pass
            # PatternOptimizer doesn't have get_suggestion
            # It has run_full_optimization() which returns statistics
            # For now, return empty dict
            return {}
        except Exception as e:
            return {}
    
    def track_dimensions(self, dimension_updates: Dict[str, float]):
        """
        Track and update dimensional values for polytopic structure.
        
        This method enables phases to dynamically update their position in the
        8-dimensional hyperdimensional space based on execution characteristics.
        
        Args:
            dimension_updates: Dict of dimension -> value (0.0-1.0)
                Supported dimensions:
                - temporal: Execution time, duration, frequency
                - functional: Complexity, call depth, functionality
                - data: Data flow, transformations, volume
                - state: State transitions, consistency, history
                - error: Error patterns, recovery, correlation
                - context: Context switches, preservation, dependencies
                - integration: Integration points, health, dependencies
                - architecture: Consistency, drift, evolution
        """
        if not hasattr(self, 'coordinator') or not self.coordinator:
            return
        
        try:
            pass
            # Update dimensions in coordinator's polytopic structure
            if hasattr(self.coordinator, 'polytope') and self.coordinator.polytope:
                phase_vertex = self.coordinator.polytope['vertices'].get(self.phase_name)
                if phase_vertex and 'dimensions' in phase_vertex:
                    for dim, value in dimension_updates.items():
                        if dim in phase_vertex['dimensions']:
                            pass
                            # Blend old and new values (exponential moving average)
                            # This creates smooth transitions and prevents sudden jumps
                            old_value = phase_vertex['dimensions'][dim]
                            phase_vertex['dimensions'][dim] = 0.7 * old_value + 0.3 * value
                    
                    self.logger.debug(f"  📐 Updated {len(dimension_updates)} dimensions for {self.phase_name}")
        except Exception as e:
            pass
    
    def track_violation(self, violation_type: str, context: Optional[Dict] = None, severity: Optional[str] = None):
        """
        Track a workflow violation for pattern feedback.
        
        This enables self-correcting behavior by:
        1. Recording when AI violates workflow steps
        2. Detecting repeat patterns
        3. Dynamically adding prompt reminders
        
        Args:
            violation_type: Type of violation (e.g., "skipped_discovery", "created_duplicate")
            context: Additional context about the violation
            severity: Override default severity ("low", "medium", "high")
        
        Example:
            # In coding phase, if AI skips find_similar_files:
            self.track_violation("skipped_discovery", 
                               context={"target_file": task.target_file})
        """
        if not hasattr(self, 'pattern_feedback') or not self.pattern_feedback:
            return
        
        try:
            self.pattern_feedback.track_workflow_violation(
                phase=self.phase_name,
                violation_type=violation_type,
                context=context,
                severity=severity
            )
            self.logger.debug(f"  📋 Tracked violation: {violation_type}")
        except Exception as e:
            pass
    
    def mark_violation_resolved(self, violation_type: str):
        """
        Mark a violation as resolved (AI followed workflow correctly).
        
        This helps measure effectiveness of prompt additions and
        automatically removes reminders when patterns are consistently resolved.
        
        Args:
            violation_type: Type of violation that was resolved
        
        Example:
            # In coding phase, if AI correctly calls find_similar_files:
            self.mark_violation_resolved("skipped_discovery")
        """
        if not hasattr(self, 'pattern_feedback') or not self.pattern_feedback:
            return
        
        try:
            self.pattern_feedback.mark_violation_resolved(
                phase=self.phase_name,
                violation_type=violation_type
            )
        except Exception as e:
            pass
    
    def get_pattern_summary(self) -> Dict:
        """
        Get summary of violation patterns for this phase.
        
        Returns:
            Dictionary with pattern statistics
        """
        if not hasattr(self, 'pattern_feedback') or not self.pattern_feedback:
            return {}
        
        try:
            return self.pattern_feedback.get_pattern_summary(phase=self.phase_name)
        except Exception as e:
            return {}
