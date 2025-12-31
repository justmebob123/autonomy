# CRITICAL: Refactoring Phase Infinite Loop Analysis

## Problem

The refactoring phase is stuck in an infinite loop doing the SAME analysis repeatedly without creating tasks or fixing issues.

**Observed Behavior** (14+ iterations):
```
ITERATION 1-14: 
  → Calls detect_duplicate_implementations
  → Finds 1 duplicate set (31 lines)
  → Says "no issues found, codebase is clean"
  → Suggests next: coding
  → Coordinator triggers refactoring again
  → REPEAT
```

## Root Cause Analysis

### 1. LLM Response Format Issue

The LLM is returning tool calls as TEXT instead of proper format:

**What LLM Returns:**
```
🔧 Tool calls: None
💬 Preview: {"name": "detect_duplicate_implementations", "arguments": {"scope": "project", "similarity_threshold": 0.7}}
```

**What Should Happen:**
```
🔧 Tool calls: [{"name": "detect_duplicate_implementations", ...}]
```

### 2. Tool Execution But No Task Creation

The handler successfully extracts and executes the tool:
```
✅ Found 1 duplicate sets
   Estimated reduction: ~31 lines
```

**BUT**: The LLM never calls `create_refactoring_task` to actually create work items!

### 3. False Success Return

The phase logic:
```python
# Check if tasks were created
pending = self._get_pending_refactoring_tasks(state)

if pending:
    # Has tasks - continue working
    return success
else:
    # NO tasks - assumes codebase is clean
    self.logger.info("✅ No refactoring issues found, codebase is clean")
    return PhaseResult(
        success=True,
        next_phase="coding"
    )
```

**The flaw**: It assumes "no tasks = clean" but actually "no tasks = LLM didn't create them"!

### 4. Coordinator Re-triggers

The coordinator sees:
- Refactoring phase succeeded ✅
- But `_detect_duplicate_patterns()` still returns True ❌
- So it triggers refactoring again ❌

## The Real Problem

**The refactoring phase has TWO modes but they're not working together:**

**Mode 1: Analysis** (what's happening)
- Detect duplicates ✅
- Find issues ✅
- Return results ✅

**Mode 2: Task Creation** (what's NOT happening)
- Create refactoring tasks ❌
- Track work to be done ❌
- Actually fix issues ❌

**The LLM is stuck in Mode 1 and never transitions to Mode 2!**

## Why This Happens

### Issue 1: Prompt Doesn't Guide Task Creation

The prompt says "analyze and create tasks" but the LLM just analyzes and stops.

### Issue 2: No Explicit Task Creation Step

After analysis, there's no explicit step that says:
"Now create a refactoring task for each issue found"

### Issue 3: Tool Call Format

The LLM returns tool calls as text, which get extracted and executed, but then the conversation doesn't continue to create tasks.

## Solutions

### Solution 1: Auto-Create Tasks from Analysis Results (RECOMMENDED)

```python
def _analyze_and_create_tasks(self, state: PipelineState) -> PhaseResult:
    # Analyze
    result = self._handle_comprehensive_refactoring(state)
    
    # Extract tool results
    tool_results = result.get('tool_results', [])
    
    # Auto-create tasks for found issues
    tasks_created = 0
    for tool_result in tool_results:
        if tool_result.get('tool') == 'detect_duplicate_implementations':
            duplicates = tool_result.get('duplicates', [])
            for dup in duplicates:
                self._auto_create_duplicate_task(dup, state)
                tasks_created += 1
    
    if tasks_created > 0:
        self.logger.info(f"  ✅ Auto-created {tasks_created} refactoring tasks")
        return PhaseResult(success=True, next_phase="refactoring")
    else:
        self.logger.info("  ✅ No issues found, codebase is clean")
        return PhaseResult(success=True, next_phase="coding")
```

### Solution 2: Fix Prompt to Explicitly Create Tasks

Add to prompt:
```
After detecting issues, you MUST create refactoring tasks using create_refactoring_task tool.

For each duplicate found:
1. Call detect_duplicate_implementations
2. For EACH duplicate in results, call create_refactoring_task
3. Continue until all issues have tasks created
```

### Solution 3: Multi-Step Workflow

```python
def _analyze_and_create_tasks(self, state: PipelineState) -> PhaseResult:
    # Step 1: Detect issues
    issues = self._detect_all_issues(state)
    
    # Step 2: Create tasks for each issue
    for issue in issues:
        self._create_task_for_issue(issue, state)
    
    # Step 3: Verify tasks created
    pending = self._get_pending_refactoring_tasks(state)
    
    return PhaseResult(success=True, next_phase="refactoring" if pending else "coding")
```

## Recommended Fix

**Implement Solution 1** (Auto-create tasks) because:
- ✅ Doesn't rely on LLM behavior
- ✅ Guaranteed to create tasks when issues found
- ✅ Simple and reliable
- ✅ Breaks the infinite loop immediately

## Implementation

1. Add `_auto_create_duplicate_task()` method
2. Add `_auto_create_complexity_task()` method
3. Add `_auto_create_dead_code_task()` method
4. Modify `_analyze_and_create_tasks()` to auto-create tasks
5. Only return "clean" when NO issues detected

## Expected Behavior After Fix

```
ITERATION 1: Refactoring
  → Detects 1 duplicate (31 lines)
  → Auto-creates 1 refactoring task
  → Returns success, next=refactoring

ITERATION 2: Refactoring
  → Has 1 pending task
  → Works on task (merges duplicates)
  → Marks task complete
  → Returns success, next=refactoring

ITERATION 3: Refactoring
  → No pending tasks
  → Analyzes again
  → No duplicates found
  → Returns success, next=coding

ITERATION 4: Coding
  → Continues development
```

## Priority

**CRITICAL** - System is completely non-functional in refactoring phase