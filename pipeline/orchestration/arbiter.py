"""
Arbiter Model

The arbiter coordinates all model interactions, routing queries to specialists
and making high-level decisions about workflow and phase transitions.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..client import OllamaClient
from pipeline.logging_setup import get_logger
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
        
        # Call arbiter model WITHOUT tools (model can't handle them properly)
        # Instead, we'll parse the text response
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            tools=None,
            temperature=0.3
        )
        
        # Log the raw response
        self.logger.info(f"📥 Arbiter Raw Response:\n{response}")
        
        # Parse decision from TEXT response (not tool calls)
        decision = self._parse_text_decision(response, state, context)
        
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
        
        # Get current phase safely
        current_phase = getattr(state, "current_phase", 
                               state.phase_history[-1] if hasattr(state, "phase_history") and state.phase_history else "unknown")
        
        # Get QA pending count
        qa_pending = len([t for t in state.tasks.values() 
                         if t.status == TaskStatus.QA_PENDING])
        
        # Get needs fixes count
        needs_fixes = len([t for t in state.tasks.values() 
                          if t.status == TaskStatus.NEEDS_FIXES])
        
        # Add arbiter-specific decision context
        prompt += f"""

PROJECT STATUS:
- Current Phase: {current_phase}
- Total Tasks: {len(state.tasks)}
- Completed: {len([t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED])}
- In Progress: {prompt_context.task['pending_tasks']}
- QA Pending: {qa_pending}
- Needs Fixes: {needs_fixes}
- Recent Failures: {len(prompt_context.recent_failures)}

YOUR DECISION (choose ONE action):

If QA pending tasks exist ({qa_pending} tasks):
→ Call: consult_analysis_specialist with query "Review QA pending tasks"

If failures exist ({len(prompt_context.recent_failures)} failures):
→ Call: consult_reasoning_specialist with query "Diagnose recent failures"

If needs fixes exist ({needs_fixes} tasks):
→ Call: change_phase with phase "debugging" and reason "Tasks need fixes"

If documentation needed (context shows needs_documentation: {context.get('needs_documentation', False)}):
→ Call: change_phase with phase "documentation" and reason "Documentation is needed"

If no pending work and phase is complete:
→ Call: change_phase with phase "<next_logical_phase>" and reason "Current phase complete"

Otherwise:
→ Call: continue_current_phase

