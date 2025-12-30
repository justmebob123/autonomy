# Deep Analysis: Architecture Refactoring & File Reconciliation Capabilities

## Executive Summary

After comprehensive analysis of the autonomy pipeline, I've identified that **the system LACKS a dedicated architecture refactoring and file reconciliation capability**. While it has excellent analysis tools, it does NOT have the ability to:

1. ❌ Detect when MASTER_PLAN.md changes require architecture refactoring
2. ❌ Compare duplicate/conflicting files and merge them intelligently
3. ❌ Automatically reconcile files that don't match the architecture
4. ❌ Use AI to merge features from equivalent files
5. ❌ Remove incorrect files after successful reconciliation

---

## Current State Analysis

### What EXISTS ✅

#### 1. Analysis Tools (Excellent)
- **Integration Gap Detector** (`pipeline/analysis/integration_gaps.py`)
  - Finds unused classes
  - Detects classes with unused methods
  - Identifies imported but unused code
  
- **Integration Conflict Detector** (`pipeline/analysis/integration_conflicts.py`)
  - Detects duplicate implementations
  - Finds naming inconsistencies
  - Identifies feature overlap
  
- **Dead Code Detector**
  - Finds unused functions and methods
  
- **Complexity Analyzer**
  - Identifies high-complexity code needing refactoring

#### 2. Polytopic Structure (7 Primary Phases)
```python
PRIMARY_PHASES = {
    'planning',           # Creates tasks from MASTER_PLAN.md
    'coding',            # Implements tasks
    'qa',                # Reviews code
    'debugging',         # Fixes issues
    'investigation',     # Analyzes problems
    'project_planning',  # Expands project
    'documentation'      # Updates docs
}
```

#### 3. Specialized Phases (On-Demand)
```python
SPECIALIZED_PHASES = {
    'tool_design',        # Creates new tools
    'prompt_design',      # Designs prompts
    'role_design',        # Designs roles
    'prompt_improvement', # Improves prompts
    'role_improvement',   # Improves roles
    'tool_evaluation'     # Evaluates tools
}
```

#### 4. File Operations
- Create files
- Modify files
- Delete files (but not used for reconciliation)
- Append to files
- Update sections

### What's MISSING ❌

#### 1. Architecture Change Detection
**Current**: Planning phase reads MASTER_PLAN.md and creates tasks
**Missing**: 
- No detection of MASTER_PLAN.md changes
- No comparison of new architecture vs existing files
- No identification of files that need refactoring
- No tracking of architecture evolution

#### 2. File Reconciliation Phase
**Current**: No dedicated phase for file reconciliation
**Missing**:
- No phase to handle duplicate/conflicting files
- No AI-powered file merging
- No feature extraction and combination
- No systematic file cleanup

#### 3. Duplicate File Handling
**Current**: Planning phase skips duplicate tasks
**Missing**:
- No detection of duplicate implementations in different files
- No comparison of similar files
- No merging of duplicate functionality
- No removal of redundant files

#### 4. Architecture Refactoring Tools
**Current**: Analysis tools detect issues
**Missing**:
- No tools to refactor architecture
- No tools to merge files
- No tools to extract features
- No tools to reconcile conflicts

#### 5. MASTER_PLAN Change Tracking
**Current**: Planning phase has `_should_update_master_plan()` but it's TODO
**Missing**:
- No tracking of MASTER_PLAN.md changes
- No diff analysis of architecture changes
- No impact analysis of changes
- No automated refactoring based on changes

---

## Detailed Gap Analysis

### Gap 1: No Architecture Change Detection

**Location**: `pipeline/phases/planning.py`

**Current Code**:
```python
def _should_update_master_plan(self, state: PipelineState) -> bool:
    """Check if 95% completion threshold reached for MASTER_PLAN update"""
    # TODO: Implement MASTER_PLAN update logic
    return False
```

**What's Missing**:
- No detection of MASTER_PLAN.md modifications
- No comparison of old vs new architecture
- No identification of affected files
- No creation of refactoring tasks

**What's Needed**:
```python
def detect_architecture_changes(self, old_plan: str, new_plan: str) -> Dict:
    """
    Detect changes in MASTER_PLAN.md and identify impact.
    
    Returns:
        {
            'added_objectives': [...],
            'removed_objectives': [...],
            'modified_objectives': [...],
            'affected_files': [...],
            'refactoring_needed': bool
        }
    """
```

