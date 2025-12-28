"""
Markdown Reporter - Generates comprehensive markdown reports.
"""

from typing import List, Dict, Any
from datetime import datetime


class MarkdownReporter:
    """Generates markdown reports from analysis results."""
    
    @staticmethod
    def generate(result: Any, filepath: str) -> str:
        """
        Generate comprehensive markdown report.
        
        Args:
            result: AnalysisResult object
            filepath: Path to analyzed file
            
        Returns:
            Markdown formatted report
        """
        md = f"""# DEPTH-61 ANALYSIS: {filepath}

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analyst**: Deep Code Analysis Framework v2.0  
**Lines**: {result.lines}  
**Complexity**: {result.complexity.get('average_complexity', 0):.1f} average  
**Severity**: {result.severity}

---

## 📊 EXECUTIVE SUMMARY

**Overall Assessment**: {result.severity}

**Metrics**:
- **Lines**: {result.lines}
- **Classes**: {result.classes}
- **Functions**: {result.functions}
- **Average Complexity**: {result.complexity.get('average_complexity', 0):.1f}
- **Max Complexity**: {result.complexity.get('max_complexity', 0)}
- **Issues Found**: {result.issues_count}

---

## 🐛 BUGS FOUND ({len(result.bugs)})

"""
        
        if result.bugs:
            for bug in result.bugs:
                md += f"""### {bug['severity']}: {bug['pattern']}

**Location**: {bug['location']} (line {bug['line']})  
**Message**: {bug['message']}

**Fix**:
```python
{bug['fix']}
```

**Example**:
```python
{bug['example']}
```

---

"""
        else:
            md += "✅ No bugs found!\n\n---\n\n"
        
        md += f"""## 📈 COMPLEXITY ANALYSIS

**Distribution**:
"""
        
        dist = result.complexity.get('complexity_distribution', {})
        for category, count in dist.items():
            md += f"- {category}: {count}\n"
        
        md += f"""
**Top 10 Most Complex Functions**:

"""
        
        for func in result.complexity.get('functions', [])[:10]:
            status = "🔴" if func['complexity'] > 50 else "⚠️" if func['complexity'] > 30 else "✅"
            md += f"{status} **{func['name']}** - Complexity: {func['complexity']} (line {func['line']})\n"
        
        md += "\n---\n\n"
        
        md += f"""## 🎯 RECOMMENDATIONS

"""
        
        for i, rec in enumerate(result.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        md += "\n---\n\n"
        md += f"**Analysis Complete**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return md