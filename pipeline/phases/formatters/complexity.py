"""
Complexity Formatter

Formats complexity analysis data.
"""

from .base import IssueFormatter


class ComplexityFormatter(IssueFormatter):
    """Formats complexity issues."""
    
    def format(self, data: dict) -> str:
        """Format complexity data."""
        func_name = data.get('name', 'unknown')
        complexity = data.get('complexity', 0)
        file_path = data.get('file', 'unknown')
        
        return f"""
HIGH COMPLEXITY DETECTED:
- Function: {func_name}
- File: {file_path}
- Complexity: {complexity}

ACTION REQUIRED:
1. Review the function to understand its logic
2. Break it down into smaller, focused functions
3. Use create_issue_report if refactoring requires major changes
"""