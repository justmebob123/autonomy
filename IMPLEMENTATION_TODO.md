# Critical File Operations Implementation TODO

## PHASE 1: Import Analysis Infrastructure ⏳

### 1.1 Enhanced Import Graph Builder
- [ ] Create `pipeline/analysis/import_graph.py`
  - [ ] ImportGraphBuilder class
  - [ ] Build complete import graph
  - [ ] Detect circular dependencies
  - [ ] Find orphaned files
  - [ ] Cache graph for performance

### 1.2 Import Impact Analyzer
- [ ] Create `pipeline/analysis/import_impact.py`
  - [ ] ImportImpactAnalyzer class
  - [ ] Analyze move/rename/delete impact
  - [ ] List affected files
  - [ ] Calculate risk level
  - [ ] Estimate changes needed

### 1.3 Import Updater
- [ ] Create `pipeline/analysis/import_updater.py`
  - [ ] ImportUpdater class
  - [ ] Generate import updates for moves
  - [ ] Update all affected files
  - [ ] Validate no broken imports
  - [ ] Handle edge cases

### 1.4 Architectural Context Provider
- [ ] Create `pipeline/context/architectural.py`
  - [ ] ArchitecturalContextProvider class
  - [ ] Parse ARCHITECTURE.md placement rules
  - [ ] Suggest optimal file locations
  - [ ] Validate file placements
  - [ ] Convention-based organization

### 1.5 File Placement Analyzer
- [ ] Create `pipeline/analysis/file_placement.py`
  - [ ] FilePlacementAnalyzer class
  - [ ] Find misplaced files
  - [ ] Suggest relocations
  - [ ] Analyze architectural violations

## PHASE 2: File Operation Tools ⏳

### 2.1 Move File Tool
- [ ] Add to `pipeline/tool_modules/file_operations.py`
  - [ ] move_file tool definition
  - [ ] Uses git mv for history
  - [ ] Auto-updates imports
  - [ ] Creates directories
  - [ ] Validates result

### 2.2 Rename File Tool
- [ ] Add to `pipeline/tool_modules/file_operations.py`
  - [ ] rename_file tool definition
  - [ ] Renames in same directory
  - [ ] Auto-updates imports
  - [ ] Preserves git history

### 2.3 Restructure Directory Tool
- [ ] Add to `pipeline/tool_modules/file_operations.py`
  - [ ] restructure_directory tool definition
  - [ ] Moves multiple files
  - [ ] Updates all imports
  - [ ] Handles dependencies

### 2.4 Analyze File Placement Tool
- [ ] Add to `pipeline/tool_modules/file_operations.py`
  - [ ] analyze_file_placement tool definition
  - [ ] Suggests optimal location
  - [ ] Analyzes impact
  - [ ] Provides confidence score

### 2.5 Build Import Graph Tool
- [ ] Add to `pipeline/tool_modules/import_operations.py`
  - [ ] build_import_graph tool definition
  - [ ] Returns complete graph
  - [ ] Identifies issues

### 2.6 Analyze Import Impact Tool
- [ ] Add to `pipeline/tool_modules/import_operations.py`
  - [ ] analyze_import_impact tool definition
  - [ ] Predicts impact
  - [ ] Lists affected files

## PHASE 3: Handler Integration ⏳

### 3.1 Add Handlers to ToolCallHandler
- [ ] Update `pipeline/handlers.py`
  - [ ] _handle_move_file
  - [ ] _handle_rename_file
  - [ ] _handle_restructure_directory
  - [ ] _handle_analyze_file_placement
  - [ ] _handle_build_import_graph
  - [ ] _handle_analyze_import_impact

### 3.2 Initialize Analysis Components
- [ ] Update `ToolCallHandler.__init__`
  - [ ] Add ImportGraphBuilder
  - [ ] Add ImportImpactAnalyzer
  - [ ] Add ImportUpdater
  - [ ] Add ArchitecturalContextProvider
  - [ ] Add FilePlacementAnalyzer

