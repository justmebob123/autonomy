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
            'planning': {'read': 'PLANNING_READ.md', 'write': 'PLANNING_WRITE.md'},
            'coding': {'read': 'DEVELOPER_READ.md', 'write': 'DEVELOPER_WRITE.md'},
            'qa': {'read': 'QA_READ.md', 'write': 'QA_WRITE.md'},
            'debugging': {'read': 'DEBUG_READ.md', 'write': 'DEBUG_WRITE.md'},
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
<!-- Messages for developer phase -->

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