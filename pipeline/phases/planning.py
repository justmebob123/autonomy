import time
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
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..analysis.integration_conflicts import IntegrationConflictDetector
        from ..tool_modules.file_updates import FileUpdateTools
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.conflict_detector = IntegrationConflictDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.file_updater = FileUpdateTools(str(self.project_dir), self.logger)
        
        self.logger.info("  📊 Planning phase initialized with analysis capabilities")
        self.logger.info("  🔀 Integration conflict detection enabled")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.OBJECTIVE_ACTIVATED,
                MessageType.OBJECTIVE_BLOCKED,
                MessageType.SYSTEM_ALERT,
            ])
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute the planning phase with full architecture and IPC integration"""
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent planning performance
        if self.adaptive_prompts:
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'recent_objectives': state.get_recent_objectives(limit=5) if hasattr(state, 'get_recent_objectives') else [],
                'recent_issues': state.get_recent_issues(self.phase_name, limit=5) if hasattr(state, 'get_recent_issues') else []
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
            'correlations': correlations,
            'optimization': optimization
        })
        
        # ========== ARCHITECTURE VALIDATION ==========
        # 1. READ INTENDED ARCHITECTURE from MASTER_PLAN.md
        intended_arch = self.arch_manager._read_intended_architecture()
        self.logger.info(f"  📋 Intended architecture: {len(intended_arch.get('components', {}))} components defined")
        
        # 2. ANALYZE CURRENT ARCHITECTURE using validation tools
        current_arch = self.arch_manager.analyze_current_architecture()
        self.logger.info(f"  🔍 Current architecture: {len(current_arch.components)} components found")
        
        # 3. VALIDATE CONSISTENCY between intended and current
        validation = self.arch_manager.validate_architecture_consistency(intended_arch)
        self.logger.info(f"  ✅ Architecture validation: {'CONSISTENT' if validation.is_consistent else 'DRIFT DETECTED'}")
        
        if not validation.is_consistent:
            if validation.missing_components:
                self.logger.warning(f"    ⚠️  Missing {len(validation.missing_components)} components")
            if validation.integration_gaps:
                self.logger.warning(f"    ⚠️  Found {len(validation.integration_gaps)} integration gaps")
        
        # 4. GET ARCHITECTURE DIFF (if we have previous analysis)
        diff = self.arch_manager.get_architecture_diff()
        if diff.has_changes():
            self.logger.info(f"  📊 Architecture changes: +{len(diff.added)} -{len(diff.removed)} ~{len(diff.modified)}")
        
        # 5. UPDATE ARCHITECTURE.MD with comprehensive view
        self.arch_manager.update_architecture_document(
            intended=intended_arch,
            current=current_arch,
            diff=diff,
            validation=validation
        )
        
        # 6. PUBLISH ARCHITECTURE EVENTS via message bus
        self._publish_architecture_events(validation, diff)
        
        # 7. CREATE ARCHITECTURE-AWARE TASKS
        arch_tasks = self._create_architecture_tasks(validation, diff)
        if arch_tasks:
            self.logger.info(f"  📝 Created {len(arch_tasks)} architecture tasks")
        
        # Store validation in state for other phases
        state.architecture_validation = validation
        
        # ========== INTEGRATION: READ ARCHITECTURE AND OBJECTIVES ==========
        # Read architecture to understand project structure
        architecture = self._read_architecture()
        if architecture.get('structure'):
            self.logger.debug(f"📐 Architecture loaded: {len(architecture['structure'])} chars")
        
        # Read existing objectives to understand current goals
        existing_objectives = self._read_objectives()
        obj_count = sum(len(existing_objectives.get(level, [])) for level in ['primary', 'secondary', 'tertiary'])
        if obj_count > 0:
            self.logger.info(f"🎯 {obj_count} existing objectives loaded")
        
        # Write starting status
        self._write_status({
            'status': 'running',
            'message': 'Starting planning phase',
            'architecture_loaded': bool(architecture.get('structure')),
            'objectives_loaded': obj_count
        })
        
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
        self._update_primary_objectives(state)
        self._update_secondary_objectives(analysis_results, phase_outputs)
        self._update_tertiary_objectives(analysis_results)
        self._update_architecture_doc(analysis_results)
        
        # IPC: Check if MASTER_PLAN needs update (95% threshold)
        if self._should_update_master_plan(state):
            self.logger.info("  🎯 95% completion reached - MASTER_PLAN update needed")
            self._update_master_plan_for_completion(state)
        
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
        
        # Log prompt size for monitoring
        if hasattr(self, 'config') and self.config.verbose:
            self.logger.info(f"  Planning prompt length: {len(user_message)} chars")
        
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
        tasks_skipped_test_without_code = 0
        
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
        if tasks_skipped_test_without_code > 0:
            self.logger.warning(f"     Skipped (tests without code): {tasks_skipped_test_without_code}")
            self.logger.info(f"     💡 Create production code first, then add tests!")
        
        # CRITICAL: Detect when ALL tasks are duplicates (planning loop)
        if tasks_added == 0 and tasks_suggested > 0:
            self.logger.warning(f"  ⚠️  All {tasks_suggested} suggested tasks already exist!")
            
            # CRITICAL FIX: Check for tasks in SKIPPED/FAILED status and reactivate them
            from ..state.manager import TaskStatus
            inactive_tasks = [t for t in state.tasks.values() 
                            if t.status in [TaskStatus.SKIPPED, TaskStatus.FAILED]]
            
            if inactive_tasks:
                self.logger.info(f"  🔄 Found {len(inactive_tasks)} inactive tasks - checking for reactivation")
                reactivated = 0
                for task in inactive_tasks[:10]:  # Reactivate up to 10 at a time
                    # CRITICAL: Don't reactivate tasks with empty target_file
                    # These are invalid and will just be skipped again
                    if not task.target_file or task.target_file.strip() == "":
                        self.logger.debug(f"    ⏭️  Skipping reactivation of task with empty target_file: {task.description[:60]}...")
                        continue
                    
                    task.status = TaskStatus.NEW
                    task.attempts = 0  # Reset attempts
                    reactivated += 1
                    self.logger.info(f"    ✅ Reactivated: {task.description[:60]}...")
                
                # Rebuild queue with reactivated tasks
                state.rebuild_queue()
                
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Reactivated {reactivated} inactive tasks",
                    next_phase="coding",  # Move to coding to work on reactivated tasks
                    data={
                        "task_count": reactivated,
                        "tasks_reactivated": reactivated,
                        "reason": "reactivated_inactive_tasks"
                    }
                )
            
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
        
        # ========== INTEGRATION: WRITE COMPLETION STATUS ==========
        self._write_status({
            'status': 'completed',
            'message': f'Created plan with {tasks_added} new tasks',
            'tasks_added': tasks_added,
            'tasks_suggested': tasks_suggested,
            'tasks_skipped': tasks_skipped_duplicate
        })
        
        # ========== INTEGRATION: UPDATE ARCHITECTURE IF NEEDED ==========
        # Planning phase should update architecture with planned components
        if tasks_added > 0:
            planned_files = [task.get('target_file') for task in tasks if task.get('target_file')]
            self._update_architecture({
                'type': 'planning_completed',
                'details': {
                    'tasks_planned': tasks_added,
                    'files_planned': planned_files[:10],  # First 10 files
                    'rationale': 'Tasks created based on MASTER_PLAN analysis'
                }
            })
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'tasks_added': tasks_added,
            'tasks_suggested': tasks_suggested
        })
        
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
        Build a simple, focused planning message with architecture context.
        
        The conversation history provides context, so we keep this simple.
        """
        parts = []
        
        # Master plan
        parts.append(f"Master Plan:\n{master_plan}")
        
        # Architecture context (if available in state)
        if hasattr(self, '_current_validation'):
            validation = self._current_validation
            parts.append("\n## Architecture Context\n")
            parts.append(f"**Status**: {'✅ CONSISTENT' if validation.is_consistent else '⚠️ DRIFT DETECTED'}")
            
            if validation.missing_components:
                parts.append(f"\n**Missing Components**: {', '.join(validation.missing_components[:5])}")
            
            if validation.integration_gaps:
                parts.append(f"\n**Integration Gaps**: {len(validation.integration_gaps)} components need integration")
            
            if not validation.is_consistent:
                parts.append("\n⚠️ **CRITICAL**: Architecture tasks MUST be prioritized before feature development.")
        
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
        if hasattr(self, '_current_validation') and not self._current_validation.is_consistent:
            parts.append("PRIORITIZE architecture consistency tasks before feature development.")
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
                dead_code_result = self.dead_code_detector.analyze(filepath)
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
            gap_result = self.gap_finder.analyze()
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
            timestamp = self.format_timestamp()
            
            # Build content for each section
            sections_to_update = []
            
            # High complexity functions
            if analysis_results.get('complexity_issues'):
                content = f"**Last Updated**: {timestamp}\n\n"
                for issue in analysis_results['complexity_issues'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Function**: `{issue['function']}`\n"
                    content += f"**Complexity**: {issue['complexity']}\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Recommendation**: {issue['recommendation']}\n\n"
                sections_to_update.append(('Specific Code Fixes Needed', content))
            
            # Dead code
            if analysis_results.get('dead_code'):
                content = f"**Last Updated**: {timestamp}\n\n"
                for issue in analysis_results['dead_code'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Item**: `{issue['name']}`\n"
                    content += f"**Type**: {issue['type']}\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Action**: Remove or add usage\n\n"
                sections_to_update.append(('Known Issues', content))
            
            # Integration gaps
            if analysis_results.get('integration_gaps'):
                content = f"**Last Updated**: {timestamp}\n\n"
                for issue in analysis_results['integration_gaps'][:10]:
                    content += f"**File**: `{issue['file']}`\n"
                    content += f"**Class**: `{issue['class']}`\n"
                    content += f"**Line**: {issue['line']}\n"
                    content += f"**Action**: Complete integration or remove\n\n"
                sections_to_update.append(('Known Issues', content))
            
            # Integration conflicts
            if analysis_results.get('integration_conflicts'):
                content = f"**Last Updated**: {timestamp}\n\n"
                for conflict in analysis_results['integration_conflicts'][:10]:
                    content += f"**Type**: {conflict['type']}\n"
                    content += f"**Severity**: {conflict['severity'].upper()}\n"
                    content += f"**Files Involved**:\n"
                    for file in conflict['files']:
                        content += f"  - `{file}`\n"
                    content += f"**Description**: {conflict['description']}\n"
                    content += f"**Recommendation**: {conflict['recommendation']}\n\n"
                sections_to_update.append(('Integration Conflicts to Resolve', content))
            
            # Update each section (appends to existing content)
            for section_name, content in sections_to_update:
                self.file_updater.update_section(
                    'TERTIARY_OBJECTIVES.md',
                    section_name,
                    content
                )
            
            if sections_to_update:
                self.logger.info(f"  📝 Updated {len(sections_to_update)} sections in TERTIARY_OBJECTIVES.md")
            
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
                    
                    self.send_message_to_phase('coding', message)
                    
                    # PATTERN RECOGNITION: Record planning pattern
                    self.record_execution_pattern({
                        'pattern_type': 'planning_complete',
                        'success': True
                    })
                    
                    # ANALYTICS: Track planning metric
                    self.track_phase_metric({
                        'metric': 'planning_completed'
                    })
                    self.logger.info(f"  📤 Sent {len(dev_tasks)} tasks to coding phase")
            
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
    
    def _update_master_plan_for_completion(self, state: PipelineState):
        """Update MASTER_PLAN.md when project nears completion."""
        import re
        from datetime import datetime
        
        try:
            master_plan_path = self.project_dir / 'MASTER_PLAN.md'
            
            if not master_plan_path.exists():
                self.logger.warning("  ⚠️  MASTER_PLAN.md not found, skipping update")
                return
            
            content = master_plan_path.read_text()
            
            # Calculate statistics
            total_tasks = len(state.tasks)
            completed_tasks = len([t for t in state.tasks.values() 
                                  if t.status == TaskStatus.COMPLETED])
            pending_tasks = len([t for t in state.tasks.values() 
                               if t.status in (TaskStatus.NEW, TaskStatus.IN_PROGRESS)])  # Use NEW instead of PENDING
            
            # Create completion status section
            completion_section = f"""
## 📊 Project Status (Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')})

- **Completion**: {state.completion_percentage:.1f}%
- **Current Phase**: {state.current_phase}
- **Tasks Completed**: {completed_tasks}/{total_tasks}
- **Tasks Remaining**: {pending_tasks}

### Next Steps

1. **Final Testing**: Comprehensive testing of all implemented features
2. **Code Review**: Review all code for quality and consistency
3. **Documentation**: Ensure all features are properly documented
4. **Deployment Preparation**: Prepare for production deployment

### Completion Checklist

- [ ] All critical features implemented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code reviewed and refactored
- [ ] Performance optimized
- [ ] Security reviewed
- [ ] Deployment plan ready
"""
            
            # Update or append status section
            if '## 📊 Project Status' in content or '## Project Status' in content:
                # Update existing section
                content = re.sub(
                    r'## (?:📊 )?Project Status.*?(?=\n##|\Z)',
                    completion_section.strip(),
                    content,
                    flags=re.DOTALL
                )
            else:
                # Append new section
                content += '\n\n' + completion_section
            
            # Write updated content
            master_plan_path.write_text(content)
            self.logger.info("  ✅ Updated MASTER_PLAN.md with completion status")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update MASTER_PLAN.md: {e}")
    
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
            f"- New: {len(state.get_tasks_by_status(TaskStatus.NEW))}",
            f"- In Progress: {len(state.get_tasks_by_status(TaskStatus.IN_PROGRESS))}",
            f"- QA Pending: {len(state.get_tasks_by_status(TaskStatus.QA_PENDING))}",
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
            'integration_conflicts': [],
            'architectural_issues': [],
            'test_gaps': [],
            'failures': []
        }
        
        # First, run project-wide conflict detection
        self.logger.info("  🔀 Detecting integration conflicts...")
        try:
            conflict_result = self.conflict_detector.analyze()
            for conflict in conflict_result.conflicts:
                results['integration_conflicts'].append({
                    'type': conflict.conflict_type,
                    'severity': conflict.severity,
                    'files': conflict.files,
                    'description': conflict.description,
                    'recommendation': conflict.recommendation,
                    'details': conflict.details
                })
        except Exception as e:
            self.logger.warning(f"  Conflict detection failed: {e}")
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
                dead_code_result = self.dead_code_detector.analyze(filepath)
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
                gap_result = self.gap_finder.analyze(filepath)
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
            if results['integration_conflicts']:
                self.logger.info(f"    - {len(results['integration_conflicts'])} integration conflicts")
                high_conflicts = [c for c in results['integration_conflicts'] if c['severity'] == 'high']
                if high_conflicts:
                    self.logger.warning(f"      ⚠️  {len(high_conflicts)} HIGH SEVERITY conflicts need immediate attention")
        return results
    def _update_tertiary_objectives(self, analysis_results: Dict):
        """Update TERTIARY_OBJECTIVES.md with highly specific implementation details"""
        try:
            tertiary_path = self.project_dir / 'TERTIARY_OBJECTIVES.md'
            
            content = f"""# Tertiary Objectives - Specific Implementation Details

> **Purpose**: Highly specific implementation steps, code examples, and exact changes needed
> **Updated By**: Planning phase (from detailed analysis)
> **Read By**: Coding, Debugging, Refactoring phases
> **Last Updated**: {self.format_timestamp()}

---

## Specific Code Changes Required

> This section provides exact file locations, line numbers, and concrete implementation steps.
> Each item includes the problem, the fix, and example code where applicable.

"""
            
            # Import integration point checker
            from pipeline.analysis.integration_points import is_integration_point
            
            # 1. HIGH COMPLEXITY REFACTORING
            if analysis_results.get('complexity_issues'):
                high_complexity = [i for i in analysis_results['complexity_issues'] if i['complexity'] >= 30]
                if high_complexity:
                    content += f"""### 1. High Complexity Refactoring ({len(high_complexity)} functions)

> Functions with cyclomatic complexity >= 30 need to be broken down.

"""
                    for idx, issue in enumerate(high_complexity[:10], 1):
                        content += f"""#### {idx}. `{issue['file']}::{issue['function']}` (Line {issue['line']})

**Complexity Score**: {issue['complexity']} (threshold: 30)

**Problem**: Function is too complex and hard to maintain.

**Recommendation**: {issue['recommendation']}

**Implementation Steps**:
1. Identify logical sections within the function
2. Extract each section into a separate helper function
3. Add clear docstrings to each new function
4. Update tests to cover new functions
5. Verify original functionality is preserved

**Example Refactoring Pattern**:
```python
# Before: Complex function
def complex_function(data):
    # 100+ lines of mixed logic
    result = process_step1(data)
    result = process_step2(result)
    result = process_step3(result)
    return result

# After: Broken down
def complex_function(data):
    &quot;&quot;&quot;Main orchestration function.&quot;&quot;&quot;
    result = _process_step1(data)
    result = _process_step2(result)
    result = _process_step3(result)
    return result

def _process_step1(data):
    &quot;&quot;&quot;Handle step 1 logic.&quot;&quot;&quot;
    # Clear, focused logic
    pass

def _process_step2(data):
    &quot;&quot;&quot;Handle step 2 logic.&quot;&quot;&quot;
    # Clear, focused logic
    pass
```

---

"""
            
            # 2. DEAD CODE REMOVAL
            if analysis_results.get('dead_code'):
                # Filter out integration points
                real_dead_code = [i for i in analysis_results['dead_code'] 
                                if not is_integration_point(i['file'], i['type'], i['name'])]
                
                if real_dead_code:
                    content += f"""### 2. Dead Code Removal ({len(real_dead_code)} items)

> Unused code that can be safely removed to improve maintainability.

"""
                    for idx, dead in enumerate(real_dead_code[:10], 1):
                        content += f"""#### {idx}. `{dead['file']}::{dead['name']}` (Line {dead['line']})

**Type**: {dead['type'].title()}

**Problem**: This {dead['type']} is defined but never called or used.

**Recommendation**: {dead['recommendation']}

**Action Required**:
1. Verify no external dependencies use this {dead['type']}
2. Check if it's part of a public API (if so, deprecate first)
3. Remove the {dead['type']} definition
4. Remove any associated tests
5. Update documentation if referenced

**Verification Command**:
```bash
# Search for any usage of this {dead['type']}
grep -r "{dead['name']}" . --include="*.py" | grep -v "def {dead['name']}"
```

---

"""
            
            # 3. INTEGRATION GAPS
            if analysis_results.get('integration_gaps'):
                # Filter out known integration points
                real_gaps = [i for i in analysis_results['integration_gaps'] 
                           if not is_integration_point(i['file'], 'class', i.get('class', ''))]
                
                if real_gaps:
                    content += f"""### 3. Integration Gaps ({len(real_gaps)} components)

> Components that are defined but not integrated into the system.

"""
                    for idx, gap in enumerate(real_gaps[:10], 1):
                        content += f"""#### {idx}. `{gap['file']}::{gap['class']}` (Line {gap['line']})

**Problem**: Class is defined but not instantiated or used anywhere.

**Integration Steps**:
1. Identify where this component should be used
2. Import the class in the appropriate module
3. Instantiate with required dependencies
4. Wire into existing workflow/pipeline
5. Add integration tests

**Example Integration Pattern**:
```python
# In the appropriate module (e.g., main.py, coordinator.py)
from {gap['file'].replace('/', '.').replace('.py', '')} import {gap['class']}

# Instantiate with dependencies
{gap['class'].lower()} = {gap['class']}(
    dependency1=dep1,
    dependency2=dep2
)

# Use in workflow
result = {gap['class'].lower()}.process(data)
```

**Files to Modify**:
- `{gap['file']}` - The component itself (may need constructor updates)
- `[main module]` - Where component should be instantiated
- `[workflow module]` - Where component should be called
- `tests/test_{gap['class'].lower()}.py` - Integration tests

---

"""
            
            # 4. INTEGRATION CONFLICTS
            if analysis_results.get('integration_conflicts'):
                content += f"""### 4. Integration Conflicts ({len(analysis_results['integration_conflicts'])} conflicts)

> Conflicts between components that need resolution.

"""
                for idx, conflict in enumerate(analysis_results['integration_conflicts'][:5], 1):
                    content += f"""#### {idx}. {conflict.get('description', 'Unknown conflict')}

**Type**: {conflict.get('type', 'Unknown')}

**Affected Components**:
{chr(10).join(f"- `{comp}`" for comp in conflict.get('components', []))}

**Resolution Steps**:
1. Analyze the conflict in detail
2. Determine which component should take precedence
3. Refactor interfaces to be compatible
4. Add adapter/bridge pattern if needed
5. Update all call sites

---

"""
            
            # 5. SUMMARY
            content += """## Implementation Priority

> Recommended order for addressing these issues:

1. **Integration Conflicts** - Fix first to unblock other work
2. **Integration Gaps** - Wire up components to enable functionality
3. **High Complexity** - Refactor to improve maintainability
4. **Dead Code** - Remove to reduce cognitive load

## Notes for Implementers

- Always run tests after each change
- Commit frequently with clear messages
- Update documentation as you go
- Ask for code review on complex refactorings
- Use feature flags for risky changes

---

*This document is automatically updated by the Planning phase based on detailed codebase analysis.*
"""
            
            tertiary_path.write_text(content)
            self.logger.info("  📝 Updated TERTIARY_OBJECTIVES.md with specific implementation details")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update TERTIARY_OBJECTIVES: {e}")
    def _update_architecture_doc(self, analysis_results: Dict):
        """Update ARCHITECTURE.md with INTENDED design and track drift from ACTUAL design"""
        try:
            arch_path = self.project_dir / 'ARCHITECTURE.md'
            
            # Read MASTER_PLAN to extract INTENDED architecture
            master_plan_path = self.project_dir / 'MASTER_PLAN.md'
            master_plan = ""
            if master_plan_path.exists():
                master_plan = master_plan_path.read_text()
            
            # ARCHITECTURE.md is a strategic document tracking INTENDED vs ACTUAL design
            content = f"""# Architecture Document

> **Purpose**: Track INTENDED architectural design and monitor drift from ACTUAL implementation
> **Updated By**: Planning phase (intended design), Refactoring phase (actual design adjustments)
> **Last Updated**: {self.format_timestamp()}

---

## INTENDED Architecture

> This section represents the DESIRED architectural design from MASTER_PLAN.
> Planning phase updates this based on strategic objectives.
> This is what we WANT the codebase to look like.

"""
            
            # Extract intended architecture from MASTER_PLAN
            if master_plan:
                import re
                
                # Look for architecture section
                arch_match = re.search(r'##\s+Architecture\s*\n(.*?)(?=\n##|\Z)', master_plan, re.DOTALL | re.IGNORECASE)
                if arch_match:
                    intended_arch = arch_match.group(1).strip()
                    content += intended_arch + "\n\n"
                else:
                    # Look for structure/design section
                    structure_match = re.search(r'##\s+(?:Structure|Design|Components)\s*\n(.*?)(?=\n##|\Z)', master_plan, re.DOTALL | re.IGNORECASE)
                    if structure_match:
                        intended_arch = structure_match.group(1).strip()
                        content += intended_arch + "\n\n"
                    else:
                        content += "### Components\n\n"
                        content += "<!-- Define intended components and their responsibilities -->\n"
                        content += "<!-- Planning phase will extract from MASTER_PLAN -->\n\n"
                        
                        content += "### Directory Structure\n\n"
                        content += "<!-- Define intended directory organization -->\n"
                        content += "<!-- Planning phase will extract from MASTER_PLAN -->\n\n"
            else:
                content += "### Components\n\n"
                content += "<!-- No MASTER_PLAN.md found - define intended components -->\n\n"
                
                content += "### Directory Structure\n\n"
                content += "<!-- No MASTER_PLAN.md found - define intended structure -->\n\n"
            
            content += """---

## ACTUAL Architecture

> This section represents the CURRENT implementation state.
> Automatically analyzed from codebase.
> This is what the codebase ACTUALLY looks like right now.

### Current Components

"""
            
            # Analyze actual architecture from codebase
            from pathlib import Path
            
            # Get all Python files
            py_files = list(self.project_dir.rglob("*.py"))
            
            # Group by top-level directory
            components = {}
            for py_file in py_files:
                try:
                    rel_path = py_file.relative_to(self.project_dir)
                    parts = rel_path.parts
                    if len(parts) > 0 and not parts[0].startswith('.'):
                        component = parts[0]
                        if component not in components:
                            components[component] = []
                        components[component].append(str(rel_path))
                except ValueError:
                    continue
            
            # List actual components
            for component, files in sorted(components.items()):
                content += f"**{component}/** ({len(files)} files)\n"
            
            content += "\n### Current Metrics\n\n"
            
            # Import integration point checker
            from pipeline.analysis.integration_points import is_integration_point
            
            # Add complexity summary
            if analysis_results.get('complexity_issues'):
                high_complexity = [i for i in analysis_results['complexity_issues'] if i['complexity'] >= 30]
                content += f"**High Complexity Functions**: {len(high_complexity)}\n"
                if high_complexity:
                    content += "\nTop complexity issues:\n"
                    for issue in high_complexity[:5]:
                        content += f"- `{issue['file']}::{issue['function']}` (complexity: {issue['complexity']})\n"
                    content += "\n"
            
            # Add dead code summary (filtered for integration points)
            if analysis_results.get('dead_code'):
                # Filter out integration points
                real_dead_code = []
                for issue in analysis_results['dead_code']:
                    if not is_integration_point(issue['file'], issue['type'], issue['name']):
                        real_dead_code.append(issue)
                
                if real_dead_code:
                    content += f"**Dead Code Items**: {len(real_dead_code)}\n"
                    content += "\nUnused components:\n"
                    for issue in real_dead_code[:5]:
                        content += f"- `{issue['file']}::{issue['name']}` ({issue['type']})\n"
                    content += "\n"
            
            # Add integration gaps summary (filtered for known integration points)
            if analysis_results.get('integration_gaps'):
                # Filter out known integration points
                real_gaps = []
                for issue in analysis_results['integration_gaps']:
                    if not is_integration_point(issue['file'], 'class', issue.get('class', '')):
                        real_gaps.append(issue)
                
                if real_gaps:
                    content += f"**Integration Gaps**: {len(real_gaps)} (filtered from {len(analysis_results['integration_gaps'])} total)\n"
                    content += "\nUnintegrated components:\n"
                    for issue in real_gaps[:5]:
                        content += f"- `{issue['file']}::{issue['class']}` (line {issue['line']})\n"
                    content += "\n"
            
            content += """---

## Architectural Drift

> Differences between INTENDED and ACTUAL architecture.
> These represent work needed to align implementation with design.

"""
            
            # Calculate drift - priority issues that need addressing
            all_issues = []
            if analysis_results.get('complexity_issues'):
                all_issues.extend([('complexity', i) for i in analysis_results['complexity_issues'][:5]])
            if analysis_results.get('integration_gaps'):
                # Only include real gaps, not integration points
                real_gaps = [i for i in analysis_results['integration_gaps'] 
                           if not is_integration_point(i['file'], 'class', i.get('class', ''))]
                all_issues.extend([('integration', i) for i in real_gaps[:5]])
            
            if all_issues:
                content += "### Priority Alignment Tasks\n\n"
                for issue_type, issue in all_issues:
                    if issue_type == 'complexity':
                        content += f"- **Refactor**: `{issue['file']}::{issue['function']}` (complexity {issue['complexity']})\n"
                    elif issue_type == 'integration':
                        content += f"- **Integrate**: `{issue['file']}::{issue['class']}` (line {issue['line']})\n"
            else:
                content += "✅ No significant drift detected - implementation aligns with intended design.\n"
            
            arch_path.write_text(content)
            self.logger.info("  📝 Updated ARCHITECTURE.md (INTENDED vs ACTUAL design)")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update ARCHITECTURE: {e}")
    
    def _update_primary_objectives(self, state: PipelineState):
        """Update PRIMARY_OBJECTIVES.md with actual objectives from MASTER_PLAN"""
        try:
            primary_path = self.project_dir / 'PRIMARY_OBJECTIVES.md'
            
            # Read MASTER_PLAN to extract objectives
            master_plan_path = self.project_dir / 'MASTER_PLAN.md'
            master_plan = ""
            if master_plan_path.exists():
                master_plan = master_plan_path.read_text()
            
            content = f"""# Primary Objectives

> **Purpose**: Core functional requirements and features
> **Updated By**: Planning phase (based on MASTER_PLAN)
> **Read By**: All phases
> **Last Updated**: {self.format_timestamp()}

## Core Features

"""
            
            # Extract features from MASTER_PLAN
            if master_plan:
                # Look for features section
                import re
                features_match = re.search(r'##\s+Features?\s*\n(.*?)(?=\n##|\Z)', master_plan, re.DOTALL | re.IGNORECASE)
                if features_match:
                    features_text = features_match.group(1).strip()
                    content += features_text + "\n\n"
                else:
                    content += "<!-- Extract from MASTER_PLAN.md -->\n\n"
            else:
                content += "<!-- No MASTER_PLAN.md found -->\n\n"
            
            content += """## Functional Requirements

"""
            
            # Extract requirements from MASTER_PLAN
            if master_plan:
                requirements_match = re.search(r'##\s+Requirements?\s*\n(.*?)(?=\n##|\Z)', master_plan, re.DOTALL | re.IGNORECASE)
                if requirements_match:
                    requirements_text = requirements_match.group(1).strip()
                    content += requirements_text + "\n\n"
                else:
                    content += "<!-- Extract from MASTER_PLAN.md -->\n\n"
            else:
                content += "<!-- No MASTER_PLAN.md found -->\n\n"
            
            content += """## Success Criteria

"""
            
            # Extract success criteria from MASTER_PLAN
            if master_plan:
                success_match = re.search(r'##\s+Success\s+Criteria\s*\n(.*?)(?=\n##|\Z)', master_plan, re.DOTALL | re.IGNORECASE)
                if success_match:
                    success_text = success_match.group(1).strip()
                    content += success_text + "\n\n"
                else:
                    # Calculate from task completion
                    total_tasks = len(state.tasks)
                    completed_tasks = len([t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED])
                    content += f"- Complete all {total_tasks} planned tasks\n"
                    content += f"- Current progress: {completed_tasks}/{total_tasks} tasks completed\n\n"
            else:
                content += "<!-- Define based on MASTER_PLAN.md goals -->\n\n"
            
            content += """---
*This document is automatically updated by the Planning phase based on MASTER_PLAN analysis.*
"""
            
            primary_path.write_text(content)
            self.logger.info("  📝 Updated PRIMARY_OBJECTIVES.md")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update PRIMARY_OBJECTIVES: {e}")
    
    def _update_secondary_objectives(self, analysis_results: Dict, phase_outputs: Dict):
        """Update SECONDARY_OBJECTIVES.md with architectural changes and QA feedback"""
        try:
            secondary_path = self.project_dir / 'SECONDARY_OBJECTIVES.md'
            
            content = f"""# Secondary Objectives

> **Purpose**: Architectural changes, testing requirements, reported failures
> **Updated By**: Planning phase (based on analysis and QA feedback)
> **Read By**: All phases
> **Last Updated**: {self.format_timestamp()}

## Architectural Changes Needed

"""
            
            # Add complexity issues
            if analysis_results.get('complexity_issues'):
                high_complexity = [i for i in analysis_results['complexity_issues'] if i['complexity'] >= 30]
                if high_complexity:
                    content += f"### High Complexity Functions ({len(high_complexity)} found)\n\n"
                    for issue in high_complexity[:10]:
                        content += f"- Refactor `{issue['file']}::{issue['function']}` (complexity: {issue['complexity']})\n"
                    content += "\n"
            
            # Add integration gaps
            from pipeline.analysis.integration_points import is_integration_point
            if analysis_results.get('integration_gaps'):
                real_gaps = [i for i in analysis_results['integration_gaps'] 
                           if not is_integration_point(i['file'], 'class', i.get('class', ''))]
                if real_gaps:
                    content += f"### Integration Gaps ({len(real_gaps)} found)\n\n"
                    for issue in real_gaps[:10]:
                        content += f"- Wire up `{issue['file']}::{issue['class']}` (line {issue['line']})\n"
                    content += "\n"
            
            if not analysis_results.get('complexity_issues') and not analysis_results.get('integration_gaps'):
                content += "No architectural changes needed at this time.\n\n"
            
            content += """## Testing Requirements

"""
            
            # Extract testing needs from QA output
            qa_output = phase_outputs.get('qa', '')
            if qa_output and 'test' in qa_output.lower():
                content += "### From QA Analysis\n\n"
                # Extract test-related lines
                import re
                test_lines = [line for line in qa_output.split('\n') if 'test' in line.lower()]
                for line in test_lines[:10]:
                    if line.strip():
                        content += f"- {line.strip()}\n"
                content += "\n"
            else:
                content += "No specific testing requirements identified.\n\n"
            
            content += """## Reported Failures

"""
            
            # Extract failures from QA and debugging outputs
            qa_output = phase_outputs.get('qa', '')
            debug_output = phase_outputs.get('debugging', '')
            
            failures_found = False
            
            if qa_output and ('error' in qa_output.lower() or 'fail' in qa_output.lower()):
                content += "### From QA Phase\n\n"
                import re
                error_lines = [line for line in qa_output.split('\n') 
                             if 'error' in line.lower() or 'fail' in line.lower()]
                for line in error_lines[:10]:
                    if line.strip():
                        content += f"- {line.strip()}\n"
                        failures_found = True
                content += "\n"
            
            if debug_output and ('error' in debug_output.lower() or 'fail' in debug_output.lower()):
                content += "### From Debugging Phase\n\n"
                import re
                error_lines = [line for line in debug_output.split('\n') 
                             if 'error' in line.lower() or 'fail' in debug_output.lower()]
                for line in error_lines[:10]:
                    if line.strip():
                        content += f"- {line.strip()}\n"
                        failures_found = True
                content += "\n"
            
            if not failures_found:
                content += "No failures reported.\n\n"
            
            content += """## Integration Issues

"""
            
            # Add integration conflicts
            if analysis_results.get('integration_conflicts'):
                content += f"### Integration Conflicts ({len(analysis_results['integration_conflicts'])} found)\n\n"
                for issue in analysis_results['integration_conflicts'][:10]:
                    content += f"- {issue.get('description', 'Unknown conflict')}\n"
                content += "\n"
            else:
                content += "No integration issues detected.\n\n"
            
            content += """---
*This document is automatically updated by the Planning phase based on codebase analysis.*
"""
            
            secondary_path.write_text(content)
            self.logger.info("  📝 Updated SECONDARY_OBJECTIVES.md")
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to update SECONDARY_OBJECTIVES: {e}")
    
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
    
    # ========== ARCHITECTURE-AWARE PLANNING METHODS ==========
    
    def _publish_architecture_events(self, validation, diff):
        """
        Publish architecture events via message bus.
        
        Args:
            validation: ValidationReport
            diff: ArchitectureDiff
        """
        if not self.message_bus:
            return
        
        from ..messaging import Message, MessageType, MessagePriority
        
        # Publish validation event
        self.message_bus.publish(
            Message(
                sender=self.phase_name,
                recipient="broadcast",
                message_type=MessageType.SYSTEM_ALERT,
                priority=MessagePriority.HIGH,
                payload={
                    'type': 'architecture_validated',
                    'is_consistent': validation.is_consistent,
                    'severity': validation.severity.value,
                    'missing_components': validation.missing_components,
                    'integration_gaps': len(validation.integration_gaps)
                }
            )
        )
        
        # Publish drift detection if not consistent
        if not validation.is_consistent:
            Message(
                sender=self.phase_name,
                recipient="broadcast",
                message_type=MessageType.SYSTEM_ALERT,
                priority=MessagePriority.HIGH,
                payload={
                    'type': 'architecture_drift_detected',
                    'severity': validation.severity.value,
                    'missing_components': validation.missing_components,
                    'integration_gaps': len(validation.integration_gaps)
                }
            )
        
        # Publish component events
        for component in validation.missing_components:
            Message(
                sender=self.phase_name,
                recipient="broadcast",
                message_type=MessageType.SYSTEM_ALERT,
                priority=MessagePriority.HIGH,
                payload={
                    'type': 'architecture_component_missing',
                    'component': component
                }
            )
        
        # Publish architecture update event
        if diff.has_changes():
            Message(
                sender=self.phase_name,
                recipient="broadcast",
                message_type=MessageType.SYSTEM_ALERT,
                priority=MessagePriority.HIGH,
                payload={
                    'type': 'architecture_updated',
                    'added': len(diff.added),
                    'removed': len(diff.removed),
                    'modified': len(diff.modified),
                    'moved': len(diff.moved)
                }
            )
    
    def _create_architecture_tasks(self, validation, diff):
        """
        Create tasks to fix architecture issues.
        
        Priority order:
        1. CRITICAL: Missing required components
        2. HIGH: Misplaced components
        3. MEDIUM: Integration gaps
        4. LOW: Naming violations
        
        Args:
            validation: ValidationReport
            diff: ArchitectureDiff
            
        Returns:
            List of TaskState objects
        """
        from ..state.manager import TaskState, TaskStatus
        from ..state.priority import TaskPriority
        
        tasks = []
        
        # 1. CRITICAL: Missing components
        for component in validation.missing_components:
            task = TaskState(
                task_id=f"arch_missing_{component}",
                description=f"Create missing component: {component}",
                target_file=f"{component.replace('.', '/')}.py",
                status=TaskStatus.NEW,
                priority=TaskPriority.CRITICAL,
                created_at=datetime.now().isoformat()
            )
            tasks.append(task)
        
        # 2. HIGH: Misplaced components
        for issue in validation.misplaced_components:
            task = TaskState(
                task_id=f"arch_misplaced_{issue.component}",
                description=f"Move {issue.component} to correct location: {issue.expected_location}",
                target_file=issue.current_location,
                status=TaskStatus.NEW,
                priority=TaskPriority.HIGH,
                created_at=datetime.now().isoformat()
            )
            tasks.append(task)
        
        # 3. MEDIUM: Integration gaps (limit to top 5)
        for gap in validation.integration_gaps[:5]:
            task = TaskState(
                task_id=f"arch_integration_{gap.component}",
                description=f"Integrate component {gap.component}: {gap.reason}",
                target_file=f"{gap.component.replace('.', '/')}.py",
                status=TaskStatus.NEW,
                priority=TaskPriority.SECONDARY_FEATURES,
                created_at=datetime.now().isoformat()
            )
            tasks.append(task)
        
        # Store validation for use in message building
        self._current_validation = validation
        
        return tasks
