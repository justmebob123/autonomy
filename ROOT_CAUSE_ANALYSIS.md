# ROOT CAUSE: Why Tasks Are Being Skipped

## The Real Problem

Looking at the logs:
```
AI: compare_file_implementations(file1, file2)
Result: 0% similar, manual_review recommended
System: ⚠️ Only analysis performed, auto-creating issue report
System: ✅ Task resolved by creating issue report
```

**The AI is NEVER being forced to read the files.**

## Why This Happens

1. **AI calls compare_file_implementations first** (allowed by prompt)
2. **Gets 0% similarity** 
3. **System checks**: Did AI use read_file? NO
4. **System should**: FAIL and retry with error message
5. **But instead**: Auto-creates report and marks complete

## The Bug

In `refactoring.py` line ~500:

```python
if not tried_to_understand:
    # AI was lazy - give it ONE MORE CHANCE
    error_msg = "You only compared files without reading them..."
    task.fail(error_msg)
    return PhaseResult(success=False, ...)  # Should retry
```

**BUT** the task is marked as FAILED, not PENDING. So it doesn't retry - it just moves to the next task!

## The Fix Needed

When AI is lazy (only compares without reading):
1. **Don't mark task as FAILED** - mark as PENDING
2. **Add error context** to force reading
3. **Retry the SAME task** with stronger guidance
4. **Only after 2-3 attempts** should we auto-create report

## Current Flow (BROKEN)

```
Iteration 1:
  Task: refactor_0358
  AI: compare_file_implementations(...)
  System: "Only compared without reading - FAILED"
  Task Status: FAILED
  
Iteration 2:
  Task: refactor_0359 (NEXT TASK, not retry!)
  AI: compare_file_implementations(...)
  System: "Only compared without reading - FAILED"
  Task Status: FAILED
```

**Tasks are being SKIPPED, not RETRIED!**

## Correct Flow (NEEDED)

```
Iteration 1:
  Task: refactor_0358
  AI: compare_file_implementations(...)
  System: "Only compared without reading - RETRY"
  Task Status: PENDING (with error context)
  
Iteration 2:
  Task: refactor_0358 (SAME TASK, retry!)
  AI: read_file(file1), read_file(file2), read_file("ARCHITECTURE.md")
  AI: Decision based on understanding
  AI: merge_file_implementations(...) OR update_architecture(...)
  Task Status: COMPLETED
```

## The Critical Bug

**task.fail(error_msg)** marks the task as FAILED and moves to next task.

**Should be**: Keep task as PENDING, add error context, retry same task.

## Implementation Fix

```python
if not tried_to_understand:
    # AI was lazy - RETRY with stronger guidance
    self.logger.warning(f"Task {task.task_id}: Only compared without reading - RETRYING")
    
    # DON'T mark as failed - keep as pending with error context
    # task.fail(error_msg)  # WRONG - skips to next task
    
    # Add error context for retry
    if not hasattr(task, 'retry_count'):
        task.retry_count = 0
    task.retry_count += 1
    
    if task.retry_count >= 3:
        # After 3 attempts, auto-create report
        # ... auto-report logic ...
    else:
        # Retry with stronger guidance
        error_context = (
            f"ATTEMPT {task.retry_count + 1}/3: "
            "You only compared files without reading them. "
            "You MUST read both files to understand their purpose. "
            "Use read_file on both files, then check ARCHITECTURE.md."
        )
        
        # Keep task pending, add error context
        return PhaseResult(
            success=False,
            phase=self.phase_name,
            message=error_context,
            retry_same_task=True  # Signal to retry same task
        )
```

## Why Tasks Are Being "Skipped"

They're not being skipped - they're being **FAILED and moved past**.

The system thinks:
- "AI tried and failed, move to next task"

When it should think:
- "AI was lazy, make it try again with stronger guidance"

## The Solution

**RETRY LOGIC** instead of **FAIL LOGIC**

- Attempt 1: AI compares → System: "Read files first" → RETRY
- Attempt 2: AI reads files → AI makes decision → COMPLETE
- Attempt 3 (if needed): AI still lazy → Auto-create report → COMPLETE

**Every task gets 2-3 chances before being documented.**