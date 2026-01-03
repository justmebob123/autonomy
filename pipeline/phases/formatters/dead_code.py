"""
Dead Code Formatter

Formats dead code analysis data.
"""

from .base import IssueFormatter


class DeadCodeFormatter(IssueFormatter):
    """Formats dead code issues."""
    
    def format(self, data: dict) -> str:
        """Format dead code data."""
        file_path = data.get('file', 'unknown')
        class_name = data.get('class', 'unknown')
        function_name = data.get('function', 'unknown')
        
        item_name = class_name if class_name != 'unknown' else function_name
        
        return f"""
DEAD CODE DETECTED:
- File: {file_path}
- Item: {item_name}

⚠️ CRITICAL: This is an EARLY-STAGE project - DO NOT auto-remove code!

ACTION REQUIRED:
1. Search for usages of this code
2. Create issue report for tracking

EXAMPLE:
create_issue_report(
    title="Dead Code: {item_name}",
    description="Analysis of {item_name} usage in {file_path}",
    severity="low",
    recommendations=["Keep for now", "Monitor usage", "Remove if still unused after review"]
)

✅ DO:
- Search for usages
- Create issue report
- Recommend monitoring

⚠️ DO NOT:
- Auto-remove code
- Delete without analysis
- Assume code is unused without searching
"""