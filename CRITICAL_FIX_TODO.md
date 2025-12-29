# Critical Fix TODO - Specialized Phases Infinite Loop

## Immediate Actions Required

### Phase 1: Stop the Bleeding (URGENT)
- [ ] Examine state initialization in coordinator.py
- [ ] Examine state initialization in state/manager.py
- [ ] Determine where PhaseState objects are created
- [ ] Identify why specialized phases are missing from state.phases

### Phase 2: Deep Analysis
- [ ] Map the complete flow of phase registration
- [ ] Trace PhaseState creation for all phases
- [ ] Identify the polytopic structure initialization
- [ ] Find where PRIMARY phases are registered vs SPECIALIZED phases
- [ ] Examine the state.phases dictionary structure

### Phase 3: Root Cause Analysis
- [ ] Determine when specialized phases were removed from state registration
- [ ] Identify the commit that introduced this bug
- [ ] Understand the intended architecture for specialized phases
- [ ] Document the gap between intended and actual implementation

### Phase 4: Solution Design
- [ ] Design proper state registration for specialized phases
- [ ] Ensure specialized phases are tracked even if "on-demand"
- [ ] Verify phase recording works for all phase types
- [ ] Design graceful fallback for missing phases

### Phase 5: Implementation
- [ ] Add specialized phases to state.phases initialization
- [ ] Update coordinator to properly register specialized phases
- [ ] Add defensive checks in base.py for missing phases
- [ ] Test phase activation and recording

### Phase 6: Verification
- [ ] Test normal phase execution
- [ ] Test specialized phase activation
- [ ] Test loop detection and recovery
- [ ] Verify no infinite loops
- [ ] Test state persistence and resume

### Phase 7: Additional Bug Hunting
- [ ] Search for all uses of state.phases[phase_name]
- [ ] Identify other potential KeyError locations
- [ ] Check for similar attribute access patterns
- [ ] Verify all phase names match between registration and usage

## Critical Questions to Answer

1. Where are PhaseState objects created for PRIMARY phases?
2. Why aren't specialized phases getting PhaseState objects?
3. Is the polytopic structure initialization the right place to register phases?
4. Should specialized phases be in the polytopic structure or separate?
5. What is the correct architecture for "on-demand" phases?

## Files to Examine

1. **pipeline/coordinator.py**
   - `_initialize_polytopic_structure()` method
   - Phase registration logic
   - Specialized phase activation

2. **pipeline/state/manager.py**
   - `PhaseState` class
   - State initialization
   - Phase registration

3. **pipeline/phases/base.py**
   - `record_run()` usage
   - Phase name handling
   - State access patterns

4. **All phase files**
   - Verify phase_name attributes
   - Check for naming inconsistencies

## Expected Behavior

- All phases (PRIMARY and SPECIALIZED) should have PhaseState entries
- Specialized phases should be registered even if not in polytopic structure
- Phase recording should work for all phases
- No KeyError should occur when recording phase runs
- Loop detection should work without causing infinite loops