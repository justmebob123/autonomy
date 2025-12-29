# Phase 3: IPC Integration for Coding, QA, and Debugging Phases

## Overview
Integrate Document IPC system into the three main execution phases to enable proper inter-phase communication through documents.

## Implementation Strategy

### Common Pattern for All Phases
Each phase will follow this structure:

```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    """Execute phase with IPC integration"""
    
    # 1. INITIALIZE IPC (first run only)
    self.initialize_ipc_documents()
    
    # 2. READ OWN TASKS from {PHASE}_READ.md
    tasks = self.read_own_tasks()
    
    # 3. READ STRATEGIC DOCUMENTS for context
    strategic_docs = self.read_strategic_docs()
    
    # 4. READ OTHER PHASES' OUTPUTS for coordination
    other_outputs = self._read_relevant_phase_outputs()
    
    # 5. EXECUTE PHASE LOGIC (existing code)
    # ... existing execute logic ...
    
    # 6. WRITE OWN STATUS to {PHASE}_WRITE.md
    self.write_own_status(status_content)
    
    # 7. SEND MESSAGES to other phases' READ documents
    self._send_phase_messages(result)
    
    # 8. RETURN RESULT
    return result
```

## Phase-Specific Implementations

### 1. Coding Phase (`pipeline/phases/coding.py`)

#### Changes Needed:
1. **Add IPC initialization** at start of execute()
2. **Add method `_read_relevant_phase_outputs()`**:
   - Read PLANNING_WRITE.md for task assignments
   - Read QA_WRITE.md for feedback on previous code
   - Read DEBUG_WRITE.md for bug fixes needed

3. **Add method `_send_phase_messages()`**:
   - Send to QA_READ.md when code is ready for review
   - Include: files modified, changes made, testing notes

4. **Add method `_format_status_for_write()`**:
   - Format current task status
   - List files created/modified
   - Note any issues encountered

#### Integration Points:
```python
# At start of execute():
self.initialize_ipc_documents()
tasks_from_doc = self.read_own_tasks()
strategic_docs = self.read_strategic_docs()
phase_outputs = self._read_relevant_phase_outputs()

# Before return:
status = self._format_status_for_write(task, files_created, files_modified)
self.write_own_status(status)
self._send_phase_messages(task, files_created, files_modified)
```

### 2. QA Phase (`pipeline/phases/qa.py`)

#### Changes Needed:
1. **Add IPC initialization** at start of execute()
2. **Add method `_read_relevant_phase_outputs()`**:
   - Read DEVELOPER_WRITE.md for completed code
   - Read PLANNING_WRITE.md for quality criteria
   - Read DEBUG_WRITE.md for known issues

3. **Add method `_send_phase_messages()`**:
   - Send to DEBUG_READ.md when bugs found
   - Send to DEVELOPER_READ.md for code improvements
   - Include: issue details, severity, file locations

4. **Add method `_format_status_for_write()`**:
   - Format review results
   - List issues found by severity
   - Note files reviewed and status

#### Integration Points:
```python
# At start of execute():
self.initialize_ipc_documents()
review_requests = self.read_own_tasks()
strategic_docs = self.read_strategic_docs()
phase_outputs = self._read_relevant_phase_outputs()

# Use strategic docs for quality criteria:
quality_criteria = strategic_docs.get('SECONDARY_OBJECTIVES', '')

# Before return:
status = self._format_status_for_write(filepath, issues_found)
self.write_own_status(status)
self._send_phase_messages(issues_found)
```

### 3. Debugging Phase (`pipeline/phases/debugging.py`)

#### Changes Needed:
1. **Add IPC initialization** at start of execute()
2. **Add method `_read_relevant_phase_outputs()`**:
   - Read QA_WRITE.md for reported bugs
   - Read PLANNING_WRITE.md for known issues
   - Read DEVELOPER_WRITE.md for recent changes

3. **Add method `_send_phase_messages()`**:
   - Send to QA_READ.md when fix is ready for verification
   - Send to DEVELOPER_READ.md if architectural changes needed
   - Include: fix description, files modified, testing notes

4. **Add method `_format_status_for_write()`**:
   - Format fix results
   - List bugs fixed
   - Note any remaining issues

#### Integration Points:
```python
# At start of execute():
self.initialize_ipc_documents()
bug_reports = self.read_own_tasks()
strategic_docs = self.read_strategic_docs()
phase_outputs = self._read_relevant_phase_outputs()

# Use strategic docs for known issues:
known_issues = strategic_docs.get('TERTIARY_OBJECTIVES', '')

# Before return:
status = self._format_status_for_write(issue, fix_applied)
self.write_own_status(status)
self._send_phase_messages(issue, fix_applied)
```

## Implementation Order

1. **Coding Phase** (simplest, good starting point)
2. **QA Phase** (medium complexity)
3. **Debugging Phase** (most complex, benefits from others)

## Testing Strategy

After each phase implementation:
1. Verify document creation on first run
2. Verify READ document is read correctly
3. Verify WRITE document is updated
4. Verify messages sent to other phases
5. Verify strategic documents are used for context

## Success Criteria

- [ ] Coding phase reads DEVELOPER_READ.md
- [ ] Coding phase writes to DEVELOPER_WRITE.md
- [ ] Coding phase sends messages to QA_READ.md
- [ ] QA phase reads QA_READ.md
- [ ] QA phase writes to QA_WRITE.md
- [ ] QA phase sends messages to DEBUG_READ.md
- [ ] Debugging phase reads DEBUG_READ.md
- [ ] Debugging phase writes to DEBUG_WRITE.md
- [ ] Debugging phase sends messages to QA_READ.md
- [ ] All phases read strategic documents for context
- [ ] No phase writes to its own READ document
- [ ] No phase writes to another's WRITE document

## Code Template

```python
def _read_relevant_phase_outputs(self) -> Dict[str, str]:
    """Read outputs from other phases for context"""
    outputs = {}
    
    # Read specific phase outputs based on phase needs
    # Example for Coding phase:
    outputs['planning'] = self.read_phase_output('planning')
    outputs['qa'] = self.read_phase_output('qa')
    outputs['debug'] = self.read_phase_output('debug')
    
    return outputs

def _send_phase_messages(self, **kwargs):
    """Send messages to other phases' READ documents"""
    # Example for Coding phase:
    message = f"""
## Code Completion Update

**Files Modified**: {kwargs.get('files_modified', [])}
**Files Created**: {kwargs.get('files_created', [])}
**Task**: {kwargs.get('task_description', 'N/A')}
**Status**: Ready for QA review

Please review the changes and verify functionality.
"""
    self.send_message_to_phase('qa', message)

def _format_status_for_write(self, **kwargs) -> str:
    """Format status for WRITE document"""
    return f"""
# {self.phase_name.title()} Phase Status

**Timestamp**: {datetime.now().isoformat()}
**Status**: {kwargs.get('status', 'completed')}

## Summary
{kwargs.get('summary', 'N/A')}

## Details
{kwargs.get('details', 'N/A')}
"""
```

---
**Status**: Ready for Implementation
**Next**: Start with Coding Phase
