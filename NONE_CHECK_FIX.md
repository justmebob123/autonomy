# Critical Fix: Missing None Check in DebuggingPhase

## Problem

The system was crashing with:
```
AttributeError: 'NoneType' object has no attribute 'get'
```

This occurred at two locations in `pipeline/phases/debugging.py`:
- Line 748: `if intervention.get('requires_user_input'):`
- Line 1041: `if intervention.get('requires_user_input'):`

## Root Cause

The `_check_for_loops()` method returns `None` when no loops are detected:

```python
intervention = self._check_for_loops()
if intervention.get('requires_user_input'):  # ❌ CRASHES if intervention is None
```

When no loops are detected, `intervention` is `None`, and calling `.get()` on `None` causes an `AttributeError`.

## The Fix

Added None check before calling `.get()`:

```python
intervention = self._check_for_loops()
if intervention and intervention.get('requires_user_input'):  # ✅ Safe
```

**Locations Fixed:**
1. Line 748 - Main debugging loop
2. Line 1041 - Secondary debugging path

**Location Already Safe:**
- Line 1578 - Already inside `if intervention:` block, so no fix needed

## Impact

**Before Fix:**
- Debugging phase crashed immediately when no loops detected
- System stuck in infinite retry loop
- 211 tasks couldn't be processed

**After Fix:**
- Debugging phase handles both loop and no-loop scenarios correctly
- System can continue processing debugging tasks
- No crashes when intervention is None

## Verification

```bash
# Compile check
python3 -m py_compile pipeline/phases/debugging.py
# ✅ Success

# Pattern search
grep -n "if intervention.get" pipeline/phases/debugging.py
# 748: if intervention and intervention.get('requires_user_input'):  ✅
# 1041: if intervention and intervention.get('requires_user_input'): ✅
# 1578: if intervention.get('requires_user_input'):                 ✅ (inside if intervention: block)
```

## Related Fixes

This is the second critical bug fixed in `debugging.py` in this session:

1. **Missing init_loop_detection()** (commit 6d363ad)
   - Fixed: action_tracker not initialized
   
2. **Missing None check** (this commit)
   - Fixed: intervention.get() called on None

Both bugs prevented the debugging phase from functioning at all.

## Testing

To verify the fix works:

```bash
cd /home/ai/AI/autonomy
git pull origin main
pkill -f "python3 run.py"
python3 run.py -vv ../web/
```

**Expected Results:**
1. ✅ Debugging phase initializes without errors
2. ✅ No AttributeError when no loops detected
3. ✅ Proper handling of loop detection scenarios
4. ✅ System can process debugging tasks

## Lessons Learned

**Always check for None before calling methods:**
```python
# ❌ BAD - Can crash if value is None
if value.get('key'):
    ...

# ✅ GOOD - Safe even if value is None
if value and value.get('key'):
    ...
```

This is a common Python pattern that should be enforced in code reviews and static analysis.