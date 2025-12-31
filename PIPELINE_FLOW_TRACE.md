# Complete Pipeline Flow Trace

## Pipeline Execution Flow

### 1. Entry Point: run.py
```
run.py
  → PipelineCoordinator.__init__()
  → PipelineCoordinator.run()
```

### 2. Coordinator Initialization
```
PipelineCoordinator.__init__()
  → StateManager.__init__()
  → _initialize_polytopic_structure()
  → _load_phases()
    → PlanningPhase()
    → CodingPhase()
    → QAPhase()
    → DebuggingPhase()
    → DocumentationPhase()
    → InvestigationPhase()
    → ProjectPlanningPhase()
    → RefactoringPhase()  # NEW
```

### 3. Main Loop
```
PipelineCoordinator.run()
  LOOP:
    → _select_next_phase(state)
      → _tactical_decision_tree(state)
        → Check debugging needed
        → Check pending tasks
        → Check QA needed
        → Check refactoring needed  # NEW
        → Default to planning
    
    → phase.execute(state)
      → Phase-specific logic
      → Tool calls via ToolCallHandler
      → IPC document updates
      → Return PhaseResult
    
    → _update_state(state, result)
    → _check_completion(state)
  END LOOP when complete or max iterations
```

### 4. Phase Execution Pattern

#### Standard Phase (e.g., Coding)
```
CodingPhase.execute(state)
  → _select_task(state)
  → _build_context(task)
  → chat_with_history(prompt, tools)
  → ToolCallHandler.process_tool_calls()
  → _update_task_status(task)
  → Return PhaseResult(next_phase="qa")
```

#### Refactoring Phase (Current)
```
RefactoringPhase.execute(state)
  → _determine_refactoring_type()
  → _handle_comprehensive_refactoring()
    → _build_comprehensive_context()
    → chat_with_history(prompt, tools)
    → ToolCallHandler.process_tool_calls()
    → _write_refactoring_results()
    → _determine_next_phase()
    → Return PhaseResult(next_phase="coding" or "refactoring")
```

#### Refactoring Phase (Target - Phase 2+)
```
RefactoringPhase.execute(state)
  → _get_pending_refactoring_tasks(state)
  
  IF no pending tasks:
    → _analyze_codebase(state)
    → _create_tasks_from_issues(issues)
    → _add_tasks_to_state(state, tasks)
  
  → _select_next_task(pending_tasks)
  → _work_on_task(state, task)
    → chat_with_history(prompt, tools)
    → ToolCallHandler.process_tool_calls()
    → _update_task_status(task)
  
  IF more tasks remain:
    → Return PhaseResult(next_phase="refactoring")
  ELSE:
    → _re_analyze_codebase(state)
    IF new issues found:
      → Return PhaseResult(next_phase="refactoring")
    ELSE:
      → Return PhaseResult(next_phase="coding")
```

### 5. Tool Call Flow

```
ToolCallHandler.process_tool_calls(tool_calls)
  FOR each tool_call:
    → _validate_tool_call(tool_call)
    → handler = self.handlers[tool_name]
    → result = handler(args)
    → _log_result(result)
  RETURN results
```

### 6. IPC Document Flow

```
Phase A writes:
  → phase_a.write_own_status(content)
  → Writes to .ai/PHASE_A_WRITE.md

Phase B reads:
  → phase_b.read_file(".ai/PHASE_A_WRITE.md")
  → Parses content
  → Uses in context
```

### 7. State Management Flow

```
StateManager
  → tasks: Dict[str, TaskState]
  → phases: Dict[str, PhaseState]
  → phase_history: List[str]
  → current_phase: str
  → completion_percentage: float
  → project_phase: str  # foundation, integration, consolidation, completion
```

### 8. Task Lifecycle

```
Task Creation:
  Planning → create_task() → TaskState(status=NEW)

Task Assignment:
  Coordinator → _select_next_phase() → Routes to appropriate phase

Task Execution:
  Phase → execute() → TaskState(status=IN_PROGRESS)

Task Completion:
  Phase → mark_complete() → TaskState(status=COMPLETED)
  OR
  Phase → mark_qa_pending() → TaskState(status=QA_PENDING)

Task Verification:
  QA → execute() → TaskState(status=COMPLETED or QA_FAILED)

Task Debugging:
  Debugging → execute() → TaskState(status=COMPLETED or FAILED)
```

### 9. Refactoring Task Lifecycle (Target)

