"""
Architecture Manager - Central system for managing ARCHITECTURE.md

This module provides a unified interface for reading, updating, and maintaining
the project's ARCHITECTURE.md file, which serves as the source of truth for:
- Project structure and organization
- Component definitions and responsibilities
- Integration guidelines
- Design patterns and conventions
- Architectural changes history
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class ArchitectureManager:
    """
    Manages ARCHITECTURE.md as the central source of truth.
    
    All phases must:
    1. Read architecture before making decisions
    2. Update architecture after structural changes
    3. Record architectural changes for tracking
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.arch_file = self.project_dir / "ARCHITECTURE.md"
        self.logger = logger
        
    def read_architecture(self) -> Dict[str, Any]:
        """
        Read and parse ARCHITECTURE.md into structured data.
        
        Returns:
            Dict containing:
            - structure: Project structure definition
            - components: Component definitions
            - conventions: Naming and coding conventions
            - guidelines: Integration and design guidelines
            - history: Recent architectural changes
        """
        if not self.arch_file.exists():
            if self.logger:
                self.logger.warning(f"⚠️  ARCHITECTURE.md not found, creating template")
            self._create_template()
            return self._get_empty_architecture()
        
        try:
            content = self.arch_file.read_text(encoding='utf-8')
            return self._parse_architecture(content)
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to read ARCHITECTURE.md: {e}")
            return self._get_empty_architecture()
    
    def _parse_architecture(self, content: str) -> Dict[str, Any]:
        """Parse ARCHITECTURE.md content into structured data."""
        architecture = {
            'structure': self._extract_section(content, 'Project Structure'),
            'components': self._extract_section(content, 'Components'),
            'conventions': self._extract_section(content, 'Naming Conventions'),
            'guidelines': self._extract_section(content, 'Integration Guidelines'),
            'history': self._extract_section(content, 'Change History'),
            'raw_content': content
        }
        
        return architecture
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from markdown content."""
        # Match ## Section Name through next ## or end of file
        pattern = rf'##\s+{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _get_empty_architecture(self) -> Dict[str, Any]:
        """Return empty architecture structure."""
        return {
            'structure': '',
            'components': '',
            'conventions': '',
            'guidelines': '',
            'history': '',
            'raw_content': ''
        }
    
    def update_section(self, section_name: str, content: str):
        """
        Update a specific section in ARCHITECTURE.md.
        
        Args:
            section_name: Name of section (e.g., "Project Structure")
            content: New content for the section
        """
        if not self.arch_file.exists():
            self._create_template()
        
        try:
            current_content = self.arch_file.read_text(encoding='utf-8')
            
            # Find and replace section
            pattern = rf'(##\s+{re.escape(section_name)}.*?\n)(.*?)(?=\n##|\Z)'
            
            def replace_section(match):
                return match.group(1) + content + '\n\n'
            
            updated_content = re.sub(
                pattern,
                replace_section,
                current_content,
                flags=re.IGNORECASE | re.DOTALL
            )
            
            # If section wasn't found, append it
            if updated_content == current_content:
                updated_content += f"\n\n## {section_name}\n\n{content}\n"
            
            self.arch_file.write_text(updated_content, encoding='utf-8')
            
            if self.logger:
                self.logger.info(f"✅ Updated ARCHITECTURE.md section: {section_name}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to update ARCHITECTURE.md: {e}")
    
    def add_component(self, name: str, description: str, location: str, 
                     responsibilities: List[str] = None):
        """
        Add a new component to the architecture.
        
        Args:
            name: Component name
            description: Component description
            location: File/directory location
            responsibilities: List of component responsibilities
        """
        # Read current components section
        arch = self.read_architecture()
        components_section = arch.get('components', '')
        
        # Create component entry
        component_entry = f"""
### {name}

**Location**: `{location}`

**Description**: {description}
"""
        
        if responsibilities:
            component_entry += "\n**Responsibilities**:\n"
            for resp in responsibilities:
                component_entry += f"- {resp}\n"
        
        component_entry += f"\n**Added**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Append to components section
        updated_components = components_section + "\n" + component_entry
        self.update_section("Components", updated_components)
    
    def record_change(self, phase: str, change_type: str, details: Dict):
        """
        Record an architectural change in the history.
        
        Args:
            phase: Phase that made the change
            change_type: Type of change (e.g., "component_added", "structure_modified")
            details: Dictionary with change details
        """
        # Read current history
        arch = self.read_architecture()
        history_section = arch.get('history', '')
        
        # Create change entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        change_entry = f"""
