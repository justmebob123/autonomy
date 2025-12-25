# Verification Logic Fix Implementation

## Problem
The verification logic in `handlers.py` was causing infinite loops when AI wrapped code in try/except blocks. The system would:
1. AI wraps `curses.cbreak()` in try/except
2. Verification checks if original code is still present
3. It IS present (inside the try block)
4. Verification fails with "Original code still present"
5. AI tries again, creating nested try blocks
6. **INFINITE LOOP**

## Root Cause
The verification logic didn't distinguish between:
- **Wrapping operations** (code is contained within new code, like try/except)
- **Replacement operations** (code is completely replaced)

## Solution
Implement smart detection of wrapping vs replacement:

```python
# Normalize whitespace for comparison
original_normalized = ' '.join(original.split())
new_code_normalized = ' '.join(new_code.split())
written_normalized = ' '.join(written_content.split())

# Detect if this is a wrapping operation
is_wrapping = (
    original_normalized in new_code_normalized and  # Original is inside new code
    len(new_code_normalized) > len(original_normalized) * 1.3  # New code is 30%+ larger
)

if is_wrapping:
    # For wrapping: just verify wrapped code was added
    if new_code_normalized not in written_normalized:
        verification_errors.append("Wrapped code not found")
else:
    # For replacement: verify original removed AND new added
    if new_code_normalized not in written_normalized:
        verification_errors.append("New code not found")
    
    if original_normalized not in new_code_normalized:
        if original_normalized in written_normalized:
            verification_errors.append("Original code still present")
```

## Changes Required

### File: `pipeline/handlers.py`
**Location:** Lines 453-462 (in `_handle_modify_file` method)

**Replace:**
```python
# 3. Verify the change actually occurred
# Check if the exact original code block was replaced
# Note: If new_code contains original (like wrapping in try/except), 
# we should check that the standalone original is gone
if original not in new_code:  # Only check if original was completely replaced
    if original in written_content:
        verification_errors.append("Original code still present - change may not have applied")
        verification_passed = False

# Check if new code is present (with some flexibility for whitespace)
new_code_stripped = new_code.strip()
```

**With:**
```python
# 3. Verify the change actually occurred - FIXED LOGIC
# Normalize whitespace for comparison
original_normalized = ' '.join(original.split())
new_code_normalized = ' '.join(new_code.split())
written_normalized = ' '.join(written_content.split())

# Detect if this is a wrapping operation (code is being wrapped, not replaced)
is_wrapping = (
    original_normalized in new_code_normalized and  # Original is inside new code
    len(new_code_normalized) > len(original_normalized) * 1.3  # New code is significantly larger (30%+)
)

if is_wrapping:
    # For wrapping operations (try/except, if/else, etc.)
    # Just verify the new wrapped code was added
    if new_code_normalized not in written_normalized:
        verification_errors.append("Wrapped code not found in file - wrapping operation may have failed")
        verification_passed = False
else:
    # For replacement operations
    # Verify original was removed AND new was added
    if new_code_normalized not in written_normalized:
        verification_errors.append("New code not found in file - replacement may have failed")
        verification_passed = False
    
    # Only check if original was completely replaced (not just wrapped)
    if original_normalized not in new_code_normalized:
        if original_normalized in written_normalized:
            verification_errors.append("Original code still present - replacement incomplete")
            verification_passed = False

# Check if new code is present (with some flexibility for whitespace)
new_code_stripped = new_code.strip()
```

## Testing

### Test Case 1: Wrapping (should PASS)
```python
original = "curses.cbreak()"
new = """try:
    curses.cbreak()
except curses.error:
    pass"""
# Result: PASS - wrapping detected, no "original still present" error
```

### Test Case 2: Replacement (should PASS)
```python
original = "curses.cbreak()"
new = "curses.nocbreak()"
# Result: PASS - replacement detected, original removed
```

### Test Case 3: Failed Replacement (should FAIL)
```python
original = "curses.cbreak()"
new = "curses.nocbreak()"
written = "curses.cbreak()"  # Original still there!
# Result: FAIL - correctly detects failure
```

## Expected Outcomes

After this fix:
1. ✅ AI can wrap code in try/except without triggering false failures
2. ✅ No more nested try blocks
3. ✅ No more infinite loops
4. ✅ Proper detection of actual replacement failures
5. ✅ System can make iterative progress

## Implementation Steps

1. Stop the current debugging run (Ctrl+C)
2. Apply the patch to `pipeline/handlers.py`
3. Commit and push changes
4. Manually fix the nested try blocks in `pipeline_ui.py`
5. Re-run the debugging system
6. Verify no more infinite loops

## Priority
**CRITICAL** - This is the root cause of the infinite loop issue.