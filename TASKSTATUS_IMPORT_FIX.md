# TaskStatus Import Fix

## Problem
The system was crashing with:
```
UnboundLocalError: cannot access local variable 'TaskStatus' where it is not associated with a value
```

This occurred during the deduplication checks in the refactoring phase.

## Root Cause
There were conflicting imports of `TaskStatus`:

1. **Module-level import (correct)**: Line 15 imports `TaskStatus` from `..state.manager`
   ```python
   from ..state.manager import PipelineState, TaskState, TaskStatus
   ```

2. **Local import (incorrect)**: Line 2021 tried to import `TaskStatus` from `pipeline.state.refactoring_task`
   ```python
   from pipeline.state.refactoring_task import TaskStatus
   ```

3. **Another local import (incorrect)**: Line 2510 also tried to import from the wrong module
   ```python
   from pipeline.state.refactoring_task import RefactoringPriority, TaskStatus
   ```

The problem is that `TaskStatus` only exists in `pipeline.state.manager`, not in `pipeline.state.refactoring_task`. The local import statement was creating a scoping issue where Python couldn't determine which `TaskStatus` to use.

## Solution
Removed the redundant and incorrect local imports:

1. **Line 2021**: Removed the local import inside the deduplication loop
   - The module-level import is sufficient and correct

2. **Line 2510**: Removed `TaskStatus` from the local import statement
   - Only kept `RefactoringPriority` which does exist in `refactoring_task.py`
   - The module-level `TaskStatus` import is used instead

## Impact
- ✅ Deduplication checks now work correctly
- ✅ No more UnboundLocalError
- ✅ Proper use of module-level imports
- ✅ Cleaner code with fewer redundant imports

## Technical Details
The error occurred because:
1. Python saw a local import statement for `TaskStatus` inside a loop
2. The import was from the wrong module (which doesn't have `TaskStatus`)
3. When the code tried to use `TaskStatus.COMPLETED`, Python couldn't resolve it
4. This created an UnboundLocalError because the local variable wasn't properly initialized

By removing the incorrect local imports and relying on the correct module-level import, the issue is resolved.