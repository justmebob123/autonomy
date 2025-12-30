# Architecture Refactoring System - Implementation Plan

## Overview

This document provides a detailed implementation plan for adding architecture refactoring and file reconciliation capabilities to the autonomy pipeline.

---

## Phase 1: Foundation Components (Week 1)

### 1.1 Architecture Change Detector

**File**: `pipeline/analysis/architecture_changes.py`

**Classes**:
```python
@dataclass
class ObjectiveChange:
    """Represents a change to an objective."""
    change_type: str  # 'added', 'removed', 'modified'
    objective_id: str
    old_content: Optional[str]
    new_content: Optional[str]
    affected_files: List[str]

@dataclass
class ArchitectureChanges:
    """Result of architecture change detection."""
    added_objectives: List[ObjectiveChange]
    removed_objectives: List[ObjectiveChange]
    modified_objectives: List[ObjectiveChange]
    affected_files: Set[str]
    refactoring_needed: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""

class ArchitectureChangeDetector:
    """Detects changes in MASTER_PLAN.md."""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = project_dir
        self.logger = logger
        self.master_plan_path = project_dir / 'MASTER_PLAN.md'
        self.history_path = project_dir / '.autonomy' / 'master_plan_history.json'
    
    def detect_changes(self) -> ArchitectureChanges:
        """
        Detect changes in MASTER_PLAN.md since last run.
        
        Algorithm:
        1. Load current MASTER_PLAN.md
        2. Load previous version from history
        3. Parse both into objectives
        4. Compare objectives
        5. Identify affected files
        6. Return ArchitectureChanges
        """
    
    def parse_master_plan(self, content: str) -> Dict[str, Dict]:
        """
        Parse MASTER_PLAN.md into structured objectives.
        
        Returns:
            {
                'objective_id': {
                    'title': str,
                    'description': str,
                    'type': 'primary'|'secondary'|'tertiary',
                    'files': List[str]
                }
            }
        """
    
    def compare_objectives(self, old: Dict, new: Dict) -> ArchitectureChanges:
        """Compare old and new objectives."""
    
    def identify_affected_files(self, changes: ArchitectureChanges) -> Set[str]:
        """Identify files affected by changes."""
    
    def save_current_version(self):
        """Save current MASTER_PLAN.md to history."""
```

**Implementation Details**:
- Use regex to parse MASTER_PLAN.md sections
- Store history in JSON format
- Use difflib for text comparison
- Track file mentions in objectives

### 1.2 File Similarity Detector

**File**: `pipeline/analysis/file_similarity.py`

**Classes**:
```python
@dataclass
class FileSimilarity:
    """Represents similarity between two files."""
    file1: str
    file2: str
    similarity_score: float  # 0.0 to 1.0
    common_functions: List[str]
    common_classes: List[str]
    unique_to_file1: List[str]
    unique_to_file2: List[str]

@dataclass
class DuplicateSet:
    """A set of duplicate/similar files."""
    files: List[str]
    similarity_scores: Dict[Tuple[str, str], float]
    common_features: List[str]
    merge_recommended: bool
    merge_strategy: str

class FileSimilarityDetector:
    """Detects similar and duplicate files."""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = project_dir
        self.logger = logger
    
    def find_duplicates(self, threshold: float = 0.8) -> List[DuplicateSet]:
        """
        Find sets of duplicate/similar files.
        
        Algorithm:
        1. Get all Python files
        2. Parse each file into AST
        3. Extract features (functions, classes, imports)
        4. Compare all pairs of files
        5. Group similar files into sets
        6. Return DuplicateSets
        """
    
    def compare_files(self, file1: str, file2: str) -> FileSimilarity:
        """Compare two files and calculate similarity."""
    
    def extract_features(self, filepath: str) -> Dict:
        """
        Extract features from a file.
        
        Returns:
            {
                'functions': List[str],
                'classes': List[str],
                'imports': List[str],
                'docstrings': List[str]
            }
        """
    
    def calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Calculate similarity score between two feature sets.
        
        Uses Jaccard similarity:
        similarity = |A ∩ B| / |A ∪ B|
        """
    
    def group_similar_files(self, similarities: List[FileSimilarity], 
                           threshold: float) -> List[DuplicateSet]:
        """Group similar files into duplicate sets."""
```

**Implementation Details**:
- Use AST parsing for feature extraction
- Use Jaccard similarity for comparison
- Use graph clustering for grouping
- Consider function signatures, not just names

### 1.3 File Comparator

**File**: `pipeline/analysis/file_comparison.py`

