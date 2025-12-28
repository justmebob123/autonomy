# CRITICAL: Non-Atomic File Writes Risk Data Corruption

## Executive Summary

Found **51 non-atomic file write operations** across the codebase, including the **StateManager** which is critical for system operation. If the process crashes during a write, files will be corrupted.

## The Problem

### Current Implementation (Unsafe)
```python
def save(self, state: PipelineState):
    """Save state to disk"""
    state.updated = datetime.now().isoformat()
    try:
        self.state_file.write_text(
            json.dumps(state.to_dict(), indent=2)
        )
    except Exception as e:
        self.logger.error(f"Failed to save state: {e}")
        raise
```

**Risk**: If process crashes between opening file and completing write:
- File is left partially written
- JSON is malformed
- State cannot be recovered
- System cannot restart

### Atomic Write Pattern (Safe)
```python
def save(self, state: PipelineState):
    """Save state to disk atomically"""
    state.updated = datetime.now().isoformat()
    
    # Write to temporary file first
    temp_file = self.state_file.with_suffix('.tmp')
    try:
        temp_file.write_text(
            json.dumps(state.to_dict(), indent=2)
        )
        # Atomic rename (POSIX guarantees atomicity)
        temp_file.replace(self.state_file)
        self.logger.debug(f"Saved state to {self.state_file}")
    except Exception as e:
        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()
        self.logger.error(f"Failed to save state: {e}")
        raise
```

**Benefits**:
- Write completes fully or not at all
- Original file unchanged until write succeeds
- Atomic rename ensures consistency
- System can always recover

## Files at Risk

### Critical (State/Configuration)
1. **state/manager.py** - Pipeline state (CRITICAL)
2. **pattern_recognition.py** - Pattern data (2 writes)
3. **tool_registry.py** - Tool specifications (3 writes)
4. **role_registry.py** - Role specifications (2 writes)

### High (Code/Patches)
5. **handlers.py** - File modifications (6 writes)
6. **patch_manager.py** - Patch files (4 writes)
7. **line_fixer.py** - Code fixes (2 writes)

### Medium (Documentation/Logs)
8. **phases/debugging.py** - Debug logs (10 writes)
9. **phases/documentation.py** - Documentation (3 writes)
10. **phases/prompt_improvement.py** - Prompts (6 writes)
11. **phases/role_improvement.py** - Roles (10 writes)

## Impact Analysis

### StateManager Corruption
**Scenario**: Process crashes during state save
**Result**:
- State file is corrupted (malformed JSON)
- System cannot load state on restart
- All task progress is lost
- Must start from scratch

**Probability**: Low but non-zero (crashes, OOM, SIGKILL)
**Impact**: CRITICAL - Complete loss of work

### Tool/Role Registry Corruption
**Scenario**: Process crashes during tool/role save
**Result**:
- Tool/role specification corrupted
- System cannot load tools/roles
- Features become unavailable
- May require manual recovery

**Probability**: Low
**Impact**: HIGH - System functionality impaired

### Code File Corruption
**Scenario**: Process crashes during code modification
**Result**:
- Source file corrupted
- Code becomes invalid
- Build/test failures
- Manual recovery needed

**Probability**: Low
**Impact**: HIGH - Code integrity compromised

## Recommended Fixes

### Priority 1: StateManager (CRITICAL)
```python
def save(self, state: PipelineState):
    """Save state to disk atomically"""
    state.updated = datetime.now().isoformat()
    
    temp_file = self.state_file.with_suffix('.tmp')
    try:
        # Write to temp file
        temp_file.write_text(
            json.dumps(state.to_dict(), indent=2)
        )
        # Atomic rename
        temp_file.replace(self.state_file)
        self.logger.debug(f"Saved state to {self.state_file}")
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        self.logger.error(f"Failed to save state: {e}")
        raise
```

### Priority 2: Create Atomic Write Utility
```python
# pipeline/atomic_file.py
def atomic_write(filepath: Path, content: str):
    """Write file atomically using temp + rename"""
    temp_file = filepath.with_suffix('.tmp')
    try:
        temp_file.write_text(content)
        temp_file.replace(filepath)
    except Exception:
        if temp_file.exists():
            temp_file.unlink()
        raise
```

Then use everywhere:
```python
# Instead of:
file.write_text(content)

# Use:
atomic_write(file, content)
```

### Priority 3: Fix All Critical Files
1. StateManager (CRITICAL)
2. PatternRecognition (HIGH)
3. ToolRegistry (HIGH)
4. RoleRegistry (HIGH)
5. PatchManager (HIGH)

## Testing Strategy

### Test Atomic Writes
```python
def test_atomic_write_crash_safety():
    """Test that crashes don't corrupt files"""
    import signal
    import subprocess
    
    # Start process that writes file
    proc = subprocess.Popen(['python', 'write_test.py'])
    
    # Kill it mid-write
    time.sleep(0.1)
    proc.send_signal(signal.SIGKILL)
    
    # Check file integrity
    try:
        with open('test_file.json') as f:
            json.load(f)  # Should succeed
        print("✓ File not corrupted")
    except json.JSONDecodeError:
        print("✗ File corrupted!")
```

### Test State Recovery
```python
def test_state_recovery_after_crash():
    """Test that state can be recovered after crash"""
    # Save state
    state_manager.save(state)
    
    # Simulate crash by killing process
    # ... restart ...
    
    # Load state
    recovered_state = state_manager.load()
    
    # Verify integrity
    assert recovered_state.tasks == original_state.tasks
```

## Migration Plan

### Phase 1: Create Atomic Write Utility
1. Create `pipeline/atomic_file.py`
2. Implement `atomic_write()` function
3. Add tests for atomicity
4. Verify on all platforms (Linux, macOS, Windows)

### Phase 2: Fix StateManager
1. Update `state/manager.py` to use atomic writes
2. Test state save/load extensively
3. Verify no regressions
4. Deploy and monitor

### Phase 3: Fix Other Critical Files
1. Update PatternRecognition
2. Update ToolRegistry
3. Update RoleRegistry
4. Update PatchManager
5. Test each change

### Phase 4: Gradual Migration
1. Update remaining files as time permits
2. Prioritize by criticality
3. Test each change
4. Monitor for issues

## Monitoring

After fixes, monitor for:
1. **Corrupted files** - Should be zero
2. **Recovery failures** - Should be zero
3. **Temp file cleanup** - Verify no temp file buildup
4. **Performance impact** - Atomic writes are slightly slower

## Conclusion

Non-atomic file writes are a **CRITICAL** issue that can cause:
- Complete loss of state
- Corrupted tool/role specifications
- Corrupted source code
- System unable to restart

The fix is straightforward (temp + rename) but must be applied carefully to avoid regressions. **Priority 1** is fixing StateManager, as state corruption is the most severe failure mode.

**Recommendation**: Fix StateManager immediately, then gradually migrate other files.