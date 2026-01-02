"""
IPC Integration - Document-based inter-phase communication

This module provides unified interfaces for:
- Reading objectives (PRIMARY/SECONDARY/TERTIARY)
- Writing phase status updates
- Reading other phases' status
- Requesting actions from other phases
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class ObjectiveReader:
    """
    Reads objectives from PRIMARY/SECONDARY/TERTIARY_OBJECTIVES.md files.
    
    All phases should read objectives before execution to understand:
    - What needs to be built (PRIMARY)
    - What needs to be fixed/improved (SECONDARY)
    - What optimizations are needed (TERTIARY)
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.logger = logger
        
    def read_primary_objectives(self) -> List[Dict[str, Any]]:
        """
        Read PRIMARY_OBJECTIVES.md - Core features and requirements.
        
        Returns:
            List of objectives with:
            - title: Objective title
            - description: Detailed description
            - priority: Priority level
            - status: Current status
        """
        return self._read_objectives_file('PRIMARY_OBJECTIVES.md')
    
    def read_secondary_objectives(self) -> List[Dict[str, Any]]:
        """
        Read SECONDARY_OBJECTIVES.md - Architectural changes and fixes.
        
        Returns:
            List of objectives (same structure as primary)
        """
        return self._read_objectives_file('SECONDARY_OBJECTIVES.md')
    
    def read_tertiary_objectives(self) -> List[Dict[str, Any]]:
        """
        Read TERTIARY_OBJECTIVES.md - Optimizations and improvements.
        
        Returns:
            List of objectives (same structure as primary)
        """
        return self._read_objectives_file('TERTIARY_OBJECTIVES.md')
    
    def get_all_objectives(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all objectives organized by level.
        
        Returns:
            Dict with keys: 'primary', 'secondary', 'tertiary'
        """
        return {
            'primary': self.read_primary_objectives(),
            'secondary': self.read_secondary_objectives(),
            'tertiary': self.read_tertiary_objectives()
        }
    
    def _read_objectives_file(self, filename: str) -> List[Dict[str, Any]]:
        """Read and parse an objectives file."""
        file_path = self.project_dir / filename
        
        if not file_path.exists():
            if self.logger:
                self.logger.debug(f"📄 {filename} not found")
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return self._parse_objectives(content)
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to read {filename}: {e}")
            return []
    
    def _parse_objectives(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse objectives from markdown content.
        
        Looks for patterns like:
        ### Objective Title
        Description text
        - Priority: high
        - Status: pending
        """
        objectives = []
        
        # Split by ### headers
        sections = re.split(r'\n###\s+', content)
        
        for section in sections[1:]:  # Skip first (before any ###)
            lines = section.split('\n')
            if not lines:
                continue
            
            title = lines[0].strip()
            description = []
            priority = 'medium'
            status = 'pending'
            
            for line in lines[1:]:
                line = line.strip()
                
                # Check for metadata
                if line.startswith('- Priority:') or line.startswith('**Priority**:'):
                    priority = line.split(':', 1)[1].strip().lower()
                elif line.startswith('- Status:') or line.startswith('**Status**:'):
                    status = line.split(':', 1)[1].strip().lower()
                elif line and not line.startswith('#'):
                    description.append(line)
            
            if title:
                objectives.append({
                    'title': title,
                    'description': '\n'.join(description),
                    'priority': priority,
                    'status': status
                })
        
        return objectives


class StatusWriter:
    """
    Writes phase status updates to IPC documents.
    
    Each phase writes to its own WRITE document which other phases can read.
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.logger = logger
        
    def write_phase_status(self, phase: str, status: Dict[str, Any]):
        """
        Write phase status to its WRITE document.
        
        Args:
            phase: Phase name (e.g., 'coding', 'qa')
            status: Status dict with:
                - status: 'running', 'completed', 'failed'
                - message: Status message
                - files_modified: List of modified files
                - timestamp: When status was written
        """
        write_file = self.project_dir / f"{phase.upper()}_WRITE.md"
        
        # Add timestamp if not present
        if 'timestamp' not in status:
            status['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create status entry
        entry = f"""
## Status Update - {status['timestamp']}

**Status**: {status.get('status', 'unknown')}

**Message**: {status.get('message', 'No message')}
"""
        
        if status.get('files_modified'):
            entry += "\n**Files Modified**:\n"
            for file in status['files_modified']:
                entry += f"- `{file}`\n"
        
        if status.get('files_created'):
            entry += "\n**Files Created**:\n"
            for file in status['files_created']:
                entry += f"- `{file}`\n"
        
        entry += "\n---\n"
        
        # Append to file (prepend actually, so most recent is first)
        try:
            if write_file.exists():
                current_content = write_file.read_text(encoding='utf-8')
                # Keep only last 10 status updates
                updates = current_content.split('---')
                if len(updates) > 10:
                    updates = updates[:10]
                    current_content = '---'.join(updates)
                new_content = entry + current_content
            else:
                header = f"""# {phase.upper()} Phase Status

> **Purpose**: Status updates from {phase} phase
> **Written By**: {phase.title()} phase
> **Read By**: Other phases

"""
                new_content = header + entry
            
            write_file.write_text(new_content, encoding='utf-8')
            
            if self.logger:
                self.logger.debug(f"✅ Wrote status to {write_file.name}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to write status: {e}")
    
    def write_completion(self, phase: str, results: Dict[str, Any]):
        """
        Write phase completion status.
        
        Args:
            phase: Phase name
            results: Completion results dict
        """
        self.write_phase_status(phase, {
            'status': 'completed',
            'message': results.get('message', 'Phase completed'),
            'files_modified': results.get('files_modified', []),
            'files_created': results.get('files_created', []),
            'success': results.get('success', True)
        })
    
    def write_request(self, from_phase: str, to_phase: str, request: Dict[str, Any]):
        """
        Write a request from one phase to another.
        
        Args:
            from_phase: Requesting phase
            to_phase: Target phase
            request: Request dict with:
                - action: What action is requested
                - reason: Why it's needed
                - details: Additional details
        """
        read_file = self.project_dir / f"{to_phase.upper()}_READ.md"
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        entry = f"""
## Request from {from_phase.title()} - {timestamp}

**Action Requested**: {request.get('action', 'unknown')}

**Reason**: {request.get('reason', 'No reason provided')}

**Details**:
{request.get('details', 'No additional details')}

---
"""
        
        try:
            if read_file.exists():
                current_content = read_file.read_text(encoding='utf-8')
                new_content = entry + current_content
            else:
                header = f"""# {to_phase.upper()} Phase Requests

> **Purpose**: Requests and messages for {to_phase} phase
> **Written By**: Other phases
> **Read By**: {to_phase.title()} phase

"""
                new_content = header + entry
            
            read_file.write_text(new_content, encoding='utf-8')
            
            if self.logger:
                self.logger.info(f"✅ Wrote request from {from_phase} to {to_phase}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to write request: {e}")


class StatusReader:
    """
    Reads status updates from other phases.
    
    Allows phases to check what other phases are doing.
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.logger = logger
        
    def read_phase_status(self, phase: str) -> List[Dict[str, Any]]:
        """
        Read status updates from a phase's WRITE document.
        
        Args:
            phase: Phase name to read from
            
        Returns:
            List of status updates (most recent first)
        """
        write_file = self.project_dir / f"{phase.upper()}_WRITE.md"
        
        if not write_file.exists():
            return []
        
        try:
            content = write_file.read_text(encoding='utf-8')
            return self._parse_status_updates(content)
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to read {phase} status: {e}")
            return []
    
    def _parse_status_updates(self, content: str) -> List[Dict[str, Any]]:
        """Parse status updates from content."""
        updates = []
        
        # Split by ## Status Update
        sections = re.split(r'\n##\s+Status Update', content)
        
        for section in sections[1:]:  # Skip header
            lines = section.split('\n')
            if not lines:
                continue
            
            # First line has timestamp
            timestamp_match = re.search(r'-\s+(.+)', lines[0])
            timestamp = timestamp_match.group(1) if timestamp_match else 'unknown'
            
            status = 'unknown'
            message = ''
            files_modified = []
            files_created = []
            
            for line in lines[1:]:
                line = line.strip()
                
                if line.startswith('**Status**:'):
                    status = line.split(':', 1)[1].strip()
                elif line.startswith('**Message**:'):
                    message = line.split(':', 1)[1].strip()
                elif line.startswith('- `') and 'Files Modified' in '\n'.join(lines):
                    file_match = re.search(r'`(.+?)`', line)
                    if file_match:
                        files_modified.append(file_match.group(1))
                elif line.startswith('- `') and 'Files Created' in '\n'.join(lines):
                    file_match = re.search(r'`(.+?)`', line)
                    if file_match:
                        files_created.append(file_match.group(1))
            
            updates.append({
                'timestamp': timestamp,
                'status': status,
                'message': message,
                'files_modified': files_modified,
                'files_created': files_created
            })
        
        return updates
    
    def get_all_phase_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get status from all phases.
        
        Returns:
            Dict mapping phase names to their status updates
        """
        phases = ['planning', 'coding', 'qa', 'debugging', 'refactoring', 
                 'documentation', 'investigation']
        
        return {
            phase: self.read_phase_status(phase)
            for phase in phases
        }