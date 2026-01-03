"""
Duplicate Code Formatter

Formats duplicate code analysis data.
"""

from .base import IssueFormatter


class DuplicateCodeFormatter(IssueFormatter):
    """Formats duplicate code issues."""
    
    def format(self, data: dict) -> str:
        """Format duplicate code data."""
        files = data.get('files', [])
        similarity = data.get('similarity', 0)
        file1 = files[0] if len(files) > 0 else 'unknown'
        file2 = files[1] if len(files) > 1 else 'unknown'
        
        return f"""
DUPLICATE FILES DETECTED:
- File 1: {file1}
- File 2: {file2}
- Similarity: {similarity:.0%}

ACTION REQUIRED:
Use merge_file_implementations to merge these duplicate files into one.

EXAMPLE:
merge_file_implementations(
    source_files=["{file1}", "{file2}"],
    target_file="{file1}",
    strategy="ai_merge"
)

OPTIONAL: If you want to understand the differences first, you CAN compare:
compare_file_implementations(file1="{file1}", file2="{file2}")
BUT you MUST still call merge_file_implementations after comparing!

The merge tool will:
- Automatically handle imports
- Preserve all functionality
- Remove duplicates
- Create backups
"""