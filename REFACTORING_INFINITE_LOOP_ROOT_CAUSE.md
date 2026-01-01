# Refactoring Infinite Loop - Root Cause Analysis

## Problem Observed

The refactoring phase is stuck in an infinite loop:
- **Iteration 1-2**: Task `refactor_0203` calls `detect_duplicate_implementations`
- **Result**: Tool succeeds, but task marked as FAILED with message "only analysis performed, no action taken"
- **Iteration 3+**: Moves to other tasks, but duplicate detection keeps triggering refactoring

## Root Cause

### Issue 1: AI Not Using Correct Tools for Duplicates

**What's Happening**:
```
Task: "Duplicate code detected"
AI Action: detect_duplicate_implementations (ANALYSIS ONLY)
Result: ❌ FAILED - "only analysis performed, no action taken"
```

**What Should Happen**:
```
Task: "Duplicate code detected"
AI Action: 
  1. detect_duplicate_implementations (analyze)
  2. compare_file_implementations (compare duplicates)
  3. merge_file_implementations (FIX - merge duplicates)
Result: ✅ COMPLETED - duplicates merged
```

### Issue 2: Prompt Not Clear About Required Actions

Looking at the refactoring prompt, it says:
- "Use `detect_duplicate_implementations` to find duplicates"
- But doesn't emphasize: "Then use `merge_file_implementations` to FIX them"

### Issue 3: Task Description Too Vague

Task description: "Duplicate code detected"
- Doesn't specify WHICH files are duplicates
- Doesn't provide the duplicate analysis data
- AI has to re-analyze every time

## Solution Required

### 1. Fix Task Creation
When creating duplicate tasks, include:
- Which files are duplicates
- Similarity score
- What needs to be merged
- Full analysis data

### 2. Enhance Prompt
Make it crystal clear:
```
For DUPLICATE_CODE tasks:
1. If analysis_data provided: Skip to step 2
2. If no analysis_data: Call detect_duplicate_implementations first
3. Call compare_file_implementations on the duplicate files
4. Call merge_file_implementations to FIX the issue
5. NEVER mark complete after just analysis
```

### 3. Add Workflow Examples
Show the AI exactly what to do:
```
Example: Duplicate Code
- Task: api/resources.py and resources/resource_estimator.py are 85% similar
- Action 1: compare_file_implementations(api/resources.py, resources/resource_estimator.py)
- Action 2: merge_file_implementations(target=api/resources.py, source=resources/resource_estimator.py)
- Result: ✅ Files merged, duplicate removed
```

## Files to Fix

1. `pipeline/phases/refactoring.py` - Task creation (add analysis_data)
2. `pipeline/prompts.py` - Refactoring prompts (add workflow examples)
3. `pipeline/phases/refactoring.py` - Task context building (include full analysis)

## Expected Behavior After Fix

```
Iteration 1:
  Task: refactor_0203 - Duplicate: api/resources.py vs resources/resource_estimator.py (85% similar)
  AI: compare_file_implementations(api/resources.py, resources/resource_estimator.py)
  AI: merge_file_implementations(target=api/resources.py, source=resources/resource_estimator.py)
  Result: ✅ COMPLETED - Files merged

Iteration 2:
  Task: refactor_0214 - Unused class: AIBot
  AI: cleanup_redundant_files([core/chat/ai_chat_interface.py])
  Result: ✅ COMPLETED - File removed

Iteration 3:
  No more duplicate code detected
  Refactoring phase exits
  Continues to coding phase
```