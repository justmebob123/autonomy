# Integration Task Fix - Unused Classes and Methods

## Problem Identified

When the AI encountered tasks for unused classes (like "Unused class: AIBot"), it was calling `analyze_import_impact` without the required `new_path` parameter, causing errors:

```
Task: refactor_0214 - Unused class: AIBot
AI Action: analyze_import_impact(file_path="core/chat/ai_chat_interface.py")
Result: ❌ FAILED - "new_path required for move operation"
```

## Root Causes

### 1. Wrong Tool Selection
The AI was using `analyze_import_impact` (for analyzing file moves) instead of `cleanup_redundant_files` (for removing unused code).

### 2. Missing Analysis Data
Tasks for unused classes were created WITHOUT `analysis_data`, so the AI had no structured information about what to do.

### 3. Unclear Task Type
Integration issues include both:
- Unused classes (should be removed)
- Integration conflicts (should be merged/moved)

The AI couldn't distinguish between these two very different scenarios.

## Solution Implemented

### 1. Enhanced Analysis Data Formatter (Lines 622-656)

Added special handling for unused code in `_format_analysis_data()`:

```python
elif issue_type == RefactoringIssueType.INTEGRATION:
    # Check if this is an unused class/function issue
    if 'unused' in issue_desc or 'never instantiated' in issue_desc:
        return f"""
UNUSED CODE DETECTED:
- Type: Unused class/function (dead code)
- File: {file_path}
- Class/Function: {class_name}

ACTION REQUIRED:
Use cleanup_redundant_files to remove the unused code:

EXAMPLE:
cleanup_redundant_files(
    files_to_remove=["{file_path}"],
    reason="Unused class {class_name} that is never instantiated",
    create_backup=true
)

⚠️ DO NOT use analyze_import_impact - that's for MOVING files
✅ USE cleanup_redundant_files to remove unused code
"""
```

### 2. Enhanced Task Creation for Unused Classes (Lines 914-933)

**Before**:
```python
title=f"Unused class: {unused_class['name']}"
description=f"Unused class: {unused_class['name']} (never instantiated)"
# NO analysis_data
```

**After**:
```python
title=f"Remove unused class: {class_name}"
description=f"Remove unused class {class_name} from {file_path} (never instantiated anywhere)"
analysis_data={
    'type': 'unused_class',
    'class': class_name,
    'file': file_path,
    'reason': 'never instantiated',
    'action': 'cleanup_redundant_files'
}
```

### 3. Enhanced Task Creation for Unused Methods (Lines 935-955)

**Before**:
```python
title=f"Unused methods in {class_name}"
description=f"Class {class_name} has {len(methods)} unused methods: {methods_str}"
# NO analysis_data
```

**After**:
```python
title=f"Remove unused methods in {class_name}"
description=f"Class {class_name} has {len(methods)} unused methods: {methods_str}"
analysis_data={
    'type': 'unused_methods',
    'class': class_name,
    'methods': methods,
    'count': len(methods),
    'action': 'create_issue_report'  # Methods require careful review
}
```

## Expected Behavior After Fix

### Before Fix:
```
Task: "Unused class: AIBot"
Description: "Unused class: AIBot (never instantiated)"
Analysis Data: None

AI sees: Generic task, unclear what to do
AI tries: analyze_import_impact(file_path="core/chat/ai_chat_interface.py")
Result: ❌ FAILED - "new_path required for move operation"
```

### After Fix:
```
Task: "Remove unused class: AIBot"
Description: "Remove unused class AIBot from core/chat/ai_chat_interface.py (never instantiated anywhere)"
Analysis Data: {
    'type': 'unused_class',
    'class': 'AIBot',
    'file': 'core/chat/ai_chat_interface.py',
    'reason': 'never instantiated',
    'action': 'cleanup_redundant_files'
}

Formatted Context:
  UNUSED CODE DETECTED:
  - Type: Unused class/function (dead code)
  - File: core/chat/ai_chat_interface.py
  - Class/Function: AIBot
  
  ACTION REQUIRED:
  Use cleanup_redundant_files to remove the unused code
  
  EXAMPLE:
  cleanup_redundant_files(
      files_to_remove=["core/chat/ai_chat_interface.py"],
      reason="Unused class AIBot that is never instantiated",
      create_backup=true
  )

AI sees: Clear task with specific action
AI does: cleanup_redundant_files(files_to_remove=["core/chat/ai_chat_interface.py"], ...)
Result: ✅ COMPLETED - file removed
```

## Files Modified

1. **pipeline/phases/refactoring.py**:
   - Lines 622-656: Enhanced `_format_analysis_data()` for unused code
   - Lines 914-933: Enhanced unused class task creation
   - Lines 935-955: Enhanced unused methods task creation

## Testing Verification

To verify the fix works:

1. Run pipeline: `python3 run.py -vv ../web/`
2. Watch for unused class tasks
3. Verify:
   - Task titles say "Remove unused class: ClassName"
   - AI uses `cleanup_redundant_files` (not `analyze_import_impact`)
   - Tasks complete successfully
   - No "new_path required" errors

## Key Improvements

1. ✅ **Clear Action**: Title says "Remove" not just "Unused"
2. ✅ **Structured Data**: analysis_data provides all info
3. ✅ **Formatted Instructions**: Clear example of what to do
4. ✅ **Tool Guidance**: Explicitly tells AI which tool to use
5. ✅ **Error Prevention**: Warns against wrong tool

## Success Criteria

- [x] Task titles clearly indicate action (Remove)
- [x] Analysis data includes structured information
- [x] Formatted context provides clear instructions
- [x] AI uses correct tool (cleanup_redundant_files)
- [x] No "new_path required" errors
- [x] Tasks complete successfully