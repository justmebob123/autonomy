"""
Orchestrated Pipeline

The main pipeline that uses the arbiter and specialists to execute tasks.
This replaces the traditional phase-based pipeline with an intelligent,
model-driven orchestration system.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..logging_setup import get_logger
from ..state.manager import StateManager, PipelineState, TaskStatus
from ..handlers import ToolCallHandler

from .arbiter import ArbiterModel
from .model_tool import get_specialist_registry
from .conversation_manager import MultiModelConversationManager


class OrchestratedPipeline:
    """
    Pipeline orchestrated by the arbiter model.
    
    Instead of hardcoded phase logic, the arbiter decides:
    - Which specialists to consult
    - When to change phases
    - How to handle failures
    - When to request user input
    
    The application provides capabilities (tools), models make decisions.
    """
    
    def __init__(self, project_dir: Path, config: Optional[Dict] = None):
        """
        Initialize the orchestrated pipeline.
        
        Args:
            project_dir: Project directory
            config: Configuration dict
        """
        self.project_dir = project_dir
        self.config = config or {}
        self.logger = get_logger()
        
        # Initialize components
        self.state_manager = StateManager(project_dir)
        self.arbiter = ArbiterModel(project_dir)
        self.specialists = get_specialist_registry()
        self.tool_handler = ToolCallHandler(project_dir)
        
        # Execution state
        self.iteration = 0
        self.max_iterations = self.config.get("max_iterations", 100)
        self.running = False
        
        self.logger.info("=" * 70)
        self.logger.info("  ORCHESTRATED PIPELINE - Model-Driven Architecture")
        self.logger.info("=" * 70)
        self.logger.info(f"  Project: {project_dir}")
        self.logger.info(f"  Arbiter: {self.arbiter.model}")
        self.logger.info(f"  Specialists: {len(self.specialists.get_all())}")
        self.logger.info("=" * 70)
    
    def run(self):
        """
        Main execution loop.
        
        The arbiter drives the workflow, consulting specialists as needed.
        """
        self.running = True
        self.iteration = 0
        
        # Load state
        state = self.state_manager.load()
        
        self.logger.info("\n🚀 Starting orchestrated pipeline...\n")
        
        try:
            while self.running and self.iteration < self.max_iterations:
                self.iteration += 1
                
                self.logger.info("=" * 70)
                self.logger.info(f"  ITERATION {self.iteration}")
                self.logger.info("=" * 70)
                
                # Get context
                context = self._build_context(state)
                
                # Arbiter decides what to do
                decision = self.arbiter.decide_action(state, context)
                
                # Execute decision
                result = self._execute_decision(decision, state)
                
                # Update state
                state = self.state_manager.load()
                
                # Check if complete
                if self._is_complete(state, result):
                    self.logger.info("\n✓ Pipeline complete!")
                    break
                
                # Check for user input request
                if decision["action"] == "request_user_input":
                    self.logger.info("\n⏸️  Waiting for user input...")
                    break
            
            if self.iteration >= self.max_iterations:
                self.logger.warning(f"\n⚠️  Reached max iterations ({self.max_iterations})")
        
        except KeyboardInterrupt:
            self.logger.info("\n⏸️  Pipeline interrupted by user")
        
        except Exception as e:
            self.logger.error(f"\n✗ Pipeline error: {e}", exc_info=True)
        
        finally:
            self.running = False
            self._show_final_stats()
    
    def _build_context(self, state: PipelineState) -> Dict[str, Any]:
        """
        Build context for arbiter decision-making.
        
        Args:
            state: Current state
        
        Returns:
            Context dict
        """
        # Get pending tasks
        pending_tasks = [
            t for t in state.tasks.values()
            if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
        ]
        
        # Get failed tasks
        failed_tasks = [
            t for t in state.tasks.values()
            if t.status in [TaskStatus.QA_FAILED, TaskStatus.NEEDS_FIXES]
        ]
        
        # Get recent errors
        recent_errors = []
        for task in state.tasks.values():
            if task.errors:
                recent_errors.extend(task.errors[-2:])
        
        return {
            "current_phase": state.current_phase,
            "total_tasks": len(state.tasks),
            "pending_tasks": len(pending_tasks),
            "failed_tasks": len(failed_tasks),
            "recent_errors": recent_errors[:5],  # Last 5 errors
            "iteration": self.iteration,
            "needs_planning": state.needs_planning,
            "needs_documentation": state.needs_documentation_update
        }
    
    def _execute_decision(self, decision: Dict[str, Any], 
                         state: PipelineState) -> Dict[str, Any]:
        """
        Execute the arbiter's decision.
        
        Args:
            decision: Decision dict from arbiter
            state: Current state
        
        Returns:
            Execution result
        """
        action = decision["action"]
        
        self.logger.info(f"\n📋 Executing: {action}")
        
        if action == "consult_specialist":
            return self._consult_specialist(decision, state)
        
        elif action == "change_phase":
            return self._change_phase(decision, state)
        
        elif action == "request_user_input":
            return self._request_user_input(decision)
        
        elif action == "continue_current_phase":
            return self._continue_current_phase(decision, state)
        
        else:
            self.logger.warning(f"Unknown action: {action}")
            return {"success": False, "error": f"Unknown action: {action}"}
    
    def _consult_specialist(self, decision: Dict[str, Any], 
                           state: PipelineState) -> Dict[str, Any]:
        """
        Consult a specialist model.
        
        Args:
            decision: Decision dict
            state: Current state
        
        Returns:
            Consultation result
        """
        specialist_name = decision["specialist"]
        query = decision["query"]
        context = decision.get("context", {})
        
        # Add state to context
        context["state"] = {
            "phase": state.current_phase,
            "tasks": len(state.tasks)
        }
        
        # Consult specialist
        result = self.arbiter.consult_specialist(specialist_name, query, context)
        
        if not result.get("success"):
            self.logger.error(f"  ✗ Specialist consultation failed")
            return result
        
        # Process tool calls from specialist
        tool_calls = result.get("tool_calls", [])
        
        if tool_calls:
            self.logger.info(f"  Processing {len(tool_calls)} tool call(s)...")
            tool_results = self.tool_handler.process_tool_calls(tool_calls)
            result["tool_results"] = tool_results
            
            # Update state based on tool results
            self._update_state_from_tools(tool_results, state)
        
        return result
    
    def _change_phase(self, decision: Dict[str, Any], 
                     state: PipelineState) -> Dict[str, Any]:
        """
        Change pipeline phase.
        
        Args:
            decision: Decision dict
            state: Current state
        
        Returns:
            Change result
        """
        new_phase = decision["phase"]
        reason = decision["reason"]
        
        self.logger.info(f"  Changing phase: {state.current_phase} → {new_phase}")
        self.logger.info(f"  Reason: {reason}")
        
        # Update state
        state.current_phase = new_phase
        self.state_manager.save(state)
        
        return {
            "success": True,
            "old_phase": state.current_phase,
            "new_phase": new_phase,
            "reason": reason
        }
    
    def _request_user_input(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request user input.
        
        Args:
            decision: Decision dict
        
        Returns:
            Request result
        """
        question = decision["question"]
        context = decision.get("context", "")
        
        self.logger.info(f"\n❓ User input requested:")
        self.logger.info(f"  {question}")
        if context:
            self.logger.info(f"  Context: {context}")
        
        # Stop execution - user needs to respond
        self.running = False
        
        return {
            "success": True,
            "action": "user_input_requested",
            "question": question,
            "context": context
        }
    
    def _continue_current_phase(self, decision: Dict[str, Any], 
                               state: PipelineState) -> Dict[str, Any]:
        """
        Continue with current phase.
        
        Args:
            decision: Decision dict
            state: Current state
        
        Returns:
            Continue result
        """
        reason = decision.get("reason", "No specific action needed")
        
        self.logger.info(f"  Continuing with {state.current_phase}")
        self.logger.info(f"  Reason: {reason}")
        
        return {
            "success": True,
            "action": "continue",
            "phase": state.current_phase,
            "reason": reason
        }
    
    def _update_state_from_tools(self, tool_results: List[Dict], 
                                 state: PipelineState):
        """
        Update state based on tool execution results.
        
        Args:
            tool_results: List of tool result dicts
            state: Current state
        """
        for result in tool_results:
            tool_name = result.get("tool", "")
            success = result.get("success", False)
            
            if not success:
                continue
            
            # Handle file creation
            if tool_name in ["create_python_file", "create_file"]:
                filepath = result.get("filepath", "")
                if filepath:
                    # Mark file as created
                    state.mark_file_created(filepath)
            
            # Handle task completion
            elif tool_name == "approve_code":
                filepath = result.get("filepath", "")
                if filepath:
                    # Mark file as approved
                    state.mark_file_reviewed(filepath, approved=True)
        
        # Save state
        self.state_manager.save(state)
    
    def _is_complete(self, state: PipelineState, result: Dict[str, Any]) -> bool:
        """
        Check if pipeline is complete.
        
        Args:
            state: Current state
            result: Last execution result
        
        Returns:
            True if complete
        """
        # Check if all tasks are done
        incomplete_tasks = [
            t for t in state.tasks.values()
            if t.status not in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
        ]
        
        if not incomplete_tasks:
            return True
        
        return False
    
    def _show_final_stats(self):
        """Show final statistics."""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("  FINAL STATISTICS")
        self.logger.info("=" * 70)
        
        # Arbiter stats
        arbiter_stats = self.arbiter.get_stats()
        self.logger.info(f"\n📊 Arbiter Decisions: {arbiter_stats['total_decisions']}")
        for action, count in arbiter_stats['action_counts'].items():
            self.logger.info(f"  - {action}: {count}")
        
        # Specialist stats
        self.logger.info(f"\n🔧 Specialist Usage:")
        for name, stats in arbiter_stats['specialist_stats'].items():
            success_rate = stats['success_rate'] * 100
            self.logger.info(f"  - {name}: {stats['call_count']} calls ({success_rate:.1f}% success)")
        
        self.logger.info("\n" + "=" * 70)


def create_orchestrated_pipeline(project_dir: Path, 
                                config: Optional[Dict] = None) -> OrchestratedPipeline:
    """
    Create an orchestrated pipeline instance.
    
    Args:
        project_dir: Project directory
        config: Configuration dict
    
    Returns:
        OrchestratedPipeline instance
    """
    return OrchestratedPipeline(project_dir, config)