"""
QA Phase

Reviews code for quality issues.
"""

from datetime import datetime
from typing import Dict, List, Tuple

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus, FileStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_qa_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


class QAPhase(BasePhase, LoopDetectionMixin):
    """
    QA phase that reviews generated code.
    
    Responsibilities:
    - Review files pending QA
    - Check for issues
    - Update task priorities based on results
    - Write QA_STATE.md
    """
    
    phase_name = "qa"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..analysis.call_graph import CallGraphGenerator
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.call_graph = CallGraphGenerator(str(self.project_dir), self.logger)
        
        self.logger.info("  🔍 QA phase initialized with comprehensive analysis capabilities")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_COMPLETED,
                MessageType.FILE_CREATED,
                MessageType.FILE_MODIFIED,
                MessageType.SYSTEM_ALERT,
            ])
    
    def execute(self, state: PipelineState,
                filepath: str = None, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute QA review for a file or task"""
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # IPC INTEGRATION: Read review requests from QA_READ.md
        review_requests = self.read_own_tasks()
        if review_requests:
            self.logger.info(f"  📋 Read review requests from QA_READ.md")
        
        # IPC INTEGRATION: Read strategic documents for quality criteria
        strategic_docs = self.read_strategic_docs()
        if strategic_docs:
            self.logger.debug(f"  📚 Loaded {len(strategic_docs)} strategic documents")
        
        # IPC INTEGRATION: Read other phases' outputs
        phase_outputs = self._read_relevant_phase_outputs()
        
        # MESSAGE BUS: Check for relevant messages
        if self.message_bus:
            from ..messaging import MessageType
            messages = self._get_messages(
                message_types=[MessageType.TASK_COMPLETED, MessageType.FILE_MODIFIED],
                limit=5
            )
            if messages:
                self.logger.info(f"  📨 Received {len(messages)} messages")
                for msg in messages:
                    self.logger.info(f"    • {msg.message_type.value}: {msg.payload.get('file', msg.payload.get('task_id', 'N/A'))}")
                # Clear processed messages
                self._clear_messages([msg.id for msg in messages])
        
        # Check no-update count BEFORE processing (loop prevention)
        from ..state.manager import StateManager
        state_manager = StateManager(self.project_dir)
        no_update_count = state_manager.get_no_update_count(state, self.phase_name)
        
        if no_update_count >= 3:
            self.logger.warning(f"  ⚠️ QA phase returned 'no files to review' {no_update_count} times")
            self.logger.info("  🔄 Forcing transition to next phase to prevent loop")
            
            # Reset counter
            state_manager.reset_no_update_count(state, self.phase_name)
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="QA reviewed multiple times - forcing completion to prevent loop",
                next_phase="coding"
            )
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is not None:
                task = task_from_state
            # If not found, keep the original (might be a standalone review)
        
        # Determine what to review
        if filepath is None and task is not None:
            filepath = task.target_file
            
            # Skip tasks with empty target_file
            if not filepath or filepath.strip() == "":
                self.logger.warning(f"  ⚠️ Task {task.task_id} has empty target_file, marking as SKIPPED")
                task.status = TaskStatus.SKIPPED
                state_manager.save(state)
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Skipped task with empty target_file"
                )
        elif filepath is None:
            # Find files needing review
            files = state.get_files_needing_qa()
            if not files:
                # Increment no-update counter
                count = state_manager.increment_no_update_count(state, self.phase_name)
                self.logger.info(f"  No files need QA review (count: {count}/3)")
                
                # After 2 "no files", suggest moving on
                if count >= 2:
                    message = "No files need QA review. Ready to move to next phase."
                    next_phase = "coding"
                else:
                    message = "No files need QA review"
                    next_phase = None
                
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=message,
                    next_phase=next_phase
                )
            filepath = files[0]
            
            # If we got a file to review, reset counter (making progress)
            state_manager.reset_no_update_count(state, self.phase_name)
        
        # Normalize filepath
        filepath = filepath.lstrip('/').replace('\\', '/')
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        self.logger.info(f"  Reviewing: {filepath}")
        
        # Check if it's a directory - skip directories
        full_path = self.project_dir / filepath
        if full_path.is_dir():
            self.logger.warning(f"  ⚠️ Skipping directory: {filepath}")
            # Mark task as completed if provided
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                self.state_manager.save(state)
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Skipped directory: {filepath}",
                next_phase="coding"
            )
        
        # Read file content
        content = self.read_file(filepath)
        if not content:
            # File not found - mark task as SKIPPED and save state
            self.logger.warning(f"⚠️ File not found, marking task as SKIPPED: {filepath}")
            
            # Update task status if we have a task object
            if task is not None:
                task.status = TaskStatus.SKIPPED
                state_manager.save(state)
            
            return PhaseResult(
                success=True,  # Mark as success to avoid infinite loop
                phase=self.phase_name,
                message=f"File not found (task marked SKIPPED): {filepath}",
                next_phase="coding",  # Move to coding to continue with other tasks
                data={"skipped": True, "reason": "file_not_found"}
            )
        
        # ANALYSIS INTEGRATION: Run comprehensive analysis before manual review
        # OPTIMIZATION: Skip deep analysis for test files and small files
        analysis_issues = []
        skip_analysis = (
            filepath.startswith('tests/') or 
            filepath.startswith('test_') or
            '/test_' in filepath
        )
        
        if filepath.endswith('.py') and not skip_analysis:
            self.logger.info(f"  📊 Running comprehensive analysis on {filepath}...")
            try:
                analysis_result = self.run_comprehensive_analysis(filepath)
                if analysis_result and analysis_result.get('success'):
                    analysis_issues = analysis_result.get('issues', [])
                    if analysis_issues:
                        self.logger.info(f"  Found {len(analysis_issues)} issues via analysis")
            except Exception as e:
                self.logger.warning(f"  Analysis failed: {e}")
        elif skip_analysis:
            self.logger.info(f"  ⚡ Skipping deep analysis for test file: {filepath}")
        
        # Build review message with analysis results
        user_message_parts = [
            f"Please review this code for quality issues:\n\nFile: {filepath}\n\n```\n{content}\n```"
        ]
        
        if analysis_issues:
            user_message_parts.append("\n## Automated Analysis Found Issues:\n")
            for issue in analysis_issues[:5]:  # Limit to top 5
                user_message_parts.append(f"- {issue['severity']}: {issue.get('description', 'Unknown issue')}")
                if 'line' in issue:
                    user_message_parts.append(f"  (Line {issue['line']})")
            if len(analysis_issues) > 5:
                user_message_parts.append(f"\n... and {len(analysis_issues) - 5} more issues")
            user_message_parts.append("\nPlease review these automated findings and add any additional issues you identify.")
        
        user_message_parts.append("\nIf you find issues, use the report_qa_issue tool to report them.")
        user_message_parts.append("If the code looks good, just say &quot;APPROVED&quot; (no tool calls needed).")
        
        user_message = "\n".join(user_message_parts)
        
        # Get tools for QA phase
        tools = get_tools_for_phase("qa")
        
        # Call model with conversation history
        self.logger.info(f"  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        text_content = response.get("content", "")
        
        # Debug logging: Show what we got from the model
        self.logger.debug(f"QA Response Analysis:")
        self.logger.debug(f"  - Tool calls found: {len(tool_calls)}")
        self.logger.debug(f"  - Text content length: {len(text_content)}")
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                func = tc.get("function", {})
                self.logger.debug(f"  - Tool[{i}]: name='{func.get('name', '')}', args={list(func.get('arguments', {}).keys())}")
        if text_content and not tool_calls:
            self.logger.debug(f"  - Text content preview: {text_content[:500]}")
        
        if not tool_calls:
            # No tool calls = implicit approval
            self.logger.info("  No issues reported (implicit approval)")
            state.mark_file_reviewed(filepath, approved=True)
            
            # Update task status if applicable
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed = datetime.now().isoformat()
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="File approved (no issues found)"
            )
        
        # Process tool calls
        verbose = getattr(self.config, 'verbose', 0) if hasattr(self, 'config') else 0
        activity_log = self.project_dir / 'ai_activity.log'
        handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self.track_tool_calls(tool_calls, results, agent="qa")
        
        # Check for loops
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
        
        # Check results
        if handler.approved:
            self.logger.info(f"  ✓ Approved: {filepath}")
            state.mark_file_reviewed(filepath, approved=True)
            
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed = datetime.now().isoformat()
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"File approved: {filepath}"
            )
        
        if handler.issues:
            self.logger.warning(f"  ⚠ Found {len(handler.issues)} issues")
            
            # Record issues
            state.mark_file_reviewed(filepath, approved=False, issues=handler.issues)
            
            # Create Issue objects in IssueTracker (NEW)
            if hasattr(self, 'coordinator') and hasattr(self.coordinator, 'issue_tracker'):
                from ..issue_tracker import Issue, IssueType, IssueSeverity
                
                for issue_data in handler.issues:
                    # Determine issue type
                    issue_type_str = issue_data.get("type", "other")
                    try:
                        issue_type = IssueType(issue_type_str)
                    except ValueError:
                        issue_type = IssueType.OTHER
                    
                    # Determine severity
                    severity_map = {
                        "syntax_error": IssueSeverity.CRITICAL,
                        "import_error": IssueSeverity.CRITICAL,
                        "incomplete": IssueSeverity.HIGH,
                        "logic_error": IssueSeverity.HIGH,
                        "type_error": IssueSeverity.MEDIUM,
                        "style_violation": IssueSeverity.LOW
                    }
                    severity = severity_map.get(issue_type_str, IssueSeverity.MEDIUM)
                    
                    # Create Issue object
                    issue = Issue(
                        id="",  # Will be generated
                        issue_type=issue_type,
                        severity=severity,
                        file=filepath,
                        line_number=issue_data.get("line"),
                        title=issue_data.get("type", "QA Issue"),
                        description=issue_data.get("description", ""),
                        related_task=task.task_id if task else None,
                        related_objective=task.objective_id if task else None,
                        reported_by="qa"
                    )
                    
                    # Add to tracker
                    issue_id = self.coordinator.issue_tracker.create_issue(issue, state)
                    
                    # MESSAGE BUS: Publish ISSUE_FOUND event
                    from ..messaging import MessageType, MessagePriority
                    msg_priority = MessagePriority.CRITICAL if severity == IssueSeverity.CRITICAL else MessagePriority.HIGH
                    self._publish_message(
                        message_type=MessageType.ISSUE_FOUND,
                        payload={
                            'issue_id': issue_id,
                            'issue_type': issue_type,
                            'severity': severity.value if hasattr(severity, 'value') else str(severity),
                            'file': file_path,
                            'description': description
                        },
                        recipient="broadcast",
                        priority=msg_priority,
                        issue_id=issue_id,
                        task_id=task.task_id if task else None,
                        objective_id=task.objective_id if task else None,
                        file_path=file_path
                    )
                    
                    # Link to objective if present
                    if task and task.objective_id and task.objective_level:
                        obj_level = task.objective_level
                        obj_id = task.objective_id
                        if obj_level in state.objectives and obj_id in state.objectives[obj_level]:
                            obj_data = state.objectives[obj_level][obj_id]
                            if 'open_issues' not in obj_data:
                                obj_data['open_issues'] = []
                            if issue_id not in obj_data['open_issues']:
                                obj_data['open_issues'].append(issue_id)
                            
                            if severity == IssueSeverity.CRITICAL:
                                if 'critical_issues' not in obj_data:
                                    obj_data['critical_issues'] = []
                                if issue_id not in obj_data['critical_issues']:
                                    obj_data['critical_issues'].append(issue_id)
            
            # Update task priority - CRITICAL FIX: Use NEEDS_FIXES to trigger debugging
            if task:
                task.status = TaskStatus.NEEDS_FIXES  # Changed from QA_FAILED
                task.priority = TaskPriority.QA_FAILURE  # Keep same priority
                
                # Add errors to task
                for issue in handler.issues:
                    task.add_error(
                        issue.get("type", "qa_issue"),
                        issue.get("description", "Unknown issue"),
                        line_number=issue.get("line"),
                        phase="qa"
                    )
            
            # Rebuild queue with new priorities
            state.rebuild_queue()
            
            # CRITICAL FIX: QA finding issues = QA SUCCESS (code has problems)
            # QA phase succeeded in its job of finding issues
            # The CODE needs fixing, not the QA phase
            
            # IPC INTEGRATION: Write status to QA_WRITE.md
            status_content = self._format_status_for_write(filepath, handler.issues, approved=False)
            self.write_own_status(status_content)
            self.logger.info("  📝 Updated QA_WRITE.md with review results")
            
            # IPC INTEGRATION: Send messages to other phases
            self._send_phase_messages(filepath, handler.issues)
            
            return PhaseResult(
                success=True,  # QA succeeded in finding issues!
                phase=self.phase_name,
                message=f"QA found {len(handler.issues)} issues in code - needs fixes",
                errors=handler.issues,
                data={"issues": handler.issues, "filepath": filepath},
                next_phase="debugging"  # Route to debugging to fix the issues
            )
        
        # No explicit approval or issues - this is ambiguous
        # Check if tool calls were actually processed
        successful_tools = sum(1 for r in results if r.get('success', False))
        
        if successful_tools == 0 and len(tool_calls) > 0:
            # Tool calls were made but none succeeded - this is a failure
            self.logger.warning(f"  ⚠️  {len(tool_calls)} tool calls made but none succeeded")
            
            # If this task has failed multiple times, mark it as SKIPPED to prevent infinite loops
            if task:
                task.attempts += 1
                if task.attempts >= 3:
                    self.logger.warning(f"  ⚠️  Task {task.task_id} has failed QA {task.attempts} times, marking as SKIPPED")
                    task.status = TaskStatus.SKIPPED
                    from ..state.manager import StateManager
                    state_manager = StateManager(self.project_dir)
                    state_manager.save(state)
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"QA failed: {len(tool_calls)} tool calls failed",
                errors=[{"type": "tool_failure", "message": "All tool calls failed"}]
            )
        
        # If we got here with successful tool calls but no explicit approval/issues,
        # treat as implicit approval (AI reviewed but didn't find issues)
        self.logger.info("  ✓ Review completed (implicit approval)")
        state.mark_file_reviewed(filepath, approved=True)
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed = datetime.now().isoformat()
        
        # IPC INTEGRATION: Write status to QA_WRITE.md
        status_content = self._format_status_for_write(filepath, [], approved=True)
        self.write_own_status(status_content)
        self.logger.info("  📝 Updated QA_WRITE.md with approval")
        
        # IPC INTEGRATION: Send messages to other phases
        self._send_phase_messages(filepath, [])
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Review completed (implicit approval)"
        )
    
    def review_multiple(self, state: PipelineState, 
                        filepaths: List[str] = None) -> PhaseResult:
        """Review multiple files"""
        if filepaths is None:
            filepaths = state.get_files_needing_qa()
        
        results = []
        all_issues = []
        
        for filepath in filepaths:
            result = self.execute(state, filepath=filepath)
            results.append(result)
            all_issues.extend(result.errors)
        
        approved = sum(1 for r in results if r.success)
        rejected = len(results) - approved
        
        return PhaseResult(
            success=rejected == 0,
            phase=self.phase_name,
            message=f"Reviewed {len(results)} files: {approved} approved, {rejected} rejected",
            errors=all_issues,
            data={"reviewed": len(results), "approved": approved, "rejected": rejected}
        )
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate QA_STATE.md content"""
        lines = [
            "# QA State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Review Summary",
            "",
        ]
        
        # Count by status
        status_counts = {
            "PENDING": 0,
            "APPROVED": 0,
            "REJECTED": 0,
        }
        
        for file_state in state.files.values():
            if file_state.qa_status == FileStatus.APPROVED:
                status_counts["APPROVED"] += 1
            elif file_state.qa_status == FileStatus.REJECTED:
                status_counts["REJECTED"] += 1
            else:
                status_counts["PENDING"] += 1
        
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        for status, count in status_counts.items():
            lines.append(f"| {status} | {count} |")
        lines.append("")
        
        # Pending reviews
        pending = [f for f in state.files.values() 
                   if f.qa_status in [FileStatus.UNKNOWN, FileStatus.PENDING]]
        if pending:
            lines.append("## Pending Reviews")
            lines.append("")
            lines.append("| File | Last Modified | Size |")
            lines.append("|------|---------------|------|")
            for f in pending:
                modified = self.format_timestamp(f.last_modified)
                lines.append(f"| `{f.filepath}` | {modified} | {f.size} bytes |")
            lines.append("")
        
        # Recent approvals
        approved = [f for f in state.files.values() 
                    if f.qa_status == FileStatus.APPROVED]
        if approved:
            lines.append("## Approved Files")
            lines.append("")
            for f in sorted(approved, key=lambda x: x.last_qa or "", reverse=True)[:10]:
                qa_time = self.format_timestamp(f.last_qa) if f.last_qa else "?"
                lines.append(f"- ✓ `{f.filepath}` - {qa_time}")
            lines.append("")
        
        # Rejected files with issues
        rejected = [f for f in state.files.values() 
                    if f.qa_status == FileStatus.REJECTED]
        if rejected:
            lines.append("## Rejected Files")
            lines.append("")
            for f in rejected:
                lines.append(f"### `{f.filepath}`")
                lines.append("")
                if f.issues:
                    for issue in f.issues:
                        lines.append(f"- **[{issue.get('type', 'unknown')}]** {issue.get('description', '')}")
                        if issue.get('line'):
                            lines.append(f"  - Line: {issue['line']}")
                        if issue.get('fix'):
                            lines.append(f"  - Suggested fix: {issue['fix']}")
                lines.append("")
        
        # Session stats
        lines.append("## Session Stats")
        lines.append("")
        lines.append(f"- Total Runs: {state.phases['qa'].runs}")
        lines.append(f"- Successful Reviews: {state.phases['qa'].successes}")
        lines.append(f"- Failed Reviews: {state.phases['qa'].failures}")
        lines.append("")
        
        return "\n".join(lines)
    
    def run_comprehensive_analysis(self, filepath: str) -> Dict:
        """
        Run comprehensive analysis on a file using native analysis tools.
        
        This is CORE QA functionality - not external tools.
        
        Args:
            filepath: Path to file to analyze
        
        Returns:
            Dict with analysis results and quality issues
        """
        issues = []
        
        try:
            # 1. Complexity Analysis
            self.logger.info(f"  📊 Analyzing complexity...")
            complexity_result = self.complexity_analyzer.analyze(target=filepath)
            
            # Check for high complexity functions
            for func in complexity_result.results:
                if func.complexity >= 30:
                    issues.append({
                        'type': 'high_complexity',
                        'severity': 'high' if func.complexity >= 50 else 'medium',
                        'function': func.name,
                        'complexity': func.complexity,
                        'line': func.line,
                        'description': f"Function {func.name} has complexity {func.complexity} (threshold: 30)",
                        'recommendation': f"Refactor to reduce complexity. Estimated effort: {func.effort_days}"
                    })
            
            # 2. Dead Code Detection
            self.logger.info(f"  🔍 Detecting dead code...")
            dead_code_result = self.dead_code_detector.analyze(target=filepath)
            
            # Check for unused functions
            if dead_code_result.unused_functions:
                for func_name, file, line in dead_code_result.unused_functions:
                    if file == filepath or filepath in file:
                        issues.append({
                            'type': 'dead_code',
                            'severity': 'medium',
                            'function': func_name,
                            'line': line,
                            'description': f"Function {func_name} is defined but never called",
                            'recommendation': "Remove if truly unused, or add usage"
                        })
            
            # Check for unused methods
            if dead_code_result.unused_methods:
                for method_key, file, line in dead_code_result.unused_methods:
                    if file == filepath or filepath in file:
                        issues.append({
                            'type': 'dead_code',
                            'severity': 'low',
                            'method': method_key,
                            'line': line,
                            'description': f"Method {method_key} is defined but never called",
                            'recommendation': "Verify if method is needed"
                        })
            
            # 3. Integration Gap Analysis
            self.logger.info(f"  🔗 Checking integration gaps...")
            gap_result = self.gap_finder.analyze(target=filepath)
            
            # Check for unused classes
            if gap_result.unused_classes:
                for class_name, file, line in gap_result.unused_classes:
                    if file == filepath or filepath in file:
                        issues.append({
                            'type': 'integration_gap',
                            'severity': 'medium',
                            'class': class_name,
                            'line': line,
                            'description': f"Class {class_name} is defined but never instantiated",
                            'recommendation': "Complete integration or remove if not needed"
                        })
            
            # Log summary
            if issues:
                self.logger.warning(f"  ⚠️  Found {len(issues)} quality issues via analysis")
                complexity_issues = [i for i in issues if i['type'] == 'high_complexity']
                dead_code_issues = [i for i in issues if i['type'] == 'dead_code']
                gap_issues = [i for i in issues if i['type'] == 'integration_gap']
                
                if complexity_issues:
                    self.logger.warning(f"    - {len(complexity_issues)} high complexity functions")
                if dead_code_issues:
                    self.logger.warning(f"    - {len(dead_code_issues)} dead code instances")
                if gap_issues:
                    self.logger.warning(f"    - {len(gap_issues)} integration gaps")
            else:
                self.logger.info(f"  ✅ No quality issues found via analysis")
            
            return {
                'success': True,
                'issues': issues,
                'complexity': complexity_result.to_dict(),
                'dead_code': dead_code_result.to_dict(),
                'gaps': gap_result.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"  ❌ Analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'issues': []
            }
    
    def _read_relevant_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases for context"""
        outputs = {}
        
        try:
            # Read coding output for completed code
            coding_output = self.read_phase_output('coding')
            if coding_output:
                outputs['coding'] = coding_output
                self.logger.debug("  📖 Read coding phase output")
            
            # Read planning output for quality criteria
            planning_output = self.read_phase_output('planning')
            if planning_output:
                outputs['planning'] = planning_output
                self.logger.debug("  📖 Read planning phase output")
            
            # Read debugging output for known issues
            debug_output = self.read_phase_output('debugging')
            if debug_output:
                outputs['debugging'] = debug_output
                self.logger.debug("  📖 Read debugging phase output")
                
        except Exception as e:
            self.logger.debug(f"  Error reading phase outputs: {e}")
        
        return outputs
    
    def _send_phase_messages(self, filepath: str, issues_found: List[Dict]):
        """Send messages to other phases' READ documents"""
        try:
            if issues_found:
                # Send to debugging phase when bugs found
                debug_message = f"""
## QA Issues Found - {self.format_timestamp()}

**File**: {filepath}
**Issues Found**: {len(issues_found)}
**Status**: Requires debugging

### Issue Summary
"""
                
                # Group by severity
                critical = [i for i in issues_found if i.get('severity') == 'critical']
                high = [i for i in issues_found if i.get('severity') == 'high']
                medium = [i for i in issues_found if i.get('severity') == 'medium']
                low = [i for i in issues_found if i.get('severity') == 'low']
                
                if critical:
                    debug_message += f"\n🔴 **Critical**: {len(critical)} issues\n"
                    for issue in critical[:3]:
                        debug_message += f"  - Line {issue.get('line', 'N/A')}: {issue.get('description', 'N/A')}\n"
                
                if high:
                    debug_message += f"\n🟠 **High**: {len(high)} issues\n"
                    for issue in high[:3]:
                        debug_message += f"  - Line {issue.get('line', 'N/A')}: {issue.get('description', 'N/A')}\n"
                
                if medium:
                    debug_message += f"\n🟡 **Medium**: {len(medium)} issues\n"
                
                if low:
                    debug_message += f"\n🟢 **Low**: {len(low)} issues\n"
                
                debug_message += "\nPlease address these issues and resubmit for QA.\n"
                
                self.send_message_to_phase('debugging', debug_message)
                self.logger.info(f"  📤 Sent {len(issues_found)} issues to debugging phase")
            else:
                # Send approval to developer phase
                dev_message = f"""
## QA Approval - {self.format_timestamp()}

**File**: {filepath}
**Status**: ✅ Approved
**Issues Found**: None

The code has passed quality assurance review. No issues detected.
"""
                
                self.send_message_to_phase('developer', dev_message)
                self.logger.info("  📤 Sent approval to developer phase")
                
        except Exception as e:
            self.logger.debug(f"  Error sending phase messages: {e}")
    
    def _format_status_for_write(self, filepath: str, issues_found: List[Dict], 
                                 approved: bool) -> str:
        """Format status for QA_WRITE.md"""
        status = f"""# QA Phase Status

**Timestamp**: {self.format_timestamp()}
**File Reviewed**: {filepath}
**Status**: {'✅ Approved' if approved else '❌ Issues Found'}

## Review Summary

"""
        
        if issues_found:
            status += f"**Total Issues**: {len(issues_found)}\n\n"
            
            # Group by severity
            by_severity = {}
            for issue in issues_found:
                severity = issue.get('severity', 'unknown')
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            # Report by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in by_severity:
                    issues = by_severity[severity]
                    status += f"### {severity.title()} Priority ({len(issues)} issues)\n\n"
                    for issue in issues[:5]:  # Show first 5
                        status += f"- **Line {issue.get('line', 'N/A')}**: {issue.get('description', 'N/A')}\n"
                        if issue.get('recommendation'):
                            status += f"  - *Recommendation*: {issue['recommendation']}\n"
                    if len(issues) > 5:
                        status += f"  - ... and {len(issues) - 5} more\n"
                    status += "\n"
        else:
            status += "✅ No issues found. Code meets quality standards.\n\n"
        
        status += "## Next Steps\n\n"
        if issues_found:
            status += "- Issues sent to debugging phase\n"
            status += "- Awaiting fixes and resubmission\n"
        else:
            status += "- File approved and marked as reviewed\n"
            status += "- Ready for deployment or next phase\n"
        
        return status
