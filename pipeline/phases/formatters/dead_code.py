"""
Dead Code Formatter

Formats dead code analysis data with comprehensive analysis.
"""

from .base import IssueFormatter
import logging


class DeadCodeFormatter(IssueFormatter):
    """Formats dead code issues with comprehensive analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format(self, data: dict) -> str:
        """Format dead code data with comprehensive analysis."""
        item_name = data.get('name', 'unknown') if isinstance(data, dict) else 'unknown'
        item_file = data.get('file', 'unknown') if isinstance(data, dict) else 'unknown'
        item_type = data.get('type', 'function') if isinstance(data, dict) else 'function'
        
        # Try to perform comprehensive analysis
        try:
            from pipeline.analysis.unused_code_analyzer import UnusedCodeAnalyzer, UnusedCodeDecision
            from pathlib import Path
            
            # Get project dir from data or use current
            project_dir = data.get('project_dir', '.')
            analyzer = UnusedCodeAnalyzer(str(project_dir), self.logger)
            analysis = analyzer.analyze(item_file, item_name, item_type)
            
            # Generate response based on analysis decision
            if analysis.decision == UnusedCodeDecision.INTEGRATE:
                return f"""
DEAD CODE ANALYSIS - INTEGRATION RECOMMENDED:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: INTEGRATE (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

INTEGRATION PLAN:
{analysis.integration_plan}

ACTION: Create issue report with integration plan
"""
            elif analysis.decision == UnusedCodeDecision.KEEP:
                return f"""
DEAD CODE ANALYSIS - KEEP FOR FUTURE:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: KEEP (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

ACTION: Mark task complete - code should be kept
"""
            else:  # REPORT
                related_files_str = ', '.join(analysis.related_files[:3]) if analysis.related_files else 'none'
                return f"""
DEAD CODE ANALYSIS - REVIEW REQUIRED:
- Item: {item_name}
- File: {item_file}
- Project: {analysis.project_stage} stage ({analysis.completion_percentage:.1f}% complete)
- Decision: REPORT (Confidence: {analysis.confidence:.0%})

{analysis.reasoning}

Related files: {related_files_str}

ACTION: Create issue report for developer review
"""
        except Exception as e:
            self.logger.warning(f"Could not perform dead code analysis: {e}")
            return self._format_simple_dead_code(item_name, item_file)
    
    def _format_simple_dead_code(self, item_name: str, item_file: str) -> str:
        """Simple format for dead code when analysis fails."""
        return f"""
DEAD CODE DETECTED:
- File: {item_file}
- Item: {item_name}

⚠️ CRITICAL: This is an EARLY-STAGE project - DO NOT auto-remove code!

ACTION REQUIRED:
1. Search for usages of this code
2. Create issue report for tracking

EXAMPLE:
create_issue_report(
    title="Dead Code: {item_name}",
    description="Analysis of {item_name} usage in {item_file}",
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