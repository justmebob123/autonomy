# Critical Bug Fixes: Task Reactivation and Error Context

## Problem 1: QA_FAILED Tasks Not Being Reactivated ✅ FIXED
- Pipeline had 69-79 tasks stuck in QA_FAILED status
- Coordinator only checked for SKIPPED and FAILED, missing QA_FAILED
- Result: "Reactivated 0 tasks" infinite loop
- **FIXED in commit 6c1cb39**

## Problem 2: Error Context Lost on Reactivation 🔴 CRITICAL
- When tasks are reactivated, `task.attempts` is reset to 0
- Error context only shown when `task.attempts > 1`
- Result: LLM doesn't see the detailed error context with full file content
- LLM repeats the same mistake because it doesn't know what went wrong

## Solution for Problem 2
**Option A**: Don't reset attempts counter when reactivating
**Option B**: Always show error context if task has errors, regardless of attempts
**Option C**: Preserve error history separately from attempts counter

**CHOSEN**: Option B - Show error context whenever task has errors

## Tasks
- [x] Identify QA_FAILED bug in coordinator.py
- [x] Fix QA_FAILED reactivation logic
- [x] Commit and push QA_FAILED fix
- [x] Identify error context bug
- [x] Fix error context display logic
- [x] Commit and push
- [ ] User to test the complete fix