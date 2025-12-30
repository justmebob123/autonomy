# Critical Bug Fix: modify_file Failures Not Retried

## Problem
When modify_file fails with "Original code not found":
1. Error context created with full file content
2. Task marked as FAILED
3. Phase returns
4. **Different task picked up next iteration**
5. Failed task never retried with error context
6. LLM never sees the full file content

## Solution: Immediate Retry
When modify_file fails:
1. Add error context to task
2. **Retry immediately in same iteration**
3. LLM sees full file content right away
4. Can use full_file_rewrite to fix the issue
5. Only mark FAILED if retry also fails

## Tasks
- [x] Identify the issue (tasks not retried immediately)
- [x] Implement immediate retry logic
- [ ] Test the fix
- [ ] Commit and push