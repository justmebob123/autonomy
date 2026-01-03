"""
Shared status formatter for all phases.

This module provides a unified way to format status messages for different phases,
eliminating the duplicate _format_status_for_write methods across phases.
"""

from typing import Dict, List, Any
from datetime import datetime


class StatusFormatter:
    """
    Shared formatter for phase status writes.
    
    Provides static methods to format status messages for different phases,
    maintaining consistent formatting while eliminating code duplication.
    """
    
    @staticmethod
    def format_timestamp() -> str:
        """Format current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    @staticmethod
    def format_debugging_status(
        issue: Dict,
        filepath: str,
        fix_applied: bool,
        files_modified: List[str],
        timestamp: str = None
    ) -> str:
        """
        Format status for DEBUG_WRITE.md
        
        Args:
            issue: Dictionary containing issue details (type, description, line, severity)
            filepath: Path to the file being debugged
            fix_applied: Whether the fix was successfully applied
            files_modified: List of files that were modified
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            Formatted status string for debugging phase
        """
        if timestamp is None:
            timestamp = StatusFormatter.format_timestamp()
            
        status = f"""# Debugging Phase Status

**Timestamp**: {timestamp}
**File**: {filepath}
**Status**: {'✅ Fix Applied' if fix_applied else '❌ Fix Failed'}

## Issue Details

**Type**: {issue.get('type', 'N/A')}
**Description**: {issue.get('description', 'N/A')}
**Line**: {issue.get('line', 'N/A')}
**Severity**: {issue.get('severity', 'N/A')}

"""
        
        if fix_applied:
            status += f"## Fix Summary\n\n"
            status += f"**Files Modified**: {len(files_modified)}\n\n"
            for filepath in files_modified:
                status += f"- `{filepath}`\n"
            
            status += "\n## Verification Needed\n\n"
            status += "- Fix has been applied to the code\n"
            status += "- File marked for QA re-review\n"
            status += "- Please verify the fix resolves the issue\n"
            status += "- Check for any potential regressions\n"
        else:
            status += "## Fix Attempt Failed\n\n"
            status += "The debugging attempt was unsuccessful. Possible reasons:\n"
            status += "- Issue requires manual intervention\n"
            status += "- More context needed to understand the problem\n"
            status += "- Architectural changes required\n"
            status += "\n**Recommendation**: Review the issue manually or provide additional context.\n"
        
        return status
    
    @staticmethod
    def format_qa_status(
        filepath: str,
        issues_found: List[Dict],
        approved: bool,
        timestamp: str = None
    ) -> str:
        """
        Format status for QA_WRITE.md
        
        Args:
            filepath: Path to the file being reviewed
            issues_found: List of issues found during QA (each with severity, line, description, recommendation)
            approved: Whether the file was approved
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            Formatted status string for QA phase
        """
        if timestamp is None:
            timestamp = StatusFormatter.format_timestamp()
            
        status = f"""# QA Phase Status

**Timestamp**: {timestamp}
**File Reviewed**: {filepath}
**Status**: {'✅ Approved' if approved else '❌ Issues Found'}

## Review Summary

"""
        
        if issues_found:
            status += f"**Total Issues**: {len(issues_found)}\n\n"
            
            # Group by severity
            by_severity = {}
            for issue in issues_found:
                severity = issue.get('severity', 'unknown')
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            # Report by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in by_severity:
                    issues = by_severity[severity]
                    status += f"### {severity.title()} Priority ({len(issues)} issues)\n\n"
                    for issue in issues[:5]:  # Show first 5
                        status += f"- **Line {issue.get('line', 'N/A')}**: {issue.get('description', 'N/A')}\n"
                        if issue.get('recommendation'):
                            status += f"  - *Recommendation*: {issue['recommendation']}\n"
                    if len(issues) > 5:
                        status += f"  - ... and {len(issues) - 5} more\n"
                    status += "\n"
        else:
            status += "✅ No issues found. Code meets quality standards.\n\n"
        
        status += "## Next Steps\n\n"
        if issues_found:
            status += "- Issues sent to debugging phase\n"
            status += "- Awaiting fixes and resubmission\n"
        else:
            status += "- File approved and marked as reviewed\n"
            status += "- Ready for deployment or next phase\n"
        
        return status
    
    @staticmethod
    def format_coding_status(
        task: Any,  # TaskState object
        files_created: List[str],
        files_modified: List[str],
        complexity_warnings: List[str],
        timestamp: str = None
    ) -> str:
        """
        Format status for DEVELOPER_WRITE.md
        
        Args:
            task: TaskState object with task_id, description, target_file, attempts
            files_created: List of files that were created
            files_modified: List of files that were modified
            complexity_warnings: List of complexity warning messages
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            Formatted status string for coding phase
        """
        if timestamp is None:
            timestamp = StatusFormatter.format_timestamp()
            
        status = f"""# Coding Phase Status

**Timestamp**: {timestamp}
**Status**: Task Completed
**Task ID**: {task.task_id}

## Task Summary
**Description**: {task.description}
**Target File**: {task.target_file}
**Attempt**: {task.attempts}

## Changes Made

### Files Created ({len(files_created)})
"""
        
        for filepath in files_created:
            status += f"- `{filepath}`\n"
        
        status += f"\n### Files Modified ({len(files_modified)})\n"
        for filepath in files_modified:
            status += f"- `{filepath}`\n"
        
        status += "\n## Quality Metrics\n\n"
        
        if complexity_warnings:
            status += f"⚠️ **Complexity Warnings**: {len(complexity_warnings)}\n\n"
            for warning in complexity_warnings:
                status += f"- {warning}\n"
        else:
            status += "✅ No complexity warnings detected\n"
        
        status += f"\n## Next Steps\n\n"
        status += f"- Task marked as QA_PENDING\n"
        status += f"- Files ready for quality assurance review\n"
        status += f"- Awaiting QA phase verification\n"
        
        return status