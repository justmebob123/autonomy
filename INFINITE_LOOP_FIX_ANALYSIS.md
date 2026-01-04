# Infinite Planning Loop - Root Cause Analysis and Fix

## The Problem

**Iterations 39-45**: System stuck in infinite loop with ZERO progress

### Loop Pattern
```
ITERATION 39-45 (repeating):
1. Planning phase runs
2. Finds 161 integration gaps (same number every time)
3. Creates 30 tasks
4. ALL 30 tasks are duplicates (already exist)
5. Adds 0 new tasks
6. Says "No new work needed - suggesting move to coding phase"
7. BUT THEN GOES BACK TO PLANNING (step 1)
8. Repeat forever...
```

### System State During Loop
- **Progress**: Stuck at 24.9% (foundation phase)
- **Pending tasks**: 0
- **QA tasks waiting**: 12
- **Completed tasks**: 66
- **Total tasks**: 265

## Root Cause Analysis

### Problem 1: Foundation Phase QA Deferral
```python
# Foundation phase (0-25%): Defer QA, continue building codebase
if project_phase == 'foundation':
    self.logger.info(f"Foundation phase, deferring QA - continue building codebase")
    # Don't return - fall through to planning  <--- PROBLEM!
```

**Issue**: When at 24.9% with 12 QA tasks and 0 pending tasks, the system:
1. Defers QA (because foundation phase)
2. Falls through to planning
3. Planning has no new tasks to create
4. Returns to planning again
5. Infinite loop

### Problem 2: Planning Loop Detection Too Lenient
```python
if state._consecutive_planning_count >= 3:  # Too high!
    # Break loop
```

**Issue**: Allows 3 consecutive planning iterations before breaking the loop. This wastes 9+ minutes (3 iterations × 3 minutes each) before detecting the problem.

### Problem 3: Planning Creates Same Duplicate Tasks
The planning phase keeps suggesting the EXACT same 30 tasks every iteration:
- Task 1: "Analyze project codebase for integration gaps"
- Task 2: "Document identified integration gaps"
- Task 3-30: Same tasks every time

All are marked as duplicates, but planning doesn't learn from this.

## The Fix

### Fix 1: Smart Foundation Phase QA
```python
# Foundation phase: Run QA if we have 10+ tasks OR if stuck in planning loop
if project_phase == 'foundation':
    if not pending and len(qa_pending) >= 10:
        # No coding work, lots of QA waiting - run QA to break loop
        return {'phase': 'qa', 'task': qa_pending[0], 
                'reason': f'Breaking planning loop with QA: {len(qa_pending)} tasks ready'}
    else:
        # Still building, defer QA
        # Don't return - fall through to planning
```

**Result**: When stuck with 12 QA tasks and no pending work, runs QA instead of looping

### Fix 2: Aggressive Planning Loop Detection
```python
if state._consecutive_planning_count >= 2:  # Changed from 3 to 2
    self.logger.warning(f"Planning loop detected")
    
    # If we have QA tasks, run them to break the loop
    if qa_pending:
        return {'phase': 'qa', 'task': qa_pending[0], 
                'reason': f'Breaking planning loop with QA: {len(qa_pending)} tasks'}
    else:
        return {'phase': 'documentation', 'reason': 'Breaking planning loop'}
```

**Result**: 
- Detects loop after 2 iterations (6 minutes) instead of 3 (9 minutes)
- Prioritizes running QA tasks to make progress
- Falls back to documentation if no QA tasks

## Expected Behavior After Fix

### Before Fix (Infinite Loop)
```
Iteration 39: Planning → 0 new tasks → Planning
Iteration 40: Planning → 0 new tasks → Planning  
Iteration 41: Planning → 0 new tasks → Planning
Iteration 42: Planning → 0 new tasks → Planning
... forever ...
```

### After Fix (Progress Resumes)
```
Iteration 39: Planning → 0 new tasks → Planning
Iteration 40: Planning → 0 new tasks → Planning (loop detected!)
Iteration 41: QA → Process 12 waiting tasks → Progress!
Iteration 42: QA → More tasks → Progress!
... continues normally ...
```

## Why This Happened

The system was designed to defer QA during foundation phase to focus on building code. But when there's NO MORE CODE to build (0 pending tasks), it should switch to QA instead of looping in planning.

The workflow logic didn't account for this edge case:
- **0 pending coding tasks**
- **12 QA tasks waiting**
- **Planning has nothing new to plan**
- **Result**: Infinite loop

## Testing

After pulling these changes, the system should:
1. ✅ Detect the planning loop after 2 iterations
2. ✅ Switch to QA phase to process the 12 waiting tasks
3. ✅ Make actual progress instead of looping
4. ✅ Move past 24.9% completion

## Files Modified

- `pipeline/coordinator.py` - Fixed workflow decision logic
- `debug_integration_status.py` - Added for debugging (can be removed)

## Commit

`9a63084` - fix: Break infinite planning loop by running QA when stuck