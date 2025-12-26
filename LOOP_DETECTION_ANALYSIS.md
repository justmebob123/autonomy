# Loop Detection False Positive Analysis

## Issue Identified

The loop detector is triggering false positives during normal QA and investigation workflows.

### Example from User's Output:

```
19:52:38 [WARNING] Loop intervention #1
19:52:38 [WARNING] LOOP DETECTED - INTERVENTION REQUIRED

1. PATTERN_REPETITION [CRITICAL]
   Complex pattern repeated 10 times
   Evidence:
     - Pattern: unknown() -> unknown()
     
2. STATE_CYCLE [HIGH]
   System cycling through same 3 states 8 times
   Evidence:
     - States: debug:unknown -> debug:unknown -> debug:unknown
     
3. ACTION_LOOP [LOW]
   Same action repeated 3 times consecutively
   Evidence:
     - Action: unknown()
```

### Context:

This happened during **QA phase** which was:
- Reading file: `src/execution/server_pool.py`
- Searching code for imports: `(import\s+|from\s+)(threading|logging|uuid)\b`
- Searching code for class: `ServerPool`
- Searching code for methods: `(acquire_server|acquire_for_conversation|acquire_for_tool)\(`

**This is NORMAL QA behavior**, not a loop!

## Root Cause

The loop detector is tracking actions as "unknown()" because:
1. Tool names aren't being properly extracted
2. QA phase naturally calls multiple tools in sequence
3. The detector sees repeated "unknown" actions and flags it as a loop

## Problems with Current Detection

### 1. Tool Name Extraction
```python
# Current code likely does:
action = call.get('name', 'unknown')  # Gets 'unknown' for nested structure
```

Should be:
```python
# Handle nested structure
if 'function' in call:
    action = call['function'].get('name', 'unknown')
else:
    action = call.get('name', 'unknown')
```

### 2. Phase Context Ignored

The detector doesn't consider:
- **QA phase** naturally reads multiple files
- **Investigation phase** naturally gathers context from multiple sources
- **Debugging phase** may try multiple approaches

### 3. Success/Failure Not Tracked

The detector counts repetitions but doesn't track:
- Did the action succeed or fail?
- Is progress being made?
- Are different files being processed?

## Proposed Fixes

### Fix #1: Improve Tool Name Extraction

Update `ActionTracker` to properly extract tool names from nested structures.

### Fix #2: Add Phase-Aware Detection

Different phases have different "normal" patterns:

**QA Phase:**
- Reading 5-10 files: NORMAL
- Searching code 10+ times: NORMAL
- Only flag if SAME file read 3+ times

**Investigation Phase:**
- Reading 3-5 related files: NORMAL
- Calling investigation tools: NORMAL
- Only flag if no progress after 3 attempts

**Debugging Phase:**
- Trying 2-3 different approaches: NORMAL
- Only flag if SAME fix attempted 3+ times

### Fix #3: Track Success/Failure

```python
class ActionTracker:
    def track_action(self, action: str, success: bool, context: dict):
        # Track whether action succeeded
        # Only count as loop if FAILING repeatedly
        # Success + repetition = thorough work, not a loop
```

### Fix #4: Add File Context

```python
# Don't flag as loop if processing different files
if action == 'read_file':
    if all files are different:
        return False  # Not a loop, just thorough
```

## Immediate Action

For now, the false positive is harmless (just a warning), but we should fix this to avoid:
1. Unnecessary warnings cluttering output
2. Potential intervention when none is needed
3. Confusion about system state

## Priority

**Medium** - System is working correctly despite the false positive, but this should be fixed to improve user experience and system reliability.