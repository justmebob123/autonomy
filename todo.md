# TODO: Architecture-Driven Integration Conflict Detection System

## 1. Remove Hardcoded Library Paths ✅
- [x] Create ARCHITECTURE_SCHEMA.md - Schema definition
- [x] Create ARCHITECTURE_EXAMPLE.md - Example for projects
- [x] Create pipeline/architecture_parser.py - Parser implementation
- [x] Remove hardcoded paths from `pipeline/phases/qa.py`
- [x] Update QA phase to use architecture config
- [x] Load architecture config in QA __init__
- [ ] Remove any other hardcoded project-specific assumptions

## 2. Enhanced Dead Code Detection ✅
- [x] Modify `pipeline/analysis/dead_code.py` to:
  - [x] Accept architecture config parameter
  - [x] Mark unused code for REVIEW instead of deletion
  - [x] Detect similar functionality across files
  - [x] Flag potential duplicate implementations
  - [x] Provide context about why code might be unused
  - [x] Use architecture config to identify library modules
  - [x] Add DeadCodeIssue dataclass for review issues
  - [x] Add _generate_review_issues() method
  - [x] Add _find_similar_functions() and _find_similar_methods()

## 3. Integration Conflict Detector ✅
- [x] Create `pipeline/analysis/integration_conflicts.py`:
  - [x] Detect duplicate/parallel implementations
  - [x] Compare file naming conventions
  - [x] Identify feature overlap between files
  - [x] Flag as integration conflicts with recommendations
  - [x] Use architecture config for intelligent detection
  - [x] Add IntegrationConflict and IntegrationConflictResult dataclasses
  - [x] Implement _detect_duplicate_classes()
  - [x] Implement _detect_duplicate_functions()
  - [x] Implement _detect_naming_conflicts()
  - [x] Implement _detect_parallel_implementations()

## 4. Update QA Phase ✅
- [x] Import architecture_parser
- [x] Load architecture config in __init__
- [x] Pass config to dead code detector
- [x] Use config.is_library_module() instead of hardcoded checks
- [x] Update run_comprehensive_analysis() to use config
- [x] Add integration conflict detection
- [x] Add dead code review issues to analysis
- [x] Update logging to include conflicts and review issues

## 5. Update Planning Phase ✅
- [x] Import architecture_parser
- [x] Load architecture config
- [x] Use integration conflict detector
- [x] Add project-wide conflict detection to _perform_deep_analysis()
- [x] Update _update_tertiary_objectives() to include conflicts
- [x] Add conflict resolution guidance to TERTIARY_OBJECTIVES.md

## 6. Update Debugging Phase ⏳
- [ ] Import architecture_parser
- [ ] Load architecture config
- [ ] Handle integration conflict resolution
- [ ] Merge features from multiple files
- [ ] Delete obsolete implementations

## 7. Testing ⏳
- [ ] Test with email.py / email_alerts.py example
- [ ] Verify no hardcoded assumptions
- [ ] Verify architecture-driven behavior
- [ ] Verify proper conflict detection and resolution
- [ ] Test with project that has ARCHITECTURE.md
- [ ] Test with project that lacks ARCHITECTURE.md (defaults)

## 8. Push to GitHub ⏳
- [x] Commit all changes (commits 4440420, ab01367)
- [ ] Push to GitHub repository

## Success Criteria
- [x] No hardcoded project-specific paths in pipeline code
- [x] Architecture document drives library detection
- [x] Dead code marked for review, not deletion
- [x] Duplicate implementations detected as integration conflicts
- [x] Conflict resolution proposes unified implementations
- [ ] All changes tested and deployed