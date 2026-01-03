"""
Architecture Formatter

Formats architecture violation analysis data.
"""

from .base import IssueFormatter


class ArchitectureFormatter(IssueFormatter):
    """Formats architecture violation issues."""
    
    def format(self, data: dict) -> str:
        """Format architecture violation data."""
        file_path = data.get('file', 'unknown')
        violation_type = data.get('type', 'unknown')
        expected_location = data.get('expected_location', 'unknown')
        current_location = data.get('current_location', file_path)
        
        return f"""
ARCHITECTURE VIOLATION DETECTED:
- File: {file_path}
- Type: {violation_type}
- Current Location: {current_location}
- Expected Location: {expected_location}

ACTION REQUIRED:
1. Read ARCHITECTURE.md to understand correct structure
2. Fix the violation using appropriate tools

TOOLS:
- move_file: Relocate misplaced files
- rename_file: Fix naming issues
- restructure_directory: Large structural changes

EXAMPLE:
move_file(
    source="{current_location}",
    destination="{expected_location}"
)
"""