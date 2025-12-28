# CRITICAL BUG FIX: role_design.py Variable Order

## Bug Summary 🔴

**File**: `autonomy/pipeline/phases/role_design.py`  
**Lines**: 159-163  
**Severity**: CRITICAL  
**Type**: Variable used before assignment  
**Impact**: Causes `NameError`, breaks entire role design phase

---

## The Problem

**Current Code (WRONG)**:
```python
# Line 150-159: Check for loops and track tool calls
if self.check_for_loops():
    self.logger.warning("  Loop detected in role design phase")
    return PhaseResult(
        success=False,
        phase=self.phase_name,
        message="Loop detected - stopping to prevent infinite cycle"
    )

# Track tool calls for loop detection
self.track_tool_calls(tool_calls, results)  # ❌ ERROR: 'results' not defined yet!

# Line 161-163: Process tool calls
from ..handlers import ToolCallHandler
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
results = handler.process_tool_calls(tool_calls)  # ✅ 'results' defined here
```

**Error**:
```
NameError: name 'results' is not defined
```

---

## The Fix

**Corrected Code**:
```python
# Line 150-157: Check for loops
if self.check_for_loops():
    self.logger.warning("  Loop detected in role design phase")
    return PhaseResult(
        success=False,
        phase=self.phase_name,
        message="Loop detected - stopping to prevent infinite cycle"
    )

# Line 159-161: Process tool calls FIRST
from ..handlers import ToolCallHandler
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
results = handler.process_tool_calls(tool_calls)

# Line 163: THEN track tool calls
self.track_tool_calls(tool_calls, results)
```

---

## Root Cause

Lines were likely reordered during editing/refactoring, causing the tracking call to be placed before the processing call.

---

## Impact Assessment

### Before Fix:
- ❌ Role design phase completely broken
- ❌ Cannot create specialist roles
- ❌ Multi-agent collaboration disabled
- ❌ Runtime error on every execution

### After Fix:
- ✅ Role design phase works correctly
- ✅ Specialist roles can be created
- ✅ Multi-agent collaboration enabled
- ✅ No runtime errors

---

## Testing Required

### Unit Tests:
1. Test role design with valid role description
2. Test role design with invalid inputs
3. Test loop detection works correctly
4. Test tool call tracking works correctly

### Integration Tests:
1. Test end-to-end role creation
2. Test role registration
3. Test specialist instantiation
4. Test multi-agent collaboration

---

## Implementation Plan

1. **Backup Current File**
   ```bash
   cp autonomy/pipeline/phases/role_design.py autonomy/pipeline/phases/role_design.py.backup
   ```

2. **Apply Fix**
   - Move line 159 to after line 163
   - Verify correct order

3. **Test Fix**
   - Run unit tests
   - Run integration tests
   - Verify no regressions

4. **Commit Fix**
   ```bash
   git checkout -b fix/role-design-variable-order
   git add autonomy/pipeline/phases/role_design.py
   git commit -m "Fix critical bug: Variable used before assignment in role_design.py"
   git push origin fix/role-design-variable-order
   ```

5. **Create Pull Request**
   - Title: "Fix critical bug: Variable used before assignment in role_design.py"
   - Description: Link to this document
   - Labels: bug, critical, priority-high

---

## Verification Checklist

- [ ] Backup created
- [ ] Fix applied
- [ ] Code compiles without errors
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No regressions detected
- [ ] Commit created
- [ ] Branch pushed
- [ ] Pull request created
- [ ] Code review requested

---

## Related Files

- `autonomy/pipeline/phases/role_design.py` - File with bug
- `autonomy/pipeline/phases/prompt_design.py` - Similar pattern (no bug)
- `autonomy/pipeline/phases/tool_design.py` - Similar pattern (needs verification)

---

## Prevention

To prevent similar bugs in the future:

1. **Add Static Analysis**
   - Use pylint/flake8 to detect undefined variables
   - Add pre-commit hooks

2. **Add Unit Tests**
   - Test all execution paths
   - Verify variable definitions

3. **Code Review**
   - Require code review for all changes
   - Check variable usage order

4. **Documentation**
   - Document execution order requirements
   - Add comments for critical sections

---

**Created**: December 28, 2024  
**Priority**: CRITICAL 🔴  
**Status**: READY FOR FIX  
**Estimated Time**: 15 minutes