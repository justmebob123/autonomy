# Critical Analysis: Refactoring Phase Prompt Issues

## Problem Identified

The AI is stuck in an infinite loop alternating between:
- Attempt N (odd): `list_all_source_files` 
- Attempt N+1 (even): `read_file` on one file
- Repeat forever without resolving the task

## Root Cause: One-Size-Fits-All Prompt

The current prompt (`_build_task_prompt`) provides **GENERIC guidance** for ALL task types:

```
🔬 COMPREHENSIVE ANALYSIS REQUIRED (CONTINUOUS MODE):
**REQUIRED ANALYSIS TOOLS** (use ALL of these):
1. list_all_source_files
2. find_all_related_files  
3. read_file
4. map_file_relationships
5. cross_reference_file
6. compare_file_implementations
7. analyze_file_purpose
```

### Why This Fails

**Task Type**: Missing method: `RiskAssessment.generate_risk_chart`
- **What AI needs to do**: Implement a missing method
- **What prompt tells AI to do**: Analyze entire codebase, compare files, map relationships
- **Result**: AI follows instructions, does comprehensive analysis, never gets to implementation

### The Mismatch

| Task Type | What's Needed | What Prompt Says | Result |
|-----------|---------------|------------------|---------|
| Missing Method | Read file, implement method | Analyze entire codebase | ❌ Infinite analysis |
| Duplicate Code | Compare files, merge | Analyze entire codebase | ❌ Over-analysis |
| Integration Conflict | Read both files, check architecture | Analyze entire codebase | ✅ Appropriate |
| Dead Code | Check if used, decide | Analyze entire codebase | ❌ Over-analysis |

## The Infinite Loop Pattern

```
Attempt 1: list_all_source_files → BLOCKED (need to read files)
Attempt 2: read_file(one file) → BLOCKED (need comprehensive analysis)
Attempt 3: list_all_source_files → BLOCKED (need to read files)
Attempt 4: read_file(one file) → BLOCKED (need comprehensive analysis)
... forever
```

### Why It Loops

1. **Attempt N (odd)**: AI calls `list_all_source_files`
   - Retry logic says: "You only compared files without reading them"
   - Forces retry with: "You MUST read both files"

2. **Attempt N+1 (even)**: AI calls `read_file` 
   - Retry logic says: "You read files but did NOT complete comprehensive analysis"
   - Forces retry with: "REQUIRED NEXT STEPS: list_all_source_files..."

3. **Repeat**: AI alternates between these two states forever

## Solution: Task-Type-Specific Prompts

Different task types need different workflows:

### 1. Missing Method Tasks
**Workflow**: Simple and direct
```
1. Read the file containing the class
2. Understand what the method should do
3. Implement the method
4. OR create issue report if requires domain knowledge
```

**NO NEED FOR**:
- Listing all source files
- Finding related files
- Mapping relationships
- Comparing implementations

### 2. Duplicate Code Tasks  
**Workflow**: Compare then merge
```
1. Compare the duplicate files
2. Understand differences
3. Merge using merge_file_implementations
```

**NO NEED FOR**:
- Listing all source files (we already know which files)
- Finding related files (task specifies the files)

### 3. Integration Conflict Tasks
**Workflow**: Comprehensive analysis (current approach is correct)
```
1. List all source files
2. Find related files
3. Read all relevant files
4. Check architecture
5. Make intelligent decision
```

### 4. Dead Code / Unused Code Tasks
**Workflow**: Check usage, decide
```
1. Search for usages of the code
2. Check if part of planned architecture
3. Create issue report (early-stage project)
```

## Implementation Plan

### Phase 1: Add Task-Type Detection
Modify `_build_task_prompt` to detect task type and provide appropriate guidance.

### Phase 2: Create Task-Type-Specific Prompts
Create separate prompt templates for each task type:
- `_get_missing_method_prompt()`
- `_get_duplicate_code_prompt()`
- `_get_integration_conflict_prompt()`
- `_get_dead_code_prompt()`
- `_get_architecture_violation_prompt()`

### Phase 3: Update Retry Logic
Modify retry logic to be task-type-aware:
- Missing method: Don't require comprehensive analysis
- Duplicate code: Only require comparison, not full codebase scan
- Integration conflict: Require comprehensive analysis (keep current)

### Phase 4: Simplify Analysis Tracker
The `TaskAnalysisTracker` with 15 checkpoints is overkill for simple tasks.
Make it task-type-aware with different checkpoint sets.

## Expected Impact

### Before Fix
- Missing method task: 10+ attempts, infinite loop
- Duplicate code task: 5+ attempts, over-analysis
- Integration conflict task: Works correctly
- Dead code task: 8+ attempts, over-analysis

### After Fix
- Missing method task: 1-2 attempts, direct implementation
- Duplicate code task: 1-2 attempts, quick merge
- Integration conflict task: 3-5 attempts, thorough analysis
- Dead code task: 1-2 attempts, quick decision

## Key Insight

**The system is treating every task like a complex integration conflict, when most tasks are simple and direct.**

The comprehensive analysis workflow is CORRECT for integration conflicts, but WRONG for:
- Missing methods (just implement it)
- Duplicate code (just merge it)
- Dead code (just check if used)
- Simple bugs (just fix them)

## Recommendation

Implement task-type-specific prompts IMMEDIATELY. This is the root cause of the infinite loops and the reason the refactoring phase never completes any tasks.

The current "one size fits all" approach is like using a sledgehammer for every task - sometimes you just need a regular hammer, or even just a screwdriver.