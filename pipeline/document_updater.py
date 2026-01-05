"""
Document Updater - Utility for bidirectional IPC document updates

Provides functions for phases to update strategic documents:
- Mark tasks as completed
- Remove resolved issues
- Add new issues
- Update architecture sections
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime
import re
import logging


class DocumentUpdater:
    """Utility for updating strategic IPC documents."""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
    
    def mark_task_complete(
        self,
        doc_name: str,
        task_identifier: str,
        phase_name: str,
        completion_note: Optional[str] = None
    ) -> bool:
        """
        Mark a specific task as completed in objectives document.
        
        Args:
            doc_name: Document name (e.g., 'TERTIARY_OBJECTIVES.md')
            task_identifier: Unique identifier for the task (e.g., file path, line number)
            phase_name: Name of phase completing the task
            completion_note: Optional note about completion
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / doc_name
        
        if not doc_path.exists():
            self.logger.warning(f"Document {doc_name} does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find the task section containing the identifier
            # Look for patterns like: "#### 1. `filepath::function` (Line 123)"
            pattern = re.escape(task_identifier)
            
            # Add completion marker
            completion_marker = f"\n**Status:** ✅ COMPLETED ({timestamp})\n**Completed By:** {phase_name}"
            if completion_note:
                completion_marker += f"\n**Note:** {completion_note}"
            
            # Find the task header and add status after it
            # Match: #### N. `identifier` (Line X)
            task_pattern = rf'(####\s+\d+\.\s+`[^`]*{pattern}[^`]*`[^\n]*\n)'
            
            # Check if already marked complete
            if f"✅ COMPLETED" in content and task_identifier in content:
                self.logger.debug(f"Task {task_identifier} already marked complete")
                return True
            
            # Add completion marker after task header
            updated_content = re.sub(
                task_pattern,
                rf'\1{completion_marker}\n',
                content,
                count=1
            )
            
            if updated_content != content:
                doc_path.write_text(updated_content)
                self.logger.info(f"✅ Marked task complete in {doc_name}: {task_identifier}")
                return True
            else:
                self.logger.warning(f"Could not find task {task_identifier} in {doc_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to mark task complete in {doc_name}: {e}")
            return False
    
    def remove_resolved_issue(
        self,
        doc_name: str,
        issue_description: str,
        phase_name: str,
        resolution_note: Optional[str] = None
    ) -> bool:
        """
        Remove or mark as resolved an issue in objectives document.
        
        Args:
            doc_name: Document name (e.g., 'SECONDARY_OBJECTIVES.md')
            issue_description: Description of the issue to remove
            phase_name: Name of phase resolving the issue
            resolution_note: Optional note about resolution
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / doc_name
        
        if not doc_path.exists():
            self.logger.warning(f"Document {doc_name} does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find lines containing the issue description
            lines = content.split('\n')
            updated_lines = []
            found = False
            
            for line in lines:
                if issue_description in line and not '✅ FIXED' in line:
                    # Mark as fixed with strikethrough
                    resolution_text = f"✅ FIXED ({timestamp} by {phase_name})"
                    if resolution_note:
                        resolution_text += f" - {resolution_note}"
                    
                    # Add strikethrough and resolution marker
                    updated_line = line.replace('- ', f'- ~~') + f'~~ {resolution_text}'
                    updated_lines.append(updated_line)
                    found = True
                    self.logger.info(f"✅ Marked issue resolved in {doc_name}: {issue_description[:50]}...")
                else:
                    updated_lines.append(line)
            
            if found:
                updated_content = '\n'.join(updated_lines)
                doc_path.write_text(updated_content)
                return True
            else:
                self.logger.warning(f"Could not find issue in {doc_name}: {issue_description[:50]}...")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove issue from {doc_name}: {e}")
            return False
    
    def add_new_issue(
        self,
        doc_name: str,
        section_name: str,
        issue_description: str,
        phase_name: str,
        severity: str = "Error"
    ) -> bool:
        """
        Add a new issue to objectives document.
        
        Args:
            doc_name: Document name (e.g., 'SECONDARY_OBJECTIVES.md')
            section_name: Section to add to (e.g., 'Reported Failures')
            issue_description: Description of the new issue
            phase_name: Name of phase reporting the issue
            severity: Severity level (Error, Warning, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / doc_name
        
        if not doc_path.exists():
            self.logger.warning(f"Document {doc_name} does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find the section
            section_pattern = rf'##\s+{re.escape(section_name)}\s*\n'
            match = re.search(section_pattern, content)
            
            if not match:
                self.logger.warning(f"Section '{section_name}' not found in {doc_name}")
                return False
            
            # Find the subsection for this phase or create it
            phase_subsection = f"### From {phase_name.title()} Phase"
            
            if phase_subsection not in content:
                # Add new subsection after the main section
                insert_pos = match.end()
                new_subsection = f"\n{phase_subsection} (Added {timestamp})\n\n- {severity}: {issue_description}\n"
                updated_content = content[:insert_pos] + new_subsection + content[insert_pos:]
            else:
                # Append to existing subsection
                # Find the subsection and add after it
                subsection_pattern = rf'({re.escape(phase_subsection)}[^\n]*\n)'
                updated_content = re.sub(
                    subsection_pattern,
                    rf'\1- {severity}: {issue_description}\n',
                    content,
                    count=1
                )
            
            doc_path.write_text(updated_content)
            self.logger.info(f"✅ Added new issue to {doc_name}: {issue_description[:50]}...")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to add issue to {doc_name}: {e}")
            return False
    
    def update_actual_architecture(
        self,
        component_name: str,
        change_description: str,
        phase_name: str
    ) -> bool:
        """
        Update ACTUAL architecture section with changes.
        
        Args:
            component_name: Name of component changed (e.g., 'services/config_loader.py')
            change_description: Description of change (e.g., 'REFACTORED', 'INTEGRATED')
            phase_name: Name of phase making the change
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / 'ARCHITECTURE.md'
        
        if not doc_path.exists():
            self.logger.warning("ARCHITECTURE.md does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find ACTUAL Architecture section
            actual_section_pattern = r'##\s+ACTUAL\s+Architecture\s*\n'
            match = re.search(actual_section_pattern, content)
            
            if not match:
                self.logger.warning("ACTUAL Architecture section not found")
                return False
            
            # Find the component in the current components list
            component_pattern = rf'(\*\*{re.escape(component_name)}\*\*[^\n]*)'
            
            if re.search(component_pattern, content):
                # Update existing component
                updated_content = re.sub(
                    component_pattern,
                    rf'\1 - {change_description} ({timestamp} by {phase_name})',
                    content,
                    count=1
                )
            else:
                # Add new component to the list
                # Find "### Current Components" and add after it
                components_pattern = r'(###\s+Current\s+Components\s*\n)'
                updated_content = re.sub(
                    components_pattern,
                    rf'\1\n**{component_name}** - {change_description} ({timestamp} by {phase_name})\n',
                    content,
                    count=1
                )
            
            doc_path.write_text(updated_content)
            self.logger.info(f"✅ Updated ARCHITECTURE.md: {component_name} - {change_description}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to update ARCHITECTURE.md: {e}")
            return False
    
    def mark_feature_complete(
        self,
        feature_name: str,
        phase_name: str,
        completion_note: Optional[str] = None
    ) -> bool:
        """
        Mark a feature as completed in PRIMARY_OBJECTIVES.md.
        
        Args:
            feature_name: Name of the feature completed
            phase_name: Name of phase completing the feature
            completion_note: Optional note about completion
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / 'PRIMARY_OBJECTIVES.md'
        
        if not doc_path.exists():
            self.logger.warning("PRIMARY_OBJECTIVES.md does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find the feature in the list
            feature_pattern = rf'(-\s+{re.escape(feature_name)}[^\n]*)'
            
            if not re.search(feature_pattern, content):
                self.logger.warning(f"Feature '{feature_name}' not found in PRIMARY_OBJECTIVES.md")
                return False
            
            # Check if already marked complete
            if f"✅" in content and feature_name in content:
                self.logger.debug(f"Feature {feature_name} already marked complete")
                return True
            
            # Add completion marker
            completion_marker = f" ✅ COMPLETED ({timestamp})"
            if completion_note:
                completion_marker += f" - {completion_note}"
            
            updated_content = re.sub(
                feature_pattern,
                rf'\1{completion_marker}',
                content,
                count=1
            )
            
            doc_path.write_text(updated_content)
            self.logger.info(f"✅ Marked feature complete in PRIMARY_OBJECTIVES.md: {feature_name}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to mark feature complete: {e}")
            return False
    
    def update_architectural_drift(
        self,
        drift_reduction: str,
        phase_name: str
    ) -> bool:
        """
        Update architectural drift section when alignment improves.
        
        Args:
            drift_reduction: Description of what was aligned
            phase_name: Name of phase reducing drift
            
        Returns:
            True if successful, False otherwise
        """
        doc_path = self.project_dir / 'ARCHITECTURE.md'
        
        if not doc_path.exists():
            self.logger.warning("ARCHITECTURE.md does not exist")
            return False
        
        try:
            content = doc_path.read_text()
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Find Architectural Drift section
            drift_section_pattern = r'##\s+Architectural\s+Drift\s*\n'
            match = re.search(drift_section_pattern, content)
            
            if not match:
                self.logger.warning("Architectural Drift section not found")
                return False
            
            # Add note about drift reduction
            drift_note = f"\n**Drift Reduced ({timestamp}):** {drift_reduction} (by {phase_name})\n"
            
            # Insert after the drift section header
            insert_pos = match.end()
            updated_content = content[:insert_pos] + drift_note + content[insert_pos:]
            
            doc_path.write_text(updated_content)
            self.logger.info(f"✅ Updated architectural drift: {drift_reduction}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to update architectural drift: {e}")
            return False