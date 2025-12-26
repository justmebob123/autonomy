# Workflow Priority Fix - Development First

## Problem

User runs system expecting it to **start developing**, but instead:
1. System loads old state with QA_PENDING tasks
2. Prioritizes QA over coding
3. Runs QA phase repeatedly
4. User frustrated - "I just wanted it to begin developing"

## Root Causes

### 1. Wrong Priority Order
Current priority in `_determine_next_action()`:
```
0. Loop prevention hints
1. Initial planning (if no tasks)
2. QA for code awaiting review ❌ WRONG - QA before coding
3. Debugging for fixes
4. Coding for new/in-progress tasks
5. Documentation
6. Project planning
```

**Problem**: QA has higher priority than coding!

### 2. Resume Defaults to True
```python
resume = not args.fresh  # Defaults to True
```

When user runs without `--fresh`, system loads old state with QA_PENDING tasks, then prioritizes QA.

### 3. No Development-First Mode
No way to say "ignore old QA tasks, just start coding"

## User Expectations

When running `python3 run.py /path/to/project`:
1. **Start developing** (primary goal)
2. Check MASTER_PLAN.md for objectives
3. Create/continue tasks
4. Write code
5. QA can happen **after** coding

**NOT**:
1. Load old state
2. Run QA on old code
3. Run documentation updates
4. Eventually maybe code

## Solutions

### Solution 1: Fix Priority Order (CRITICAL)

Change priority to be development-first:

```python
def _determine_next_action(self, state: PipelineState) -> Dict:
    """
    Priority order (DEVELOPMENT FIRST):
    0. Loop prevention hints
    1. Initial planning (if no tasks)
    2. Coding for new/in-progress tasks ✅ CODING FIRST
    3. QA for code awaiting review
    4. Debugging for fixes
    5. Documentation
    6. Project planning
    """
    
    # 0. Loop prevention hints
    if hasattr(state, '_next_phase_hint') and state._next_phase_hint:
        ...
    
    # 1. Initial planning
    if state.needs_planning:
        return {"phase": "planning", "reason": "initial_planning"}
    
    # 2. CODING FIRST - New or in-progress tasks
    pending_tasks = [
        t for t in state.tasks.values()
        if t.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
    ]
    if pending_tasks:
        task = min(pending_tasks, key=lambda t: t.priority)
        return {"phase": "coding", "task": task, "reason": "implement_task"}
    
    # 3. QA - Only after no pending coding tasks
    for task in state.tasks.values():
        if task.status == TaskStatus.QA_PENDING:
            ...
            return {"phase": "qa", "task": task, "reason": "review_completed_code"}
    
    # 4. Debugging
    for task in state.tasks.values():
        if task.status == TaskStatus.NEEDS_FIXES:
            ...
            return {"phase": "debugging", "task": task, "reason": "fix_issues"}
    
    # 5. Documentation (only if tasks recently completed)
    ...
    
    # 6. Project planning (expand when all done)
    ...
```

### Solution 2: Add --resume Flag (Better UX)

Make resume explicit, default to fresh start:

```python
parser.add_argument(
    "--resume",
    action="store_true",
    help="Resume from saved state (default: start fresh)"
)

# In main()
resume = args.resume  # Defaults to False
```

**Behavior**:
- `python3 run.py /path` → Fresh start, begin coding
- `python3 run.py /path --resume` → Resume from saved state
- `python3 run.py /path --fresh` → Explicit fresh start (kept for compatibility)

### Solution 3: Smart Resume Logic

When resuming, skip stale QA tasks:

```python
if resume:
    state = self.state_manager.load()
    
    # Skip stale QA tasks if user wants to start coding
    stale_qa_count = sum(1 for t in state.tasks.values() if t.status == TaskStatus.QA_PENDING)
    if stale_qa_count > 0:
        self.logger.info(f"  Found {stale_qa_count} stale QA tasks from previous run")
        self.logger.info("  Marking as COMPLETED to prioritize new development")
        for task in state.tasks.values():
            if task.status == TaskStatus.QA_PENDING:
                task.status = TaskStatus.COMPLETED
        self.state_manager.save(state)
```

## Recommended Implementation

### Phase 1: Fix Priority Order (IMMEDIATE)
Change `_determine_next_action()` to prioritize coding over QA.

**Impact**: Development-first workflow
**Risk**: Low - just reordering logic
**Effort**: 10 minutes

### Phase 2: Change Resume Default (HIGH)
Make `--resume` explicit, default to fresh start.

**Impact**: Better UX, matches user expectations
**Risk**: Medium - changes default behavior
**Effort**: 5 minutes

### Phase 3: Add Smart Resume (OPTIONAL)
Skip stale QA tasks when resuming.

**Impact**: Cleaner resume behavior
**Risk**: Low - only affects resume mode
**Effort**: 15 minutes

## Testing

After implementing:

```bash
# Test 1: Fresh start (should begin coding)
python3 run.py /path/to/project
# Expected: Planning → Coding

# Test 2: Resume (should continue where left off)
python3 run.py /path/to/project --resume
# Expected: Load state → Continue

# Test 3: Fresh explicit (should start over)
python3 run.py /path/to/project --fresh
# Expected: Ignore state → Planning → Coding
```

## Priority

**CRITICAL** - This is a fundamental UX issue affecting every user.

User quote: "I just wanted it to begin developing, I wasn't looking for a massive documentation or QA phase."

This is the #1 complaint - system doesn't do what users expect.