# Critical Bug Fix: full_file_rewrite Tool Doesn't Exist

## Problem 1: QA_FAILED Tasks Not Being Reactivated ✅ FIXED
- **FIXED in commit 6c1cb39**

## Problem 2: Error Context Lost on Reactivation ✅ FIXED  
- **FIXED in commit 3489625**

## Problem 3: full_file_rewrite Tool Doesn't Exist 🔴 CRITICAL
- Error messages tell LLM to use `full_file_rewrite` tool
- But `full_file_rewrite` is NOT registered in handlers
- Available tools: `create_file`, `modify_file`, etc.
- LLM tries to use `full_file_rewrite` → "Unknown tool" error
- Task fails again with same error

### Evidence
```
TOOL CALL FAILURE: Unknown tool 'full_file_rewrite'
Available tools: create_file, modify_file, ...
```

### References to non-existent tool
- `pipeline/phases/coding.py`: "Use the full_file_rewrite tool"
- `pipeline/phases/coding.py`: "DO NOT use modify_file again - use full_file_rewrite"
- `pipeline/handlers.py`: "use full_file_rewrite instead"
- Multiple other files reference this non-existent tool

## Solution Options
**Option A**: Add `full_file_rewrite` as alias for `create_file` in handlers
**Option B**: Change all error messages to say `create_file` instead
**Option C**: Create actual `full_file_rewrite` tool with proper implementation

**CHOSEN**: Option A - Add alias (quickest, safest fix)

## Tasks
- [x] Identify QA_FAILED bug
- [x] Fix QA_FAILED reactivation
- [x] Identify error context bug
- [x] Fix error context display
- [x] Identify full_file_rewrite bug
- [x] Add full_file_rewrite as alias for create_file in handlers
- [x] Add full_file_rewrite tool definition
- [x] Commit and push
- [ ] User to test the complete fix