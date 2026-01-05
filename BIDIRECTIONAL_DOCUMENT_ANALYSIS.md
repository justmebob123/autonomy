# Bidirectional Document Analysis - Read/Write Flow

## Overview

Analyzing ALL phases to understand:
1. Which documents each phase READS
2. Which documents each phase WRITES
3. What's missing in the bidirectional flow

---

## Document Inventory

### Strategic Documents (Planning Phase Maintains)
1. **MASTER_PLAN.md** - Overall project vision and roadmap
2. **PRIMARY_OBJECTIVES.md** - Core features and requirements
3. **SECONDARY_OBJECTIVES.md** - Architectural changes and quality needs
4. **TERTIARY_OBJECTIVES.md** - Specific implementation details
5. **ARCHITECTURE.md** - INTENDED vs ACTUAL design

### IPC Documents (Phase-Specific)
6. **PLANNING_READ.md** / **PLANNING_WRITE.md**
7. **DEVELOPER_READ.md** / **DEVELOPER_WRITE.md** (Coding)
8. **QA_READ.md** / **QA_WRITE.md**
9. **DEBUG_READ.md** / **DEBUG_WRITE.md**
10. **REFACTORING_READ.md** / **REFACTORING_WRITE.md**
11. **INVESTIGATION_READ.md** / **INVESTIGATION_WRITE.md**
12. **DOCUMENTATION_READ.md** / **DOCUMENTATION_WRITE.md**

---

## Phase-by-Phase Analysis

### 1. Planning Phase

**READS:**
- MASTER_PLAN.md ✅
- Existing ARCHITECTURE.md ✅
- QA_WRITE.md (for failures) ✅
- DEBUG_WRITE.md (for failures) ✅
- DEVELOPER_WRITE.md (for completion status) ✅

**WRITES:**
- PRIMARY_OBJECTIVES.md ✅
- SECONDARY_OBJECTIVES.md ✅
- TERTIARY_OBJECTIVES.md ✅
- ARCHITECTURE.md ✅
- PLANNING_WRITE.md ✅

**MISSING:**
- ❌ Should READ completed tasks to REMOVE them from TERTIARY_OBJECTIVES
- ❌ Should READ resolved issues to REMOVE them from SECONDARY_OBJECTIVES
- ❌ Should UPDATE ARCHITECTURE.md when actual design changes

---

### 2. Coding Phase

**READS:**
- PRIMARY_OBJECTIVES.md ✅ (just added)
- TERTIARY_OBJECTIVES.md ✅ (just added)
- DEVELOPER_READ.md ✅
- Task from state ✅

**WRITES:**
- DEVELOPER_WRITE.md ✅
- Code files ✅

**MISSING:**
- ❌ Should WRITE to TERTIARY_OBJECTIVES when task is completed (mark as done)
- ❌ Should WRITE to PRIMARY_OBJECTIVES when feature is completed
- ❌ Should UPDATE ARCHITECTURE.md when implementing new components

---

### 3. QA Phase

**READS:**
- SECONDARY_OBJECTIVES.md ✅ (just added)
- TERTIARY_OBJECTIVES.md ✅ (just added)
- QA_READ.md ✅
- Code files ✅

**WRITES:**
- QA_WRITE.md ✅
- Creates tasks with issues ✅

**MISSING:**
- ❌ Should WRITE to SECONDARY_OBJECTIVES when finding new failures
- ❌ Should REMOVE from SECONDARY_OBJECTIVES when issues are resolved
- ❌ Should UPDATE TERTIARY_OBJECTIVES with specific issues found

---

### 4. Debugging Phase

**READS:**
- SECONDARY_OBJECTIVES.md ✅ (just added)
- TERTIARY_OBJECTIVES.md ✅ (just added)
- DEBUG_READ.md ✅
- Issue from task ✅

**WRITES:**
- DEBUG_WRITE.md ✅
- Fixed code files ✅

**MISSING:**
- ❌ Should REMOVE from SECONDARY_OBJECTIVES when issue is fixed
- ❌ Should REMOVE from TERTIARY_OBJECTIVES when specific fix is completed
- ❌ Should WRITE to SECONDARY_OBJECTIVES if new issues discovered

---

### 5. Refactoring Phase

**READS:**
- PRIMARY_OBJECTIVES.md ✅
- SECONDARY_OBJECTIVES.md ✅
- TERTIARY_OBJECTIVES.md ✅
- ARCHITECTURE.md ✅
- REFACTORING_READ.md ✅

**WRITES:**
- REFACTORING_WRITE.md ✅
- Refactored code files ✅

