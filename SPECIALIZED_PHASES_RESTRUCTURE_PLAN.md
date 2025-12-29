# Specialized Phases Restructure Plan

## Problem Statement
Tool Design, Prompt Design, Role Design, and their improvement phases are currently integrated into the normal polytope flow. This means they can be selected during regular development, which:

1. **Interferes with main pipeline** - Slows down normal development
2. **Wastes resources** - Creates tools/prompts/roles when not needed
3. **Causes confusion** - LLM may route to these phases unnecessarily
4. **Breaks flow** - Interrupts coding → QA → debugging cycle

## Current Architecture (WRONG)

```
Polytope Vertices: All 13 phases including meta/improvement
Edges: investigation → [prompt_design, role_design, tool_design]
Selection: Normal _select_intelligent_path() can pick any phase
```

## Correct Architecture (NEEDED)

### Primary Pipeline (Always Active)
```
planning → coding → qa → debugging → investigation → documentation
```

### Secondary Systems (On-Demand Only)
```
Tool System: tool_design ↔ tool_evaluation
Prompt System: prompt_design ↔ prompt_improvement  
Role System: role_design ↔ role_improvement
```

### Activation Triggers
1. **Loop Detection**: 3+ consecutive failures on same task
2. **Capability Gap**: Missing tool/prompt/role identified
3. **Explicit Request**: User asks for new capability
4. **Investigation Recommendation**: Investigation phase suggests need

## Implementation Plan

### Phase 1: Remove from Polytope ✅
- Remove meta/improvement phases from `_initialize_polytopic_structure()`
- Remove edges: investigation → [prompt_design, role_design, tool_design]
- Keep only primary 7 phases in polytope

### Phase 2: Create Specialized Activation Logic ✅
- Add `_detect_capability_gap()` method
- Add `_detect_failure_loop()` method
- Add `_should_activate_specialized_phase()` method
- Add activation counters to state

### Phase 3: Create Specialized Execution Methods ✅
- Keep existing `develop_tool()` method
- Add `improve_prompt()` method
- Add `design_role()` method
- These bypass polytope, execute directly

### Phase 4: Update Investigation Phase ✅
- Remove automatic routing to specialized phases
- Add recommendation system instead
- Investigation suggests, coordinator decides

### Phase 5: Add Coordinator Intelligence ✅
- Check for loops before phase selection
- Check for capability gaps
- Activate specialized phases only when needed
- Log activation reasoning

## Success Criteria

✅ Normal flow never enters specialized phases
✅ Specialized phases only activated on-demand
✅ Loop detection triggers tool/prompt/role creation
✅ User can explicitly request specialized phases
✅ Investigation can recommend but not force activation
✅ All changes backward compatible

## Testing Plan

1. **Normal Flow Test**: Run pipeline, verify no specialized phases activated
2. **Loop Test**: Create failing task, verify tool_design activated after 3 failures
3. **Explicit Test**: Request new tool, verify tool_design activated
4. **Investigation Test**: Verify investigation recommends but doesn't force

## Files to Modify

1. `pipeline/coordinator.py` - Main changes
2. `pipeline/phases/investigation.py` - Remove automatic routing
3. `pipeline/state/manager.py` - Add activation counters
4. `pipeline/prompts.py` - Update investigation prompt

## Estimated Impact

- **Code Changes**: ~500 lines
- **Testing**: 2-3 hours
- **Risk**: Low (additive changes, no breaking changes)
- **Benefit**: High (prevents interference, improves efficiency)