# CRITICAL IPC DOCUMENT BUGS FOUND

## Date: 2026-01-05

## Bug 1: ARCHITECTURE.md Growing Unbounded (3451 lines)

**Problem:**
- Planning phase appends new analysis every iteration
- File grows from hundreds to thousands of lines
- Should represent CURRENT state, not historical accumulation

**Root Cause:**
```python
# Line 1030-1033 in pipeline/phases/planning.py
if len(existing_content) < 500:
    # Create new
else:
    # APPEND to existing - THIS IS THE BUG
    content += f"\n\n## Analysis Update - {timestamp}\n\n"
```

**Fix Applied:**
- Always create fresh content
- ARCHITECTURE.md represents CURRENT state only
- No historical accumulation

**Commit:** Next commit

---

## Bug 2: PRIMARY_OBJECTIVES.md Never Populated

**Problem:**
- Document created with placeholder comments
- Says "automatically updated by Planning phase"
- Planning phase has NO CODE to update it
- Remains empty forever

**Root Cause:**
- `document_ipc.py` creates template
- `ObjectiveManager` can READ but not WRITE
- Planning phase never calls any update method
- No code path exists to populate this document

**Expected Content:**
```markdown
## Core Features
- Feature 1: Description
- Feature 2: Description

## Functional Requirements
- Requirement 1: Details
- Requirement 2: Details
```

**Actual Content:**
```markdown
## Core Features
<!-- List of core features to implement -->
<!-- Planning phase will populate this based on MASTER_PLAN analysis -->
```

**Fix Needed:**
- Planning phase must parse MASTER_PLAN.md
- Extract objectives and requirements
- Write to PRIMARY_OBJECTIVES.md
- Update on each planning iteration

---

## Bug 3: SECONDARY_OBJECTIVES.md Never Populated

**Problem:**
- Same as PRIMARY_OBJECTIVES.md
- Created with placeholders
- Never populated by any phase
- Says "updated by Planning phase based on analysis and QA feedback"
- No code exists to do this

**Expected Content:**
```markdown
## Architectural Changes Needed
- Refactor X for better Y
- Split Z into separate modules

## Testing Requirements
- Add unit tests for A
- Add integration tests for B

## Reported Failures
- Issue #123: Description
- Issue #456: Description
```

**Actual Content:**
```markdown
## Architectural Changes Needed
<!-- Changes to architecture based on analysis -->
<!-- Planning phase adds findings from complexity and integration analysis -->
```

**Fix Needed:**
- Planning phase must aggregate:
  - Complexity analysis results → Architectural Changes
  - QA_WRITE.md issues → Reported Failures
  - Missing test coverage → Testing Requirements
  - Integration gaps → Integration Issues
- Write structured content to SECONDARY_OBJECTIVES.md

---

## Bug 4: Documents Not Used Correctly

**Problem:**
- Documents exist but phases don't read them properly
- Phases use direct analysis instead of reading objectives
- IPC system bypassed in favor of direct tool calls

**Evidence:**
```bash
ai@Saturn:/home/ai/AI/web$ cat PRIMARY_OBJECTIVES.md 
# Primary Objectives
<!-- Empty placeholders -->

ai@Saturn:/home/ai/AI/web$ cat SECONDARY_OBJECTIVES.md
# Secondary Objectives  
<!-- Empty placeholders -->

ai@Saturn:/home/ai/AI/web$ cat ARCHITECTURE.md | wc -l
3451  # MASSIVE FILE
```

**Root Cause:**
- IPC system designed but not fully implemented
- Phases have analysis tools but don't write to IPC docs
- Coordinator doesn't enforce IPC usage
- Documents become stale or grow unbounded

---

## Impact

**Current State:**
- ARCHITECTURE.md: 3451 lines (should be ~100-200)
- PRIMARY_OBJECTIVES.md: Empty placeholders
- SECONDARY_OBJECTIVES.md: Empty placeholders
- System ignores IPC documents
- Phases do redundant analysis

**Expected State:**
- ARCHITECTURE.md: ~100-200 lines, CURRENT state only
- PRIMARY_OBJECTIVES.md: Populated with actual objectives
- SECONDARY_OBJECTIVES.md: Populated with actual requirements
- Phases read and update IPC documents
- No redundant analysis

---

## Fix Strategy

### 1. ARCHITECTURE.md (FIXED)
- ✅ Remove append logic
- ✅ Always create fresh content
- ✅ Represent CURRENT state only

### 2. PRIMARY_OBJECTIVES.md (TODO)
- Parse MASTER_PLAN.md in Planning phase
- Extract core features and requirements
- Write structured content
- Update on each planning iteration

### 3. SECONDARY_OBJECTIVES.md (TODO)
- Aggregate analysis results in Planning phase
- Read QA_WRITE.md for failures
- Extract architectural changes from complexity analysis
- Write structured content

### 4. Enforce IPC Usage (TODO)
- Phases must read objectives before planning
- Phases must write results to IPC docs
- Coordinator validates IPC document freshness
- Add logging for IPC document reads/writes

---

## Files to Modify

1. ✅ `pipeline/phases/planning.py` - Fix ARCHITECTURE.md growth
2. TODO: `pipeline/phases/planning.py` - Add PRIMARY_OBJECTIVES update
3. TODO: `pipeline/phases/planning.py` - Add SECONDARY_OBJECTIVES update
4. TODO: `pipeline/objective_manager.py` - Add write methods
5. TODO: `pipeline/coordinator.py` - Enforce IPC usage

---

## Testing

After fixes:
1. Delete existing IPC documents
2. Run planning phase
3. Verify ARCHITECTURE.md stays ~100-200 lines
4. Verify PRIMARY_OBJECTIVES.md has actual content
5. Verify SECONDARY_OBJECTIVES.md has actual content
6. Run multiple iterations - verify no unbounded growth