# Fix Summary: Allow Step 2 Validation in Multi-Turn Workflow

## Problem
The system prompt defines a 3-step workflow:
- **STEP 1:** Call `find_similar_files` (discovery)
- **STEP 2:** Call `validate_filename` (validation)
- **STEP 3:** Call `create_file` or `str_replace` (creation)

However, the validation logic was treating Step 2 as "analysis again" and failing the task, even though the model was correctly following the prescribed workflow.

## Root Cause
Both `find_similar_files` and `validate_filename` were in the `analysis_tools` list. When the model:
1. **Attempt 1:** Called `find_similar_files` (Step 1) → SUCCESS
2. **Attempt 2:** Called `validate_filename` (Step 2) → FAILED as "analysis again"

The code didn't distinguish between:
- **Legitimate Step 2** (validation after discovery)
- **Stuck in analysis** (repeating Step 1 tools)

## Solution
Modified the validation logic to:
1. Recognize Step 2 tools (`validate_filename`) as distinct from Step 1 tools
2. Allow Step 2 in the second attempt if Step 1 was completed
3. Only fail if the model repeats Step 1 tools or doesn't proceed to Step 3

### Code Changes
```python
# Check if this is Step 2 (validation only)
step2_tools = ['validate_filename']
is_step2_only = all(call.get("function", {}).get("name") in step2_tools for call in tool_calls)

if task.attempts == 1 or (task.attempts == 2 and is_step2_only and task.metadata.get('analysis_completed', False)):
    # Allow Step 1 in attempt 1, or Step 2 in attempt 2
    step_name = "STEP 2 (VALIDATION)" if is_step2_only else "STEP 1-2"
    # ... mark as success and continue
```

## Expected Behavior

### Correct Workflow (Now Allowed)
1. **Attempt 1:** `find_similar_files` → SUCCESS (Step 1 complete)
2. **Attempt 2:** `validate_filename` → SUCCESS (Step 2 complete)
3. **Attempt 3:** `create_file` → SUCCESS (Step 3 complete)

### Stuck in Analysis (Still Caught)
1. **Attempt 1:** `find_similar_files` → SUCCESS (Step 1 complete)
2. **Attempt 2:** `find_similar_files` → FAILED (repeating Step 1)

### Skipping to Creation (Allowed)
1. **Attempt 1:** `find_similar_files` + `validate_filename` + `create_file` → SUCCESS (all steps in one turn)

## Benefits
- ✅ Model can follow the 3-step workflow as prescribed
- ✅ No false failures for legitimate validation steps
- ✅ Still catches infinite analysis loops
- ✅ Supports both multi-turn and single-turn completion
- ✅ Clear logging of which step is being completed

## Files Modified
- `pipeline/phases/coding.py` - Updated validation logic to allow Step 2

## Testing
The system should now:
1. Allow Step 1 (discovery) in first attempt
2. Allow Step 2 (validation) in second attempt
3. Require Step 3 (creation) by third attempt
4. Still fail if model repeats Step 1 tools
5. Log which step is being completed for debugging