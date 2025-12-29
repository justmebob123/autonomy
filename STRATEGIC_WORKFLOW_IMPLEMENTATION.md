# Strategic Workflow Implementation Plan

## Phase 1: Core Infrastructure (IMMEDIATE)

### 1.1 Add Strategic Document Loading to Planning Phase
**File**: `pipeline/phases/planning.py`
**Changes**:
```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # Load all strategic documents
    master_plan = self.read_file("MASTER_PLAN.md")
    primary_objectives = self.read_file("PRIMARY_OBJECTIVES.md") or ""
    secondary_objectives = self.read_file("SECONDARY_OBJECTIVES.md") or ""
    tertiary_objectives = self.read_file("TERTIARY_OBJECTIVES.md") or ""
    architecture = self.read_file("ARCHITECTURE.md") or ""
    
    # Perform deep analysis
    analysis_results = self._perform_deep_analysis(existing_files)
    
    # Update strategic documents based on analysis
    self._update_strategic_documents(
        analysis_results,
        secondary_objectives,
        tertiary_objectives,
        architecture
    )
    
    # Check if MASTER_PLAN needs update (95% threshold)
    if self._should_update_master_plan(state):
        self._update_master_plan(master_plan, state)
```

### 1.2 Add Deep Analysis Method
**File**: `pipeline/phases/planning.py`
**New Method**:
```python
def _perform_deep_analysis(self, existing_files: List[str]) -> Dict:
    """
    Perform comprehensive codebase analysis.
    
    Returns:
        Dict with:
        - complexity_issues: List of high-complexity components
        - dead_code: List of unused code
        - integration_gaps: List of missing integrations
        - architectural_issues: List of design problems
        - test_gaps: List of missing tests
        - failures: List of known failures
    """
    results = {
        'complexity_issues': [],
        'dead_code': [],
        'integration_gaps': [],
        'architectural_issues': [],
        'test_gaps': [],
        'failures': []
    }
    
    python_files = [f for f in existing_files if f.endswith('.py')]
    
    for filepath in python_files:
        # Complexity analysis
        complexity = self.complexity_analyzer.analyze(filepath)
        for func in complexity.results:
            if func.complexity >= 30:
                results['complexity_issues'].append({
                    'file': filepath,
                    'function': func.name,
                    'complexity': func.complexity,
                    'line': func.line
                })
        
        # Dead code detection
        dead_code = self.dead_code_detector.detect(filepath)
        if dead_code.unused_functions:
            results['dead_code'].extend([
                {'file': filepath, 'type': 'function', 'name': f[0], 'line': f[2]}
                for f in dead_code.unused_functions
            ])
        
        # Integration gaps
        gaps = self.gap_finder.find_gaps(filepath)
        if gaps.unused_classes:
            results['integration_gaps'].extend([
                {'file': filepath, 'type': 'class', 'name': c[0], 'line': c[2]}
                for c in gaps.unused_classes
            ])
    
    return results
```

### 1.3 Add Document Update Method
**File**: `pipeline/phases/planning.py`
**New Method**:
```python
def _update_strategic_documents(
    self,
    analysis_results: Dict,
    secondary_objectives: str,
    tertiary_objectives: str,
    architecture: str
) -> None:
    """
    Update strategic documents with analysis findings.
    """
    # Update SECONDARY_OBJECTIVES.md
    secondary_updates = self._format_secondary_objectives(analysis_results)
    if secondary_updates:
        self.file_updater.update_section(
            "SECONDARY_OBJECTIVES.md",
            "## Analysis Findings",
            secondary_updates
        )
    
    # Update TERTIARY_OBJECTIVES.md
    tertiary_updates = self._format_tertiary_objectives(analysis_results)
    if tertiary_updates:
        self.file_updater.update_section(
            "TERTIARY_OBJECTIVES.md",
            "## Specific Fixes Needed",
            tertiary_updates
        )
    
    # Update ARCHITECTURE.md
    arch_updates = self._format_architecture_updates(analysis_results)
    if arch_updates:
        self.file_updater.update_section(
            "ARCHITECTURE.md",
            "## Current Issues",
            arch_updates
        )
```

### 1.4 Add MASTER_PLAN Update Check
**File**: `pipeline/phases/planning.py`
**New Method**:
```python
def _should_update_master_plan(self, state: PipelineState) -> bool:
    """
    Check if MASTER_PLAN should be updated (95% completion threshold).
    """
    total_tasks = len(state.tasks)
    completed_tasks = len([t for t in state.tasks if t.status == TaskStatus.COMPLETED])
    
    if total_tasks == 0:
        return False
    
    completion_rate = completed_tasks / total_tasks
    return completion_rate >= 0.95
```

## Phase 2: Enhance All Phases to Use Documents (HIGH PRIORITY)

