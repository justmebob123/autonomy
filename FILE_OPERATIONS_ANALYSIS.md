# File Operations and Refactoring Capabilities Analysis

## Executive Summary

This document analyzes the file operation capabilities of the coding and refactoring phases, examining their ability to move, delete, rename, and restructure file paths while maintaining import relationships and code integrity.

---

## 1. CURRENT FILE OPERATION TOOLS

### 1.1 Available Tools in Coding Phase

**Location**: `pipeline/tools/__init__.py` and tool registry

```python
# Current coding phase tools:
- create_file(filepath, content)
- modify_file(filepath, original_code, new_code)
- full_file_rewrite(filepath, content)
- delete_file(filepath)
- mark_task_complete(reason)
```

**Analysis**:
- ✅ Can create new files
- ✅ Can modify existing files
- ✅ Can delete files
- ❌ **CANNOT move/rename files**
- ❌ **CANNOT restructure directories**
- ❌ **CANNOT update imports automatically**

### 1.2 Available Tools in Refactoring Phase

**Location**: `pipeline/phases/refactoring.py` and handlers

```python
# Current refactoring phase tools:
- detect_duplicate_implementations()
- compare_file_implementations(file1, file2)
- merge_file_implementations(source_file, target_file, strategy)
- cleanup_redundant_files(files_to_remove, reason)
- create_issue_report(task_id, severity, impact_analysis, ...)
- request_developer_review(task_id, questions, context)
- update_refactoring_task(task_id, status, notes)
```

**Analysis**:
- ✅ Can detect duplicates
- ✅ Can compare files
- ✅ Can merge implementations
- ✅ Can delete redundant files
- ❌ **CANNOT move/rename files**
- ❌ **CANNOT restructure directories**
- ❌ **CANNOT update imports automatically**

---

## 2. CRITICAL GAPS IDENTIFIED

### 2.1 Missing File Operation Capabilities

#### Gap 1: No Move/Rename Capability
**Problem**: Neither phase can move or rename files.

**Impact**:
- Cannot reorganize code into proper directory structure
- Cannot fix misplaced files
- Cannot implement architectural changes requiring file moves
- Cannot rename files to match conventions

**Example Scenario**:
```
Current: app/utils/database.py
Desired: app/storage/database.py

Current tools: Can only delete old file and create new file
Problem: Loses git history, breaks imports, requires manual import updates
```

#### Gap 2: No Import Update Capability
**Problem**: When files are moved/renamed, imports are not automatically updated.

**Impact**:
- Moving files breaks all imports
- Manual import updates required
- High risk of missing imports
- Code becomes non-functional after refactoring

**Example Scenario**:
```python
# Before move:
from app.utils.database import Database

# After moving app/utils/database.py -> app/storage/database.py
# Import is now broken, but no tool to fix it
```

#### Gap 3: No Directory Restructuring
**Problem**: Cannot create/reorganize directory structures.

**Impact**:
- Cannot implement architectural changes
- Cannot organize code by feature/module
- Cannot fix flat directory structures
- Cannot implement proper separation of concerns

**Example Scenario**:
```
Current structure:
app/
  file1.py
  file2.py
  file3.py

Desired structure:
app/
  models/
    file1.py
  services/
    file2.py
  utils/
    file3.py

Current tools: Cannot achieve this restructuring
```

---

## 3. CONTEXT AND REASONING CAPABILITIES

### 3.1 Current Context Available to Phases

#### Coding Phase Context
**Location**: `pipeline/phases/coding.py:_build_context()`

```python
def _build_context(self, state: PipelineState, task: TaskState) -> str:
    context_parts = []
    
    # 1. Strategic documents
    - MASTER_PLAN.md
    - ARCHITECTURE.md
    - ROADMAP.md
    
    # 2. Task information
    - Task description
    - Target file
    - Dependencies
    
    # 3. Error history
    - Previous attempts
    - Error messages
    - Code snippets
    
    # 4. Existing code
    - Current file content (if exists)
    - Related files (limited)
    
    # 5. IPC documents
    - DEVELOPER_READ.md
    - Phase outputs
```

**Missing Context**:
- ❌ Import graph (who imports this file?)
- ❌ Dependency graph (what does this file import?)
- ❌ File relationships (related files, tests, etc.)
- ❌ Directory structure overview
- ❌ Architectural constraints (where files should be)