## PHASE 4: Phase Integration ⏳

### 4.1 Coding Phase Enhancement
- [ ] Update `pipeline/phases/coding.py`
  - [ ] Add import context to _build_context
  - [ ] Add architectural context
  - [ ] Update prompts to mention new tools
  - [ ] Add file placement validation

### 4.2 Refactoring Phase Enhancement
- [ ] Update `pipeline/phases/refactoring.py`
  - [ ] Add file placement analysis
  - [ ] Create tasks for misplaced files
  - [ ] Add import impact analysis
  - [ ] Update prompts to mention new tools

### 4.3 Update Tool Definitions
- [ ] Update `pipeline/tools.py`
  - [ ] Import new tool modules
  - [ ] Add to TOOLS_CODING
  - [ ] Add to TOOLS_REFACTORING

## PHASE 5: Prompt Updates ⏳

### 5.1 Coding Phase Prompts
- [ ] Update `pipeline/prompts.py`
  - [ ] Add file operation guidelines
  - [ ] Mention move_file tool
  - [ ] Mention rename_file tool
  - [ ] Explain when to use each

### 5.2 Refactoring Phase Prompts
- [ ] Update refactoring prompts
  - [ ] Add file placement analysis
  - [ ] Mention restructure_directory
  - [ ] Explain architectural alignment
  - [ ] Guide on import-aware refactoring

## PHASE 6: Testing & Validation ⏳

### 6.1 Unit Tests
- [ ] Create `tests/test_import_graph.py`
- [ ] Create `tests/test_import_impact.py`
- [ ] Create `tests/test_import_updater.py`
- [ ] Create `tests/test_file_placement.py`
- [ ] Create `tests/test_file_operations.py`

### 6.2 Integration Tests
- [ ] Test move_file with import updates
- [ ] Test rename_file with import updates
- [ ] Test restructure_directory
- [ ] Test file placement analysis
- [ ] Test end-to-end refactoring

### 6.3 Validation
- [ ] Verify no broken imports after moves
- [ ] Verify git history preserved
- [ ] Verify architectural alignment
- [ ] Verify all edge cases handled

## PHASE 7: Documentation ⏳

### 7.1 Tool Documentation
- [ ] Document move_file usage
- [ ] Document rename_file usage
- [ ] Document restructure_directory usage
- [ ] Document analysis tools
- [ ] Add examples

### 7.2 Integration Documentation
- [ ] Document phase integration
- [ ] Document handler integration
- [ ] Document prompt updates
- [ ] Add troubleshooting guide

## CRITICAL DEPENDENCIES

### Must Complete First
1. Import Graph Builder (foundation for everything)
2. Import Impact Analyzer (needed for safe operations)
3. Import Updater (needed for move/rename)

### Can Parallelize
- File operation tools (once import system ready)
- Handler integration (once tools defined)
- Phase integration (once handlers ready)

## PRIORITY ORDER

1. **CRITICAL** - Import Graph Builder
2. **CRITICAL** - Import Impact Analyzer
3. **CRITICAL** - Import Updater
4. **HIGH** - move_file tool
5. **HIGH** - rename_file tool
6. **HIGH** - Handler integration
7. **MEDIUM** - restructure_directory tool
8. **MEDIUM** - File placement analyzer
9. **MEDIUM** - Phase integration
10. **LOW** - Testing and documentation

## ESTIMATED TIMELINE

- Phase 1 (Import Infrastructure): 2-3 days
- Phase 2 (File Operation Tools): 1-2 days
- Phase 3 (Handler Integration): 1 day
- Phase 4 (Phase Integration): 1 day
- Phase 5 (Prompt Updates): 0.5 days
- Phase 6 (Testing): 1-2 days
- Phase 7 (Documentation): 0.5 days

**Total**: 7-10 days for complete implementation

## CURRENT STATUS

- [x] Analysis complete
- [x] Design complete
- [ ] Implementation in progress
- [ ] Testing pending
- [ ] Documentation pending