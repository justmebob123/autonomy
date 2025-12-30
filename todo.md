# Fix modify_file Error Handling - Continue Conversation Instead of Retry

## Problem
Currently when `modify_file` fails, we do an IMMEDIATE RETRY in the same iteration. This is WRONG.

We should:
1. Add error context with full file content to the task
2. Return from current iteration (mark task as IN_PROGRESS, not FAILED)
3. Next iteration picks up same task
4. Error context is included in the message
5. LLM sees full file and uses `full_file_rewrite`

This allows the conversation to continue naturally instead of forcing a retry.

## Tasks

### [x] Phase 1: Understand Current Flow
- [x] Analyze how error context is added to tasks
- [x] Understand how next iteration picks up tasks
- [x] Verify error context is included in messages

### [x] Phase 2: Remove Immediate Retry Logic
- [x] Removed the immediate retry code (was lines 285-335 in coding.py)
- [x] Kept the error context creation
- [x] Return from iteration after adding error context
- [x] Task stays IN_PROGRESS (not marked as FAILED)
- [x] Fixed comment about when task is marked FAILED

### [x] Phase 3: Ensure Next Iteration Picks Up Task
- [x] Verified task selection logic picks IN_PROGRESS tasks (line 482-483 in state/manager.py)
- [x] Verified error context is included in message building (lines 476-478 in coding.py)
- [x] Verified error context is retrieved (line 117 in coding.py)
- [x] Flow is complete: task stays IN_PROGRESS → next iteration picks it up → error context included

### [ ] Phase 4: Test and Verify
- [ ] User will test with a modify_file failure scenario
- [ ] User will verify error context is shown to LLM
- [ ] User will verify LLM can use full_file_rewrite
- [ ] User will verify no immediate retry happens

### [x] Phase 5: Documentation and Commit
- [x] Created MODIFY_FILE_CONVERSATION_FIX.md with complete documentation
- [x] Documented the problem, solution, implementation, and benefits
- [x] Committed changes with descriptive message
- [x] Pushed to GitHub (commit 50ba1dd)