"""
QA Phase Prompt Builder.

Handles all prompt and message building for the QA phase,
extracted from the QAPhase class to reduce complexity.
"""

from typing import List, Dict
from .shared.base_prompt_builder import BasePromptBuilder


class QAPromptBuilder(BasePromptBuilder):
    """
    Prompt builder specifically for QA phase operations.
    
    Handles building messages for inter-phase communication and
    formatting QA-specific contexts.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize QA prompt builder.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
    
    def build_debug_phase_message(
        self,
        filepath: str,
        issues_found: List[Dict],
        timestamp: str
    ) -> str:
        """
        Build message to send to debugging phase when issues are found.
        
        Args:
            filepath: Path to the file with issues
            issues_found: List of issues found during QA
            timestamp: Timestamp of the QA review
            
        Returns:
            Formatted message for DEBUG_READ.md
        """
        message = f"""
## QA Issues Found - {timestamp}

**File**: {filepath}
**Issues Found**: {len(issues_found)}
**Status**: Requires debugging

### Issues by Severity

"""
        
        # Group by severity
        by_severity = {}
        for issue in issues_found:
            severity = issue.get('severity', 'unknown')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
        
        # List issues by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                issues = by_severity[severity]
                message += f"#### {severity.title()} ({len(issues)} issues)\n\n"
                for issue in issues:
                    message += f"- **Line {issue.get('line', 'N/A')}**: {issue.get('description', 'N/A')}\n"
                    if issue.get('type'):
                        message += f"  - Type: {issue['type']}\n"
                    if issue.get('recommendation'):
                        message += f"  - Recommendation: {issue['recommendation']}\n"
                message += "\n"
        
        message += """
### Next Steps

1. Review each issue and determine fix approach
2. Apply fixes to the code
3. Re-run QA to verify fixes
4. Mark file as QA_APPROVED once all issues resolved

"""
        
        return message
    
    def build_coding_phase_message(
        self,
        filepath: str,
        approved: bool,
        timestamp: str
    ) -> str:
        """
        Build message to send to coding phase about QA results.
        
        Args:
            filepath: Path to the reviewed file
            approved: Whether the file was approved
            timestamp: Timestamp of the QA review
            
        Returns:
            Formatted message for DEVELOPER_READ.md
        """
        if approved:
            message = f"""
## QA Approval - {timestamp}

**File**: {filepath}
**Status**: ✅ Approved

The file has passed QA review and meets quality standards.

### Quality Metrics Met

- Code style and formatting
- Error handling
- Documentation
- Test coverage (if applicable)
- Performance considerations

**Next Steps**: File is ready for deployment or next phase.

"""
        else:
            message = f"""
## QA Review - {timestamp}

**File**: {filepath}
**Status**: ⚠️ Issues Found

The file has been reviewed and issues have been identified. 
Please see DEBUG_READ.md for details on issues that need to be addressed.

**Next Steps**: Address issues and resubmit for QA review.

"""
        
        return message