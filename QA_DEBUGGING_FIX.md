# Critical Bug Fix: QA → Debugging Transition Broken

## The Problem

**Symptom:** QA phase runs continuously, finds issues, creates NEEDS_FIXES tasks, but debugging phase never runs. Progress stuck at ~24%.

**User's Question:**
> "is QA actually testing different files? is it finding anything meaningful? Is it adding tasks? is there a reason we haven't returned to the coder to fix the existing problems it has found yet?"

**Answer:**
- ✅ YES, QA is testing different files (each iteration tests a different file)
- ✅ YES, QA is finding issues (1 issue per file: "method never called")
- ✅ YES, QA is creating NEEDS_FIXES tasks (logs show "Created task qa_fix_...")
- ❌ NO, debugging phase never runs because of a critical bug

## Root Cause Analysis

### The Bug

In `pipeline/state/manager.py`, the `TaskState.__post_init__` method has this code:

```python
# Map NEEDS_FIXES to QA_FAILED for compatibility
if status_upper == "NEEDS_FIXES":
    self.status = TaskStatus.QA_FAILED
```

### What Happens

1. **QA Phase Creates Task:**
   ```python
   task = TaskState(
       task_id="qa_fix_services_ollama_server_manager.py_0",
       status=TaskStatus.NEEDS_FIXES,  # ← Created with NEEDS_FIXES
       ...
   )
   state.tasks[task_id] = task
   state_manager.save(state)
   ```

2. **Coordinator Loads State:**
   ```python
   state = self.state_manager.load()  # ← Loads from disk
   # TaskState.__post_init__ runs and converts NEEDS_FIXES → QA_FAILED
   ```

3. **Coordinator Counts Tasks:**
   ```python
   needs_fixes = [t for t in state.tasks.values() 
                  if t.status == TaskStatus.NEEDS_FIXES]  # ← Empty!
   # All tasks are now QA_FAILED, not NEEDS_FIXES
   ```

4. **Workflow Decision:**
   ```python
   if qa_pending and not pending:
       return qa_phase  # ← Keeps running QA
   
   if needs_fixes:  # ← Never true because needs_fixes is empty
       return debugging_phase
   ```

### Evidence from Logs

```
22:53:04 [INFO]   🔧 Creating 1 NEEDS_FIXES tasks for services/ollama_server_manager.py
22:53:04 [INFO]     ✅ Created task qa_fix_services_ollama_server_manager.py_0 (priority 10)
22:53:05 [INFO]   💾 Saved state with 1 new NEEDS_FIXES tasks
...
22:53:06 [INFO] 📊 Task Status: 0 pending, 11 QA, 0 fixes, 66 done
                                                    ↑
                                            Should be 1, not 0!
```

## The Fix

Changed the coordinator to check for BOTH `NEEDS_FIXES` and `QA_FAILED` statuses:

```python
# CRITICAL FIX: TaskState.__post_init__ converts NEEDS_FIXES to QA_FAILED for compatibility
# So we need to check for BOTH statuses
needs_fixes = [t for t in state.tasks.values() 
               if t.status in [TaskStatus.NEEDS_FIXES, TaskStatus.QA_FAILED]]
```

## Why This Bug Existed

The "compatibility mapping" was added to handle legacy state files that used `NEEDS_FIXES` before it was renamed to `QA_FAILED`. But:

1. The QA phase was updated to create tasks with `NEEDS_FIXES` status
2. The coordinator was only checking for `NEEDS_FIXES` status
3. The mapping silently converted all `NEEDS_FIXES` to `QA_FAILED`
4. Result: coordinator never saw any tasks needing fixes

## Expected Behavior After Fix

```
Iteration 1: QA (finds issue) → creates NEEDS_FIXES task
Iteration 2: Coordinator sees needs_fixes=[task] → Debugging
Iteration 3: Debugging (fixes issue) → marks task COMPLETED
Iteration 4: QA (next file) → creates NEEDS_FIXES task
Iteration 5: Coordinator sees needs_fixes=[task] → Debugging
...and so on
```

## Files Modified

- `pipeline/coordinator.py`: Updated `needs_fixes` list comprehension to check both statuses

## Testing

To verify the fix:
1. Run the pipeline
2. Watch for QA phase to find issues
3. Verify next iteration goes to Debugging phase (not QA again)
4. Check task status shows "X fixes" instead of "0 fixes"

## Related Issues

This bug also explains why:
- The "integration points" false positives weren't being addressed
- The system kept running QA instead of fixing known issues
- Progress was stuck at 24% (QA finding issues but never fixing them)
- The polytopic learning couldn't adapt (no debugging data to learn from)