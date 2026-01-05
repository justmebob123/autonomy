# Bidirectional IPC Implementation Plan

## Overview

This document outlines the complete implementation plan for bidirectional IPC document updates across all phases.

---

## Phase 1: Core Infrastructure (COMPLETE)

### 1.1 Document Updater Utility ✅
- Created `pipeline/document_updater.py`
- Provides 6 key methods:
  1. `mark_task_complete()` - Mark tasks done in TERTIARY_OBJECTIVES
  2. `remove_resolved_issue()` - Remove fixed issues from SECONDARY_OBJECTIVES
  3. `add_new_issue()` - Add new issues to SECONDARY_OBJECTIVES
  4. `update_actual_architecture()` - Update ARCHITECTURE.md ACTUAL section
  5. `mark_feature_complete()` - Mark features done in PRIMARY_OBJECTIVES
  6. `update_architectural_drift()` - Update drift reduction in ARCHITECTURE.md

---

## Phase 2: Critical Write Operations (IMMEDIATE PRIORITY)

### 2.1 Coding Phase - Task Completion Updates

**File:** `pipeline/phases/coding.py`

**When:** After successfully completing a task

**What to Update:**
1. Mark task complete in TERTIARY_OBJECTIVES.md
2. Mark feature complete in PRIMARY_OBJECTIVES.md (if feature is done)
3. Update ARCHITECTURE.md ACTUAL (if new component added)

**Implementation:**
```python
# In coding phase after task completion
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# Mark task complete in TERTIARY_OBJECTIVES
if task.target_file:
    task_id = f"{task.target_file}::{task.description[:30]}"
    doc_updater.mark_task_complete(
        'TERTIARY_OBJECTIVES.md',
        task_id,
        'Coding',
        f"Implemented {task.description}"
    )

# If this completes a feature, mark in PRIMARY_OBJECTIVES
if task.metadata and 'feature_name' in task.metadata:
    doc_updater.mark_feature_complete(
        task.metadata['feature_name'],
        'Coding',
        f"All tasks for {task.metadata['feature_name']} completed"
    )

# If new component added, update ARCHITECTURE
if task.metadata and 'new_component' in task.metadata:
    doc_updater.update_actual_architecture(
        task.target_file,
        'IMPLEMENTED',
        'Coding'
    )
```

---

### 2.2 Debugging Phase - Issue Resolution Updates

**File:** `pipeline/phases/debugging.py`

**When:** After successfully fixing an issue

**What to Update:**
1. Remove fixed issue from SECONDARY_OBJECTIVES.md
2. Remove specific fix from TERTIARY_OBJECTIVES.md
3. Add new issues if discovered during debugging

**Implementation:**
```python
# In debugging phase after successful fix
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# Remove fixed issue from SECONDARY_OBJECTIVES
issue_desc = issue.get('description', '')
doc_updater.remove_resolved_issue(
    'SECONDARY_OBJECTIVES.md',
    issue_desc,
    'Debugging',
    f"Fixed in {filepath}"
)

# Remove from TERTIARY_OBJECTIVES
if filepath:
    task_id = f"{filepath}::{issue.get('type', 'unknown')}"
    doc_updater.mark_task_complete(
        'TERTIARY_OBJECTIVES.md',
        task_id,
        'Debugging',
        f"Fixed {issue.get('type', 'issue')}"
    )

# If new issues discovered, add them
if new_issues_found:
    for new_issue in new_issues_found:
        doc_updater.add_new_issue(
            'SECONDARY_OBJECTIVES.md',
            'Reported Failures',
            new_issue['description'],
            'Debugging',
            new_issue.get('severity', 'Error')
        )
```

---

### 2.3 Refactoring Phase - Architectural Updates

**File:** `pipeline/phases/refactoring.py`

**When:** After completing a refactoring task

**What to Update:**
1. Remove completed task from SECONDARY_OBJECTIVES.md
2. Remove specific refactoring from TERTIARY_OBJECTIVES.md
3. Update ARCHITECTURE.md ACTUAL section
4. Update ARCHITECTURE.md drift reduction

