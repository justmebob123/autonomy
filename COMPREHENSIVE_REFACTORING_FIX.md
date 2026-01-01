# Comprehensive Refactoring Fix Plan

## Problems Identified

### 1. Analysis Data Not Formatted Properly
**Current**: `str(task.analysis_data)` - converts dict to string
**Problem**: AI gets messy string like `{'files': ['a.py', 'b.py'], 'similarity': 0.85}`
**Solution**: Format analysis_data into clear, actionable text

### 2. Prompt Doesn't Show Specific Example for Duplicates
**Current**: Generic workflow
**Problem**: AI doesn't see concrete example of what to do
**Solution**: Add specific example showing exact tool sequence

### 3. Task Description Too Generic
**Current**: "Duplicate code detected"
**Problem**: Doesn't tell AI WHICH files or WHAT to do
**Solution**: Include file names and similarity in description

## Implementation Plan

### Fix 1: Enhance Task Description
```python
# BEFORE:
description=f"Duplicate code: {dup.get('similarity', 0):.0%} similar"

# AFTER:
files = dup.get('files', [])
similarity = dup.get('similarity', 0)
description=f"Merge duplicate files: {files[0]} and {files[1]} ({similarity:.0%} similar)"
```

### Fix 2: Format Analysis Data in Context
```python
# BEFORE:
if task.analysis_data:
    affected_code = str(task.analysis_data)

# AFTER:
if task.analysis_data:
    affected_code = self._format_analysis_data(task.issue_type, task.analysis_data)

def _format_analysis_data(self, issue_type, data):
    if issue_type == RefactoringIssueType.DUPLICATE:
        files = data.get('files', [])
        similarity = data.get('similarity', 0)
        return f"""
DUPLICATE FILES DETECTED:
- File 1: {files[0] if len(files) > 0 else 'unknown'}
- File 2: {files[1] if len(files) > 1 else 'unknown'}
- Similarity: {similarity:.0%}

ACTION REQUIRED:
1. Use compare_file_implementations to analyze differences
2. Use merge_file_implementations to merge them
"""
```

### Fix 3: Add Concrete Example to Prompt
```python
# Add to _build_task_prompt:

📋 EXAMPLE - DUPLICATE CODE:
Task: api/resources.py and resources/resource_estimator.py are 85% similar
Step 1: compare_file_implementations(file1="api/resources.py", file2="resources/resource_estimator.py")
Step 2: merge_file_implementations(target="api/resources.py", source="resources/resource_estimator.py", strategy="keep_target_structure")
Result: ✅ Files merged, duplicate removed, task RESOLVED
```

### Fix 4: Make Title More Specific
```python
# BEFORE:
title=f"Duplicate code detected"

# AFTER:
files = dup.get('files', [])
file1_name = Path(files[0]).name if len(files) > 0 else 'unknown'
file2_name = Path(files[1]).name if len(files) > 1 else 'unknown'
title=f"Merge duplicates: {file1_name} ↔ {file2_name}"
```

## Expected Behavior After Fix

### Before Fix:
```
Task: "Duplicate code detected"
Description: "Duplicate code: 85% similar"
Context: "{'files': ['api/resources.py', 'resources/resource_estimator.py'], 'similarity': 0.85}"

AI sees: Generic task, unclear what to do
AI does: detect_duplicate_implementations (re-analyzes)
Result: ❌ FAILED - only analysis performed
```

### After Fix:
```
Task: "Merge duplicates: resources.py ↔ resource_estimator.py"
Description: "Merge duplicate files: api/resources.py and resources/resource_estimator.py (85% similar)"
Context: 
  DUPLICATE FILES DETECTED:
  - File 1: api/resources.py
  - File 2: resources/resource_estimator.py
  - Similarity: 85%
  
  ACTION REQUIRED:
  1. Use compare_file_implementations to analyze differences
  2. Use merge_file_implementations to merge them

AI sees: Clear task with specific files and action
AI does: 
  1. compare_file_implementations(api/resources.py, resources/resource_estimator.py)
  2. merge_file_implementations(target=api/resources.py, source=resources/resource_estimator.py)
Result: ✅ COMPLETED - files merged
```

## Files to Modify

1. `pipeline/phases/refactoring.py`:
   - Enhance task title (line ~696)
   - Enhance task description (line ~697)
   - Add `_format_analysis_data()` method
   - Update `_build_task_context()` to use formatted data
   - Add concrete example to `_build_task_prompt()`

## Testing

After fix, run pipeline and verify:
1. Task title shows specific file names
2. Task description is actionable
3. AI uses compare → merge sequence
4. Tasks complete successfully
5. No infinite loops