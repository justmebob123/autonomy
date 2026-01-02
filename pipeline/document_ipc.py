"""
Document-based Inter-Process Communication System

Each phase communicates through READ/WRITE documents:
- Each phase READS its own READ document (written by others)
- Each phase WRITES to its own WRITE document (read by others)
- Planning phase updates strategic documents
- All phases read strategic documents
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging


class DocumentIPC:
    """Manage document-based inter-process communication between phases."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Phase document mappings
        self.phase_documents = {
            # Primary phases
            'planning': {'read': 'PLANNING_READ.md', 'write': 'PLANNING_WRITE.md'},
            'coding': {'read': 'DEVELOPER_READ.md', 'write': 'DEVELOPER_WRITE.md'},
            'qa': {'read': 'QA_READ.md', 'write': 'QA_WRITE.md'},
            'debugging': {'read': 'DEBUG_READ.md', 'write': 'DEBUG_WRITE.md'},
            'investigation': {'read': 'INVESTIGATION_READ.md', 'write': 'INVESTIGATION_WRITE.md'},
            'documentation': {'read': 'DOCUMENTATION_READ.md', 'write': 'DOCUMENTATION_WRITE.md'},
            'project_planning': {'read': 'PROJECT_PLANNING_READ.md', 'write': 'PROJECT_PLANNING_WRITE.md'},
            'refactoring': {'read': 'REFACTORING_READ.md', 'write': 'REFACTORING_WRITE.md'},
            # Specialized phases
            'tool_design': {'read': 'TOOL_DESIGN_READ.md', 'write': 'TOOL_DESIGN_WRITE.md'},
            'tool_evaluation': {'read': 'TOOL_EVALUATION_READ.md', 'write': 'TOOL_EVALUATION_WRITE.md'},
            'prompt_design': {'read': 'PROMPT_DESIGN_READ.md', 'write': 'PROMPT_DESIGN_WRITE.md'},
            'prompt_improvement': {'read': 'PROMPT_IMPROVEMENT_READ.md', 'write': 'PROMPT_IMPROVEMENT_WRITE.md'},
            'role_design': {'read': 'ROLE_DESIGN_READ.md', 'write': 'ROLE_DESIGN_WRITE.md'},
            'role_improvement': {'read': 'ROLE_IMPROVEMENT_READ.md', 'write': 'ROLE_IMPROVEMENT_WRITE.md'},
        }
        
        # Strategic documents (Planning updates, all read)
        self.strategic_documents = [
            'MASTER_PLAN.md',
            'PRIMARY_OBJECTIVES.md',
            'SECONDARY_OBJECTIVES.md',
            'TERTIARY_OBJECTIVES.md',
            'ARCHITECTURE.md'
        ]
    
    def initialize_documents(self):
        """Create all IPC documents if they don't exist."""
        self.logger.info("📄 Initializing document IPC system...")
        
        # Create phase READ/WRITE documents
        for phase, docs in self.phase_documents.items():
            self._create_read_document(phase, docs['read'])
            self._create_write_document(phase, docs['write'])
        
        # Create strategic documents
        self._create_strategic_documents()
        
        self.logger.info("✅ Document IPC system initialized")
    
    def read_own_document(self, phase: str) -> str:
        """
        Phase reads its own READ document.
        
        Args:
            phase: Phase name (planning, coding, qa, debugging)
            
        Returns:
            Content of the phase's READ document
        """
        if phase not in self.phase_documents:
            self.logger.warning(f"Unknown phase: {phase}")
            return ""
        
        doc_name = self.phase_documents[phase]['read']
        return self._read_document(doc_name)
    
    def write_own_document(self, phase: str, content: str):
        """
        Phase writes to its own WRITE document.
        
        Args:
            phase: Phase name
            content: Content to write
        """
        if phase not in self.phase_documents:
            self.logger.warning(f"Unknown phase: {phase}")
            return
        
        doc_name = self.phase_documents[phase]['write']
        self._write_document(doc_name, content, phase)
    
    def write_to_phase(self, from_phase: str, to_phase: str, message: str):
        """
        Write message to another phase's READ document.
        
        Args:
            from_phase: Sending phase
            to_phase: Receiving phase
            message: Message content
        """
        if to_phase not in self.phase_documents:
            self.logger.warning(f"Unknown target phase: {to_phase}")
            return
        
        doc_name = self.phase_documents[to_phase]['read']
        self._append_message(doc_name, from_phase, message)
    
    def read_phase_output(self, phase: str) -> str:
        """
        Read another phase's WRITE document.
        
        Args:
            phase: Phase name
            
        Returns:
            Content of the phase's WRITE document
        """
        if phase not in self.phase_documents:
            self.logger.warning(f"Unknown phase: {phase}")
            return ""
        
        doc_name = self.phase_documents[phase]['write']
        return self._read_document(doc_name)
    
    def read_strategic_document(self, doc_name: str) -> str:
        """
        Read a strategic document.
        
        Args:
            doc_name: Document name (e.g., 'MASTER_PLAN.md')
            
        Returns:
            Document content
        """
        return self._read_document(doc_name)
    
    def read_all_strategic_documents(self) -> Dict[str, str]:
        """
        Read all strategic documents.
        
        Returns:
            Dict mapping document names to content
        """
        docs = {}
        for doc_name in self.strategic_documents:
            content = self._read_document(doc_name)
            if content:
                docs[doc_name] = content
        return docs
    
    # Private helper methods
    
    def _read_document(self, doc_name: str) -> str:
        """Read a document from project directory."""
        filepath = self.project_dir / doc_name
        if not filepath.exists():
            return ""
        
        try:
            return filepath.read_text()
        except Exception as e:
            self.logger.error(f"Failed to read {doc_name}: {e}")
            return ""
    
    def _write_document(self, doc_name: str, content: str, phase: str):
        """Write content to a document."""
        filepath = self.project_dir / doc_name
        
        try:
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_content = f"{content}\n\n---\n**Last Updated**: {timestamp}\n**Updated By**: {phase}\n"
            
            filepath.write_text(full_content)
            self.logger.debug(f"Updated {doc_name}")
        except Exception as e:
            self.logger.error(f"Failed to write {doc_name}: {e}")
    
    def _append_message(self, doc_name: str, from_phase: str, message: str):
        """Append a message to a READ document."""
        filepath = self.project_dir / doc_name
        
        try:
            # Read existing content
            existing = ""
            if filepath.exists():
                existing = filepath.read_text()
            
            # Find the section for this phase
            section_header = f"### From {from_phase.title()}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_message = f"- [{timestamp}] {message}\n"
            
            # If section exists, append to it
            if section_header in existing:
                # Find the section and append
                lines = existing.split('\n')
                new_lines = []
                in_section = False
                section_added = False
                
                for line in lines:
                    new_lines.append(line)
                    if line.strip() == section_header:
                        in_section = True
                    elif in_section and (line.startswith('###') or line.startswith('---')):
                        # End of section, insert before next section or footer
                        new_lines.insert(-1, new_message)
                        section_added = True
                        in_section = False
                
                if not section_added and in_section:
                    # Section was last, append at end
                    new_lines.append(new_message)
                
                existing = '\n'.join(new_lines)
            else:
                # Section doesn't exist, add it before footer
                if '---' in existing:
                    parts = existing.split('---')
                    existing = f"{parts[0]}\n{section_header}\n{new_message}\n---{parts[1]}"
                else:
                    existing += f"\n{section_header}\n{new_message}\n"
            
            filepath.write_text(existing)
            self.logger.debug(f"Appended message to {doc_name} from {from_phase}")
        except Exception as e:
            self.logger.error(f"Failed to append to {doc_name}: {e}")
    
    def _create_read_document(self, phase: str, doc_name: str):
        """Create a READ document template if it doesn't exist."""
        filepath = self.project_dir / doc_name
        if filepath.exists():
            return
        
        phase_title = phase.replace('_', ' ').title()
        template = f"""# {doc_name}

> **Purpose**: Messages and tasks for the {phase_title} phase
> **Updated By**: Other phases (Planning, QA, Debugging, Developer)
> **Read By**: {phase_title} phase only

## Priority Tasks
<!-- High priority tasks from Planning -->

## Requirements
<!-- Specific requirements from other phases -->

## Context
<!-- Relevant context from strategic documents -->

## Messages from Other Phases

### From Planning
<!-- Planning phase messages -->

### From Qa
<!-- QA phase messages -->

### From Debugging
<!-- Debugging phase messages -->

### From Coding
<!-- Developer phase messages -->

---
**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Updated By**: system (initialization)
"""
        
        try:
            filepath.write_text(template)
            self.logger.info(f"  Created {doc_name}")
        except Exception as e:
            self.logger.error(f"Failed to create {doc_name}: {e}")
    
    def _create_write_document(self, phase: str, doc_name: str):
        """Create a WRITE document template if it doesn't exist."""
        filepath = self.project_dir / doc_name
        if filepath.exists():
            return
        
        phase_title = phase.replace('_', ' ').title()
        template = f"""# {doc_name}

> **Purpose**: Status and output from the {phase_title} phase
> **Updated By**: {phase_title} phase only
> **Read By**: All other phases

## Current Status
<!-- Current phase status -->

## Completed Tasks
<!-- List of completed tasks -->

## In Progress
<!-- Tasks currently being worked on -->

## Blockers
<!-- Any blockers encountered -->

## Output Summary
<!-- Summary of work done -->

## Messages to Other Phases

### To Planning
<!-- Messages for planning phase -->

### To Developer
<!-- Messages for coding phase -->

### To Qa
<!-- Messages for QA phase -->

### To Debugging
<!-- Messages for debugging phase -->

---
**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Updated By**: system (initialization)
"""
        
        try:
            filepath.write_text(template)
            self.logger.info(f"  Created {doc_name}")
        except Exception as e:
            self.logger.error(f"Failed to create {doc_name}: {e}")    
    def _create_strategic_documents(self):
        """Create strategic documents if they don't exist."""
        from datetime import datetime
        
        # PRIMARY_OBJECTIVES.md
        primary_path = self.project_dir / 'PRIMARY_OBJECTIVES.md'
        if not primary_path.exists():
            template = f"""# Primary Objectives

> **Purpose**: Core functional requirements and features
> **Updated By**: Planning phase (based on MASTER_PLAN)
> **Read By**: All phases
> **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Core Features
<!-- List of core features to implement -->
<!-- Planning phase will populate this based on MASTER_PLAN analysis -->

## Functional Requirements
<!-- Specific functional requirements -->
<!-- Derived from MASTER_PLAN objectives -->

## Success Criteria
<!-- How to measure success -->
<!-- Defined based on MASTER_PLAN goals -->

---
*This document is automatically updated by the Planning phase based on MASTER_PLAN analysis.*
"""
            try:
                primary_path.write_text(template)
                self.logger.info("  ✅ Created PRIMARY_OBJECTIVES.md")
            except Exception as e:
                self.logger.error(f"  ❌ Failed to create PRIMARY_OBJECTIVES.md: {e}")
        
        # SECONDARY_OBJECTIVES.md
        secondary_path = self.project_dir / 'SECONDARY_OBJECTIVES.md'
        if not secondary_path.exists():
            template = f"""# Secondary Objectives

> **Purpose**: Architectural changes, testing requirements, reported failures
> **Updated By**: Planning phase (based on analysis and QA feedback)
> **Read By**: All phases
> **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Architectural Changes Needed
<!-- Changes to architecture based on analysis -->
<!-- Planning phase adds findings from complexity and integration analysis -->

## Testing Requirements
<!-- Testing needs identified -->
<!-- QA phase reports missing tests, planning adds them here -->

## Reported Failures
<!-- Issues found by QA/debugging -->
<!-- Accumulated from QA_WRITE and DEBUG_WRITE documents -->

## Integration Issues
<!-- Integration problems to resolve -->
<!-- From integration gap and conflict detection -->

---
*This document is automatically updated by the Planning phase based on codebase analysis.*
"""
            try:
                secondary_path.write_text(template)
                self.logger.info("  ✅ Created SECONDARY_OBJECTIVES.md")
            except Exception as e:
                self.logger.error(f"  ❌ Failed to create SECONDARY_OBJECTIVES.md: {e}")
        
        # TERTIARY_OBJECTIVES.md
        tertiary_path = self.project_dir / 'TERTIARY_OBJECTIVES.md'
        if not tertiary_path.exists():
            template = f"""# Tertiary Objectives - Specific Implementation Details

> **Purpose**: Specific implementation details, code examples, and fixes
> **Updated By**: Planning phase (based on deep analysis)
> **Read By**: Coding and debugging phases primarily
> **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Specific Code Fixes Needed
<!-- Detailed fixes with file paths and line numbers -->
<!-- Planning phase adds findings from complexity, dead code, and conflict analysis -->

## Implementation Examples
<!-- Code examples and patterns to follow -->
<!-- Extracted from existing codebase or provided as guidance -->

## Known Issues
<!-- Specific bugs and their locations -->
<!-- From QA analysis and debugging reports -->

## Integration Conflicts to Resolve
<!-- Duplicate implementations and naming conflicts -->
<!-- From integration conflict detection -->

---
*This document is automatically updated by the Planning phase with specific, actionable fixes.*
"""
            try:
                tertiary_path.write_text(template)
                self.logger.info("  ✅ Created TERTIARY_OBJECTIVES.md")
            except Exception as e:
                self.logger.error(f"  ❌ Failed to create TERTIARY_OBJECTIVES.md: {e}")
        
        # ARCHITECTURE.md (if not exists, create from example)
        arch_path = self.project_dir / 'ARCHITECTURE.md'
        if not arch_path.exists():
            # Try to copy from ARCHITECTURE_EXAMPLE.md in pipeline
            from pathlib import Path
            example_path = Path(__file__).parent.parent / 'ARCHITECTURE_EXAMPLE.md'
            
            if example_path.exists():
                try:
                    arch_path.write_text(example_path.read_text())
                    self.logger.info("  ✅ Created ARCHITECTURE.md from example template")
                except Exception as e:
                    self.logger.error(f"  ❌ Failed to create ARCHITECTURE.md: {e}")
            else:
                # Create minimal template if example doesn't exist
                template = f"""# Project Architecture

> **Purpose**: Define project structure, naming conventions, and integration guidelines
> **Updated By**: Planning phase (current state) and humans (intended design)
> **Read By**: All phases
> **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Project Structure

### Library Directories
Directories containing reusable library code (meant to be imported):
<!-- Define your library directories here -->

### Application Directories
Directories containing application-specific code:
<!-- Define your application directories here -->

### Test Directories
Directories containing test code:
- `tests/` - Unit and integration tests
- `test/` - Alternative test directory

## Naming Conventions

### File Naming
- **Preferred**: `snake_case.py` with descriptive names

### Module Naming
- **Preferred**: Feature-based names

### Class Naming
- **Standard**: `PascalCase`

## Integration Guidelines

### Duplicate Detection Rules
- Files with similar names in different directories may indicate duplication
- Action: Flag as integration conflict for review

### Dead Code Review Rules
- Library code may appear unused if not yet integrated
- Don't delete library code without review
- Mark for integration review instead

---
*See ARCHITECTURE_SCHEMA.md in the autonomy repository for full schema documentation.*
"""
                try:
                    arch_path.write_text(template)
                    self.logger.info("  ✅ Created ARCHITECTURE.md with minimal template")
                except Exception as e:
                    self.logger.error(f"  ❌ Failed to create ARCHITECTURE.md: {e}")
    
    # =============================================================================
    # CRITICAL FIX: Document Archiving System
    # =============================================================================
    
    def archive_old_content(self, days_old: int = 7):
        """
        Archive old content from IPC documents.
        
        CRITICAL FIX: Prevent documents from growing indefinitely.
        Archives content older than specified days to archive files.
        
        Args:
            days_old: Archive content older than this many days (default: 7)
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        self.logger.info(f"📦 Archiving IPC content older than {days_old} days...")
        
        # Archive phase documents
        for phase, docs in self.phase_documents.items():
            # Archive WRITE documents (these grow with updates)
            write_doc = docs['write']
            archived = self._archive_document(write_doc, cutoff_date)
            if archived:
                archived_count += 1
        
        # Archive strategic documents (except MASTER_PLAN and ARCHITECTURE)
        for doc_name in self.strategic_documents:
            if doc_name not in ['MASTER_PLAN.md', 'ARCHITECTURE.md']:
                archived = self._archive_document(doc_name, cutoff_date)
                if archived:
                    archived_count += 1
        
        if archived_count > 0:
            self.logger.info(f"✅ Archived {archived_count} documents")
        else:
            self.logger.debug("  ℹ️  No documents needed archiving")
    
    def _archive_document(self, doc_name: str, cutoff_date: datetime) -> bool:
        """
        Archive a single document's old content.
        
        Args:
            doc_name: Document filename
            cutoff_date: Archive content before this date
            
        Returns:
            True if archived, False otherwise
        """
        doc_path = self.project_dir / doc_name
        
        if not doc_path.exists():
            return False
        
        try:
            content = doc_path.read_text()
            
            # Check if document has timestamps
            if not self._has_timestamps(content):
                # No timestamps, can't archive by date
                return False
            
            # Split into recent and old content
            recent_content, old_content = self._split_by_date(content, cutoff_date)
            
            if not old_content:
                # Nothing to archive
                return False
            
            # Create archive directory
            archive_dir = self.project_dir / '.pipeline' / 'archives'
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Archive filename with timestamp
            archive_name = f"{doc_name}.{datetime.now().strftime('%Y%m%d')}.archive"
            archive_path = archive_dir / archive_name
            
            # Append to archive file
            if archive_path.exists():
                existing = archive_path.read_text()
                archive_content = existing + "\n\n" + old_content
            else:
                archive_content = old_content
            
            archive_path.write_text(archive_content)
            
            # Update original document with only recent content
            doc_path.write_text(recent_content)
            
            self.logger.debug(f"  📦 Archived {doc_name} → {archive_name}")
            return True
        
        except Exception as e:
            self.logger.warning(f"  ⚠️  Error archiving {doc_name}: {e}")
            return False
    
    def _has_timestamps(self, content: str) -> bool:
        """Check if content has timestamp markers."""
        # Look for common timestamp patterns
        timestamp_patterns = [
            'Updated:',
            'Timestamp:',
            '202',  # Year pattern
            '##',   # Markdown headers often have dates
        ]
        return any(pattern in content for pattern in timestamp_patterns)
    
    def _split_by_date(self, content: str, cutoff_date: datetime) -> tuple:
        """
        Split content into recent and old based on cutoff date.
        
        Args:
            content: Document content
            cutoff_date: Split at this date
            
        Returns:
            Tuple of (recent_content, old_content)
        """
        lines = content.split('\n')
        recent_lines = []
        old_lines = []
        current_section_date = None
        in_old_section = False
        
        for line in lines:
            # Try to extract date from line
            line_date = self._extract_date_from_line(line)
            
            if line_date:
                current_section_date = line_date
                in_old_section = (line_date < cutoff_date)
            
            # Add to appropriate section
            if in_old_section:
                old_lines.append(line)
            else:
                recent_lines.append(line)
        
        recent_content = '\n'.join(recent_lines)
        old_content = '\n'.join(old_lines)
        
        return recent_content, old_content
    
    def _extract_date_from_line(self, line: str) -> Optional[datetime]:
        """
        Extract date from a line of text.
        
        Args:
            line: Line of text
            
        Returns:
            Datetime if found, None otherwise
        """
        import re
        
        # Pattern: YYYY-MM-DD HH:MM:SS
        pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        match = re.search(pattern, line)
        
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        # Pattern: YYYY-MM-DD
        pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern, line)
        
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
        
        return None
