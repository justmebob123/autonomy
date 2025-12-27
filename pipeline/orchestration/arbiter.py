"""
Arbiter Model

The arbiter coordinates all model interactions, routing queries to specialists
and making high-level decisions about workflow and phase transitions.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..client import OllamaClient
from ..logging_setup import get_logger
from ..state.manager import PipelineState, TaskStatus

from .model_tool import get_specialist_registry, ModelTool
from .conversation_manager import MultiModelConversationManager
from .dynamic_prompts import DynamicPromptBuilder, PromptContext


class ArbiterModel:
    """
    The arbiter coordinates all model interactions.
    
    Uses a fast 14b model on ollama01 for quick decision-making.
    Consults specialists for complex tasks.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize the arbiter.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = project_dir
        self.model = "qwen2.5:14b"
        self.server = "ollama01.thiscluster.net"
        
        # Import config
        from ..config import PipelineConfig
        config = PipelineConfig()
        self.client = OllamaClient(config)
        self.logger = get_logger()
        
        # Get specialist registry
        self.specialists = get_specialist_registry()
        
        # Conversation manager
        self.conversation_manager = MultiModelConversationManager(arbiter_model=self.model)
        
        # Dynamic prompt builder
        self.prompt_builder = DynamicPromptBuilder(project_dir)
        
        # Decision history
        self.decision_history: List[Dict] = []
        
        self.logger.info(f"🎯 Arbiter initialized: {self.model} on {self.server}")
    
    def decide_action(self, state: PipelineState, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide what action to take next.
        
        This is the main decision-making method. The arbiter analyzes the
        current state and decides:
        - Which specialist to consult (if any)
        - Whether to change phases
        - Whether to request user input
        - How to handle failures
        
        Args:
            state: Current pipeline state
            context: Additional context
        
        Returns:
            Dict with action decision
        """
        self.logger.info("🎯 Arbiter making decision...")
        
        # Build decision prompt
        prompt = self._build_decision_prompt(state, context)
        
        # Get arbiter tools
        tools = self._get_arbiter_tools()
        
        # Log the request details
        system_prompt = self._get_arbiter_system_prompt()
        self.logger.info(f"📝 Arbiter System Prompt:\n{system_prompt}")
        self.logger.info(f"📝 Arbiter User Prompt:\n{prompt}")
        self.logger.info(f"🔧 Available tools: {[t['name'] for t in tools]}")
        
        # Call arbiter model
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            tools=tools,
            temperature=0.3
        )
        
        # Log the raw response
        self.logger.info(f"📥 Arbiter Raw Response:\n{response}")
        
        # Parse decision
        decision = self._parse_decision(response)
        
        # Record decision
        self.decision_history.append({
            "decision": decision,
            "state": getattr(state, "current_phase", state.phase_history[-1] if hasattr(state, "phase_history") and state.phase_history else "unknown"),
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"  ✓ Decision: {decision['action']}")
        
        return decision
    
    def consult_specialist(self, specialist_name: str, query: str, 
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Consult a specialist model.
        
        Args:
            specialist_name: Name of specialist (coding, reasoning, analysis, interpreter)
            query: Query for the specialist
            context: Additional context
        
        Returns:
            Dict with specialist response
        """
        self.logger.info(f"🔧 Consulting {specialist_name} specialist...")
        
        # Get specialist
        specialist = self.specialists.get(specialist_name)
        
        if not specialist:
            self.logger.error(f"  ✗ Unknown specialist: {specialist_name}")
            return {
                "success": False,
                "error": f"Unknown specialist: {specialist_name}"
            }
        
        # Call specialist
        result = specialist(query, context)
        
        # CRITICAL: Do NOT review interpreter responses to avoid infinite loops
        # The interpreter (FunctionGemma) is used FOR reviewing, not to be reviewed
        if specialist_name == "interpreter":
            return result
        
        # Review the response for other specialists
        reviewed = self.review_specialist_response(specialist_name, result)
        
        return reviewed
    
    def review_specialist_response(self, specialist_name: str, 
                                   response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a specialist's response.
        
        The arbiter can:
        - Approve the response as-is
        - Request clarification via FunctionGemma (max 1 attempt)
        - Consult another specialist for a second opinion
        
        Args:
            specialist_name: Name of specialist
            response: Specialist's response
        
        Returns:
            Dict with reviewed response
        """
        # Check if response was successful
        if not response.get("success"):
            self.logger.warning(f"  ⚠️ Specialist {specialist_name} failed")
            return response
        
        # Check if already clarified (prevent infinite loops)
        if response.get("clarified_by_functiongemma"):
            return response
        
        # Check if tool calls are clear
        tool_calls = response.get("tool_calls", [])
        
        if not tool_calls:
            # No tool calls - might need clarification
            self.logger.debug(f"  No tool calls from {specialist_name}")
            
            # Try FunctionGemma to extract tool calls (ONCE only)
            content = response.get("response", {}).get("message", {}).get("content", "")
            if content:
                self.logger.info(f"  Attempting tool call extraction with FunctionGemma...")
                clarified = self.consult_specialist("interpreter", 
                    f"Extract tool calls from this response:\n\n{content}")
                
                if clarified.get("success") and clarified.get("tool_calls"):
                    response["tool_calls"] = clarified["tool_calls"]
                    response["clarified_by_functiongemma"] = True
                else:
                    self.logger.warning("  ✗ FunctionGemma could not extract tool calls")
        
        # Check for empty tool names
        has_empty_names = False
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            
            if not name or name.strip() == "":
                has_empty_names = True
                break
        
        if has_empty_names:
            self.logger.warning(f"  ⚠️ Empty tool name detected, requesting clarification...")
            
            # Use FunctionGemma to fix (ONCE only)
            clarified = self.consult_specialist("interpreter",
                f"Fix this tool call with empty name. Available tools: {[t['name'] for t in self._get_arbiter_tools()]}. Tool calls: {tool_calls}")
            
            if clarified.get("success") and clarified.get("tool_calls"):
                # Replace with clarified version
                response["tool_calls"] = clarified.get("tool_calls", [])
                response["clarified_by_functiongemma"] = True
            else:
                self.logger.warning("  ✗ FunctionGemma could not fix empty tool names")
        
        return response
    
    def review_message(self, from_model: str, to_model: str, 
                      message: str, context: List[Dict]) -> Dict[str, Any]:
        """
        Review a message before routing between models.
        
        The arbiter can:
        - Approve the message as-is
        - Modify the message
        - Redirect to a different model
        
        Args:
            from_model: Source model
            to_model: Destination model
            message: Message content
            context: Conversation context
        
        Returns:
            Dict with review decision
        """
        # Simple review for now - could be more sophisticated
        return {
            "should_modify": False,
            "should_redirect": False,
            "approved": True
        }
    
    def _build_decision_prompt(self, state: PipelineState, context: Dict[str, Any]) -> str:
        """
        Build prompt for decision-making using DynamicPromptBuilder.
        
        Args:
            state: Pipeline state
            context: Additional context
        
        Returns:
            Prompt string
        """
        # Use DynamicPromptBuilder for context-aware prompts
        prompt_context = PromptContext(
            phase="arbiter_decision",
            task={
                "type": "decision_making",
                "complexity": self._assess_decision_complexity(state),
                "pending_tasks": len([t for t in state.tasks.values() 
                                     if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]])
            },
            model_size="14b",
            model_capabilities=["tool_calling", "reasoning", "decision_making"],
            context_window=8192,
            recent_failures=self._get_recent_failures(state),
            project_context={
                "state": state,
                "context": context,
                "specialists": {
                    "coding": "Expert Python developer (32b model, ollama02)",
                    "reasoning": "Strategic thinker (32b model, ollama02)",
                    "analysis": "Quick analyzer (14b model, ollama01)",
                    "interpreter": "Tool call clarifier (FunctionGemma, ollama01)"
                }
            },
            available_tools=self._get_arbiter_tools()
        )
        
        # Build dynamic prompt
        prompt = self.prompt_builder.build_prompt(prompt_context)
        
        # Add arbiter-specific instructions
        prompt += f"""

CURRENT STATE:
- Phase: {getattr(state, "current_phase", state.phase_history[-1] if hasattr(state, "phase_history") and state.phase_history else "unknown")}
- Total tasks: {len(state.tasks)}
- Pending tasks: {prompt_context.task['pending_tasks']}
- Recent failures: {len(prompt_context.recent_failures)}

CONTEXT:
{self._format_context(context)}

DECIDE:
What should happen next? Consider:
1. Are there tasks that need specialist attention?
2. Should we change phases?
3. Do we need user input?
4. Are there failures that need diagnosis?

CRITICAL: You MUST call exactly ONE tool from the available tools.
"""
        
        return prompt
    
    def _assess_decision_complexity(self, state: PipelineState) -> int:
        """Assess complexity of current decision (1-10)."""
        complexity = 1
        
        # More pending tasks = more complex
        pending = len([t for t in state.tasks.values() 
                      if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]])
        complexity += min(pending // 2, 3)
        
        # Recent failures increase complexity
        failures = self._get_recent_failures(state)
        complexity += min(len(failures), 3)
        
        # Phase transitions are complex
        if hasattr(state, "phase_history") and len(state.phase_history) > 1:
            if state.phase_history[-1] != state.phase_history[-2]:
                complexity += 2
        
        return min(complexity, 10)
    
    def _get_recent_failures(self, state: PipelineState) -> list:
        """Get recent failures from state as dicts."""
        failures = []
        for task in state.tasks.values():
            if task.errors:
                # Convert TaskError objects to dicts
                for error in task.errors[-3:]:
                    if hasattr(error, 'to_dict'):
                        failures.append(error.to_dict())
                    elif isinstance(error, dict):
                        failures.append(error)
                    else:
                        # Fallback: convert to dict manually
                        failures.append({
                            'error_type': getattr(error, 'error_type', 'unknown'),
                            'message': getattr(error, 'message', str(error)),
                            'timestamp': getattr(error, 'timestamp', ''),
                            'phase': getattr(error, 'phase', 'unknown')
                        })
        return failures
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt."""
        lines = []
        
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"- {key}: {value}")
            elif isinstance(value, list):
                lines.append(f"- {key}: {len(value)} items")
            elif isinstance(value, dict):
                lines.append(f"- {key}: {len(value)} entries")
        
        return "\n".join(lines) if lines else "No additional context"
    
    def _get_arbiter_system_prompt(self) -> str:
        """Get system prompt for arbiter."""
        return """You are an arbiter coordinating AI specialists in a development pipeline.

Your role is to:
1. Analyze the current situation
2. Decide which specialists to consult
3. Coordinate their work
4. Make strategic decisions about workflow

IMPORTANT: You MUST use the provided tools to make decisions. Always call exactly ONE tool:
- consult_coding_specialist: For implementation tasks
- consult_reasoning_specialist: For strategic analysis
- consult_analysis_specialist: For quick checks
- consult_interpreter_specialist: For clarifying tool calls
- change_phase: To change pipeline phase
- request_user_input: To ask user for guidance
- continue_current_phase: To continue current work

CRITICAL: Every response MUST include a tool call with a valid tool name from the list above.
Do NOT generate tool calls with empty names or invalid tool names."""
    
    def _get_arbiter_tools(self) -> List[Dict]:
        """Get tools available to the arbiter."""
        tools = []
        
        # Specialist consultation tools
        tools.extend(self.specialists.get_tool_definitions())
        
        # Phase management tools
        tools.append({
            "name": "change_phase",
            "description": "Change to a different pipeline phase",
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": ["planning", "coding", "qa", "debugging", "documentation"],
                        "description": "The phase to change to"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this phase change is needed"
                    }
                },
                "required": ["phase", "reason"]
            }
        })
        
        # User interaction tools
        tools.append({
            "name": "request_user_input",
            "description": "Request input or guidance from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context for the question"
                    }
                },
                "required": ["question"]
            }
        })
        
        # Continue with current phase
        tools.append({
            "name": "continue_current_phase",
            "description": "Continue with the current phase",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why we should continue"
                    }
                },
                "required": ["reason"]
            }
        })
        
        return tools
    
    def _parse_decision(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse arbiter's decision from response.
        
        Args:
            response: Model response
        
        Returns:
            Dict with parsed decision
        """
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        if not tool_calls:
            # No tool calls - default to continue
            return {
                "action": "continue_current_phase",
                "reason": "No specific action indicated"
            }
        
        # Get first tool call
        first_call = tool_calls[0]
        func = first_call.get("function", {})
        name = func.get("name", "")
        args = func.get("arguments", {})
        
        # If tool name is empty, use FunctionGemma to fix it
        if not name:
            self.logger.warning(f"Empty tool name in tool call. Full tool_call: {first_call}")
            self.logger.warning(f"Function dict: {func}")
            self.logger.warning(f"All tool_calls: {tool_calls}")
            
            # Try to use FunctionGemma to extract the correct tool call
            self.logger.info("🔧 Attempting to fix malformed tool call with FunctionGemma...")
            
            # Build detailed prompt for FunctionGemma
            available_tools = [t['name'] for t in self._get_arbiter_tools()]
            fg_prompt = f"""Fix this malformed tool call. The tool name is empty but the arguments suggest the intent.

MALFORMED TOOL CALL:
{first_call}

AVAILABLE TOOLS:
{available_tools}

ARGUMENTS PROVIDED:
{args}

Based on the arguments, which tool should be called? Return ONLY the tool name."""
            
            self.logger.info(f"📝 FunctionGemma Prompt:\n{fg_prompt}")
            
            try:
                clarified = self.consult_specialist("interpreter", fg_prompt,
                    {"malformed_call": first_call, "available_tools": self._get_arbiter_tools()}
                )
                
                self.logger.info(f"📥 FunctionGemma Response:\n{clarified}")
                
                if clarified.get("success") and clarified.get("tool_calls"):
                    fixed_call = clarified["tool_calls"][0]
                    fixed_func = fixed_call.get("function", {})
                    name = fixed_func.get("name", "")
                    if name:
                        self.logger.info(f"✓ FunctionGemma fixed tool call: {name}")
                        args = fixed_func.get("arguments", args)  # Use fixed args if available
                    else:
                        self.logger.warning(f"✗ FunctionGemma returned empty name. Full response: {clarified}")
                else:
                    self.logger.warning(f"✗ FunctionGemma clarification failed. Response: {clarified}")
            except Exception as e:
                self.logger.error(f"✗ Error using FunctionGemma: {e}", exc_info=True)
        
        # Parse based on tool name
        if name.startswith("consult_"):
            specialist = name.replace("consult_", "").replace("_specialist", "")
            return {
                "action": "consult_specialist",
                "specialist": specialist,
                "query": args.get("query", ""),
                "context": args.get("context", {})
            }
        
        elif name == "change_phase":
            return {
                "action": "change_phase",
                "phase": args.get("phase", ""),
                "reason": args.get("reason", "")
            }
        
        elif name == "request_user_input":
            return {
                "action": "request_user_input",
                "question": args.get("question", ""),
                "context": args.get("context", "")
            }
        
        elif name == "continue_current_phase":
            return {
                "action": "continue_current_phase",
                "reason": args.get("reason", "")
            }
        
        else:
            self.logger.warning(f"Unknown tool call: {name}")
            return {
                "action": "continue_current_phase",
                "reason": f"Unknown tool: {name}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get arbiter statistics.
        
        Returns:
            Dict with stats
        """
        # Count decisions by action
        action_counts = {}
        for decision in self.decision_history:
            action = decision["decision"].get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_decisions": len(self.decision_history),
            "action_counts": action_counts,
            "specialist_stats": self.specialists.get_stats(),
            "conversation_stats": self.conversation_manager.get_all_stats()
        }