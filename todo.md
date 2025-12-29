# Deep Pipeline Analysis & Scripts Integration TODO

## Phase 1: Fix Custom Tools Directory (IMMEDIATE) ⚡
- [x] Examine current custom_tools/registry.py implementation
- [x] Examine current custom_tools/handler.py implementation
- [ ] Update registry.py to scan entire scripts/ directory
- [ ] Update handler.py to support both module import and executable modes
- [ ] Test custom tools discovery with new path
- [ ] Verify all scripts/ tools are discovered

## Phase 2: Add File Update Tools (IMMEDIATE) ⚡
- [x] Create pipeline/tools/file_updates.py module
- [x] Implement append_to_file function
- [x] Implement update_section function (for markdown sections)
- [x] Implement insert_after function
- [x] Create tool definitions for file update tools
- [x] Add file update tools to planning phase
- [x] Add file update tools to project_planning phase
- [ ] Test file update tools with MASTER_PLAN.md
- [ ] Test file update tools with PRIMARY_OBJECTIVES.md

## Phase 3: Analyze All Scripts (HIGH PRIORITY) 🔍
- [ ] Examine scripts/analyze_architecture.py
- [ ] Examine scripts/analyze_dependencies.py
- [ ] Examine scripts/create_dependency_graph.py
- [ ] Examine scripts/find_entry_points.py
- [ ] Examine scripts/analyze_complexity.py
- [ ] Document each script's capabilities
- [ ] Document each script's input/output format
- [ ] Identify which phases need which scripts

## Phase 4: Create Analysis Tools Module (HIGH PRIORITY) 🛠️
- [x] Create pipeline/tools/analysis_tools.py
- [x] Implement wrapper for analyze_complexity
- [x] Implement wrapper for detect_dead_code
- [x] Implement wrapper for find_integration_gaps
- [x] Implement wrapper for generate_call_graph
- [x] Implement wrapper for analyze_enhanced
- [x] Implement wrapper for analyze_improved
- [x] Implement wrapper for deep_analyze (unified)
- [x] Create tool definitions for all analysis tools
- [ ] Test each analysis tool wrapper

## Phase 5: Integrate Tools into Phases (HIGH PRIORITY) 🔗
- [x] Add analysis tools to planning phase
- [x] Add analysis tools to coding phase
- [x] Add analysis tools to QA phase
- [x] Add analysis tools to debugging phase
- [x] Add ALL tools to project_planning phase
- [x] Update pipeline/tools.py get_tools_for_phase()
- [x] Add handlers for all new tools in pipeline/handlers.py
- [ ] Test tool availability in each phase

## Phase 6: Update Phase Prompts (HIGH PRIORITY) 📝
- [ ] Examine current planning phase prompt
- [ ] Update planning prompt with analysis tools guidance
- [ ] Examine current QA phase prompt
- [ ] Update QA prompt to clarify issue attribution (CODE issues, not QA failure)
- [ ] Examine current project_planning phase prompt
- [ ] Update project_planning prompt with update capabilities
- [ ] Examine current debugging phase prompt
- [ ] Update debugging prompt with analysis tools guidance
- [ ] Test updated prompts with real scenarios

## Phase 7: Fix QA Phase Logic (CRITICAL) 🐛
- [ ] Examine pipeline/phases/qa.py
- [ ] Identify where QA phase marks itself as failed
- [ ] Update logic: report_issue = CODE problem, not QA failure
- [ ] Update logic: QA phase succeeds when it finds issues
- [ ] Update task status: mark task as needs_fix, not QA as failed
- [ ] Test QA phase with intentionally buggy code
- [ ] Verify QA phase reports success when finding issues

## Phase 8: Comprehensive Testing (CRITICAL) ✅
- [ ] Test planning phase with analysis tools
- [ ] Test planning phase expanding objectives
- [ ] Test QA phase finding and reporting issues correctly
- [ ] Test debugging phase using analysis tools
- [ ] Test project_planning phase updating documents
- [ ] Test all file update tools
- [ ] Test module import mode for scripts
- [ ] Test executable fallback mode for scripts
- [ ] Run full pipeline with test project
- [ ] Verify no regressions

## Phase 9: Documentation (HIGH PRIORITY) 📚
- [ ] Document new file update tools
- [ ] Document analysis tools integration
- [ ] Document phase-specific tool usage
- [ ] Update README with new capabilities
- [ ] Create examples for each analysis tool
- [ ] Document QA phase behavior clarification

## Phase 10: GitHub Integration (FINAL) 🚀
- [ ] Review all changes
- [ ] Create comprehensive commit message
- [ ] Push to GitHub
- [ ] Create pull request
- [ ] Document changes in PR description

## Success Criteria
- ✅ All scripts/ tools available as primary tools
- ✅ File update tools working correctly
- ✅ Planning phase can expand objectives
- ✅ QA phase correctly attributes issues to code
- ✅ All phases have appropriate analysis tools
- ✅ No regressions in existing functionality
- ✅ Comprehensive documentation
- ✅ All tests passing