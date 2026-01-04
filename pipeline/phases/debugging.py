"""
Debugging Phase

Fixes code issues identified by QA.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
import re
import time



from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus, FileStatus
from ..handlers import ToolCallHandler
from ..phase_resources import get_phase_tools, get_debugging_prompt, get_modification_decision
from ..conversation_thread import DebuggingConversationThread
from .loop_detection_mixin import LoopDetectionMixin
from ..team_coordination import TeamCoordinationFacade
from ..tools import get_tools_for_phase
from ..debugging_utils import (
    get_timestamp_iso,
    is_same_error,
    assess_error_complexity,
    analyze_no_tool_call_response,
    get_next_issue,
    get_error_strategy,
    enhance_prompt_with_error_strategy,
    get_failure_retry_prompt,
    filter_sudo_commands,
    safe_json_dumps,
    safe_json_loads,
    sleep_with_backoff,
    get_current_timestamp,
    TaskPriority
)
from ..user_proxy import UserProxyAgent


class DebuggingPhase(LoopDetectionMixin, BasePhase):
    """
    Debugging phase that fixes code issues.
    
    Responsibilities:
    - Get issues from QA
    - Apply fixes
    - Validate fixes
    - Update DEBUG_STATE.md
    """
    
    phase_name = "debugging"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Directory for conversation threads
        self.threads_dir = self.project_dir / "conversation_threads"
        self.threads_dir.mkdir(exist_ok=True)
        
        # CRITICAL FIX: Initialize loop detection from LoopDetectionMixin
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.call_graph import CallGraphGenerator
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_conflicts import IntegrationConflictDetector
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.call_graph = CallGraphGenerator(str(self.project_dir), self.logger)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.conflict_detector = IntegrationConflictDetector(str(self.project_dir), self.logger)
        
        self.logger.info("  🔧 Debugging phase initialized with ALL analysis capabilities")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.ISSUE_FOUND,
                MessageType.TASK_FAILED,
                MessageType.PHASE_ERROR,
                MessageType.SYSTEM_ALERT,
            ])
        
        # Initialize team coordination system
        self.team_coordination = TeamCoordinationFacade(
            self.client,
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
    
    def _verify_fix_with_runtime_test(self, filepath: str, original_error: Dict, tester) -> Dict:
        """
        CRITICAL FIX #2: RUNTIME VERIFICATION
        Verify fix by re-running the program and checking if error is gone.
        
        Args:
            filepath: File that was modified
            original_error: The original error we're trying to fix
            tester: RuntimeTester instance
            
        Returns:
            dict: {
                'success': bool,
                'error_fixed': bool,
                'new_errors': list,
                'same_error_persists': bool
            }
        """
                
        self.logger.info("🧪 RUNTIME VERIFICATION: Re-running program to verify fix...")
        
        # Stop current test
        if tester and tester.is_running():
            tester.stop()
            sleep_with_backoff(0, 2)
        
        # Clear log file
        if tester and tester.log_file and tester.log_file.exists():
            tester.log_file.write_text('')
            self.logger.info(f"   Cleared log file: {tester.log_file}")
        
        # Restart test
        if tester:
            tester.start()
            self.logger.info("   Program restarted, waiting 5 seconds...")
            sleep_with_backoff(0, 5)  # Give it time to hit the error
            
            # Check for errors
            new_errors = tester.get_errors()
            
            # Check if SAME error persists
            same_error_persists = False
            for error in new_errors:
                if is_same_error(error, original_error):
                    same_error_persists = True
                    self.logger.warning(f"   ❌ Same error persists: {error.get('type')}")
                    break
            
            # Stop test
            tester.stop()
            
            # ENHANCED: Detect cascading errors (new errors introduced by the fix)
            cascading_errors = []
            if not same_error_persists and new_errors:
                # Original error is gone, but new errors appeared
                for error in new_errors:
                    if not is_same_error(error, original_error):
                        cascading_errors.append(error)
            
            result = {
                'success': not same_error_persists and not cascading_errors,
                'error_fixed': not same_error_persists,
                'new_errors': new_errors,
                'same_error_persists': same_error_persists,
                'cascading_errors': cascading_errors,
                'has_cascading_errors': len(cascading_errors) > 0
            }
            
            if same_error_persists:
                self.logger.warning("❌ Runtime verification FAILED: Same error persists")
            elif cascading_errors:
                self.logger.warning(f"⚠️ Runtime verification PARTIAL: Original error fixed but {len(cascading_errors)} new error(s) introduced")
                for i, error in enumerate(cascading_errors, 1):
                    self.logger.warning(f"   {i}. {error.get('type')}: {error.get('message', '')[:80]}")
            else:
                self.logger.info("✅ Runtime verification PASSED: Error is fixed")
            
            return result
        else:
            # No tester available, assume success
            self.logger.warning("⚠️  No runtime tester available, skipping verification")
            return {
                'success': True,
                'error_fixed': True,
                'new_errors': [],
                'same_error_persists': False
            }
    
    
    def _check_for_loops(self) -> Optional[Dict]:
        """Check for loops and intervene if necessary"""
        intervention = self.check_for_loops()
        
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
    
    def _check_for_loops_and_enforce(self, intervention_count: int, thread: 'DebuggingConversationThread') -> Dict:
        """
        CRITICAL FIX #3: ENFORCED LOOP BREAKING
        Check for loops and ENFORCE intervention based on count.
        
        Args:
            intervention_count: Number of interventions so far
            thread: Conversation thread
            
        Returns:
            dict: {
                'should_stop': bool,
                'action': 'continue' | 'consult_specialist' | 'ask_user',
                'message': str,
                'specialist_type': str (if action is consult_specialist)
            }
        """
        intervention = self._check_for_loops()
        
        if not intervention:
            return {'should_stop': False, 'action': 'continue', 'message': ''}
        
        # Log the intervention count
        self.logger.warning(f"Loop intervention #{intervention_count}")
        
        # ENFORCE based on intervention count
        if intervention_count == 1:
            # First warning: Log and continue
            self.logger.warning("⚠️  First loop detected - continuing with caution")
            return {
                'should_stop': False,
                'action': 'continue',
                'message': 'First loop warning - continuing'
            }
        
        elif intervention_count == 2:
            # Second warning: Consult whitespace specialist
            self.logger.warning("⚠️  Second loop detected - CONSULTING WHITESPACE SPECIALIST")
            return {
                'should_stop': True,
                'action': 'consult_specialist',
                'message': 'Consulting whitespace specialist for fresh perspective',
                'specialist_type': 'whitespace'
            }
        
        elif intervention_count == 3:
            # Third warning: Consult syntax specialist
            self.logger.warning("⚠️  Third loop detected - CONSULTING SYNTAX SPECIALIST")
            return {
                'should_stop': True,
                'action': 'consult_specialist',
                'message': 'Consulting syntax specialist for alternative approach',
                'specialist_type': 'syntax'
            }
        
        elif intervention_count == 4:
            # Fourth warning: Consult pattern specialist
            self.logger.warning("⚠️  Fourth loop detected - CONSULTING PATTERN SPECIALIST")
            return {
                'should_stop': True,
                'action': 'consult_specialist',
                'message': 'Consulting pattern specialist for root cause analysis',
                'specialist_type': 'pattern'
            }
        
        else:
            # Fifth+ warning: FORCE user intervention
            self.logger.error("🚨 MULTIPLE LOOPS DETECTED - FORCING USER INTERVENTION")
            return {
                'should_stop': True,
                'action': 'ask_user',
                'message': f'Multiple loop interventions failed ({intervention_count} attempts) - user help required'
            }
    
    def _consult_specialist(self, specialist_type: str, thread: DebuggingConversationThread, tools: List) -> Dict:
        """
        Consult specialist from registry or fall back to hardcoded.
        
        Args:
            specialist_type: Type of specialist needed
            thread: Conversation thread
            tools: Available tools
            
        Returns:
            Specialist analysis results
        """
        # Try custom specialist first
        if self.role_registry.has_specialist(specialist_type):
            self.logger.debug(f"Using custom specialist: {specialist_type}")
            return self.role_registry.consult_specialist(
                specialist_type,
                thread=thread,
                tools=tools
            )
        
        # Fall back to hardcoded
        return self.team_coordination.consult_specialist(
            specialist_type,
            thread=thread,
            tools=tools
        )
    
    def _get_prompt(self, prompt_type: str, **variables) -> str:
        """
        Get prompt from registry or fall back to hardcoded.
        
        Args:
            prompt_type: Type of prompt (e.g., 'debugging', 'retry')
            **variables: Variables to substitute in prompt
            
        Returns:
            Formatted prompt string
        """
        # Try custom prompt first
        custom_prompt = self.prompt_registry.get_prompt(
            f"{self.phase_name}_{prompt_type}",
            variables=variables
        )
        
        if custom_prompt:
            self.logger.debug(f"Using custom prompt: {self.phase_name}_{prompt_type}")
            return custom_prompt
        
        # Fall back to hardcoded
        if prompt_type == 'debugging':
                        return get_debugging_prompt(
                variables.get('filepath'),
                variables.get('content'),
                variables.get('issue')
            )
        elif prompt_type == 'retry':
                        return get_failure_retry_prompt(
                variables.get('context'),
                variables.get('failure_analysis', {})
            )
        else:
                        return get_debugging_prompt(
                variables.get('filepath'),
                variables.get('content'),
                variables.get('issue')
            )
    
    def _build_debug_message(self, filepath: str, content: str, issue: Dict, analysis_context: str = "") -> str:
        """
        Build a simple, focused debugging message.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Issue description
        issue_type = issue.get('type', 'unknown')
        issue_desc = issue.get('description', 'No description')
        parts.append(f"Fix this issue in {filepath}:")
        parts.append(f"Issue type: {issue_type}")
        parts.append(f"Description: {issue_desc}")
        
        # Analysis context (if available)
        if analysis_context:
            parts.append(analysis_context)
        
        # Current code or summary
        if content.startswith("[File is"):
            # File too large - provide guidance
            parts.append(f"\n{content}")
            parts.append("\n## Available Tools")
            parts.append("- read_file(filepath) - Read specific file")
            parts.append("- execute_command(cmd) - Run shell commands to examine file")
            parts.append("- analyze_complexity(project_dir, filepath) - Check complexity")
            parts.append("- analyze_call_graph(project_dir, filepath) - Check function calls")
            parts.append("- detect_dead_code(project_dir, filepath) - Check for unused code")
        else:
            # File small enough to include
            parts.append(f"\nCurrent code:\n```\n{content}\n```")
        
        # Instructions
        parts.append("\nPlease fix the issue using the appropriate tools.")
        if analysis_context:
            parts.append("Consider the analysis findings when fixing the issue.")
        
        return "\n".join(parts)
    
    def _analyze_buggy_code(self, filepath: str, issue: Dict) -> str:
        """
        Analyze buggy code to understand the issue better.
        
        CRITICAL FIX: Only analyze the SPECIFIC file, not entire codebase.
        Let AI use tools to explore further if needed.
        
        Returns:
            Analysis summary as formatted string
        """
        analysis_parts = []
        analysis_parts.append("\n## Code Analysis\n")
        
        try:
            # Complexity analysis - ONLY for this specific file
            complexity_result = self.complexity_analyzer.analyze(filepath)
            if complexity_result.max_complexity >= 20:
                analysis_parts.append(f"**High Complexity in {filepath}:**")
                analysis_parts.append(f"- Maximum complexity: {complexity_result.max_complexity}")
                analysis_parts.append(f"- Average complexity: {complexity_result.average_complexity:.1f}")
                analysis_parts.append(f"- High complexity may be contributing to the bug\n")
            
            # Call graph analysis - ONLY for this specific file
            try:
                call_graph_result = self.call_graph.analyze(filepath)
                if call_graph_result.total_functions > 0:
                    analysis_parts.append(f"**Functions in {filepath}:**")
                    analysis_parts.append(f"- Total functions: {call_graph_result.total_functions}")
                    analysis_parts.append(f"- Call relationships: {call_graph_result.total_calls}")
                    if call_graph_result.orphaned_functions:
                        analysis_parts.append(f"- Orphaned functions: {len(call_graph_result.orphaned_functions)}")
                    analysis_parts.append("")
            except Exception as e:
                self.logger.debug(f"  Call graph analysis failed: {e}")
            
            # DO NOT analyze entire codebase - that creates 1.47MB prompts!
            # The AI has tools to explore further if needed:
            # - read_file: Read other files
            # - execute_command: Run grep, find, etc.
            # - analyze_missing_import: Check imports
            # - get_function_signature: Check function details
            
            # Add note about available tools
            analysis_parts.append("**Note:** Use available tools to explore further:")
            analysis_parts.append("- `read_file`: Read other files")
            analysis_parts.append("- `execute_command`: Search codebase (grep, find)")
            analysis_parts.append("- `analyze_missing_import`: Check import issues")
            analysis_parts.append("- `get_function_signature`: Check function details")
            analysis_parts.append("")
                
        except Exception as e:
            self.logger.warning(f"  Code analysis failed: {e}")
            return ""
        
        if len(analysis_parts) > 1:  # More than just the header
            return "\n".join(analysis_parts)
        
        return ""
    
        
        # Check if multiple files involved
        if 'multiple_files' in issue.get('context', {}):
            return 'complex'
        
        # Check if circular dependencies
        if 'circular' in issue.get('message', '').lower():
            return 'complex'
        
        # Check if multiple error types
        message = issue.get('message', '').lower()
        error_indicators = ['syntax', 'indentation', 'import', 'attribute', 'type']
        error_count = sum(1 for indicator in error_indicators if indicator in message)
        if error_count >= 2:
            return 'complex'
        
        # Default to simple
        return 'simple'
    
    def execute(self, state: PipelineState,
                issue: Dict = None,
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute debugging for an issue"""
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent debugging performance
        if self.adaptive_prompts:
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'recent_fixes': [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED and 'debug' in t.task_id.lower()][-5:] if state.tasks else []
            })
        
        
        # CORRELATION ENGINE: Get cross-phase correlations
        correlations = self.get_cross_phase_correlation({
            'phase': self.phase_name
        })
        if correlations:
            self.logger.debug(f"  🔗 Found {len(correlations)} cross-phase correlations")
        
        # PATTERN OPTIMIZER: Get optimization suggestions
        optimization = self.get_optimization_suggestion({
            'current_strategy': 'phase_execution'
        })
        if optimization and optimization.get('suggestions'):
            self.logger.debug(f"  💡 Optimization suggestions available")
        
        # MESSAGE BUS: Publish phase start event
        self._publish_message('PHASE_STARTED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'issue': issue.get('description') if issue else None,
            'task_id': task.task_id if task else None,
            'correlations': correlations,
            'optimization': optimization
        })
        
        # DIMENSION TRACKING: Track initial dimensions
        start_time = datetime.now()
        self.track_dimensions({
            'temporal': 0.6,  # Debugging takes time
            'error': 0.9,  # High error focus
            'functional': 0.7,  # Fixes functionality
            'context': 0.8  # Needs context
        })
        
        # ARCHITECTURE INTEGRATION: Read architecture for design context
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives for debugging priorities
        objectives = self._read_objectives()
        if objectives:
            self.logger.info(f"  🎯 Objectives loaded: PRIMARY={bool(objectives.get('primary'))}, SECONDARY={len(objectives.get('secondary', []))}")
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting debugging",
            "action": "start",
            "issue": issue.get('description') if issue else None,
            "task_id": task.task_id if task else None
        })
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # IPC INTEGRATION: Read bug reports from DEBUG_READ.md
        bug_reports = self.read_own_tasks()
        if bug_reports:
            self.logger.info(f"  📋 Read bug reports from DEBUG_READ.md")
        
        # IPC INTEGRATION: Read strategic documents for known issues
        strategic_docs = self.read_strategic_docs()
        if strategic_docs:
            self.logger.debug(f"  📚 Loaded {len(strategic_docs)} strategic documents")
        
        # IPC INTEGRATION: Read other phases' outputs
        phase_outputs = self._read_relevant_phase_outputs()
        
        # MESSAGE BUS: Check for relevant messages
        if self.message_bus:
            from ..messaging import MessageType, MessagePriority
            messages = self._get_messages(
                message_types=[MessageType.ISSUE_FOUND, MessageType.TASK_FAILED],
                limit=10
            )
            if messages:
                self.logger.info(f"  📨 Received {len(messages)} messages")
                critical_count = sum(1 for m in messages if m.priority == MessagePriority.CRITICAL)
                if critical_count > 0:
                    self.logger.warning(f"    ⚠️ {critical_count} CRITICAL issues in queue")
                for msg in messages[:3]:  # Show first 3
                    self.logger.info(f"    • {msg.message_type.value}: {msg.payload.get('issue_id', msg.payload.get('task_id', 'N/A'))}")
                # Clear processed messages
                self._clear_messages([msg.id for msg in messages])
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is not None:
                task = task_from_state
            # If not found, keep the original (might be standalone debugging)
        
        # NEW: Check IssueTracker for issues to fix
        if hasattr(self, 'coordinator') and hasattr(self.coordinator, 'issue_tracker'):
            # Load issues from state
            self.coordinator.issue_tracker.load_issues(state)
            
            # Get issues by priority
            priority_issues = self.coordinator.issue_tracker.get_issues_by_priority()
            
            if priority_issues and issue is None:
                # Use highest priority issue
                issue_obj = priority_issues[0]
                self.logger.info(f"  🎯 Using issue from tracker: {issue_obj.id} ({issue_obj.severity.value})")
                
                # Mark as in progress
                self.coordinator.issue_tracker.start_fixing(issue_obj.id, state)
                
                # Convert Issue object to dict format for compatibility
                issue = {
                    'filepath': issue_obj.file,
                    'type': issue_obj.issue_type.value,
                    'description': issue_obj.description,
                    'line': issue_obj.line_number,
                    'issue_id': issue_obj.id  # Track for later
                }
        
        # Find issue to fix (legacy path)
        if issue is None:
            issue = get_next_issue(state)
        
        if issue is None:
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No issues to fix",
                files_modified=[],
            )
        
        filepath = issue.get("filepath")
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Issue has no filepath",
                files_modified=[],
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
                message=f"File not found: {filepath}",
                files_modified=[],
            )
        
        # Build debugging message with full file content
        user_message = self._build_debug_message(filepath, content, issue, "")
        
        # Log prompt in verbose mode
        if hasattr(self, 'config') and self.config.verbose:
            self.logger.info(f"  Prompt length: {len(user_message)} chars")
            self.logger.info(f"  Prompt preview: {user_message[:300]}...")
        
        # Get tools for debugging phase
        tools = get_tools_for_phase("debugging")
        
        # Call model with conversation history
        self.logger.info(f"  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls
        tool_calls = response.get("tool_calls", [])
        
        if not tool_calls:
            self.logger.warning("  No fix applied")
            
            # Log response content
            text_content = response.get('content', '')
            if text_content:
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
                        f.write(f"Timestamp: {get_timestamp_iso()}\n")
                        f.write(f"File: {filepath}\n")
                        f.write(f"Issue: {issue.get('type')} - {issue.get('message', '')[:100]}\n")
                        f.write(f"Model: {response.get('model', 'unknown')}\n")
                        f.write(f"\nFull AI Response:\n{content}\n")
                        f.write(f"{'='*80}\n")
                except Exception as e:
                    self.logger.debug(f"Could not write to activity log: {e}")
            
            # Analyze response to understand why no tool calls
            analysis = analyze_no_tool_call_response(content, issue)
            if analysis:
                self.logger.warning(f"  Analysis: {analysis}")
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"No fix was applied - AI did not make any tool calls. {analysis}",
                data={"ai_response": content[:500], "analysis": analysis},
                files_modified=[],
            )
        
        # Execute tool calls
        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
        activity_log = self.project_dir / 'ai_activity.log'
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self._track_tool_calls(tool_calls, results, agent="main")
        
        # Check for loops
        intervention = self._check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            # AUTONOMOUS: Consult AI UserProxy specialist instead of blocking
            self.logger.info("\n" + "="*80)
            self.logger.info("🤖 AUTONOMOUS USER PROXY CONSULTATION")
            self.logger.info("="*80)
            self.logger.info("Loop detected - consulting AI specialist for guidance...")
            
            # Import and create UserProxyAgent
            from pipeline.user_proxy import UserProxyAgent
            user_proxy = UserProxyAgent(
                role_registry=self.role_registry,
                prompt_registry=self.prompt_registry,
                tool_registry=self.tool_registry,
                client=self.client,
                config=self.config,
                logger=self.logger
            )
            
            # Get guidance from AI specialist
            guidance_result = user_proxy.get_guidance(
                error_info={
                    'type': issue.get('type', 'unknown'),
                    'message': issue.get('description', 'No description'),
                    'file': filepath,
                    'line': issue.get('line', 0)
                },
                loop_info={
                    'type': intervention.get('type', 'Unknown'),
                    'iterations': intervention.get('iterations', 0),
                    'pattern': intervention.get('pattern', 'Unknown')
                },
                debugging_history=self.action_tracker.get_recent_actions(10) if hasattr(self, 'action_tracker') else [],
                context={'intervention': intervention}
            )
            
            # Apply the guidance
            guidance = guidance_result.get('guidance', '')
            self.logger.info(f"\n✓ AI Guidance: {guidance}")

            # Continue with the guidance (don't return failure)

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
                            },
                            files_modified=[],
                        )
                    
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=f"Fix failed: {error}",
                        errors=[{"type": "fix_failed", "message": error}],
                        files_modified=[],
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
        
        # NEW: Mark issue as resolved in IssueTracker
        if hasattr(self, 'coordinator') and hasattr(self.coordinator, 'issue_tracker'):
            issue_id = issue.get('issue_id')
            if issue_id:
                self.coordinator.issue_tracker.resolve_issue(
                    issue_id,
                    f"Fixed in {filepath}",
                    state
                )
                self.logger.info(f"  ✅ Issue {issue_id} marked as resolved")
                
                # MESSAGE BUS: Publish ISSUE_RESOLVED event
                from ..messaging import MessageType, MessagePriority
                self._publish_message(
                    message_type=MessageType.ISSUE_RESOLVED,
                    payload={
                        'issue_id': issue_id,
                        'file': filepath,
                        'resolution': f"Fixed in {filepath}"
                    },
                    recipient="broadcast",
                    priority=MessagePriority.NORMAL,
                    issue_id=issue_id,
                    task_id=task.task_id if task else None,
                    objective_id=task.objective_id if task else None,
                    file_path=filepath
                )
                
                # Remove from objective's open issues
                if task and task.objective_id and task.objective_level:
                    obj_level = task.objective_level
                    obj_id = task.objective_id
                    if obj_level in state.objectives and obj_id in state.objectives[obj_level]:
                        obj_data = state.objectives[obj_level][obj_id]
                        if 'open_issues' in obj_data and issue_id in obj_data['open_issues']:
                            obj_data['open_issues'].remove(issue_id)
                        if 'critical_issues' in obj_data and issue_id in obj_data['critical_issues']:
                            obj_data['critical_issues'].remove(issue_id)
        
        # Update task if provided
        if task:
            task.status = TaskStatus.DEBUG_PENDING
            task.priority = TaskPriority.DEBUG_PENDING
        
        # Mark file for re-review
        if filepath in state.files:
            state.files[filepath].qa_status = FileStatus.PENDING
        
        # IPC INTEGRATION: Write status to DEBUG_WRITE.md
        status_content = self._format_status_for_write(
            issue, filepath, fix_applied=True, files_modified=handler.files_modified
        )
        self.write_own_status(status_content)
        self.logger.info("  📝 Updated DEBUG_WRITE.md with fix status")
        
        # IPC INTEGRATION: Send messages to other phases
        self._send_phase_messages(issue, filepath, fix_applied=True)
        
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
                message="Issue has no filepath",
                files_modified=[],
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
                message=f"File not found: {filepath}",
                files_modified=[],
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
            {"role": "system", "content": self._get_system_prompt("debugging")},
            {"role": "user", "content": retry_prompt}
        ]
        
        # Use reasoning specialist for retry
        from ..orchestration.specialists.reasoning_specialist import ReasoningTask
        
        self.logger.info(f"  Using ReasoningSpecialist for retry")
        reasoning_task = ReasoningTask(
            task_type="debug_retry",
            description=f"Retry fix for {filepath}",
            context={
                'filepath': filepath,
                'retry_prompt': retry_prompt,
                'previous_attempts': previous_attempts
            }
        )
        
        specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
        
        if not specialist_result.get("success", False):
            error_msg = specialist_result.get("response", "Specialist retry failed")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Retry failed: {error_msg}",
                files_modified=[],
            )
        
        # Extract tool calls from specialist result
        tool_calls = specialist_result.get("tool_calls", [])
        
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
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self._track_tool_calls(tool_calls, results, agent="retry")
        
        # Check for loops
        intervention = self._check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            # AUTONOMOUS: Consult AI UserProxy specialist instead of blocking
            self.logger.info("\n" + "="*80)
            self.logger.info("🤖 AUTONOMOUS USER PROXY CONSULTATION")
            self.logger.info("="*80)
            self.logger.info("Loop detected - consulting AI specialist for guidance...")
            
            # Import and create UserProxyAgent
            from pipeline.user_proxy import UserProxyAgent
            user_proxy = UserProxyAgent(
                role_registry=self.role_registry,
                prompt_registry=self.prompt_registry,
                tool_registry=self.tool_registry,
                client=self.client,
                config=self.config,
                logger=self.logger
            )
            
            # Get guidance from AI specialist
            guidance_result = user_proxy.get_guidance(
                error_info={
                    'type': issue.get('type', 'unknown'),
                    'message': issue.get('description', 'No description'),
                    'file': filepath,
                    'line': issue.get('line', 0)
                },
                loop_info={
                    'type': intervention.get('type', 'Unknown'),
                    'iterations': intervention.get('iterations', 0),
                    'pattern': intervention.get('pattern', 'Unknown')
                },
                debugging_history=self.action_tracker.get_recent_actions(10) if hasattr(self, 'action_tracker') else [],
                context={'intervention': intervention}
            )
            
            # Apply the guidance
            guidance = guidance_result.get('guidance', '')
            self.logger.info(f"\n✓ AI Guidance: {guidance}")

            # Continue with the guidance (don't return failure)

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
                        errors=[{"type": "retry_failed", "message": error}],
                        files_modified=[],
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
        
        # IPC INTEGRATION: Write completion status
        self._write_status({
            "status": "Debugging completed",
            "action": "complete",
            "filepath": filepath,
            "issue_fixed": True,
            "files_modified": handler.files_modified
        })
        
        # ARCHITECTURE INTEGRATION: Update architecture if structural changes
        if handler.files_modified and architecture:
            for modified_file in handler.files_modified:
                if modified_file.endswith('.py'):
                    self._update_architecture(
                        'components',
                        f"Fixed issue in {modified_file}",
                        f"Debugging: Fixed issue in {modified_file}"
                    )
        
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
                                        max_attempts: int = 999999) -> PhaseResult:  # UNLIMITED attempts
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
        
        # CRITICAL FIX #1: MANDATORY FILE READING
        # AI MUST read the file before attempting any fix
        filepath = issue.get('filepath')
        if not filepath:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No filepath in issue",
                files_modified=[],
            )
        
        # Read file content - MANDATORY
        file_content = self.read_file(filepath)
        if not file_content:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"CRITICAL: Could not read file: {filepath}"
            )
        
        # Add file content to issue for AI context
        issue['file_content'] = file_content
        issue['file_lines'] = file_content.split('\n')
        issue['file_length'] = len(issue['file_lines'])
        
        # Get surrounding code context (40 lines around error)
        error_line = issue.get('line', 0)
        if error_line > 0:
            start = max(0, error_line - 20)
            end = min(len(issue['file_lines']), error_line + 20)
            issue['surrounding_code'] = '\n'.join(issue['file_lines'][start:end])
            issue['context_start_line'] = start + 1
            issue['context_end_line'] = end
        
        self.logger.info(f"  ✅ Read file: {filepath} ({len(file_content)} chars, {len(issue['file_lines'])} lines)")
        
        # Create conversation thread
        thread = DebuggingConversationThread(issue, self.project_dir)
        self.logger.info(f"  💬 Started conversation thread: {thread.thread_id}")
        
        # CRITICAL: Run investigation phase FIRST to diagnose the problem
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"🔍 INVESTIGATION PHASE - Diagnosing problem before fixing")
        self.logger.info(f"{'='*70}")
        
        investigation_phase = self.phases.get('investigation') if hasattr(self, 'phases') else None
        investigation_findings = None
        
        if investigation_phase:
            investigation_result = investigation_phase.execute(state, issue=issue)
            if investigation_result.success and investigation_result.data:
                investigation_findings = investigation_result.data.get('findings', {})
                self.logger.info(f"  ✅ Investigation complete")
                if investigation_findings.get('root_cause'):
                    self.logger.info(f"  🎯 Root cause: {investigation_findings['root_cause']}")
                if investigation_findings.get('recommended_fix'):
                    self.logger.info(f"  💡 Recommended fix: {investigation_findings['recommended_fix']}")
                if investigation_findings.get('related_files'):
                    self.logger.info(f"  📁 Related files: {', '.join(investigation_findings['related_files'])}")
                
                # Add investigation findings to thread context

                
                thread.add_message(
                    role="system",
                    content=f"Investigation findings:\n{safe_json_dumps(investigation_findings, indent=2)}",
                    metadata={"investigation": True}
                )
                
                # Add to issue for AI context
                issue['investigation_findings'] = investigation_findings
            else:
                self.logger.warning(f"  ⚠️ Investigation failed: {investigation_result.message}")
        else:
            self.logger.warning(f"  ⚠️ Investigation phase not available")
        
        self.logger.info(f"{'='*70}\n")
        
        # Assess error complexity
        complexity = assess_error_complexity(issue, len(thread.attempts))
        self.logger.info(f"  📊 Error complexity: {complexity}")
        
        # Use team orchestration for complex errors
        if complexity == 'complex':
            self.logger.info("  🎭 Complex error detected - using team orchestration")
            
            try:
                # Create orchestration plan
                plan = self.team_coordination.create_orchestration_plan(
                    problem=f"Fix {issue['type']}: {issue['message']}",
                    context={
                        'file': issue.get('filepath'),
                        'error': issue,
                        'thread': thread,
                        'attempts': len(thread.attempts)
                    }
                )
                
                # Execute plan
                orchestration_results = self.team_coordination.execute_plan(plan, thread)
                
                # Use synthesis for fix
                if orchestration_results['success']:
                    synthesis = orchestration_results['synthesis']
                    self.logger.info(f"  ✅ Team orchestration completed in {orchestration_results['duration']:.1f}s")
                    self.logger.info(f"  📈 Parallel efficiency: {orchestration_results['statistics']['parallel_efficiency']:.1f}x")
                    
                    # Add synthesis to thread for context
                    thread.add_message(
                        role="system",
                        content=f"Team orchestration synthesis: {synthesis}"
                    )
                else:
                    self.logger.warning("  ⚠️ Team orchestration failed, falling back to standard approach")
            except Exception as e:
                self.logger.error(f"  ❌ Team orchestration error: {e}")
                self.logger.info("  Falling back to standard debugging approach")
        
        # Get tools
        tools = get_phase_tools("debugging")
        
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
                base_prompt = self._get_prompt('debugging', filepath=filepath, content=content, issue=issue)
                
                # CRITICAL FIX #4: ERROR-SPECIFIC STRATEGIES
                # Enhance prompt with error-specific strategy if available
                error_type = issue.get('type', 'RuntimeError')
                strategy = get_error_strategy(error_type, {'issue': issue, 'filepath': filepath})
                if strategy:
                    self.logger.info(f"  📋 Using {error_type} strategy")
                    user_prompt = enhance_prompt_with_error_strategy(base_prompt, issue)
                else:
                    self.logger.debug(f"  No specific strategy for {error_type}, using generic approach")
                    user_prompt = base_prompt
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
                
                user_prompt = self._get_prompt('retry', context=context)
            
            # Add to conversation
            thread.add_message(role="user", content=user_prompt)
            
            # Get conversation history for LLM
            messages = [
                {"role": "system", "content": self._get_system_prompt("debugging")}
            ] + thread.get_conversation_history()
            
            # Use reasoning specialist for conversation-based debugging
            from ..orchestration.specialists.reasoning_specialist import ReasoningTask
            
            self.logger.info(f"  🤖 Using ReasoningSpecialist for conversational debugging...")
            reasoning_task = ReasoningTask(
                task_type="conversational_debug",
                description=f"Debug with conversation history",
                context={
                    'filepath': filepath,
                    'conversation_history': thread.get_conversation_history(),
                    'attempt': attempt_num
                }
            )
            
            specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
            
            if not specialist_result.get("success", False):
                error_msg = specialist_result.get("response", "Specialist failed")
                thread.add_message(
                    role="assistant",
                    content=f"Error: {error_msg}",
                    metadata={"error": True}
                )
                break
            
            # Extract tool calls and response
            tool_calls = specialist_result.get("tool_calls", [])
            text_response = specialist_result.get("response", "")
            
            # LOG AI RESPONSE AND TOOL CALLS
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"🤖 AI RESPONSE:")
            self.logger.info(f"{'='*70}")
            if text_response:
                # Truncate if too long
                if len(text_response) > 500:
                    self.logger.info(f"{text_response[:500]}...")
                    self.logger.info(f"  (truncated, full response: {len(text_response)} chars)")
                else:
                    self.logger.info(text_response)
            else:
                self.logger.info("  (no text response)")
            
            if tool_calls:
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"🔧 TOOL CALLS ({len(tool_calls)}):")
                self.logger.info(f"{'='*70}")
                for i, call in enumerate(tool_calls, 1):
                    # Tool calls have structure: {"function": {"name": "...", "arguments": {...}}}
                    func = call.get('function', {})
                    tool_name = func.get('name', call.get('name', 'unknown'))
                    args = func.get('arguments', call.get('arguments', {}))
                    
                    self.logger.info(f"\n  {i}. {tool_name}")
                    if args:
                           self.logger.info(f"     Arguments:")
                           for key, value in args.items():
                               if isinstance(value, str) and len(value) > 200:
                                   self.logger.info(f"       {key}: {value[:200]}... ({len(value)} chars)")
                               else:
                                   self.logger.info(f"       {key}: {safe_json_dumps(value, indent=8)}")
            else:
                self.logger.info(f"\n⚠️  NO TOOL CALLS MADE")
            self.logger.info(f"{'='*70}\n")
            
            # Add AI response to thread
            thread.add_message(
                role="assistant",
                content=text_response,
                tool_calls=tool_calls
            )
            
            # Filter sudo commands
            if tool_calls:
                allowed_calls, blocked_calls, sudo_summary = filter_sudo_commands(tool_calls)
                
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
                specialist_name = self.team_coordination.specialist_team.get_best_specialist_for_failure(failure_type)
                
                specialist_analysis = self._consult_specialist(
                    specialist_name,
                    thread,
                    tools
                )
                
                # Execute specialist's tool calls if any
                if specialist_analysis.get('tool_calls'):
                    self.logger.info(f"  🔧 Executing {len(specialist_analysis['tool_calls'])} tool calls from specialist...")
                    verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
                    activity_log = self.project_dir / 'ai_activity.log'
                    handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
                    specialist_results = handler.process_tool_calls(specialist_analysis['tool_calls'])
                    
                    # Add results to thread
                    thread.add_message(
                        role="system",
                        content=f"Specialist tool results: {len(specialist_results)} calls executed",
                        tool_results=specialist_results
                    )
                
                continue
            
            # CRITICAL: Detect repeated investigation without action
            investigation_tools = ['analyze_missing_import', 'investigate_data_flow', 
                                 'investigate_parameter_removal', 'get_function_signature',
                                 'check_import_scope', 'check_config_structure']
            
            investigation_count = sum(1 for call in tool_calls 
                                    if call.get('function', {}).get('name') in investigation_tools)
            modification_count = sum(1 for call in tool_calls 
                                   if call.get('function', {}).get('name') in ['modify_python_file', 'modify_file'])
            
            # Check if we're stuck in investigation loop
            if investigation_count > 0 and modification_count == 0:
                # Count recent investigation-only attempts
                recent_investigation_only = 0
                for attempt in thread.attempts[-3:]:  # Last 3 attempts
                    if hasattr(attempt, 'tool_calls'):
                        had_investigation = any(tc.get('function', {}).get('name') in investigation_tools 
                                              for tc in attempt.tool_calls)
                        had_modification = any(tc.get('function', {}).get('name') in ['modify_python_file', 'modify_file']
                                             for tc in attempt.tool_calls)
                        if had_investigation and not had_modification:
                            recent_investigation_only += 1
                
                if recent_investigation_only >= 2:
                    self.logger.warning("⚠️  INVESTIGATION LOOP DETECTED")
                    self.logger.warning(f"   AI has investigated {recent_investigation_only} times without making a fix")
                    self.logger.warning("   FORCING modification on next attempt")
                    
                    # Add emphatic instruction to thread
                    thread.add_message(
                        role="system",
                        content="""⚠️ CRITICAL INTERVENTION ⚠️

You have investigated multiple times without making a fix.
You MUST now call modify_python_file to apply the fix.

DO NOT call investigation tools again.
DO NOT analyze further.
MAKE THE FIX NOW using modify_python_file.

Based on your investigation, you know what needs to be fixed.
Apply the fix immediately.""",
                        metadata={"intervention": "force_modification"}
                    )
            
            # Execute tool calls
            self.logger.info(f"  🔧 Executing {len(tool_calls)} tool call(s)...")
            verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
            activity_log = self.project_dir / 'ai_activity.log'
            handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
            results = handler.process_tool_calls(tool_calls)
            
            # Track actions for loop detection
            self._track_tool_calls(tool_calls, results, agent="conversation")
            
            # CRITICAL FIX #3: ENFORCED LOOP BREAKING
            # Check for loops with enforcement
            loop_check = self._check_for_loops_and_enforce(
                intervention_count=len([a for a in thread.attempts if not a.success]),
                thread=thread
            )
            
            if loop_check['should_stop']:
                if loop_check['action'] == 'consult_specialist':
                    # FORCE specialist consultation
                    self.logger.info(f"  🔬 FORCED: {loop_check['message']}")
                    specialist_type = loop_check.get('specialist_type', 'whitespace')
                    
                    specialist_result = self._consult_specialist(
                        specialist_type,
                        thread,
                        tools
                    )
                    
                    # Add specialist guidance to thread
                    if specialist_result.get('findings'):
                        thread.add_message(
                            role="system",
                            content=f"Specialist ({specialist_type}) findings:\n{specialist_result['findings']}"
                        )
                    
                    # If specialist provided tool calls, execute them
                    if specialist_result.get('tool_calls'):
                        self.logger.info(f"  🔧 Executing specialist's {len(specialist_result['tool_calls'])} tool calls...")
                        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
                        activity_log = self.project_dir / 'ai_activity.log'
                        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
                        specialist_results = handler.process_tool_calls(specialist_result['tool_calls'])
                        
                        # Check if specialist succeeded
                        if any(r.get('success') for r in specialist_results):
                            self.logger.info("  ✅ Specialist fix applied successfully")
                            overall_success = True
                            break
                    
                    # Continue to next attempt with specialist guidance
                    continue
                
                elif loop_check['action'] == 'ask_user':
                    # FORCE user intervention - BLOCKING
                    self.logger.error(f"  🚨 FORCED USER INTERVENTION: {loop_check['message']}")
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message=loop_check['message'],
                        data={
                            'requires_user_input': True,
                            'intervention_count': len([a for a in thread.attempts if not a.success]),
                            'thread': thread
                        },
                        files_modified=[],
                    )
            
            # Old loop detection (for logging only)
            intervention = self._check_for_loops()
            if intervention:
                # Add intervention guidance to thread
                thread.add_message(
                    role="system",
                    content=f"⚠️ LOOP DETECTED\n\n{intervention['guidance']}"
                )
                
                if intervention.get('requires_user_input'):
                    # AUTONOMOUS: Consult AI UserProxy specialist instead of blocking
                    self.logger.info("\n" + "="*80)
                    self.logger.info("🤖 AUTONOMOUS USER PROXY CONSULTATION")
                    self.logger.info("="*80)
                    self.logger.info("Loop detected - consulting AI specialist for guidance...")
                    
                    # Import and create UserProxyAgent
                    from pipeline.user_proxy import UserProxyAgent
                    user_proxy = UserProxyAgent(
                        role_registry=self.role_registry,
                        prompt_registry=self.prompt_registry,
                        tool_registry=self.tool_registry,
                        client=self.client,
                        config=self.config,
                        logger=self.logger
                    )
                    
                    # Get guidance from AI specialist
                    guidance_result = user_proxy.get_guidance(
                        error_info={
                            'type': issue.get('type', 'unknown'),
                            'message': issue.get('message', 'Unknown error'),
                            'file': filepath,
                            'line': issue.get('line_number')
                        },
                        loop_info={
                            'type': intervention.get('type', 'Unknown'),
                            'iterations': intervention.get('iterations', 0),
                            'pattern': intervention.get('pattern', 'Unknown')
                        },
                        debugging_history=thread.get_conversation_history() if thread else [],
                        context={'intervention': intervention, 'thread': thread}
                    )
                    
                    # Apply the guidance
                    guidance = guidance_result.get('guidance', '')
                    self.logger.info(f"\n✓ AI Guidance: {guidance}")

                    # Add guidance to thread
                    if thread:
                        thread.add_message(
                            role="system",
                            content=f"UserProxy AI Guidance: {guidance}"
                        )
                    
                    # Continue with the guidance (don't return failure)

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
                        
                        # CRITICAL: Try to fix with FunctionGemma if original code not found
                        if 'Original code not found' in error_message or 'not found in file' in error_message:
                            self.logger.info("  🔧 Attempting to fix tool call with FunctionGemma...")
                            
                            # Get the failed tool call
                            failed_call = None
                            for call in tool_calls:
                                if call.get('function', {}).get('name') in ['modify_python_file', 'modify_file']:
                                    failed_call = call
                                    break
                            
                            if failed_call and hasattr(self, 'parser') and hasattr(self.parser, 'gemma_formatter'):
                                # Read current file content
                                filepath = result.get('filepath', issue.get('filepath'))
                                file_content = self.read_file(filepath) if filepath else None
                                
                                # Try to fix with FunctionGemma
                                fixed_call = self.parser.gemma_formatter.validate_and_fix_tool_call(
                                    tool_call=failed_call,
                                    available_tools=tools,
                                    file_content=file_content,
                                    error_message=error_message
                                )
                                
                                if fixed_call:
                                    self.logger.info("  ✅ FunctionGemma fixed the tool call, retrying...")
                                    
                                    # Re-execute with fixed call
                                    verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
                                    activity_log = self.project_dir / 'ai_activity.log'
                                    retry_handler = ToolCallHandler(self.project_dir, verbose=verbose, 
                                                                   activity_log_file=str(activity_log), 
                                                                   tool_registry=self.tool_registry)
                                    
                                    retry_results = retry_handler.process_tool_calls([fixed_call])
                                    
                                    # Check if retry succeeded
                                    for retry_result in retry_results:
                                        if retry_result.get('tool') == 'modify_file' and retry_result.get('success'):
                                            success = True
                                            error_message = None
                                            self.logger.info("  🎉 FunctionGemma fix succeeded!")
                                            results = retry_results  # Use retry results
                                            break
                                else:
                                    self.logger.warning("  ❌ FunctionGemma could not fix the tool call")
            
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
                decision_prompt = get_modification_decision(decision_context)
                
                # Use reasoning specialist for decision
                from ..orchestration.specialists.reasoning_specialist import ReasoningTask
                
                self.logger.info(f"  Using ReasoningSpecialist for modification decision")
                reasoning_task = ReasoningTask(
                    task_type="modification_decision",
                    description="Evaluate modification decision",
                    context=decision_context
                )
                
                specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
                
                if specialist_result.get("success", False):
                    decision_text = specialist_result.get('response', '')
                    # Create response format for compatibility
                    decision_response = {
                        "message": {"content": decision_text}
                    }
                    
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
                    self.logger.error(f"  ❌ Specialist decision failed")
            
            if success:
                overall_success = True
                break
            
            # If failed, consult specialists
            if failure_analysis and attempt_num < max_attempts:
                self.logger.info("  🔬 Consulting specialist team...")
                
                # Get best specialist for this failure type
                failure_type = failure_analysis.get('failure_type', 'UNKNOWN')
                specialist_name = self.team_coordination.specialist_team.get_best_specialist_for_failure(failure_type)
                
                specialist_analysis = self._consult_specialist(
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
            
            # MESSAGE BUS: Publish phase completion (success)
            self._publish_message('PHASE_COMPLETED', {
                'phase': self.phase_name,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'filepath': filepath,
                'attempts': thread.current_attempt,
                'task_id': task.task_id if task else None
            })
            
            # DIMENSION TRACKING: Update dimensions based on successful fix
            execution_duration = (datetime.now() - start_time).total_seconds()
            self.track_dimensions({
                'temporal': min(1.0, execution_duration / 180.0),
                'error': 0.1,
                'functional': 0.7,
                'context': 0.8
            })
            
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
            # MESSAGE BUS: Publish phase completion (failure)
            self._publish_message('PHASE_COMPLETED', {
                'phase': self.phase_name,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'attempts': thread.current_attempt,
                'task_id': task.task_id if task else None
            })
            
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
            issue = get_next_issue(state)
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
            data={"fixed": fixed, "failed": failed},
            files_modified=[],
        )
    
    
    
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
        if 'debug' in state.phases:
            lines.append(f"- Total Runs: {state.phases['debug'].runs}")
            lines.append(f"- Successful Fixes: {state.phases['debug'].successes}")
            lines.append(f"- Failed Fixes: {state.phases['debug'].failures}")
        else:
            lines.append("- Stats not available (phase not initialized)")
        lines.append("")
        
        return "\n".join(lines)
    
    def _read_relevant_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases for context"""
        outputs = {}
        
        try:
            # Read QA output for reported bugs
            qa_output = self.read_phase_output('qa')
            if qa_output:
                outputs['qa'] = qa_output
                self.logger.debug("  📖 Read QA phase output")
            
            # Read planning output for known issues
            planning_output = self.read_phase_output('planning')
            if planning_output:
                outputs['planning'] = planning_output
                self.logger.debug("  📖 Read planning phase output")
            
            # Read coding output for recent changes
            coding_output = self.read_phase_output('coding')
            if coding_output:
                outputs['coding'] = coding_output
                self.logger.debug("  📖 Read coding phase output")
                
        except Exception as e:
            self.logger.debug(f"  Error reading phase outputs: {e}")
        
        return outputs
    
    def _send_phase_messages(self, issue: Dict, filepath: str, fix_applied: bool):
        """Send messages to other phases' READ documents"""
        try:
            if fix_applied:
                # Send to QA phase when fix is ready for verification
                qa_message = f"""
## Debug Fix Complete - {self.format_timestamp()}

**File**: {filepath}
**Issue Type**: {issue.get('type', 'N/A')}
**Status**: ✅ Fix applied

### Issue Details
**Description**: {issue.get('description', 'N/A')}
**Line**: {issue.get('line', 'N/A')}

### Fix Applied
The issue has been addressed. Please verify the fix and ensure no regressions were introduced.

**Action Required**: Re-review the file to confirm the fix is correct.
"""
                
                self.send_message_to_phase('qa', qa_message)
                self.logger.info("  📤 Sent fix completion to QA phase")
                
                # PATTERN RECOGNITION: Record fix completion pattern
                self.record_execution_pattern({
                    'pattern_type': 'fix_completion',
                    'issue_type': issue.get('type', 'unknown'),
                    'success': True
                })
                
                # ANALYTICS: Track fix completion metric
                self.track_phase_metric({
                    'metric': 'fix_completed',
                    'issue_type': issue.get('type', 'unknown')
                })
                
                # Also notify coding phase if architectural changes were needed
                if issue.get('type') in ['integration_gap', 'architectural']:
                    dev_message = f"""
## Architectural Fix Applied - {self.format_timestamp()}

**File**: {filepath}
**Issue**: {issue.get('description', 'N/A')}

An architectural issue was fixed. Please review to ensure it aligns with the overall design.
"""
                    self.send_message_to_phase('coding', dev_message)
                    self.logger.info("  📤 Sent architectural fix notice to coding phase")
            else:
                # Send failure notice
                qa_message = f"""
## Debug Attempt Failed - {self.format_timestamp()}

**File**: {filepath}
**Issue Type**: {issue.get('type', 'N/A')}
**Status**: ❌ Fix failed

The debugging attempt was unsuccessful. The issue may require manual intervention or a different approach.
"""
                
                self.send_message_to_phase('qa', qa_message)
                self.logger.info("  📤 Sent failure notice to QA phase")
                
        except Exception as e:
            self.logger.debug(f"  Error sending phase messages: {e}")
    
    def _format_status_for_write(self, issue: Dict, filepath: str, 
                                 fix_applied: bool, files_modified: List[str]) -> str:
        """Format status for DEBUG_WRITE.md"""
        status = f"""# Debugging Phase Status

**Timestamp**: {self.format_timestamp()}
**File**: {filepath}
**Status**: {'✅ Fix Applied' if fix_applied else '❌ Fix Failed'}

## Issue Details

**Type**: {issue.get('type', 'N/A')}
**Description**: {issue.get('description', 'N/A')}
**Line**: {issue.get('line', 'N/A')}
**Severity**: {issue.get('severity', 'N/A')}

"""
        
        if fix_applied:
            status += f"## Fix Summary\n\n"
            status += f"**Files Modified**: {len(files_modified)}\n\n"
            for filepath in files_modified:
                status += f"- `{filepath}`\n"
            
            status += "\n## Verification Needed\n\n"
            status += "- Fix has been applied to the code\n"
            status += "- File marked for QA re-review\n"
            status += "- Please verify the fix resolves the issue\n"
            status += "- Check for any potential regressions\n"
        else:
            status += "## Fix Attempt Failed\n\n"
            status += "The debugging attempt was unsuccessful. Possible reasons:\n"
            status += "- Issue requires manual intervention\n"
            status += "- More context needed to understand the problem\n"
            status += "- Architectural changes required\n"
            status += "\n**Recommendation**: Review the issue manually or provide additional context.\n"
        
        return status