### {timestamp} - {phase.title()} Phase

**Change Type**: {change_type}

**Details**:
"""
        
        for key, value in details.items():
            if isinstance(value, list):
                change_entry += f"- **{key}**: {', '.join(str(v) for v in value)}\n"
            else:
                change_entry += f"- **{key}**: {value}\n"
        
        # Prepend to history (most recent first)
        updated_history = change_entry + "\n" + history_section
        
        # Keep only last 20 changes to prevent bloat
        history_entries = updated_history.split('###')
        if len(history_entries) > 21:  # 1 empty + 20 entries
            history_entries = history_entries[:21]
            updated_history = '###'.join(history_entries)
        
        self.update_section("Change History", updated_history)
    
    def record_file_placement(self, file_path: str, rationale: str):
        """
        Record why a file was placed in a specific location.
        
        Args:
            file_path: Path to the file
            rationale: Explanation of placement decision
        """
        self.record_change(
            phase="system",
            change_type="file_placement",
            details={
                'file': file_path,
                'rationale': rationale
            }
        )
    
    def get_component_location(self, component_type: str) -> Optional[str]:
        """
        Get the expected location for a component type.
        
        Args:
            component_type: Type of component (e.g., "model", "service", "util")
            
        Returns:
            Expected directory path or None if not defined
        """
        arch = self.read_architecture()
        structure = arch.get('structure', '')
        
        # Look for patterns like:
        # - models/ - Database models
        # - services/ - Business logic
        
        pattern = rf'-\s+(\S+/)\s+-\s+.*{re.escape(component_type)}'
        match = re.search(pattern, structure, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    def validate_file_location(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Validate if a file is in the correct location according to architecture.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (e.g., "model", "service", "test")
            
        Returns:
            Dict with:
            - valid: bool
            - expected_location: str
            - current_location: str
            - suggestion: str
        """
        expected_location = self.get_component_location(file_type)
        current_location = str(Path(file_path).parent)
        
        if not expected_location:
            return {
                'valid': True,  # Can't validate if no rule defined
                'expected_location': 'Not defined in architecture',
                'current_location': current_location,
                'suggestion': 'Define architecture rules for this component type'
            }
        
        # Check if current location matches expected
        valid = expected_location.rstrip('/') in current_location
        
        return {
            'valid': valid,
            'expected_location': expected_location,
            'current_location': current_location,
            'suggestion': f"Move to {expected_location}" if not valid else "Location is correct"
        }
    
    def _create_template(self):
        """Create ARCHITECTURE.md template if it doesn't exist."""
        template = f"""# Project Architecture

> **Purpose**: Define project structure, naming conventions, and integration guidelines
> **Updated By**: All phases (record changes here)
> **Read By**: All phases (before making decisions)
> **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Structure

### Directory Organization

Define your project's directory structure here. Example:

- `app/` - Main application code
  - `models/` - Database models and data structures
  - `services/` - Business logic and services
  - `controllers/` - Request handlers and controllers
  - `utils/` - Utility functions and helpers
- `tests/` - Test files
- `docs/` - Documentation

### Library vs Application Code

**Library Directories**: Reusable code meant to be imported
- Define your library directories here

**Application Directories**: Application-specific code
- Define your application directories here

## Components

Define major components of your system here.

### Example Component

**Location**: `app/services/`

**Description**: Business logic services

**Responsibilities**:
- Handle business logic
- Coordinate between models and controllers
- Implement core functionality

## Naming Conventions

### File Naming
- **Preferred**: `snake_case.py` with descriptive names
- **Example**: `user_service.py`, `data_processor.py`

### Class Naming
- **Standard**: `PascalCase`
- **Example**: `UserService`, `DataProcessor`

### Function Naming
- **Standard**: `snake_case`
- **Example**: `process_data()`, `get_user()`

## Integration Guidelines

### Duplicate Detection Rules
- Files with similar names in different directories may indicate duplication
- Action: Flag as integration conflict for review

### Dead Code Review Rules
- Library code may appear unused if not yet integrated
- Don't delete library code without review
- Mark for integration review instead

### Import Conventions
- Use absolute imports for clarity
- Group imports: standard library, third-party, local

## Change History

Recent architectural changes will be recorded here automatically by phases.

---
*This document is the source of truth for project architecture. All phases must read and update it.*
"""
        
        try:
            self.arch_file.write_text(template, encoding='utf-8')
            if self.logger:
                self.logger.info("✅ Created ARCHITECTURE.md template")
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to create ARCHITECTURE.md: {e}")