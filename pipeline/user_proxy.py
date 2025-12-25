"""
User Proxy Agent - AI specialist that simulates user guidance
When the system needs "user" input, this creates an AI specialist to provide it.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

class UserProxyAgent:
    """
    Creates and consults an AI specialist to simulate user guidance.
    This ensures the system remains fully autonomous with no human blocking.
    """
    
    def __init__(self, role_registry, prompt_registry, tool_registry, client, config, logger=None):
        self.role_registry = role_registry
        self.prompt_registry = prompt_registry
        self.tool_registry = tool_registry
        self.client = client
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Track if we've created the user proxy role
        self._user_proxy_created = False
        
        # Initialize ToolAdvisor for FunctionGemma support
        from pipeline.agents.tool_advisor import ToolAdvisor
        self.tool_advisor = ToolAdvisor(client, config)
    
    def _ensure_user_proxy_role_exists(self) -> bool:
        """
        Ensure the UserProxy specialist role exists.
        Creates it if needed using RoleCreator.
        """
        # Check if role already exists
        if self.role_registry.has_specialist("user_proxy"):
            self.logger.info("✓ UserProxy role already exists")
            return True
        
        self.logger.info("Creating UserProxy specialist role...")
        
        # Define the role specification
        role_spec = {
            "name": "user_proxy",
            "description": "AI specialist that simulates user guidance when the system is stuck",
            "purpose": "Provide strategic guidance and alternative approaches when debugging loops are detected",
            "capabilities": [
                "Analyze debugging history and identify why loops are occurring",
                "Suggest alternative debugging strategies",
                "Recommend different approaches to problem-solving",
                "Provide high-level guidance without specific code changes",
                "Identify when to escalate to different specialists"
            ],
            "tools": "ALL",  # UserProxy gets access to ALL tools
            "model": "qwen2.5:14b",
            "server": "ollama02.thiscluster.net",
            "collaboration_pattern": "sequential",
            "prompt_template": """You are a UserProxy AI specialist - you simulate an experienced developer providing guidance when the debugging system is stuck in a loop.

CRITICAL: You have access to ALL tools (read_file, execute_command, search_code, modify_python_file, etc.). USE THEM to investigate and provide informed guidance.

CONTEXT:
The debugging system has been attempting to fix an error but has entered a loop, trying the same approaches repeatedly without success.

YOUR ROLE:
- USE TOOLS to investigate the problem thoroughly
- Read the actual file to see the code context
- Execute commands to understand the environment
- Search the codebase for related code
- Analyze the debugging history to identify patterns
- Provide SPECIFIC, ACTIONABLE guidance based on your investigation
- NEVER suggest skipping or giving up - always find a way forward

AVAILABLE TOOLS:
- read_file: Read source files to understand context
- execute_command: Run commands to test theories
- search_code: Find related code in the codebase
- list_directory: Explore project structure
- modify_python_file: Suggest specific code changes
- And many more - use whatever tools you need!

DEBUGGING HISTORY:
{history}

CURRENT ERROR:
{error_info}

LOOP PATTERN DETECTED:
{loop_info}

YOUR TASK:
1. USE TOOLS to investigate the problem (read files, search code, etc.)
2. Identify the root cause based on your investigation
3. Provide SPECIFIC, ACTIONABLE guidance with concrete steps
4. NEVER suggest skipping - always provide a path forward

Consider:
1. Read the actual file - what does the code look like?
2. Search for similar patterns - how is this done elsewhere?
3. Check imports and dependencies - are they correct?
4. Look at related files - is there missing context?
5. Test your theories - run commands to verify

