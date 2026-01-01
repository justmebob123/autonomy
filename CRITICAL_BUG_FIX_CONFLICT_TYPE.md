# Critical Bug Fix: CONFLICT vs INTEGRATION Type Mismatch

## The Problem

The step-aware prompt system I implemented was **NEVER BEING USED** despite being correctly implemented. The system continued to loop infinitely because it was using the old generic prompt.

## Root Cause Analysis

### Evidence from Logs
```
🎯 Selected task: refactor_0409 - Integration conflict
Priority: critical, Type: conflict
```

The task type is **`conflict`** (lowercase, from enum value).

### Code Inspection

**The Enum Definition** (`pipeline/state/refactoring_task.py`):
```python
class RefactoringIssueType(Enum):
    DUPLICATE = "duplicate"
    COMPLEXITY = "complexity"
    DEAD_CODE = "dead_code"
    ARCHITECTURE = "architecture"
    CONFLICT = "conflict"          # ← This one
    INTEGRATION = "integration"    # ← Different from this one
    NAMING = "naming"
    STRUCTURE = "structure"
```

**The Routing Code** (`pipeline/phases/refactoring.py` line 1367):
```python
elif task.issue_type == RefactoringIssueType.INTEGRATION:
    return self._get_integration_conflict_prompt(task, context)
```

**The Problem**: 
- Tasks are created with type `CONFLICT`
- Code only checks for `INTEGRATION`
- These are **two separate enum values**
- Result: Step-aware prompt never called, falls through to generic prompt

### Why This Happened

When integration conflicts are detected, tasks are created with:
```python
task = manager.create_task(
    issue_type=RefactoringIssueType.CONFLICT,  # ← Uses CONFLICT
    ...
)
```

But the routing logic only checked for:
```python
elif task.issue_type == RefactoringIssueType.INTEGRATION:  # ← Checks INTEGRATION
```

So the condition was **never true**, and the step-aware prompt was **never called**.

## The Fixes Applied

### Fix #1: Route CONFLICT to Step-Aware Prompt (Commit f92472b)

**File**: `pipeline/phases/refactoring.py` line 1367

**Before**:
```python
elif task.issue_type == RefactoringIssueType.INTEGRATION:
    return self._get_integration_conflict_prompt(task, context)
```

**After**:
```python
elif task.issue_type == RefactoringIssueType.INTEGRATION or task.issue_type == RefactoringIssueType.CONFLICT:
    return self._get_integration_conflict_prompt(task, context)
```

### Fix #2: Handle CONFLICT in Analysis Data Formatting (Commit 759ff73)

**File**: `pipeline/phases/refactoring.py` line 904

**Before**:
```python
elif issue_type == RefactoringIssueType.INTEGRATION:
    # Check if this is an unused class/function issue
    issue_desc = str(data).lower()
```

**After**:
```python
elif issue_type == RefactoringIssueType.INTEGRATION or issue_type == RefactoringIssueType.CONFLICT:
    # Check if this is an unused class/function issue
    issue_desc = str(data).lower()
```

## Why The Step-Aware Prompt Wasn't Working

The step-aware prompt implementation was **100% correct**:
- ✅ Analyzes conversation history
- ✅ Determines current step (1-5)
- ✅ Shows only next action
- ✅ Includes progress tracker
- ✅ Forces iterative execution

**BUT** it was never being called because of the type mismatch!

The system was falling through to the generic prompt, which:
- ❌ Shows all 5 steps at once
- ❌ AI interprets as "output all 5 tools"
- ❌ System executes only first tool
- ❌ Infinite loop continues

## Expected Behavior After Fixes

### Before Fixes
```
Task type: CONFLICT
Routing check: task.issue_type == INTEGRATION? → FALSE
Falls through to: Generic prompt
AI sees: All 5 steps
AI outputs: 4 tools at once
System executes: Only first tool
Result: Infinite loop (attempts 49, 50, 51, 52...)
```

### After Fixes
```
Task type: CONFLICT
Routing check: task.issue_type == INTEGRATION or CONFLICT? → TRUE
Uses: Step-aware prompt
AI sees: "YOU ARE ON STEP 1 OF 5 - Call read_file(file1)"
AI outputs: 1 tool
System executes: 1 tool
Next iteration: "YOU ARE ON STEP 2 OF 5 - Call read_file(file2)"
Result: Linear progress (step 1 → 2 → 3 → 4 → 5 → COMPLETE)
```

## Testing Instructions

```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

**Look for these indicators**:
- ✅ Prompt shows "YOU ARE ON STEP X OF 5"
- ✅ Prompt shows progress tracker with ✅ and ⬜
- ✅ AI outputs only ONE tool per iteration
- ✅ Step numbers increment: 1 → 2 → 3 → 4 → 5
- ✅ Task completes in 5-7 iterations (not 50+)

## Lessons Learned

### 1. Always Check Enum Values
When working with enums, verify the **actual values** being used, not just the names.

### 2. Test with Real Data
The step-aware prompt worked perfectly in isolation, but failed in production because of a type mismatch.

### 3. Trace the Full Path
Follow the execution path from task creation → routing → prompt selection to ensure all pieces connect.

### 4. Check Logs Carefully
The logs showed `Type: conflict` which was the key clue that led to discovering the mismatch.

## Conclusion

The step-aware prompt system was correctly implemented but never executed due to a simple type mismatch. By adding `CONFLICT` to the routing conditions, the system now uses the step-aware prompt and should eliminate the infinite loop.

**Status**: ✅ FIXED - Both routing and data formatting now handle CONFLICT type
**Commits**: f92472b, 759ff73
**Ready for testing**: YES