### Gap 2: No File Reconciliation Phase

**Current Phases**: 7 primary + 6 specialized = 13 total
**Missing**: Architecture Refactoring Phase

**What's Needed**:
```python
class ArchitectureRefactoringPhase(BasePhase):
    """
    Phase for reconciling files with architecture changes.
    
    Responsibilities:
    1. Detect duplicate/conflicting implementations
    2. Compare similar files and extract features
    3. Use AI to merge features intelligently
    4. Create reconciled file
    5. Remove old/incorrect files
    6. Update all references
    """
```

### Gap 3: No File Comparison & Merging Tools

**Current Tools**: 
- `create_python_file` - Creates new file
- `modify_python_file` - Modifies existing file
- `delete_file` - Deletes file (exists but not used for reconciliation)

**Missing Tools**:
```python
TOOLS_REFACTORING = [
    {
        "name": "compare_files",
        "description": "Compare two files and identify differences, similarities, and unique features"
    },
    {
        "name": "extract_features",
        "description": "Extract specific features/functions from a file"
    },
    {
        "name": "merge_files",
        "description": "Merge features from multiple files into one reconciled file"
    },
    {
        "name": "reconcile_architecture",
        "description": "Reconcile file with architecture requirements"
    },
    {
        "name": "remove_redundant_files",
        "description": "Remove files that have been successfully reconciled"
    }
]
```

### Gap 4: No Duplicate Detection in Coding Phase

**Current**: Coding phase creates files without checking for duplicates
**Missing**: 
- No detection of similar existing files
- No warning about potential duplicates
- No suggestion to merge instead of create

**What's Needed**:
```python
def detect_similar_files(self, target_file: str, task_description: str) -> List[str]:
    """
    Detect existing files that might be similar to the target file.
    
    Returns list of similar files that might need reconciliation.
    """
```

### Gap 5: No Integration Conflict Resolution

**Current**: Integration conflict detector finds conflicts
**Missing**: No automated resolution

**What's Needed**:
```python
def resolve_integration_conflict(self, conflict: IntegrationConflict) -> Dict:
    """
    Resolve an integration conflict by:
    1. Analyzing both implementations
    2. Extracting unique features from each
    3. Creating merged implementation
    4. Removing redundant files
    5. Updating references
    """
```

---

## Proposed Solution: Architecture Refactoring System

### Component 1: Architecture Change Detector

**File**: `pipeline/analysis/architecture_changes.py`

```python
class ArchitectureChangeDetector:
    """
    Detects changes in MASTER_PLAN.md and identifies impact.
    """
    
    def detect_changes(self, old_plan: str, new_plan: str) -> ArchitectureChanges:
        """
        Compare old and new MASTER_PLAN.md.
        
        Returns:
            ArchitectureChanges with:
            - Added objectives
            - Removed objectives
            - Modified objectives
            - Affected files
            - Refactoring tasks
        """
    
    def identify_affected_files(self, changes: ArchitectureChanges) -> List[str]:
        """
        Identify files affected by architecture changes.
        """
    
    def generate_refactoring_tasks(self, changes: ArchitectureChanges) -> List[Task]:
        """
        Generate tasks to refactor architecture.
        """
```

### Component 2: File Reconciliation Phase

**File**: `pipeline/phases/architecture_refactoring.py`

```python
class ArchitectureRefactoringPhase(BasePhase):
    """
    Phase for reconciling files with architecture changes.
    """
    
    def execute(self, state: PipelineState):
        """
        Main execution:
        1. Detect architecture changes
        2. Find duplicate/conflicting files
        3. Compare and analyze files
        4. Use AI to merge features
        5. Create reconciled files
        6. Remove old files
        7. Update references
        """
    
    def find_duplicate_implementations(self) -> List[DuplicateSet]:
        """
        Find sets of files with duplicate implementations.
        """
    
    def compare_files(self, file1: str, file2: str) -> FileComparison:
        """
        Compare two files and identify:
        - Common features
        - Unique features in file1
        - Unique features in file2
        - Conflicts
        """
    
    def merge_files_with_ai(self, files: List[str], target: str) -> str:
        """
        Use AI to intelligently merge features from multiple files.
        """
    
    def remove_reconciled_files(self, files: List[str]):
        """
        Remove files that have been successfully reconciled.
        """
```

### Component 3: Refactoring Tools

