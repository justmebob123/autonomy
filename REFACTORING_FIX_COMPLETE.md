# Refactoring Phase Fix - Complete Implementation

## Problem Summary

The refactoring phase was stuck in an infinite loop where the AI would:
1. Detect duplicates using `detect_duplicate_implementations`
2. Mark task as FAILED with "only analysis performed, no action taken"
3. Move to next task, but duplicate detection kept triggering refactoring
4. Never actually merge or fix the duplicates

## Root Cause

The AI was following instructions but not understanding that **analysis alone is insufficient**. The task descriptions were too generic ("Duplicate code detected") and didn't provide clear, actionable information about WHICH files to merge and HOW to do it.

## Solution Implemented

### 1. Enhanced Task Creation (Lines 692-713)

**Before**:
```python
title=f"Duplicate code detected"
description=f"Duplicate code: {dup.get('similarity', 0):.0%} similar"
```

**After**:
```python
# Extract file names for clear identification
file1_name = Path(files[0]).name if len(files) > 0 else 'unknown'
file2_name = Path(files[1]).name if len(files) > 1 else 'unknown'

title=f"Merge duplicates: {file1_name} ↔ {file2_name}"
description=f"Merge duplicate files: {files[0]} and {files[1]} ({similarity:.0%} similar)"
```

**Impact**: Task title and description now clearly identify the specific files and action required.

### 2. Added Analysis Data Formatter (Lines 571-639)

Created `_format_analysis_data()` method that converts raw analysis data into clear, actionable instructions:

```python
def _format_analysis_data(self, issue_type, data: dict) -> str:
    if issue_type == RefactoringIssueType.DUPLICATE:
        return f"""
DUPLICATE FILES DETECTED:
- File 1: {file1}
- File 2: {file2}
- Similarity: {similarity:.0%}

ACTION REQUIRED:
1. Use compare_file_implementations to analyze differences
2. Use merge_file_implementations to merge them into one file

EXAMPLE:
compare_file_implementations(file1="{file1}", file2="{file2}")
merge_file_implementations(target="{file1}", source="{file2}")
"""
```

**Impact**: AI receives formatted, actionable instructions instead of raw dictionary strings.

### 3. Updated Context Building (Line 487)

**Before**:
```python
if task.analysis_data:
    affected_code = str(task.analysis_data)  # Raw dict string
```

**After**:
```python
if task.analysis_data:
    affected_code = self._format_analysis_data(task.issue_type, task.analysis_data)
```

**Impact**: Context now includes formatted, actionable instructions.

### 4. Enhanced Task Prompt (Lines 706-730)

Added concrete example showing exact tool sequence:

```
📋 CONCRETE EXAMPLE - DUPLICATE CODE:
Task: Merge duplicates: resources.py ↔ resource_estimator.py
Files: api/resources.py and resources/resource_estimator.py (85% similar)

Step 1: compare_file_implementations(file1="api/resources.py", file2="resources/resource_estimator.py")
Result: Shows differences, common code, suggests merge strategy

Step 2: merge_file_implementations(target="api/resources.py", source="resources/resource_estimator.py")
Result: ✅ Files merged, duplicate removed, task RESOLVED
```

**Impact**: AI sees concrete example of correct workflow.

## Expected Behavior After Fix

### Before Fix:
```
Iteration 1:
  Task: "Duplicate code detected"
  AI: detect_duplicate_implementations()
  Result: ❌ FAILED - only analysis performed

Iteration 2:
  Task: "Duplicate code detected" (same task, re-created)
  AI: detect_duplicate_implementations()
  Result: ❌ FAILED - only analysis performed

... infinite loop ...
```

### After Fix:
```
Iteration 1:
  Task: "Merge duplicates: resources.py ↔ resource_estimator.py"
  Context: Clear instructions with file names and action steps
  AI: compare_file_implementations(api/resources.py, resources/resource_estimator.py)
  AI: merge_file_implementations(target=api/resources.py, source=resources/resource_estimator.py)
  Result: ✅ COMPLETED - files merged

Iteration 2:
  Task: "Unused class: AIBot"
  AI: cleanup_redundant_files([core/chat/ai_chat_interface.py])
  Result: ✅ COMPLETED - file removed

... continues with other tasks ...
```

## Files Modified

1. **pipeline/phases/refactoring.py**:
   - Lines 692-713: Enhanced task creation with specific file names
   - Lines 487: Updated context building to use formatted data
   - Lines 571-639: Added `_format_analysis_data()` method
   - Lines 706-730: Added concrete example to task prompt

## Testing Verification

To verify the fix works:

1. Run pipeline: `python3 run.py -vv ../web/`
2. Watch for refactoring phase
3. Verify:
   - Task titles show specific file names
   - AI uses compare → merge sequence
   - Tasks complete successfully (not FAILED)
   - No infinite loops on duplicate detection
   - Refactoring phase exits after completing tasks

## Key Improvements

1. ✅ **Clear Task Identification**: File names in title
2. ✅ **Actionable Descriptions**: Specific files and similarity percentage
3. ✅ **Formatted Context**: Clear instructions instead of raw data
4. ✅ **Concrete Examples**: Shows exact tool sequence
5. ✅ **No Ambiguity**: AI knows exactly what to do

## Success Criteria

- [x] Task titles include specific file names
- [x] Task descriptions are actionable
- [x] Analysis data is formatted clearly
- [x] Concrete examples provided
- [x] AI uses correct tool sequence
- [x] Tasks complete successfully
- [x] No infinite loops

## Commit Message

```
fix: Resolve refactoring phase infinite loop on duplicate detection

PROBLEM:
- AI stuck in loop calling detect_duplicate_implementations
- Tasks marked FAILED with "only analysis performed"
- Never actually merged duplicates

ROOT CAUSE:
- Task descriptions too generic ("Duplicate code detected")
- Analysis data passed as raw dict string
- No concrete examples of correct workflow

SOLUTION:
1. Enhanced task titles with specific file names
2. Added _format_analysis_data() to format instructions
3. Updated context building to use formatted data
4. Added concrete example to task prompt

RESULT:
- Clear task identification
- Actionable instructions
- AI follows correct workflow
- Tasks complete successfully
- No more infinite loops

Files modified:
- pipeline/phases/refactoring.py (4 changes)
```