### 2.1 Update Coding Phase
**File**: `pipeline/phases/coding.py`
**Changes**:
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # Load strategic documents for context
    primary_objectives = self.read_file("PRIMARY_OBJECTIVES.md") or ""
    secondary_objectives = self.read_file("SECONDARY_OBJECTIVES.md") or ""
    tertiary_objectives = self.read_file("TERTIARY_OBJECTIVES.md") or ""
    architecture = self.read_file("ARCHITECTURE.md") or ""
    
    # Extract relevant sections for this task
    relevant_context = self._extract_relevant_context(
        task,
        primary_objectives,
        secondary_objectives,
        tertiary_objectives,
        architecture
    )
    
    # Include in user message
    user_message = self._build_user_message(task, context, error_context, relevant_context)
```

### 2.2 Update QA Phase
**File**: `pipeline/phases/qa.py`
**Changes**:
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # Load strategic documents for quality criteria
    primary_objectives = self.read_file("PRIMARY_OBJECTIVES.md") or ""
    secondary_objectives = self.read_file("SECONDARY_OBJECTIVES.md") or ""
    architecture = self.read_file("ARCHITECTURE.md") or ""
    
    # Check against objectives
    quality_criteria = self._extract_quality_criteria(
        filepath,
        primary_objectives,
        secondary_objectives,
        architecture
    )
    
    # Include in review message
    user_message_parts.append(f"\n## Quality Criteria:\n{quality_criteria}")
```

### 2.3 Update Debugging Phase
**File**: `pipeline/phases/debugging.py`
**Changes**:
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # Load strategic documents for known issues
    secondary_objectives = self.read_file("SECONDARY_OBJECTIVES.md") or ""
    tertiary_objectives = self.read_file("TERTIARY_OBJECTIVES.md") or ""
    
    # Check for known issues
    known_issues = self._extract_known_issues(
        task.target_file,
        secondary_objectives,
        tertiary_objectives
    )
    
    # Include in debugging context
    if known_issues:
        user_message += f"\n## Known Issues:\n{known_issues}"
```

## Phase 3: Update Prompts (MEDIUM PRIORITY)

### 3.1 Planning Phase Prompt
**File**: `pipeline/prompts.py` or planning phase system prompt
**Add**:
```
Your responsibilities:
1. Analyze the codebase deeply
2. Compare actual vs intended architecture
3. Update SECONDARY_OBJECTIVES.md with:
   - Architectural changes needed
   - Testing requirements
   - Reported failures
   - Integration issues
4. Update TERTIARY_OBJECTIVES.md with:
   - Specific code examples
   - Component-level fixes
   - Design pattern improvements
5. Update ARCHITECTURE.md with current state
6. Only update MASTER_PLAN when 95% of objectives are complete
7. Create tasks based on document guidance
```

### 3.2 Coding Phase Prompt
**Add**:
```
Before implementing, review:
- PRIMARY_OBJECTIVES: What this feature should accomplish
- SECONDARY_OBJECTIVES: Specific requirements and constraints
- TERTIARY_OBJECTIVES: Implementation details and examples
- ARCHITECTURE.md: Design patterns to follow
```

### 3.3 QA Phase Prompt
**Add**:
```
Check code against:
- PRIMARY_OBJECTIVES: Does it meet functional requirements?
- SECONDARY_OBJECTIVES: Correct implementation approach?
- TERTIARY_OBJECTIVES: Specific details correct?
- ARCHITECTURE.md: Follows design patterns?
```

## Phase 4: Tool Enhancements (LOW PRIORITY)

### 4.1 Add Document Parsing Tools
**New Tool**: `extract_relevant_section`
```python
def extract_relevant_section(document: str, keywords: List[str]) -> str:
    """
    Extract sections from strategic documents relevant to current task.
    """
    # Parse markdown sections
    # Find sections containing keywords
    # Return relevant text
```

### 4.2 Add Architecture Comparison Tool
**New Tool**: `compare_architecture`
```python
def compare_architecture(intended: str, actual_files: List[str]) -> Dict:
    """
    Compare intended architecture vs actual implementation.
    """
    # Parse intended architecture
    # Analyze actual files
    # Return differences
```

## Implementation Order

1. **IMMEDIATE** (Today):
   - Add strategic document loading to planning phase
   - Add deep analysis method
   - Add document update methods
   - Add 95% completion check

2. **HIGH PRIORITY** (Next):
   - Update coding phase to use documents
   - Update QA phase to use documents
   - Update debugging phase to use documents

3. **MEDIUM PRIORITY** (After):
   - Update all phase prompts
   - Add document extraction helpers

4. **LOW PRIORITY** (Future):
   - Add advanced parsing tools
   - Add architecture comparison tools

## Testing Plan

1. Create test project with strategic documents
2. Run planning phase - verify it updates documents
3. Run coding phase - verify it reads documents
4. Run QA phase - verify it checks against documents
5. Verify MASTER_PLAN only updates at 95%

## Success Criteria

- ✅ Planning phase analyzes codebase
- ✅ Planning phase updates SECONDARY/TERTIARY objectives
- ✅ Planning phase updates ARCHITECTURE.md
- ✅ Planning phase only updates MASTER_PLAN at 95%
- ✅ Coding phase reads and uses documents
- ✅ QA phase checks against documents
- ✅ Debugging phase uses known issues from documents
- ✅ All phases treat documents as inter-process communication