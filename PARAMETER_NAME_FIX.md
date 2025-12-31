# Critical Parameter Name Fix

## Problem
The refactoring phase was crashing immediately with:
```
TypeError: RefactoringTask.__init__() got an unexpected keyword argument 'estimated_effort_minutes'
```

## Root Cause
The `_auto_create_tasks_from_analysis()` method was using the wrong parameter name when creating RefactoringTask objects.

**Incorrect**: `estimated_effort_minutes=30`  
**Correct**: `estimated_effort=30`

The RefactoringTask dataclass defines the field as:
```python
estimated_effort: Optional[int] = None  # Minutes
```

## Impact
- **Before**: Refactoring phase crashed on first task creation (100% failure rate)
- **After**: Tasks created successfully, refactoring can proceed

## Files Changed
- `pipeline/phases/refactoring.py` - Fixed 13 occurrences

## Locations Fixed
1. Line 445 - Duplicate detection tasks
2. Line 466 - Complexity analysis tasks
3. Line 489 - Dead code detection tasks
4. Line 524 - Architecture violation tasks
5. Line 545 - Integration gap tasks (unused classes)
6. Line 559 - Integration gap tasks (unused methods)
7. Line 580 - Integration conflict tasks
8. Line 598 - Bug detection tasks
9. Line 615 - Anti-pattern detection tasks
10. Line 632 - Import validation tasks
11. Line 649 - Syntax validation tasks
12. Line 666 - Circular import detection tasks

## Verification
```bash
# Verify no more occurrences
grep -n "estimated_effort_minutes" pipeline/phases/refactoring.py
# (returns nothing - all fixed)
```

## Expected Behavior After Fix
The refactoring phase should now:
1. ✅ Run comprehensive analysis (6 phases)
2. ✅ Detect issues (duplicates, complexity, dead code, etc.)
3. ✅ Create RefactoringTask objects successfully
4. ✅ Continue to work on tasks over multiple iterations
5. ✅ Make actual progress on refactoring

## Commit
- **Hash**: d6b9248
- **Message**: "CRITICAL FIX: Change estimated_effort_minutes to estimated_effort in RefactoringTask creation"
- **Status**: ✅ Pushed to GitHub