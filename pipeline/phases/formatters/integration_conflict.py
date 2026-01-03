"""
Integration Conflict Formatter

Formats integration conflict analysis data.
"""

from .base import IssueFormatter
import logging


class IntegrationConflictFormatter(IssueFormatter):
    """Formats integration conflict issues."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format(self, data: dict) -> str:
        """Format integration conflict data."""
        # Check if this is an unused code issue
        issue_desc = str(data).lower()
        if 'unused' in issue_desc or 'never instantiated' in issue_desc or 'dead code' in issue_desc:
            return self._format_unused_code(data)
        else:
            return self._format_regular_conflict(data)
    
    def _format_unused_code(self, data: dict) -> str:
        """Format unused code issue with analysis."""
        file_path = data.get('file', 'unknown') if isinstance(data, dict) else 'unknown'
        class_name = data.get('class', 'unknown') if isinstance(data, dict) else 'unknown'
        
        # Try to perform analysis if analyzer is available
        try:
            from pipeline.analysis.unused_code_analyzer import UnusedCodeAnalyzer, UnusedCodeDecision
            from pathlib import Path
            
            # Get project dir from data or use current
            project_dir = data.get('project_dir', '.')
            analyzer = UnusedCodeAnalyzer(str(project_dir), self.logger)
            analysis = analyzer.analyze(file_path, class_name, 'class')
            
            # Format based on decision
            if analysis.decision == UnusedCodeDecision.INTEGRATE:
                return f"""
UNUSED CODE ANALYSIS - INTEGRATION RECOMMENDED:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Architecture Alignment: {analysis.architecture_alignment}
- Decision: INTEGRATE (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

INTEGRATION PLAN:
{analysis.integration_plan}

ACTION REQUIRED:
This unused code appears to be a SUPERIOR implementation that should be integrated.
Use create_issue_report to document the integration plan.

✅ This code should be INTEGRATED, not removed!
"""
            elif analysis.decision == UnusedCodeDecision.KEEP:
                return f"""
UNUSED CODE ANALYSIS - KEEP FOR FUTURE USE:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Decision: KEEP (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

ACTION REQUIRED:
Mark this task as complete - this code should be KEPT for future integration.

✅ This code is part of planned architecture - KEEP IT!
"""
            else:  # REPORT
                return f"""
UNUSED CODE ANALYSIS - DEVELOPER REVIEW REQUIRED:
- File: {file_path}
- Item: {class_name}
- Project Stage: {analysis.project_stage} ({analysis.completion_percentage:.1f}% complete)
- Decision: REPORT (Confidence: {analysis.confidence:.0%})

ANALYSIS:
{analysis.reasoning}

ACTION REQUIRED:
Create an issue report for developer review.

⚠️ Requires developer review to make final decision
"""
        except Exception as e:
            self.logger.warning(f"Could not perform unused code analysis: {e}")
            return self._format_simple_unused_code(file_path, class_name)
    
    def _format_simple_unused_code(self, file_path: str, class_name: str) -> str:
        """Simple format for unused code when analysis fails."""
        return f"""
UNUSED CODE DETECTED:
- File: {file_path}
- Item: {class_name}

ACTION REQUIRED:
1. Search for usages of this code
2. Determine if it's part of planned architecture
3. Create issue report for review

⚠️ Do not auto-remove - requires analysis
"""
    
    def _format_regular_conflict(self, data: dict) -> str:
        """Format regular integration conflict."""
        files = data.get('files', []) if isinstance(data, dict) else []
        description = data.get('description', 'Unknown conflict') if isinstance(data, dict) else str(data)
        conflict_type = data.get('type', 'unknown') if isinstance(data, dict) else 'unknown'
        
        file_list = "\n".join(f"- {f}" for f in files) if files else "- (files not specified)"
        
        return f"""
INTEGRATION CONFLICT DETECTED:
Type: {conflict_type}
Description: {description}

Files involved:
{file_list}

ACTION REQUIRED:
1. Read ARCHITECTURE.md to understand design intent
2. Compare the conflicting implementations
3. Merge or resolve the conflict
4. Update architecture if needed
"""