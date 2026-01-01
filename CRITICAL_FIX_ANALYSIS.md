# Critical Root Cause Analysis: AI Infinite Loop

## The Problem
AI is stuck calling `read_file("resources/resource_estimator.py")` for 48+ consecutive attempts without making progress on integration conflict resolution.

## What's Happening

### AI Output (from logs):
```
Response length: 1,424 characters
Preview: {"name": "read_file", "arguments": {"filepath": "resources/resource_estimator.py"}} {"name": "read_file", "arguments": {"filepath": "core/resource/resource_estimator.py"}} {"name": "read_file", "argum...
```

**The AI is outputting 4 tool calls in a single response!**

### System Behavior:
1. AI outputs: `tool1 tool2 tool3 tool4`
2. System extracts: `tool1` (only the first one)
3. System executes: `tool1`
4. System checks: "Did you use a resolving tool?" → NO
5. System retries: "You didn't resolve, try again"
6. AI outputs: `tool1 tool2 tool3 tool4` (same sequence again!)
7. **INFINITE LOOP**

## Root Cause

The AI model (qwen2.5-coder:32b) is **NOT following the "ONE tool per iteration" instruction** despite:
- ⚠️ Multiple warnings in the prompt
- 📋 Step-by-step workflow showing one tool per step
- ✅ Examples showing correct vs wrong format
- 🎯 Explicit "DO NOT output multiple tools" warnings

**Why?** The AI is trying to be "efficient" by planning ahead and outputting all the tools it thinks it needs. But the system architecture only supports executing ONE tool at a time.

## The Mismatch

**System Architecture:**
- Designed for iterative execution
- One tool → get result → next tool
- Maintains conversation history between iterations
- Validates progress after each tool

**AI Behavior:**
- Outputs multiple tools at once
- Expects batch execution
- Doesn't wait for results
- Repeats same sequence when told to retry

## Why Current Fixes Haven't Worked

### Fix #1: "ONE tool per iteration" warning
- **Status**: Added in commit c4a2371
- **Result**: FAILED - AI still outputs multiple tools
- **Why**: AI doesn't understand or ignores the constraint

### Fix #2: Task-type-specific prompts  
- **Status**: Added in commit 905237f
- **Result**: PARTIAL - Reduced some loops, but integration conflicts still loop
- **Why**: Prompts still show multi-step workflows that AI interprets as "output all steps"

### Fix #3: Resolving tools recognition
- **Status**: Added in commit d6aef57
- **Result**: PARTIAL - File editing tools now recognized, but doesn't fix the loop
- **Why**: AI never gets to resolving tools because it's stuck on step 1

## The Real Solution Needed

We need to **FORCE** the AI to output only one tool by:

1. **State Tracking**: Track which step the AI is on (step 1, 2, 3, etc.)
2. **Step-Specific Prompts**: Give AI ONLY the next action, not the whole workflow
3. **Explicit Next Action**: Tell AI exactly which tool to call next
4. **Block Other Tools**: Make it impossible for AI to call wrong tools

### Example:

**Current Prompt (shows all steps):**
```
Step 1: read_file("file1")
Step 2: read_file("file2")  
Step 3: read_file("ARCHITECTURE.md")
Step 4: compare_file_implementations(...)
Step 5: merge_file_implementations(...)
```
→ AI outputs all 5 tools at once

**Fixed Prompt (shows only next step):**
```
YOU ARE ON STEP 1 OF 5

YOUR NEXT ACTION:
Call this ONE tool: read_file(filepath="resources/resource_estimator.py")

DO NOT call any other tools.
DO NOT output multiple tool calls.
Just call read_file with that exact filepath.
Then STOP.

The system will call you again for step 2.
```
→ AI outputs only 1 tool

## Implementation Plan

1. Add step tracking to RefactoringTask
2. Modify `_get_integration_conflict_prompt()` to be step-aware
3. Give AI ONLY the next action based on current step
4. Update step counter after each successful tool execution
5. Progress through steps: read1 → read2 → arch → compare → resolve

## Expected Result

**Before Fix:**
```
Attempt 1-48: AI outputs 4 tools, system executes tool1, retries
→ INFINITE LOOP
```

**After Fix:**
```
Attempt 1: AI outputs tool1, system executes, advances to step 2
Attempt 2: AI outputs tool2, system executes, advances to step 3
Attempt 3: AI outputs tool3, system executes, advances to step 4
Attempt 4: AI outputs tool4, system executes, advances to step 5
Attempt 5: AI outputs merge, system executes → ✅ RESOLVED
```

## Conclusion

The AI is not broken - it's just not following our instructions because the instructions are ambiguous. By showing the AI a 5-step workflow, we're implicitly telling it "here are 5 tools to call." The AI interprets this as "output all 5 tools."

The fix is to **only show the AI the NEXT step**, not the whole workflow. This forces the AI into the iterative execution model the system expects.