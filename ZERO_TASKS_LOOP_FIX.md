# Zero Tasks Infinite Loop Fix

## Problem
After fixing the enum.value bug, a NEW infinite loop appeared:
- Objective has 0 tasks
- Shows 100% completion
- Status: COMPLETING
- is_active: True
- System keeps going to PLANNING phase with "Objective needs more tasks"

## Root Cause
In `objective_manager.py`, the `update_progress()` method:

```python
def update_progress(self, state: PipelineState):
    if not self.tasks:
        self.completion_percentage = 0.0  # Should be 0%
        return
```

But the objective shows 100% completion. This means the completion percentage is being set elsewhere or not being updated.

## The Fix
When an objective has 0 tasks and 100% completion, it should be marked as COMPLETED immediately, not sent to planning for more tasks.

Add a check in coordinator.py BEFORE the phase determination logic:

```python
# Special case: objective with 0 tasks but 100% completion
# This happens when all tasks were completed and removed
# Mark as COMPLETED and move to next objective
if len(optimal_objective.tasks) == 0 and optimal_objective.completion_percentage >= 80.0:
    optimal_objective.status = ObjectiveStatus.COMPLETED
    self.objective_manager.save_objective(optimal_objective, state)
    
    # Select next objective
    next_objective = self.objective_manager.find_optimal_objective(state)
    if next_objective:
        next_objective.status = "active"
        self.objective_manager.save_objective(next_objective, state)
        optimal_objective = next_objective
```

This ensures objectives with no tasks don't get stuck in an infinite planning loop.