**Implementation:**
```python
# In refactoring phase after task completion
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# Remove from SECONDARY_OBJECTIVES
if task.issue_type == RefactoringIssueType.COMPLEXITY:
    doc_updater.remove_resolved_issue(
        'SECONDARY_OBJECTIVES.md',
        f"Refactor {task.target_files[0]}",
        'Refactoring',
        f"Reduced complexity from {task.analysis_data.get('old_complexity')} to {task.analysis_data.get('new_complexity')}"
    )

# Remove from TERTIARY_OBJECTIVES
if task.target_files:
    task_id = f"{task.target_files[0]}::{task.title}"
    doc_updater.mark_task_complete(
        'TERTIARY_OBJECTIVES.md',
        task_id,
        'Refactoring',
        f"Completed {task.issue_type.value} refactoring"
    )

# Update ACTUAL architecture
for file in task.target_files:
    doc_updater.update_actual_architecture(
        file,
        'REFACTORED',
        'Refactoring'
    )

# Update drift reduction
doc_updater.update_architectural_drift(
    f"Aligned {task.target_files[0]} with intended design",
    'Refactoring'
)
```

---

## Phase 3: Important Write Operations (HIGH PRIORITY)

### 3.1 QA Phase - Issue Reporting Updates

**File:** `pipeline/phases/qa.py`

**When:** After finding issues or approving code

**What to Update:**
1. Add new failures to SECONDARY_OBJECTIVES.md
2. Add specific issues to TERTIARY_OBJECTIVES.md
3. Remove from SECONDARY_OBJECTIVES when approving previously failed code

**Implementation:**
```python
# In QA phase after finding issues
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# If issues found, add to SECONDARY_OBJECTIVES
if issues_found:
    for issue in issues_found:
        doc_updater.add_new_issue(
            'SECONDARY_OBJECTIVES.md',
            'Reported Failures',
            f"{issue['type']}: {issue['description']} in {filepath}",
            'QA',
            issue.get('severity', 'Error')
        )
        
        # Also add to TERTIARY_OBJECTIVES for specific tracking
        doc_updater.add_new_issue(
            'TERTIARY_OBJECTIVES.md',
            'Specific Fixes Needed',
            f"{filepath} (Line {issue.get('line_number', '?')}): {issue['description']}",
            'QA',
            issue['type']
        )

# If approving previously failed code, remove from SECONDARY_OBJECTIVES
if approved and was_previously_failed:
    doc_updater.remove_resolved_issue(
        'SECONDARY_OBJECTIVES.md',
        f"in {filepath}",
        'QA',
        "Code now passes all quality checks"
    )
```

---

### 3.2 Investigation Phase - Findings Updates

**File:** `pipeline/phases/investigation.py`

**When:** After completing investigation

**What to Update:**
1. Add architectural issues to SECONDARY_OBJECTIVES.md
2. Add specific findings to TERTIARY_OBJECTIVES.md

**Implementation:**
```python
# In investigation phase after analysis
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# Add architectural issues found
if architectural_issues:
    for issue in architectural_issues:
        doc_updater.add_new_issue(
            'SECONDARY_OBJECTIVES.md',
            'Architectural Changes Needed',
            issue['description'],
            'Investigation',
            issue.get('severity', 'Warning')
        )

# Add specific findings
if specific_findings:
    for finding in specific_findings:
        doc_updater.add_new_issue(
            'TERTIARY_OBJECTIVES.md',
            'Specific Fixes Needed',
            finding['description'],
            'Investigation',
            finding.get('type', 'Finding')
        )
```

---

### 3.3 Documentation Phase - Verification Updates

**File:** `pipeline/phases/documentation.py`

**When:** After updating documentation

**What to Update:**
1. Update ARCHITECTURE.md documentation section
2. Verify PRIMARY_OBJECTIVES features are documented

**Implementation:**
```python
# In documentation phase after updates
from pipeline.document_updater import DocumentUpdater

doc_updater = DocumentUpdater(self.project_dir, self.logger)

# Update ARCHITECTURE.md with documentation status
doc_updater.update_actual_architecture(
    'Documentation',
    'UPDATED',
    'Documentation'
)

# Mark features as documented in PRIMARY_OBJECTIVES
if documented_features:
    for feature in documented_features:
        # Could add a note that feature is documented
        pass
```

