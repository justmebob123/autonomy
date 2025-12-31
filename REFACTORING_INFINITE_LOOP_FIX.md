# Refactoring Phase Infinite Loop Fix

## Problem Description

The refactoring phase was stuck in an infinite loop:
- Created 70 tasks every iteration
- Reported "No pending tasks" immediately after
- Looped infinitely without making progress

## Root Cause Analysis

### The Issue
The `RefactoringTaskManager` was **not persistent across iterations**:

1. **Iteration 1:**
   - Creates new `RefactoringTaskManager` instance
   - Auto-creates 70 tasks from analysis
   - Stores in `state.refactoring_manager`
   - Returns `PhaseResult` with `next_phase="refactoring"`

2. **Iteration 2:**
   - State is saved to disk via `PipelineState.to_dict()`
   - **BUG:** `refactoring_manager` was NOT serialized
   - State is loaded from disk via `PipelineState.from_dict()`
   - **BUG:** `refactoring_manager` was NOT restored
   - Phase starts with `state.refactoring_manager = None`
   - Creates NEW empty manager
   - Finds "no pending tasks"
   - Re-runs analysis, creates 70 tasks again
   - Loop repeats infinitely

### Evidence from Logs
```
04:34:43 [INFO]   ✅ Auto-created 70 refactoring tasks from analysis
04:34:43 [INFO]   🔍 DEBUG: Total tasks in manager: 70
04:34:43 [INFO]   🔍 DEBUG: Pending tasks returned: 70
04:34:43 [INFO]   ✅ Analysis complete, 70 tasks to work on

# Next iteration - tasks lost!
04:34:45 [INFO]   🔍 No pending tasks, analyzing codebase...
04:34:45 [INFO]   ✅ Auto-created 70 refactoring tasks from analysis
```

## Solution

### Changes Made

**File: `autonomy/pipeline/state/manager.py`**

#### 1. Serialize RefactoringTaskManager in `to_dict()`
```python
def to_dict(self) -> Dict:
    result = {
        # ... existing fields ...
    }
    
    # Serialize refactoring_manager if present
    if self.refactoring_manager is not None:
        result["refactoring_manager"] = self.refactoring_manager.to_dict()
    
    return result
```

#### 2. Deserialize RefactoringTaskManager in `from_dict()`
```python
@classmethod
def from_dict(cls, data: Dict) -> "PipelineState":
    # ... existing code ...
    
    # Deserialize refactoring_manager if present
    refactoring_manager_data = data.pop("refactoring_manager", None)
    
    # Create state instance
    state = cls(**data)
    
    # Restore refactoring_manager
    if refactoring_manager_data is not None:
        from pipeline.state.refactoring_task import RefactoringTaskManager
        state.refactoring_manager = RefactoringTaskManager.from_dict(refactoring_manager_data)
    
    return state
```

## Expected Behavior After Fix

1. **Iteration 1:**
   - Creates `RefactoringTaskManager`
   - Auto-creates 70 tasks
   - Saves state with serialized manager

2. **Iteration 2:**
   - Loads state with deserialized manager
   - Finds 70 pending tasks
   - Works on first task
   - Marks task complete
   - Saves state with 69 pending tasks

3. **Iteration 3:**
   - Loads state with 69 pending tasks
   - Works on next task
   - Progress continues until all tasks complete

## Testing

The fix ensures:
- ✅ Tasks persist across iterations
- ✅ Task state (NEW, IN_PROGRESS, COMPLETED) is maintained
- ✅ Task dependencies are preserved
- ✅ Progress tracking works correctly
- ✅ No infinite loops

## Related Files

- `autonomy/pipeline/state/manager.py` - State serialization (FIXED)
- `autonomy/pipeline/state/refactoring_task.py` - Task manager with to_dict/from_dict
- `autonomy/pipeline/phases/refactoring.py` - Refactoring phase logic

## Impact

This fix resolves the critical infinite loop bug in the refactoring phase, allowing:
- Proper task persistence across iterations
- Progressive completion of refactoring work
- Correct state management for long-running refactoring sessions
- Reliable multi-iteration refactoring workflows