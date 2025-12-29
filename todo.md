# TODO: Fix Document IPC System - Strategic Documents Not Being Created

## CRITICAL BUG DISCOVERED ⚠️

The Document IPC system has a critical flaw:
- Phase READ/WRITE documents ARE created (PLANNING_READ.md, etc.)
- Strategic documents ARE NOT created (PRIMARY_OBJECTIVES.md, SECONDARY_OBJECTIVES.md, TERTIARY_OBJECTIVES.md, ARCHITECTURE.md)
- Planning phase tries to write to these documents but they don't exist
- Result: Updates appear to happen in logs but files are never created

## Root Cause Analysis

1. `pipeline/document_ipc.py` defines strategic_documents list
2. `initialize_documents()` only creates phase documents
3. Strategic documents are never initialized with templates
4. Planning phase writes to non-existent files (creates them but with wrong format)
5. Other phases try to read non-existent files (get empty strings)

## Fix Required

### 1. Add Strategic Document Initialization ✅
- [x] Add `_create_strategic_documents()` method to DocumentIPC
- [x] Create templates for each strategic document:
  - [x] PRIMARY_OBJECTIVES.md template
  - [x] SECONDARY_OBJECTIVES.md template
  - [x] TERTIARY_OBJECTIVES.md template
  - [x] ARCHITECTURE.md template (use ARCHITECTURE_EXAMPLE.md)
- [x] Call from `initialize_documents()`
- [x] Ensure templates are comprehensive and useful

### 2. Fix Planning Phase Document Updates ✅
- [x] Review `_update_tertiary_objectives()` method
- [x] Changed from write_text() to file_updater.update_section()
- [x] Now APPENDS to existing content, doesn't overwrite
- [x] Updates multiple sections independently
- [ ] Review `_update_secondary_objectives()` method (TODO)
- [ ] Review `_update_architecture_doc()` method (TODO)

### 3. Fix All Phases Document Reading ⏳
- [ ] Verify Planning phase reads strategic docs correctly
- [ ] Verify Coding phase reads strategic docs correctly
- [ ] Verify QA phase reads strategic docs correctly
- [ ] Verify Debugging phase reads strategic docs correctly
- [ ] Add error handling for missing documents

### 4. Add Document Verification ⏳
- [ ] Add method to verify all documents exist
- [ ] Add method to check document health
- [ ] Log warnings if documents are missing
- [ ] Auto-recreate missing documents

### 5. Testing ⏳
- [ ] Test document initialization on fresh project
- [ ] Test strategic document updates
- [ ] Test document reading across phases
- [ ] Verify content accumulates correctly
- [ ] Test with missing documents (recovery)

## Success Criteria
- [ ] All strategic documents created on first run
- [ ] Planning phase successfully updates documents
- [ ] Updates are visible in the files
- [ ] Content accumulates over time (not overwritten)
- [ ] All phases can read strategic documents
- [ ] System recovers gracefully from missing documents