#### Refactoring Phase Context
**Location**: `pipeline/phases/refactoring.py:_build_task_context()`

Uses `RefactoringContextBuilder` which provides:

```python
# Context includes:
1. Strategic documents (MASTER_PLAN, ARCHITECTURE, ROADMAP)
2. Analysis reports (dead code, complexity, bugs, integration gaps)
3. Code context (target files, related files, tests)
4. Project state (phase, completion, recent changes)
5. Issue-specific data (duplicates, conflicts, etc.)
```

**Missing Context**:
- ❌ Import graph (comprehensive view)
- ❌ Full dependency analysis
- ❌ Impact analysis (what breaks if we move this?)
- ❌ Architectural placement rules
- ❌ Convention-based file naming/placement

### 3.2 Reasoning Capabilities

#### Current Reasoning
Both phases can reason about:
- ✅ Code functionality
- ✅ Duplicate detection
- ✅ Code quality issues
- ✅ Architectural violations (basic)
- ✅ Error patterns

#### Missing Reasoning
Neither phase can reason about:
- ❌ Optimal file placement based on architecture
- ❌ Import impact of file moves
- ❌ Directory structure optimization
- ❌ Convention-based file organization
- ❌ Dependency-aware refactoring

---

## 4. IMPORT RELATIONSHIP ANALYSIS

### 4.1 Current Import Tracking

**No systematic import tracking exists.**

The system does not maintain:
- Import graph (who imports what)
- Reverse import graph (who imports this file)
- Dependency chains
- Circular dependency detection
- Import impact analysis

### 4.2 Required Import Analysis

To safely move/rename files, the system needs:

#### 4.2.1 Import Graph Builder
```python
class ImportGraphBuilder:
    def build_import_graph(self, project_dir: Path) -> ImportGraph:
        """
        Build complete import graph for project.
        
        Returns:
            ImportGraph with:
            - file -> [files it imports]
            - file -> [files that import it]
            - circular dependencies
            - external dependencies
        """
```

#### 4.2.2 Import Impact Analyzer
```python
class ImportImpactAnalyzer:
    def analyze_move_impact(self, old_path: str, new_path: str) -> ImpactReport:
        """
        Analyze impact of moving a file.
        
        Returns:
            ImpactReport with:
            - Files that need import updates
            - Specific import statements to change
            - Risk assessment
            - Suggested changes
        """
```

#### 4.2.3 Import Updater
```python
class ImportUpdater:
    def update_imports_for_move(self, old_path: str, new_path: str) -> List[FileUpdate]:
        """
        Generate import updates for file move.
        
        Returns:
            List of FileUpdate objects with:
            - File to update
            - Old import statement
            - New import statement
            - Line number
        """
```

---

## 5. PROPOSED SOLUTION: NEW TOOLS

### 5.1 File Operation Tools

#### Tool 1: move_file
```python
def move_file(
    source_path: str,
    destination_path: str,
    update_imports: bool = True,
    create_directories: bool = True,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Move a file to a new location and optionally update all imports.
    
    Args:
        source_path: Current file path (relative to project root)
        destination_path: New file path (relative to project root)
        update_imports: If True, automatically update all imports
        create_directories: If True, create destination directories
        reason: Explanation for the move
        
    Returns:
        {
            "success": bool,
            "files_updated": List[str],  # Files with updated imports
            "import_changes": List[Dict],  # Specific import changes made
            "warnings": List[str],  # Any warnings or issues
            "git_history_preserved": bool
        }
        
    Process:
        1. Validate source file exists
        2. Build import graph
        3. Analyze impact of move
        4. Create destination directories if needed
        5. Move file using git mv (preserves history)
        6. Update all imports in other files
        7. Verify no broken imports
        8. Return detailed report
    """
```

#### Tool 2: rename_file
```python
def rename_file(
    file_path: str,
    new_name: str,
    update_imports: bool = True,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Rename a file and optionally update all imports.
    
    Similar to move_file but keeps file in same directory.
    """
```

