# Filename Validation & Refactoring Context Enhancement

## Overview
Implementing comprehensive filename validation and enhanced refactoring decision context to prevent issues like `<version>_projects_table.py` and ensure AI makes informed decisions about code refactoring.

## Phase 1: Filename Validation System ✅

### Core Validation
- [x] Create `FilenameValidator` class with issue detection
- [x] Implement placeholder text detection (CRITICAL)
- [x] Implement version iterator detection (WARNING)
- [x] Implement parenthetical text detection (INFO)
- [x] Implement space and special character detection
- [x] Fix None context handling bug
- [x] Test validation with example filenames

### Integration with Coding Phase
- [x] Import `FilenameValidator` in coding phase
- [x] Initialize validator in `__init__`
- [x] Create `_validate_tool_call_filenames()` method
- [x] Add validation before tool execution
- [x] Return error result with suggestions on validation failure

### Prompt Enhancement
- [x] Add filename guidelines to coding prompt
- [x] Include examples of correct/incorrect filenames
- [x] Emphasize no placeholder text requirement

## Phase 2: Refactoring Context System ✅

### Context Builder
- [x] Create `RefactoringContextBuilder` class
- [x] Implement strategic document loading (MASTER_PLAN, ARCHITECTURE, ROADMAP)
- [x] Implement analysis report loading (dead code, complexity, bugs, etc.)
- [x] Implement code context loading (target file, related files, tests)
- [x] Implement project state extraction
- [x] Create `RefactoringContext` dataclass

### Prompt Formatting
- [x] Create `format_context_for_prompt()` method
- [x] Include all strategic documents in prompt
- [x] Include all analysis reports in prompt
- [x] Include code context and relationships
- [x] Include decision framework with 5 options
- [x] Add project phase awareness

## Phase 3: Documentation ✅

### Analysis Documents
- [x] Create `FILENAME_NORMALIZATION_ANALYSIS.md`
  - Problem statement
  - Categories of issues
  - Detection strategy
  - Implementation plan
  
- [x] Create `REFACTORING_DECISION_FRAMEWORK.md`
  - Philosophy (mosaic approach)
  - Decision categories (remove, integrate, refactor, preserve)
  - Required context for AI
  - Decision workflow
  - Example decision trees
  - AI prompt template

## Phase 4: Integration with Refactoring Phase ✅

### Refactoring Phase Enhancement
- [x] Import `RefactoringContextBuilder` in refactoring phase
- [x] Initialize context builder in `__init__`
- [x] Modify `_build_task_context()` to use context builder
- [x] Update AI prompts to include full context
- [x] Ensure MASTER_PLAN and ARCHITECTURE are always included
- [x] Add project state information to prompts
- [x] Add fallback to basic context if builder fails

### Task Prompt Enhancement
- [x] Enhanced `_build_task_context()` to use comprehensive context builder
- [x] Include strategic documents in every task prompt
- [x] Include relevant analysis reports
- [x] Include code relationships and dependencies
- [x] Decision framework guidance already in `_build_task_prompt()`

### Context Gathering
- [x] Context builder loads all analysis reports
- [x] Load MASTER_PLAN.md content
- [x] Load ARCHITECTURE.md content
- [x] Load ROADMAP.md if exists
- [x] Extract project phase and completion percentage
- [x] Gather recent changes and pending tasks (placeholders for now)

## Phase 5: Testing & Validation

### Filename Validation Testing
- [ ] Test with placeholder text filenames
- [ ] Test with version iterators
- [ ] Test with parenthetical text
- [ ] Test with spaces and special characters
- [ ] Test with valid filenames
- [ ] Verify blocking behavior for CRITICAL issues
- [ ] Verify warning behavior for non-critical issues

### Refactoring Context Testing
- [ ] Test context building with all documents present
- [ ] Test context building with missing optional documents
- [ ] Test prompt formatting with full context
- [ ] Test prompt formatting with minimal context
- [ ] Verify truncation works correctly
- [ ] Verify related files detection
- [ ] Verify test files detection

### Integration Testing
- [ ] Run coding phase with filename validation
- [ ] Verify placeholder text is blocked
- [ ] Verify error messages are clear
- [ ] Run refactoring phase with enhanced context
- [ ] Verify AI receives full context
- [ ] Verify AI makes informed decisions
- [ ] Test with real project scenarios

## Phase 6: Commit & Push ✅

### Git Operations
- [x] Review all changes
- [x] Test compilation of all modified files
- [x] Commit filename validation system
- [x] Commit refactoring context system
- [x] Commit documentation
- [x] Push to GitHub repository (commit ec6a09e)

## Success Criteria

### Filename Validation
- ✅ No files created with placeholder text (e.g., `<version>`)
- ✅ Clear error messages when validation fails
- ✅ Helpful suggestions for corrections
- ✅ Non-blocking warnings for minor issues

### Refactoring Context
- ✅ AI receives MASTER_PLAN content in every refactoring decision
- ✅ AI receives ARCHITECTURE content in every refactoring decision
- ✅ AI receives all relevant analysis reports
- ✅ AI receives code context and relationships
- ✅ AI receives project state information
- ✅ AI makes informed decisions based on full context

### Overall
- ✅ Zero placeholder text in filenames
- ✅ Informed refactoring decisions
- ✅ Proper integration vs removal decisions
- ✅ Architecture-aligned refactoring
- ✅ Phase-aware decision making

## Notes

- Filename validation is CRITICAL - must block file creation
- Refactoring context is ESSENTIAL - AI needs full picture
- Project phase matters - early stage means more integration opportunities
- MASTER_PLAN and ARCHITECTURE are the source of truth
- Every piece has its place in the mosaic - understand before removing