**File**: `pipeline/tools.py` (additions)

```python
TOOLS_REFACTORING = [
    {
        "type": "function",
        "function": {
            "name": "detect_architecture_changes",
            "description": "Detect changes in MASTER_PLAN.md and identify affected files",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_plan_path": {"type": "string"},
                    "new_plan_path": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_duplicate_files",
            "description": "Find files with duplicate or similar implementations",
            "parameters": {
                "type": "object",
                "properties": {
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Similarity threshold (0.0-1.0)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_files",
            "description": "Compare two files and identify differences and similarities",
            "parameters": {
                "type": "object",
                "properties": {
                    "file1": {"type": "string"},
                    "file2": {"type": "string"}
                },
                "required": ["file1", "file2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "merge_files",
            "description": "Merge features from multiple files into one reconciled file",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_files": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "target_file": {"type": "string"},
                    "merge_strategy": {
                        "type": "string",
                        "enum": ["keep_all", "prefer_newer", "ai_merge"]
                    }
                },
                "required": ["source_files", "target_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_redundant_files",
            "description": "Remove files that have been successfully reconciled",
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "reason": {"type": "string"}
                },
                "required": ["files", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_features",
            "description": "Extract specific features/functions from a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string"},
                    "features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of function/class names to extract"
                    }
                },
                "required": ["source_file", "features"]
            }
        }
    }
]
```

### Component 4: Polytopic Integration

**File**: `pipeline/coordinator.py` (modifications)

```python
def _initialize_polytopic_structure(self):
    """Initialize hyperdimensional polytopic structure."""
    
    # PRIMARY PHASES (add architecture_refactoring)
    phase_types = {
        'planning': 'planning',
        'coding': 'execution',
        'qa': 'validation',
        'debugging': 'correction',
        'investigation': 'analysis',
        'project_planning': 'planning',
        'documentation': 'documentation',
        'architecture_refactoring': 'refactoring'  # NEW
    }
    
    # PRIMARY FLOW EDGES (add refactoring connections)
    self.polytope['edges'] = {
        'planning': ['coding', 'architecture_refactoring'],  # Can go to refactoring
        'coding': ['qa', 'documentation'],
        'qa': ['debugging', 'documentation', 'architecture_refactoring'],  # Can detect conflicts
        'debugging': ['investigation', 'coding'],
        'investigation': ['debugging', 'coding', 'architecture_refactoring'],  # Can recommend refactoring
        'documentation': ['planning', 'qa'],
        'project_planning': ['planning'],
        'architecture_refactoring': ['coding', 'qa']  # NEW - goes to coding or qa after refactoring
    }
```

### Component 5: Handlers

**File**: `pipeline/handlers.py` (additions)

