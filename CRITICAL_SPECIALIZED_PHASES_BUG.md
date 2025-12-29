# CRITICAL BUG: Specialized Phases Infinite Loop

## Problem Analysis

### Issue 1: Specialized Phases Not Registered in State
The specialized phases (tool_design, prompt_design, role_design, etc.) are being activated but are NOT registered in `state.phases` dictionary, causing:

```python
KeyError: 'tool_design'
# at line: state.phases[self.phase_name].record_run(result.success)
```

### Issue 2: Infinite Loop
1. Task fails 3 times
2. Loop detection activates specialized phase (e.g., tool_design)
3. Specialized phase tries to record run in state.phases
4. KeyError occurs because phase not registered
5. Error triggers loop detection again
6. Loop detection activates specialized phase again
7. **INFINITE LOOP**

### Issue 3: Root Cause
When specialized phases were restructured to be "on-demand only", they were removed from the polytopic structure initialization, but the state management system still expects them to be registered.

## The Problem Chain

```
1. coordinator.py line 811: Loop detected for task_034
2. coordinator.py: Activates tool_design phase
3. base.py line 358: Tries to access state.phases['tool_design']
4. KeyError: 'tool_design' not in state.phases
5. Error handling triggers loop detection again
6. GOTO 1 (infinite loop)
```

## Files Affected

1. **pipeline/coordinator.py**
   - Line 811: Loop detection
   - Specialized phase activation logic

2. **pipeline/phases/base.py**
   - Line 358: `state.phases[self.phase_name].record_run(result.success)`
   - Assumes all phases are registered in state

3. **pipeline/state/manager.py**
   - PhaseState registration
   - Needs to include specialized phases

## Solution Required

### Option 1: Register Specialized Phases in State (RECOMMENDED)
Even though specialized phases are "on-demand", they still need to be registered in the state management system for tracking purposes.

### Option 2: Make Phase Recording Optional
Modify base.py to handle missing phases gracefully:
```python
if self.phase_name in state.phases:
    state.phases[self.phase_name].record_run(result.success)
```

### Option 3: Disable Specialized Phase Activation
Remove the automatic activation of specialized phases from loop detection until the state management is fixed.

## Immediate Impact

- **Pipeline is COMPLETELY BROKEN**
- Infinite loop on any task that fails 3 times
- No way to recover without manual intervention
- All specialized phase functionality is non-functional

## Priority

**CRITICAL - P0**
- Blocks all pipeline execution
- Causes infinite loops
- Requires immediate fix

## Related Issues

This is directly related to the recent specialized phases restructuring where phases were made "on-demand only" but the state management integration was not updated accordingly.