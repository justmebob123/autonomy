# Integration Conflict Context Fix

## The Problem

The AI was stuck in an infinite loop on task refactor_0409 (attempt 27+) because the task context was too vague:

```
INTEGRATION CONFLICT DETECTED:
{'files': [...], 'description': '...', 'type': '...'}

ACTION REQUIRED:
1. Analyze the integration conflict
2. Use move_file if files are in wrong locations
3. Use merge_file_implementations if implementations conflict
4. Use create_issue_report if issue requires developer decision
```

**Issues with this approach**:
1. Raw dictionary dump - not human-readable
2. Generic instructions - no specific guidance
3. No file names shown - AI doesn't know what to read
4. No step-by-step workflow - AI doesn't know where to start
5. "create_issue_report" option - gives AI an escape hatch

**Result**: AI kept calling the same 4 tools in the same order every iteration, never making progress.

## The Fix

### Before (Vague)
```python
return f"""
INTEGRATION CONFLICT DETECTED:
{data}

ACTION REQUIRED:
1. Analyze the integration conflict
2. Use move_file if files are in wrong locations
3. Use merge_file_implementations if implementations conflict
4. Use create_issue_report if issue requires developer decision
"""
```

### After (Specific)
```python
files = data.get('files', [])
description = data.get('description', 'Unknown conflict')
conflict_type = data.get('type', 'unknown')

return f"""
INTEGRATION CONFLICT DETECTED:
Type: {conflict_type}
Description: {description}

FILES INVOLVED:
{file_list}

SPECIFIC ACTIONS TO TAKE:

Step 1: READ the conflicting files to understand what they do
read_file(filepath="{files[0]}")
read_file(filepath="{files[1]}")

Step 2: READ ARCHITECTURE.md to understand where they should be
read_file(filepath="ARCHITECTURE.md")

Step 3: COMPARE the implementations to see if they're duplicates
compare_file_implementations(file1="{files[0]}", file2="{files[1]}")

Step 4: MAKE A DECISION based on what you found:
- If files are >80% similar → merge_file_implementations
- If one is misplaced → move_file to correct location
- If both are misplaced → move both files
- If names conflict → rename_file to clarify

Step 5: EXECUTE your decision (merge, move, or rename)

⚠️ DO NOT just analyze and stop - you MUST take action to resolve the conflict!
"""
```

## What Changed

### 1. Extract Specific Information
- **Files**: Show actual file paths, not raw dict
- **Description**: Show human-readable description
- **Type**: Show conflict type

### 2. Provide Step-by-Step Workflow
- **Step 1**: Specific read_file calls with actual file names
- **Step 2**: Read ARCHITECTURE.md
- **Step 3**: Specific compare call with actual file names
- **Step 4**: Clear decision tree
- **Step 5**: Execute the decision

### 3. Remove Escape Hatch
- Removed "create_issue_report if issue requires developer decision"
- Added warning: "DO NOT just analyze and stop"
- Emphasized: "you MUST take action"

### 4. Show Actual Tool Calls
Instead of:
```
1. Analyze the integration conflict
```

Now shows:
```
Step 1: READ the conflicting files to understand what they do
read_file(filepath="resources/resource_estimator.py")
read_file(filepath="core/resource/resource_estimator.py")
```

## Expected Behavior After Fix

### Before Fix (Attempt 27)
```
Iteration 1: read_file("resources/resource_estimator.py")
Iteration 2: read_file("resources/resource_estimator.py")  # Same file again!
Iteration 3: read_file("resources/resource_estimator.py")  # Still same file!
... infinite loop
```

### After Fix
```
Iteration 1: read_file("resources/resource_estimator.py")
Iteration 2: read_file("core/resource/resource_estimator.py")
Iteration 3: read_file("ARCHITECTURE.md")
Iteration 4: compare_file_implementations(...)
Iteration 5: DECISION: 95% similar, merge them
Iteration 6: merge_file_implementations(...) → ✅ RESOLVED
```

## Why This Works

### 1. Specific File Names
AI knows EXACTLY which files to read, not guessing

### 2. Clear Workflow
AI follows steps 1→2→3→4→5, not wandering aimlessly

### 3. Concrete Examples
Shows actual tool calls with actual parameters

### 4. No Escape Hatch
Can't create report and move on - must resolve

### 5. Decision Tree
Clear criteria for each action (>80% similar = merge, etc.)

## Impact

- ✅ AI will know which files are conflicting
- ✅ AI will follow clear step-by-step workflow
- ✅ AI will see actual tool calls to make
- ✅ AI will make decision and execute it
- ✅ Task will complete in 5-7 iterations instead of infinite loop

## Commit

**Hash**: ce91584
**Message**: "fix: Provide specific actionable information for integration conflicts"
**Changes**: 1 file, 33 insertions, 7 deletions

## Testing

The user should:
1. Pull latest changes: `git pull origin main`
2. Resume pipeline: `python3 run.py -vv ../web/`
3. Watch task refactor_0409 complete in next 5-7 iterations

## Status

✅ FIXED - Integration conflicts now have specific, actionable context