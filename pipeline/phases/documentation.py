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
from ..tools import TOOLS_DOCUMENTATION
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
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute documentation phase"""
        
        self.logger.info("  📝 Reviewing documentation...")
        
        # Gather context
        context = self._gather_documentation_context(state)
        
        # Calculate new completions since last update
        completed_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.COMPLETED)
        last_update = getattr(state, 'last_doc_update_count', 0)
        new_completions = completed_count - last_update
        
        # Build messages using centralized prompts
        messages = [
            {"role": "system", "content": self._get_system_prompt("documentation")},
            {"role": "user", "content": get_documentation_prompt(context, new_completions)}
        ]
        
        # Call LLM with documentation tools from centralized tools.py
        response = self.chat(
            messages=messages,
            tools=TOOLS_DOCUMENTATION,
            task_type="qa"  # Use QA model for review-type work
        )
        
        if "error" in response:
            self.logger.error(f"  LLM error: {response['error']}")
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"LLM error: {response['error']}"
            )
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if not tool_calls:
            # No updates needed or couldn't parse
            self.logger.info("  Documentation appears current")
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message="Documentation reviewed - no updates needed"
            )
        
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
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Documentation updated: {len(updates_made)} changes",
            files_modified=["README.md"] if updates_made else [],
            data={"updates": updates_made}
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
        master_plan = self.project_dir / "MASTER_PLAN.md"
        
        if master_plan.exists():
            content = master_plan.read_text()
            match = re.search(r'^#\s*(?:MASTER PLAN:?\s*)?(.+)$', content, re.MULTILINE)
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
