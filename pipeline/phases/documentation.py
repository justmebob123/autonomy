"""
Documentation Phase

Updates README.md and reviews ARCHITECTURE.md after development cycles.
Ensures documentation stays in sync with implementation.

This phase runs before project_planning to ensure docs are current
before planning new expansion tasks.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..prompts import SYSTEM_PROMPTS, get_documentation_prompt
from ..tools import TOOLS_DOCUMENTATION, get_tools_for_phase
from ..handlers import ToolCallHandler
from ..logging_setup import get_logger


class DocumentationPhase(LoopDetectionMixin, BasePhase):
    """
    Documentation update phase.
    
    Runs after tasks are completed to ensure README.md and ARCHITECTURE.md
    accurately reflect the current state of the project.
    """
    
    phase_name = "documentation"
    
    def __init__(self, *args, **kwargs):
        """Initialize with loop detection"""
        BasePhase.__init__(self, *args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        self.logger.info("  📝 Documentation phase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute documentation phase"""
        
        self.logger.info("  📝 Reviewing documentation...")
        
        # CHECK IF README EXISTS - if not, complete documentation task anyway
        readme_path = self.project_dir / "README.md"
        if not readme_path.exists():
            self.logger.warning("  ⚠️  README.md not found - marking documentation task complete")
            self.logger.info("  💡 Tip: Create README.md to enable documentation updates")
            
            # Find and complete any documentation tasks
            from ..state.manager import StateManager
            state_manager = StateManager(self.project_dir)
            
            doc_tasks_completed = 0
            for task_id, task in state.tasks.items():
                if task.status == TaskStatus.PENDING:
                    # Check if it's a documentation task
                    is_doc_task = False
                    if task.target and task.target.endswith('.md'):
                        is_doc_task = True
                    elif task.description:
                        doc_keywords = ['documentation', 'write docs', 'create docs', 'document', 'readme', 'guide']
                        desc_lower = task.description.lower()
                        if any(keyword in desc_lower for keyword in doc_keywords):
                            is_doc_task = True
                    
                    if is_doc_task:
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        doc_tasks_completed += 1
                        self.logger.info(f"  ✅ Marked documentation task complete: {task.description[:60]}")
            
            if doc_tasks_completed > 0:
                state_manager.save(state)
            
            # Update state to prevent re-entry
            completed_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
            state.last_doc_update_count = completed_count
            state_manager.save(state)
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"README.md not found - marked {doc_tasks_completed} documentation tasks complete",
                next_phase=None  # Let coordinator decide next phase
            )
        
        # INITIALIZE IPC DOCUMENTS (if first run)
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS for context
        strategic_docs = self.read_strategic_docs()
        master_plan = strategic_docs.get('MASTER_PLAN.md', '')
        architecture_doc = strategic_docs.get('ARCHITECTURE.md', '')
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS for context
        planning_output = self.read_phase_output('planning')
        coding_output = self.read_phase_output('coding')
        qa_output = self.read_phase_output('qa')
        
        # Check no-update count BEFORE processing
        from ..state.manager import StateManager
        state_manager = StateManager(self.project_dir)
        no_update_count = state_manager.get_no_update_count(state, self.phase_name)
        
        if no_update_count >= 3:
            self.logger.warning(f"  ⚠️  Documentation phase returned 'no updates' {no_update_count} times")
            self.logger.info("  🔄 Forcing transition to next phase to prevent loop")
            
            # Reset counter
            state_manager.reset_no_update_count(state, self.phase_name)
            
            # CRITICAL: Update last_doc_update_count to prevent re-entry
            completed_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
            state.last_doc_update_count = completed_count
            state_manager.save(state)
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="Documentation reviewed multiple times - forcing completion to prevent loop",
                next_phase="project_planning"  # Explicit transition
            )
        
        # Gather context
        context = self._gather_documentation_context(state)
        
        # Calculate new completions since last update
        completed_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        last_update = getattr(state, 'last_doc_update_count', 0)
        new_completions = completed_count - last_update
        
        # Build simple documentation message
        user_message = self._build_documentation_message(context, new_completions)
        
        # Get tools for documentation phase
        tools = get_tools_for_phase("documentation")
        
        # Call model with conversation history
        self.logger.info("  Calling model with conversation history")
        response = self.chat_with_history(user_message, tools)
        
        # Extract tool calls and content
        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        
        if not tool_calls:
            # Increment no-update counter
            count = state_manager.increment_no_update_count(state, self.phase_name)
            
            self.logger.info(f"  Documentation appears current (count: {count}/3)")
            
            # CRITICAL: Update last_doc_update_count even when no updates needed
            # This prevents the system from re-entering documentation phase
            state.last_doc_update_count = completed_count
            state_manager.save(state)
            
            # After 2 "no updates", suggest moving on
            if count >= 2:
                message = "Documentation reviewed - no updates needed. Ready to move to next phase."
                next_phase = "project_planning"
            else:
                message = "Documentation reviewed - no updates needed"
                next_phase = None
            
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=message,
                next_phase=next_phase
            )
        
        # If we got tool calls, reset counter (making progress)
        state_manager.reset_no_update_count(state, self.phase_name)
        
        # Check for loops before processing
        if self.check_for_loops():
            self.logger.warning("  Loop detected in documentation phase")
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
        
        # Extract updates from results
        updates_made = []
        for result in results:
            if result.get("success"):
                tool_name = result.get("tool", "unknown")
                if "update_readme" in tool_name or "add_readme" in tool_name:
                    updates_made.append(f"Updated documentation via {tool_name}")
        
        # Update state tracking
        state.last_doc_update_count = completed_count
        
        # CRITICAL FIX: Mark documentation task as COMPLETED
        # This prevents infinite loop where task stays PENDING forever
        from ..state.manager import StateManager
        state_manager = StateManager(self.project_dir)
        
        doc_tasks_completed = 0
        for task_id, task in state.tasks.items():
            if task.status in [TaskStatus.PENDING, TaskStatus.NEW, TaskStatus.IN_PROGRESS]:
                # Check if it's a documentation task
                is_doc_task = False
                if task.target_file and task.target_file.endswith('.md'):
                    is_doc_task = True
                elif task.description:
                    doc_keywords = ['documentation', 'write docs', 'create docs', 'document', 'readme', 'guide']
                    desc_lower = task.description.lower()
                    if any(keyword in desc_lower for keyword in doc_keywords):
                        is_doc_task = True
                
                if is_doc_task:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    doc_tasks_completed += 1
                    self.logger.info(f"  ✅ Marked documentation task complete: {task.description[:60]}")
        
        if doc_tasks_completed > 0:
            state_manager.save(state)
            self.logger.info(f"  📝 Completed {doc_tasks_completed} documentation task(s)")
        
        # WRITE STATUS to DOCUMENTATION_WRITE.md
        status_content = f"""# Documentation Phase Status

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Updates Made
{chr(10).join(f"- {update}" for update in updates_made) if updates_made else "- No updates needed"}

## Files Modified
{chr(10).join(f"- {file}" for file in (["README.md"] if updates_made else [])) if updates_made else "- None"}

## Completed Tasks
- Reviewed {completed_count} completed tasks
- New completions since last update: {new_completions}
- Documentation tasks completed this run: {doc_tasks_completed}

## Next Steps
- Continue monitoring for documentation needs
"""
        self.write_own_status(status_content)
        
        # SEND MESSAGES to other phases
        if updates_made:
            self.send_message_to_phase('planning', f"Documentation updated: {len(updates_made)} changes made")
            self.send_message_to_phase('qa', "Documentation is current - ready for review")
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Documentation updated: {len(updates_made)} changes, {doc_tasks_completed} tasks completed",
            files_modified=["README.md"] if updates_made else [],
            data={"updates": updates_made, "tasks_completed": doc_tasks_completed}
        )
    
    def _gather_documentation_context(self, state: PipelineState) -> str:
        """Gather context for documentation review"""
        context_parts = []
        
        # 1. Current README.md
        readme_path = self.project_dir / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text()
            context_parts.append(f"# CURRENT README.md\n\n{readme_content}")
        else:
            context_parts.append("# README.md\n\n(Does not exist - needs to be created)")
        
        # 2. Current ARCHITECTURE.md
        arch_path = self.project_dir / "ARCHITECTURE.md"
        if arch_path.exists():
            arch_content = arch_path.read_text()
            if len(arch_content) > 3000:
                arch_content = arch_content[:3000] + "\n\n... (truncated)"
            context_parts.append(f"# CURRENT ARCHITECTURE.md\n\n{arch_content}")
        
        # 3. Recently completed tasks
        completed = [
            t for t in state.tasks.values()
            if t.status == TaskStatus.COMPLETED
        ]
        
        recent_completed = sorted(completed, key=lambda t: t.updated_at, reverse=True)[:10]
        
        if recent_completed:
            tasks_list = "\n".join([
                f"- {t.description} → `{t.target_file}`"
                for t in recent_completed
            ])
            context_parts.append(f"# RECENTLY COMPLETED TASKS\n\n{tasks_list}")
        
        # 4. Current project files summary
        py_files = list(self.project_dir.rglob("*.py"))
        file_list = []
        for f in sorted(py_files)[:30]:
            if ".pipeline" not in str(f) and "__pycache__" not in str(f):
                rel = f.relative_to(self.project_dir)
                size = f.stat().st_size
                file_list.append(f"- `{rel}` ({size} bytes)")
        
        if file_list:
            context_parts.append("# PROJECT FILES\n\n" + "\n".join(file_list))
        
        return "\n\n---\n\n".join(context_parts)
    
    def _update_readme_section(self, args: Dict) -> bool:
        """Update a section in README.md"""
        readme_path = self.project_dir / "README.md"
        
        if not readme_path.exists():
            self._create_basic_readme()
        
        section = args.get("section_heading", "")
        new_content = args.get("new_content", "")
        action = args.get("action", "replace")
        
        if not section or not new_content:
            return False
        
        content = readme_path.read_text()
        
        # Pattern: ## Section Heading followed by content until next ## or end
        pattern = rf'(## {re.escape(section)}\n\n)(.*?)(\n## |\Z)'
        
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            before = match.group(1)
            existing = match.group(2)
            after = match.group(3)
            
            if action == "replace":
                updated = new_content
            elif action == "append":
                updated = existing.rstrip() + "\n\n" + new_content
            elif action == "prepend":
                updated = new_content + "\n\n" + existing.lstrip()
            else:
                updated = new_content
            
            new_section = before + updated + after
            content = content[:match.start()] + new_section + content[match.end():]
            
            readme_path.write_text(content)
            self.logger.info(f"    Updated README section: {section}")
            return True
        else:
            # Section not found, add it
            return self._add_readme_section({
                "section_heading": section,
                "content": new_content
            })
    
    def _add_readme_section(self, args: Dict) -> bool:
        """Add a new section to README.md"""
        readme_path = self.project_dir / "README.md"
        
        if not readme_path.exists():
            self._create_basic_readme()
        
        section = args.get("section_heading", "")
        content_text = args.get("content", "")
        after_section = args.get("after_section")
        
        if not section or not content_text:
            return False
        
        content = readme_path.read_text()
        
        new_section = f"\n## {section}\n\n{content_text}\n"
        
        if after_section:
            pattern = rf'(## {re.escape(after_section)}\n\n.*?)(\n## |\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                insert_pos = match.end() - len(match.group(2))
                content = content[:insert_pos] + new_section + content[insert_pos:]
            else:
                content += new_section
        else:
            content += new_section
        
        readme_path.write_text(content)
        self.logger.info(f"    Added README section: {section}")
        return True
    
    def _create_basic_readme(self) -> None:
        """Create a basic README.md if it doesn't exist"""
        readme_path = self.project_dir / "README.md"
        
        project_name = self.project_dir.name
        # Use strategic docs already read at start of execute()
        if master_plan:  # master_plan from read_strategic_docs()
            match = re.search(r'^#\s*(?:MASTER PLAN:?\s*)?(.+)$', master_plan, re.MULTILINE)
            if match:
                project_name = match.group(1).strip()
        
        basic_readme = f"""# {project_name}

> Auto-generated README - will be updated as development progresses.

## Overview

This project is under active development by an AI development pipeline.

## Features

(Features will be documented as they are implemented)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.project_dir.name}

# Install dependencies
pip install -r requirements.txt
```

## Usage

(Usage examples will be added as features are completed)

## Development

This project uses an AI-assisted development pipeline that:
- Reads objectives from MASTER_PLAN.md
- Implements features incrementally
- Reviews code for quality
- Updates documentation automatically

## License

(License information)

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        readme_path.write_text(basic_readme)
        self.logger.info("  📄 Created README.md")
    
    def _log_analysis(self, analysis: Dict) -> None:
        """Log documentation analysis results"""
        readme_needs = analysis.get("readme_needs_update", False)
        arch_needs = analysis.get("architecture_needs_update", False)
        new_features = analysis.get("new_features_to_document", [])
        
        self.logger.info(f"  📊 Documentation Analysis:")
        self.logger.info(f"      README needs update: {readme_needs}")
        self.logger.info(f"      ARCHITECTURE needs update: {arch_needs}")
        
        if new_features:
            self.logger.info(f"      New features to document: {len(new_features)}")
            for feat in new_features[:3]:
                self.logger.info(f"        - {feat[:50]}")
    
    def _build_documentation_message(self, context, new_completions: int) -> str:
        """
        Build a simple, focused documentation message.
        
        The conversation history provides context, so we keep this simple.
        
        Args:
            context: Either a string (from _gather_documentation_context) or a Dict
            new_completions: Number of new completions since last update
        """
        parts = []
        
        # Handle both string and dict context (for backward compatibility)
        if isinstance(context, str):
            # Context is already a formatted string from _gather_documentation_context
            parts.append(context)
            
            # Add new completions info
            if new_completions > 0:
                parts.append(f"\n{new_completions} new tasks have been completed since last documentation update.")
            
            parts.append("\nPlease review and update the project documentation as needed.")
            return "\n\n".join(parts)
        
        # Legacy dict-based context (kept for backward compatibility)
        # Project context
        parts.append(f"Project: {context.get('project_name', 'Unknown')}")
        parts.append(f"Description: {context.get('description', 'No description')}")
        
        # New completions
        if new_completions > 0:
            parts.append(f"\n{new_completions} new tasks have been completed since last documentation update.")
        
        # Completed tasks
        completed = context.get('completed_tasks', [])
        if completed:
            parts.append(f"\nCompleted tasks ({len(completed)}):")
            for task in completed[:5]:
                parts.append(f"- {task.get('description', 'No description')[:80]}")
            if len(completed) > 5:
                parts.append(f"... and {len(completed) - 5} more")
        
        # Instructions
        parts.append("\nPlease update project documentation (README.md, ARCHITECTURE.md, etc.) to reflect the current state.")
        parts.append("Use the appropriate tools to create or update documentation files.")
        
        return "\n".join(parts)
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown state file"""
        readme_exists = (self.project_dir / "README.md").exists()
        arch_exists = (self.project_dir / "ARCHITECTURE.md").exists()
        
        last_update = getattr(state, 'last_doc_update_count', 0)
        current = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        
        return f"""# Documentation State

**Last Run**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Status

- README.md exists: {'✓' if readme_exists else '✗'}
- ARCHITECTURE.md exists: {'✓' if arch_exists else '✗'}
- Tasks documented at: {last_update}
- Current completed tasks: {current}
- Pending documentation: {current - last_update} tasks

## Recent Updates

(Updates are logged in the pipeline output)
"""
