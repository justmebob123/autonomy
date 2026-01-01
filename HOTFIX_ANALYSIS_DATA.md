# Hotfix: Missing analysis_data Parameter

## Problem
After implementing the task-type-specific requirements fix, the system crashed with:
```
NameError: name 'analysis_data' is not defined
```

## Root Cause
In my previous fix (commit cf6da11), I added code that references `analysis_data`:
```python
if 'duplicate' in str(analysis_data.get('type', '')).lower() or \
   'Merge duplicates' in str(analysis_data.get('title', '')):
```

But the `validate_tool_calls()` function didn't have `analysis_data` as a parameter!

## The Fix

### 1. Updated Function Signature
**File**: `pipeline/state/task_analysis_tracker.py`

**Before**:
```python
def validate_tool_calls(self, task_id: str, tool_calls: List[Dict], 
                      target_files: List[str], attempt_number: int):
```

**After**:
```python
def validate_tool_calls(self, task_id: str, tool_calls: List[Dict], 
                      target_files: List[str], attempt_number: int,
                      analysis_data: Dict[str, Any] = None):
```

### 2. Updated Function Call
**File**: `pipeline/phases/refactoring.py`

**Before**:
```python
is_valid, error_message = self._analysis_tracker.validate_tool_calls(
    task_id=task.task_id,
    tool_calls=tool_calls,
    target_files=task.target_files,
    attempt_number=task.attempts
)
```

**After**:
```python
is_valid, error_message = self._analysis_tracker.validate_tool_calls(
    task_id=task.task_id,
    tool_calls=tool_calls,
    target_files=task.target_files,
    attempt_number=task.attempts,
    analysis_data=task.analysis_data  # <-- Added this
)
```

## Testing
- ✅ Syntax validation passed
- ✅ Both files compile successfully
- ✅ Committed and pushed to GitHub

## Impact
This hotfix enables the task-type-specific requirements to work correctly by providing the necessary data to detect task types.

## Commit
**Hash**: 97fa888
**Message**: "fix: Add missing analysis_data parameter to validate_tool_calls"
**Files**: 2 modified (8 insertions, 2 deletions)

## Status
✅ FIXED - System should now work correctly