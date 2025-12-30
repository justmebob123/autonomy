# Issue: Failed Tasks Not Immediately Retried with Error Context

## Problem

When `modify_file` fails:
1. Error context is created with full file content
2. Task is marked as FAILED
3. Phase returns with failure
4. **Different task is picked up next iteration**
5. Failed task sits in queue without being retried
6. Error context is never used

## Example from Log

```
Iteration 7: asas/alerts/local.py - modify_file fails
Iteration 8: asas/alerts/webhook.py - different task!
```

The failed task with error context is not retried immediately.

## Root Cause

In `pipeline/phases/coding.py`, when tool execution fails:
```python
task.status = TaskStatus.FAILED
return PhaseResult(success=False, ...)
```

This returns immediately, and the coordinator picks a different task for the next iteration.

## Solution Options

### Option A: Retry Immediately (Recommended)
When `modify_file` fails with "Original code not found":
1. Add error context to task
2. **Do NOT mark as FAILED yet**
3. **Retry immediately in same iteration**
4. Only mark FAILED if retry also fails

### Option B: Priority Queue
Mark failed tasks with error context as high priority so they're picked up next

### Option C: Dedicated Retry Phase
Create a phase specifically for retrying failed tasks with error context

## Recommended Fix

Modify `pipeline/phases/coding.py` to retry immediately when modify_file fails:

```python
if result.get("tool") == "modify_file" and "Original code not found" in error_msg:
    # Add error context
    task.add_error("modify_file_failed", error_context, phase="coding")
    
    # RETRY IMMEDIATELY with error context
    self.logger.info("  🔄 Retrying with full file content...")
    
    # Get error context and rebuild message
    error_ctx = task.get_error_context()
    retry_message = self._build_user_message(task, context, error_ctx)
    
    # Call model again
    retry_response = self.chat_with_history(retry_message, tools)
    
    # Process retry response
    # ... (handle retry results)
```

This ensures the LLM sees the error context immediately and can use `full_file_rewrite`.