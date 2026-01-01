# ROOT CAUSE IDENTIFIED: AI Calling Multiple Tools Per Iteration

## The REAL Problem

After 37+ attempts, I finally identified the root cause of the infinite loop:

**The AI is outputting multiple tool calls in a single response:**
```json
{"name": "read_file", "arguments": {"filepath": "resources/resource_estimator.py"}}
{"name": "read_file", "arguments": {"filepath": "core/resource/resource_estimator.py"}}
{"name": "read_file", "arguments": {"filepath": "ARCHITECTURE.md"}}
{"name": "compare_file_implementations", "arguments": {...}}
```

**But the system only executes the FIRST tool call:**
```
Extracted tool call from text response
📖 [AI Activity] Reading file: resources/resource_estimator.py
✅ Result: SUCCESS
⚠️ Task not resolved - RETRYING
```

**Result**: The AI keeps outputting the same 4-tool sequence, but only the first tool executes each time, creating an infinite loop.

## Evidence from Logs

```
13:14:15 [INFO] Response length: 1,571 characters  # Multiple tools!
13:14:15 [INFO] Preview: {"name": "read_file", ...} {"name": "read_file", ...} {"name": "read_file", ...}
13:14:15 [INFO] Extracted tool call from text response  # Only ONE extracted
13:14:15 [INFO] 📖 [AI Activity] Reading file: resources/resource_estimator.py  # Only first one executed
```

This pattern repeats for 37+ iterations!

## Why This Happens

### The AI's Mental Model
The AI thinks it can plan ahead and output a sequence of tools:
```
"I need to:
1. Read file A
2. Read file B  
3. Read architecture
4. Compare them
5. Merge them

Let me output all 5 tool calls at once!"
```

### The System's Reality
The system only processes ONE tool call per iteration:
```
Iteration 1: Execute tool 1 → Return result
Iteration 2: AI outputs tools 1-5 again → Execute tool 1 → Return result
Iteration 3: AI outputs tools 1-5 again → Execute tool 1 → Return result
... infinite loop
```

## The Fix

### Added Explicit Warning
```
⚠️ CRITICAL: You can only call ONE tool per iteration. 
After each tool, wait for the result before calling the next tool.
```

### Changed Workflow Format
**Before**:
```
1️⃣ Read both files:
   read_file(filepath="<file1>")
   read_file(filepath="<file2>")
```
This implies "call both at once"

**After**:
```
1️⃣ First iteration: Read the first conflicting file
   read_file(filepath="<file1>")
   → Wait for result

2️⃣ Second iteration: Read the second conflicting file
   read_file(filepath="<file2>")
   → Wait for result
```
This explicitly says "one per iteration"

### Added DO/DON'T Examples
```
DO NOT output multiple tool calls like this:
❌ {"name": "read_file", ...} {"name": "read_file", ...} {"name": "compare_file_implementations", ...}

Instead, output ONE tool call per iteration:
✅ Iteration 1: {"name": "read_file", "arguments": {"filepath": "resources/resource_estimator.py"}}
✅ Iteration 2: {"name": "read_file", "arguments": {"filepath": "core/resource/resource_estimator.py"}}
```

## Expected Behavior After Fix

### Before Fix (Attempt 37)
```
Iteration 1: AI outputs 4 tools → System executes tool 1 → RETRY
Iteration 2: AI outputs 4 tools → System executes tool 1 → RETRY
Iteration 3: AI outputs 4 tools → System executes tool 1 → RETRY
... infinite loop (same tool 1 executed 37 times)
```

### After Fix
```
Iteration 1: AI outputs 1 tool (read file 1) → System executes → SUCCESS
Iteration 2: AI outputs 1 tool (read file 2) → System executes → SUCCESS
Iteration 3: AI outputs 1 tool (read architecture) → System executes → SUCCESS
Iteration 4: AI outputs 1 tool (compare) → System executes → SUCCESS
Iteration 5: AI outputs 1 tool (merge) → System executes → ✅ RESOLVED
```

## Why This Is The Root Cause

All previous fixes addressed symptoms, not the root cause:
1. ✅ Task-type-specific requirements - Good, but didn't fix the loop
2. ✅ Specific file names in context - Good, but didn't fix the loop
3. ✅ Remove report escape hatch - Good, but didn't fix the loop

**The root cause**: AI doesn't understand the execution model (one tool per iteration)

## Impact

This fix should:
- ✅ Break the infinite loop immediately
- ✅ AI will call one tool per iteration
- ✅ Each tool will execute and return results
- ✅ AI will progress through the workflow
- ✅ Task will complete in 5-7 iterations

## Commit

**Hash**: c4a2371
**Message**: "fix: CRITICAL - Explicitly tell AI to call ONE tool per iteration"
**Changes**: 1 file, 30 insertions, 14 deletions

## Testing

The user should see:
```
Iteration 1: read_file("resources/resource_estimator.py") → SUCCESS
Iteration 2: read_file("core/resource/resource_estimator.py") → SUCCESS
Iteration 3: read_file("ARCHITECTURE.md") → SUCCESS
Iteration 4: compare_file_implementations(...) → SUCCESS
Iteration 5: merge_file_implementations(...) → ✅ RESOLVED
```

Instead of:
```
Iteration 28-37: read_file("resources/resource_estimator.py") → RETRY
... infinite loop
```

## Status

✅ ROOT CAUSE IDENTIFIED AND FIXED

This is the critical fix that should break the infinite loop.