Provide clear, specific guidance with concrete actions the AI should take."""
        }
        
        # Register the role
        self.role_registry.register_role(role_spec)
        self._user_proxy_created = True
        self.logger.info("✓ UserProxy role created and registered")
        return True
    
    def get_guidance(self, 
                    error_info: Dict[str, Any],
                    loop_info: Dict[str, Any],
                    debugging_history: list,
                    context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get guidance from the UserProxy AI specialist.
        
        Args:
            error_info: Information about the current error
            loop_info: Information about the detected loop
            debugging_history: History of debugging attempts
            context: Additional context
            
        Returns:
            Dict with guidance and recommended actions
        """
        self.logger.info("\n" + "="*80)
        self.logger.info("🤖 AUTONOMOUS USER PROXY CONSULTATION")
        self.logger.info("="*80)
        self.logger.info("Loop detected - consulting AI specialist for guidance...")
        
        # Ensure the role exists
        if not self._ensure_user_proxy_role_exists():
            self.logger.error("Failed to create UserProxy role")
            return {
                "guidance": "Continue with current approach",
                "action": "continue",
                "reason": "UserProxy role creation failed"
            }
        
        # Format the history for the prompt
        history_text = self._format_history(debugging_history)
        
        # Format error info
        error_text = f"""
Error Type: {error_info.get('type', 'Unknown')}
Error Message: {error_info.get('message', 'Unknown')}
File: {error_info.get('file', 'Unknown')}
Line: {error_info.get('line', 'Unknown')}
"""
        
        # Format loop info
        loop_text = f"""
Loop Type: {loop_info.get('type', 'Unknown')}
Iterations: {loop_info.get('iterations', 0)}
Pattern: {loop_info.get('pattern', 'Unknown')}
"""
        
        # Create a conversation thread for the specialist
        from pipeline.conversation_thread import ConversationThread
        thread = ConversationThread(
            filepath=error_info.get('file', 'unknown'),
            error_type=error_info.get('type', 'Unknown'),
            error_message=error_info.get('message', 'Unknown'),
            line_number=error_info.get('line', 0)
        )
        
        # Add context to thread
        thread.add_message(
            role="system",
            content=f"DEBUGGING HISTORY:\n{history_text}\n\nCURRENT ERROR:\n{error_text}\n\nLOOP PATTERN:\n{loop_text}"
        )
        
        # Get ALL tools from tool registry
        from pipeline.tools import PIPELINE_TOOLS, TOOLS_DEBUGGING
        all_tools = PIPELINE_TOOLS + TOOLS_DEBUGGING
        
        # Use ToolAdvisor to help select best tools for this task
        task_desc = f"Analyze debugging loop and provide guidance. Error: {error_info.get('message', 'Unknown')}"
        suggested_tools = self.tool_advisor.suggest_tools(task_desc, all_tools)
        self.logger.info(f"ToolAdvisor suggested tools: {suggested_tools}")
        
        # Consult the specialist with ALL tools
        try:
            result = self.role_registry.consult_specialist(
                name="user_proxy",
                thread=thread,
                tools=all_tools  # Give UserProxy ALL tools
            )
            
            if result.get("success"):
                guidance = result.get("analysis", "")
                self.logger.info("\n📋 USER PROXY GUIDANCE:")
                self.logger.info("-" * 80)
                self.logger.info(guidance)
                self.logger.info("-" * 80)
                
                # Parse the guidance to determine action
                action = self._parse_guidance_action(guidance)
                
                return {
                    "guidance": guidance,
                    "action": action,
                    "success": True
                }
            else:
                self.logger.warning("UserProxy consultation failed")
                return {
                    "guidance": "Try a different approach - examine related files and dependencies",
                    "action": "continue",
                    "success": False
                }
                
        except Exception as e:
            self.logger.error(f"Error consulting UserProxy: {e}")
            return {
                "guidance": "Continue with alternative strategy",
                "action": "continue",
                "success": False,
                "error": str(e)
            }
    
    def _format_history(self, history: list) -> str:
        """Format debugging history for the prompt."""
        if not history:
            return "No previous attempts"
        
        formatted = []
        for i, attempt in enumerate(history[-5:], 1):  # Last 5 attempts
            formatted.append(f"\nAttempt {i}:")
            formatted.append(f"  Action: {attempt.get('action', 'Unknown')}")
            formatted.append(f"  Result: {attempt.get('result', 'Unknown')}")
            if 'error' in attempt:
                formatted.append(f"  Error: {attempt['error']}")
        
        return "\n".join(formatted)
    
    def _parse_guidance_action(self, guidance: str) -> str:
        """
        Parse the guidance to determine recommended action.
        
        Returns:
            'continue' - Continue with the guidance (ALWAYS - never skip)
            'escalate' - Escalate to different specialist
        
        NOTE: UserProxy NEVER skips bugs - always provides guidance
        """
        guidance_lower = guidance.lower()
        
        # Check for escalation indicators
        if any(word in guidance_lower for word in ['escalate', 'different specialist', 'consult', 'expert']):
            return 'escalate'
        
        # ALWAYS continue - never skip
        return 'continue'
    
    def create_custom_specialist(self, 
                                 problem_description: str,
                                 required_capabilities: list) -> Optional[str]:
        """
        Create a custom specialist for a specific problem.
        Uses RoleCreator to design the specialist dynamically.
        
        Args:
            problem_description: Description of the problem
            required_capabilities: List of required capabilities
            
        Returns:
            Name of the created specialist, or None if failed
        """
        self.logger.info(f"\n🎯 Creating custom specialist for: {problem_description}")
        
        # Use RoleCreator to design the specialist
        # This would integrate with the role_design phase
        # For now, return None to indicate not implemented
        self.logger.warning("Custom specialist creation not yet implemented")
        return None