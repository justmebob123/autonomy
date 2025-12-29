# Pipeline Design Improvements TODO

## Phase 1: Remove All Hardcoded Patterns ✅

### 1.1 Clean Up Coordinator ✅
- [x] Remove 'asas' hardcoded check
- [x] Remove hardcoded test patterns ('test_', '/tests/')
- [x] Remove hardcoded directory assumptions ('core/', 'src/')
- [x] Remove documentation skipping logic
- [x] Simplify to: execute tasks by priority, don't filter by patterns

### 1.2 Clean Up Planning Phase ✅
- [x] Remove 'asas' hardcoded check
- [x] Remove test/doc creation bias
- [x] Focus on production code task creation

## Phase 2: Redesign Priority System ✅

### 2.1 Update Task Priority Values ✅
- [x] Production code: 10-80 (keep)
- [x] Tests: 200+ (much lower)
- [x] Documentation: 300+ (lowest)
- [x] Update all task creation to use new priorities

### 2.2 Simplify Task Selection ✅
- [x] Remove complex filtering logic
- [x] Use simple priority-based selection
- [x] Let priority numbers do the work

## Phase 3: Update Prompts ⏳

### 3.1 Planning Phase Prompt
- [ ] Remove test creation guidance
- [ ] Remove documentation guidance
- [ ] Add "PRODUCTION CODE ONLY" emphasis
- [ ] Tests/docs only if explicitly in MASTER_PLAN

### 3.2 Other Phase Prompts
- [ ] Review coding prompt - ensure production focus
- [ ] Review QA prompt - ensure it doesn't trigger test creation
- [ ] Review all prompts for hardcoded assumptions

## Phase 4: Add Generic Classification (Optional) ⏳

### 4.1 File Type Classification
- [ ] Create utility module for file classification
- [ ] Use file extensions, not patterns
- [ ] Use content analysis when needed
- [ ] Make it project-agnostic

## Phase 5: Testing & Validation ⏳

### 5.1 Test Changes
- [ ] Test with test-automation project
- [ ] Verify no hardcoded patterns remain
- [ ] Verify production code prioritized
- [ ] Verify tests/docs minimal

### 5.2 Documentation
- [ ] Update README with design principles
- [ ] Document priority system
- [ ] Document file classification approach