#### Tool 3: restructure_directory
```python
def restructure_directory(
    restructuring_plan: Dict[str, str],
    update_imports: bool = True,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Restructure multiple files according to a plan.
    
    Args:
        restructuring_plan: Dict mapping old paths to new paths
        update_imports: If True, automatically update all imports
        reason: Explanation for the restructuring
        
    Returns:
        {
            "success": bool,
            "files_moved": int,
            "files_updated": List[str],
            "import_changes": List[Dict],
            "warnings": List[str]
        }
        
    Process:
        1. Validate all source files exist
        2. Build complete import graph
        3. Analyze impact of all moves
        4. Create all destination directories
        5. Move all files (in dependency order)
        6. Update all imports
        7. Verify no broken imports
        8. Return detailed report
    """
```

#### Tool 4: analyze_file_placement
```python
def analyze_file_placement(
    file_path: str,
    architecture_rules: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Analyze if a file is in the correct location according to architecture.
    
    Args:
        file_path: File to analyze
        architecture_rules: Optional custom rules (uses ARCHITECTURE.md if None)
        
    Returns:
        {
            "current_location": str,
            "suggested_location": str,
            "reason": str,
            "confidence": float,
            "architectural_violations": List[str],
            "import_impact": Dict,
            "related_files": List[str]
        }
        
    Process:
        1. Parse ARCHITECTURE.md for placement rules
        2. Analyze file content (models, services, utils, etc.)
        3. Check import patterns
        4. Check related files
        5. Suggest optimal location
        6. Analyze impact of move
    """
```

### 5.2 Import Analysis Tools

#### Tool 5: build_import_graph
```python
def build_import_graph(
    scope: str = "project"
) -> Dict[str, Any]:
    """
    Build complete import graph for the project.
    
    Args:
        scope: "project" or specific directory
        
    Returns:
        {
            "nodes": List[str],  # All files
            "edges": List[Tuple[str, str]],  # Import relationships
            "reverse_edges": Dict[str, List[str]],  # Who imports this file
            "circular_dependencies": List[List[str]],
            "external_dependencies": Dict[str, List[str]],
            "orphaned_files": List[str]  # Files not imported by anyone
        }
    """
```

#### Tool 6: analyze_import_impact
```python
def analyze_import_impact(
    file_path: str,
    new_path: Optional[str] = None,
    operation: str = "move"
) -> Dict[str, Any]:
    """
    Analyze the impact of moving, renaming, or deleting a file.
    
    Args:
        file_path: File to analyze
        new_path: New path (for move/rename)
        operation: "move", "rename", or "delete"
        
    Returns:
        {
            "affected_files": List[str],
            "import_changes_needed": List[Dict],
            "risk_level": str,  # "low", "medium", "high"
            "circular_dependency_risk": bool,
            "test_files_affected": List[str],
            "estimated_changes": int
        }
    """
```

---

## 6. ENHANCED CONTEXT SYSTEM

### 6.1 Architectural Context Provider

```python
class ArchitecturalContextProvider:
    """
    Provides architectural context for file placement decisions.
    """
    
    def get_placement_rules(self) -> Dict[str, Any]:
        """
        Parse ARCHITECTURE.md and extract file placement rules.
        
        Returns:
            {
                "models": {"location": "app/models/", "pattern": "*_model.py"},
                "services": {"location": "app/services/", "pattern": "*_service.py"},
                "utils": {"location": "app/utils/", "pattern": "*.py"},
                "tests": {"location": "tests/", "pattern": "test_*.py"},
                ...
            }
        """
    
    def suggest_file_location(self, file_content: str, file_name: str) -> str:
        """
        Suggest optimal location for a file based on its content.
        
        Analyzes:
        - Class types (Model, Service, Controller, etc.)
        - Import patterns
        - Function signatures
        - Naming conventions
        
        Returns suggested path.
        """
    
    def validate_file_location(self, file_path: str) -> Dict[str, Any]:
        """
        Validate if a file is in the correct location.
        
        Returns:
            {
                "valid": bool,
                "violations": List[str],
                "suggested_location": str,
                "reason": str
            }
        """
```

### 6.2 Import Context Provider

```python
class ImportContextProvider:
    """
    Provides import relationship context.
    """
    
    def get_file_imports(self, file_path: str) -> List[str]:
        """Get all files imported by this file."""
    
    def get_file_importers(self, file_path: str) -> List[str]:
        """Get all files that import this file."""
    
    def get_import_chain(self, file_path: str, depth: int = 3) -> Dict:
        """Get full import chain up to specified depth."""
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect all circular dependencies in project."""
    
    def get_import_distance(self, file1: str, file2: str) -> int:
        """Calculate import distance between two files."""
```

