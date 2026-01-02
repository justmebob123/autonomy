# Prompt System Fix - Force Action After Analysis

## Problem

The AI is stuck in an infinite loop:
1. Reads files ✅
2. Compares files ✅
3. Reads ARCHITECTURE.md ✅
4. **Goes back to reading files again** ❌
5. Never uses resolution tools ❌

## Root Cause

The step-aware prompt system is too complex and the AI is not following it correctly. After completing all analysis steps, the AI should be FORCED to use a resolution tool, but instead it keeps going back to analysis.

## Solution

Implement a **HARD STOP** after analysis is complete that FORCES the AI to use a resolution tool.

### Implementation

```python
def _get_integration_conflict_prompt(self, task: Any, context: str) -> str:
    """Prompt for integration conflicts - FORCE ACTION after analysis."""
    
    # Get target files
    target_files = task.target_files if task.target_files else []
    file1 = target_files[0] if len(target_files) > 0 else "file1"
    file2 = target_files[1] if len(target_files) > 1 else "file2"
    
    # Check what's been done
    state = self._analysis_tracker.get_or_create_state(task.task_id)
    
    # Count tool executions
    files_read = set()
    architecture_read = False
    comparison_done = False
    
    for tool_call in state.tool_calls_history:
        tool_name = tool_call['tool']
        arguments = tool_call.get('arguments', {})
        
        if tool_name == 'read_file':
            filepath = arguments.get('filepath', '')
            if file1 in filepath:
                files_read.add(file1)
            if file2 in filepath:
                files_read.add(file2)
            if 'ARCHITECTURE' in filepath:
                architecture_read = True
        
        if tool_name == 'compare_file_implementations':
            comparison_done = True
    
    # CRITICAL: If analysis is complete, FORCE resolution
    analysis_complete = (
        len(files_read) >= 2 and 
        architecture_read and 
        comparison_done
    )
    
    if analysis_complete:
        # FORCE RESOLUTION - NO MORE ANALYSIS ALLOWED
        return f"""🚨 CRITICAL: ANALYSIS COMPLETE - TAKE ACTION NOW! 🚨

{context}

═══════════════════════════════════════════════════════════════
⛔ ANALYSIS PHASE IS COMPLETE ⛔

You have already:
✅ Read both files
✅ Read ARCHITECTURE.md
✅ Compared implementations

🚫 DO NOT READ ANY MORE FILES
🚫 DO NOT DO ANY MORE ANALYSIS
🚫 DO NOT COMPARE AGAIN

═══════════════════════════════════════════════════════════════
🎯 YOU MUST NOW RESOLVE THE CONFLICT 🎯

Choose ONE of these resolution tools:

1️⃣ merge_file_implementations - Merge the files
2️⃣ move_file - Move one file to correct location
3️⃣ rename_file - Rename one file
4️⃣ create_issue_report - Report for manual review

═══════════════════════════════════════════════════════════════
⚠️ CRITICAL REQUIREMENT ⚠️

You MUST use ONE of the resolution tools above.
If you use read_file or any analysis tool, the task will FAIL.

This is attempt {task.attempts} - you've analyzed enough!
NOW TAKE ACTION TO RESOLVE THE CONFLICT!

═══════════════════════════════════════════════════════════════

🎯 OUTPUT YOUR RESOLUTION TOOL CALL NOW:
"""
    
    # Otherwise, guide through analysis steps
    if file1 not in files_read:
        return f"""🎯 STEP 1: Read {file1}

Use: read_file(filepath="{file1}")
"""
    
    if file2 not in files_read:
        return f"""🎯 STEP 2: Read {file2}

Use: read_file(filepath="{file2}")
"""
    
    if not architecture_read:
        return f"""🎯 STEP 3: Read ARCHITECTURE.md

Use: read_file(filepath="ARCHITECTURE.md")
"""
    
    if not comparison_done:
        return f"""🎯 STEP 4: Compare implementations

Use: compare_file_implementations(file1="{file1}", file2="{file2}")
"""
    
    # Fallback (should never reach here)
    return f"""🎯 RESOLVE THE CONFLICT

Use one of: merge_file_implementations, move_file, rename_file, create_issue_report
"""
```

## Key Changes

1. **Analysis Complete Detection**: Check if all analysis steps are done
2. **HARD STOP**: When analysis is complete, FORBID any more analysis tools
3. **FORCE RESOLUTION**: Make it crystal clear that ONLY resolution tools are allowed
4. **Clear Consequences**: Warn that using analysis tools will cause failure
5. **Simple Choice**: Present exactly 4 resolution options

## Expected Behavior After Fix

### Before (BROKEN)
```
Attempt 1: read_file(file1)
Attempt 2: read_file(file2)
Attempt 3: read_file(ARCHITECTURE.md)
Attempt 4: compare_file_implementations()
Attempt 5: read_file(file1) again ❌
Attempt 6: read_file(file2) again ❌
Attempt 7: read_file(ARCHITECTURE.md) again ❌
... infinite loop
```

### After (WORKING)
```
Attempt 1: read_file(file1)
Attempt 2: read_file(file2)
Attempt 3: read_file(ARCHITECTURE.md)
Attempt 4: compare_file_implementations()
Attempt 5: merge_file_implementations() ✅
Task complete!
```

## Validation Logic Enhancement

Also need to enhance the validation to REJECT analysis tools after analysis is complete:

```python
def _validate_tool_selection(self, task, tool_name, state):
    """Validate that the AI is using appropriate tools."""
    
    # Check if analysis is complete
    analysis_complete = self._is_analysis_complete(task, state)
    
    if analysis_complete:
        # Analysis is done - ONLY resolution tools allowed
        resolution_tools = [
            'merge_file_implementations',
            'move_file',
            'rename_file',
            'create_issue_report',
            'mark_task_complete'
        ]
        
        if tool_name not in resolution_tools:
            return False, f"Analysis complete - must use resolution tool, not {tool_name}"
    
    return True, "Tool selection valid"
```

## Implementation Priority

This is a **CRITICAL FIX** that should be implemented immediately. Without it, the refactoring phase will continue to loop indefinitely on integration conflict tasks.