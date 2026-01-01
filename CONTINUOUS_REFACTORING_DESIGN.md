# Continuous Refactoring System - Design Document

## User Requirements

### Critical Issues with Current System
1. **3 retries is too low** - Should continuously loop until resolved
2. **Conversation pruned at 50** - Should maintain substantial context for complex analysis
3. **Not examining entire codebase** - Should use ALL tools to understand full context
4. **Stops too early** - Should continue until ALL refactoring tasks complete
5. **Creates reports instead of fixing** - Should only report new code requirements

### Required Behavior

**Continuous Loop Through Entire Codebase**:
- Examine ALL files in continuous conversation
- Use ALL available tools for comprehensive analysis
- Continue resolving issues and refactoring until complete
- Maintain full context throughout entire process
- Never give up on a task (except new code requirements)

**Only Skip New Code Requirements**:
- New features/functionality outside current scope
- But MUST still address:
  - Design pattern consistency
  - Architecture alignment
  - Integration with existing code
  - Provide pattern for coder to follow

**Stable Architecture Goal**:
- Refactor everything into consistent design
- Ensure coder has stable architecture to work with
- All files follow same design patterns
- Complete integration of all existing code

## Implementation Plan

### 1. Remove Attempt Limits
```python
# OLD: max_attempts = 3
# NEW: max_attempts = None (unlimited)

# Continuous loop until:
# - Task actually resolved (code fixed)
# - OR confirmed as new code requirement (after thorough analysis)
```

### 2. Expand Conversation Context
```python
# OLD: max_messages = 50
# NEW: max_messages = 500 (or unlimited for refactoring)

# Maintain full conversation history including:
# - All file reads
# - All analysis results
# - All architectural decisions
# - All integration attempts
```

### 3. Force Comprehensive Analysis
```python
# Before ANY decision, AI MUST:
1. Read ALL related files (not just 2)
2. Check ARCHITECTURE.md
3. Check MASTER_PLAN.md
4. Use list_all_source_files to see full codebase
5. Use find_all_related_files to find dependencies
6. Use cross_reference_file to validate placement
7. Use map_file_relationships to understand connections
8. Use analyze_file_purpose for each file
9. Use compare_multiple_files for all related files

# Only AFTER all analysis, then decide:
# - Merge/move/refactor (if can be done)
# - OR create detailed report (if new code needed)
```

### 4. Continuous Integration Loop
```python
# Refactoring phase continues until:
while refactoring_tasks_exist():
    task = get_next_task()
    
    # Comprehensive analysis (no limits)
    while not fully_understood(task):
        use_all_analysis_tools()
        examine_all_related_files()
        check_all_architectural_documents()
    
    # Attempt resolution (no attempt limit)
    while not resolved(task):
        if can_fix_automatically():
            fix_it()
        elif needs_integration():
            integrate_it()
        elif needs_refactoring():
            refactor_it()
        elif truly_new_code_requirement():
            # Only after exhaustive analysis
            create_detailed_report()
            break
        else:
            # Continue analyzing with more tools
            use_more_analysis_tools()
```

### 5. Task Classification
```python
def classify_task(task):
    # After comprehensive analysis
    
    if is_duplicate_code():
        return "MERGE"  # Can fix automatically
    
    if is_misplaced_file():
        return "MOVE"  # Can fix automatically
    
    if is_inconsistent_pattern():
        return "REFACTOR"  # Can fix automatically
    
    if is_integration_conflict():
        # Analyze both implementations
        if one_is_superior():
            return "INTEGRATE"  # Use better one
        elif can_merge():
            return "MERGE"  # Combine both
        else:
            return "REFACTOR"  # Redesign
    
    if is_missing_method():
        # Check if method exists elsewhere
        if exists_in_related_file():
            return "MOVE"  # Relocate method
        elif can_generate_from_pattern():
            return "IMPLEMENT"  # Follow pattern
        else:
            return "NEW_CODE"  # Truly new requirement
    
    # Default: continue analyzing
    return "ANALYZE_MORE"
```

## New Checkpoint System

### Comprehensive Analysis Checkpoints
```python
checkpoints = {
    # File Understanding (ALL related files)
    "read_all_target_files": False,
    "read_all_related_files": False,
    "read_all_similar_files": False,
    
    # Architectural Understanding
    "read_architecture": False,
    "read_master_plan": False,
    "validate_against_architecture": False,
    
    # Codebase Context
    "list_all_source_files": False,
    "find_all_related_files": False,
    "map_file_relationships": False,
    
    # Deep Analysis
    "analyze_each_file_purpose": False,
    "compare_all_implementations": False,
    "check_integration_points": False,
    "validate_design_patterns": False,
    
    # Decision Making
    "identify_superior_implementation": False,
    "determine_merge_strategy": False,
    "plan_refactoring_steps": False,
}

# AI cannot proceed until ALL checkpoints complete
# No attempt limit - continues until all done
```

## Conversation Management

### Substantial Context Retention
```python
# OLD: Prune at 50 messages
# NEW: Keep ALL messages for refactoring phase

conversation_context = {
    "max_messages": None,  # Unlimited for refactoring
    "include_all_tool_results": True,
    "include_all_file_contents": True,
    "include_all_analysis": True,
    "summarize_only_when": "context > 100k tokens",
    "summary_preserves": [
        "all_architectural_decisions",
        "all_file_purposes",
        "all_integration_points",
        "all_design_patterns",
    ]
}
```