### 6.3 Dependency Context Provider

```python
class DependencyContextProvider:
    """
    Provides dependency relationship context.
    """
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Get all dependencies for a file.
        
        Returns:
            {
                "direct_imports": List[str],
                "indirect_imports": List[str],
                "external_packages": List[str],
                "test_files": List[str],
                "related_files": List[str]
            }
        """
    
    def analyze_dependency_health(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze dependency health.
        
        Returns:
            {
                "circular_dependencies": List[List[str]],
                "deep_import_chains": List[List[str]],
                "unused_imports": List[str],
                "missing_imports": List[str]
            }
        """
```

---

## 7. INTEGRATION WITH EXISTING PHASES

### 7.1 Coding Phase Integration

**Location**: `pipeline/phases/coding.py`

**Changes Needed**:

```python
class CodingPhase(BasePhase, LoopDetectionMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ADD: Import analysis capabilities
        from ..analysis.imports import ImportGraphBuilder, ImportImpactAnalyzer
        self.import_graph_builder = ImportGraphBuilder(self.project_dir)
        self.import_impact_analyzer = ImportImpactAnalyzer(self.project_dir)
        
        # ADD: Architectural context
        from ..context.architectural import ArchitecturalContextProvider
        self.arch_context = ArchitecturalContextProvider(self.project_dir)
    
    def _build_context(self, state: PipelineState, task: TaskState) -> str:
        context = super()._build_context(state, task)
        
        # ADD: Import context
        if task.target_file:
            import_context = self._build_import_context(task.target_file)
            context += f"\n\n## Import Context\n{import_context}"
        
        # ADD: Architectural context
        arch_context = self._build_architectural_context(task.target_file)
        context += f"\n\n## Architectural Context\n{arch_context}"
        
        return context
    
    def _build_import_context(self, file_path: str) -> str:
        """Build import relationship context for a file."""
        if not Path(self.project_dir / file_path).exists():
            return "File does not exist yet."
        
        imports = self.import_graph_builder.get_file_imports(file_path)
        importers = self.import_graph_builder.get_file_importers(file_path)
        
        context = f"**Imports**: {len(imports)} files\n"
        for imp in imports[:10]:  # Limit to 10
            context += f"- {imp}\n"
        
        context += f"\n**Imported By**: {len(importers)} files\n"
        for imp in importers[:10]:  # Limit to 10
            context += f"- {imp}\n"
        
        return context
    
    def _build_architectural_context(self, file_path: str) -> str:
        """Build architectural context for file placement."""
        validation = self.arch_context.validate_file_location(file_path)
        
        if validation["valid"]:
            return f"✅ File is in correct location according to ARCHITECTURE.md"
        else:
            context = f"⚠️ File location issues:\n"
            for violation in validation["violations"]:
                context += f"- {violation}\n"
            context += f"\n**Suggested Location**: {validation['suggested_location']}\n"
            context += f"**Reason**: {validation['reason']}\n"
            return context
```

### 7.2 Refactoring Phase Integration

**Location**: `pipeline/phases/refactoring.py`

**Changes Needed**:

