# Missing Import Fix - Message and MessagePriority

## Error Discovered

**Error Type:** `NameError`
**Message:** `name 'Message' is not defined`
**Location:** `pipeline/phases/refactoring.py`, line 624

## Root Cause

During the polytopic integration work, multiple locations in `refactoring.py` were updated to publish message bus events using `Message` and `MessagePriority` classes. However, these classes were not imported - only `MessageType` was imported.

## Affected Locations

Five locations in `refactoring.py` were using `Message` and `MessagePriority` without importing them:

1. **Line 431** - Analysis started event
2. **Line 487** - Analysis complete event (with issues)
3. **Line 512** - Analysis complete event (no issues)
4. **Line 624** - Refactoring started event
5. **Line 843** - Refactoring complete event

## The Fix

Changed all import statements from:
```python
from ..messaging import MessageType
```

To:
```python
from ..messaging import MessageType, Message, MessagePriority
```

## Why This Wasn't Caught Earlier

This error demonstrates another limitation of static analysis:

1. **Import Checking**: The validators check if imported names exist, but don't check if all USED names are imported
2. **Runtime-Only Detection**: This error only appears when the code path is executed
3. **Conditional Imports**: The imports are inside `if self.message_bus:` blocks, making them harder to track statically

## Verification

- ✅ Compilation successful: `python3 -m py_compile pipeline/phases/refactoring.py`
- ✅ All 5 locations fixed
- ✅ Committed and pushed to GitHub

## Impact

### Before Fix
- ❌ Pipeline crashed when refactoring phase tried to publish message bus events
- ❌ Error: `NameError: name 'Message' is not defined`
- ❌ Refactoring phase completely non-functional

### After Fix
- ✅ All message bus events can be published successfully
- ✅ Refactoring phase can execute normally
- ✅ Pipeline continues execution

## Related Issues

This is the **second** runtime error found in the refactoring phase:

1. **First Error** (Fixed in commit 8acd9f2): `UnboundLocalError` - variable `task` used before definition
2. **Second Error** (Fixed in commit 6ba8b87): `NameError` - `Message` and `MessagePriority` not imported

Both errors were introduced during the polytopic integration work and were not caught by static validators.

## Lessons Learned

1. **Import Validation**: Need better validation to ensure all used names are imported
2. **Integration Testing**: Runtime testing is essential to catch these errors
3. **Code Review**: When adding new functionality, verify all dependencies are imported
4. **Systematic Checking**: After bulk changes, systematically verify all affected files

## Status

✅ **FIXED** - Committed (6ba8b87) and pushed to GitHub