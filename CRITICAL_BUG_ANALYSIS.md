# CRITICAL BUG ANALYSIS - Infinite Loop Root Cause

## Date: 2024-12-25 02:21

## Problem Summary
The debugging system is stuck in an infinite loop trying to fix curses errors. Each iteration creates nested try blocks, making the code progressively worse.

## Root Cause: Verification Logic Bug

### The Issue
When AI wraps code in try/except blocks, the verification logic in `handlers.py` incorrectly flags it as a failure because:

1. AI replaces:
   ```python
   curses.cbreak()
   ```
   
2. With:
   ```python
   try:
       curses.cbreak()
   except curses.error:
       pass
   ```

3. Verification checks if original code (`curses.cbreak()`) is still in file
4. It IS still there (inside the try block)
5. Verification fails with "Original code still present"
6. But due to new architecture, change is NOT rolled back
7. AI sees "verification failed" and tries again
8. Creates NESTED try blocks
9. **INFINITE LOOP**

## Evidence from Logs

```
02:16:08 [INFO]       ├─ original_code:                 try:
                    self.stdscr = curses.initscr()
                    curses.noecho()
                    try:                           # ← NESTED!
                        self.stdscr = curses.initscr()  # ← DUPLICATE!
```

This shows multiple layers of try blocks from repeated failed attempts.

## The Verification Logic (handlers.py)

```python
# Current logic (BROKEN for try/except wrapping)
if original not in new_code:
    if original in written_content:
        verification_errors.append("Original code still present")
```

This logic assumes that if original code is gone from `new_code` but present in `written_content`, it's a failure. But this is WRONG when wrapping in try/except!

## Solution Required

### Option 1: Smarter Verification (RECOMMENDED)
Detect when code is being wrapped (not replaced) and adjust verification:

```python
# Check if this is a wrapping operation (try/except, if/else, etc.)
is_wrapping = (
    original in new_code and  # Original is inside new code
    len(new_code) > len(original) * 1.5  # New code is significantly larger
)

if is_wrapping:
    # For wrapping, just verify new code was added
    if new_code not in written_content:
        verification_errors.append("New code not found in file")
else:
    # For replacement, verify original was removed
    if original not in new_code:
        if original in written_content:
            verification_errors.append("Original code still present")
```

### Option 2: Disable Verification for Try/Except
Add a parameter to skip verification when wrapping in error handling.

### Option 3: Better AI Guidance
Instruct AI to REPLACE the entire block including the try/except, not wrap it.

## Immediate Action Required

1. **Stop the current run** - It will loop forever
2. **Manually fix the file** - Remove nested try blocks
3. **Fix verification logic** - Implement Option 1
4. **Update AI prompts** - Clarify wrapping vs replacement
5. **Test with simple case** - Verify fix works

## File to Fix
- `pipeline/handlers.py` - Line ~180-200 (verification logic)

## Test Case
Create a test that:
1. Has code with an error
2. AI wraps it in try/except
3. Verification should PASS (not fail)
4. No nested try blocks should be created

## Priority
**CRITICAL** - System is completely non-functional due to this bug.