MAKE YOUR DECISION NOW. Call exactly ONE tool.
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
        return """You are an arbiter that makes DECISIONS, not asks questions.

YOU MUST DECIDE what to do next. DO NOT ask what should happen - YOU decide.

Your ONLY way to communicate is through tool calls. No text allowed.

Available tools:
- consult_coding_specialist: Get expert help with implementation
- consult_reasoning_specialist: Get strategic analysis and recommendations
- consult_analysis_specialist: Get quick code review or assessment
- change_phase: Move to a different phase (coding, qa, debugging, etc.)
- request_user_input: Ask user for clarification ONLY when you cannot decide
- continue_current_phase: Keep working on current phase

DECISION RULES:
1. If there are QA pending tasks → consult_analysis_specialist to review them
2. If there are failures → consult_reasoning_specialist to diagnose
3. If documentation is needed → change_phase to "documentation"
4. If no pending work → change_phase to next logical phase
5. If truly stuck → request_user_input

NEVER ask "what should happen?" - YOU DECIDE what happens.

Example GOOD response:
<tool_call>
<name>consult_analysis_specialist</name>
<arguments>{"query": "Review the 2 QA pending tasks and determine if they pass quality checks"}</arguments>
</tool_call>

Example BAD response (asking instead of deciding):
<tool_call>
<name>consult_reasoning_specialist</name>
<arguments>{"query": "What should we do next?"}</arguments>
</tool_call>"""
    
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
    
    def _parse_text_decision(self, response: Dict[str, Any], state: PipelineState, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse decision from TEXT response (not tool calls).
        
        The model can't generate proper tool calls, so we parse the text.
        """
        content = response.get("message", {}).get("content", "").lower()
        
        self.logger.info(f"📝 Parsing text decision from: {content[:200]}")
        
        # Check for phase change
        if "change_phase" in content or "change to" in content or "move to" in content:
            # Extract phase name
            for phase in ["coding", "qa", "debugging", "documentation", "planning"]:
                if phase in content:
                    return {
                        "action": "change_phase",
                        "phase": phase,
                        "reason": "Arbiter decided to change phase"
                    }
        
        # Check for specialist consultation
        if "consult" in content or "ask" in content or "get help" in content:
            if "analysis" in content or "review" in content or "qa" in content:
                return {
                    "action": "consult_specialist",
                    "specialist": "analysis",
                    "query": "Review current tasks",
                    "context": {}
                }
            elif "reasoning" in content or "diagnose" in content or "failure" in content:
                return {
                    "action": "consult_specialist",
                    "specialist": "reasoning",
                    "query": "Diagnose issues",
                    "context": {}
                }
            elif "coding" in content or "implement" in content:
                return {
                    "action": "consult_specialist",
                    "specialist": "coding",
                    "query": "Help with implementation",
                    "context": {}
                }
        
        # Check for user input request
        if "user" in content or "ask user" in content or "need input" in content:
            return {
                "action": "request_user_input",
                "question": "What should happen next?",
                "context": "Arbiter needs guidance"
            }
        
        # Default: continue current phase
        return {
            "action": "continue_current_phase",
            "reason": "No clear action in response"
        }
    
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
        
        # If tool name is empty, try to extract from content first
        if not name:
            self.logger.warning(f"Empty tool name in tool call. Full tool_call: {first_call}")
            self.logger.warning(f"Function dict: {func}")
            self.logger.warning(f"All tool_calls: {tool_calls}")
            
            # FIRST: Try to extract tool name from the content field (arbiter often writes it there)
            content = response.get("message", {}).get("content", "")
            if content:
                self.logger.info(f"📝 Checking arbiter content for tool name: {content[:200]}")
                available_tools = [t['name'] for t in self._get_arbiter_tools()]
                for tool_name in available_tools:
                    if tool_name in content:
                        name = tool_name
                        self.logger.info(f"✓ Found tool name in content: {name}")
                        # Try to extract arguments from content if present
                        import json
                        try:
                            # Look for JSON in the content
                            if "{" in content and "}" in content:
                                json_start = content.index("{")
                                json_end = content.rindex("}") + 1
                                json_str = content[json_start:json_end]
                                extracted_args = json.loads(json_str)
                                args = extracted_args
                                self.logger.info(f"✓ Extracted arguments from content: {args}")
                        except Exception as e:
                            self.logger.debug(f"Could not extract JSON from content: {e}")
                        break
            
            # If still no name, infer from arguments
            if not name:
                self.logger.info("🔍 Inferring tool name from arguments...")
                
                # Infer tool based on argument keys and content
                if "new_phase" in args or "phase" in args:
                    name = "change_phase"
                    # Normalize the argument name
                    if "new_phase" in args and "phase" not in args:
                        args["phase"] = args.pop("new_phase")
                    self.logger.info(f"✓ Inferred tool from 'phase' argument: {name}")
                elif "query" in args:
                    # Infer which specialist based on query content
                    query = args.get("query", "").lower()
                    if "review" in query or "qa" in query or "check" in query or "quality" in query:
                        name = "consult_analysis_specialist"
                        self.logger.info(f"✓ Inferred analysis specialist from query: {query[:50]}")
                    elif "diagnose" in query or "failure" in query or "error" in query or "debug" in query:
                        name = "consult_reasoning_specialist"
                        self.logger.info(f"✓ Inferred reasoning specialist from query: {query[:50]}")
                    elif "implement" in query or "code" in query or "write" in query or "create" in query:
                        name = "consult_coding_specialist"
                        self.logger.info(f"✓ Inferred coding specialist from query: {query[:50]}")
                    else:
                        # Default to reasoning for strategic questions
                        name = "consult_reasoning_specialist"
                        self.logger.info(f"✓ Defaulting to reasoning specialist for query: {query[:50]}")
                elif "message" in args or "question" in args:
                    name = "request_user_input"
                    self.logger.info(f"✓ Inferred tool from message/question argument: {name}")
                else:
                    # Default fallback
                    name = "continue_current_phase"
                    self.logger.warning(f"⚠️ Could not infer tool, defaulting to: {name}")
        
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
            action = decision.get('decision', None).get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_decisions": len(self.decision_history),
            "action_counts": action_counts,
            "specialist_stats": self.specialists.get_stats(),
            "conversation_stats": self.conversation_manager.get_all_stats()
        }