# Remaining 38 Errors - Fix Plan

## Summary
After validator enhancements, we have 38 remaining legitimate errors to fix.

## Error Categories

### 1. Old Analysis Scripts (22 errors)
**Files to Update/Remove:**
- `DEPTH_59_POLYTOPIC_ANALYSIS.py`
- `DEPTH_61_DEFAULTDICT_ANALYSIS.py`
- `ENHANCED_DEPTH_61_ANALYZER.py`
- `DEPTH_31_ANALYSIS.py`
- `IMPROVED_DEPTH_61_ANALYZER.py`
- `bin/analysis/*.py` (6 files)
- `scripts/analysis/*.py` (6 files)

**Issue:** Outdated API calls to `generate_report()` and `analyze_directory()`

**Solution:** 
- Remove old DEPTH_* analysis files (obsolete)
- Update bin/analysis/ and scripts/analysis/ to use current API

### 2. Pipeline Phase Message Issues (15 errors)
**Files:**
- `pipeline/phases/planning.py`
- `pipeline/phases/execution.py`
- `pipeline/phases/investigation.py`
- `pipeline/phases/refactoring.py`
- `pipeline/phases/debugging.py`

**Issue:** `Message.__init__()` calls missing required `content` argument

**Solution:** Add `content` parameter to all Message instantiations

### 3. Logging Issue (1 error)
**File:** `pipeline/messaging/message_bus.py:469`

**Issue:** `logger.error()` called with unexpected `exc_info` kwarg

**Solution:** Check if this is a false positive or fix the call

## Execution Plan

1. ✅ Analyze all 38 errors
2. ⬜ Fix pipeline phase Message issues (15 errors)
3. ⬜ Fix logging issue (1 error)
4. ⬜ Remove obsolete DEPTH_* files (5 errors)
5. ⬜ Update bin/analysis/ scripts (6 errors)
6. ⬜ Update scripts/analysis/ scripts (6 errors)
7. ⬜ Run validation to confirm 0 errors
8. ⬜ Commit and push fixes