"""
Debugging Phase Prompt Builder.

Handles all prompt and message building for the Debugging phase,
extracted from the DebuggingPhase class to reduce complexity.
"""

from typing import Dict, List
from .shared.base_prompt_builder import BasePromptBuilder


class DebuggingPromptBuilder(BasePromptBuilder):
    """
    Prompt builder specifically for Debugging phase operations.
    
    Handles building prompts and messages for debugging tasks.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize Debugging prompt builder.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
    
    def build_debug_prompt(
        self,
        issue: Dict,
        filepath: str,
        file_content: str = None
    ) -> str:
        """
        Build prompt for debugging an issue.
        
        Args:
            issue: Dictionary containing issue details
            filepath: Path to the file with the issue
            file_content: Optional file content
            
        Returns:
            Formatted debug prompt
        """
        prompt = "# Debugging Task\n\n"
        
        # Add issue context
        prompt += self.build_error_context(issue)
        
        # Add file context
        if file_content:
            prompt += f"## File Content: {filepath}\n\n"
            prompt += f"```python\n{file_content}\n```\n\n"
        else:
            prompt += self.build_file_context(filepath, include_content=True)
        
        prompt += """
## Instructions

Please analyze the issue and provide a fix:

1. **Understand the Issue**: Review the error details and file content
2. **Identify Root Cause**: Determine what's causing the issue
3. **Propose Solution**: Suggest the appropriate fix
4. **Implement Fix**: Apply the fix to the code
5. **Verify**: Ensure the fix resolves the issue without introducing new problems

## Deliverables

- Clear explanation of the root cause
- Proposed fix with rationale
- Updated code with the fix applied
- Any additional recommendations

"""
        return prompt
    
    def build_debug_message(
        self,
        issue: Dict,
        filepath: str
    ) -> str:
        """
        Build debug message for inter-phase communication.
        
        Args:
            issue: Dictionary containing issue details
            filepath: Path to the file with the issue
            
        Returns:
            Formatted debug message
        """
        message = f"""
## Debug Request

**File**: {filepath}
**Issue Type**: {issue.get('type', 'Unknown')}
**Severity**: {issue.get('severity', 'Unknown')}

### Issue Description

{issue.get('description', 'No description provided')}

"""
        
        if issue.get('line'):
            message += f"**Line**: {issue['line']}\n"
        
        if issue.get('recommendation'):
            message += f"\n### Recommendation\n\n{issue['recommendation']}\n"
        
        message += "\n### Next Steps\n\n"
        message += "1. Analyze the issue\n"
        message += "2. Implement the fix\n"
        message += "3. Verify the fix resolves the issue\n"
        message += "4. Submit for QA review\n"
        
        return message
    
    def build_qa_phase_message(
        self,
        filepath: str,
        issue: Dict,
        fix_applied: bool,
        timestamp: str
    ) -> str:
        """
        Build message to send to QA phase after debugging.
        
        Args:
            filepath: Path to the debugged file
            issue: Dictionary containing issue details
            fix_applied: Whether the fix was successfully applied
            timestamp: Timestamp of the debugging session
            
        Returns:
            Formatted message for QA_READ.md
        """
        if fix_applied:
            message = f"""
## Debug Fix Applied - {timestamp}

**File**: {filepath}
**Issue Type**: {issue.get('type', 'Unknown')}
**Status**: ✅ Fix Applied

### Issue Details

**Description**: {issue.get('description', 'No description')}
**Line**: {issue.get('line', 'N/A')}
**Severity**: {issue.get('severity', 'Unknown')}

### Fix Summary

The issue has been analyzed and a fix has been applied to the code.

### Next Steps

1. Re-run QA analysis on the file
2. Verify the fix resolves the issue
3. Check for any potential regressions
4. Approve if all checks pass

**Priority**: Please review at your earliest convenience.

"""
        else:
            message = f"""
## Debug Attempt Failed - {timestamp}

**File**: {filepath}
**Issue Type**: {issue.get('type', 'Unknown')}
**Status**: ❌ Fix Failed

### Issue Details

**Description**: {issue.get('description', 'No description')}
**Line**: {issue.get('line', 'N/A')}
**Severity**: {issue.get('severity', 'Unknown')}

### Failure Reason

The debugging attempt was unsuccessful. Possible reasons:
- Issue requires manual intervention
- More context needed to understand the problem
- Architectural changes required

### Recommendation

Please review the issue manually or provide additional context.

"""
        
        return message
    
    def build_coding_phase_message(
        self,
        filepath: str,
        fix_applied: bool,
        timestamp: str
    ) -> str:
        """
        Build message to send to coding phase about debug results.
        
        Args:
            filepath: Path to the debugged file
            fix_applied: Whether the fix was successfully applied
            timestamp: Timestamp of the debugging session
            
        Returns:
            Formatted message for DEVELOPER_READ.md
        """
        if fix_applied:
            message = f"""
## Debug Fix Notification - {timestamp}

**File**: {filepath}
**Status**: ✅ Fix Applied

A bug fix has been applied to this file. The file has been updated and is ready for QA review.

### Next Steps

- File marked for QA review
- Awaiting QA verification
- Will be approved once QA passes

"""
        else:
            message = f"""
## Debug Attempt Notification - {timestamp}

**File**: {filepath}
**Status**: ⚠️ Fix Unsuccessful

A debugging attempt was made but the fix could not be applied automatically.

### Next Steps

- Manual review may be required
- Additional context may be needed
- Consider architectural changes if necessary

"""
        
        return message