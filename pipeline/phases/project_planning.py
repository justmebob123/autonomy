import time
"""
Project Planning Phase

Analyzes the project when all tasks are complete and creates
new expansion tasks based on MASTER_PLAN objectives and ARCHITECTURE.

This phase ensures the pipeline runs continuously by always finding
new work to do - either expanding features or improving quality.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..prompts import SYSTEM_PROMPTS, get_project_planning_prompt
from ..tools import TOOLS_PROJECT_PLANNING
from ..handlers import ToolCallHandler
from pipeline.logging_setup import get_logger
from ..text_tool_parser import TextToolParser
from ..objective_file_generator import ObjectiveFileGenerator

from ..orchestration.specialists.reasoning_specialist import ReasoningType

class ProjectPlanningPhase(LoopDetectionMixin, BasePhase):
    """
    Project expansion planning phase.
    
    Triggers when all current tasks are complete.
    Analyzes the codebase against MASTER_PLAN and ARCHITECTURE,
    then creates new tasks for project expansion.
    
    This phase ensures the pipeline NEVER exits - it always finds
    new work to do.
    """
    
    phase_name = "project_planning"
    
    # Limits to prevent runaway expansion
    MAX_TASKS_PER_CYCLE = 5
    MAX_EXPANSION_CYCLES = 999999  # UNLIMITED expansion cycles
    
    def __init__(self, *args, **kwargs):
        """Initialize with loop detection"""
        BasePhase.__init__(self, *args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_COMPLETED,
                MessageType.OBJECTIVE_ACTIVATED,
                MessageType.SYSTEM_ALERT,  # Use SYSTEM_ALERT for architecture changes
            ])
            self.logger.info("  📡 Message bus subscriptions configured")
        
        
        # CORE ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.complexity import ComplexityAnalyzer
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_gaps import IntegrationGapFinder
        from ..analysis.call_graph import CallGraphGenerator
        from ..tool_modules.file_updates import FileUpdateTools
        
        self.complexity_analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger)
        self.gap_finder = IntegrationGapFinder(str(self.project_dir), self.logger)
        self.call_graph = CallGraphGenerator(str(self.project_dir), self.logger)
        self.file_updater = FileUpdateTools(str(self.project_dir), self.logger)
        
        self.logger.debug("  📋 Project Planning phase initialized with comprehensive analysis capabilities")
        self.text_parser = TextToolParser()
        self.objective_generator = ObjectiveFileGenerator(self.project_dir)
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute project planning phase"""
        
        
        # ADAPTIVE PROMPTS: Update system prompt based on recent planning
        if self.adaptive_prompts:
            self.update_system_prompt_with_adaptation({
                'state': state,
                'phase': self.phase_name,
                'expansion_count': state.expansion_count if hasattr(state, 'expansion_count') else 0,
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
        
        # ARCHITECTURE INTEGRATION: Read architecture for project structure
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives for expansion priorities
        objectives = self._read_objectives()
        if objectives:
            pass
        
        # IPC INTEGRATION: Write status at start
        self._write_status({
            "status": "Starting project planning",
            "action": "start",
            "expansion_cycle": state.metadata.get('expansion_cycles', 0)
        })
        
        # INITIALIZE IPC DOCUMENTS (if first run)
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS for context
        strategic_docs = self.read_strategic_docs()
        master_plan = strategic_docs.get('MASTER_PLAN.md', '')
        architecture_doc = strategic_docs.get('ARCHITECTURE.md', '')
        primary_objectives = strategic_docs.get('PRIMARY_OBJECTIVES.md', '')
        secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')
        
        # Store as instance variables for use in helper methods
        self._master_plan_content = master_plan
        self._architecture_content = architecture_doc
        self._primary_objectives_content = primary_objectives
        self._secondary_objectives_content = secondary_objectives
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS for context
        planning_output = self.read_phase_output('planning')
        documentation_output = self.read_phase_output('documentation')
        
        # Check expansion health
        if not self._check_expansion_health(state):
            return self._create_maintenance_result(state)
        
        # Ensure ARCHITECTURE.md exists (will use strategic docs)
        self._ensure_architecture_exists()
        
        # Gather complete project context (now includes strategic docs)
        context = self._gather_complete_context(state)
        
        # ANALYSIS INTEGRATION: Analyze entire codebase for planning
        analysis_summary = self._analyze_codebase_for_planning()
        if analysis_summary:
            context += "\n\n" + analysis_summary
        
        # Get counts for prompt
        expansion_count = getattr(state, 'expansion_count', 0)
        completed_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        total_tasks = len(state.tasks)
        
        # Build planning messages using centralized prompts
        messages = [
            {"role": "system", "content": self._get_system_prompt("project_planning")},
            {"role": "user", "content": get_project_planning_prompt(
                context, expansion_count, completed_count, total_tasks
            )}
        ]
        
        # Use reasoning specialist for project planning
        from ..orchestration.specialists.reasoning_specialist import ReasoningTask
        
        self.logger.info("  Using ReasoningSpecialist for project planning...")
        reasoning_task = ReasoningTask(
            reasoning_type=ReasoningType.STRATEGIC_PLANNING,
            question="Expand project with new features",
            context={
                'project_context': context,
                'expansion_count': expansion_count,
                'completed_count': completed_count,
                'total_tasks': total_tasks
            }
        )
        
        specialist_result = self.reasoning_specialist.execute_task(reasoning_task)
        
        if not specialist_result.get("success", False):
            error_msg = specialist_result.get("response", "Specialist project planning failed")
            self.logger.error(f"  Specialist error: {error_msg}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Project planning failed: {error_msg}"
            )
        
        # Extract tool calls and content
        tool_calls = specialist_result.get("tool_calls", [])
        content = specialist_result.get("response", "")
        
        self.logger.debug(f"  Tool calls from specialist: {len(tool_calls)}")
        if content:
            self.logger.debug(f"  Content preview: {content[:200]}")
        
        if not tool_calls:
            self.logger.warning("  No tool calls in response")
            if content:
                self.logger.warning(f"  Response content (first 500 chars): {content[:500]}...")
                self.logger.warning(f"  Response content (last 500 chars): ...{content[-500:]}")
            
            # Log the full response for debugging
            self.logger.debug(f"  Full specialist result: {specialist_result}")
            
            # Check if response contains tool-like patterns
            if "analyze_project_status" in content or "propose_expansion_tasks" in content:
                self.logger.error("  Response contains tool names but parser failed to extract them!")
                self.logger.error("  This indicates a parsing issue, not a model issue")
            
            # FALLBACK: Try to extract tasks from text response
            if content:
                self.logger.info("  🔄 Attempting to extract tasks from text response...")
                self.logger.debug(f"  Content length: {len(content)} chars")
                
                tasks = self.text_parser.parse_project_planning_response(content)
                
                if tasks:
                    for i, task in enumerate(tasks, 1):
                        self.logger.debug(f"    Task {i}: {task['description'][:50]}... -> {task['target_file']}")
                    
                    # Convert to tool call format
                    tool_calls = self.text_parser.create_tool_calls_from_tasks(tasks)
                    # Continue with normal processing below
                else:
                    self.logger.warning("  ✗ Could not extract tasks from text response")
                    self.logger.debug("  Debugging extraction failure:")
                    
                    # Debug: Check for patterns
                    import re
                    numbered = re.findall(r'(?:^|\n)\s*\d+\.\s*', content, re.MULTILINE)
                    files = re.findall(r'([a-zA-Z0-9_/]+\.py)', content)
                    self.logger.debug(f"    Numbered items found: {len(numbered)}")
                    self.logger.debug(f"    Python files found: {len(files)}")
                    if files:
                        self.logger.debug(f"    Files: {files[:5]}")
                    return PhaseResult(
                        success=False,
                        phase=self.phase_name,
                        message="Failed to generate expansion plan - no tool calls in response",
                        data={
                            "response_length": len(content) if content else 0,
                            "has_content": bool(content),
                            "content_preview": content[:200] if content else None
                        }
                    )
            else:
                return PhaseResult(
                    success=False,
                    phase=self.phase_name,
                    message="Failed to generate expansion plan - no tool calls and no content",
                    data={
                        "response_length": 0,
                        "has_content": False,
                        "content_preview": None
                    }
                )
        
        # Check for loops before processing
        if self.check_for_loops():
            self.logger.warning("  Loop detected in project planning phase")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Loop detected - stopping to prevent infinite cycle"
            )
        
        # Process tool calls using ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)

        # Track tool calls for loop detection
        self.track_tool_calls(tool_calls, results)
        
        # Extract new tasks from handler results
        new_tasks = []
        if hasattr(handler, 'tasks') and handler.tasks:
            new_tasks = handler.tasks[:self.MAX_TASKS_PER_CYCLE]
            self.logger.info(f"  📝 Generated {len(new_tasks)} expansion tasks")
        
        project_status = None
        architecture_updates = []
        
        # Create new tasks in state
        tasks_created = []
        created_task_objects = []
        base_id = len(state.tasks) + 1
        
        for i, task_data in enumerate(new_tasks):
            task_id = f"task_{base_id + i:03d}"
            
            task = TaskState(
                task_id=task_id,
                description=task_data["description"],
                target_file=self._normalize_path(task_data["target_file"]),
                priority=task_data.get("priority", 50),
                dependencies=task_data.get("dependencies", []),
                status=TaskStatus.NEW,
                created_at=datetime.now().isoformat()
            )
            
            state.tasks[task_id] = task
            tasks_created.append(task_id)
            created_task_objects.append(task)
            
            self.logger.info(f"    → {task_id}: {task.description[:50]}...")
        
        # Generate objective files from tasks and context
        if created_task_objects and context:
            try:
                objective_files = self.objective_generator.generate_objective_files(
                    state, context, created_task_objects
                )
                
                if objective_files:
                    pass
                    # Write objective files to disk
                    created_files = self.objective_generator.write_objective_files(objective_files)
                    
                    # Link tasks to objectives
                    linked_count = self.objective_generator.link_tasks_to_objectives(
                        state, objective_files
                    )
                    
                    if linked_count > 0:
                        self.logger.info(f"  🔗 Linked {linked_count} tasks to objectives")
                else:
                    self.logger.debug("  ℹ️ No objectives extracted from context")
            except Exception as e:
                pass
                # Continue anyway - objective files are optional
        
        # Apply architecture updates if any
        if architecture_updates:
            self._apply_architecture_updates(architecture_updates)
        
        # Update expansion tracking in state
        state.expansion_count = getattr(state, 'expansion_count', 0) + 1
        
        # WRITE STATUS to PROJECT_PLANNING_WRITE.md
        status_content = f"""# Project Planning Phase Status

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Expansion Cycle
- Cycle Number: {state.expansion_count}
- Tasks Created: {len(tasks_created)}
- Focus Area: {new_tasks[0].get("category", "general") if new_tasks else "none"}

## New Tasks
{chr(10).join(f"- {task.get('description', 'No description')}" for task in new_tasks[:5])}

## Architecture Updates
{chr(10).join(f"- {update}" for update in architecture_updates) if architecture_updates else "- No architecture updates"}

## Next Steps
- Planning phase will refine these tasks
- Coding phase will implement
"""
        self.write_own_status(status_content)
        
        # SEND MESSAGES to other phases
        if tasks_created:
            self.send_message_to_phase('planning', f"Created {len(tasks_created)} new expansion tasks for cycle {state.expansion_count}")
            
            # PATTERN RECOGNITION: Record expansion pattern
            self.record_execution_pattern({
                'pattern_type': 'expansion_planning',
                'tasks_created': len(tasks_created),
                'success': True
            })
            
            # ANALYTICS: Track expansion metric
            self.track_phase_metric({
                'metric': 'expansion_planned',
                'tasks_created': len(tasks_created)
            })
        
        # IPC INTEGRATION: Write completion status
        self._write_status({
            "status": "Project planning completed",
            "action": "complete",
            "tasks_created": len(tasks_created),
            "expansion_count": state.expansion_count,
            "focus": new_tasks[0].get("category", "general") if new_tasks else "none"
        })
        
        # ARCHITECTURE INTEGRATION: Update architecture with new planned components
        if architecture and tasks_created:
            for task_data in tasks_created:
                if 'target_file' in task_data:
                    self._update_architecture(
                        'planned_components',
                        f"Planned: {task_data.get('description', 'New component')}",
                        f"Project Planning: Added {task_data['target_file']}"
                    )
        
        # MESSAGE BUS: Publish phase completion
        self._publish_message('PHASE_COMPLETED', {
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'tasks_created': len(tasks_created),
            'expansion_count': state.expansion_count
        })
        
        return PhaseResult(
            success=len(tasks_created) > 0,
            phase=self.phase_name,
            message=f"Created {len(tasks_created)} expansion tasks",
            data={
                "tasks_created": tasks_created,
                "expansion_count": state.expansion_count,
                "focus": new_tasks[0].get("category", "general") if new_tasks else "none"
            }
        )
    
    def _gather_complete_context(self, state: PipelineState) -> str:
        """Gather complete project context for planning"""
        context_parts = []
        
        # Use strategic docs already read at start of execute()
        # These are available as instance variables from execute()
        
        # 1. MASTER_PLAN.md (full content - this is the source of truth)
        if hasattr(self, '_master_plan_content') and self._master_plan_content:
            context_parts.append(f"# MASTER_PLAN.md\n\n{self._master_plan_content}")
        else:
            context_parts.append("# MASTER_PLAN.md\n\n(NOT FOUND - this is required!)")
        
        # 2. ARCHITECTURE.md (full content)
        if hasattr(self, '_architecture_content') and self._architecture_content:
            context_parts.append(f"# ARCHITECTURE.md\n\n{self._architecture_content}")
        else:
            context_parts.append("# ARCHITECTURE.md\n\n(Not yet created - will be generated)")
        
        # 3. README.md (for context)
        readme = self.project_dir / "README.md"
        if readme.exists():
            content = readme.read_text()
            if len(content) > 5000:
                content = content[:5000] + "\n\n... (truncated)"
            context_parts.append(f"# README.md\n\n{content}")
        
        # 4. All Python files with structure
        py_files = sorted(self.project_dir.rglob("*.py"))
        file_summaries = []
        
        for py_file in py_files:
            rel_path = py_file.relative_to(self.project_dir)
            if ".pipeline" in str(rel_path) or "__pycache__" in str(rel_path):
                continue
            
            try:
                content = py_file.read_text()
                size = len(content)
                
                if size < 3000:
                    file_summaries.append(f"## FILE: {rel_path} ({size} bytes)\n\n```python\n{content}\n```")
                else:
                    structure = self._extract_file_structure(content)
                    file_summaries.append(f"## FILE: {rel_path} ({size} bytes) - STRUCTURE ONLY\n\n{structure}")
            except Exception as e:
                file_summaries.append(f"## FILE: {rel_path} - ERROR: {e}")
        
        if file_summaries:
            context_parts.append("# PROJECT FILES\n\n" + "\n\n---\n\n".join(file_summaries))
        else:
            context_parts.append("# PROJECT FILES\n\n(No Python files found)")
        
        # 5. Completed tasks summary
        completed = [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED]
        if completed:
            completed_list = "\n".join([
                f"- ✓ {t.description[:60]} → {t.target_file}"
                for t in sorted(completed, key=lambda x: x.task_id)
            ])
            context_parts.append(f"# COMPLETED TASKS ({len(completed)} total)\n\n{completed_list}")
        
        # 6. Failed/skipped tasks (to avoid repeating)
        skipped = [t for t in state.tasks.values() if t.status == TaskStatus.SKIPPED]
        if skipped:
            skipped_list = "\n".join([
                f"- ✗ {t.description[:60]} (failed {t.attempts} times)"
                for t in skipped
            ])
            context_parts.append(f"# SKIPPED TASKS (do not retry these)\n\n{skipped_list}")
        
        return "\n\n" + "="*60 + "\n\n".join(context_parts)
    
    def _extract_file_structure(self, content: str) -> str:
        """Extract class/function structure from Python file"""
        lines = []
        
        imports = []
        for line in content.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        if imports:
            lines.append("Imports: " + ", ".join(imports[:5]))
            if len(imports) > 5:
                lines.append(f"  ... and {len(imports) - 5} more imports")
        
        class_pattern = r'^class\s+(\w+)'
        func_pattern = r'^def\s+(\w+)'
        method_pattern = r'^\s{4}def\s+(\w+)'
        
        current_class = None
        
        for line in content.split('\n'):
            class_match = re.match(class_pattern, line)
            if class_match:
                current_class = class_match.group(1)
                lines.append(f"\nclass {current_class}:")
                continue
            
            func_match = re.match(func_pattern, line)
            if func_match:
                current_class = None
                lines.append(f"\ndef {func_match.group(1)}()")
                continue
            
            method_match = re.match(method_pattern, line)
            if method_match and current_class:
                lines.append(f"    def {method_match.group(1)}()")
        
        return "\n".join(lines) if lines else "(empty file)"
    
    def _validate_proposed_tasks(self, tasks: List[Dict], state: PipelineState) -> List[Dict]:
        """Validate and filter proposed tasks"""
        valid_tasks = []
        
        for task in tasks:
            if not all(k in task for k in ["description", "target_file", "priority"]):
                self.logger.warning(f"  Task missing required fields, skipping")
                continue
            
            target = self._normalize_path(task["target_file"])
            task["target_file"] = target
            
            if ".." in target:
                self.logger.warning(f"  Invalid path (traversal): {target}")
                continue
            
            if len(task["description"]) < 15:
                self.logger.warning(f"  Description too short: {task['description']}")
                continue
            
            if self._is_duplicate_task(task, state):
                self.logger.info(f"  Skipping duplicate: {task['description'][:40]}...")
                continue
            
            valid_tasks.append(task)
        
        return valid_tasks
    
    def _is_duplicate_task(self, new_task: Dict, state: PipelineState) -> bool:
        """Check if task duplicates an existing one"""
        new_target = new_task["target_file"].lower()
        new_desc = new_task["description"].lower()
        
        for existing in state.tasks.values():
            if existing.target_file.lower() == new_target:
                existing_words = set(existing.description.lower().split())
                new_words = set(new_desc.split())
                
                overlap = len(existing_words & new_words)
                total = len(existing_words | new_words)
                
                if total > 0 and overlap / total > 0.6:
                    return True
        
        return False
    
    def _normalize_path(self, filepath: str) -> str:
        """Normalize file path"""
        filepath = filepath.lstrip("/")
        filepath = filepath.replace("\\", "/")
        if filepath.startswith("./"):
            filepath = filepath[2:]
        return filepath
    
    def _check_expansion_health(self, state: PipelineState) -> bool:
        """Check if expansion should proceed"""
        expansion_count = getattr(state, 'expansion_count', 0)
        if expansion_count >= self.MAX_EXPANSION_CYCLES:
            self.logger.warning(f"  Reached max expansion cycles ({self.MAX_EXPANSION_CYCLES})")
            return False
        
        recent_tasks = list(state.tasks.values())[-20:]
        if len(recent_tasks) >= 10:
            failures = sum(1 for t in recent_tasks if t.status == TaskStatus.SKIPPED)
            if failures / len(recent_tasks) > 0.5:
                self.logger.warning(f"  High failure rate: {failures}/{len(recent_tasks)}")
                return False
        
        return True
    
    def _create_maintenance_result(self, state: PipelineState) -> PhaseResult:
        """Create result for maintenance mode"""
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Entering maintenance mode - high failure rate or expansion limit reached",
            data={"mode": "maintenance"}
        )
    
    def _ensure_architecture_exists(self) -> None:
        """Create ARCHITECTURE.md if it doesn't exist"""
        arch_path = self.project_dir / "ARCHITECTURE.md"
        
        if arch_path.exists():
            return
        
        master_plan = self.project_dir / "MASTER_PLAN.md"
        project_name = "Project"
        if master_plan.exists():
            content = master_plan.read_text()
            match = re.search(r'^#\s*(?:MASTER PLAN:?\s*)?(.+)$', content, re.MULTILINE)
            if match:
                project_name = match.group(1).strip()
        
        initial_arch = f"""# {project_name} - Architecture

> This document describes the architectural design and patterns used in this project.
> It is automatically maintained by the AI development pipeline.

---

## Overview

This document will be updated as the project evolves to reflect:
- Module structure and dependencies
- Design patterns in use
- Key abstractions and interfaces
- Data flow and component interactions

---

## Module Structure

(To be documented as modules are created)

---

## Design Patterns

(To be documented as patterns emerge)

---

## Key Decisions

(To be documented as decisions are made)

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        arch_path.write_text(initial_arch)
    
    def _apply_architecture_updates(self, updates: List[Dict]) -> None:
        """Apply updates to ARCHITECTURE.md"""
        arch_path = self.project_dir / "ARCHITECTURE.md"
        
        if not arch_path.exists():
            self._ensure_architecture_exists()
        
        content = arch_path.read_text()
        
        for update in updates:
            sections_to_add = update.get("sections_to_add", [])
            sections_to_update = update.get("sections_to_update", [])
            
            for section in sections_to_add:
                heading = section.get("heading", "")
                sect_content = section.get("content", "")
                
                if heading and sect_content:
                    new_section = f"\n## {heading}\n\n{sect_content}\n"
                    
                    if "**Last Updated**" in content:
                        content = content.replace(
                            "**Last Updated**",
                            f"{new_section}\n---\n\n**Last Updated**"
                        )
                    else:
                        content += new_section
                    
                    self.logger.info(f"    Added architecture section: {heading}")
            
            for section in sections_to_update:
                heading = section.get("heading", "")
                new_content = section.get("new_content", "")
                
                if heading and new_content:
                    pattern = rf'(## {re.escape(heading)}\n\n).*?(\n---|\n## |\Z)'
                    replacement = rf'\1{new_content}\n\2'
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    self.logger.info(f"    Updated architecture section: {heading}")
        
        content = re.sub(
            r'\*\*Last Updated\*\*:.*',
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
            content
        )
        
        arch_path.write_text(content)
    
    def _analyze_codebase_for_planning(self) -> str:
        """
        Analyze entire codebase to inform project planning decisions.
        
        Returns:
            Analysis summary as formatted string
        """
        
        analysis_parts = []
        analysis_parts.append("\n# Codebase Analysis for Planning\n")
        
        # Get all Python files
        py_files = sorted(self.project_dir.rglob("*.py"))
        py_files = [f for f in py_files if ".pipeline" not in str(f) and "__pycache__" not in str(f)]
        
        if not py_files:
            return ""
        
        # Aggregate statistics
        total_files = len(py_files)
        high_complexity_count = 0
        dead_code_count = 0
        total_complexity = 0
        
        for py_file in py_files[:20]:  # Limit to first 20 files
            try:
                rel_path = str(py_file.relative_to(self.project_dir))
                
                # Complexity analysis
                complexity_result = self.complexity_analyzer.analyze(rel_path)
                total_complexity += complexity_result.average_complexity
                
                if complexity_result.max_complexity >= 30:
                    high_complexity_count += 1
                
                # Dead code detection
                dead_code_result = self.dead_code_detector.analyze(rel_path)
                if dead_code_result.unused_functions or dead_code_result.unused_classes:
                    dead_code_count += 1
                    
            except Exception as e:
                self.logger.debug(f"  Analysis failed for {rel_path}: {e}")
                continue
        
        # Check for integration gaps (project-wide)
        integration_issues = 0
        try:
            gap_result = self.gap_finder.analyze()
            integration_issues = len(gap_result.unused_classes) + len(gap_result.missing_integrations)
        except Exception as e:
            self.logger.debug(f"  Integration gap analysis failed: {e}")
        
        # Format results
        analysis_parts.append(f"## Codebase Health Metrics\n")
        analysis_parts.append(f"- Total Python files analyzed: {min(total_files, 20)}")
        analysis_parts.append(f"- Average complexity: {total_complexity / min(total_files, 20):.1f}")
        analysis_parts.append(f"- Files with high complexity (≥30): {high_complexity_count}")
        analysis_parts.append(f"- Files with dead code: {dead_code_count}")
        analysis_parts.append(f"- Integration issues: {integration_issues}")
        analysis_parts.append("")
        
        # Recommendations
        if high_complexity_count > 0 or dead_code_count > 0 or integration_issues > 0:
            analysis_parts.append("## Planning Recommendations\n")
            if high_complexity_count > 0:
                analysis_parts.append(f"- Consider refactoring {high_complexity_count} high-complexity files")
            if dead_code_count > 0:
                analysis_parts.append(f"- Consider cleaning up {dead_code_count} files with dead code")
            if integration_issues > 0:
                analysis_parts.append(f"- Address {integration_issues} integration issues")
            analysis_parts.append("")
        
        return "\n".join(analysis_parts)
    
    def _log_project_status(self, status: Dict) -> None:
        """Log project status analysis"""
        completed = status.get("objectives_completed", [])
        in_progress = status.get("objectives_in_progress", [])
        pending = status.get("objectives_pending", [])
        focus = status.get("recommended_focus", "")
        
        self.logger.info(f"  📈 Project Status:")
        self.logger.info(f"      Completed: {len(completed)} objectives")
        self.logger.info(f"      In Progress: {len(in_progress)} objectives")
        self.logger.info(f"      Pending: {len(pending)} objectives")
        self.logger.info(f"      Focus: {focus}")
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown state file"""
        expansion_count = getattr(state, 'expansion_count', 0)
        completed = [t for t in state.tasks.values() if t.status == TaskStatus.COMPLETED]
        pending = [t for t in state.tasks.values() if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]]
        
        md = f"""# Project Planning State

**Last Run**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Expansion Cycle**: {expansion_count}

## Statistics

- Total Tasks Created: {len(state.tasks)}
- Completed: {len(completed)}
- Pending: {len(pending)}

## Recent Expansions

"""
        
        recent = sorted(state.tasks.values(), key=lambda t: t.created_at, reverse=True)[:10]
        for task in recent:
            status_icon = "✓" if task.status == TaskStatus.COMPLETED else "○"
            md += f"- {status_icon} {task.description[:50]}... → `{task.target_file}`\n"
        
        return md
