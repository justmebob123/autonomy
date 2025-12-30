# CRITICAL BUG FIX: QA_FAILED Tasks Not Being Reactivated

## Problem Identified

The pipeline was stuck in an infinite loop between planning and coding phases, with the following symptoms:

1. **69-79 tasks stuck in QA_FAILED status**
2. **Coordinator attempting reactivation**: "🔄 Coordinator forcing reactivation of 69 tasks"
3. **Zero tasks actually reactivated**: "Reactivated 0 tasks"
4. **Pipeline looping endlessly**: Planning → Coding → Planning → Coding...
5. **No new files being created**: Only existing files being checked and marked "already correct"

## Root Cause

The reactivation logic in `pipeline/coordinator.py` line 1652 only checked for:
```python
if task.status in [TaskStatus.SKIPPED, TaskStatus.FAILED]:
```

But the tasks were in **QA_FAILED** status, which was NOT included in this check.

### Why This Happened

When tasks fail QA, they are marked as `TaskStatus.QA_FAILED`. The coordinator's safety net tries to reactivate failed tasks, but it was only looking for `SKIPPED` and `FAILED` statuses, completely missing `QA_FAILED` tasks.

## The Fix

**File**: `pipeline/coordinator.py`  
**Line**: 1652  
**Change**: Added `TaskStatus.QA_FAILED` to the reactivation status check

```python
# BEFORE
if task.status in [TaskStatus.SKIPPED, TaskStatus.FAILED]:

# AFTER
if task.status in [TaskStatus.SKIPPED, TaskStatus.FAILED, TaskStatus.QA_FAILED]:
```

## Expected Behavior After Fix

1. ✅ QA_FAILED tasks will now be properly reactivated
2. ✅ Coordinator will show "Reactivated N tasks" where N > 0
3. ✅ Pipeline will make actual progress on failed tasks
4. ✅ New files will be created/modified instead of just checking existing ones
5. ✅ No more infinite planning-coding loops

## Testing Instructions

```bash
cd /home/ai/AI/autonomy
git pull
python3 run.py -vv ../test-automation/
```

You should now see:
- "✅ Reactivated: [task description]..." messages
- "Reactivated N tasks" where N > 0
- Actual file modifications happening
- Progress being made on QA_FAILED tasks

## Commit Details

**Commit**: 6c1cb39  
**Message**: "CRITICAL FIX: Include QA_FAILED tasks in reactivation logic"  
**Branch**: main  
**Status**: Pushed to GitHub

## Impact

This was a **critical bug** that prevented the pipeline from making any progress on tasks that had failed QA review. The pipeline would endlessly loop without ever attempting to fix the QA failures.

With this fix, the pipeline can now:
- Properly retry QA_FAILED tasks
- Make progress on the 69-79 stuck tasks
- Actually create/modify files instead of just checking existing ones
- Complete the development work as intended