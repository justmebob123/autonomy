"""
Coding Phase

Implements code based on task descriptions.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_coding_prompt
from ..handlers import ToolCallHandler
from ..utils import validate_python_syntax
from .loop_detection_mixin import LoopDetectionMixin
from ..validation.filename_validator import FilenameValidator, IssueLevel


class CodingPhase(BasePhase, LoopDetectionMixin):
    """
    Coding phase that implements tasks.
    
    Responsibilities:
    - Get next task from queue
    - Build context with error history
    - Generate code via LLM
    - Validate syntax
    - Write files
    - Update CODING_STATE.md
    """
    
    phase_name = "coding"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        
        # FILENAME VALIDATION - Prevent problematic filenames
        self.filename_validator = FilenameValidator(strict_mode=True)
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_STARTED,
                MessageType.ISSUE_FOUND,
                MessageType.PHASE_COMPLETED,
            ])
            self.logger.info("  📡 Subscribed to 3 message types")
        
        self.logger.info("  💻 Coding phase initialized with analysis capabilities")
    
    def execute(self, state: PipelineState, 
                task: TaskState = None, **kwargs) -> PhaseResult:
        """Execute the coding phase with full architecture and IPC integration"""
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent performance
        if self.adaptive_prompts:
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'recent_tasks': [t for t in state.tasks.values() if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]][-5:] if state.tasks else []
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
            'task_id': task.task_id if task else None,
            'correlations': correlations,
            'optimization': optimization
        })
        
        # DIMENSION TRACKING: Track initial dimensions
        start_time = datetime.now()
        self.track_dimensions({
            'temporal': 0.4,  # Coding is relatively fast
            'functional': 0.8,  # High functionality
            'data': 0.5,  # Medium data handling
            'integration': 0.6  # Integrates with system
        })
        
        # ========== INTEGRATION: READ ARCHITECTURE AND OBJECTIVES ==========
        # Read architecture to understand where files should be placed
        architecture = self._read_architecture()
        if architecture.get('structure'):
            self.logger.debug(f"📐 Architecture loaded: {len(architecture['structure'])} chars")
        
        # Read objectives to understand what needs to be built
        objectives = self._read_objectives()
        obj_count = sum(len(objectives.get(level, [])) for level in ['primary', 'secondary', 'tertiary'])
        if obj_count > 0:
            self.logger.info(f"🎯 {obj_count} objectives loaded")
        
        # Write starting status
        self._write_status({
            'status': 'running',
            'message': 'Starting coding phase',
            'task': task.task_id if task else None
        })
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # IPC INTEGRATION: Read tasks from DEVELOPER_READ.md
        tasks_from_doc = self.read_own_tasks()
        if tasks_from_doc:
            self.logger.info(f"  📋 Read {len(tasks_from_doc.split('##'))-1} task(s) from DEVELOPER_READ.md")
        
        # IPC INTEGRATION: Read strategic documents for context
        strategic_docs = self.read_strategic_docs()
        if strategic_docs:
            self.logger.debug(f"  📚 Loaded {len(strategic_docs)} strategic documents")
        
        # IPC INTEGRATION: Read other phases' outputs
        phase_outputs = self._read_relevant_phase_outputs()
        
        # CRITICAL: If task was passed from coordinator, look it up in the loaded state
        # This ensures we modify the task in the state that will be saved
        if task is not None:
            task_from_state = state.get_task(task.task_id)
            if task_from_state is None:
                self.logger.error(f"Task {task.task_id} not found in loaded state")
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    task_id=task.task_id,
                    message=f"Task {task.task_id} not found in state"
                )
            task = task_from_state
        else:
            task = state.get_next_task()
        
        if task is None:
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="No tasks to implement"
            )
        
        # CRITICAL: Skip tasks with empty target_file
        if not task.target_file or task.target_file.strip() == "":
            self.logger.warning(f"  ⚠️  Task {task.task_id} has empty target_file, marking as SKIPPED")
            task.status = TaskStatus.SKIPPED
            self.state_manager.save(state)
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="Skipped task with empty target_file",
                task_id=task.task_id
            )
        
        self.logger.info(f"  Task: {task.description[:60]}...")
        self.logger.info(f"  Target: {task.target_file}")
        self.logger.info(f"  Attempt: {task.attempts + 1}")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.attempts += 1
        
        # Build context
        context = self._build_context(state, task)
        error_context = task.get_error_context()
        
        # Build user message with task details
        user_message = self._build_user_message(task, context, error_context)
        
        # Get tools for this phase
        tools = get_tools_for_phase("coding")
        
        # Call model with conversation history
        self.logger.info(f"  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        
        if not tool_calls:
            # Check if file exists and LLM explained why no changes needed
            file_exists = (self.project_dir / task.target_file).exists()
            
            if file_exists and content and len(content) > 50:
                # LLM provided explanation, file exists - this is SUCCESS (no changes needed)
                self.logger.info("  ℹ️  No changes needed - file already correct")
                task.status = TaskStatus.COMPLETED
                
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    task_id=task.task_id,
                    message="No changes needed - file already correct",
                    next_phase="qa"  # Still send to QA for verification
                )
            else:
                # No file and no tool calls - this is a real failure
                task.add_error("no_tool_call", "Model did not use tools", phase="coding")
                task.status = TaskStatus.FAILED
                task.failure_count = getattr(task, 'failure_count', 0) + 1
                
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    task_id=task.task_id,
                    message="No tool calls in response"
                )
        
        # Execute tool calls
        
        # Check if mark_task_complete was called
        mark_complete_call = None
        for call in tool_calls:
            if call.get("function", {}).get("name") == "mark_task_complete":
                mark_complete_call = call
                break
        
        if mark_complete_call:
            # Task is being marked complete without changes
            reason = mark_complete_call.get("function", {}).get("arguments", {}).get("reason", "File is already complete")
            self.logger.info(f"  ✅ Task marked complete: {reason}")
            task.status = TaskStatus.COMPLETED
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                task_id=task.task_id,
                message=f"Task marked complete: {reason}",
                next_phase="qa"  # Still send to QA for verification
            )
        
        # FILENAME VALIDATION - Check for problematic filenames before processing
        filename_issues = self._validate_tool_call_filenames(tool_calls)
        if filename_issues:
            # Build context about the filename issues
            issue_context = self._build_filename_issue_context(filename_issues, task)
            
            # Add to error context so AI can see it in next iteration
            for issue in filename_issues:
                from ..context.error import ErrorRecord
                error_record = ErrorRecord(
                    error_type="filename_validation",
                    message=f"{issue['message']}: {issue['filepath']}",
                    filepath=issue['filepath'],
                    task_id=task.task_id,
                    phase="coding",
                    context={'issue_context': issue_context, 'suggestion': issue.get('suggestion')}
                )
                self.error_context.add(error_record)
            
            # Return error result with detailed context for AI to resolve
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message=f"Filename validation failed - AI needs to provide correct filenames",
                data={
                    'filename_issues': filename_issues,
                    'requires_ai_resolution': True,
                    'context': issue_context
                }
            )
        
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Track actions for loop detection
        self.track_tool_calls(tool_calls, results, agent="coding")
        
        # Check for loops
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
        
        # Check results
        files_created = handler.files_created
        files_modified = handler.files_modified
        
        if not files_created and not files_modified:
            # Check for syntax errors in results
            for result in results:
                if not result.get("success") and "Syntax error" in result.get("error", ""):
                    error_msg = result["error"]
                    filepath = result.get("filepath", task.target_file)
                    
                    task.add_error(
                        "syntax_error",
                        error_msg,
                        phase="coding"
                    )
                    
                    # Add to error context for next attempt
                    self.error_context.add_syntax_error(
                        error_msg,
                        filepath=filepath,
                        task_id=task.task_id,
                        phase="coding"
                    )
                elif not result.get("success"):
                    # Record other errors too
                    error_msg = result.get("error", "Unknown error")
                    task.add_error(
                        result.get("error_type", "tool_error"),
                        error_msg,
                        phase="coding"
                    )
                    
                    # CRITICAL: If modify_file failed, provide the ENTIRE file content and ask for full rewrite
                    if result.get("tool") == "modify_file" and ("Original code not found" in error_msg or "Missing original_code" in error_msg):
                        filepath = result.get("filepath", task.target_file)
                        full_path = self.project_dir / filepath
                        
                        # Read the current file content
                        try:
                            current_content = full_path.read_text()
                            
                            # Get the modification that was attempted
                            original_code = result.get("original_code", "")
                            new_code = result.get("new_code", "")
                            
                            # Create detailed error with full context
                            error_context = f"""MODIFY_FILE FAILED - FULL FILE REWRITE REQUIRED

