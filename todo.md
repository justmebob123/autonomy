# Complete Scripts Integration TODO

## ✅ COMPLETED
- ✅ Native analysis tools (complexity, dead_code, integration_gaps, call_graph)
- ✅ File update tools (append, update_section, insert_after/before, replace_between)
- ✅ Direct phase access (analyzers imported in __init__)
- ✅ QA phase logic fix (success=True when finding issues)
- ✅ Wrapper layer removed (analysis_tools.py deleted)
- ✅ Core integration deployed to main branch

## Phase 1: External Script Handlers ⏳
- [ ] Add handler for analyze_enhanced (ENHANCED_DEPTH_61_ANALYZER.py)
- [ ] Add handler for analyze_improved (IMPROVED_DEPTH_61_ANALYZER.py)
- [ ] Add handler for deep_analyze (deep_analyze.py)
- [ ] Update handlers.py with new tool definitions
- [ ] Test external script handlers

## Phase 2: Phase Execute() Integration ✅
- [x] Planning Phase: Add complexity & gap analysis calls in execute()
- [x] QA Phase: Add comprehensive analysis calls in execute()
- [x] Debugging Phase: Add complexity & call graph calls in execute()
- [x] Coding Phase: Add complexity validation calls in execute()
- [x] Project Planning Phase: Add full codebase analysis calls in execute()
- [ ] Test phase integration with real scenarios

## Phase 3: Phase Prompt Updates ⏳
- [ ] Update Planning Phase prompt with analysis guidance
- [ ] Update QA Phase prompt with analysis guidance
- [ ] Update Debugging Phase prompt with analysis guidance
- [ ] Update Coding Phase prompt with analysis guidance
- [ ] Update Project Planning Phase prompt with analysis guidance
- [ ] Add examples of when/how to use analysis tools

## Phase 4: Custom Tools Registration ⏳
- [ ] Register code_complexity custom tool in handlers
- [ ] Register find_todos custom tool in handlers
- [ ] Register analyze_imports custom tool in handlers
- [ ] Add custom tool definitions to tool_definitions.py
- [ ] Test custom tool calling from LLM

## Phase 5: Review Other Phases ⏳
- [ ] Review tool_design phase for analysis needs
- [ ] Review tool_evaluation phase for analysis needs
- [ ] Review documentation phase for analysis needs
- [ ] Add analysis capabilities where appropriate

## Phase 6: Testing & Validation ⏳
- [ ] Test all external script handlers
- [ ] Test phase execute() logic with analysis
- [ ] Test custom tools integration
- [ ] Test file update tools with real files
- [ ] Validate end-to-end workflow
- [ ] Run full pipeline with test project

## Phase 7: Documentation ⏳
- [ ] Update README with new capabilities
- [ ] Document all analysis tools
- [ ] Document custom tools integration
- [ ] Create usage examples
- [ ] Document phase-specific tool usage

## Phase 8: Deployment ⏳
- [ ] Review all changes
- [ ] Commit all changes
- [ ] Push to main branch
- [ ] Create deployment summary
- [ ] Mark complete

## Success Criteria
- [ ] All scripts/ tools accessible via tool calling
- [ ] All phases use analysis in execute() logic
- [ ] Phase prompts guide LLM on analysis usage
- [ ] Custom tools properly registered and working
- [ ] Comprehensive testing completed
- [ ] Documentation updated
- [ ] No regressions in existing functionality