**MISSING:**
- ❌ Should REMOVE from SECONDARY_OBJECTIVES when architectural change is done
- ❌ Should REMOVE from TERTIARY_OBJECTIVES when refactoring task is done
- ❌ Should UPDATE ARCHITECTURE.md actual design when refactoring changes structure
- ❌ Should REDUCE architectural drift in ARCHITECTURE.md

---

### 6. Investigation Phase

**READS:**
- PRIMARY_OBJECTIVES.md ✅
- SECONDARY_OBJECTIVES.md ✅
- INVESTIGATION_READ.md ✅

**WRITES:**
- INVESTIGATION_WRITE.md ✅
- Analysis reports ✅

**MISSING:**
- ❌ Should WRITE to SECONDARY_OBJECTIVES when finding architectural issues
- ❌ Should WRITE to TERTIARY_OBJECTIVES with specific investigation findings

---

### 7. Documentation Phase

**READS:**
- PRIMARY_OBJECTIVES.md ✅
- SECONDARY_OBJECTIVES.md ✅
- ARCHITECTURE.md ✅
- DOCUMENTATION_READ.md ✅

**WRITES:**
- DOCUMENTATION_WRITE.md ✅
- README.md ✅
- Other docs ✅

**MISSING:**
- ❌ Should UPDATE ARCHITECTURE.md documentation section
- ❌ Should VERIFY PRIMARY_OBJECTIVES are documented

---

## Critical Missing Flows

### 1. Task Completion → Remove from TERTIARY_OBJECTIVES
**Problem:** When Coding/Debugging/Refactoring completes a task, it's never removed from TERTIARY_OBJECTIVES
**Solution:** Each phase should mark items as [DONE] or remove them

### 2. Issue Resolution → Remove from SECONDARY_OBJECTIVES
**Problem:** When Debugging fixes an issue, it stays in SECONDARY_OBJECTIVES forever
**Solution:** Debugging phase should remove resolved failures

### 3. Architectural Changes → Update ARCHITECTURE.md ACTUAL
**Problem:** When Refactoring changes structure, ARCHITECTURE.md ACTUAL section is never updated
**Solution:** Refactoring phase should update ACTUAL design section

### 4. New Issues → Add to SECONDARY_OBJECTIVES
**Problem:** When QA/Debugging finds new issues, they're not added to SECONDARY_OBJECTIVES
**Solution:** QA and Debugging should append new failures

### 5. Feature Completion → Update PRIMARY_OBJECTIVES
**Problem:** When Coding completes a feature, PRIMARY_OBJECTIVES never shows progress
**Solution:** Coding phase should mark features as completed

### 6. Architectural Drift → Reduce in ARCHITECTURE.md
**Problem:** When Refactoring aligns code with design, drift section is never updated
**Solution:** Refactoring phase should update drift analysis

---

## Proposed Write Operations by Phase

### Planning Phase (Already Implemented)
- ✅ WRITE PRIMARY_OBJECTIVES.md (full rewrite)
- ✅ WRITE SECONDARY_OBJECTIVES.md (full rewrite)
- ✅ WRITE TERTIARY_OBJECTIVES.md (full rewrite)
- ✅ WRITE ARCHITECTURE.md (full rewrite)

### Coding Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to DEVELOPER_WRITE.md (already done)
- ❌ MARK DONE in TERTIARY_OBJECTIVES.md (specific task)
- ❌ MARK DONE in PRIMARY_OBJECTIVES.md (when feature complete)
- ❌ UPDATE ARCHITECTURE.md ACTUAL (when adding new components)

### QA Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to QA_WRITE.md (already done)
- ❌ APPEND to SECONDARY_OBJECTIVES.md (new failures found)
- ❌ APPEND to TERTIARY_OBJECTIVES.md (specific issues found)
- ❌ REMOVE from SECONDARY_OBJECTIVES.md (when approving previously failed code)

### Debugging Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to DEBUG_WRITE.md (already done)
- ❌ REMOVE from SECONDARY_OBJECTIVES.md (issue fixed)
- ❌ REMOVE from TERTIARY_OBJECTIVES.md (specific fix completed)
- ❌ APPEND to SECONDARY_OBJECTIVES.md (if new issues discovered)

### Refactoring Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to REFACTORING_WRITE.md (already done)
- ❌ REMOVE from SECONDARY_OBJECTIVES.md (architectural change done)
- ❌ REMOVE from TERTIARY_OBJECTIVES.md (refactoring task done)
- ❌ UPDATE ARCHITECTURE.md ACTUAL (structure changed)
- ❌ UPDATE ARCHITECTURE.md DRIFT (alignment improved)

