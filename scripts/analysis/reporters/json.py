"""
JSON Reporter - Generates JSON reports for programmatic access.
"""

import json
from typing import Any
from datetime import datetime


class JSONReporter:
    """Generates JSON reports from analysis results."""
    
    @staticmethod
    def generate(result: Any) -> str:
        """
        Generate JSON report.
        
        Args:
            result: AnalysisResult object
            
        Returns:
            JSON formatted report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'filepath': result.filepath,
            'severity': result.severity,
            'metrics': {
                'lines': result.lines,
                'classes': result.classes,
                'functions': result.functions,
                'issues_count': result.issues_count,
            },
            'complexity': result.complexity,
            'bugs': result.bugs,
            'antipatterns': result.antipatterns,
            'deadcode': result.deadcode,
            'recommendations': result.recommendations,
        }
        
        return json.dumps(report, indent=2)