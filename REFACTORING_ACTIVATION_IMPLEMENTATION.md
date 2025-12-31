# Refactoring Phase Activation - Implementation Plan

**Date**: December 31, 2024  
**Priority**: HIGH  
**Estimated Time**: 2-3 hours  

---

## Problem Statement

The refactoring phase is fully implemented but never activated because:
1. Tactical decision tree (most common path) doesn't route to it
2. Dimensional profile scores too low in polytopic selection
3. No IPC integration (no input from other phases)
4. No phase hint system

---

## Implementation Phases

### Phase 1: Quick Fixes (30 minutes)
**Goal**: Make refactoring activate immediately

#### Fix 1.1: Add Refactoring Trigger to Tactical Decision Tree
**File**: `pipeline/coordinator.py`  
**Location**: Line ~1636 (in `_determine_next_action_tactical`)  
**Changes**:
- Add `_should_trigger_refactoring()` method
- Call it before routing to coding phase
- Trigger based on:
  - Every 20 iterations
  - 15+ files created in last 10 iterations
  - Duplicate patterns detected

#### Fix 1.2: Improve Dimensional Profile
**File**: `pipeline/coordinator.py`  
**Location**: Line ~345 (in `_initialize_polytopic_structure`)  
**Changes**:
- Increase functional: 0.5 → 0.8
- Increase temporal: 0.5 → 0.7
- Increase error: 0.5 → 0.6
- Increase integration: 0.8 → 0.9

### Phase 2: IPC Integration (45 minutes)
**Goal**: Enable phases to request refactoring

#### Fix 2.1: QA Phase Integration
**File**: `pipeline/phases/qa.py`  
**Changes**:
- Detect duplicate implementations
- Write to REFACTORING_READ.md
- Set next_phase hint

#### Fix 2.2: Coding Phase Integration
**File**: `pipeline/phases/coding.py`  
**Changes**:
- Track files created per iteration
- Write to REFACTORING_READ.md after 10+ files
- Set next_phase hint

#### Fix 2.3: Investigation Phase Integration
**File**: `pipeline/phases/investigation.py`  
**Changes**:
- Detect integration conflicts
- Write to REFACTORING_READ.md
- Set next_phase hint

### Phase 3: Advanced Features (45 minutes)
**Goal**: Intelligent refactoring triggers

#### Fix 3.1: Duplicate Pattern Detection
**File**: `pipeline/coordinator.py`  
**New Method**: `_detect_duplicate_patterns()`  
**Logic**:
- Check for files with similar names
- Check for files in same directory
- Use simple heuristics

#### Fix 3.2: File Creation Tracking
**File**: `pipeline/coordinator.py`  
**New Method**: `_count_recent_files()`  
**Logic**:
- Track files created in last N iterations
- Store in state for persistence

#### Fix 3.3: Data Dimension Scoring
**File**: `pipeline/coordinator.py`  
**Location**: `_calculate_phase_priority()`  
**Changes**:
- Add data-intensive situation detection
- Add many-files situation detection
- Use data dimension in scoring

---

## Implementation Order

### Step 1: Add Refactoring Trigger Method
```python
def _should_trigger_refactoring(self, state: PipelineState, pending_tasks: List[TaskState]) -> bool:
    """Check if refactoring should be triggered"""
    
    # Trigger every 20 iterations
    iteration_count = len(getattr(state, 'phase_history', []))
    if iteration_count > 0 and iteration_count % 20 == 0:
        self.logger.info("  🔄 Triggering refactoring (periodic check)")
        return True
    
    # Trigger if many files created recently
    recent_files = self._count_recent_files(state, iterations=10)
    if recent_files > 15:
        self.logger.info(f"  🔄 Triggering refactoring ({recent_files} files created recently)")
        return True
    
    # Trigger if duplicate patterns detected
    if self._detect_duplicate_patterns(state):
        self.logger.info("  🔄 Triggering refactoring (duplicate patterns detected)")
        return True
    
    return False
```

### Step 2: Add File Tracking Method
```python
def _count_recent_files(self, state: PipelineState, iterations: int = 10) -> int:
    """Count files created in last N iterations"""
    
    if not hasattr(state, 'phase_history'):
        return 0
    
    # Get last N phases
    recent_phases = state.phase_history[-iterations:] if len(state.phase_history) > iterations else state.phase_history
    
    # Count files created in coding phase runs
    files_created = 0
    for phase_name in recent_phases:
        if phase_name == 'coding' and phase_name in state.phases:
            phase_state = state.phases[phase_name]
            # Count successful runs
            files_created += len([r for r in phase_state.runs if r.success and r.files_created])
    
    return files_created
```

### Step 3: Add Duplicate Detection Method
```python
def _detect_duplicate_patterns(self, state: PipelineState) -> bool:
    """Detect potential duplicate implementations"""
    
    # Simple heuristic: check for files with similar names
    files = {}
    for task in state.tasks.values():
        if task.target_file and task.status == TaskStatus.COMPLETED:
            # Extract base name without extension
            base_name = Path(task.target_file).stem
            
            # Group by base name
            if base_name not in files:
                files[base_name] = []
            files[base_name].append(task.target_file)
    
    # Check for duplicates
    for base_name, file_list in files.items():
        if len(file_list) > 1:
            # Multiple files with same base name
            self.logger.debug(f"  Potential duplicates: {file_list}")
            return True
    
    return False
```

