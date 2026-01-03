"""
Issue Formatters

Formats analysis data for different refactoring issue types.
"""

from .base import IssueFormatter
from .duplicate_code import DuplicateCodeFormatter
from .complexity import ComplexityFormatter
from .integration_conflict import IntegrationConflictFormatter
from .dead_code import DeadCodeFormatter
from .architecture import ArchitectureFormatter

# Formatter registry (lowercase keys to match enum values)
FORMATTERS = {
    'duplicate': DuplicateCodeFormatter(),
    'complexity': ComplexityFormatter(),
    'integration': IntegrationConflictFormatter(),
    'conflict': IntegrationConflictFormatter(),
    'dead_code': DeadCodeFormatter(),
    'architecture': ArchitectureFormatter(),
}


def get_formatter(issue_type) -> IssueFormatter:
    """
    Get formatter for issue type.
    
    Args:
        issue_type: RefactoringIssueType enum or string
    
    Returns:
        IssueFormatter instance
    """
    # Convert enum to string if needed
    if hasattr(issue_type, 'value'):
        issue_type_str = issue_type.value
    else:
        issue_type_str = str(issue_type)
    
    # Get formatter or use base as fallback
    formatter = FORMATTERS.get(issue_type_str)
    if formatter:
        return formatter
    
    # Fallback to base formatter
    return IssueFormatter()


__all__ = [
    'IssueFormatter',
    'DuplicateCodeFormatter',
    'ComplexityFormatter',
    'IntegrationConflictFormatter',
    'DeadCodeFormatter',
    'ArchitectureFormatter',
    'get_formatter',
]