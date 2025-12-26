# Refactoring debugging.py - Action Plan

## Current State
- **Import Sources**: 14 (Target: <10)
- **Methods**: 12 in DebuggingPhase class (was 16)
- **Risk Level**: HIGH (affects BasePhase, impacts all 14 phases)

## Phase 1: Extract Debugging Utilities [COMPLETE]
- [x] Analyze current structure
- [x] Create `pipeline/debugging_utils.py` for standalone utilities
- [x] Move error analysis functions
- [x] Move loop detection helpers
- [x] Test extraction

## Phase 2: Consolidate Imports [COMPLETE]
- [x] Group related imports
- [x] Remove unused imports (Path, SYSTEM_PROMPTS, validate_python_syntax)
- [x] Create loop_detection_system.py facade (consolidated 3 imports)
- [x] Create team_coordination.py facade (consolidated 2 imports)
- [x] Create debugging_support.py (consolidated 5 imports)
- [x] Fix indentation issues
- [x] Verify functionality

## Current Status: 14 imports (need 5 more reductions to reach <10)

Remaining imports:
1. base
2. conversation_thread
3. datetime
4. debugging_support
5. debugging_utils
6. handlers
7. loop_detection_system
8. pipeline.user_proxy
9. prompts
10. state.manager
11. state.priority
12. team_coordination
13. tools
14. typing

## Phase 3: Further Consolidation [IN PROGRESS]
- [ ] Consolidate state imports (state.manager + state.priority)
- [ ] Consider merging debugging_support + debugging_utils
- [ ] Evaluate if datetime can be moved to utilities
- [ ] Run comprehensive tests

## Phase 4: Validation [PENDING]
- [ ] Run all phase tests
- [ ] Test polytopic navigation
- [ ] Verify all 14 phases work
- [ ] Performance benchmarks

## Success Criteria
- Import sources: <10 ✗ (currently 14)
- All tests pass ✗
- No functionality loss ✗
- Performance maintained ✗