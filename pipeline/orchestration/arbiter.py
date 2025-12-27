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
        
        # Call arbiter model
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_arbiter_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            tools=tools,
            temperature=0.3
        )
        
        # Parse decision
        decision = self._parse_decision(response)
        
        # Record decision
        self.decision_history.append({
            "decision": decision,
            "state": state.current_phase,
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
        
        # Review the response
        reviewed = self.review_specialist_response(specialist_name, result)
        
        return reviewed
    
    def review_specialist_response(self, specialist_name: str, 
                                   response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a specialist's response.
        
        The arbiter can:
        - Approve the response as-is
        - Request clarification via FunctionGemma
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
        
        # Check if tool calls are clear
        tool_calls = response.get("tool_calls", [])
        
        if not tool_calls:
            # No tool calls - might need clarification
            self.logger.debug(f"  No tool calls from {specialist_name}")
            
            # Try FunctionGemma to extract tool calls
            content = response.get("response", {}).get("message", {}).get("content", "")
            if content:
                self.logger.info(f"  Attempting tool call extraction with FunctionGemma...")
                clarified = self.consult_specialist("interpreter", 
                    f"Extract tool calls from this response:\n\n{content}")
                
                if clarified.get("success") and clarified.get("tool_calls"):
                    response["tool_calls"] = clarified["tool_calls"]
                    response["clarified_by_functiongemma"] = True
        
        # Check for empty tool names
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            
            if not name or name.strip() == "":
                self.logger.warning(f"  ⚠️ Empty tool name detected, requesting clarification...")
                
                # Use FunctionGemma to fix
                clarified = self.consult_specialist("interpreter",
                    f"Fix this tool call with empty name:\n\n{tc}")
                
                if clarified.get("success"):
                    # Replace with clarified version
                    response["tool_calls"] = clarified.get("tool_calls", [])
                    response["clarified_by_functiongemma"] = True
        
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
        Build prompt for decision-making.
        
        Args:
            state: Pipeline state
            context: Additional context
        
        Returns:
            Prompt string
        """
        # Get pending tasks
        pending_tasks = [
            t for t in state.tasks.values()
            if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
        ]
        
        # Get recent failures
        recent_failures = []
        for task in state.tasks.values():
            if task.errors:
                recent_failures.extend(task.errors[-3:])  # Last 3 errors per task
        
        prompt = f"""You are coordinating an AI development pipeline.

CURRENT STATE:
- Phase: {state.current_phase}
- Total tasks: {len(state.tasks)}
- Pending tasks: {len(pending_tasks)}
- Recent failures: {len(recent_failures)}

CONTEXT:
{self._format_context(context)}

AVAILABLE SPECIALISTS:
- coding: Expert Python developer (32b model, ollama02)
- reasoning: Strategic thinker (32b model, ollama02)
- analysis: Quick analyzer (14b model, ollama01)
- interpreter: Tool call clarifier (FunctionGemma, ollama01)

DECIDE:
What should happen next? Consider:
1. Are there tasks that need specialist attention?
2. Should we change phases?
3. Do we need user input?
4. Are there failures that need diagnosis?

Use tools to make your decision.
"""
        
        return prompt
    
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

You have access to specialist models:
- Coding specialist: For implementation tasks
- Reasoning specialist: For strategic analysis
- Analysis specialist: For quick checks
- Interpreter specialist: For clarifying tool calls

Make decisions efficiently and delegate to specialists when appropriate.
Use tools to communicate your decisions."""
    
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