The modify_file tool failed because it couldn't find the exact code to replace.

CURRENT FILE CONTENT ({filepath}):
```
{current_content}
```

YOUR ATTEMPTED MODIFICATION:
Original code you tried to find:
```
{original_code}
```

Replacement code you wanted to insert:
```
{new_code}
```

INSTRUCTIONS FOR NEXT ATTEMPT:
1. Review the CURRENT FILE CONTENT above
2. Identify where your modification should go
3. Create the COMPLETE new file content with your changes applied
4. Use the full_file_rewrite tool with the complete new content

DO NOT use modify_file again - use full_file_rewrite with the entire file content."""
                            
                            task.add_error(
                                "modify_file_failed",
                                error_context,
                                phase="coding"
                            )
                            
                            # CONTINUE CONVERSATION: Save state and return
                            # The next iteration will pick up this task with the error context
                            # and the LLM will see the full file content
                            self.logger.info("")
                            self.logger.info("="*70)
                            self.logger.info("💬 CONTINUING CONVERSATION: Error context added, will retry in next iteration")
                            self.logger.info("="*70)
                            self.logger.info("  📝 Full file content added to error context")
                            self.logger.info("  🔄 Task will be picked up in next iteration")
                            self.logger.info("  ✅ LLM will see error context and can use full_file_rewrite")
                            
                            # Save state with error context
                            self.state_manager.save(state)
                            
                            # Return success so coordinator continues
                            # Task stays IN_PROGRESS and will be picked up next iteration
                            return PhaseResult(
                                success=True,
                                phase=self.phase_name,
                                task_id=task.task_id,
                                message="Added error context for modify_file failure, continuing conversation in next iteration"
                            )
                                
                        except Exception as e:
                            # Fallback if we can't read the file
                            task.add_error(
                                "modify_file_failed",
                                f"IMPORTANT: The modify_file tool failed. On your next attempt, use full_file_rewrite instead. Error: {e}",
                                phase="coding"
                            )
            
            # Mark as FAILED for non-modify_file errors or if we couldn't read the file
            task.status = TaskStatus.FAILED
            task.failure_count = getattr(task, 'failure_count', 0) + 1
            
            # Log detailed error information
            error_summary = handler.get_error_summary()
            self.logger.error(f"  ❌ File operation failed: {error_summary}")
            for result in results:
                if not result.get("success"):
                    self.logger.error(f"     Tool: {result.get('tool', 'unknown')}")
                    self.logger.error(f"     Error: {result.get('error', 'Unknown error')}")
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                task_id=task.task_id,
                message="Failed to create/modify files",
                errors=[{"type": "file_error", "message": error_summary}]
            )
        
        # ANALYSIS INTEGRATION: Validate complexity after code generation
        complexity_warnings = []
        for filepath in files_created + files_modified:
            if filepath.endswith('.py'):
                try:
                    self.logger.info(f"  📊 Validating complexity for {filepath}...")
                    complexity_result = self.complexity_analyzer.analyze(filepath)
                    
                    if complexity_result.max_complexity >= 30:
                        warning = f"{filepath}: High complexity detected (max={complexity_result.max_complexity})"
                        complexity_warnings.append(warning)
                        self.logger.warning(f"  ⚠️ {warning}")
                        
                        # Add note to task for QA review
                        task.add_error(
                            "high_complexity",
                            f"Generated code has high complexity (max={complexity_result.max_complexity}). Consider refactoring.",
                            phase="coding"
                        )
                except Exception as e:
                    self.logger.debug(f"  Complexity validation failed for {filepath}: {e}")
        
        # Success - update state with lifecycle awareness
        project_phase = state.get_project_phase()
        completion = state.calculate_completion_percentage()
        
        if project_phase == 'foundation':
            # Foundation phase (0-25%): Mark as completed, defer QA
            task.status = TaskStatus.COMPLETED
            self.logger.info(f"  📊 Foundation phase ({completion:.1f}%): Task completed (QA deferred)")
        else:
            # Integration/Consolidation/Completion: Mark for QA
            task.status = TaskStatus.QA_PENDING
            self.logger.debug(f"  📊 {project_phase.title()} phase ({completion:.1f}%): Task marked for QA")
        
        task.failure_count = 0  # Reset failure count on success
        
        # Update file tracking in state
        for filepath in files_created + files_modified:
            file_hash = self.file_tracker.update_hash(filepath)
            full_path = self.project_dir / filepath
            if full_path.exists():
                state.update_file(filepath, file_hash, full_path.stat().st_size)
        
        message = f"Created {len(files_created)} files, modified {len(files_modified)}"
        if complexity_warnings:
            message += f" (⚠️ {len(complexity_warnings)} complexity warnings)"
        
        # IPC INTEGRATION: Write status to DEVELOPER_WRITE.md
        status_content = self._format_status_for_write(
            task, files_created, files_modified, complexity_warnings
        )
        self.write_own_status(status_content)
        self.logger.info("  📝 Updated DEVELOPER_WRITE.md with task status")
        
        # IPC INTEGRATION: Send messages to other phases
        self._send_phase_messages(task, files_created, files_modified, complexity_warnings)
        
        # ========== INTEGRATION: WRITE COMPLETION STATUS ==========
        self._write_status({
            'status': 'completed',
            'message': message,
            'task_id': task.task_id,
            'files_created': files_created,
            'files_modified': files_modified
        })
        
        # ========== INTEGRATION: UPDATE ARCHITECTURE ==========
        # Record new components in architecture
        if files_created:
            for file_path in files_created:
                # Determine component type from file path
                component_name = Path(file_path).stem
                
                self.arch_manager.add_component(
                    name=component_name,
                    description=f"Created by coding phase for task: {task.description[:100]}",
                    location=file_path,
                    responsibilities=[task.description]
                )
            
            # Record the change
            self._update_architecture({
                'type': 'components_created',
                'details': {
                    'files_created': files_created,
                    'task_id': task.task_id,
                    'rationale': 'Implementation of planned tasks'
                }
            })
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'task_id': task.task_id,
            'files_created': len(files_created),
            'files_modified': len(files_modified)
        })
        
        # DIMENSION TRACKING: Update dimensions based on execution
        execution_duration = (datetime.now() - start_time).total_seconds()
        total_files = len(files_created) + len(files_modified)
        self.track_dimensions({
            'temporal': min(1.0, execution_duration / 120.0),
            'functional': 0.8,
            'data': min(1.0, total_files / 10.0),
            'integration': 0.6
        })
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            task_id=task.task_id,
            message=message,
            files_created=files_created,
            files_modified=files_modified,
            data={'complexity_warnings': complexity_warnings} if complexity_warnings else {}
        )
    
    def _build_context(self, state: PipelineState, task: TaskState) -> str:
        """Build code context for the task"""
        parts = []
        
        # Get related files
        code_ctx = self.code_context.get_context_for_task(
            task.target_file,
            task.description,
            max_context_chars=3000
        )
        if code_ctx:
            parts.append("=== RELATED CODE FROM PROJECT ===")
            parts.append(code_ctx)
        
        # Add dependency file contents
        if task.dependencies:
            parts.append("\n=== DEPENDENCY FILES (required for this task) ===")
            for i, dep in enumerate(task.dependencies[:3], 1):
                # Skip directories
                dep_path = self.project_dir / dep
                if dep_path.exists() and dep_path.is_dir():
                    parts.append(f"\n{i}. {dep} (directory - skipped)")
                    continue
                
                dep_content = self.read_file(dep)
                if dep_content:
                    parts.append(f"\n{i}. FILE: {dep}")
                    parts.append("```python")
                    parts.append(dep_content[:2000])  # Increased from 1000 to 2000
                    if len(dep_content) > 2000:
                        parts.append("... (truncated)")
                    parts.append("```")
                else:
                    parts.append(f"\n{i}. {dep} (file not found yet - will be created by another task)")
        
        # CRITICAL: Add import context for existing files
        if task.target_file:
            target_path = self.project_dir / task.target_file
            if target_path.exists():
                import_context = self._build_import_context(task.target_file)
                if import_context:
                    parts.append("\n=== IMPORT RELATIONSHIPS ===")
                    parts.append(import_context)
        
        # CRITICAL: Add architectural context
        arch_context = self._build_architectural_context(task.target_file)
        if arch_context:
            parts.append("\n=== ARCHITECTURAL CONTEXT ===")
            parts.append(arch_context)
        
        return "\n".join(parts)
    
    def _build_import_context(self, file_path: str) -> str:
        """Build import relationship context for a file."""
        try:
            from ..analysis.import_graph import ImportGraphBuilder
            
            graph_builder = ImportGraphBuilder(str(self.project_dir), self.logger)
            graph_builder.build_graph()
            
            if file_path not in graph_builder.nodes:
                return ""
            
            imports = graph_builder.get_file_imports(file_path)
            importers = graph_builder.get_file_importers(file_path)
            
            lines = []
            
            if imports:
                lines.append(f"**This file imports** ({len(imports)} files):")
                for imp in imports[:10]:  # Limit to 10
                    lines.append(f"  - {imp}")
                if len(imports) > 10:
                    lines.append(f"  ... and {len(imports) - 10} more")
            
            if importers:
                lines.append(f"\n**Imported by** ({len(importers)} files):")
                for imp in importers[:10]:  # Limit to 10
                    lines.append(f"  - {imp}")
                if len(importers) > 10:
                    lines.append(f"  ... and {len(importers) - 10} more")
            
            if not imports and not importers:
                lines.append("⚠️  This file has no import relationships (orphaned or entry point)")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.debug(f"Failed to build import context: {e}")
            return ""
    
    def _build_architectural_context(self, file_path: str) -> str:
        """Build architectural context for file placement."""
        try:
            from ..context.architectural import ArchitecturalContextProvider
            
            arch_context = ArchitecturalContextProvider(str(self.project_dir), self.logger)
            validation = arch_context.validate_file_location(file_path)
            
            lines = []
            
            if validation.valid:
                lines.append(f"✅ File is in correct location according to ARCHITECTURE.md")
                lines.append(f"   Confidence: {validation.confidence:.0%}")
            else:
                lines.append(f"⚠️  File location issues detected:")
                for violation in validation.violations:
                    lines.append(f"   - {violation}")
                if validation.suggested_location:
                    lines.append(f"\n💡 **Suggested location**: {validation.suggested_location}")
                    lines.append(f"   Reason: {validation.reason}")
                    lines.append(f"   Confidence: {validation.confidence:.0%}")
                    lines.append(f"\n   Use 'move_file' tool to relocate if appropriate.")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.debug(f"Failed to build architectural context: {e}")
            return ""
    
    def _build_user_message(self, task: TaskState, context: str, error_context: str) -> str:
        """
        Build a simple, focused user message for the task.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Task description
        parts.append(f"Task: {task.description}")
        parts.append(f"Target file: {task.target_file}")
        
        # CRITICAL FIX: Check if target file already exists
        if task.target_file:
            target_path = self.project_dir / task.target_file
            if target_path.exists():
                try:
                    existing_content = target_path.read_text()
                    file_size = len(existing_content)
                    self.logger.info(f"  📖 File exists: {task.target_file} ({file_size} bytes)")
                    
                    # Add existing file content to context
                    parts.append(f"\n🚨 IMPORTANT: The file {task.target_file} ALREADY EXISTS with {file_size} bytes of content.")
                    parts.append("\nExisting file content:")
                    parts.append(f"```python\n{existing_content}\n```")
                    parts.append("\n⚠️ CRITICAL DECISION REQUIRED:")
                    parts.append("1. If the file is COMPLETE and CORRECT → Use 'mark_task_complete' tool")
                    parts.append("2. If the file has BUGS → Fix ONLY the bugs")
                    parts.append("3. If the file needs ENHANCEMENTS → Add ONLY what's missing")
                    parts.append("4. DO NOT make trivial changes (comments, formatting, etc.)")
                    parts.append("\nExplain your decision before taking action.")
                except Exception as e:
                    self.logger.warning(f"  ⚠️ Could not read existing file: {e}")
        
        # List dependencies explicitly
        if task.dependencies:
            parts.append(f"\nDependencies (files this task depends on):")
            for dep in task.dependencies:
                parts.append(f"  - {dep}")
        
        # Add context if available
        if context:
            parts.append(f"\nRelated code and dependency contents:\n{context}")
        
        # Add error context if available (regardless of attempts, since reactivation resets attempts)
        if error_context:
            parts.append(f"\nPrevious attempt failed:\n{error_context}")
            parts.append("\nPlease fix the issues and try again.")
        
        return "\n".join(parts)
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate CODING_STATE.md content"""
        lines = [
            "# Coding State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Current Session Stats",
            "",
        ]
        
        if 'coding' in state.phases:
            lines.extend([
                f"- Files Created: {state.phases['coding'].successes}",
                f"- Failed Attempts: {state.phases['coding'].failures}",
                f"- Total Runs: {state.phases['coding'].runs}",
            ])
        else:
            lines.append("- Stats not available (phase not initialized)")
        
        lines.append("")
        
        # In-progress tasks
        in_progress = state.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        if in_progress:
            lines.append("## In Progress")
            lines.append("")
            for task in in_progress:
                lines.append(f"### {task.target_file}")
                lines.append(f"- Description: {task.description[:100]}")
                lines.append(f"- Attempt: {task.attempts}")
                lines.append("")
        
        # Recent errors
        recent_errors = []
        for task in state.tasks.values():
            for error in task.errors[-3:]:
                recent_errors.append((task, error))
        
        if recent_errors:
            lines.append("## Recent Errors")
            lines.append("")
            
            # Sort by timestamp
            recent_errors.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            for task, error in recent_errors[:10]:
                lines.append(f"### {task.target_file} - Attempt {error.attempt}")
                lines.append(f"- **Type:** {error.error_type}")
                lines.append(f"- **Message:** {error.message}")
                lines.append(f"- **Time:** {self.format_timestamp(error.timestamp)}")
                if error.line_number:
                    lines.append(f"- **Line:** {error.line_number}")
                if error.code_snippet:
                    lines.append("- **Code:**")
                    lines.append("```python")
                    lines.append(error.code_snippet)
                    lines.append("```")
                lines.append("")
        
        # QA Pending
        qa_pending = state.get_tasks_by_status(TaskStatus.QA_PENDING)
        if qa_pending:
            lines.append("## Awaiting QA Review")
            lines.append("")
            for task in qa_pending:
                lines.append(f"- `{task.target_file}`")
            lines.append("")
        
        # Error patterns
        patterns = self.error_context.get_error_patterns()
        if patterns:
            lines.append("## Error Patterns")
            lines.append("")
            lines.append("| Error Type | Count |")
            lines.append("|------------|-------|")
            for error_type, count in sorted(patterns.items(), key=lambda x: -x[1]):
                lines.append(f"| {error_type} | {count} |")
            lines.append("")
        
        return "\n".join(lines)
    
    def _read_relevant_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases for context"""
        outputs = {}
        
        try:
            # Read planning output for task assignments and priorities
            planning_output = self.read_phase_output('planning')
            if planning_output:
                outputs['planning'] = planning_output
                self.logger.debug("  📖 Read planning phase output")
            
            # Read QA output for feedback on previous code
            qa_output = self.read_phase_output('qa')
            if qa_output:
                outputs['qa'] = qa_output
                self.logger.debug("  📖 Read QA phase output")
            
            # Read debugging output for bug fixes needed
            debug_output = self.read_phase_output('debugging')
            if debug_output:
                outputs['debugging'] = debug_output
                self.logger.debug("  📖 Read debugging phase output")
                
        except Exception as e:
            self.logger.debug(f"  Error reading phase outputs: {e}")
        
        return outputs
    
    def _send_phase_messages(self, task: TaskState, files_created: List[str], 
                            files_modified: List[str], complexity_warnings: List[str]):
        """Send messages to other phases' READ documents"""
        try:
            # Send to QA phase when code is ready for review
            qa_message = f"""
## Code Completion Update - {self.format_timestamp()}

**Task**: {task.description[:100]}
**Target File**: {task.target_file}
**Status**: Ready for QA review

### Changes Made
- **Files Created**: {len(files_created)}
  {chr(10).join(f'  - {f}' for f in files_created[:5])}
- **Files Modified**: {len(files_modified)}
  {chr(10).join(f'  - {f}' for f in files_modified[:5])}

### Quality Notes
"""
            
            if complexity_warnings:
                qa_message += f"⚠️ **Complexity Warnings**: {len(complexity_warnings)}\n"
                for warning in complexity_warnings[:3]:
                    qa_message += f"  - {warning}\n"
            else:
                qa_message += "✅ No complexity warnings detected\n"
            
            qa_message += "\nPlease review the changes and verify functionality.\n"
            
            self.send_message_to_phase('qa', qa_message)
            self.logger.info("  📤 Sent completion message to QA phase")
            
            # PATTERN RECOGNITION: Record task completion pattern
            self.record_execution_pattern({
                'pattern_type': 'task_completion',
                'task_id': task.task_id if task else 'unknown',
                'success': True
            })
            
            # ANALYTICS: Track task completion metric
            self.track_phase_metric({
                'metric': 'task_completed',
                'task_id': task.task_id if task else 'unknown'
            })
            
        except Exception as e:
            self.logger.debug(f"  Error sending phase messages: {e}")
    
    def _validate_tool_call_filenames(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Validate filenames in tool calls before execution.
        
        Returns list of issues found (empty if all valid).
        """
        issues = []
        
        # Tools that create or modify files
        file_tools = ['create_python_file', 'create_file', 'full_file_rewrite', 
                     'modify_python_file', 'str_replace', 'insert_code']
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name', '')
            if tool_name not in file_tools:
                continue
            
            # Extract filepath from arguments
            args = tool_call.get('arguments', {})
            filepath = args.get('filepath') or args.get('file_path')
            
            if not filepath:
                continue
            
            # Build context for validation (existing files in directory)
            context = self._build_validation_context(filepath)
            
            # Validate the filename
            is_valid, validation_issues = self.filename_validator.validate(filepath, context)
            
            # Only report CRITICAL issues (blocking)
            critical_issues = [i for i in validation_issues if i.level == IssueLevel.CRITICAL]
            
            if critical_issues:
                for issue in critical_issues:
                    issues.append({
                        'tool': tool_name,
                        'filepath': filepath,
                        'level': issue.level.value,
                        'message': issue.message,
                        'suggestion': issue.suggestion,
                        'pattern': issue.pattern,
                        'existing_files': context.get('existing_files', [])
                    })
        
        return issues
    
    def _build_validation_context(self, filepath: str) -> Dict:
        """
        Build context for filename validation.
        
        Includes existing files in the target directory to help with
        version number suggestions and pattern detection.
        """
        from pathlib import Path
        
        target_path = Path(filepath)
        directory = target_path.parent
        full_dir = self.project_dir / directory
        
        context = {
            'directory': str(directory),
            'existing_files': []
        }
        
        if full_dir.exists() and full_dir.is_dir():
            try:
                context['existing_files'] = [
                    f.name for f in full_dir.iterdir() 
                    if f.is_file() and not f.name.startswith('.')
                ]
            except Exception as e:
                self.logger.debug(f"  Could not list directory {directory}: {e}")
        
        return context
    
    def _build_filename_issue_context(self, issues: List[Dict], task: TaskState) -> str:
        """
        Build detailed context about filename issues for AI to resolve.
        
        This provides the AI with:
        - What's wrong with the filename
        - Existing files in the directory
        - Suggestions for corrections
        - Examples of correct filenames
        """
        context_parts = []
        
        context_parts.append("🚨 FILENAME VALIDATION FAILED\n\n")
        context_parts.append("You attempted to create files with problematic filenames. ")
        context_parts.append("Please provide corrected filenames and try again.\n\n")
        
        for i, issue in enumerate(issues, 1):
            context_parts.append(f"## Issue {i}: {issue['filepath']}\n\n")
            context_parts.append(f"**Problem**: {issue['message']}\n")
            context_parts.append(f"**Tool**: {issue['tool']}\n")
            context_parts.append(f"**Pattern Detected**: `{issue['pattern']}`\n\n")
            
            if issue.get('existing_files'):
                context_parts.append(f"**Existing files in directory**:\n")
                for f in issue['existing_files'][:10]:  # Limit to 10
                    context_parts.append(f"  - {f}\n")
                context_parts.append("\n")
            
            if issue['suggestion'] and not issue['suggestion'].startswith('NEEDS_AI_CONSULTATION'):
                context_parts.append(f"**Suggested correction**: `{issue['suggestion']}`\n\n")
            else:
                context_parts.append("**Action required**: You must determine the correct filename.\n\n")
        
        context_parts.append("## How to Fix\n\n")
        context_parts.append("For migration files:\n")
        context_parts.append("- Use actual version numbers: `001_projects_table.py`, `002_users_table.py`\n")
        context_parts.append("- Check existing files to determine next version number\n\n")
        
        context_parts.append("For timestamped files:\n")
        context_parts.append("- Use actual timestamps: `backup_20240101_120000.sql`\n")
        context_parts.append("- Format: YYYYMMDD_HHMMSS\n\n")
        
        context_parts.append("For general files:\n")
        context_parts.append("- Use descriptive names: `user_authentication.py`\n")
        context_parts.append("- Use underscores, not spaces: `my_file.py` not `my file.py`\n")
        context_parts.append("- Avoid version suffixes: `config.py` not `config_v2.py`\n\n")
        
        context_parts.append("**IMPORTANT**: Replace ALL placeholder text with actual values before retrying.\n")
        
        return "".join(context_parts)
    
    def _format_status_for_write(self, task: TaskState, files_created: List[str],
                                 files_modified: List[str], complexity_warnings: List[str]) -> str:
        """Format status for DEVELOPER_WRITE.md"""
        status = f"""# Coding Phase Status

**Timestamp**: {self.format_timestamp()}
**Status**: Task Completed
**Task ID**: {task.task_id}

## Task Summary
**Description**: {task.description}
**Target File**: {task.target_file}
**Attempt**: {task.attempts}

## Changes Made

### Files Created ({len(files_created)})
"""
        
        for filepath in files_created:
            status += f"- `{filepath}`\n"
        
        status += f"\n### Files Modified ({len(files_modified)})\n"
        for filepath in files_modified:
            status += f"- `{filepath}`\n"
        
        status += "\n## Quality Metrics\n\n"
        
        if complexity_warnings:
            status += f"⚠️ **Complexity Warnings**: {len(complexity_warnings)}\n\n"
            for warning in complexity_warnings:
                status += f"- {warning}\n"
        else:
            status += "✅ No complexity warnings detected\n"
        
        status += f"\n## Next Steps\n\n"
        status += f"- Task marked as QA_PENDING\n"
        status += f"- Files ready for quality assurance review\n"
        status += f"- Awaiting QA phase verification\n"
        
        return status