### Progressive Context Building
```python
# Build comprehensive context over time
iteration_1: Read target files
iteration_2: Read related files
iteration_3: Read similar files
iteration_4: Analyze all files
iteration_5: Compare implementations
iteration_6: Validate architecture
iteration_7: Plan integration
iteration_8: Execute refactoring
# ... continues until resolved
```

## Resolution Criteria

### Task is RESOLVED when:
```python
def is_task_resolved(task):
    if task.type == "duplicate":
        return files_merged() and tests_pass()
    
    if task.type == "integration_conflict":
        return (
            superior_implementation_identified() and
            inferior_removed() and
            all_imports_updated() and
            architecture_consistent()
        )
    
    if task.type == "missing_method":
        return (
            method_implemented() or
            method_relocated() or
            confirmed_new_code_requirement()
        )
    
    if task.type == "architecture_violation":
        return (
            files_relocated() and
            patterns_consistent() and
            architecture_validated()
        )
    
    # Never resolved by just creating report
    # Only resolved by actual fix or confirmed new code
    return False
```

### New Code Requirement Confirmation
```python
def confirm_new_code_requirement(task):
    # Exhaustive checks before confirming
    checks = [
        "searched_entire_codebase",
        "checked_all_related_files",
        "validated_no_existing_implementation",
        "confirmed_not_in_architecture",
        "verified_not_in_master_plan",
        "analyzed_all_similar_patterns",
        "attempted_generation_from_patterns",
    ]
    
    if all(checks):
        # Create detailed report with:
        # - What exists (design pattern to follow)
        # - What's missing (new code needed)
        # - How to implement (follow existing patterns)
        # - Where to place (architecture alignment)
        return True
    
    return False  # Continue analyzing
```

## Implementation Changes

### 1. Remove Attempt Limits
**File**: `pipeline/state/refactoring_task.py`
```python
# OLD
max_attempts: int = 3

# NEW
max_attempts: int = None  # Unlimited
```

### 2. Expand Conversation Context
**File**: `pipeline/phases/base.py`
```python
# OLD
MAX_CONVERSATION_HISTORY = 50

# NEW
MAX_CONVERSATION_HISTORY = None  # Unlimited for refactoring
# Or: 500 for substantial context
```

### 3. Enhanced Checkpoints
**File**: `pipeline/state/task_analysis_tracker.py`
```python
# Add comprehensive checkpoints
checkpoints = {
    # Existing
    "read_target_files": ...,
    "read_architecture": ...,
    "perform_analysis": ...,
    
    # NEW - Comprehensive
    "read_all_related_files": ...,
    "list_all_source_files": ...,
    "find_all_related_files": ...,
    "map_file_relationships": ...,
    "analyze_all_file_purposes": ...,
    "compare_all_implementations": ...,
    "validate_architecture_alignment": ...,
    "identify_design_patterns": ...,
    "plan_integration_strategy": ...,
}
```

### 4. Continuous Loop Logic
**File**: `pipeline/phases/refactoring.py`
```python
def _work_on_task(self, state, task):
    # Remove attempt limit check
    # while not task.resolved:  # Continuous until resolved
    
    # Comprehensive analysis (no limits)
    while not self._analysis_tracker.is_fully_analyzed(task):
        # Force more analysis
        prompt = self._build_analysis_prompt(task)
        result = self.chat_with_history(prompt, tools)
        
        # Track progress
        self._analysis_tracker.update(task, result)
    
    # Attempt resolution (no limits)
    while not task.resolved:
        prompt = self._build_resolution_prompt(task)
        result = self.chat_with_history(prompt, tools)
        
        if result.is_resolving_action():
            task.resolve()
        elif result.is_new_code_requirement():
            # Only after exhaustive analysis
            if self._confirm_new_code(task):
                task.report_new_code()
            else:
                # Continue analyzing
                continue
        else:
            # Continue with more analysis
            continue
```

## Expected Behavior

### Before (Current System)
```
Iteration 1: compare → BLOCKED
Iteration 2: compare → BLOCKED
Iteration 3: compare → BLOCKED
Result: Report created (lazy, didn't fix)
```

### After (Continuous System)
```
Iteration 1: compare → BLOCKED (need to read files)
Iteration 2: read file1, file2 → BLOCKED (need architecture)
Iteration 3: read ARCHITECTURE.md → BLOCKED (need related files)
Iteration 4: find_all_related_files → BLOCKED (need to read them)
Iteration 5-10: read all related files → BLOCKED (need analysis)
Iteration 11: analyze_file_purpose (all files) → BLOCKED (need comparison)
Iteration 12: compare_multiple_files → BLOCKED (need integration plan)
Iteration 13: map_file_relationships → BLOCKED (need decision)
Iteration 14: identify superior implementation → READY
Iteration 15: merge_file_implementations → RESOLVED
Result: Files actually merged, task complete
```

## Summary

The new system will:
1. ✅ Never give up (no attempt limits)
2. ✅ Maintain full context (no message pruning)
3. ✅ Examine entire codebase (use ALL tools)
4. ✅ Continue until stable (all tasks resolved)
5. ✅ Only skip new code (after exhaustive analysis)
6. ✅ Provide consistent design (stable architecture)
7. ✅ Give coder patterns to follow (even for new code)

This creates a truly autonomous refactoring system that doesn't stop until the job is done.