**Classes**:
```python
@dataclass
class FeatureComparison:
    """Comparison of a specific feature."""
    feature_type: str  # 'function', 'class', 'import'
    name: str
    in_file1: bool
    in_file2: bool
    implementation_differs: bool
    file1_code: Optional[str]
    file2_code: Optional[str]
    recommendation: str

@dataclass
class FileComparison:
    """Detailed comparison of two files."""
    file1: str
    file2: str
    similarity_score: float
    common_features: List[FeatureComparison]
    unique_to_file1: List[FeatureComparison]
    unique_to_file2: List[FeatureComparison]
    conflicts: List[FeatureComparison]
    merge_strategy: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""

class FileComparator:
    """Compares two files in detail."""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = project_dir
        self.logger = logger
    
    def compare(self, file1: str, file2: str) -> FileComparison:
        """
        Compare two files in detail.
        
        Algorithm:
        1. Parse both files into AST
        2. Extract all features
        3. Compare each feature
        4. Identify common, unique, and conflicting features
        5. Recommend merge strategy
        6. Return FileComparison
        """
    
    def compare_functions(self, func1: ast.FunctionDef, 
                         func2: ast.FunctionDef) -> FeatureComparison:
        """Compare two function definitions."""
    
    def compare_classes(self, class1: ast.ClassDef, 
                       class2: ast.ClassDef) -> FeatureComparison:
        """Compare two class definitions."""
    
    def recommend_merge_strategy(self, comparison: FileComparison) -> str:
        """
        Recommend merge strategy based on comparison.
        
        Strategies:
        - 'keep_file1': File1 is superset
        - 'keep_file2': File2 is superset
        - 'merge_simple': No conflicts, simple merge
        - 'merge_ai': Conflicts exist, need AI
        """
```

**Implementation Details**:
- Use AST comparison for accuracy
- Use difflib for code comparison
- Consider function signatures and docstrings
- Detect semantic equivalence

### 1.4 Tool Definitions

**File**: `pipeline/tools.py` (additions)

Add `TOOLS_REFACTORING` list with 6 tools:
1. `detect_architecture_changes`
2. `find_duplicate_files`
3. `compare_files`
4. `merge_files`
5. `remove_redundant_files`
6. `extract_features`

### 1.5 Tool Handlers

**File**: `pipeline/handlers.py` (additions)

Add 6 handler methods:
1. `_handle_detect_architecture_changes()`
2. `_handle_find_duplicate_files()`
3. `_handle_compare_files()`
4. `_handle_merge_files()`
5. `_handle_remove_redundant_files()`
6. `_handle_extract_features()`

**Testing**:
- Unit tests for each component
- Integration tests for tool handlers
- Test with sample duplicate files

---

## Phase 2: Core Refactoring Phase (Week 2)

### 2.1 Architecture Refactoring Phase

**File**: `pipeline/phases/architecture_refactoring.py`

