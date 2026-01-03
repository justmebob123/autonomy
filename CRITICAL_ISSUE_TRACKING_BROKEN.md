# 🚨 CRITICAL: ISSUE TRACKING SYSTEM IS COMPLETELY BROKEN

## The Problem

**QA finds issues, but NO phase ever fixes them. Issues are reported and then FORGOTTEN.**

## What's Happening (From Your Logs)

### ✅ QA Phase Works:
```
01:20:29 [INFO] 🤖 [AI Activity] Calling tool: report_issue
01:20:29 [INFO]    └─ filepath: api/prompts.py
01:20:29 [INFO]    └─ issue_type: incomplete
01:20:29 [INFO]    └─ description: Function add_prompt is defined but never called...
01:20:29 [WARNING]   ⚠ Found 1 issues
01:20:29 [INFO]   📤 Sent 1 issues to debugging phase
01:20:29 [INFO]   💡 Phase suggests next: debugging
```

### ❌ But Then:
```
01:20:53 [INFO]   ITERATION 3 - PLANNING
01:20:53 [INFO]   Reason: Need to plan next steps
```

**Coordinator IGNORES the "debugging" suggestion and goes to PLANNING instead!**

## Root Causes

### Issue #1: QA Issues Don't Create Tasks
When QA calls `report_issue`, it:
1. Logs the issue
2. Sends a message to debugging phase via IPC
3. Sets `_next_phase_hint = 'debugging'`

**BUT**: It does NOT create a `TaskState` with `status = NEEDS_FIXES`

The coordinator checks:
```python
needs_fixes = [t for t in state.tasks.values() if t.status == TaskStatus.NEEDS_FIXES]
if needs_fixes:
    return {'phase': 'debugging', ...}
```

Since no tasks have `NEEDS_FIXES` status, debugging is never triggered!

### Issue #2: Phase Hints Are Ignored
QA sets `state._next_phase_hint = 'debugging'`, but:
1. Coordinator checks for `pending` tasks first
2. Finds 22 pending tasks
3. Routes to CODING
4. Phase hint is never checked because pending tasks take priority

### Issue #3: Debugging Phase Doesn't Read IPC Messages
Even if debugging phase was triggered, it:
1. Expects an `issue` parameter passed directly
2. Does NOT read from `DEBUGGING_READ.md` IPC document
3. Would have no idea what issues QA reported

### Issue #4: Coding Phase Never Fixes Existing Files
Coding phase:
1. Reads from `DEVELOPER_READ.md` (new tasks only)
2. Creates NEW files
3. Never goes back to FIX existing files with issues
4. Has no mechanism to read QA issue reports

## The Complete Broken Flow

```
QA Phase:
  ├─ Finds issue in api/prompts.py
  ├─ Calls report_issue tool
  ├─ Writes to DEBUGGING_WRITE.md (IPC)
  ├─ Sets _next_phase_hint = 'debugging'
  └─ Returns success

Coordinator:
  ├─ Checks needs_fixes tasks: NONE (❌ QA didn't create task)
  ├─ Checks pending tasks: 22 found
  ├─ Routes to CODING (ignores phase hint)
  └─ Issue is FORGOTTEN

Coding Phase:
  ├─ Reads DEVELOPER_READ.md (new tasks)
  ├─ Creates NEW file (core/parser.py)
  ├─ Never reads QA issue reports
  └─ api/prompts.py issue NEVER FIXED

Result: Issue reported but NEVER addressed
```

## What Should Happen

```
QA Phase:
  ├─ Finds issue in api/prompts.py
  ├─ Creates TaskState with:
  │   ├─ status = NEEDS_FIXES
  │   ├─ target_file = "api/prompts.py"
  │   ├─ description = "Function add_prompt never called"
  │   └─ issue_data = {...}
  └─ Returns success

Coordinator:
  ├─ Checks needs_fixes tasks: 1 found ✅
  ├─ Routes to DEBUGGING
  └─ Passes task to debugging phase

Debugging Phase:
  ├─ Receives task with issue details
  ├─ Reads api/prompts.py
  ├─ Fixes the issue
  ├─ Marks task as COMPLETED
  └─ Returns success

Result: Issue FIXED ✅
```

## The Fix Required

### Fix #1: QA Must Create NEEDS_FIXES Tasks
Modify `pipeline/phases/qa.py`:
```python
def execute(self, state, ...):
    # ... existing code ...
    
    if issues_found:
        # CREATE A TASK for each issue
        for issue in issues_found:
            task = TaskState(
                task_id=f"qa_fix_{filepath}_{issue['line_number']}",
                description=f"Fix {issue['issue_type']} in {filepath}: {issue['description']}",
                target_file=filepath,
                status=TaskStatus.NEEDS_FIXES,
                priority=self._get_priority_for_issue_type(issue['issue_type']),
                issue_data=issue
            )
            state.tasks[task.task_id] = task
        
        # Save state so coordinator sees the NEEDS_FIXES tasks
        self.state_manager.save(state)
```

### Fix #2: Coordinator Must Prioritize NEEDS_FIXES
Already works! The coordinator checks:
```python
if needs_fixes:
    return {'phase': 'debugging', 'task': needs_fixes[0], ...}
```

This is BEFORE checking pending tasks, so it will work once QA creates the tasks.

### Fix #3: Debugging Phase Must Handle Tasks
Already works! Debugging phase accepts a `task` parameter:
```python
def execute(self, state, task=None, issue=None, **kwargs):
    if task and task.status == TaskStatus.NEEDS_FIXES:
        # Extract issue from task
        issue = task.issue_data
        filepath = task.target_file
        # ... fix the issue ...
```

### Fix #4: After Fix, Mark Task Complete
Debugging phase must:
```python
# After successful fix
task.status = TaskStatus.COMPLETED
task.completion_time = datetime.now()
self.state_manager.save(state)
```

## Summary

**The entire issue tracking system is broken because QA reports issues but doesn't create tasks.**

The fix is simple:
1. QA creates `NEEDS_FIXES` tasks when it finds issues
2. Coordinator already routes to debugging for `NEEDS_FIXES` tasks
3. Debugging already handles tasks
4. Just need to connect the pieces!

**Without this fix, ALL QA issues are IGNORED and NEVER FIXED.**