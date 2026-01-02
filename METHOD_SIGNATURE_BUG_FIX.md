# 🚨 CRITICAL BUG FIX: Method Signature Mismatch

## Problem
Documentation phase (and 10 other phases) were crashing in an **infinite loop** with this error:

```
TypeError: BasePhase._write_status() takes 2 positional arguments but 3 were given
```

The system was stuck calling documentation phase repeatedly, failing every time, for 20+ iterations.

## Root Cause

When I added the IPC integration to all 14 phases, I made a mistake with the `_write_status()` method signature.

### What I Did Wrong:
```python
# WRONG - Called with 2 arguments (string + dict)
self._write_status("Starting documentation review", {
    "action": "start"
})
```

### What the Method Actually Expects:
```python
# Method signature in base.py
def _write_status(self, status: Dict[str, Any]):
    # Takes only 1 argument: a dictionary
```

### The Correct Way:
```python
# CORRECT - Called with 1 argument (dict with 'status' key)
self._write_status({
    "status": "Starting documentation review",
    "action": "start"
})
```

## Impact

**11 phases** were affected:
1. debugging.py (2 calls)
2. documentation.py (2 calls) ← **This caused the infinite loop**
3. investigation.py (2 calls)
4. project_planning.py (2 calls)
5. prompt_design.py (2 calls)
6. prompt_improvement.py (2 calls)
7. qa.py (3 calls)
8. role_design.py (2 calls)
9. role_improvement.py (2 calls)
10. tool_design.py (2 calls)
11. tool_evaluation.py (2 calls)

**Total**: 23 incorrect method calls fixed

## Why It Caused an Infinite Loop

1. Coordinator detected a documentation task
2. Routed to documentation phase
3. Documentation phase crashed immediately (wrong method signature)
4. Coordinator retried documentation phase
5. Crashed again
6. Repeat 20+ times
7. System stuck in loop

## The Fix

Changed all 23 calls from:
```python
self._write_status("message", {dict})  # 2 args - WRONG
```

To:
```python
self._write_status({"status": "message", ...})  # 1 dict arg - CORRECT
```

## Testing

After this fix:
```bash
cd autonomy
git pull origin main
python3 run.py -vv ../web/
```

**Expected behavior**:
- Documentation phase should run without crashing
- No more infinite loops
- All phases should write status correctly

## Commits

**Commit**: `6c0bfd3`
**Message**: "CRITICAL FIX: Fix _write_status() method signature in all phases"
**Files Modified**: 11 phase files
**Lines Changed**: +52, -23

**Status**: ✅ PUSHED TO GITHUB

## Lesson Learned

When adding new integration code to multiple files:
1. ✅ Check the method signature in the base class FIRST
2. ✅ Test at least ONE phase before copying to all phases
3. ✅ Don't assume the signature - verify it
4. ❌ Don't copy-paste code to 11 files without testing

This bug was introduced when I rushed to add IPC integration to all phases without carefully checking the base class method signature.