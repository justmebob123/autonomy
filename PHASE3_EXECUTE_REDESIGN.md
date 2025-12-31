# Phase 3: Multi-Iteration Execute Method Redesign

## Current Flow (Single Iteration)
```
execute(state)
  → _determine_refactoring_type()
  → _handle_comprehensive_refactoring()
    → Analyze codebase
    → Execute tools
    → Return PhaseResult(next_phase="coding")
```

## Target Flow (Multi-Iteration)
```
execute(state)
  → Initialize refactoring_manager if needed
  → Get pending refactoring tasks
  
  IF no pending tasks:
    → Analyze codebase (comprehensive)
    → Create tasks from issues found
    → Return PhaseResult(next_phase="refactoring")  # Continue
  
  ELSE:
    → Select next task (by priority)
    → Work on task
      → Build context
      → Call LLM with tools
      → Execute tool calls
      → Update task status
    
    → Check if more tasks remain
    IF more tasks:
      → Return PhaseResult(next_phase="refactoring")  # Continue
    ELSE:
      → Re-analyze codebase
      IF new issues found:
        → Create new tasks
        → Return PhaseResult(next_phase="refactoring")  # Continue
      ELSE:
        → Return PhaseResult(next_phase="coding")  # Complete
```

## Implementation Plan

### Step 1: Add Task System Integration
- Initialize RefactoringTaskManager in execute()
- Store in state.refactoring_manager
- Persist across iterations

### Step 2: Add Analysis → Task Creation
- When no pending tasks, run comprehensive analysis
- Parse analysis results
- Create RefactoringTask for each issue
- Prioritize tasks

### Step 3: Add Task Execution Loop
- Select highest priority pending task
- Build context for task
- Call LLM with task-specific prompt
- Execute tool calls
- Update task status

### Step 4: Add Completion Detection
- After task completion, check for more tasks
- If no tasks, re-analyze
- If no new issues, mark refactoring complete
- Return appropriate next_phase

### Step 5: Add Conversation Continuity
- Maintain conversation history across iterations
- Build on previous analysis
- Reference completed tasks in context

## Key Methods to Add

1. `_initialize_refactoring_manager(state)` - Setup task manager
2. `_analyze_and_create_tasks(state)` - Analysis → tasks
3. `_select_next_task(state)` - Task selection
4. `_work_on_task(state, task)` - Task execution
5. `_check_completion(state)` - Completion detection
6. `_build_task_context(task)` - Task-specific context

## Backward Compatibility

Keep existing methods for now:
- `_handle_comprehensive_refactoring()` - Used when no task system
- `_handle_duplicate_detection()` - Can be called from tasks
- `_handle_conflict_resolution()` - Can be called from tasks
- etc.

## Next Steps

1. Implement new execute() method
2. Add helper methods
3. Update prompts for task-based refactoring
4. Test multi-iteration flow