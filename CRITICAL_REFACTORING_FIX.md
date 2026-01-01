# CRITICAL: Refactoring Phase Not Taking Action

## Problem Analysis

The AI is calling `compare_file_implementations` to analyze integration conflicts, but then **stopping without taking any resolving action**. This causes tasks to fail with:

```
⚠️ Task refactor_0355: Tools succeeded but issue not resolved - only analysis performed, no action taken
```

## Root Cause

Despite comprehensive prompts telling the AI to:
1. Compare files (optional)
2. Then RESOLVE with merge/report/review

The AI is:
1. Comparing files ✅
2. Stopping ❌

## Why This Happens

The AI sees the comparison result (e.g., "50% similar, manual_review recommended") and interprets "manual_review" as "I should stop and let a human handle this."

## Solution: Force Action After Analysis

We need to make the system **automatically** take the next step when the AI only performs analysis.

### Option 1: Auto-Create Report After Compare (RECOMMENDED)

If AI calls `compare_file_implementations` without following up with a resolving tool, automatically create an issue report with the comparison results.

### Option 2: Remove compare_file_implementations from Available Tools

Force AI to go directly to merge/report/review without the comparison step.

### Option 3: Multi-Turn Enforcement

After AI calls compare, immediately prompt it again: "You compared the files. Now you MUST take action: merge, report, or review."

## Recommended Implementation

**Option 1** is best because:
- Preserves AI's ability to analyze
- Ensures every task gets resolved
- Creates useful documentation
- No infinite loops

### Code Changes Needed

In `pipeline/phases/refactoring.py`, after tool execution:

```python
# After executing tools, check if only analysis was performed
analysis_only_tools = {"compare_file_implementations", "detect_duplicate_implementations", "analyze_complexity"}
resolving_tools = {"merge_file_implementations", "cleanup_redundant_files", "create_issue_report", "request_developer_review"}

tools_used = {result.get("tool") for result in results if result.get("success")}

if tools_used.issubset(analysis_only_tools):
    # AI only analyzed, didn't resolve - auto-create report
    self.logger.warning(f"  ⚠️ Task {task.task_id}: Only analysis performed, auto-creating issue report")
    
    # Extract comparison/analysis results
    analysis_data = {}
    for result in results:
        if result.get("success"):
            analysis_data[result.get("tool")] = result.get("result")
    
    # Auto-create issue report
    report_result = self._handle_create_issue_report({
        "task_id": task.task_id,
        "severity": "medium",
        "impact_analysis": f"Integration conflict requires manual review: {task.description}",
        "recommended_approach": "Review comparison results and determine merge strategy",
        "code_examples": str(analysis_data),
        "estimated_effort": "30 minutes"
    })
    
    if report_result.get("success"):
        task.complete("Auto-created issue report after analysis")
        return PhaseResult(success=True, ...)
```

This ensures:
- ✅ Every task gets resolved (either fixed or documented)
- ✅ No infinite loops
- ✅ AI's analysis is preserved in the report
- ✅ Developer gets actionable information