```
Issue Detection:
  Refactoring → analyze_codebase() → Issues found

Task Creation:
  Refactoring → create_refactoring_task() → RefactoringTask(status=NEW)

Task Execution:
  Refactoring → work_on_task() → RefactoringTask(status=IN_PROGRESS)

Task Completion:
  Refactoring → mark_complete() → RefactoringTask(status=COMPLETED)
  OR
  Refactoring → create_issue_report() → RefactoringTask(status=NEEDS_REVIEW)

Re-analysis:
  Refactoring → re_analyze() → Find more issues or complete
```

### 10. Polytopic Navigation

```
Current Phase: coding
Completion: 30%
Project Phase: integration

Coordinator._select_next_phase():
  → Check tactical decision tree
  → Check quality triggers
  → Check polytopic edges
  → Select next phase based on:
    - Task status
    - Quality metrics
    - Project phase
    - Phase history
    - Dimensional profile
```

### 11. Conversation Management

```
BasePhase.chat_with_history():
  → _build_conversation_history()
  → _add_system_prompt()
  → _add_user_message()
  → _call_llm(messages, tools)
  → _parse_response()
  → _update_conversation_history()
  → Return result
```

### 12. Error Handling Flow

```
Phase.execute():
  TRY:
    → Execute phase logic
    → Return PhaseResult(success=True)
  EXCEPT Exception as e:
    → Log error
    → Return PhaseResult(success=False, error=str(e))

Coordinator.run():
  IF phase_result.success == False:
    → Increment failure_count
    IF failure_count >= 3:
      → Trigger specialized phase (tool_design, prompt_design, etc.)
    ELSE:
      → Retry same phase
```

---

## Critical Flow Points for Refactoring

### 1. Trigger Point
```
Coordinator._should_trigger_refactoring(state)
  → Check current_phase == 'refactoring' (continue)
  → Check project_phase != 'foundation' (skip early)
  → Check quality issues (duplicates, complexity, architecture)
  → Return True/False
```

### 2. Execution Point
```
RefactoringPhase.execute(state)
  → Current: Single iteration, returns immediately
  → Target: Multi-iteration loop, continues until complete
```

### 3. Continuation Point
```
Coordinator._select_next_phase(state)
  → Current: Uses tactical decision tree
  → Target: Check if refactoring has pending work, continue if yes
```

### 4. Completion Point
```
RefactoringPhase._determine_next_phase(recommendations)
  → Current: Returns "coding", "qa", "planning", or "investigation"
  → Target: Returns "refactoring" if more work, else "coding"
```

---

## Data Flow Diagram

```
User Request
    ↓
Coordinator.run()
    ↓
StateManager (load state)
    ↓
_select_next_phase()
    ↓
Phase.execute()
    ↓
chat_with_history()
    ↓
LLM Response
    ↓
ToolCallHandler.process_tool_calls()
    ↓
Tool Handlers (modify files, analyze code, etc.)
    ↓
PhaseResult
    ↓
StateManager (update state)
    ↓
IPC Documents (write results)
    ↓
_check_completion()
    ↓
LOOP or COMPLETE
```

---

## Refactoring Integration Points

### Integration Point 1: Coordinator Trigger
**Location**: `pipeline/coordinator.py:_should_trigger_refactoring()`
**Status**: ✅ Implemented (Phase 1)
**Function**: Decides when to trigger refactoring

### Integration Point 2: Phase Selection
**Location**: `pipeline/coordinator.py:_select_next_phase()`
**Status**: ✅ Implemented (Phase 1)
**Function**: Routes to refactoring when triggered

### Integration Point 3: Phase Execution
**Location**: `pipeline/phases/refactoring.py:execute()`
**Status**: ⚠️ Partial (needs multi-iteration loop)
**Function**: Executes refactoring work

### Integration Point 4: Tool System
**Location**: `pipeline/tools.py:get_tools_for_phase()`
**Status**: ✅ Implemented
**Function**: Provides refactoring tools

### Integration Point 5: Handler System
**Location**: `pipeline/handlers.py`
**Status**: ✅ Implemented (8/8 handlers)
**Function**: Executes tool calls

### Integration Point 6: IPC System
**Location**: `pipeline/document_ipc.py`
**Status**: ✅ Implemented
**Function**: Phase-to-phase communication

### Integration Point 7: State Management
**Location**: `pipeline/state/manager.py`
**Status**: ⚠️ Needs RefactoringTask support
**Function**: Tracks refactoring tasks

### Integration Point 8: Prompt System
**Location**: `pipeline/prompts.py:get_refactoring_prompt()`
**Status**: ✅ Implemented (Phase 1)
**Function**: Guides LLM behavior

---

## Conclusion

**Pipeline Flow**: ✅ Well-understood
**Integration Points**: 6/8 complete, 2 need work
**Critical Gap**: Task management system (Phase 2)
**Next Step**: Implement RefactoringTask and task management tools