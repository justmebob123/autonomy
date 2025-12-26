# QA Phase Loop Issue

## Problem

After fixing the documentation loop, discovered a new loop in the QA phase:
1. QA phase runs 5 times consecutively
2. Forced transition to debugging works (iteration 1)
3. Debugging finds no issues
4. System returns to QA phase
5. QA phase loops again (iterations 2-6+)

## Root Causes

### 1. Empty target_file in Task
Task has `QA_PENDING` status but empty `target_file`:
```
Reviewing: 
Failed to read : [Errno 21] Is a directory: '/home/ai/AI/test-automation'
```

### 2. QA Phase Doesn't Skip Invalid Tasks
QA phase tries to review empty filename, fails, but still returns success=False, which doesn't change task status.

### 3. Forced Transition Doesn't Fix Root Cause
- Forced transition to debugging works
- But debugging finds nothing to fix
- Task still has QA_PENDING status with empty target_file
- System returns to QA phase
- Loop continues

## Solutions Needed

### Solution 1: Skip Tasks with Empty target_file
QA phase should skip tasks that have empty or invalid target_file:

```python
# In qa.py execute()
if filepath is None and task is not None:
    filepath = task.target_file
    
    # Skip tasks with empty target_file
    if not filepath or filepath.strip() == "":
        self.logger.warning(f"  ⚠️ Task {task.task_id} has empty target_file, marking as SKIPPED")
        task.status = TaskStatus.SKIPPED
        self.state_manager.save(state)
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Skipped task with empty target_file"
        )
```

### Solution 2: QA Phase Loop Prevention
Add same loop prevention logic as documentation phase:

```python
# Check no-update count BEFORE processing
from ..state.manager import StateManager
state_manager = StateManager(self.project_dir)
no_update_count = state_manager.get_no_update_count(state, self.phase_name)

if no_update_count >= 3:
    self.logger.warning(f"  ⚠️ QA phase returned 'no files to review' {no_update_count} times")
    self.logger.info("  🔄 Forcing transition to next phase to prevent loop")
    
    state_manager.reset_no_update_count(state, self.phase_name)
    
    return PhaseResult(
        success=True,
        phase=self.phase_name,
        message="QA reviewed multiple times - forcing completion to prevent loop",
        next_phase="coding"  # Move to coding to work on remaining tasks
    )
```

### Solution 3: Better Task Validation in _determine_next_action
Coordinator should validate tasks before returning them:

```python
# 2. Tasks awaiting QA review
for task in state.tasks.values():
    if task.status == TaskStatus.QA_PENDING:
        # Validate task has valid target_file
        if not task.target_file or task.target_file.strip() == "":
            self.logger.warning(f"Task {task.task_id} has empty target_file, skipping")
            task.status = TaskStatus.SKIPPED
            self.state_manager.save(state)
            continue
            
        return {
            "phase": "qa",
            "task": task,
            "reason": "review_new_code"
        }
```

## Priority

**HIGH** - System is currently stuck in QA loop, blocking all progress.

## Implementation Order

1. Fix coordinator to skip invalid tasks (immediate)
2. Fix QA phase to skip empty target_file (immediate)
3. Add QA phase loop prevention (safety net)