```python
def _handle_detect_architecture_changes(self, args: Dict) -> Dict:
    """Handle detect_architecture_changes tool."""
    from pipeline.analysis.architecture_changes import ArchitectureChangeDetector
    
    detector = ArchitectureChangeDetector(self.project_dir, self.logger)
    changes = detector.detect_changes(
        args.get('old_plan_path'),
        args.get('new_plan_path')
    )
    
    return {
        'tool': 'detect_architecture_changes',
        'success': True,
        'changes': changes.to_dict()
    }

def _handle_find_duplicate_files(self, args: Dict) -> Dict:
    """Handle find_duplicate_files tool."""
    from pipeline.analysis.file_similarity import FileSimilarityDetector
    
    detector = FileSimilarityDetector(self.project_dir, self.logger)
    duplicates = detector.find_duplicates(
        threshold=args.get('similarity_threshold', 0.8)
    )
    
    return {
        'tool': 'find_duplicate_files',
        'success': True,
        'duplicates': [d.to_dict() for d in duplicates]
    }

def _handle_compare_files(self, args: Dict) -> Dict:
    """Handle compare_files tool."""
    from pipeline.analysis.file_comparison import FileComparator
    
    comparator = FileComparator(self.project_dir, self.logger)
    comparison = comparator.compare(
        args['file1'],
        args['file2']
    )
    
    return {
        'tool': 'compare_files',
        'success': True,
        'comparison': comparison.to_dict()
    }

def _handle_merge_files(self, args: Dict) -> Dict:
    """Handle merge_files tool."""
    from pipeline.refactoring.file_merger import FileMerger
    
    merger = FileMerger(self.project_dir, self.logger, self.config)
    result = merger.merge(
        source_files=args['source_files'],
        target_file=args['target_file'],
        strategy=args.get('merge_strategy', 'ai_merge')
    )
    
    return {
        'tool': 'merge_files',
        'success': result.success,
        'merged_file': result.merged_file,
        'conflicts': result.conflicts
    }

def _handle_remove_redundant_files(self, args: Dict) -> Dict:
    """Handle remove_redundant_files tool."""
    files = args['files']
    reason = args['reason']
    
    removed = []
    for file in files:
        file_path = self.project_dir / file
        if file_path.exists():
            file_path.unlink()
            removed.append(file)
            self.logger.info(f"  🗑️  Removed redundant file: {file} ({reason})")
    
    return {
        'tool': 'remove_redundant_files',
        'success': True,
        'removed': removed,
        'reason': reason
    }

def _handle_extract_features(self, args: Dict) -> Dict:
    """Handle extract_features tool."""
    from pipeline.refactoring.feature_extractor import FeatureExtractor
    
    extractor = FeatureExtractor(self.project_dir, self.logger)
    features = extractor.extract(
        source_file=args['source_file'],
        feature_names=args['features']
    )
    
    return {
        'tool': 'extract_features',
        'success': True,
        'features': features
    }
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Create `ArchitectureChangeDetector` class
2. Create `FileSimilarityDetector` class
3. Create `FileComparator` class
4. Add refactoring tools to `pipeline/tools.py`
5. Add handlers to `pipeline/handlers.py`

### Phase 2: Core Refactoring (Week 2)
1. Create `ArchitectureRefactoringPhase` class
2. Implement file merging logic
3. Implement feature extraction
4. Add to polytopic structure
5. Test with simple cases

### Phase 3: AI Integration (Week 3)
1. Create prompts for file comparison
2. Create prompts for feature merging
3. Implement AI-powered merge strategy
4. Test with complex cases

### Phase 4: Integration (Week 4)
1. Integrate with planning phase
2. Integrate with investigation phase
3. Add MASTER_PLAN change tracking
4. Add automatic refactoring triggers
5. Comprehensive testing

---

## Example Workflow

### Scenario: User Updates MASTER_PLAN.md

**Step 1: Detection**
```
Planning Phase:
  - Detects MASTER_PLAN.md has changed
  - Calls detect_architecture_changes tool
  - Identifies affected files: [auth.py, user_manager.py]
  - Creates refactoring task
```

**Step 2: Analysis**
```
Architecture Refactoring Phase:
  - Calls find_duplicate_files tool
  - Finds: auth.py and user_manager.py have duplicate login logic
  - Calls compare_files tool
  - Identifies:
    * auth.py has: login(), logout(), validate_token()
    * user_manager.py has: user_login(), user_logout(), check_session()
    * Duplicate: login logic in both files
```

**Step 3: Merging**
```
Architecture Refactoring Phase:
  - Calls merge_files tool with strategy='ai_merge'
  - AI analyzes both files
  - AI extracts unique features:
    * From auth.py: validate_token()
    * From user_manager.py: check_session()
  - AI creates merged auth_service.py with:
    * login() (merged from both)
    * logout() (merged from both)
    * validate_token() (from auth.py)
    * check_session() (from user_manager.py)
```

**Step 4: Cleanup**
```
Architecture Refactoring Phase:
  - Calls remove_redundant_files tool
  - Removes: auth.py, user_manager.py
  - Updates all imports to use auth_service.py
  - Creates task to update tests
```

**Step 5: Verification**
```
QA Phase:
  - Reviews merged file
  - Checks all features present
  - Verifies no regressions
  - Approves or sends to debugging
```

---

## Conclusion

The autonomy pipeline currently **LACKS** a dedicated architecture refactoring and file reconciliation system. While it has excellent analysis tools to detect issues, it cannot:

1. ❌ Automatically detect MASTER_PLAN.md changes
2. ❌ Compare and merge duplicate files
3. ❌ Use AI to intelligently combine features
4. ❌ Remove redundant files after reconciliation
5. ❌ Refactor architecture based on changes

**Recommendation**: Implement the proposed Architecture Refactoring System as a new phase in the polytopic structure with dedicated tools and handlers.

**Estimated Effort**: 4 weeks for complete implementation
**Priority**: HIGH - This is a critical capability for maintaining architecture consistency