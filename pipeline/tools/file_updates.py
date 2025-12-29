"""
File Update Tools

Provides tools for incrementally updating files without full rewrites.
Essential for updating structured documents like MASTER_PLAN.md, PRIMARY_OBJECTIVES.md, etc.
"""

import re
from pathlib import Path
from typing import Optional, List
import logging

from ..logging_setup import get_logger


class FileUpdateTools:
    """
    Tools for incremental file updates.
    
    Provides:
    - append_to_file: Append content to end of file
    - update_section: Update a specific markdown section
    - insert_after: Insert content after a marker
    - insert_before: Insert content before a marker
    - replace_section: Replace content between markers
    
    Example:
        tools = FileUpdateTools('/project')
        
        # Append to file
        tools.append_to_file('MASTER_PLAN.md', '\\n## New Section\\nContent...')
        
        # Update markdown section
        tools.update_section('PRIMARY_OBJECTIVES.md', 'Phase 2', 'New content...')
        
        # Insert after marker
        tools.insert_after('README.md', '## Features', '\\n- New feature')
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize file update tools.
        
        Args:
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or get_logger()
        
        self.logger.info(f"FileUpdateTools initialized for {project_dir}")
    
    def append_to_file(self, filepath: str, content: str, 
                      ensure_newline: bool = True) -> dict:
        """
        Append content to end of file.
        
        Args:
            filepath: Path to file (relative to project_dir)
            content: Content to append
            ensure_newline: Ensure file ends with newline before appending
        
        Returns:
            Result dict with success, message
        """
        try:
            file_path = self.project_dir / filepath
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing content
            if file_path.exists():
                existing = file_path.read_text()
                
                # Ensure newline before appending if requested
                if ensure_newline and existing and not existing.endswith('\n'):
                    existing += '\n'
            else:
                existing = ''
            
            # Append content
            new_content = existing + content
            
            # Write back
            file_path.write_text(new_content)
            
            self.logger.info(f"Appended to file: {filepath}")
            
            return {
                'success': True,
                'message': f'Appended {len(content)} characters to {filepath}',
                'filepath': str(filepath)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to append to file {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'append_failed'
            }
    
    def update_section(self, filepath: str, section_title: str, 
                      new_content: str, create_if_missing: bool = True) -> dict:
        """
        Update a specific section in a markdown file.
        
        Finds section by title (e.g., "## Section Title") and replaces
        content until next section of same or higher level.
        
        Args:
            filepath: Path to file (relative to project_dir)
            section_title: Section title (without # markers)
            new_content: New content for section
            create_if_missing: Create section if it doesn't exist
        
        Returns:
            Result dict with success, message
        """
        try:
            file_path = self.project_dir / filepath
            
            if not file_path.exists():
                if create_if_missing:
                    # Create file with section
                    content = f"# {file_path.stem}\n\n## {section_title}\n{new_content}\n"
                    file_path.write_text(content)
                    
                    self.logger.info(f"Created file with section: {filepath}")
                    return {
                        'success': True,
                        'message': f'Created {filepath} with section {section_title}',
                        'filepath': str(filepath),
                        'created': True
                    }
                else:
                    return {
                        'success': False,
                        'error': f'File not found: {filepath}',
                        'error_type': 'file_not_found'
                    }
            
            # Read existing content
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Find section
            section_pattern = re.compile(rf'^(#+)\s+{re.escape(section_title)}\s*$')
            section_start = None
            section_level = None
            
            for i, line in enumerate(lines):
                match = section_pattern.match(line)
                if match:
                    section_start = i
                    section_level = len(match.group(1))
                    break
            
            if section_start is None:
                if create_if_missing:
                    # Append section to end
                    new_lines = lines + [
                        '',
                        f'## {section_title}',
                        new_content,
                        ''
                    ]
                    file_path.write_text('\n'.join(new_lines))
                    
                    self.logger.info(f"Added new section to {filepath}: {section_title}")
                    return {
                        'success': True,
                        'message': f'Added section {section_title} to {filepath}',
                        'filepath': str(filepath),
                        'created': True
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Section not found: {section_title}',
                        'error_type': 'section_not_found'
                    }
            
            # Find section end (next section of same or higher level)
            section_end = len(lines)
            for i in range(section_start + 1, len(lines)):
                if lines[i].startswith('#'):
                    # Check level
                    level = len(lines[i].split()[0])
                    if level <= section_level:
                        section_end = i
                        break
            
            # Replace section content
            new_lines = (
                lines[:section_start + 1] +  # Keep section header
                [new_content] +               # New content
                lines[section_end:]           # Rest of file
            )
            
            file_path.write_text('\n'.join(new_lines))
            
            self.logger.info(f"Updated section in {filepath}: {section_title}")
            
            return {
                'success': True,
                'message': f'Updated section {section_title} in {filepath}',
                'filepath': str(filepath),
                'updated': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update section in {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'update_failed'
            }
    
    def insert_after(self, filepath: str, marker: str, content: str,
                    first_occurrence: bool = True) -> dict:
        """
        Insert content after a marker line.
        
        Args:
            filepath: Path to file (relative to project_dir)
            marker: Marker line to search for
            content: Content to insert
            first_occurrence: Insert after first occurrence (vs all)
        
        Returns:
            Result dict with success, message
        """
        try:
            file_path = self.project_dir / filepath
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {filepath}',
                    'error_type': 'file_not_found'
                }
            
            # Read existing content
            existing = file_path.read_text()
            lines = existing.split('\n')
            
            # Find marker
            insertions = 0
            new_lines = []
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                if marker in line:
                    # Insert content after this line
                    new_lines.append(content)
                    insertions += 1
                    
                    if first_occurrence:
                        # Add remaining lines and break
                        new_lines.extend(lines[i + 1:])
                        break
            
            if insertions == 0:
                return {
                    'success': False,
                    'error': f'Marker not found: {marker}',
                    'error_type': 'marker_not_found'
                }
            
            # Write back
            file_path.write_text('\n'.join(new_lines))
            
            self.logger.info(f"Inserted content after marker in {filepath}")
            
            return {
                'success': True,
                'message': f'Inserted content after "{marker}" in {filepath}',
                'filepath': str(filepath),
                'insertions': insertions
            }
            
        except Exception as e:
            self.logger.error(f"Failed to insert after marker in {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'insert_failed'
            }
    
    def insert_before(self, filepath: str, marker: str, content: str,
                     first_occurrence: bool = True) -> dict:
        """
        Insert content before a marker line.
        
        Args:
            filepath: Path to file (relative to project_dir)
            marker: Marker line to search for
            content: Content to insert
            first_occurrence: Insert before first occurrence (vs all)
        
        Returns:
            Result dict with success, message
        """
        try:
            file_path = self.project_dir / filepath
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {filepath}',
                    'error_type': 'file_not_found'
                }
            
            # Read existing content
            existing = file_path.read_text()
            lines = existing.split('\n')
            
            # Find marker
            insertions = 0
            new_lines = []
            
            for i, line in enumerate(lines):
                if marker in line:
                    # Insert content before this line
                    new_lines.append(content)
                    insertions += 1
                    
                    if first_occurrence:
                        # Add remaining lines and break
                        new_lines.extend(lines[i:])
                        break
                
                new_lines.append(line)
            
            if insertions == 0:
                return {
                    'success': False,
                    'error': f'Marker not found: {marker}',
                    'error_type': 'marker_not_found'
                }
            
            # Write back
            file_path.write_text('\n'.join(new_lines))
            
            self.logger.info(f"Inserted content before marker in {filepath}")
            
            return {
                'success': True,
                'message': f'Inserted content before "{marker}" in {filepath}',
                'filepath': str(filepath),
                'insertions': insertions
            }
            
        except Exception as e:
            self.logger.error(f"Failed to insert before marker in {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'insert_failed'
            }
    
    def replace_between(self, filepath: str, start_marker: str, end_marker: str,
                       new_content: str, include_markers: bool = False) -> dict:
        """
        Replace content between two markers.
        
        Args:
            filepath: Path to file (relative to project_dir)
            start_marker: Start marker line
            end_marker: End marker line
            new_content: New content to insert
            include_markers: Replace markers too (vs keep them)
        
        Returns:
            Result dict with success, message
        """
        try:
            file_path = self.project_dir / filepath
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {filepath}',
                    'error_type': 'file_not_found'
                }
            
            # Read existing content
            existing = file_path.read_text()
            lines = existing.split('\n')
            
            # Find markers
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if start_marker in line and start_idx is None:
                    start_idx = i
                elif end_marker in line and start_idx is not None:
                    end_idx = i
                    break
            
            if start_idx is None:
                return {
                    'success': False,
                    'error': f'Start marker not found: {start_marker}',
                    'error_type': 'marker_not_found'
                }
            
            if end_idx is None:
                return {
                    'success': False,
                    'error': f'End marker not found: {end_marker}',
                    'error_type': 'marker_not_found'
                }
            
            # Build new content
            if include_markers:
                new_lines = lines[:start_idx] + [new_content] + lines[end_idx + 1:]
            else:
                new_lines = (
                    lines[:start_idx + 1] +  # Keep start marker
                    [new_content] +
                    lines[end_idx:]           # Keep end marker
                )
            
            # Write back
            file_path.write_text('\n'.join(new_lines))
            
            self.logger.info(f"Replaced content between markers in {filepath}")
            
            return {
                'success': True,
                'message': f'Replaced content between markers in {filepath}',
                'filepath': str(filepath)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to replace between markers in {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'replace_failed'
            }