### Investigation Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to INVESTIGATION_WRITE.md (already done)
- ❌ APPEND to SECONDARY_OBJECTIVES.md (architectural issues found)
- ❌ APPEND to TERTIARY_OBJECTIVES.md (specific findings)

### Documentation Phase (NEEDS IMPLEMENTATION)
- ❌ APPEND to DOCUMENTATION_WRITE.md (already done)
- ❌ UPDATE ARCHITECTURE.md (documentation section)
- ❌ VERIFY PRIMARY_OBJECTIVES (all features documented)

---

## Implementation Priority

### Phase 1: Critical Write Operations (Immediate)
1. **Coding Phase** - Mark tasks done in TERTIARY_OBJECTIVES
2. **Debugging Phase** - Remove fixed issues from SECONDARY_OBJECTIVES
3. **Refactoring Phase** - Update ARCHITECTURE.md ACTUAL section

### Phase 2: Important Write Operations (High Priority)
4. **QA Phase** - Add new failures to SECONDARY_OBJECTIVES
5. **Refactoring Phase** - Remove completed tasks from SECONDARY/TERTIARY
6. **Coding Phase** - Mark features done in PRIMARY_OBJECTIVES

### Phase 3: Enhancement Write Operations (Medium Priority)
7. **Investigation Phase** - Add findings to SECONDARY/TERTIARY
8. **Documentation Phase** - Update ARCHITECTURE.md documentation
9. **Refactoring Phase** - Update ARCHITECTURE.md drift analysis

---

## Document Update Patterns

### Pattern 1: Mark as Done (TERTIARY_OBJECTIVES)
```markdown
## Specific Code Changes Required

### 1. High Complexity Refactoring

#### 1. `services/resource_estimator.py::estimate_resources` (Line 145)
**Status:** ✅ COMPLETED (2026-01-05)
**Completed By:** Refactoring Phase
```

### Pattern 2: Remove Resolved Issue (SECONDARY_OBJECTIVES)
```markdown
## Reported Failures

### From QA Phase

- ~~Error: Missing import in debugging.py~~ ✅ FIXED (2026-01-05)
- Error: Task status mapping incorrect
```

### Pattern 3: Update ACTUAL Architecture (ARCHITECTURE.md)
```markdown
## ACTUAL Architecture

### Current Components

**services/** (15 files)
- resource_estimator.py - Resource estimation (REFACTORED 2026-01-05)
- config_loader.py - Configuration loading (INTEGRATED 2026-01-05)
```

### Pattern 4: Add New Issue (SECONDARY_OBJECTIVES)
```markdown
## Reported Failures

### From QA Phase (Added 2026-01-05)

- Error: New validation issue in user_service.py
- Failure: Missing error handling in api_client.py
```

---

## Tools Needed

### 1. Document Section Updater
```python
def update_document_section(
    doc_path: str,
    section_name: str,
    operation: str,  # 'append', 'remove', 'mark_done', 'update'
    content: str
) -> bool:
    """Update a specific section in a strategic document."""
    pass
```

### 2. Task Completion Marker
```python
def mark_task_complete(
    doc_path: str,
    task_identifier: str,
    phase_name: str
) -> bool:
    """Mark a specific task as completed in objectives document."""
    pass
```

### 3. Issue Remover
```python
def remove_resolved_issue(
    doc_path: str,
    issue_identifier: str,
    resolution_note: str
) -> bool:
    """Remove or mark as resolved an issue in objectives document."""
    pass
```

### 4. Architecture Updater
```python
def update_actual_architecture(
    component_name: str,
    change_description: str,
    phase_name: str
) -> bool:
    """Update ACTUAL architecture section with changes."""
    pass
```

---

## Next Steps

1. Create document update utility functions
2. Implement write operations in each phase
3. Add logging for all document updates
4. Test bidirectional flow
5. Verify documents stay synchronized with actual state

---

## Success Criteria

- ✅ Completed tasks removed from TERTIARY_OBJECTIVES
- ✅ Fixed issues removed from SECONDARY_OBJECTIVES
- ✅ Completed features marked in PRIMARY_OBJECTIVES
- ✅ ARCHITECTURE.md ACTUAL reflects current structure
- ✅ ARCHITECTURE.md DRIFT decreases as refactoring progresses
- ✅ New issues added to SECONDARY_OBJECTIVES by QA/Debugging
- ✅ Documents stay synchronized with codebase state