```python
class RefactoringPhase(BasePhase, LoopDetectionMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ADD: Import analysis capabilities
        from ..analysis.imports import ImportGraphBuilder, ImportImpactAnalyzer, ImportUpdater
        self.import_graph_builder = ImportGraphBuilder(self.project_dir)
        self.import_impact_analyzer = ImportImpactAnalyzer(self.project_dir)
        self.import_updater = ImportUpdater(self.project_dir)
        
        # ADD: Architectural context
        from ..context.architectural import ArchitecturalContextProvider
        self.arch_context = ArchitecturalContextProvider(self.project_dir)
        
        # ADD: File placement analyzer
        from ..analysis.file_placement import FilePlacementAnalyzer
        self.placement_analyzer = FilePlacementAnalyzer(
            self.project_dir, 
            self.logger,
            self.arch_context
        )
    
    def _analyze_and_create_tasks(self, state: PipelineState) -> PhaseResult:
        """Enhanced analysis including file placement."""
        
        # Existing analysis
        result = super()._analyze_and_create_tasks(state)
        
        # ADD: File placement analysis
        misplaced_files = self.placement_analyzer.find_misplaced_files()
        
        if misplaced_files:
            self.logger.info(f"  📁 Found {len(misplaced_files)} misplaced files")
            
            for file_info in misplaced_files:
                task = state.refactoring_manager.create_task(
                    issue_type=RefactoringIssueType.MISPLACED_FILE,
                    title=f"File in wrong location: {file_info['file']}",
                    description=f"File should be moved from {file_info['current']} to {file_info['suggested']}",
                    target_files=[file_info['file']],
                    priority=RefactoringPriority.MEDIUM,
                    analysis_data={
                        "current_location": file_info['current'],
                        "suggested_location": file_info['suggested'],
                        "reason": file_info['reason'],
                        "import_impact": file_info['import_impact']
                    }
                )
        
        return result
```

---

## 8. IMPLEMENTATION PLAN

### Phase 1: Import Analysis Infrastructure (Week 1)
1. Create `pipeline/analysis/imports.py`
   - ImportGraphBuilder
   - ImportImpactAnalyzer
   - ImportUpdater

2. Create `pipeline/context/architectural.py`
   - ArchitecturalContextProvider
   - File placement rules parser

3. Create `pipeline/analysis/file_placement.py`
   - FilePlacementAnalyzer
   - Misplaced file detector

### Phase 2: New Tools (Week 2)
1. Create `pipeline/tools/file_operations.py`
   - move_file
   - rename_file
   - restructure_directory
   - analyze_file_placement

2. Create `pipeline/tools/import_operations.py`
   - build_import_graph
   - analyze_import_impact
   - update_imports

3. Register tools in tool registry

### Phase 3: Phase Integration (Week 3)
1. Update CodingPhase
   - Add import context
   - Add architectural context
   - Update prompts

2. Update RefactoringPhase
   - Add file placement analysis
   - Add import impact analysis
   - Update task creation

3. Update prompts to guide AI on using new tools

### Phase 4: Testing & Validation (Week 4)
1. Unit tests for all new components
2. Integration tests for file moves
3. Import update verification
4. End-to-end refactoring tests

---

## 9. RISK ANALYSIS

### 9.1 Risks of Current System

**HIGH RISK**: Without these capabilities:
- ❌ Cannot safely reorganize code
- ❌ File moves break imports
- ❌ Manual import updates error-prone
- ❌ Architectural violations persist
- ❌ Technical debt accumulates

### 9.2 Risks of New System

**MEDIUM RISK**: With new capabilities:
- ⚠️ Import updates might miss edge cases
- ⚠️ Complex import patterns might break
- ⚠️ Git history might be lost if not using git mv
- ⚠️ Circular dependencies might cause issues

**MITIGATION**:
- Comprehensive testing
- Dry-run mode for all operations
- Backup before major refactoring
- Validation after all changes
- Developer review for complex moves

---

## 10. CONCLUSION

### Current State: ❌ INSUFFICIENT

The coding and refactoring phases **CANNOT** safely:
- Move or rename files
- Restructure directories
- Update imports automatically
- Reason about file placement
- Analyze import impact

### Required Enhancements: 🎯 CRITICAL

To enable proper file operations and refactoring:

1. **Import Analysis System** (CRITICAL)
   - Build import graphs
   - Analyze impact
   - Update imports automatically

2. **File Operation Tools** (CRITICAL)
   - move_file with import updates
   - rename_file with import updates
   - restructure_directory

3. **Architectural Context** (HIGH)
   - Parse placement rules
   - Validate file locations
   - Suggest optimal placement

4. **Enhanced Phase Context** (HIGH)
   - Import relationships
   - Dependency analysis
   - Architectural constraints

### Implementation Priority: 🚀 HIGH

These capabilities are essential for:
- Safe code refactoring
- Architectural improvements
- Technical debt reduction
- Code organization
- Maintainability

**Recommendation**: Implement in 4-week sprint as outlined above.

---

**Analysis Complete**: 2024-12-31  
**Analyst**: SuperNinja AI Agent  
**Status**: Critical gaps identified, implementation plan provided