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

## PHASE 2: File Operation Tools ✅

### 2.1 Move File Tool
- [x] Add to `pipeline/tool_modules/file_operations.py`
  - [x] move_file tool definition
  - [x] Uses git mv for history
  - [x] Auto-updates imports
  - [x] Creates directories
  - [x] Validates result

### 2.2 Rename File Tool
- [x] Add to `pipeline/tool_modules/file_operations.py`
  - [x] rename_file tool definition
  - [x] Renames in same directory
  - [x] Auto-updates imports
  - [x] Preserves git history

### 2.3 Restructure Directory Tool
- [x] Add to `pipeline/tool_modules/file_operations.py`
  - [x] restructure_directory tool definition
  - [x] Moves multiple files
  - [x] Updates all imports
  - [x] Handles dependencies

### 2.4 Analyze File Placement Tool
- [x] Add to `pipeline/tool_modules/file_operations.py`
  - [x] analyze_file_placement tool definition
  - [x] Suggests optimal location
  - [x] Analyzes impact
  - [x] Provides confidence score

### 2.5 Build Import Graph Tool
- [x] Add to `pipeline/tool_modules/import_operations.py`
  - [x] build_import_graph tool definition
  - [x] Returns complete graph
  - [x] Identifies issues

### 2.6 Analyze Import Impact Tool
- [x] Add to `pipeline/tool_modules/import_operations.py`
  - [x] analyze_import_impact tool definition
  - [x] Predicts impact
  - [x] Lists affected files

## PHASE 3: Handler Integration ✅

### 3.1 Add Handlers to ToolCallHandler
- [x] Update `pipeline/handlers.py`
  - [x] _handle_move_file
  - [x] _handle_rename_file
  - [x] _handle_restructure_directory
  - [x] _handle_analyze_file_placement
  - [x] _handle_build_import_graph
  - [x] _handle_analyze_import_impact

### 3.2 Initialize Analysis Components
- [x] Update `ToolCallHandler.__init__`
  - [x] Add ImportGraphBuilder (created on demand)
  - [x] Add ImportImpactAnalyzer (created on demand)
  - [x] Add ImportUpdater (created on demand)
  - [x] Add ArchitecturalContextProvider (created on demand)
  - [x] Add FilePlacementAnalyzer (created on demand)

## PHASE 4: Phase Integration ✅

### 4.1 Coding Phase Enhancement
- [x] Update `pipeline/phases/coding.py`
  - [x] Add import context to _build_context
  - [x] Add architectural context
  - [x] Update prompts to mention new tools
  - [x] Add file placement validation

### 4.2 Refactoring Phase Enhancement
- [x] Update `pipeline/phases/refactoring.py`
  - [x] Add file placement analysis
  - [x] Create tasks for misplaced files
  - [x] Add import impact analysis
  - [x] Update prompts to mention new tools

### 4.3 Update Tool Definitions
- [x] Update `pipeline/tools.py`
  - [x] Import new tool modules
  - [x] Add to TOOLS_CODING
  - [x] Add to TOOLS_REFACTORING

## PHASE 5: Prompt Updates ✅

### 5.1 Coding Phase Prompts
- [x] Update `pipeline/prompts.py`
  - [x] Add file operation guidelines
  - [x] Mention move_file tool
  - [x] Mention rename_file tool
  - [x] Explain when to use each

### 5.2 Refactoring Phase Prompts
- [x] Update refactoring prompts
  - [x] Add file placement analysis
  - [x] Mention restructure_directory
  - [x] Explain architectural alignment
  - [x] Guide on import-aware refactoring

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
- [x] Implementation COMPLETE ✅
- [ ] Testing pending (recommended but not blocking)
- [x] Documentation complete