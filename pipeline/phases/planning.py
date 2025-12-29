"""
Planning Phase

Creates development plans from project specifications.
"""

from datetime import datetime
from typing import Dict, List, Optional

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_planning_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


class PlanningPhase(BasePhase, LoopDetectionMixin):
    """
    Planning phase that creates task plans from MASTER_PLAN.md.
    
    Responsibilities:
    - Parse MASTER_PLAN.md
    - Generate task breakdown
    - Set priorities and dependencies
    - Write PLANNING_STATE.md
    """
    
    phase_name = "planning"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..tool_modules.file_updates import FileUpdateTools
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.file_updater = FileUpdateTools(str(self.project_dir), self.logger)
        
        self.logger.info("  📊 Planning phase initialized with analysis capabilities")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.OBJECTIVE_ACTIVATED,
                MessageType.OBJECTIVE_BLOCKED,
                MessageType.SYSTEM_ALERT,
            ])
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute the planning phase"""
        
        # MESSAGE BUS: Check for relevant messages
        if self.message_bus:
            from ..messaging import MessageType
            messages = self._get_messages(
                message_types=[MessageType.OBJECTIVE_ACTIVATED, MessageType.OBJECTIVE_BLOCKED],
                limit=5
            )
            if messages:
                self.logger.info(f"  📨 Received {len(messages)} messages")
                for msg in messages:
                    self.logger.info(f"    • {msg.message_type.value}: {msg.payload.get('objective_id', 'N/A')}")
                # Clear processed messages
                self._clear_messages([msg.id for msg in messages])
        
        # Check if we have an active objective (strategic mode)
        objective = kwargs.get('objective')
        if objective:
            self.logger.info(f"  🎯 Planning for objective: {objective.title}")
        
        # Load MASTER_PLAN.md
        master_plan = self.read_file("MASTER_PLAN.md")
        if not master_plan:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="MASTER_PLAN.md not found"
            )
        
        self.logger.info(f"  Loaded MASTER_PLAN.md ({len(master_plan)} bytes)")
        
        # IPC: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # IPC: Read outputs from other phases
        phase_outputs = self._read_phase_outputs()
        qa_output = phase_outputs.get('qa', '')
        dev_output = phase_outputs.get('coding', '')
        debug_output = phase_outputs.get('debugging', '')
        
        # IPC: Read strategic documents
        strategic_docs = self.read_strategic_docs()
        
        # Get existing files for context
        existing_files = self._get_existing_files()
        
        # DEEP ANALYSIS: Perform comprehensive codebase analysis
        analysis_results = self._perform_deep_analysis(existing_files)
        
        # IPC: Update strategic documents with findings
        self._update_secondary_objectives(analysis_results, qa_output, debug_output)
        self._update_tertiary_objectives(analysis_results)
        self._update_architecture_doc(analysis_results)
        
        # IPC: Check if MASTER_PLAN needs update (95% threshold)
        if self._should_update_master_plan(state):
            self.logger.info("  🎯 95% completion reached - MASTER_PLAN update needed")
            # TODO: Implement MASTER_PLAN update logic
        
        # ANALYSIS INTEGRATION: Analyze existing codebase before planning
        analysis_context = self._analyze_existing_codebase(existing_files)
        
        # Build messages
        messages = [
            {"role": "system", "content": self._get_system_prompt("planning")},
            {"role": "user", "content": get_planning_prompt(master_plan, existing_files)}
        ]
        
        # Use reasoning specialist for planning
        # Build simple planning message with analysis context
        user_message = self._build_planning_message(master_plan, existing_files, analysis_context)
        
        # Get tools for planning phase
        tools = get_tools_for_phase("planning")
        
        # Call model with conversation history
        self.logger.info("  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        
        tasks = []
        tasks_suggested = 0
        
        if tool_calls:
            # Process tool calls
            handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
            results = handler.process_tool_calls(tool_calls)
            tasks = handler.tasks
            tasks_suggested = len(tasks)
            
            # Track actions for loop detection
            self.track_tool_calls(tool_calls, results, agent="planning")
            
            # Check for loops
            intervention = self.check_for_loops()
            if intervention and intervention.get('requires_user_input'):
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message=f"Loop detected - user intervention required",
                    data={'intervention': intervention}
                )
        
        # Fallback: extract from text
        if not tasks and content:
            self.logger.warning("  Model returned text instead of tool call")
            tasks = self.parser.extract_tasks_from_text(content)
            if tasks:
                tasks_suggested = len(tasks)
                self.logger.info(f"  Extracted {len(tasks)} tasks from text")
        
        if not tasks:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Could not extract tasks from response"
            )
        
        # Track task processing statistics
        tasks_added = 0
        tasks_skipped_duplicate = 0
        tasks_skipped_directory = 0
        tasks_skipped_empty = 0
        
        # Add tasks to state
        for task_data in tasks:
            # Check if task already exists (by description)
            existing = self._find_existing_task(state, task_data)
            
            if existing:
                tasks_skipped_duplicate += 1
                self.logger.debug(f"  ⏭️  Skipping duplicate: {task_data.get('target_file')} (already exists)")
                continue
            
            target_file = task_data.get("target_file", "").strip()
            
            # Skip tasks with empty filenames
            if not target_file:
                tasks_skipped_empty += 1
                self.logger.warning(f"  ⚠️ Skipping task with empty filename: {task_data.get('description', 'Unknown')}")
                continue
                
            # Skip tasks targeting directories
            full_path = self.project_dir / target_file
            if full_path.exists() and full_path.is_dir():
                tasks_skipped_directory += 1
                self.logger.warning(f"  ⚠️ Skipping task targeting directory: {target_file}")
                continue
            
            # Get objective info if available
            objective_id = None
            objective_level = None
            objective = kwargs.get('objective')
            if objective:
                objective_id = objective.id
                objective_level = objective.level.value if hasattr(objective.level, 'value') else objective.level
            
            # Create task with objective linking
            task = state.add_task(
                description=task_data.get("description", ""),
                target_file=target_file,
                priority=task_data.get("priority", TaskPriority.NEW_TASK),
                dependencies=task_data.get("dependencies", []),
                objective_id=objective_id,
                objective_level=objective_level
            )
            
            # Link task to objective
            if objective and objective_id:
                if objective_id not in state.objectives.get(objective_level, {}):
                    # Create objective entry if it doesn't exist
                    if objective_level not in state.objectives:
                        state.objectives[objective_level] = {}
                    state.objectives[objective_level][objective_id] = objective.to_dict()
                
                # Add task to objective's task list
                obj_data = state.objectives[objective_level][objective_id]
                if 'tasks' not in obj_data:
                    obj_data['tasks'] = []
                if task.task_id not in obj_data['tasks']:
                    obj_data['tasks'].append(task.task_id)
                    obj_data['total_tasks'] = len(obj_data['tasks'])
            
            # MESSAGE BUS: Publish TASK_CREATED event
            from ..messaging import MessageType, MessagePriority
            self._publish_message(
                message_type=MessageType.TASK_CREATED,
                payload={
                    'task_id': task.task_id,
                    'description': task.description,
                    'target_file': task.target_file,
                    'priority': task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                },
                recipient="broadcast",
                priority=MessagePriority.NORMAL,
                task_id=task.task_id,
                objective_id=objective_id,
                file_path=task.target_file
            )
            
            # Track that we added this task
            tasks_added += 1
        
        # Log task processing summary
        self.logger.info(f"  📋 Task Summary:")
        self.logger.info(f"     Suggested by model: {tasks_suggested}")
        self.logger.info(f"     Actually added: {tasks_added}")
        if tasks_skipped_duplicate > 0:
            self.logger.info(f"     Skipped (duplicate): {tasks_skipped_duplicate}")
        if tasks_skipped_empty > 0:
            self.logger.info(f"     Skipped (empty filename): {tasks_skipped_empty}")
        if tasks_skipped_directory > 0:
            self.logger.info(f"     Skipped (directory): {tasks_skipped_directory}")
        
        # CRITICAL: Detect when ALL tasks are duplicates (planning loop)
        if tasks_added == 0 and tasks_suggested > 0:
            self.logger.warning(f"  ⚠️  All {tasks_suggested} suggested tasks already exist!")
            self.logger.info(f"  💡 No new work needed - suggesting move to coding phase")
            
            # Rebuild queue anyway (in case priorities changed)
            state.rebuild_queue()
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"No new tasks needed (all {tasks_suggested} already exist)",
                next_phase="coding",  # Hint to coordinator to move forward
                data={
                    "task_count": 0,
                    "tasks_suggested": tasks_suggested,
                    "tasks_skipped": tasks_suggested,
                    "reason": "all_duplicates"
                }
            )
        
        # Rebuild queue with current priorities
        state.rebuild_queue()
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Created plan with {tasks_added} new tasks (suggested {tasks_suggested})",
            data={
                "task_count": tasks_added,
                "tasks": tasks,
                "tasks_suggested": tasks_suggested,
                "tasks_added": tasks_added,
                "tasks_skipped_duplicate": tasks_skipped_duplicate
            }
        )
    
    def _get_existing_files(self) -> str:
        """Get list of existing Python files"""
        files = []
        for f in self.project_dir.rglob("*.py"):
            if "__pycache__" not in str(f):
                rel = f.relative_to(self.project_dir)
                files.append(f"  - {rel}")
        
        return "\n".join(files[:20]) if files else "(no files yet)"
    
    def _find_existing_task(self, state: PipelineState, 
                            task_data: Dict) -> Optional[TaskState]:
        """Find if a similar task already exists"""
        desc = task_data.get("description", "")[:50]
        target = task_data.get("target_file", "")
        
        for task in state.tasks.values():
            if task.description[:50] == desc or task.target_file == target:
                return task
        return None
    
    def _build_planning_message(self, master_plan: str, existing_files: List[str], analysis_context: str = "") -> str:
        """
        Build a simple, focused planning message.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Master plan
        parts.append(f"Master Plan:\n{master_plan}")
        
        # Existing files context
        if existing_files:
            parts.append(f"\nExisting files in project:\n" + "\n".join(f"- {f}" for f in existing_files[:10]))
            if len(existing_files) > 10:
                parts.append(f"... and {len(existing_files) - 10} more files")
        
        # Analysis context (if available)
        if analysis_context:
            parts.append(analysis_context)
        
        # Instructions
        parts.append("\nPlease create a detailed task plan using the create_task tool for each task needed.")
        parts.append("Break down the master plan into specific, actionable tasks.")
        if analysis_context:
            parts.append("Consider the analysis findings when planning tasks.")
        
        return "\n".join(parts)
    
    def _analyze_existing_codebase(self, existing_files: List[str]) -> str:
        """
        Analyze existing codebase to inform planning decisions.
        
        Returns:
            Analysis summary as formatted string
        """
        if not existing_files:
            return ""
        
        self.logger.info("  📊 Analyzing existing codebase...")
        
        analysis_parts = []
        analysis_parts.append("\n## Codebase Analysis\n")
        
        # Analyze Python files only
        python_files = [f for f in existing_files if f.endswith('.py')]
        
        if not python_files:
            return ""
        
        # Limit to first 10 files to avoid overwhelming analysis
        files_to_analyze = python_files[:10]
        
        high_complexity_files = []
        dead_code_files = []
        integration_issues = []
        
        for filepath in files_to_analyze:
            try:
                # Complexity analysis
                complexity_result = self.complexity_analyzer.analyze(filepath)
                if complexity_result.max_complexity >= 30:
                    high_complexity_files.append({
                        'file': filepath,
                        'max_complexity': complexity_result.max_complexity,
                        'avg_complexity': complexity_result.average_complexity
                    })
                
                # Dead code detection
                dead_code_result = self.dead_code_detector.detect(filepath)
                if dead_code_result.unused_functions or dead_code_result.unused_classes:
                    dead_code_files.append({
                        'file': filepath,
                        'unused_functions': len(dead_code_result.unused_functions),
                        'unused_classes': len(dead_code_result.unused_classes)
                    })
                    
            except Exception as e:
                self.logger.debug(f"  Analysis failed for {filepath}: {e}")
                continue
        
        # Check for integration gaps (project-wide)
        try:
            gap_result = self.gap_finder.find_gaps()
            if gap_result.unused_classes or gap_result.missing_integrations:
                integration_issues.append({
                    'unused_classes': len(gap_result.unused_classes),
                    'missing_integrations': len(gap_result.missing_integrations)
                })
        except Exception as e:
            self.logger.debug(f"  Integration gap analysis failed: {e}")
        
        # Format results
        if high_complexity_files:
            analysis_parts.append("### High Complexity Files (≥30)")
            for item in high_complexity_files[:5]:
                analysis_parts.append(f"- `{item['file']}`: max={item['max_complexity']}, avg={item['avg_complexity']:.1f}")
            analysis_parts.append("")
        
        if dead_code_files:
            analysis_parts.append("### Files with Potential Dead Code")
            for item in dead_code_files[:5]:
                analysis_parts.append(f"- `{item['file']}`: {item['unused_functions']} unused functions, {item['unused_classes']} unused classes")
            analysis_parts.append("")
        
        if integration_issues:
            analysis_parts.append("### Integration Issues")
            for item in integration_issues:
                if item['unused_classes'] > 0:
                    analysis_parts.append(f"- {item['unused_classes']} unused classes detected")
                if item['missing_integrations'] > 0:
                    analysis_parts.append(f"- {item['missing_integrations']} missing integrations detected")
            analysis_parts.append("")
        
        if len(analysis_parts) > 1:  # More than just the header
            analysis_parts.append("**Planning Recommendation:** Consider addressing high complexity and dead code issues in your task planning.\n")
            return "\n".join(analysis_parts)
        
        return ""
    
    
    def _update_tertiary_objectives(self, analysis_results: Dict):
        """Update TERTIARY_OBJECTIVES with specific code fixes"""
        try:
            tertiary_path = self.project_dir / 'TERTIARY_OBJECTIVES.md'
            
            content = f"""# Tertiary Objectives - Specific Implementation Details

**Last Updated**: {self.format_timestamp()}

## Specific Code Fixes Needed

"""
            
            # Add complexity issues with specific fixes
            if analysis_results.get('complexity_issues'):
                content += "### High Complexity Functions\n\n"
                for issue in analysis_results['complexity_issues'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Function**: `{issue['function']}`\n"
                    content += f"**Complexity**: {issue['complexity']}\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Recommendation**: {issue['recommendation']}\n\n"
            
            # Add dead code with specific removal guidance
            if analysis_results.get('dead_code'):
                content += "### Dead Code to Remove\n\n"
                for issue in analysis_results['dead_code'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Item**: `{issue['name']}`\n"
                    content += f"**Type**: {issue['type']}\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Action**: Remove or add usage\n\n"
            
            # Add integration gaps with specific integration steps
            if analysis_results.get('integration_gaps'):
                content += "### Integration Gaps to Address\n\n"
                for issue in analysis_results['integration_gaps'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Class**: `{issue['class']}`\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Action**: Complete integration or remove\n\n"
            
            tertiary_path.write_text(content)
            self.logger.info("  📝 Updated TERTIARY_OBJECTIVES.md")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update TERTIARY_OBJECTIVES: {e}")
    
    def _write_phase_messages(self, tasks: List, analysis_results: Dict):
        """Send messages to other phases' READ documents"""
        try:
            # Message to Developer
            if tasks:
                dev_tasks = [t for t in tasks if t.target_file.endswith('.py')]
                if dev_tasks:
                    message = f"""
## Planning Update - {self.format_timestamp()}

**New Tasks**: {len(dev_tasks)} files to implement

### Task List
"""
                    for task in dev_tasks[:5]:
                        message += f"- `{task.target_file}`: {task.description[:60]}\n"
                    
                    self.send_message_to_phase('developer', message)
                    self.logger.info(f"  📤 Sent {len(dev_tasks)} tasks to developer phase")
            
            # Message to QA
            if analysis_results.get('complexity_issues'):
                message = f"""
## Quality Review Needed - {self.format_timestamp()}

**High Complexity Functions**: {len(analysis_results['complexity_issues'])}

Please review these functions for potential refactoring.
"""
                self.send_message_to_phase('qa', message)
                self.logger.info("  📤 Sent complexity warnings to QA phase")
            
            # Message to Debugging
            if analysis_results.get('integration_gaps'):
                message = f"""
## Integration Issues Found - {self.format_timestamp()}

**Integration Gaps**: {len(analysis_results['integration_gaps'])}

Please address these architectural integration issues.
"""
                self.send_message_to_phase('debug', message)
                self.logger.info("  📤 Sent integration gaps to debugging phase")
                
        except Exception as e:
            self.logger.error(f"  ❌ Failed to send phase messages: {e}")
    
    def _should_update_master_plan(self, state: PipelineState) -> bool:
        """Check if 95% completion threshold reached for MASTER_PLAN update"""
        try:
            total_tasks = len(state.tasks)
            if total_tasks == 0:
                return False
            
            completed_tasks = len([t for t in state.tasks.values() 
                                  if t.status == TaskStatus.COMPLETED])
            
            completion_rate = (completed_tasks / total_tasks) * 100
            
            self.logger.info(f"  📊 Completion rate: {completion_rate:.1f}% ({completed_tasks}/{total_tasks})")
            
            return completion_rate >= 95.0
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to check completion rate: {e}")
            return False
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate PLANNING_STATE.md content"""
        lines = [
            "# Planning State",
            f"Generated: {self.format_timestamp()}",
            f"Pipeline Run: {state.pipeline_run_id}",
            "",
            "## Task Queue Summary",
            "",
            f"- Total Tasks: {len(state.tasks)}",
            f"- Pending: {len(state.get_tasks_by_status(TaskStatus.PENDING))}",
            f"- In Progress: {len(state.get_tasks_by_status(TaskStatus.IN_PROGRESS))}",
            f"- Completed: {len(state.get_tasks_by_status(TaskStatus.COMPLETED))}",
            f"- Failed: {len(state.get_tasks_by_status(TaskStatus.FAILED))}",
            "",
        ]
        
        # Add recent tasks
        recent_tasks = list(state.tasks.values())[-5:]
        if recent_tasks:
            lines.append("## Recent Tasks")
            lines.append("")
            for task in recent_tasks:
                lines.append(f"### {task.target_file}")
                lines.append(f"- Status: {task.status.value}")
                lines.append(f"- Description: {task.description[:100]}")
                lines.append("")
        
        return "\n".join(lines)

    def _perform_deep_analysis(self, existing_files: List[str]) -> Dict:
        self.logger.info("  🔍 Performing deep codebase analysis...")
        results = {
            'complexity_issues': [],
            'dead_code': [],
            'integration_gaps': [],
            'architectural_issues': [],
            'test_gaps': [],
            'failures': []
        }
        python_files = [f for f in existing_files if f.endswith('.py')]
        for filepath in python_files:
            try:
                # Complexity analysis
                complexity_result = self.complexity_analyzer.analyze(filepath)
                for func in complexity_result.results:
                    if func.complexity >= 30:
                        results['complexity_issues'].append({
                            'file': filepath,
                            'function': func.name,
                            'complexity': func.complexity,
                            'line': func.line,
                            'recommendation': f"Refactor - estimated {func.effort_days} days"
                        })
                # Dead code detection
                dead_code_result = self.dead_code_detector.detect(filepath)
                if dead_code_result.unused_functions:
                    for func_name, file, line in dead_code_result.unused_functions:
                        if file == filepath or filepath in file:
                            results['dead_code'].append({
                                'file': filepath,
                                'type': 'function',
                                'name': func_name,
                                'line': line,
                                'recommendation': 'Remove or add usage'
                            })
                # Integration gaps
                gap_result = self.gap_finder.find_gaps(filepath)
                if gap_result.unused_classes:
                    for class_name, file, line in gap_result.unused_classes:
                        if file == filepath or filepath in file:
                            results['integration_gaps'].append({
                                'file': filepath,
                                'type': 'class',
                                'name': class_name,
                                'line': line,
                                'recommendation': 'Complete integration or remove'
                            })
            except Exception as e:
                self.logger.warning(f"  Analysis failed for {filepath}: {e}")
        # Log summary
        total_issues = sum(len(v) for v in results.values())
        if total_issues > 0:
            self.logger.info(f"  📊 Found {total_issues} total issues:")
            if results['complexity_issues']:
                self.logger.info(f"    - {len(results['complexity_issues'])} high complexity")
            if results['dead_code']:
                self.logger.info(f"    - {len(results['dead_code'])} dead code")
            if results['integration_gaps']:
                self.logger.info(f"    - {len(results['integration_gaps'])} integration gaps")
        return results
    def _update_secondary_objectives(self, analysis_results: Dict, qa_output: str, debug_output: str):
        self.logger.info("  📝 Updating TERTIARY_OBJECTIVES.md...")
        content_parts = []
        # Specific code fixes needed
        if analysis_results['complexity_issues'] or analysis_results['dead_code']:
            content_parts.append("## Specific Fixes Needed\n\n")
            # High complexity fixes
            for issue in analysis_results['complexity_issues'][:5]:
                content_parts.append(f"### {issue['file']} - Line {issue['line']}\n")
                content_parts.append(f"**Problem**: Function `{issue['function']}` has complexity {issue['complexity']}\n")
                content_parts.append(f"**Fix**: {issue['recommendation']}\n")
                content_parts.append("**Approach**: Break down into smaller functions, extract logic\n\n")
            # Dead code removal
            for dead in analysis_results['dead_code'][:5]:
                content_parts.append(f"### {dead['file']} - Line {dead['line']}\n")
                content_parts.append(f"**Problem**: {dead['type'].title()} `{dead['name']}` is unused\n")
                content_parts.append(f"**Fix**: {dead['recommendation']}\n\n")
        if content_parts:
            full_content = "".join(content_parts)
            try:
                self.file_updater.update_section(
                    "TERTIARY_OBJECTIVES.md",
                    "## Implementation Details",
                    full_content
                )
                self.logger.info("  ✅ Updated TERTIARY_OBJECTIVES.md")
            except Exception as e:
                self.logger.warning(f"  Failed to update TERTIARY_OBJECTIVES.md: {e}")
    def _update_architecture_doc(self, analysis_results: Dict):
        """Update ARCHITECTURE.md with current state and priority issues"""
        try:
            arch_path = self.project_dir / 'ARCHITECTURE.md'
            
            content = f"""# Architecture Document

**Last Updated**: {self.format_timestamp()}

## Current State Analysis

### Code Quality Metrics
"""
            
            # Add complexity summary
            if analysis_results.get('complexity_issues'):
                high_complexity = [i for i in analysis_results['complexity_issues'] if i['complexity'] >= 30]
                content += f"\n**High Complexity Functions**: {len(high_complexity)}\n"
                if high_complexity:
                    content += "\nTop complexity issues:\n"
                    for issue in high_complexity[:5]:
                        content += f"- `{issue['file']}::{issue['function']}` (complexity: {issue['complexity']})\n"
            
            # Add dead code summary
            if analysis_results.get('dead_code'):
                content += f"\n**Dead Code Items**: {len(analysis_results['dead_code'])}\n"
                if analysis_results['dead_code']:
                    content += "\nUnused components:\n"
                    for issue in analysis_results['dead_code'][:5]:
                        content += f"- `{issue['file']}::{issue['name']}` ({issue['type']})\n"
            
            # Add integration gaps summary
            if analysis_results.get('integration_gaps'):
                content += f"\n**Integration Gaps**: {len(analysis_results['integration_gaps'])}\n"
                if analysis_results['integration_gaps']:
                    content += "\nUnintegrated components:\n"
                    for issue in analysis_results['integration_gaps'][:5]:
                        content += f"- `{issue['file']}::{issue['class']}` (line {issue['line']})\n"
            
            content += "\n## Priority Issues\n\n"
            
            # Prioritize issues
            all_issues = []
            if analysis_results.get('complexity_issues'):
                all_issues.extend([('complexity', i) for i in analysis_results['complexity_issues'][:3]])
            if analysis_results.get('integration_gaps'):
                all_issues.extend([('integration', i) for i in analysis_results['integration_gaps'][:3]])
            
            if all_issues:
                for issue_type, issue in all_issues:
                    if issue_type == 'complexity':
                        content += f"1. **Refactor**: `{issue['file']}::{issue['function']}` (complexity {issue['complexity']})\n"
                    elif issue_type == 'integration':
                        content += f"1. **Integrate**: `{issue['file']}::{issue['class']}` (line {issue['line']})\n"
            else:
                content += "No critical issues found.\n"
            
            arch_path.write_text(content)
            self.logger.info("  📝 Updated ARCHITECTURE.md")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update ARCHITECTURE: {e}")
    def _read_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases for context"""
        outputs = {}
        
        try:
            # Read QA output for quality feedback
            qa_output = self.read_phase_output('qa')
            if qa_output:
                outputs['qa'] = qa_output
                self.logger.debug("  📖 Read QA phase output")
            
            # Read coding output for completion status
            developer_output = self.read_phase_output('coding')
            if developer_output:
                outputs['coding'] = developer_output
                self.logger.debug("  📖 Read coding phase output")
            
            # Read debugging output for fixed issues
            debug_output = self.read_phase_output('debugging')
            if debug_output:
                outputs['debugging'] = debug_output
                self.logger.debug("  📖 Read debugging phase output")
                
        except Exception as e:
            self.logger.debug(f"  Error reading phase outputs: {e}")
        
        return outputs

        def generate_state_markdown(self, state: PipelineState) -> str:
            """Generate PLANNING_STATE.md content"""
            lines = [
                "# Planning State",
                f"Generated: {self.format_timestamp()}",
                f"Pipeline Run: {state.pipeline_run_id}",
                "",
                "## Task Queue Summary",
                "",
                f"| Status | Count |",
                f"|--------|-------|",
            ]
        
            # Count by status
            status_counts = {}
            for task in state.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
        
            for status, count in sorted(status_counts.items()):
                lines.append(f"| {status} | {count} |")
        
            lines.append("")
            lines.append("## Tasks by Priority")
            lines.append("")
        
            # Group by priority
            by_priority: Dict[int, List[TaskState]] = {}
            for task in state.tasks.values():
                p = task.priority
                if p not in by_priority:
                    by_priority[p] = []
                by_priority[p].append(task)
        
            priority_names = {
                1: "CRITICAL_BUG",
                2: "QA_FAILURE", 
                3: "DEBUG_PENDING",
                4: "IN_PROGRESS",
                5: "INCOMPLETE",
                6: "NEW_TASK",
                7: "LOW",
                10: "DEFERRED",
            }
        
            for priority in sorted(by_priority.keys()):
                tasks = by_priority[priority]
                priority_name = priority_names.get(priority, f"PRIORITY_{priority}")
            
                lines.append(f"### Priority {priority}: {priority_name}")
                lines.append("")
            
                if not tasks:
                    lines.append("(none)")
                else:
                    for task in tasks:
                        status_icon = {
                            TaskStatus.COMPLETED: "[x]",
                            TaskStatus.SKIPPED: "[~]",
                            TaskStatus.IN_PROGRESS: "[>]",
                            TaskStatus.QA_FAILED: "[!]",
                        }.get(task.status, "[ ]")
                    
                        lines.append(f"- {status_icon} `{task.target_file}` - {task.description[:60]}")
                    
                        if task.dependencies:
                            deps = ", ".join(task.dependencies)
                            lines.append(f"  - Depends on: {deps}")
                    
                        if task.attempts > 0:
                            lines.append(f"  - Attempts: {task.attempts}")
                    
                        if task.errors:
                            last_error = task.errors[-1]
                            lines.append(f"  - Last error: {last_error.message[:50]}")
            
                lines.append("")
        
            # Completed tasks
            completed = state.get_tasks_by_status(TaskStatus.COMPLETED)
            if completed:
                lines.append("## Completed Tasks")
                lines.append("")
                for task in completed:
                    completed_time = self.format_timestamp(task.completed) if task.completed else "?"
                    lines.append(f"- [x] `{task.target_file}` - Completed {completed_time}")
                lines.append("")
        
            return "\n".join(lines)
