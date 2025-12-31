# Critical Fix: RefactoringTask Creation Method

## Problem
The refactoring phase was stuck in an infinite loop with this error:
```
TypeError: RefactoringTask.__init__() missing 2 required positional arguments: 'task_id' and 'title'
```

## Root Cause
The code was calling `RefactoringTask()` directly instead of using the `RefactoringTaskManager.create_task()` method.

RefactoringTask is a dataclass with these required positional arguments:
```python
@dataclass
class RefactoringTask:
    task_id: str        # REQUIRED
    issue_type: RefactoringIssueType
    title: str          # REQUIRED
    description: str
    target_files: List[str]
    # ... other fields with defaults
```

The code was trying to create tasks like this:
```python
task = RefactoringTask(
    issue_type=RefactoringIssueType.DUPLICATE,
    priority=RefactoringPriority.MEDIUM,
    description="...",
    target_files=[...],
    # Missing: task_id and title!
)
```

## Solution
Changed all 12 occurrences to use `manager.create_task()` which:
1. Generates unique task_id automatically
2. Requires title parameter
3. Handles proper initialization
4. Adds task to manager automatically

**Correct usage:**
```python
task = manager.create_task(
    issue_type=RefactoringIssueType.DUPLICATE,
    title="Duplicate code detected",  # Now required
    description="...",
    target_files=[...],
    priority=RefactoringPriority.MEDIUM,
    fix_approach=RefactoringApproach.AUTONOMOUS,
    estimated_effort=30
)
# No need for manager.add_task(task) - create_task does it
```

## Files Changed
- `pipeline/phases/refactoring.py` - Fixed 12 occurrences

## Locations Fixed
1. Line 439 - Duplicate detection tasks
2. Line 460 - Complexity analysis tasks
3. Line 483 - Dead code detection tasks
4. Line 518 - Architecture violation tasks
5. Line 539 - Integration gap tasks (unused classes)
6. Line 553 - Integration gap tasks (unused methods)
7. Line 574 - Integration conflict tasks
8. Line 592 - Bug detection tasks
9. Line 609 - Anti-pattern detection tasks
10. Line 626 - Import validation tasks
11. Line 643 - Syntax validation tasks
12. Line 660 - Circular import detection tasks

## Impact
- **Before**: Refactoring phase crashed with TypeError on every task creation attempt
- **After**: Tasks created successfully, refactoring can proceed

## Commit
- **Hash**: 1fa47bb
- **Message**: "CRITICAL FIX: Use manager.create_task() instead of RefactoringTask() directly"
- **Status**: ✅ Pushed to GitHub

## Expected Behavior
The refactoring phase should now:
1. Complete all 6 analysis phases ✅
2. Create RefactoringTask objects successfully ✅
3. Add tasks to manager ✅
4. Start working on tasks ✅
5. Make actual progress on refactoring ✅

## Testing
Run the pipeline and verify:
```bash
cd /home/ai/AI/autonomy && python3 run.py -vv ../web/
```

Expected output:
- ✅ All 6 phases complete
- ✅ "Found X duplicate sets, creating tasks..."
- ✅ "Created X refactoring tasks"
- ✅ No TypeError
- ✅ Phase continues to work on tasks