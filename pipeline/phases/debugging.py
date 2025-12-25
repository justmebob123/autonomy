"""
Debugging Phase

Fixes code issues identified by QA.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus, FileStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_debug_prompt
from ..handlers import ToolCallHandler
from ..utils import validate_python_syntax
from ..conversation_thread import ConversationThread
from ..specialist_agents import SpecialistTeam
from ..failure_prompts import get_retry_prompt
from ..sudo_filter import filter_sudo_from_tool_calls
from ..action_tracker import ActionTracker
from ..pattern_detector import PatternDetector
from ..loop_intervention import LoopInterventionSystem
from ..team_orchestrator import TeamOrchestrator


class DebuggingPhase(BasePhase):
    """
    Debugging phase that fixes code issues.
    
    Responsibilities:
    - Get issues from QA
    - Apply fixes
    - Validate fixes
    - Update DEBUG_STATE.md
    """
    
    phase_name = "debug"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize specialist team
        self.specialist_team = SpecialistTeam(self.client, self.logger)
        # Directory for conversation threads
        self.threads_dir = self.project_dir / "conversation_threads"
        self.threads_dir.mkdir(exist_ok=True)
        
        # Initialize loop detection system
        logs_dir = self.project_dir / ".autonomous_logs"
        logs_dir.mkdir(exist_ok=True)
        self.action_tracker = ActionTracker(
            history_file=logs_dir / "action_history.jsonl"
        )
        self.pattern_detector = PatternDetector(self.action_tracker)
        self.loop_intervention = LoopInterventionSystem(
            self.action_tracker,
            self.pattern_detector,
            self.logger
        )
        
        # Initialize team orchestrator for parallel specialist execution
        self.team_orchestrator = TeamOrchestrator(
            self.client,
            self.specialist_team,
            self.logger,
            max_workers=4
        )
    
    def _track_tool_calls(self, tool_calls: List[Dict], results: List[Dict], agent: str = "main"):
        """Track tool calls for loop detection"""
        for tool_call, result in zip(tool_calls, results):
            tool_name = tool_call.get('tool', 'unknown')
            args = tool_call.get('args', {})
            
            # Extract file path if present
            file_path = None
            if 'file_path' in args:
                file_path = args['file_path']
            elif 'filepath' in args:
                file_path = args['filepath']
            
            # Track the action
            self.action_tracker.track_action(
                phase=self.phase_name,
                agent=agent,
                tool=tool_name,
                args=args,
                result=result,
                file_path=file_path,
                success=result.get('success', False)
            )
    
    def _check_for_loops(self) -> Optional[Dict]:
        """Check for loops and intervene if necessary"""
        intervention = self.loop_intervention.check_and_intervene()
        
        if intervention:
            # Log the intervention
            self.logger.warning("=" * 80)
            self.logger.warning("LOOP DETECTED - INTERVENTION REQUIRED")
            self.logger.warning("=" * 80)
            self.logger.warning(intervention['guidance'])
            self.logger.warning("=" * 80)
            
            # Return intervention for AI to see
            return intervention
        
        return None
    
    def execute(self, state: PipelineState,
                issue: Dict = None,
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute debugging for an issue"""
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is not None:
                task = task_from_state
            # If not found, keep the original (might be standalone debugging)
        
        # Find issue to fix
        if issue is None:
            issue = self._get_next_issue(state)
        
        if issue is None:
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No issues to fix"
            )
        
        filepath = issue.get("filepath")
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Issue has no filepath"
            )
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  Fixing: {filepath}")
        self.logger.info(f"  Issue: [{issue.get('type')}] {issue.get('description', '')[:50]}")
        
        # Read current content
        content = self.read_file(filepath)
        if not content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"File not found: {filepath}"
            )
        
        # Build messages
        user_prompt = get_debug_prompt(filepath, content, issue)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["debugging"]},
            {"role": "user", "content": user_prompt}
        ]
        
        # Log prompt in verbose mode
        if hasattr(self, 'config') and self.config.verbose:
            self.logger.info(f"  Prompt length: {len(user_prompt)} chars")
            self.logger.info(f"  Prompt preview: {user_prompt[:300]}...")
        
        # Get tools
        tools = get_tools_for_phase("debugging")
        self.logger.debug(f"  Available tools: {[t['function']['name'] for t in tools]}")
        
        # Send request
        response = self.chat(messages, tools, task_type="debugging")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Debug failed: {response['error']}"
            )
        
        # CRITICAL: Check for empty response
        message = response.get('message', {}) if response else {}
        content = message.get('content', '')
        if not response or not content:
            self.logger.error("  AI returned empty response - possible timeout or model issue")
            self.logger.error(f"  Response object: {response}")
            
            # Try with a different model if available
            self.logger.warning("  Attempting retry with alternative model...")
            
            # Force use of any available 14b model (excluding models that don't support tools)
            alternative_models = ["qwen2.5:14b", "qwen2.5-coder:14b", "llama3.1:70b"]
            for alt_model in alternative_models:
                for host, models in self.client.available_models.items():
                    for model in models:
                        if alt_model.lower() in model.lower():
                            self.logger.info(f"  Retrying with {model} on {host}")
                            # Retry with this model (increased timeout for CPU inference)
                            retry_response = self.client.chat(
                                host, model, messages, tools, 
                                temperature=0.3, timeout=7200
                            )
                            retry_message = retry_response.get('message', {}) if retry_response else {}
                            retry_content = retry_message.get('content', '')
                            if retry_response and retry_content:
                                response = retry_response
                                content = retry_content
                                self.logger.info("  Retry successful!")
                                break
                    if response and content:
                        break
                if response and content:
                    break
            
            # If still empty, return error
            if not response or not content:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message="AI returned empty response after retries - possible model timeout or availability issue"
                )
        
        # Parse response
        tool_calls, _ = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No fix applied")
            
            # ENHANCED LOGGING: Always log full response to understand why no tool calls
            content = response.get('content', '')
            
            # Log to console (truncated)
            if content:
                self.logger.warning(f"  AI responded but made no tool calls.")
                self.logger.warning(f"  Response preview: {content[:300]}...")
            else:
                self.logger.warning(f"  AI returned empty response")
            
            # Log full response to activity log for analysis
            if hasattr(self, 'config'):
                activity_log = self.project_dir / 'ai_activity.log'
                try:
                    with open(activity_log, 'a') as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"DEBUGGING PHASE - NO TOOL CALLS\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                        f.write(f"File: {filepath}\n")
                        f.write(f"Issue: {issue.get('type')} - {issue.get('message', '')[:100]}\n")
                        f.write(f"Model: {response.get('model', 'unknown')}\n")
                        f.write(f"\nFull AI Response:\n{content}\n")
                        f.write(f"{'='*80}\n")
                except Exception as e:
                    self.logger.debug(f"Could not write to activity log: {e}")
            
            # Analyze response to understand why no tool calls
            analysis = self._analyze_no_tool_call_response(content, issue)
            if analysis:
                self.logger.warning(f"  Analysis: {analysis}")
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"No fix was applied - AI did not make any tool calls. {analysis}",
                data={"ai_response": content[:500], "analysis": analysis}
            )
        
        # Execute tool calls
        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
        activity_log = self.project_dir / 'ai_activity.log'
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self._track_tool_calls(tool_calls, results, agent="main")
        
        # Check for loops
        intervention = self._check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            # Critical: Must escalate to user
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required: {intervention['guidance'][:200]}",
                data={'intervention': intervention}
            )
        
        # Show activity summary
        self.logger.info(handler.get_activity_summary())
        
        if not handler.files_modified:
            # Check for errors
            for result in results:
                if not result.get("success"):
                    error = result.get("error", "Unknown error")
                    self.logger.warning(f"  Fix failed: {error}")
                    
                    # ENHANCED: Check if we have AI feedback from failure analysis
                    ai_feedback = result.get("ai_feedback")
                    failure_report = result.get("failure_report")
                    
                    if ai_feedback:
                        self.logger.info(f"  📋 Detailed failure analysis available")
                        if failure_report:
                            self.logger.info(f"  📄 Report: {failure_report}")
                        
                        # If we have AI feedback, we should retry with this information
                        # For now, include it in the error data
                        return PhaseResult(
                            success=False,
                            phase=self.phase_name,
                            message=f"Fix failed: {error}",
                            errors=[{
                                "type": "fix_failed", 
                                "message": error,
                                "ai_feedback": ai_feedback,
                                "failure_report": failure_report
                            }],
                            data={
                                "should_retry": True,
                                "ai_feedback": ai_feedback,
                                "failure_analysis": result.get("failure_analysis")
                            }
                        )
                    
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Fix failed: {error}",
                        errors=[{"type": "fix_failed", "message": error}]
                    )
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No modifications made"
            )
        
        # Success - update state
        self.logger.info(f"  ✓ Fixed: {filepath}")
        
        # Update file hash
        for modified_file in handler.files_modified:
            file_hash = self.file_tracker.update_hash(modified_file)
            full_path = self.project_dir / modified_file
            if full_path.exists():
                state.update_file(modified_file, file_hash, full_path.stat().st_size)
        
        # Update task if provided
        if task:
            task.status = TaskStatus.DEBUG_PENDING
            task.priority = TaskPriority.DEBUG_PENDING
        
        # Mark file for re-review
        if filepath in state.files:
            state.files[filepath].qa_status = FileStatus.PENDING
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Fixed issue in {filepath}",
            files_modified=handler.files_modified,
            data={"issue": issue, "filepath": filepath}
        )
    
    def retry_with_feedback(self, state: PipelineState, 
                           issue: Dict,
                           ai_feedback: str,
                           previous_attempt: Dict = None) -> PhaseResult:
        """
        Retry fixing an issue with detailed failure feedback.
        
        This method provides the AI with comprehensive information about
        why the previous attempt failed.
        """
        
        filepath = issue.get("filepath")
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Issue has no filepath"
            )
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  🔄 Retrying fix with failure analysis: {filepath}")
        
        # Read current content
        content = self.read_file(filepath)
        if not content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"File not found: {filepath}"
            )
        
        # Build enhanced prompt with failure feedback
        retry_prompt = f"""# RETRY: Fix with Failure Analysis

You previously attempted to fix this issue but the modification failed.
Here is detailed analysis of what went wrong and how to fix it.

{ai_feedback}

## Current Task
Fix the following issue in `{filepath}`:

**Issue Type:** {issue.get('type')}
**Description:** {issue.get('description', '')}
**Line:** {issue.get('line', 'N/A')}

## Current File Content
```python
{content}
```

## Instructions
1. READ the failure analysis carefully
2. UNDERSTAND why the previous attempt failed
3. FOLLOW the suggestions provided
4. Use the correct tool calls to fix the issue
5. VERIFY your code before applying changes

Remember:
- Copy EXACT code from the file, including all whitespace
- Use larger code blocks with context if needed
- Test your replacement code for syntax errors
- Match the indentation of surrounding code
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["debugging"]},
            {"role": "user", "content": retry_prompt}
        ]
        
        # Get tools
        tools = get_tools_for_phase("debugging")
        
        # Send request
        response = self.chat(messages, tools, task_type="debugging")
        
        if "error" in response:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Retry failed: {response['error']}"
            )
        
        # Parse response
        tool_calls, _ = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No fix applied in retry attempt")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Retry: No modifications made"
            )
        
        # Execute tool calls
        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
        activity_log = self.project_dir / 'ai_activity.log'
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self._track_tool_calls(tool_calls, results, agent="retry")
        
        # Check for loops
        intervention = self._check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            # Critical: Must escalate to user
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected during retry - user intervention required",
                data={'intervention': intervention}
            )
        
        # Show activity summary
        self.logger.info(handler.get_activity_summary())
        
        if not handler.files_modified:
            # Check for errors
            for result in results:
                if not result.get("success"):
                    error = result.get("error", "Unknown error")
                    self.logger.warning(f"  Retry failed: {error}")
                    
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Retry failed: {error}",
                        errors=[{"type": "retry_failed", "message": error}]
                    )
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Retry: No modifications made"
            )
        
        # Success
        self.logger.info(f"  ✅ Retry successful: {filepath}")
        
        # Update file hash
        for modified_file in handler.files_modified:
            file_hash = self.file_tracker.update_hash(modified_file)
            full_path = self.project_dir / modified_file
            if full_path.exists():
                state.update_file(modified_file, file_hash, full_path.stat().st_size)
        
        # Mark file for re-review
        if filepath in state.files:
            state.files[filepath].qa_status = FileStatus.PENDING
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Retry successful: Fixed issue in {filepath}",
            files_modified=handler.files_modified,
            data={"issue": issue, "filepath": filepath, "retry": True}
        )
    
    def execute_with_conversation_thread(self, state: PipelineState,
                                        issue: Dict,
                                        task: TaskState = None,
                                        max_attempts: int = 5) -> PhaseResult:
        """
        Execute debugging with persistent conversation thread and specialist consultation.
        
        This method:
        1. Creates a conversation thread for the issue
        2. Attempts fixes with full context
        3. Consults specialists when needed
        4. Maintains conversation history across attempts
        5. Filters sudo commands
        6. Saves complete thread for analysis
        """
        
        # Create conversation thread
        thread = ConversationThread(issue, self.project_dir)
        self.logger.info(f"  💬 Started conversation thread: {thread.thread_id}")
        
        # Get tools
        tools = get_tools_for_phase("debugging")
        
        # Track overall success
        overall_success = False
        
        # Attempt loop
        while thread.should_continue(max_attempts):
            attempt_num = thread.current_attempt + 1
            self.logger.info(f"\n  🔄 Attempt #{attempt_num}")
            
            # Build prompt with full conversation context
            if attempt_num == 1:
                # First attempt - use standard debug prompt
                filepath = issue.get("filepath")
                content = self.read_file(filepath)
                user_prompt = get_debug_prompt(filepath, content, issue)
            else:
                # Subsequent attempts - use retry prompt with failure analysis
                last_attempt = thread.attempts[-1]
                
                # CRITICAL FIX: Always read the CURRENT file state, not stale snapshots
                # After rollback, the file is back to its original state
                filepath = issue.get('filepath')
                current_content = self.read_file(filepath)
                
                context = {
                    'filepath': filepath,
                    'intended_original': last_attempt.original_code,
                    'replacement_code': last_attempt.replacement_code,
                    'file_content': current_content,  # Use CURRENT file content, not snapshot
                    'attempt_summary': thread.get_attempt_summary(),
                    'error_message': last_attempt.error_message,
                    'failure_type': last_attempt.analysis.get('failure_type') if last_attempt.analysis else 'UNKNOWN'
                }
                
                user_prompt = get_retry_prompt(context, last_attempt.analysis or {})
            
            # Add to conversation
            thread.add_message(role="user", content=user_prompt)
            
            # Get conversation history for LLM
            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS["debugging"]}
            ] + thread.get_conversation_history()
            
            # Send request
            self.logger.info(f"  🤖 Requesting fix from AI...")
            response = self.chat(messages, tools, task_type="debugging")
            
            if "error" in response:
                thread.add_message(
                    role="assistant",
                    content=f"Error: {response['error']}",
                    metadata={"error": True}
                )
                break
            
            # Parse response
            tool_calls, text_response = self.parser.parse_response(response)
            
            # Add AI response to thread
            thread.add_message(
                role="assistant",
                content=text_response,
                tool_calls=tool_calls
            )
            
            # Filter sudo commands
            if tool_calls:
                allowed_calls, blocked_calls, sudo_summary = filter_sudo_from_tool_calls(tool_calls)
                
                if blocked_calls:
                    self.logger.warning(f"  ⚠️  Blocked {len(blocked_calls)} sudo command(s)")
                    # Add sudo block message to thread
                    thread.add_message(
                        role="system",
                        content=sudo_summary,
                        metadata={"sudo_blocked": True}
                    )
                
                tool_calls = allowed_calls
            
            if not tool_calls:
                self.logger.warning("  ⚠️  No tool calls made")
                
                # Consult specialist for guidance
                self.logger.info("  🔬 Consulting specialists for guidance...")
                failure_type = thread.attempts[-1].analysis.get('failure_type') if thread.attempts else 'UNKNOWN'
                specialist_name = self.specialist_team.get_best_specialist_for_failure(failure_type)
                
                specialist_analysis = self.specialist_team.consult_specialist(
                    specialist_name,
                    thread,
                    tools
                )
                
                # Execute specialist's tool calls if any
                if specialist_analysis.get('tool_calls'):
                    self.logger.info(f"  🔧 Executing {len(specialist_analysis['tool_calls'])} tool calls from specialist...")
                    verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
                    activity_log = self.project_dir / 'ai_activity.log'
                    handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
                    specialist_results = handler.process_tool_calls(specialist_analysis['tool_calls'])
                    
                    # Add results to thread
                    thread.add_message(
                        role="system",
                        content=f"Specialist tool results: {len(specialist_results)} calls executed",
                        tool_results=specialist_results
                    )
                
                continue
            
            # Execute tool calls
            self.logger.info(f"  🔧 Executing {len(tool_calls)} tool call(s)...")
            verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
            activity_log = self.project_dir / 'ai_activity.log'
            handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))
            results = handler.process_tool_calls(tool_calls)
            
            # Track actions for loop detection
            self._track_tool_calls(tool_calls, results, agent="conversation")
            
            # Check for loops
            intervention = self._check_for_loops()
            if intervention:
                # Add intervention guidance to thread
                thread.add_message(
                    role="system",
                    content=f"⚠️ LOOP DETECTED\n\n{intervention['guidance']}"
                )
                
                if intervention.get('requires_user_input'):
                    # Critical: Must escalate to user
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Loop detected - user intervention required",
                        data={'intervention': intervention, 'thread': thread}
                    )
            
            # Add results to thread
            thread.add_message(
                role="system",
                content="Tool execution results",
                tool_results=results
            )
            
            # Check if modification was successful
            success = False
            error_message = None
            failure_analysis = None
            
            for result in results:
                if result.get('tool') == 'modify_file':
                    if result.get('success'):
                        success = True
                        self.logger.info("  ✅ Modification successful!")
                    else:
                        error_message = result.get('error', 'Unknown error')
                        failure_analysis = result.get('failure_analysis')
                        self.logger.warning(f"  ❌ Modification failed: {error_message}")
            
            # Record attempt
            original_code = ""
            replacement_code = ""
            for call in tool_calls:
                if call.get('function', {}).get('name') == 'modify_file':
                    args = call.get('function', {}).get('arguments', {})
                    original_code = args.get('original_code', args.get('original', ''))
                    replacement_code = args.get('new_code', args.get('replacement', ''))
                    break
            
            thread.record_attempt(
                agent_name="Primary Debugger",
                original_code=original_code,
                replacement_code=replacement_code,
                success=success,
                error_message=error_message,
                tool_calls=tool_calls,
                tool_results=results,
                analysis=failure_analysis
            )
            
            
            # ARCHITECTURAL CHANGE: Check if AI decision is needed
            needs_decision = False
            decision_context = None
            
            for result in results:
                if result.get('tool') == 'modify_file' and result.get('needs_ai_decision'):
                    needs_decision = True
                    decision_context = {
                        'filepath': result.get('filepath'),
                        'verification_issues': result.get('verification_issues', []),
                        'modified_content': result.get('modified_content', ''),
                        'original_content': result.get('original_content', ''),
                        'failure_analysis': result.get('failure_analysis', {}),
                        'patch': result.get('patch'),
                        'rollback_available': result.get('rollback_available', False)
                    }
                    break
            
            # If AI decision is needed, ask the AI what to do
            if needs_decision:
                self.logger.info("  🤔 AI decision required - asking AI to evaluate the change...")
                
                from ..prompts import get_modification_decision_prompt
                decision_prompt = get_modification_decision_prompt(decision_context)
                
                # Ask AI for decision
                decision_messages = [
                    {"role": "system", "content": SYSTEM_PROMPTS["debugging"]},
                    {"role": "user", "content": decision_prompt}
                ]
                
                decision_response = self.chat(decision_messages, tools, task_type="debugging")
                
                if "error" not in decision_response:
                    decision_text = decision_response.get('message', {}).get('content', '')
                    self.logger.info(f"  💭 AI Decision: {decision_text[:200]}...")
                    
                    # Parse decision
                    if "DECISION: ACCEPT" in decision_text.upper():
                        self.logger.info("  ✅ AI decided to ACCEPT the change")
                        success = True
                        overall_success = True
                        
                    elif "DECISION: REFINE" in decision_text.upper():
                        self.logger.info("  🔧 AI decided to REFINE the change")
                        # Parse any tool calls from the refinement
                        refine_calls, _ = self.parser.parse_response(decision_response)
                        if refine_calls:
                            self.logger.info(f"  🔧 Executing {len(refine_calls)} refinement tool calls...")
                            refine_results = handler.process_tool_calls(refine_calls)
                            # Check if refinement succeeded
                            for r in refine_results:
                                if r.get('success') and not r.get('needs_ai_decision'):
                                    success = True
                                    overall_success = True
                        
                    elif "DECISION: ROLLBACK" in decision_text.upper():
                        self.logger.info("  🔄 AI decided to ROLLBACK the change")
                        # Perform rollback
                        if decision_context.get('rollback_available') and decision_context.get('patch'):
                            try:
                                filepath = decision_context['filepath']
                                full_path = self.project_dir / filepath
                                full_path.write_text(decision_context['original_content'])
                                self.logger.info("  ✅ Rollback completed")
                            except Exception as e:
                                self.logger.error(f"  ❌ Rollback failed: {e}")
                    else:
                        self.logger.warning("  ⚠️  Could not parse AI decision, treating as failure")
                else:
                    self.logger.error(f"  ❌ Error getting AI decision: {decision_response.get('error')}")
            
            if success:
                overall_success = True
                break
            
            # If failed, consult specialists
            if failure_analysis and attempt_num < max_attempts:
                self.logger.info("  🔬 Consulting specialist team...")
                
                # Get best specialist for this failure type
                failure_type = failure_analysis.get('failure_type', 'UNKNOWN')
                specialist_name = self.specialist_team.get_best_specialist_for_failure(failure_type)
                
                specialist_analysis = self.specialist_team.consult_specialist(
                    specialist_name,
                    thread,
                    tools
                )
                
                # Execute specialist's tool calls
                if specialist_analysis.get('tool_calls'):
                    self.logger.info(f"  🔧 Executing {len(specialist_analysis['tool_calls'])} specialist tool calls...")
                    specialist_results = handler.process_tool_calls(specialist_analysis['tool_calls'])
                    
                    # Add to thread
                    thread.add_message(
                        role="system",
                        content=f"Specialist analysis complete",
                        tool_results=specialist_results
                    )
        
        # Save conversation thread
        thread_file = thread.save_thread(self.threads_dir)
        self.logger.info(f"  💾 Conversation thread saved: {thread_file.name}")
        
        # Update state if successful
        if overall_success:
            filepath = issue.get("filepath")
            
            # Update file hash
            for modified_file in handler.files_modified:
                file_hash = self.file_tracker.update_hash(modified_file)
                full_path = self.project_dir / modified_file
                if full_path.exists():
                    state.update_file(modified_file, file_hash, full_path.stat().st_size)
            
            # Update task if provided
            if task:
                task.status = TaskStatus.DEBUG_PENDING
                task.priority = TaskPriority.DEBUG_PENDING
            
            # Mark file for re-review
            if filepath in state.files:
                state.files[filepath].qa_status = FileStatus.PENDING
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Fixed issue in {filepath} after {thread.current_attempt} attempt(s)",
                files_modified=handler.files_modified,
                data={
                    "issue": issue,
                    "filepath": filepath,
                    "attempts": thread.current_attempt,
                    "thread_id": thread.thread_id,
                    "specialists_consulted": thread.specialists_consulted
                }
            )
        else:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Failed to fix issue after {thread.current_attempt} attempt(s)",
                data={
                    "issue": issue,
                    "attempts": thread.current_attempt,
                    "thread_id": thread.thread_id,
                    "specialists_consulted": thread.specialists_consulted,
                    "thread_file": str(thread_file)
                }
            )
    
    def fix_all_issues(self, state: PipelineState, 
                       max_fixes: int = 10) -> PhaseResult:
        """Attempt to fix all pending issues"""
        fixed = 0
        failed = 0
        all_errors = []
        
        for _ in range(max_fixes):
            issue = self._get_next_issue(state)
            if not issue:
                break
            
            result = self.execute(state, issue=issue)
            
            if result.success:
                fixed += 1
            else:
                failed += 1
                all_errors.extend(result.errors)
        
        return PhaseResult(
            success=failed == 0,
            phase=self.phase_name,
            message=f"Fixed {fixed} issues, {failed} failed",
            errors=all_errors,
            data={"fixed": fixed, "failed": failed}
        )
    
    def _analyze_no_tool_call_response(self, content: str, issue: Dict) -> str:
        """
        Analyze AI response to understand why no tool calls were made.
        
        Returns a brief analysis string.
        """
        if not content:
            return "AI returned empty response"
        
        content_lower = content.lower()
        
        # Check for common patterns
        if "cannot" in content_lower or "can't" in content_lower or "unable" in content_lower:
            return "AI believes it cannot fix this issue"
        
        if "need more" in content_lower or "require" in content_lower or "missing" in content_lower:
            return "AI needs more information or context"
        
        if "not sure" in content_lower or "unclear" in content_lower or "don't know" in content_lower:
            return "AI is uncertain about the fix"
        
        if "explanation" in content_lower or "because" in content_lower or "reason" in content_lower:
            return "AI provided explanation instead of fix"
        
        if "tool" in content_lower or "function" in content_lower or "call" in content_lower:
            return "AI mentioned tools but didn't call them"
        
        if len(content) > 1000:
            return "AI provided lengthy response without action"
        
        return "AI responded but reason for no tool calls unclear"
    
    def _get_next_issue(self, state: PipelineState) -> Optional[Dict]:
        """Get the next issue to fix"""
        # Check rejected files
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.REJECTED and file_state.issues:
                return file_state.issues[0]
        
        # Check task errors
        for task in state.tasks.values():
            if task.status == TaskStatus.QA_FAILED and task.errors:
                last_error = task.errors[-1]
                return {
                    "filepath": task.target_file,
                    "type": last_error.error_type,
                    "description": last_error.message,
                    "line": last_error.line_number,
                }
        
        return None
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate DEBUG_STATE.md content"""
        lines = [
            "# Debug State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Active Issues",
            "",
        ]
        
        # Collect all issues
        issues = []
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.REJECTED:
                for issue in file_state.issues:
                    issues.append({
                        "filepath": file_state.filepath,
                        **issue
                    })
        
        if issues:
            lines.append("| File | Type | Description |")
            lines.append("|------|------|-------------|")
            for issue in issues:
                lines.append(
                    f"| `{issue['filepath']}` | {issue.get('type', '?')} | "
                    f"{issue.get('description', '')[:50]} |"
                )
            lines.append("")
        else:
            lines.append("(no active issues)")
            lines.append("")
        
        # Fix history from tasks
        lines.append("## Recent Fix Attempts")
        lines.append("")
        
        fix_history = []
        for task in state.tasks.values():
            for error in task.errors:
                if error.phase == "debug":
                    fix_history.append((task, error))
        
        if fix_history:
            # Sort by timestamp
            fix_history.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            for task, error in fix_history[:10]:
                lines.append(f"### {task.target_file}")
                lines.append(f"- **Issue:** {error.error_type}")
                lines.append(f"- **Time:** {self.format_timestamp(error.timestamp)}")
                lines.append(f"- **Message:** {error.message}")
                lines.append("")
        else:
            lines.append("(no fix attempts yet)")
            lines.append("")
        
        # Error patterns
        lines.append("## Error Patterns")
        lines.append("")
        
        patterns: Dict[str, int] = {}
        for task in state.tasks.values():
            for error in task.errors:
                patterns[error.error_type] = patterns.get(error.error_type, 0) + 1
        
        if patterns:
            lines.append("| Error Type | Count |")
            lines.append("|------------|-------|")
            for error_type, count in sorted(patterns.items(), key=lambda x: -x[1]):
                lines.append(f"| {error_type} | {count} |")
            lines.append("")
            
            # Recommendations
            lines.append("## Recommendations for Coding Phase")
            lines.append("")
            if patterns.get("SyntaxError", 0) > 2:
                lines.append("- ⚠ Multiple syntax errors detected. Ensure proper indentation.")
            if patterns.get("missing_import", 0) > 0:
                lines.append("- ⚠ Missing imports detected. Include all required imports at top of file.")
            if patterns.get("type_error", 0) > 0:
                lines.append("- ⚠ Type errors detected. Verify type hints match actual types.")
        else:
            lines.append("(no error patterns detected)")
        
        lines.append("")
        
        # Session stats
        lines.append("## Session Stats")
        lines.append("")
        lines.append(f"- Total Runs: {state.phases['debug'].runs}")
        lines.append(f"- Successful Fixes: {state.phases['debug'].successes}")
        lines.append(f"- Failed Fixes: {state.phases['debug'].failures}")
        lines.append("")
        
        return "\n".join(lines)
