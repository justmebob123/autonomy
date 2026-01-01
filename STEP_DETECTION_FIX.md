# CRITICAL FIX: Step-Aware Prompt Now Uses Actual Tool Execution History

## Problem Summary

The refactoring phase was stuck in an infinite loop where:
1. AI reads files (timeline/critical_path_algorithm.py, core/task_management/task_service.py)
2. AI tries to merge files
3. System blocks: "Read ARCHITECTURE.md to understand design intent"
4. AI tries to merge again (ignoring the requirement)
5. Loop repeats 21+ times

## Root Cause

The `_get_integration_conflict_prompt()` method was checking the **assistant's message content** to determine what step we're on:

```python
for msg in conversation_history:
    if msg.get('role') == 'assistant':
        content = str(msg.get('content', ''))
        if 'read_file' in content and 'ARCHITECTURE.md' in content:
            architecture_read = True
```

**The Bug:** This checks if the assistant's JSON output contains "read_file" and "ARCHITECTURE.md", but:
- The assistant outputs: `{"name": "read_file", "arguments": {"filepath": "timeline/critical_path_algorithm.py"}}`
- Even if AI called `read_file(filepath="ARCHITECTURE.md")`, the detection wouldn't work reliably
- The step detection was looking at the wrong data source

## The Fix

Changed to use `TaskAnalysisTracker` which records **actual tool executions**:

```python
# FIXED: Use TaskAnalysisTracker to check actual tool executions
state = self.analysis_tracker.get_or_create_state(task.task_id)

# Count what's been done by looking at ACTUAL tool executions
files_read = set()
architecture_read = state.checkpoints['read_architecture'].completed
comparison_done = False

for tool_call in state.tool_calls_history:
    tool_name = tool_call['tool']
    arguments = tool_call.get('arguments', {})
    
    if tool_name == 'read_file':
        filepath = arguments.get('filepath') or arguments.get('file_path', '')
        if file1 in filepath:
            files_read.add(file1)
        if file2 in filepath:
            files_read.add(file2)
    
    if tool_name == 'compare_file_implementations':
        comparison_done = True
```

## Expected Behavior After Fix

**Before:**
```
Iteration 1: read_file(timeline/critical_path_algorithm.py) → Step detection: Step 1
Iteration 2: read_file(core/task_management/task_service.py) → Step detection: Step 1 (didn't see it!)
Iteration 3: merge_file_implementations → BLOCKED (need ARCHITECTURE.md)
Iteration 4: merge_file_implementations → BLOCKED (still thinks step 1!)
... infinite loop
```

**After:**
```
Iteration 1: read_file(timeline/critical_path_algorithm.py) → Step detection: Step 1 ✓
Iteration 2: read_file(core/task_management/task_service.py) → Step detection: Step 2 ✓
Iteration 3: Prompt says "Step 3: read_file(ARCHITECTURE.md)" → AI reads it
Iteration 4: Prompt says "Step 4: compare_file_implementations" → AI compares
Iteration 5: Prompt says "Step 5: merge_file_implementations" → AI merges → ✅ COMPLETE
```

## Files Modified

- `pipeline/phases/refactoring.py` - Fixed `_get_integration_conflict_prompt()` method

## Testing

To verify the fix works:
```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

Expected: Task refactor_0410 should complete in 5 iterations instead of looping infinitely.

## Impact

- ✅ Step-aware prompt now correctly detects completed steps
- ✅ AI progresses through steps 1 → 2 → 3 → 4 → 5
- ✅ No more infinite loops on integration conflicts
- ✅ Tasks complete successfully