**Class**:
```python
class ArchitectureRefactoringPhase(BasePhase):
    """
    Phase for reconciling files with architecture changes.
    
    This phase is activated when:
    1. MASTER_PLAN.md changes detected
    2. Duplicate files detected by QA
    3. Integration conflicts found
    4. Investigation phase recommends refactoring
    """
    
    def __init__(self, config, state_manager, logger):
        super().__init__(config, state_manager, logger, "architecture_refactoring")
        
        # Initialize detectors
        self.change_detector = ArchitectureChangeDetector(self.project_dir, logger)
        self.similarity_detector = FileSimilarityDetector(self.project_dir, logger)
        self.file_comparator = FileComparator(self.project_dir, logger)
        
        # Initialize refactoring components
        self.feature_extractor = FeatureExtractor(self.project_dir, logger)
        self.file_merger = FileMerger(self.project_dir, logger, config)
    
    def execute(self, state: PipelineState):
        """
        Main execution flow:
        
        1. Detect what triggered refactoring
        2. Analyze scope of refactoring needed
        3. Create refactoring plan
        4. Execute refactoring with AI
        5. Verify results
        6. Clean up old files
        7. Update references
        """
        self.logger.info("=" * 60)
        self.logger.info("  ARCHITECTURE REFACTORING PHASE")
        self.logger.info("=" * 60)
        
        # Step 1: Detect trigger
        trigger = self._detect_refactoring_trigger(state)
        self.logger.info(f"  Refactoring triggered by: {trigger['type']}")
        
        # Step 2: Analyze scope
        scope = self._analyze_refactoring_scope(trigger)
        self.logger.info(f"  Scope: {len(scope['files'])} files affected")
        
        # Step 3: Create plan
        plan = self._create_refactoring_plan(scope)
        self.logger.info(f"  Plan: {len(plan['steps'])} steps")
        
        # Step 4: Execute with AI
        results = self._execute_refactoring_plan(plan, state)
        
        # Step 5: Verify
        verification = self._verify_refactoring(results)
        
        # Step 6: Clean up
        if verification['success']:
            self._cleanup_old_files(results)
        
        # Step 7: Update references
        self._update_references(results)
        
        return {
            'success': verification['success'],
            'files_merged': results['merged_files'],
            'files_removed': results['removed_files'],
            'next_phase': 'qa' if verification['success'] else 'debugging'
        }
    
    def _detect_refactoring_trigger(self, state: PipelineState) -> Dict:
        """
        Detect what triggered refactoring.
        
        Possible triggers:
        1. MASTER_PLAN.md changed
        2. Duplicate files detected
        3. Integration conflicts found
        4. Investigation recommendation
        """
    
    def _analyze_refactoring_scope(self, trigger: Dict) -> Dict:
        """
        Analyze scope of refactoring needed.
        
        Returns:
            {
                'files': List[str],
                'duplicate_sets': List[DuplicateSet],
                'conflicts': List[IntegrationConflict],
                'complexity': 'low'|'medium'|'high'
            }
        """
    
    def _create_refactoring_plan(self, scope: Dict) -> Dict:
        """
        Create refactoring plan.
        
        Returns:
            {
                'steps': [
                    {
                        'type': 'merge'|'extract'|'remove',
                        'files': List[str],
                        'target': str,
                        'strategy': str
                    }
                ]
            }
        """
    
    def _execute_refactoring_plan(self, plan: Dict, state: PipelineState) -> Dict:
        """
        Execute refactoring plan with AI assistance.
        
        For each step:
        1. Prepare context for AI
        2. Call AI with refactoring prompt
        3. Execute AI's recommendations
        4. Verify step completion
        """
    
    def _verify_refactoring(self, results: Dict) -> Dict:
        """
        Verify refactoring results.
        
        Checks:
        1. All features preserved
        2. No syntax errors
        3. No import errors
        4. Tests still pass (if any)
        """
    
    def _cleanup_old_files(self, results: Dict):
        """Remove old files after successful refactoring."""
    
    def _update_references(self, results: Dict):
        """Update all references to old files."""
```

### 2.2 Feature Extractor

**File**: `pipeline/refactoring/feature_extractor.py`

**Class**:
```python
class FeatureExtractor:
    """Extracts specific features from files."""
    
    def extract(self, source_file: str, feature_names: List[str]) -> Dict:
        """
        Extract specific features from a file.
        
        Returns:
            {
                'feature_name': {
                    'type': 'function'|'class',
                    'code': str,
                    'dependencies': List[str],
                    'docstring': str
                }
            }
        """
    
    def extract_with_dependencies(self, source_file: str, 
                                  feature_name: str) -> Dict:
        """Extract feature with all its dependencies."""
```

### 2.3 File Merger

**File**: `pipeline/refactoring/file_merger.py`

**Class**:
```python
class FileMerger:
    """Merges multiple files into one."""
    
    def merge(self, source_files: List[str], target_file: str, 
             strategy: str) -> MergeResult:
        """
        Merge multiple files into one.
        
        Strategies:
        - 'keep_all': Keep all features from all files
        - 'prefer_newer': Prefer features from newer files
        - 'ai_merge': Use AI to intelligently merge
        """
    
    def merge_with_ai(self, source_files: List[str], 
                     target_file: str) -> MergeResult:
        """
        Use AI to intelligently merge files.
        
        Algorithm:
        1. Compare all files
        2. Identify conflicts
        3. Prepare context for AI
        4. Call AI with merge prompt
        5. Execute AI's merge
        6. Verify result
        """
```

### 2.4 Polytopic Integration

**File**: `pipeline/coordinator.py` (modifications)

Add `architecture_refactoring` to polytopic structure:
- Add to `phase_types`
- Add edges from planning, qa, investigation
- Add edges to coding, qa

### 2.5 Phase Registration

**File**: `pipeline/phases/__init__.py` (modifications)

```python
from .architecture_refactoring import ArchitectureRefactoringPhase

__all__ = [
    # ... existing phases ...
    'ArchitectureRefactoringPhase'
]
```

**Testing**:
- Test with simple duplicate files
- Test with complex merge scenarios
- Test polytopic transitions

---

## Phase 3: AI Integration (Week 3)

### 3.1 Refactoring Prompts

**File**: `pipeline/prompts.py` (additions)

