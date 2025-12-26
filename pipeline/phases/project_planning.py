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
from ..logging_setup import get_logger


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
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute project planning phase"""
        
        self.logger.info("  📊 Analyzing project for expansion opportunities...")
        
        # Check expansion health
        if not self._check_expansion_health(state):
            self.logger.warning("  ⚠️ Expansion paused - entering maintenance mode")
            return self._create_maintenance_result(state)
        
        # Ensure ARCHITECTURE.md exists
        self._ensure_architecture_exists()
        
        # Gather complete project context
        context = self._gather_complete_context(state)
        
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
        
        # Call LLM with project planning tools from centralized tools.py
        self.logger.debug(f"  Calling LLM with {len(TOOLS_PROJECT_PLANNING)} tools")
        self.logger.debug(f"  Tools: {[t['function']['name'] for t in TOOLS_PROJECT_PLANNING]}")
        
        response = self.chat(
            messages=messages,
            tools=TOOLS_PROJECT_PLANNING,
            task_type="planning"  # Use planning model (qwen2.5:14b)
        )
        
        if "error" in response:
            self.logger.error(f"  LLM error: {response['error']}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"LLM error: {response['error']}"
            )
        
        # Log response structure for debugging
        self.logger.debug(f"  Response keys: {list(response.keys())}")
        if "message" in response:
            msg = response["message"]
            self.logger.debug(f"  Message keys: {list(msg.keys()) if isinstance(msg, dict) else 'not a dict'}")
            if isinstance(msg, dict) and "tool_calls" in msg:
                self.logger.debug(f"  Tool calls in message: {len(msg['tool_calls']) if msg['tool_calls'] else 0}")
            if isinstance(msg, dict) and "content" in msg:
                content_preview = str(msg["content"])[:200] if msg["content"] else "empty"
                self.logger.debug(f"  Content preview: {content_preview}")
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No tool calls in response")
            if content:
                self.logger.warning(f"  Response content (first 500 chars): {content[:500]}...")
                self.logger.warning(f"  Response content (last 500 chars): ...{content[-500:]}")
            
            # Log the full response for debugging
            self.logger.debug(f"  Full response: {response}")
            
            # Check if response contains tool-like patterns
            if "analyze_project_status" in content or "propose_expansion_tasks" in content:
                self.logger.error("  Response contains tool names but parser failed to extract them!")
                self.logger.error("  This indicates a parsing issue, not a model issue")
            
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to generate expansion plan - no tool calls in response",
                metadata={
                    "response_length": len(content) if content else 0,
                    "has_content": bool(content),
                    "content_preview": content[:200] if content else None
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
            
            self.logger.info(f"    → {task_id}: {task.description[:50]}...")
        
        # Apply architecture updates if any
        if architecture_updates:
            self._apply_architecture_updates(architecture_updates)
        
        # Update expansion tracking in state
        state.expansion_count = getattr(state, 'expansion_count', 0) + 1
        
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
        
        # 1. MASTER_PLAN.md (full content - this is the source of truth)
        master_plan = self.project_dir / "MASTER_PLAN.md"
        if master_plan.exists():
            content = master_plan.read_text()
            context_parts.append(f"# MASTER_PLAN.md\n\n{content}")
        else:
            context_parts.append("# MASTER_PLAN.md\n\n(NOT FOUND - this is required!)")
        
        # 2. ARCHITECTURE.md (full content)
        arch = self.project_dir / "ARCHITECTURE.md"
        if arch.exists():
            content = arch.read_text()
            context_parts.append(f"# ARCHITECTURE.md\n\n{content}")
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
        self.logger.info("  📄 Created ARCHITECTURE.md")
    
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