---

## Phase 4: Integration Points

### 4.1 Base Phase Integration

**File:** `pipeline/phases/base.py`

**Add to Base Class:**
```python
from pipeline.document_updater import DocumentUpdater

class BasePhase:
    def __init__(self, ...):
        # ... existing init ...
        self.doc_updater = DocumentUpdater(self.project_dir, self.logger)
```

This makes `self.doc_updater` available to all phases.

---

### 4.2 State Manager Integration

**File:** `pipeline/state/manager.py`

**Track Document Updates:**
```python
# Add to state tracking
state.document_updates = {
    'last_updated': timestamp,
    'updates_by_phase': {
        'coding': count,
        'debugging': count,
        'refactoring': count,
        ...
    }
}
```

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests

**File:** `tests/test_document_updater.py`

Test each method:
- mark_task_complete()
- remove_resolved_issue()
- add_new_issue()
- update_actual_architecture()
- mark_feature_complete()
- update_architectural_drift()

### 5.2 Integration Tests

**File:** `tests/test_bidirectional_ipc.py`

Test complete flows:
- Coding completes task → TERTIARY_OBJECTIVES updated
- Debugging fixes issue → SECONDARY_OBJECTIVES updated
- Refactoring changes structure → ARCHITECTURE.md updated
- QA finds issue → SECONDARY_OBJECTIVES updated

### 5.3 End-to-End Tests

Run full pipeline and verify:
- Documents stay synchronized
- Completed items are removed
- New issues are added
- Architecture reflects actual state

---

## Implementation Order

### Week 1: Core Infrastructure
1. ✅ Create DocumentUpdater utility
2. ✅ Add to base phase
3. ⏳ Write unit tests

### Week 2: Critical Phases
4. ⏳ Implement Coding phase updates
5. ⏳ Implement Debugging phase updates
6. ⏳ Implement Refactoring phase updates

### Week 3: Important Phases
7. ⏳ Implement QA phase updates
8. ⏳ Implement Investigation phase updates
9. ⏳ Implement Documentation phase updates

### Week 4: Testing & Refinement
10. ⏳ Integration testing
11. ⏳ End-to-end testing
12. ⏳ Documentation and examples

---

## Success Metrics

### Document Synchronization
- ✅ Completed tasks removed from TERTIARY_OBJECTIVES within 1 iteration
- ✅ Fixed issues removed from SECONDARY_OBJECTIVES within 1 iteration
- ✅ New issues added to SECONDARY_OBJECTIVES immediately
- ✅ ARCHITECTURE.md ACTUAL reflects current state within 1 iteration

### Phase Behavior
- ✅ Coding phase updates documents on task completion
- ✅ Debugging phase updates documents on issue resolution
- ✅ Refactoring phase updates documents on structural changes
- ✅ QA phase updates documents on issue discovery
- ✅ All phases log document updates

### System Health
- ✅ No stale entries in objectives documents
- ✅ Documents stay under 500 lines each
- ✅ Architectural drift decreases over time
- ✅ Document updates don't cause performance issues

---

## Rollout Plan

### Phase 1: Soft Launch (Testing)
- Enable document updates in dev environment
- Monitor for issues
- Collect feedback

### Phase 2: Gradual Rollout
- Enable for Coding phase first
- Then Debugging phase
- Then Refactoring phase
- Finally QA and Investigation phases

### Phase 3: Full Production
- All phases updating documents
- Monitoring and optimization
- Documentation and training

---

## Monitoring & Maintenance

### Logging
- Log every document update
- Track update frequency by phase
- Monitor document sizes

### Alerts
- Alert if document exceeds size limit
- Alert if update fails
- Alert if documents become stale

### Maintenance
- Weekly review of document health
- Monthly cleanup of old completed items
- Quarterly review of update patterns

---

## Next Steps

1. Add DocumentUpdater to base phase
2. Implement Coding phase updates
3. Implement Debugging phase updates
4. Implement Refactoring phase updates
5. Test and iterate