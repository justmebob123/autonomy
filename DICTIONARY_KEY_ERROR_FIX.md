# Dictionary Key Error Fix

## Problem

The refactoring phase was encountering errors with dictionary key error tasks:

1. **Invalid key_path values**: Tasks created with `key_path='0'` or other numeric/invalid values
2. **AI confusion**: AI didn't know how to fix these tasks due to incomplete data
3. **Wrong tool usage**: AI calling `compare_file_implementations` without required `file2` parameter
4. **Infinite loops**: Tasks failing repeatedly because they couldn't be resolved

## Root Cause

The `validate_dict_structure` tool was creating tasks with incomplete or invalid error data:
- `key_path` was sometimes just a number like "0" instead of an actual dictionary key path
- File paths were sometimes missing or invalid
- No handler in `_format_analysis_data()` to guide AI on how to fix dictionary key errors

## Solution Implemented

### Fix 1: Add Dictionary Key Error Handler
**File**: `pipeline/phases/refactoring.py`

Added comprehensive handler in `_format_analysis_data()`:
```python
if 'key_path' in data:
    # This is a dictionary key error from validate_dict_structure
    key_path = data.get('key_path', 'unknown')
    file_path = data.get('file', 'unknown')
    line = data.get('line', '?')
    message = data.get('message', 'Dictionary key error')
    suggestion = data.get('suggestion', 'Add default value or check if key exists')
    
    return f"""
DICTIONARY KEY ERROR DETECTED:
- Key path: {key_path}
- File: {file_path}
- Line: {line}
- Error: {message}
- Suggestion: {suggestion}

ACTION REQUIRED:
1. Read the file to understand the context
2. Fix the dictionary access to handle missing keys
3. If the fix is complex, create an issue report

EXAMPLE (simple fix):
read_file(filepath="{file_path}")
# Then use modify_file or replace_between to add:
# - .get() with default value: dict.get('key', default_value)
# - Check if key exists: if 'key' in dict:
# - Try/except: try: value = dict['key'] except KeyError: value = default
...
"""
```

### Fix 2: Add Validation During Task Creation
**File**: `pipeline/phases/refactoring.py`

Added validation to skip invalid dictionary errors:
```python
# Validate error data before creating task
key_path = error.get('key_path', '')
file_path = error.get('file', '')

# Skip if key_path is invalid (just a number, empty, or 'unknown')
if not key_path or key_path.isdigit() or key_path == 'unknown':
    self.logger.debug(f"  ⚠️  Skipping dict error with invalid key_path: {key_path}")
    continue

# Skip if file path is invalid
if not file_path or file_path == 'unknown':
    self.logger.debug(f"  ⚠️  Skipping dict error with invalid file: {file_path}")
    continue
```

### Fix 3: Enhanced Cleanup
**File**: `pipeline/phases/refactoring.py`

Enhanced `_cleanup_broken_tasks()` to remove invalid dictionary key error tasks:
```python
# Also check for dictionary key errors with invalid key_path
if "Dictionary key error" in task.title:
    key_path = task.analysis_data.get('key_path', '') if isinstance(task.analysis_data, dict) else ''
    if not key_path or key_path.isdigit() or key_path == 'unknown':
        is_broken = True
```

## Expected Behavior

### Before Fix:
- ❌ Tasks created with `key_path='0'` or other invalid values
- ❌ AI confused, calling wrong tools
- ❌ Tasks failing repeatedly with `'file2'` error
- ❌ Infinite loops

### After Fix:
- ✅ Invalid dictionary errors skipped during task creation
- ✅ Existing broken tasks cleaned up automatically
- ✅ AI receives clear guidance on how to fix valid dictionary errors
- ✅ Tasks complete successfully or create proper issue reports

## Testing

After pulling the latest changes:
```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

Expected output:
```
🗑️  Removing broken task: refactor_0336 - Dictionary key error: 0
    Reason: Invalid key_path (just a number)
🗑️  Removing broken task: refactor_0337 - Dictionary key error: 0
    Reason: Invalid key_path (just a number)
✅ Cleaned up X broken tasks
```

Then new dictionary errors (if any) should have valid data and be fixable by AI.

## Files Modified

1. `pipeline/phases/refactoring.py` - Added handler, validation, and cleanup

## Commit

- **Commit**: aabbe45
- **Message**: "fix: Add dictionary key error handler and validation"
- **Status**: ✅ Pushed to GitHub