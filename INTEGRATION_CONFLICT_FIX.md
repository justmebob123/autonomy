# Integration Conflict Analysis Loop Fix

## Problem Observed

The AI was stuck in an infinite analysis loop on task "refactor_0409 - Integration conflict":

```
Iteration 1: list_all_source_files → RETRY (needs to read files)
Iteration 2: read_file → RETRY (didn't resolve)
Iteration 3: read ARCHITECTURE.md → RETRY (didn't resolve)
Iteration 4: read MASTER_PLAN.md → RETRY (didn't resolve)
Iteration 5: find_all_related_files → RETRY (only compared)
Iteration 6: map_file_relationships → RETRY (only compared)
Iteration 7: read_file again → RETRY (didn't resolve)
Iteration 8-10: More analysis → RETRY (didn't resolve)
... infinite loop
```

## Root Cause

**Integration conflict tasks are inherently complex and vague:**
- Task title: "Integration conflict" (no specifics)
- Task description: "Integration conflict: [some description]"
- Multiple files involved
- No clear single action to take

**The AI didn't know when to stop analyzing and take action:**
- Prompt said: "merge_file_implementations OR move_file"
- But AI didn't know WHICH one to use
- Kept analyzing hoping to find clarity
- Never reached a decision point

## The Fix

### 1. Updated Tool Selection Guide

**Before**:
```
- Integration conflicts: merge_file_implementations OR move_file to correct location
```

**After**:
```
- Integration conflicts: 
  * If clear what to do: merge_file_implementations OR move_file
  * If unclear after 3-4 analysis steps: create_issue_report with detailed findings
  * DO NOT analyze indefinitely - after reading files and checking architecture, TAKE ACTION
```

### 2. Added Concrete Example

Added a detailed example showing:
- **Correct approach (clear)**: Read files → Read architecture → Take action (merge/move)
- **Correct approach (unclear)**: Read files → Read architecture → Create detailed report
- **Wrong approach**: Keep calling analysis tools without taking action

### 3. Added Explicit Rule

```
⚠️ INTEGRATION CONFLICT RULE: After 3-4 analysis steps, you MUST take action 
(merge, move, or report). DO NOT analyze indefinitely!
```

## Expected Behavior After Fix

### Before Fix
```
Iteration 1-10: Analyze, analyze, analyze...
Result: ❌ Infinite loop, task never completes
```

### After Fix
```
Iteration 1: read_file (understand files)
Iteration 2: read ARCHITECTURE.md (understand design)
Iteration 3: read MASTER_PLAN.md (understand goals)
Iteration 4: create_issue_report (document findings and ask for guidance)
Result: ✅ Task RESOLVED by documenting
```

OR if clear:
```
Iteration 1: read_file
Iteration 2: read ARCHITECTURE.md
Iteration 3: merge_file_implementations (fix the conflict)
Result: ✅ Task RESOLVED by fixing
```

## Why This Works

1. **Sets clear expectations**: AI knows it must act after 3-4 steps
2. **Provides escape hatch**: If unclear, create report (valid resolution)
3. **Prevents infinite loops**: Explicit rule against indefinite analysis
4. **Concrete examples**: Shows exactly what to do in both scenarios

## Impact

- ✅ Integration conflict tasks will complete in 3-5 iterations (not 10+)
- ✅ AI will create detailed reports when unsure (better than looping)
- ✅ Clear decision point after initial analysis
- ✅ Maintains quality (AI still analyzes, just doesn't loop forever)

## Commit

**Hash**: d282431
**Message**: "fix: Add guidance for integration conflict tasks to prevent infinite analysis loops"
**Files**: 1 modified (31 insertions, 1 deletion)

## Testing

The user's pipeline should now:
1. Complete the current integration conflict task (refactor_0409) in next 1-3 iterations
2. Either fix the conflict OR create a detailed report
3. Move on to next task instead of looping

## Status

✅ FIXED - Integration conflict tasks now have clear resolution path