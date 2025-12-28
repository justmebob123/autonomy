# Critical Fixes Applied - QA Phase Issues

## Date: December 28, 2024

## Issues Fixed

### Issue 1: QA Task Count Not Decrementing ✅ FIXED

**Problem**: Files were approved but QA task count stayed at 2

**Root Cause**: 
- Coordinator called QA phase WITHOUT passing the task parameter
- QA phase code: `if task: task.status = TaskStatus.COMPLETED`
- Since task was None, status was never updated

**Fix Applied** (`autonomy/pipeline/coordinator.py` line ~1053):
```python
# Before:
if qa_pending:
    return {'phase': 'qa', 'reason': f'{len(qa_pending)} tasks awaiting QA'}

# After:
if qa_pending:
    return {'phase': 'qa', 'task': qa_pending[0], 'reason': f'{len(qa_pending)} tasks awaiting QA'}
```

**Impact**: QA tasks will now properly transition to COMPLETED when approved

### Issue 2: QA Issues Not Triggering Debugging ✅ FIXED

**Problem**: Model found meaningful issues but they weren't being fixed

**Root Cause**:
- QA phase set task.status = QA_FAILED
- Coordinator only checks for NEEDS_FIXES status to trigger debugging

**Fix Applied** (`autonomy/pipeline/phases/qa.py` line ~208):
```python
# Before:
task.status = TaskStatus.QA_FAILED
task.priority = TaskPriority.QA_FAILURE

# After:
task.status = TaskStatus.NEEDS_FIXES  # Triggers debugging!
task.priority = TaskPriority.HIGH
```

**Impact**: QA issues will now trigger debugging phase automatically

### Issue 3: State Reload Causing Data Loss ✅ FIXED

**Problem**: Coordinator reloaded state multiple times, potentially losing changes

**Root Cause**:
- State loaded once for phase hint
- State loaded again for recording phase stats
- Multiple reloads could cause race conditions

**Fix Applied** (`autonomy/pipeline/coordinator.py` line ~910):
```python
# Before:
if result.next_phase:
    state = self.state_manager.load()
    state._next_phase_hint = result.next_phase
    self.state_manager.save(state)

state = self.state_manager.load()  # Reload again!
if phase_name in state.phases:
    state.phases[phase_name].record_run(...)
self.state_manager.save(state)

# After:
state = self.state_manager.load()  # Load ONCE

if result.next_phase:
    state._next_phase_hint = result.next_phase

if phase_name in state.phases:
    state.phases[phase_name].record_run(...)

self.state_manager.save(state)  # Save ONCE
```

**Impact**: State changes are now properly preserved

### Issue 4: Empty Tool Names (Partial Fix) ⚠️ NEEDS MORE WORK

**Problem**: Model returns `{"name": "", "arguments": {...}}`

**Current Status**:
- Prompts have been strengthened with explicit requirements
- Inference fallback exists in handlers.py
- But model still returns empty names

**Next Steps**:
- Research qwen2.5 specific tool calling format
- May need model-specific prompting
- Consider using different model for QA

## Files Modified

1. `autonomy/pipeline/coordinator.py`
   - Fixed state reload (line ~910)
   - Added task parameter to phase decisions (lines ~1048, 1053, 1058)

2. `autonomy/pipeline/phases/qa.py`
   - Changed QA_FAILED to NEEDS_FIXES (line ~208)
   - Changed QA_FAILURE to HIGH priority (line ~209)

## Testing Recommendations

1. **Test QA Task Decrement**:
   ```bash
   ./run.py /path/to/project
   # Watch for "📊 Task Status" logs
   # QA count should decrease after approvals
   ```

2. **Test QA → Debugging Transition**:
   ```bash
   # Let QA find issues
   # Should automatically go to debugging phase
   # Check logs for "tasks need fixes"
   ```

3. **Test State Persistence**:
   ```bash
   # Run pipeline
   # Kill it mid-execution
   # Resume - should maintain correct state
   ```

## Expected Behavior After Fixes

### Before:
```
Iteration 1 - QA: Reviewing file1.py → APPROVED
📊 Task Status: 0 pending, 2 QA, 0 fixes, 11 done

Iteration 2 - QA: Reviewing file2.py → APPROVED  
📊 Task Status: 0 pending, 2 QA, 0 fixes, 11 done  ← BUG: Still 2 QA!

Iteration 3 - QA: Reviewing file3.py → Found issues
📊 Task Status: 0 pending, 2 QA, 0 fixes, 11 done  ← BUG: Not going to debugging!
```

### After:
```
Iteration 1 - QA: Reviewing file1.py → APPROVED
📊 Task Status: 0 pending, 1 QA, 0 fixes, 12 done  ← FIXED: Decremented!

Iteration 2 - QA: Reviewing file2.py → APPROVED
📊 Task Status: 0 pending, 0 QA, 0 fixes, 13 done  ← FIXED: Decremented!

Iteration 3 - QA: Reviewing file3.py → Found issues
📊 Task Status: 0 pending, 0 QA, 1 fixes, 13 done  ← FIXED: NEEDS_FIXES!

Iteration 4 - DEBUGGING: Fixing issues in file3.py
```

## Remaining Issues

### Empty Tool Names
- Model still returns empty names despite prompt improvements
- Inference fallback works but is a band-aid
- Need to research qwen2.5 specific requirements

### Potential Solutions:
1. Use different model for QA (e.g., qwen2.5-coder:32b)
2. Add model-specific prompt formatting
3. Use function calling examples from qwen2.5 docs
4. Consider using functiongemma for tool formatting

## Conclusion

Three critical bugs fixed:
1. ✅ QA tasks now properly decrement
2. ✅ QA issues trigger debugging
3. ✅ State changes persist correctly

One issue remains:
4. ⚠️ Empty tool names (needs research)

The pipeline should now properly flow through phases and maintain correct state.