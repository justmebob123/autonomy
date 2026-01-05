"""
Architecture Document Parser

Parses ARCHITECTURE.md files to extract project structure information,
naming conventions, and integration guidelines.

This allows the pipeline to make architecture-aware decisions instead of
using hardcoded project-specific assumptions.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class ArchitectureConfig:
    """Configuration extracted from ARCHITECTURE.md"""
    
    # Directory classifications
    library_dirs: Set[str]
    application_dirs: Set[str]
    test_dirs: Set[str]
    
    # Naming conventions
    preferred_file_naming: str
    preferred_module_naming: str
    class_naming_conventions: Dict[str, str]
    
    # Integration rules
    duplicate_detection_enabled: bool
    dead_code_review_mode: bool  # True = mark for review, False = mark for deletion
    
    # Known issues
    known_conflicts: List[Dict[str, str]]
    
    def is_library_module(self, filepath: str) -> bool:
        """Check if a file path is in a library directory"""
        return any(filepath.startswith(lib_dir) for lib_dir in self.library_dirs)
    
    def is_application_module(self, filepath: str) -> bool:
        """Check if a file path is in an application directory"""
        return any(filepath.startswith(app_dir) for app_dir in self.application_dirs)
    
    def is_test_module(self, filepath: str) -> bool:
        """Check if a file path is in a test directory"""
        return any(filepath.startswith(test_dir) for test_dir in self.test_dirs)


class ArchitectureParser:
    """Parser for ARCHITECTURE.md files"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.architecture_file = self.project_dir / "ARCHITECTURE.md"
    
    def parse(self) -> Optional[ArchitectureConfig]:
        """
        Parse ARCHITECTURE.md and return configuration.
        
        Returns None if file doesn't exist or can't be parsed.
        """
        if not self.architecture_file.exists():
            return None
        
        try:
            content = self.architecture_file.read_text()
            
            return ArchitectureConfig(
                library_dirs=self._extract_library_dirs(content),
                application_dirs=self._extract_application_dirs(content),
                test_dirs=self._extract_test_dirs(content),
                preferred_file_naming=self._extract_file_naming(content),
                preferred_module_naming=self._extract_module_naming(content),
                class_naming_conventions=self._extract_class_naming(content),
                duplicate_detection_enabled=self._has_duplicate_detection(content),
                dead_code_review_mode=self._has_dead_code_review(content),
                known_conflicts=self._extract_known_conflicts(content),
            )
        except Exception as e:
            pass
            # If parsing fails, return None (fall back to defaults)
            return None
    
    def _extract_library_dirs(self, content: str) -> Set[str]:
        """Extract library directory paths from content"""
        dirs = set()
        
        # Find "Library Directories" section
        section = self._extract_section(content, "Library Directories")
        if not section:
            return dirs
        
        # Extract directory paths from bullet points
        # Pattern: - `path/` - Description
        pattern = r'-\s+`([^`]+)`\s+-'
        matches = re.findall(pattern, section)
        
        for match in matches:
            pass
            # Normalize path (ensure trailing slash)
            path = match.strip()
            if not path.endswith('/'):
                path += '/'
            dirs.add(path)
        
        return dirs
    
    def _extract_application_dirs(self, content: str) -> Set[str]:
        """Extract application directory paths from content"""
        dirs = set()
        
        section = self._extract_section(content, "Application Directories")
        if not section:
            return dirs
        
        pattern = r'-\s+`([^`]+)`\s+-'
        matches = re.findall(pattern, section)
        
        for match in matches:
            path = match.strip()
            if not path.endswith('/'):
                path += '/'
            dirs.add(path)
        
        return dirs
    
    def _extract_test_dirs(self, content: str) -> Set[str]:
        """Extract test directory paths from content"""
        dirs = set()
        
        section = self._extract_section(content, "Test Directories")
        if not section:
            pass
            # Default test directories
            return {'tests/', 'test/'}
        
        pattern = r'-\s+`([^`]+)`\s+-'
        matches = re.findall(pattern, section)
        
        for match in matches:
            path = match.strip()
            if not path.endswith('/'):
                path += '/'
            dirs.add(path)
        
        return dirs
    
    def _extract_file_naming(self, content: str) -> str:
        """Extract preferred file naming convention"""
        section = self._extract_section(content, "File Naming")
        if not section:
            return "snake_case"
        
        # Look for "Preferred:" line
        match = re.search(r'-\s+\*\*Preferred\*\*:\s+`([^`]+)`', section)
        if match:
            return match.group(1)
        
        return "snake_case"
    
    def _extract_module_naming(self, content: str) -> str:
        """Extract preferred module naming convention"""
        section = self._extract_section(content, "Module Naming")
        if not section:
            return "descriptive"
        
        match = re.search(r'-\s+\*\*Preferred\*\*:\s+([^\n]+)', section)
        if match:
            return match.group(1).strip()
        
        return "descriptive"
    
    def _extract_class_naming(self, content: str) -> Dict[str, str]:
        """Extract class naming conventions"""
        conventions = {}
        
        section = self._extract_section(content, "Class Naming")
        if not section:
            return {"default": "PascalCase"}
        
        # Extract suffix conventions
        # Pattern: - `*Suffix` for description
        pattern = r'-\s+`\*([A-Za-z]+)`\s+for\s+([^\n]+)'
        matches = re.findall(pattern, section)
        
        for suffix, description in matches:
            conventions[suffix] = description.strip()
        
        if not conventions:
            conventions["default"] = "PascalCase"
        
        return conventions
    
    def _has_duplicate_detection(self, content: str) -> bool:
        """Check if duplicate detection is enabled"""
        section = self._extract_section(content, "Duplicate Detection Rules")
        return section is not None
    
    def _has_dead_code_review(self, content: str) -> bool:
        """Check if dead code should be marked for review (vs deletion)"""
        section = self._extract_section(content, "Dead Code Review Rules")
        if not section:
            return False
        
        # Look for keywords indicating review mode
        review_keywords = ["mark for review", "don't delete", "review before"]
        return any(keyword in section.lower() for keyword in review_keywords)
    
    def _extract_known_conflicts(self, content: str) -> List[Dict[str, str]]:
        """Extract known integration conflicts"""
        conflicts = []
        
        section = self._extract_section(content, "Integration Conflicts")
        if not section:
            return conflicts
        
        # Pattern: - `file1` vs `file2`
        pattern = r'-\s+`([^`]+)`\s+vs\s+`([^`]+)`'
        matches = re.findall(pattern, section)
        
        for file1, file2 in matches:
            conflicts.append({
                "file1": file1.strip(),
                "file2": file2.strip(),
                "status": "detected"
            })
        
        return conflicts
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """
        Extract a section from markdown content.
        
        Returns the content between the section header and the next header.
        """
        # Pattern: ### Section Name (with optional #'s)
        pattern = rf'###?\s+{re.escape(section_name)}\s*\n(.*?)(?=\n###?\s+|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None


def get_architecture_config(project_dir: Path) -> ArchitectureConfig:
    """
    Get architecture configuration for a project.
    
    If ARCHITECTURE.md doesn't exist or can't be parsed, returns default config.
    """
    parser = ArchitectureParser(project_dir)
    config = parser.parse()
    
    if config is None:
        pass
        # Return default configuration
        return ArchitectureConfig(
            library_dirs=set(),
            application_dirs=set(),
            test_dirs={'tests/', 'test/'},
            preferred_file_naming="snake_case",
            preferred_module_naming="descriptive",
            class_naming_conventions={"default": "PascalCase"},
            duplicate_detection_enabled=False,
            dead_code_review_mode=False,
            known_conflicts=[],
        )
    
    return config