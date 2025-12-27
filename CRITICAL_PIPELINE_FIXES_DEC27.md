# Critical Pipeline Fixes - December 27, 2024

## Issues Identified

### 1. QA Phase Calling Tools with Empty Names
**Problem:** The AI model was generating tool calls with empty name fields, causing "Unknown tool:" warnings and failures.

**Root Cause:** The tool call parser was not validating that tool names were non-empty strings.

**Fix Applied:** Modified `pipeline/handlers.py` to detect and reject tool calls with empty names:
```python
# Handle empty string names (common AI model error)
if not name or name.strip() == "":
    name = "unknown"
    self.logger.warning(f"Tool call has empty name field")
    return {
        "tool": "unknown",
        "success": False,
        "error": "empty_tool_name",
        "message": "Tool call has empty name field"
    }
```

### 2. System Stuck in QA with 20 Consecutive Failures
**Problem:** The system would reach 20 consecutive QA failures before transitioning, despite the threshold being set to 3.

**Root Cause:** 
- Phase transition was being forced correctly
- But the same failing task remained in QA_PENDING status
- Task selection logic would immediately select it again
- This created an infinite loop

**Fixes Applied:**

1. **Mark failing tasks as SKIPPED** (`pipeline/phases/qa.py`):
```python
if task:
    task.attempts += 1
    if task.attempts >= 3:
        self.logger.warning(f"Task {task.task_id} has failed QA {task.attempts} times, marking as SKIPPED")
        task.status = TaskStatus.SKIPPED
```

2. **Reduce consecutive failure threshold** (`pipeline/coordinator.py`):
```python
# Changed from >= 3 to >= 2 for faster escape
if consecutive_failures >= 2:
    self.logger.warning(f"⚠️  Phase {current_phase} has {consecutive_failures} consecutive failures")
    return True
```

### 3. Files Being Created in features/ Directory
**Problem:** All files were being created in a non-existent `features/` directory instead of the proper project structure.

**Root Cause:** The text tool parser defaulted to `features/{name}.py` for unknown categories.

**Fix Applied:** Modified `pipeline/text_tool_parser.py` to use actual project structure:
```python
elif re.search(r'\b(phase|workflow)\b', text_lower):
    name = self._extract_meaningful_name(text)
    return f"pipeline/phases/{name}.py"
elif re.search(r'\b(tool|utility|helper)\b', text_lower):
    name = self._extract_meaningful_name(text)
    return f"pipeline/tools/{name}.py"
else:
    # Default to pipeline directory for general code
    name = self._extract_meaningful_name(text)
    return f"pipeline/{name}.py"
```

### 4. Verbose File Listing Every Iteration
**Problem:** The system was listing ALL Python files in the project every iteration, creating excessive log output.

**Root Cause:** `_show_project_status()` in `coordinator.py` was using `rglob("*.py")` to list all files.

**Fix Applied:** Modified to only show files with active tasks:
```python
def _show_project_status(self, state: PipelineState) -> None:
    """Show current project file status - only files with active tasks"""
    # Only show files that have active tasks (not all files)
    active_files = set()
    for task in state.tasks.values():
        if task.target_file and task.status in [
            TaskStatus.NEW, TaskStatus.IN_PROGRESS, 
            TaskStatus.QA_PENDING, TaskStatus.NEEDS_FIXES
        ]:
            active_files.add(task.target_file)
    
    if not active_files:
        return  # Don't show anything if no active tasks
```

## Impact

These fixes address the critical issues that were causing:
- Rapid iteration without progress
- Infinite QA loops
- Incorrect file placement
- Excessive log verbosity

The system should now:
- Properly handle malformed tool calls from AI models
- Escape from failing QA tasks within 2-3 attempts
- Create files in the correct project directories
- Produce concise, readable logs

## Files Modified

1. `pipeline/handlers.py` - Empty tool name validation
2. `pipeline/phases/qa.py` - Task skip logic after repeated failures
3. `pipeline/coordinator.py` - Reduced failure threshold and concise logging
4. `pipeline/text_tool_parser.py` - Correct directory structure

## Commit

```
commit 85569be
Author: root
Date: Fri Dec 27 03:23:45 2024 +0000

Fix critical pipeline issues: QA loops, empty tool names, verbose logging
```

## Next Steps

The user needs to pull these changes from the repository:
```bash
cd autonomy
git pull origin main
```

Note: Push failed due to invalid authentication token. The changes are committed locally and need to be pushed with valid credentials.