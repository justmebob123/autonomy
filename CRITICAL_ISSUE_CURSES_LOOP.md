# Critical Issue: AI Stuck in Loop on Curses Error

## Problem Identified

The AI is stuck in an infinite loop trying to fix curses errors. Analysis shows:

### Symptoms:
1. **Attempt #1**: AI provides code with nested try blocks
2. **Result**: "Original code not found in file"
3. **Attempt #2**: AI provides THE EXACT SAME CODE again
4. **Result**: "Original code not found in file" (again)
5. **Loop continues indefinitely**

### Root Cause:
The AI is NOT reading the file to see the current state before attempting fixes. It's working from stale context and keeps hallucinating the same incorrect code structure.

### Evidence from Logs:
```
20:12:02 [INFO]       ├─ original_code:             try:
                curses.noecho()
                try:
                    curses.noecho()  # NESTED TRY - WRONG!
                    curses.cbreak()
                    
20:12:02 [WARNING]   ⚠️ Original code not found in src/ui/pipeline_ui.py

20:25:01 [INFO]       ├─ original_code:             try:
                curses.noecho()
                try:
                    curses.noecho()  # SAME WRONG CODE AGAIN!
                    curses.cbreak()
```

## Why This Happens

### 1. **Investigation Phase Reads File Once**
- Investigation phase reads the file at the START
- Provides context to debugging phase
- But if the file changes during debugging, context becomes stale

### 2. **Debugging Phase Doesn't Re-Read**
- Debugging phase uses the stale context from investigation
- Doesn't read the file again before each attempt
- AI works from memory, not current file state

### 3. **Specialist Consultation Doesn't Help**
- Pattern Analyst is consulted
- But it also doesn't read the current file
- Just provides generic advice based on stale context

### 4. **FunctionGemma Can't Fix**
- FunctionGemma tries to fix the tool call
- But it's given the same stale context
- Can't fix what it can't see

## The Fix Needed

### MANDATORY: Read File Before EVERY Attempt

The debugging phase MUST read the current file state before EVERY fix attempt, not just once at the start.

**Current Flow (BROKEN):**
```
Investigation → Read file once → Debugging Attempt #1 → Fail
                                → Debugging Attempt #2 (uses stale context) → Fail
                                → Debugging Attempt #3 (uses stale context) → Fail
```

**Fixed Flow (NEEDED):**
```
Investigation → Read file once → Debugging Attempt #1 → Fail
                                → READ FILE AGAIN → Debugging Attempt #2 → Success
```

### Implementation:

In `pipeline/phases/debugging.py`, the retry logic should:

```python
# BEFORE EVERY ATTEMPT (not just first):
current_file_content = self.read_file(filepath)

# Update the context with CURRENT state
variables['code'] = current_file_content

# Then call AI with FRESH context
response = self.client.chat(...)
```

### Why This Matters:

1. **File may have changed** - Previous attempts may have partially modified it
2. **AI needs current state** - Can't fix what it can't see
3. **Prevents hallucination** - AI works from facts, not memory
4. **Breaks infinite loops** - Each attempt sees actual current state

## Additional Enhancements Needed

### 1. **Show AI the "Did you mean" Suggestion**

When code is not found, the system suggests:
```
Did you mean:
    curses.noecho()
    try:
        curses.noecho()
        curses.cbreak()
```

But this suggestion is NOT shown to the AI! It's only logged. The AI should see this and use it.

### 2. **Limit Identical Attempts**

If the AI provides the EXACT SAME code twice:
- Don't execute it again
- Force a different approach
- Consult a different specialist
- Or ask user for guidance

### 3. **Enforce Tool Usage in Retry**

The retry prompt should MANDATE:
```
CRITICAL: Before attempting another fix:
1. Call read_file to see the CURRENT file state
2. Use the EXACT code you see in the file
3. Do NOT use code from previous attempts
```

## Immediate Action Required

This is a **CRITICAL** bug that causes infinite loops. The fix is straightforward:

**Add to debugging.py retry logic:**
```python
# CRITICAL: Always read current file state before retry
logger.info(f"  📖 Reading current file state before retry...")
current_content = self.read_file(filepath)
variables['code'] = current_content
variables['file_content'] = current_content
```

This ensures the AI always sees the CURRENT state, not stale context.

## Priority: CRITICAL

This bug prevents the system from making progress on ANY error that requires multiple attempts. It must be fixed immediately.