### Step 4: Update Tactical Decision Tree
```python
# In _determine_next_action_tactical(), after line 1636:

# 3. If we have pending tasks, route to appropriate phase
if pending:
    # Simple priority-based selection
    pending_sorted = sorted(pending, key=lambda t: t.priority)
    task = pending_sorted[0]
    
    # Skip tasks with empty target_file
    if not task.target_file or task.target_file.strip() == "":
        # ... existing code ...
    
    # Check if refactoring is needed BEFORE routing to coding
    if self._should_trigger_refactoring(state, pending):
        return {'phase': 'refactoring', 'reason': 'Refactoring needed before continuing development'}
    
    # Route documentation tasks
    if is_doc_task:
        # ... existing code ...
    
    # Regular code tasks go to coding phase
    return {'phase': 'coding', 'task': task, 'reason': f'{len(pending)} tasks in progress'}
```

### Step 5: Update Dimensional Profile
```python
# In _initialize_polytopic_structure(), line ~345:

'refactoring': {
    'type': 'refactoring',
    'dimensions': {
        'temporal': 0.7,      # Increased from 0.5
        'functional': 0.8,    # Increased from 0.5
        'error': 0.6,         # Increased from 0.5
        'context': 0.9,       # Keep high
        'integration': 0.9,   # Increased from 0.8
        'data': 0.8           # Keep high
    }
}
```

### Step 6: Add IPC Integration to QA Phase
```python
# In qa.py, after duplicate detection:

# Check for duplicate implementations
if self._detect_duplicates(state):
    # Write to refactoring phase
    self.write_to_phase('refactoring',
        f"## Duplicate Implementations Detected\n\n"
        f"QA phase detected potential duplicate implementations.\n"
        f"Recommend refactoring to consolidate code.\n\n"
        f"Files to analyze:\n"
        f"{self._format_duplicate_list()}\n"
    )
    
    # Suggest refactoring as next phase
    result.next_phase = 'refactoring'
```

### Step 7: Add IPC Integration to Coding Phase
```python
# In coding.py, after file creation:

# Track files created this iteration
if not hasattr(state, '_files_created_this_iteration'):
    state._files_created_this_iteration = 0

state._files_created_this_iteration += 1

# If many files created, suggest refactoring
if state._files_created_this_iteration >= 10:
    self.write_to_phase('refactoring',
        f"## Many Files Created\n\n"
        f"Coding phase created {state._files_created_this_iteration} files.\n"
        f"Recommend refactoring to improve organization.\n"
    )
    
    result.next_phase = 'refactoring'
    state._files_created_this_iteration = 0  # Reset counter
```

---

## Testing Plan

### Test 1: Periodic Trigger
**Steps**:
1. Run pipeline for 20 iterations
2. Check phase_history for 'refactoring' at iteration 20

**Expected**:
- Refactoring phase activated at iteration 20
- REFACTORING_WRITE.md created
- Analysis performed

### Test 2: Many Files Trigger
**Steps**:
1. Create 16 files in 10 iterations
2. Check for refactoring activation

**Expected**:
- Refactoring phase activated after 16th file
- Files analyzed for duplicates
- Recommendations generated

### Test 3: Duplicate Detection
**Steps**:
1. Create 2 files with similar names (e.g., `utils.py`, `utils_v2.py`)
2. Run QA phase
3. Check for refactoring activation

**Expected**:
- Duplicate pattern detected
- Refactoring phase activated
- Duplicate analysis performed

### Test 4: IPC Integration
**Steps**:
1. Trigger QA duplicate detection
2. Check REFACTORING_READ.md for QA message
3. Check refactoring phase processes message

**Expected**:
- QA writes to REFACTORING_READ.md
- Refactoring reads message
- Refactoring performs requested analysis

---

## Success Criteria

✅ Refactoring phase activates every 20 iterations  
✅ Refactoring phase activates after 15+ files created  
✅ Refactoring phase activates on duplicate detection  
✅ QA phase writes to REFACTORING_READ.md  
✅ Coding phase writes to REFACTORING_READ.md  
✅ Refactoring phase reads and processes IPC messages  
✅ Dimensional profile scores competitively in polytopic selection  
✅ Phase hint system works (next_phase suggestions)  

---

## Rollback Plan

If issues occur:
1. Revert coordinator.py changes
2. Revert dimensional profile changes
3. Revert IPC integration changes
4. Test with original code

All changes are additive and can be safely reverted.

---

## Next Steps

1. Implement Phase 1 (Quick Fixes)
2. Test periodic trigger
3. Implement Phase 2 (IPC Integration)
4. Test IPC flow
5. Implement Phase 3 (Advanced Features)
6. Full integration testing
7. Document results

---

**End of Implementation Plan**