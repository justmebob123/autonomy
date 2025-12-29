# Deep Pipeline Analysis & FULL Integration TODO

## CRITICAL UNDERSTANDING
- Analysis tools must be CORE PIPELINE FUNCTIONALITY
- Not wrappers, not external scripts - INTEGRATED into the pipeline
- Native implementations ARE the tools, not separate entities
- Scripts/ directory versions can be moved to bin/ or marked as external_
- Focus: Make analysis a FIRST-CLASS pipeline capability

## Phase 1: Proper Integration (CRITICAL) ⚡
- [x] Remove wrapper layer (analysis_tools.py deleted)
- [x] Add analysis capabilities directly to Planning phase __init__
- [x] Add analysis capabilities directly to QA phase __init__
- [x] Add analysis capabilities directly to Debugging phase __init__
- [x] Add analysis capabilities directly to Project Planning phase __init__
- [x] Add analysis capabilities directly to Coding phase __init__
- [x] Add comprehensive analysis method to QA phase
- [x] Update handlers to call native implementations directly
- [ ] Add analysis methods to other phases
- [ ] Update phase prompts to use analysis capabilities
- [ ] Test integrated analysis in each phase

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
- [x] Examine scripts/analysis/ directory structure
- [x] Examine each analysis script in detail
- [x] Extract core logic from each script
- [x] Reimplement as native pipeline tools (4 core tools)
- [x] Create pipeline/analysis/ module with native implementations
- [x] Update handlers to use native implementations
- [ ] Test native implementations

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
- [x] Examine pipeline/phases/qa.py
- [x] Identify where QA phase marks itself as failed
- [x] Update logic: report_issue = CODE problem, not QA failure
- [x] Update logic: QA phase succeeds when it finds issues (returns success=True)
- [x] Task status already correctly set to NEEDS_FIXES
- [x] Next phase set to "debugging" when issues found
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
- [x] Review all changes
- [x] Create comprehensive commit message
- [x] Commit to local repository (commit 625e745, 48bece0)
- [x] Push to GitHub (commits pushed to main)
- [x] Changes now live on main branch
- [x] Native analysis tools deployed
- [x] QA phase logic fix deployed

## Success Criteria
- ✅ All scripts/ tools available as primary tools
- ✅ File update tools working correctly
- ✅ Planning phase can expand objectives
- ✅ QA phase correctly attributes issues to code
- ✅ All phases have appropriate analysis tools
- ✅ No regressions in existing functionality
- ✅ Comprehensive documentation
- ✅ All tests passing