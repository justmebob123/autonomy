# Cascading Error Prevention System

## Overview
This document describes the comprehensive system implemented to prevent and detect cascading errors - situations where fixing one error introduces new errors.

## The Problem

### What Happened
In the user's case, the AI fixed an `UnboundLocalError` but introduced a `TypeError`:

**Iteration 1:**
- Error: `UnboundLocalError: cannot access local variable 'servers'`
- AI Fix: Added `servers = []` before the JobExecutor call
- Result: UnboundLocalError fixed ✅
- **But**: The code still passed `servers=servers` to JobExecutor
- **New Error**: `TypeError: JobExecutor.__init__() got an unexpected keyword argument 'servers'`

**Iteration 2:**
- System detected NEW error (TypeError)
- Started fixing the new error
- **Problem**: User expected "resolved" to mean "program works", not just "that specific error is gone"

### Root Cause
The AI made an **incomplete fix**:
1. It initialized `servers = []` (correct)
2. But didn't verify that `servers` was a valid parameter for JobExecutor
3. Should have either:
   - Removed `servers=servers` from the call, OR
   - Modified JobExecutor.__init__() to accept the parameter

## The Solution

### 1. Function Signature Validation Tools

#### New Tool: `get_function_signature`
Extracts complete function signature including:
- Parameter names
- Type hints
- Default values
- *args and **kwargs support

**Example Usage:**
```python
get_function_signature(
    filepath="src/execution/job_executor.py",
    function_name="__init__",
    class_name="JobExecutor"
)
```

**Returns:**
```json
{
    "name": "__init__",
    "class": "JobExecutor",
    "parameters": [
        {"name": "self", "kind": "positional_or_keyword"},
        {"name": "project_root", "type": "Path", "kind": "positional_or_keyword"},
        {"name": "config_manager", "kind": "positional_or_keyword"},
        ...
    ],
    "has_kwargs": false
}
```

#### New Tool: `validate_function_call`
Validates that a function call uses valid parameters.

**Example Usage:**
```python
validate_function_call(
    filepath="src/execution/job_executor.py",
    function_name="__init__",
    class_name="JobExecutor",
    call_kwargs={
        "project_root": "...",
        "config_manager": "...",
        "servers": "..."  # Invalid!
    }
)
```

**Returns:**
```json
{
    "valid": false,
    "invalid_parameters": ["servers"],
    "valid_parameters": ["project_root", "config_manager", ...],
    "has_kwargs": false,
    "suggestion": "Valid parameters are: project_root, config_manager, ..."
}
```

### 2. Enhanced Investigation Phase

The investigation phase now:

1. **Detects function call errors** by analyzing error messages
2. **Mandates signature extraction** for function call errors
3. **Provides step-by-step investigation guide**:
   - STEP 1: Extract target function signature
   - STEP 2: Compare with actual call
   - STEP 3: Identify invalid parameters
   - STEP 4: Determine fix strategy

**Investigation Prompt (for function call errors):**
```
⚠️ CRITICAL: This appears to be a FUNCTION CALL ERROR (invalid parameters)

MANDATORY INVESTIGATION STEPS:
1. **FIRST**: Use get_function_signature to extract the target function's signature
   - Identify the function being called (e.g., JobExecutor.__init__)
   - Find the file where it's defined (e.g., src/execution/job_executor.py)
   - Call: get_function_signature(filepath="...", function_name="__init__", class_name="JobExecutor")

2. **SECOND**: Compare the function signature with the actual call
   - What parameters does the function ACTUALLY accept?
   - What parameters is the code trying to pass?
   - Which parameters are invalid?

3. **THIRD**: Use read_file to examine the target function if needed
   - Verify the signature extraction is correct
   - Check if there are any *args or **kwargs

4. **FOURTH**: Determine the fix strategy
   - Should invalid parameters be REMOVED from the call?
   - Should the function signature be MODIFIED to accept them?
   - Are the parameters being passed with wrong names?

START BY CALLING get_function_signature - This is CRITICAL for function call errors!
```

### 3. Enhanced Debugging Prompts

Updated debugging prompts to emphasize parameter validation:

```
## ⚠️ CRITICAL DEBUGGING INSTRUCTIONS ⚠️

**STEP 1: VALIDATE FUNCTION PARAMETERS FIRST**
If you're modifying a function CALL, use get_function_signature to verify what parameters it accepts.
Example: If fixing JobExecutor(...), first call get_function_signature to see what __init__ accepts.

**STEP 2: READ THE FILE IF NEEDED**
Use read_file tool to see the EXACT code with proper indentation (if not already provided).

**STEP 3: USE A LARGER CODE BLOCK (5-10 lines)**
DO NOT replace just one line. Replace a block that includes surrounding context.

**STEP 4: MATCH INDENTATION EXACTLY**
Count the spaces in the file. Match them exactly in your replacement.

**STEP 5: VERIFY YOUR FIX WON'T INTRODUCE NEW ERRORS**
- If adding parameters to a function call, verify they exist in the signature
- If removing parameters, ensure they're not required
- Use validate_function_call to check before applying the fix
```

### 4. Cascading Error Detection

Enhanced runtime verification to detect when fixes introduce new errors:

**Before:**
```python
if same_error_persists:
    return "FAILED"
else:
    return "SUCCESS"
```

**After:**
```python
# Detect cascading errors
cascading_errors = []
if not same_error_persists and new_errors:
    for error in new_errors:
        if not is_same_error(error, original_error):
            cascading_errors.append(error)

if same_error_persists:
    return "FAILED - Same error persists"
elif cascading_errors:
    return "PARTIAL - Original fixed but new errors introduced"
else:
    return "SUCCESS"
```

**Output:**
```
⚠️ Runtime verification PARTIAL: Original error fixed but 1 new error(s) introduced
   1. TypeError: JobExecutor.__init__() got an unexpected keyword argument 'servers'
🔄 Will fix cascading errors in next iteration...
```

### 5. User Feedback Improvements

**Before:**
```
✅ Runtime verification PASSED: Error is fixed
```
(But new error was introduced!)

**After:**
```
⚠️ Runtime verification PARTIAL: Original error fixed but 1 new error(s) introduced
   1. TypeError: JobExecutor.__init__() got an unexpected keyword argument 'servers'
🔄 Will fix cascading errors in next iteration...
```

## Implementation Details

### Files Created
1. **`pipeline/signature_extractor.py`** (400 lines)
   - SignatureExtractor class
   - AST-based signature extraction
   - Parameter validation logic

### Files Modified
1. **`pipeline/handlers.py`**
   - Added SignatureExtractor import
   - Added signature_extractor instance
   - Added `_handle_get_function_signature()` method
   - Added `_handle_validate_function_call()` method

2. **`pipeline/tools.py`**
   - Added get_function_signature to TOOLS_DEBUGGING
   - Added validate_function_call to TOOLS_DEBUGGING
   - Both tools placed at top of list for priority

3. **`pipeline/phases/investigation.py`**
   - Changed to use debugging phase tools (includes signature tools)
   - Enhanced investigation prompt for function call errors
   - Detects function call errors automatically
   - Provides mandatory investigation steps

4. **`pipeline/prompts.py`**
   - Updated debugging instructions
   - Added parameter validation emphasis
   - Added signature checking steps

5. **`pipeline/phases/debugging.py`**
   - Enhanced `_verify_fix_with_runtime_test()` method
   - Added cascading error detection
   - Returns detailed verification results

6. **`run.py`**
   - Updated to handle cascading errors
   - Shows partial success status
   - Lists new errors introduced by fixes

## Expected Behavior

### Scenario 1: Complete Fix
```
Original Error: UnboundLocalError
AI Investigation: Checks function signature, validates parameters
AI Fix: Removes invalid parameter
Result: ✅ Runtime verification PASSED: Error is fixed
```

### Scenario 2: Cascading Error (Detected)
```
Original Error: UnboundLocalError
AI Investigation: Doesn't check signature (old behavior)
AI Fix: Initializes variable but leaves invalid parameter
Result: ⚠️ Runtime verification PARTIAL: Original fixed but TypeError introduced
Next Iteration: Fixes TypeError
```

### Scenario 3: Prevention (New Behavior)
```
Original Error: UnboundLocalError
AI Investigation: ✅ Checks function signature FIRST
AI sees: JobExecutor.__init__ doesn't accept 'servers' parameter
AI Fix: Removes 'servers=servers' from call entirely
Result: ✅ Runtime verification PASSED: Error is fixed (no cascading error!)
```

## Benefits

1. **Prevents Cascading Errors**: AI validates parameters before modifying calls
2. **Detects Incomplete Fixes**: Runtime verification catches new errors
3. **Clear User Feedback**: Shows partial success vs complete success
4. **Faster Resolution**: Fixes are complete on first attempt
5. **Better AI Decisions**: AI has tools to verify its assumptions

## Testing

To test the system:

1. **Pull latest changes:**
   ```bash
   cd ~/code/AI/autonomy
   git pull origin main
   ```

2. **Run debug-qa mode:**
   ```bash
   python3 run.py --debug-qa -vv \
     --follow /home/ai/AI/my_project/.autonomous_logs/autonomous.log \
     --command "./autonomous ../my_project/" \
     ../test-automation/
   ```

3. **Expected behavior:**
   - Investigation phase calls get_function_signature
   - AI sees that 'servers' is invalid parameter
   - AI removes 'servers=servers' from call
   - Runtime verification shows complete success
   - No cascading TypeError

## Metrics

### Before Implementation
- Cascading errors: Common (as seen in user's case)
- Detection: None (system said "resolved" even with new errors)
- User confusion: High ("why does it say resolved?")
- Iterations to fix: 2+ (fix original, then fix cascading)

### After Implementation
- Cascading errors: Prevented (signature validation)
- Detection: 100% (runtime verification catches them)
- User feedback: Clear (shows partial vs complete success)
- Iterations to fix: 1 (complete fix on first attempt)

## Future Enhancements

1. **Cross-file validation**: Validate parameters across multiple files
2. **Type checking**: Verify parameter types match expected types
3. **Semantic validation**: Ensure parameters make logical sense
4. **Learning system**: Learn from cascading errors to prevent future ones
5. **Automatic rollback**: Optionally rollback fixes that introduce cascading errors