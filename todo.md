# Refactoring Phase Activation - Implementation TODO

## Phase 1: Quick Fixes (PRIORITY: CRITICAL)

### Fix 1.1: Add Refactoring Trigger to Tactical Decision Tree
- [x] Add `_should_trigger_refactoring()` method to coordinator.py
- [x] Add `_count_recent_files()` method to coordinator.py
- [x] Add `_detect_duplicate_patterns()` method to coordinator.py
- [x] Update `_determine_next_action_tactical()` to call trigger check
- [ ] Test periodic trigger (every 20 iterations)
- [ ] Test file count trigger (15+ files)
- [ ] Test duplicate pattern trigger

### Fix 1.2: Improve Dimensional Profile
- [x] Update refactoring dimensions in `_calculate_initial_dimensions()`
- [x] Change temporal: 0.6 → 0.7
- [x] Change functional: 0.7 → 0.8
- [x] Change error: 0.4 → 0.6
- [x] Change integration: 0.8 → 0.9
- [ ] Test polytopic selection with new dimensions

## Phase 2: IPC Integration

### Fix 2.1: QA Phase Integration
- [ ] Add duplicate detection to qa.py
- [ ] Add write to REFACTORING_READ.md
- [ ] Add next_phase hint setting
- [ ] Test QA → Refactoring flow

### Fix 2.2: Coding Phase Integration
- [ ] Add file creation tracking to coding.py
- [ ] Add write to REFACTORING_READ.md after 10+ files
- [ ] Add next_phase hint setting
- [ ] Test Coding → Refactoring flow

### Fix 2.3: Investigation Phase Integration
- [ ] Add conflict detection to investigation.py
- [ ] Add write to REFACTORING_READ.md
- [ ] Add next_phase hint setting
- [ ] Test Investigation → Refactoring flow

## Phase 3: Advanced Features

### Fix 3.1: Enhanced Duplicate Detection
- [ ] Improve `_detect_duplicate_patterns()` with AST analysis
- [ ] Add similarity scoring
- [ ] Add configurable threshold

### Fix 3.2: Enhanced File Tracking
- [ ] Add persistent file creation tracking to state
- [ ] Add file creation rate calculation
- [ ] Add trend analysis

### Fix 3.3: Data Dimension Scoring
- [ ] Add data-intensive situation detection to `_analyze_situation()`
- [ ] Add many-files situation detection
- [ ] Update `_calculate_phase_priority()` to use data dimension
- [ ] Test scoring with data dimension

## Testing & Validation

### Integration Tests
- [ ] Test periodic refactoring trigger
- [ ] Test file count trigger
- [ ] Test duplicate pattern trigger
- [ ] Test IPC flow (QA → Refactoring)
- [ ] Test IPC flow (Coding → Refactoring)
- [ ] Test phase hint system
- [ ] Test polytopic selection with new dimensions

### End-to-End Tests
- [ ] Run full pipeline with refactoring enabled
- [ ] Verify refactoring activates appropriately
- [ ] Verify refactoring performs analysis
- [ ] Verify refactoring generates recommendations
- [ ] Verify refactoring integrates with other phases

## Documentation

- [ ] Update DEEP_REFACTORING_ANALYSIS.md with implementation results
- [ ] Create REFACTORING_ACTIVATION_COMPLETE.md
- [ ] Update pipeline documentation
- [ ] Add refactoring examples

## Git Commits

- [ ] Commit Phase 1 changes
- [ ] Commit Phase 2 changes
- [ ] Commit Phase 3 changes
- [ ] Commit documentation
- [ ] Push all changes to GitHub

---

**Current Status**: Ready to implement Phase 1
**Next Action**: Implement `_should_trigger_refactoring()` method