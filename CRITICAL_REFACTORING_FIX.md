# 🚨 CRITICAL REFACTORING FIX - Root Cause Analysis

## The Problem

The refactoring phase is stuck in an infinite loop where:
1. AI reads ONE file
2. System detects "no resolution tool used"
3. Task is retried
4. AI reads the SAME file again
5. Repeat forever

## Root Causes Identified

### Issue #1: AI Returns Text Instead of Tool Calls
```
[INFO]   🔧 Tool calls: None
[INFO]   💬 Preview: {"name": "read_file", "arguments": {...}}
[INFO]   Extracted tool call from text response
```

The AI is returning tool calls as TEXT, not using structured tool calling. This suggests:
- Model doesn't understand tool calling format
- Prompt isn't clear enough about tool usage
- Model is confused about what action to take

### Issue #2: Step-Aware Prompt Not Working
The step-aware prompt checks `TaskAnalysisTracker.tool_calls_history` to determine which step we're at, but:
- On retry, the tracker state is NOT reset
- So on attempt 2, it still thinks we're at step 5 (all analysis done)
- But the AI only read ONE file, not all files needed

### Issue #3: Hard Limit Not Triggering
The hard limit (force `request_developer_review` after 3 tools) doesn't trigger because:
- AI only makes 1 tool call per attempt
- Never reaches the 3-tool threshold
- Gets retried before hitting the limit

### Issue #4: Retry Prompt Not Strong Enough
The retry message is added to `task.analysis_data['retry_reason']`, but:
- It's buried in the context
- Not prominent enough
- AI ignores it and repeats the same action

## The Solution

We need a MULTI-LAYERED fix:

### Fix #1: Reset TaskAnalysisTracker on Retry
When a task is retried, RESET the tracker state so step detection works correctly.

### Fix #2: Make Retry Prompt UNMISSABLE
Put the retry warning at the TOP of the prompt in a huge box that the AI cannot ignore.

### Fix #3: Lower Hard Limit Threshold
Change from 3 tools to 2 tools before forcing escalation.

### Fix #4: Add Tool Call Validation
Check if AI is returning text instead of tool calls, and add explicit guidance.

### Fix #5: Simplify the Workflow
Instead of step-aware prompts, use a simpler approach:
- Attempt 1: Normal prompt
- Attempt 2: "You failed, try again with THIS specific action"
- Attempt 3: Force escalation automatically

## Implementation Plan

1. Modify `_get_integration_conflict_prompt()` to:
   - Check attempt number FIRST
   - On attempt 2+, show HUGE warning box at top
   - Simplify the workflow (no step-aware logic)

2. Reset TaskAnalysisTracker when task is retried:
   - Add `self._analysis_tracker.reset_state(task.task_id)` before retry

3. Lower hard limit from 3 to 2 tools

4. Add explicit tool calling guidance to system prompt

Let's implement these fixes now.