```python
def get_architecture_refactoring_prompt(context: Dict) -> str:
    """
    Generate prompt for architecture refactoring.
    
    Context includes:
    - Architecture changes
    - Duplicate files
    - File comparisons
    - Merge strategy
    """
    return f"""You are refactoring the project architecture.

ARCHITECTURE CHANGES:
{context['architecture_changes']}

DUPLICATE FILES DETECTED:
{context['duplicate_files']}

FILE COMPARISON:
{context['file_comparison']}

YOUR TASK:
1. Analyze the duplicate files
2. Identify unique features in each file
3. Create a merged file that combines all features
4. Ensure no functionality is lost
5. Remove redundant code
6. Maintain code quality

Use these tools:
- compare_files: Compare two files in detail
- extract_features: Extract specific features
- merge_files: Merge files with strategy
- remove_redundant_files: Remove old files

IMPORTANT:
- Preserve all unique functionality
- Maintain or improve code quality
- Update all imports and references
- Add comments explaining the merge
"""

def get_file_comparison_prompt(file1: str, file2: str, 
                               comparison: FileComparison) -> str:
    """Generate prompt for file comparison analysis."""
    
def get_merge_strategy_prompt(files: List[str], 
                              comparisons: List[FileComparison]) -> str:
    """Generate prompt for determining merge strategy."""
```

### 3.2 AI-Powered Merge Logic

**File**: `pipeline/refactoring/ai_merger.py`

**Class**:
```python
class AIMerger:
    """Uses AI to intelligently merge files."""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
    
    def merge_with_ai(self, files: List[str], 
                     comparisons: List[FileComparison],
                     target: str) -> MergeResult:
        """
        Use AI to merge files.
        
        Algorithm:
        1. Prepare comprehensive context
        2. Build conversation history
        3. Call AI with merge prompt
        4. Parse AI's response
        5. Execute merge operations
        6. Verify result
        """
    
    def prepare_merge_context(self, files: List[str], 
                             comparisons: List[FileComparison]) -> Dict:
        """Prepare context for AI merge."""
    
    def execute_ai_merge(self, ai_response: Dict, target: str) -> MergeResult:
        """Execute AI's merge instructions."""
```

### 3.3 Conflict Resolution

**File**: `pipeline/refactoring/conflict_resolver.py`

**Class**:
```python
class ConflictResolver:
    """Resolves conflicts during merging."""
    
    def resolve_conflicts(self, conflicts: List[FeatureComparison]) -> Dict:
        """
        Resolve conflicts using AI.
        
        For each conflict:
        1. Analyze both implementations
        2. Ask AI to choose or merge
        3. Verify resolution
        """
```

**Testing**:
- Test AI merge with simple cases
- Test AI merge with conflicts
- Test AI merge with complex dependencies

---

## Phase 4: Integration & Testing (Week 4)

### 4.1 Planning Phase Integration

**File**: `pipeline/phases/planning.py` (modifications)

```python
def execute(self, state: PipelineState):
    # ... existing code ...
    
    # NEW: Check for MASTER_PLAN changes
    if self._master_plan_changed():
        self.logger.info("  🔄 MASTER_PLAN.md changed - triggering refactoring")
        return {
            'success': True,
            'next_phase': 'architecture_refactoring',
            'reason': 'master_plan_changed'
        }
    
    # ... rest of existing code ...

def _master_plan_changed(self) -> bool:
    """Check if MASTER_PLAN.md has changed."""
    from ..analysis.architecture_changes import ArchitectureChangeDetector
    
    detector = ArchitectureChangeDetector(self.project_dir, self.logger)
    changes = detector.detect_changes()
    
    return changes.refactoring_needed
```

### 4.2 QA Phase Integration

**File**: `pipeline/phases/qa.py` (modifications)

```python
def execute(self, state: PipelineState):
    # ... existing code ...
    
    # NEW: Check for duplicate implementations
    duplicates = self._detect_duplicates()
    if duplicates:
        self.logger.warning(f"  ⚠️  Found {len(duplicates)} duplicate implementations")
        return {
            'success': True,
            'next_phase': 'architecture_refactoring',
            'reason': 'duplicates_detected',
            'duplicates': duplicates
        }
    
    # ... rest of existing code ...

def _detect_duplicates(self) -> List[DuplicateSet]:
    """Detect duplicate implementations."""
    from ..analysis.file_similarity import FileSimilarityDetector
    
    detector = FileSimilarityDetector(self.project_dir, self.logger)
    return detector.find_duplicates(threshold=0.8)
```

