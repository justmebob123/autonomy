# Class Renaming Plan

## Overview
Found 16 duplicate class names across the codebase. Most duplicates fall into two categories:
1. **Test file duplicates** - MockCoordinator appears 4 times in test_loop_fix.py (nested test classes)
2. **bin/ vs scripts/ duplicates** - Identical tool implementations in two directories

## Renaming Strategy

### Category 1: Test File Duplicates (No Action Needed)
**MockCoordinator (4 instances in test_loop_fix.py)**
- These are nested classes within different test functions
- Python allows this - they're in different scopes
- **Action**: None needed - this is valid Python

### Category 2: Core Pipeline Duplicates (Rename for Clarity)

#### 1. ToolValidator (3 instances)
**Current:**
- `pipeline/tool_validator.py` - Main pipeline validator
- `bin/custom_tools/core/validator.py` - Custom tool validator
- `scripts/custom_tools/core/validator.py` - Duplicate of bin version

**Plan:**
- Keep: `pipeline/tool_validator.py::ToolValidator` (main pipeline)
- Rename: `bin/custom_tools/core/validator.py::ToolValidator` → `CustomToolValidator`
- Rename: `scripts/custom_tools/core/validator.py::ToolValidator` → `CustomToolValidator`

#### 2. CallGraphVisitor (2 instances)
**Current:**
- `pipeline/call_chain_tracer.py` - Traces call chains
- `pipeline/analysis/call_graph.py` - Analyzes call graphs

**Plan:**
- Rename: `pipeline/call_chain_tracer.py::CallGraphVisitor` → `CallChainVisitor`
- Keep: `pipeline/analysis/call_graph.py::CallGraphVisitor` (more general purpose)

#### 3. ToolRegistry (2 instances)
**Current:**
- `pipeline/tool_registry.py` - Main tool registry
- `pipeline/custom_tools/registry.py` - Custom tools registry

**Plan:**
- Keep: `pipeline/tool_registry.py::ToolRegistry` (main registry)
- Rename: `pipeline/custom_tools/registry.py::ToolRegistry` → `CustomToolRegistry`

#### 4. ArchitectureAnalyzer (2 instances)
**Current:**
- `pipeline/architecture_analyzer.py` - Main architecture analyzer
- `pipeline/analysis/file_refactoring.py` - Refactoring-specific analyzer

**Plan:**
- Keep: `pipeline/architecture_analyzer.py::ArchitectureAnalyzer` (main analyzer)
- Rename: `pipeline/analysis/file_refactoring.py::ArchitectureAnalyzer` → `RefactoringArchitectureAnalyzer`

#### 5. Message (2 instances)
**Current:**
- `pipeline/conversation_thread.py` - Legacy message class
- `pipeline/messaging/message.py` - New messaging system

**Plan:**
- Rename: `pipeline/conversation_thread.py::Message` → `ConversationMessage`
- Keep: `pipeline/messaging/message.py::Message` (new standard)

#### 6. ProjectPlanningPhase (2 instances)
**Current:**
- `pipeline/phases/project_planning.py` - Current implementation
- `pipeline/phases/project_planning_backup.py` - Backup file

**Plan:**
- Keep: `pipeline/phases/project_planning.py::ProjectPlanningPhase`
- **Delete**: `pipeline/phases/project_planning_backup.py` (backup file should not be in repo)

### Category 3: bin/ vs scripts/ Duplicates (Consolidate)

These are exact duplicates - same code in two directories:
- `bin/custom_tools/` - Appears to be the active version
- `scripts/custom_tools/` - Appears to be a duplicate/backup

**Classes affected:**
- TestTool
- AnalyzeImports
- FindTodos
- CodeComplexity
- TemplateGenerator
- ToolResult
- TimeoutError
- BaseTool
- ToolExecutor

**Plan:**
- Keep: All classes in `bin/custom_tools/`
- **Delete**: Entire `scripts/custom_tools/` directory (duplicate)

## Implementation Order

1. **Delete duplicate directory** - Remove `scripts/custom_tools/` (9 duplicates resolved)
2. **Delete backup file** - Remove `project_planning_backup.py` (1 duplicate resolved)
3. **Rename core classes** - Rename 5 classes with clear, descriptive names
4. **Update all imports** - Find and update all references to renamed classes
5. **Verify** - Run validation and tests

## Expected Outcome
- 16 duplicates → 0 duplicates
- Clearer class naming conventions
- Cleaner codebase (removed backup/duplicate files)