### 4.3 Investigation Phase Integration

**File**: `pipeline/phases/investigation.py` (modifications)

```python
def execute(self, state: PipelineState):
    # ... existing code ...
    
    # NEW: Check if refactoring recommended
    if self._should_recommend_refactoring(analysis_results):
        self.logger.info("  💡 Recommending architecture refactoring")
        return {
            'success': True,
            'next_phase': 'architecture_refactoring',
            'reason': 'refactoring_recommended'
        }
    
    # ... rest of existing code ...

def _should_recommend_refactoring(self, analysis: Dict) -> bool:
    """Check if refactoring should be recommended."""
    # Check for high duplicate count
    # Check for high conflict count
    # Check for architectural issues
```

### 4.4 Comprehensive Testing

**Test Suite**: `tests/test_architecture_refactoring.py`

```python
class TestArchitectureRefactoring:
    """Test architecture refactoring system."""
    
    def test_detect_master_plan_changes(self):
        """Test MASTER_PLAN change detection."""
    
    def test_find_duplicate_files(self):
        """Test duplicate file detection."""
    
    def test_compare_files(self):
        """Test file comparison."""
    
    def test_merge_simple_files(self):
        """Test simple file merge."""
    
    def test_merge_with_conflicts(self):
        """Test merge with conflicts."""
    
    def test_ai_merge(self):
        """Test AI-powered merge."""
    
    def test_remove_redundant_files(self):
        """Test file removal."""
    
    def test_update_references(self):
        """Test reference updates."""
    
    def test_full_refactoring_workflow(self):
        """Test complete refactoring workflow."""
```

### 4.5 Documentation

**Files to Create/Update**:
1. `ARCHITECTURE_REFACTORING_GUIDE.md` - User guide
2. `REFACTORING_TOOLS_REFERENCE.md` - Tool reference
3. `REFACTORING_EXAMPLES.md` - Example scenarios
4. Update `README.md` with refactoring info

---

## Success Criteria

### Functional Requirements
- ✅ Detect MASTER_PLAN.md changes
- ✅ Find duplicate/similar files
- ✅ Compare files in detail
- ✅ Merge files intelligently
- ✅ Remove redundant files
- ✅ Update all references
- ✅ Integrate with existing phases

### Quality Requirements
- ✅ No data loss during merging
- ✅ Preserve all unique features
- ✅ Maintain code quality
- ✅ Handle conflicts gracefully
- ✅ Comprehensive error handling
- ✅ Detailed logging

### Performance Requirements
- ✅ Detect changes in < 5 seconds
- ✅ Compare files in < 2 seconds
- ✅ Merge files in < 30 seconds
- ✅ Handle projects with 100+ files

---

## Risk Mitigation

### Risk 1: Data Loss During Merge
**Mitigation**:
- Create backups before merging
- Verify all features preserved
- Allow rollback if verification fails

### Risk 2: AI Makes Incorrect Merge
**Mitigation**:
- Always verify AI output
- Send to QA phase for review
- Allow manual intervention

### Risk 3: Breaking References
**Mitigation**:
- Track all imports and references
- Update systematically
- Verify no broken imports

### Risk 4: Performance Issues
**Mitigation**:
- Cache analysis results
- Use incremental analysis
- Optimize AST parsing

---

## Timeline

**Week 1**: Foundation Components
- Days 1-2: Architecture Change Detector
- Days 3-4: File Similarity Detector
- Days 5-7: File Comparator + Tools + Handlers

**Week 2**: Core Refactoring Phase
- Days 1-3: Architecture Refactoring Phase
- Days 4-5: Feature Extractor + File Merger
- Days 6-7: Polytopic Integration + Testing

**Week 3**: AI Integration
- Days 1-2: Refactoring Prompts
- Days 3-5: AI-Powered Merge Logic
- Days 6-7: Conflict Resolution + Testing

**Week 4**: Integration & Testing
- Days 1-2: Phase Integrations
- Days 3-5: Comprehensive Testing
- Days 6-7: Documentation + Final Testing

**Total**: 4 weeks (28 days)

---

## Conclusion

This implementation plan provides a complete roadmap for adding architecture refactoring and file reconciliation capabilities to the autonomy pipeline. The system will be able to:

1. ✅ Detect MASTER_PLAN.md changes automatically
2. ✅ Find and analyze duplicate/similar files
3. ✅ Use AI to intelligently merge files
4. ✅ Remove redundant files safely
5. ✅ Maintain architecture consistency

The implementation is structured in 4 phases over 4 weeks, with clear milestones, testing requirements, and risk mitigation strategies.