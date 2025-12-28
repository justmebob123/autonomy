# Depth-29 Recursive Analysis: pipeline/coordinator.py

## File Overview
- **Path**: autonomy/pipeline/coordinator.py
- **Lines**: 1,823
- **Classes**: 1 (PhaseCoordinator)
- **Methods**: 30
- **Purpose**: Orchestrate pipeline phases and manage main execution loop

---

## Class Structure

### Class: PhaseCoordinator (Lines 19-1823)
**Purpose**: Main coordinator that orchestrates all pipeline phases

**Key Attributes**:
- `config: PipelineConfig` - Pipeline configuration
- `project_dir: Path` - Project directory
- `logger` - Logger instance
- `verbose: bool` - Verbose mode
- `client: OllamaClient` - Ollama client
- `state_manager: StateManager` - State management
- `file_tracker: FileTracker` - File tracking
- `prompt_registry: PromptRegistry` - Prompt registry
- `tool_registry: ToolRegistry` - Tool registry
- `role_registry: RoleRegistry` - Role registry
- `message_bus: MessageBus` - Message bus for phase communication
- `coding_tool: UnifiedModelTool` - Coding model tool
- `reasoning_tool: UnifiedModelTool` - Reasoning model tool
- `analysis_tool: UnifiedModelTool` - Analysis model tool
- `coding_specialist` - Coding specialist
- `reasoning_specialist` - Reasoning specialist
- `analysis_specialist` - Analysis specialist
- `phases: Dict` - Phase instances

**Methods** (30 total):

### Initialization Methods
1. `__init__(config, verbose)` - Initialize coordinator
2. `_init_phases()` - Initialize all phases
3. `_calculate_initial_dimensions(phase_name, phase_type)` - Calculate initial dimensions
4. `_initialize_polytopic_structure()` - Initialize polytopic structure

### Phase Selection Methods
5. `_should_force_transition(state, current_phase, last_result)` - Check if phase transition should be forced
6. `_select_next_phase_polytopic(state, current_phase)` - Select next phase using polytopic analysis
7. `_analyze_situation(context)` - Analyze current situation
8. `_assess_error_severity(errors)` - Assess error severity
9. `_assess_complexity(context)` - Assess complexity
10. `_assess_urgency(situation)` - Assess urgency
11. `_determine_dimensional_focus(situation)` - Determine dimensional focus
12. `_select_intelligent_path(situation, current_phase)` - Select intelligent path
13. `_calculate_phase_priority(phase_name, situation)` - Calculate phase priority

### Polytopic Analysis Methods
14. `_update_polytope_dimensions(phase_name, result)` - Update polytope dimensions
15. `_analyze_correlations(state)` - Analyze correlations

### Main Execution Methods
16. `run(resume)` - Main entry point
17. `_develop_tool(tool_name, tool_args, context, state)` - Develop new tool
18. `_run_loop()` - Main execution loop (COMPLEXITY: 38)

### Action Determination Methods
19. `_determine_next_action(state)` - Determine next action
20. `_determine_next_action_strategic(state)` - Strategic action determination
21. `_determine_next_action_tactical(state)` - Tactical action determination

### Disabled Methods (Arbiter-related)
22. `_build_arbiter_context_DISABLED(state)` - Build arbiter context (disabled)
23. `_convert_arbiter_decision_DISABLED(decision, state)` - Convert arbiter decision (disabled)
24. `_execute_specialist_consultation_DISABLED(specialist_name, query, context)` - Execute specialist consultation (disabled)

### Improvement Cycle Methods
25. `_should_run_improvement_cycle(state)` - Check if improvement cycle should run
26. `_get_next_improvement_phase(state)` - Get next improvement phase

### Utility Methods
27. `_dependencies_met(state, task)` - Check if dependencies are met
28. `_record_execution_pattern(phase_name, result, state)` - Record execution pattern
29. `_show_project_status(state)` - Show project status
30. `_print_banner()` - Print banner
31. `_summarize_run()` - Summarize run
32. `visualize_dimensional_space(visualization_type)` - Visualize dimensional space

---

## Depth-29 Call Stack Analysis

### Entry Point 1: run()
**Purpose**: Main entry point for coordinator

**Call Stack (Depth 29)**:
```
Level 0: run(resume)
  ├─ Level 1: self._print_banner()
  │   └─ Level 2: print() operations
  ├─ Level 1: self.client.discover_servers()
  │   └─ Level 2-10: HTTP requests to discover models
  ├─ Level 1: self.state_manager.load()
  │   └─ Level 2-8: File I/O and JSON parsing
  ├─ Level 1: self._initialize_polytopic_structure()
  │   ├─ Level 2: For each phase in self.phases
  │   │   └─ Level 3: self._calculate_initial_dimensions()
  │   │       └─ Level 4-6: Dimension calculations
  │   └─ Level 2: self.state_manager.save()
  │       └─ Level 3-8: File I/O and JSON serialization
  ├─ Level 1: self._run_loop()
  │   └─ Level 2-29: Main execution loop (see below)
  └─ Level 1: self._summarize_run()
      └─ Level 2-5: Summary generation and display
```

### Entry Point 2: _run_loop() [HIGH COMPLEXITY: 38]
**Purpose**: Main execution loop that never exits

**Call Stack (Depth 29)**:
```
Level 0: _run_loop()
  ├─ Level 1: while True loop
  │   ├─ Level 2: self.state_manager.load()
  │   │   └─ Level 3-8: File I/O and JSON parsing
  │   ├─ Level 2: self._show_project_status(state)
  │   │   └─ Level 3-5: Status display
  │   ├─ Level 2: self._determine_next_action(state)
  │   │   ├─ Level 3: self._determine_next_action_strategic(state)
  │   │   │   ├─ Level 4: Check for blocked objectives
  │   │   │   ├─ Level 4: Check for critical issues
  │   │   │   ├─ Level 4: Check for pending tasks
  │   │   │   └─ Level 4: Return action dict
  │   │   └─ Level 3: self._determine_next_action_tactical(state)
  │   │       ├─ Level 4: Check task statuses
  │   │       ├─ Level 4: Check dependencies
  │   │       ├─ Level 4: Select next task
  │   │       └─ Level 4: Return action dict
  │   ├─ Level 2: Get phase instance
  │   │   └─ Level 3: self.phases.get(phase_name)
  │   ├─ Level 2: phase.execute(state)
  │   │   ├─ Level 3: Phase-specific execution
  │   │   │   ├─ Level 4: Planning Phase
  │   │   │   │   ├─ Level 5: Gather context
  │   │   │   │   ├─ Level 5: Generate tasks
  │   │   │   │   ├─ Level 5: Create objective files
  │   │   │   │   └─ Level 5-15: LLM calls and processing
  │   │   │   ├─ Level 4: Coding Phase
  │   │   │   │   ├─ Level 5: Get next task
  │   │   │   │   ├─ Level 5: Generate code
  │   │   │   │   ├─ Level 5: Write files
  │   │   │   │   └─ Level 5-20: LLM calls, file operations
  │   │   │   ├─ Level 4: QA Phase
  │   │   │   │   ├─ Level 5: Review code
  │   │   │   │   ├─ Level 5: Find issues
  │   │   │   │   └─ Level 5-15: LLM calls and analysis
  │   │   │   ├─ Level 4: Debugging Phase
  │   │   │   │   ├─ Level 5: Get issues
  │   │   │   │   ├─ Level 5: Fix issues
  │   │   │   │   ├─ Level 5: Test fixes
  │   │   │   │   └─ Level 5-25: LLM calls, file operations, testing
  │   │   │   └─ Level 4: Documentation Phase
  │   │   │       ├─ Level 5: Update README
  │   │   │       ├─ Level 5: Update ARCHITECTURE
  │   │   │       └─ Level 5-15: LLM calls, file operations
  │   │   └─ Level 3: Return result
  │   ├─ Level 2: self._update_polytope_dimensions(phase_name, result)
  │   │   └─ Level 3-8: Dimension updates and calculations
  │   ├─ Level 2: self._record_execution_pattern(phase_name, result, state)
  │   │   └─ Level 3-8: Pattern recording and analysis
  │   ├─ Level 2: self.state_manager.save(state)
  │   │   └─ Level 3-8: File I/O and JSON serialization
  │   ├─ Level 2: Check for completion
  │   │   └─ Level 3: All tasks complete check
  │   ├─ Level 2: Check for max_iterations
  │   │   └─ Level 3: Iteration count check
  │   └─ Level 2: Sleep between iterations
  │       └─ Level 3: time.sleep()
  └─ Level 1: Return success/failure
```

**Variables Tracked**:
- `state: PipelineState` - Current pipeline state
- `iteration: int` - Current iteration number
- `action: Dict` - Next action to take
- `phase_name: str` - Current phase name
- `phase: BasePhase` - Current phase instance
- `result: Dict` - Phase execution result
- `all_complete: bool` - All tasks complete flag

**State Mutations**:
- `state.tasks` - Task statuses updated
- `state.current_phase` - Current phase updated
- `state.iteration` - Iteration count incremented
- `state.performance_metrics` - Metrics updated
- `state.learned_patterns` - Patterns recorded
- File system - Files created/modified by phases
- State file - Saved after each iteration

**CRITICAL FINDING**: This method has complexity 38 due to:
1. Infinite while loop
2. Multiple nested conditionals
3. Complex phase selection logic
4. State management operations
5. Error handling
6. Message bus operations
7. Polytopic analysis integration

### Entry Point 3: _determine_next_action()
**Purpose**: Determine next action to take

**Call Stack (Depth 29)**:
```
Level 0: _determine_next_action(state)
  ├─ Level 1: self._determine_next_action_strategic(state)
  │   ├─ Level 2: Check for blocked objectives
  │   │   └─ Level 3: state.objectives iteration
  │   ├─ Level 2: Check for critical issues
  │   │   └─ Level 3: state.issues iteration
  │   ├─ Level 2: Check for pending tasks
  │   │   └─ Level 3: state.tasks iteration
  │   ├─ Level 2: Check for improvement cycle
  │   │   └─ Level 3: self._should_run_improvement_cycle(state)
  │   │       └─ Level 4-8: Cycle determination logic
  │   └─ Level 2: Return strategic action
  └─ Level 1: self._determine_next_action_tactical(state)
      ├─ Level 2: Get pending tasks
      │   └─ Level 3: Filter tasks by status
      ├─ Level 2: Get in-progress tasks
      │   └─ Level 3: Filter tasks by status
      ├─ Level 2: Get failed tasks
      │   └─ Level 3: Filter tasks by status
      ├─ Level 2: Priority determination
      │   ├─ Level 3: Failed tasks first
      │   ├─ Level 3: In-progress tasks second
      │   └─ Level 3: Pending tasks third
      ├─ Level 2: Dependency checking
      │   └─ Level 3: self._dependencies_met(state, task)
      │       └─ Level 4-8: Dependency resolution
      └─ Level 2: Return tactical action
```

**Variables Tracked**:
- `state: PipelineState` - Current pipeline state
- `blocked_objectives: List` - Blocked objectives
- `critical_issues: List` - Critical issues
- `pending_tasks: List` - Pending tasks
- `in_progress_tasks: List` - In-progress tasks
- `failed_tasks: List` - Failed tasks
- `next_task: TaskState` - Next task to execute
- `action: Dict` - Action to take

---

## Integration Points

### 1. State Management Integration
**Used By**: All methods
**Dependencies**:
- StateManager - State persistence
- PipelineState - State data structure
- TaskState - Task data structure

**Call Paths**:
```
run() -> state_manager.load()
_run_loop() -> state_manager.load() -> state_manager.save()
All methods -> state manipulation
```

### 2. Client Integration
**Used By**: Initialization and phase execution
**Dependencies**:
- OllamaClient - Model communication

**Call Paths**:
```
__init__() -> OllamaClient(config)
run() -> client.discover_servers()
Phases -> client.chat() (via phase.execute())
```

### 3. Phase Integration
**Used By**: Main execution loop
**Dependencies**:
- PlanningPhase
- CodingPhase
- QAPhase
- DebuggingPhase
- DocumentationPhase
- ProjectPlanningPhase

**Call Paths**:
```
_init_phases() -> Create phase instances
_run_loop() -> phase.execute(state)
```

### 4. Message Bus Integration
**Used By**: Phase communication
**Dependencies**:
- MessageBus - Event-driven communication
- MessageType - Message types

**Call Paths**:
```
__init__() -> MessageBus(state_manager)
__init__() -> message_bus.subscribe()
Phases -> message_bus.publish() (implicit)
```

### 5. Registry Integration
**Used By**: Shared resources
**Dependencies**:
- PromptRegistry - Prompt management
- ToolRegistry - Tool management
- RoleRegistry - Role management

**Call Paths**:
```
__init__() -> PromptRegistry(project_dir)
__init__() -> ToolRegistry(project_dir)
__init__() -> RoleRegistry(project_dir, client)
Phases -> Use registries (implicit)
```

### 6. Specialist Integration
**Used By**: Advanced reasoning
**Dependencies**:
- UnifiedModelTool - Model tools
- Specialists - Coding, reasoning, analysis

**Call Paths**:
```
__init__() -> Create UnifiedModelTool instances
__init__() -> Create specialist instances
Phases -> Use specialists (implicit)
```

### 7. Polytopic Integration
**Used By**: Dimensional analysis
**Dependencies**:
- Polytopic system - 7D analysis

**Call Paths**:
```
_initialize_polytopic_structure() -> Calculate dimensions
_update_polytope_dimensions() -> Update dimensions
_select_next_phase_polytopic() -> Use dimensions for selection
```

---

## Complexity Analysis

### High Complexity Methods

#### 1. _run_loop() - Complexity: 38
**Reasons**:
- Infinite while loop
- Multiple nested conditionals
- Complex phase selection logic
- State management operations
- Error handling
- Message bus operations
- Polytopic analysis integration
- Multiple exit conditions

**Refactoring Recommendations**:
1. Extract phase execution to separate method
2. Extract action determination to separate method (already done)
3. Extract state persistence to separate method
4. Simplify error handling
5. Extract message bus operations to separate method
6. Consider using state machine pattern

#### 2. _determine_next_action_strategic() - Complexity: 20
**Reasons**:
- Multiple conditional branches
- Objective checking
- Issue checking
- Task checking
- Improvement cycle checking

**Refactoring Recommendations**:
1. Extract each check to separate method
2. Use strategy pattern for action selection
3. Simplify conditional logic

#### 3. _determine_next_action_tactical() - Complexity: 18
**Reasons**:
- Task filtering
- Priority determination
- Dependency checking
- Multiple conditional branches

**Refactoring Recommendations**:
1. Extract task filtering to separate method
2. Extract priority determination to separate method
3. Simplify dependency checking

---

## Data Flow Analysis

### Flow 1: Initialization
```
__init__(config, verbose)
  ├─> OllamaClient(config)
  ├─> StateManager(project_dir)
  ├─> FileTracker(project_dir)
  ├─> PromptRegistry(project_dir)
  ├─> ToolRegistry(project_dir)
  ├─> RoleRegistry(project_dir, client)
  ├─> MessageBus(state_manager)
  ├─> UnifiedModelTool instances
  ├─> Specialist instances
  └─> _init_phases()
      └─> Create phase instances
```

**Variables**:
- Input: config (PipelineConfig), verbose (bool)
- Output: Initialized coordinator
- Side Effects: Registries created, message bus initialized

### Flow 2: Main Execution
```
run(resume)
  ├─> _print_banner()
  ├─> client.discover_servers()
  ├─> state_manager.load()
  ├─> _initialize_polytopic_structure()
  ├─> _run_loop()
  │   └─> Infinite loop (see Flow 3)
  └─> _summarize_run()
```

**Variables**:
- Input: resume (bool)
- Output: success (bool)
- Side Effects: State loaded, phases executed, state saved

### Flow 3: Execution Loop
```
_run_loop()
  └─> while True:
      ├─> state_manager.load()
      ├─> _show_project_status(state)
      ├─> _determine_next_action(state)
      │   ├─> _determine_next_action_strategic(state)
      │   └─> _determine_next_action_tactical(state)
      ├─> Get phase instance
      ├─> phase.execute(state)
      ├─> _update_polytope_dimensions(phase_name, result)
      ├─> _record_execution_pattern(phase_name, result, state)
      ├─> state_manager.save(state)
      ├─> Check for completion
      ├─> Check for max_iterations
      └─> time.sleep()
```

**Variables**:
- Input: None (uses self.state_manager)
- Output: success (bool)
- Side Effects: State updated, phases executed, files created/modified

---

## Issues Analysis

### No Critical Issues Found
After depth-29 analysis, no critical issues were found in this file.

### Observations

#### 1. High Complexity in _run_loop()
**Severity**: Medium
**Impact**: Maintainability
**Recommendation**: Refactor using state machine pattern

#### 2. Disabled Arbiter Methods
**Severity**: Low
**Impact**: Code cleanliness
**Recommendation**: Remove disabled methods or re-enable if needed

#### 3. Multiple Responsibilities
**Severity**: Low
**Impact**: Single Responsibility Principle violation
**Recommendation**: Consider splitting into:
- PhaseOrchestrator (phase execution)
- ActionDeterminator (action selection)
- StateCoordinator (state management)
- PolytopicAnalyzer (dimensional analysis)

---

## Dependencies (Depth-29 Traced)

### Standard Library
1. **time** - Sleep operations
2. **pathlib** - Path operations
3. **typing** - Type hints
4. **datetime** - Timestamp operations

### Internal Dependencies
1. **config** - PipelineConfig
2. **client** - OllamaClient
3. **state.manager** - StateManager, PipelineState, TaskState, TaskStatus
4. **logging_setup** - get_logger, setup_logging
5. **state.file_tracker** - FileTracker
6. **prompt_registry** - PromptRegistry
7. **tool_registry** - ToolRegistry
8. **role_registry** - RoleRegistry
9. **messaging** - MessageBus, MessageType
10. **orchestration.unified_model_tool** - UnifiedModelTool
11. **orchestration.specialists** - Specialist creators
12. **phases** - All phase classes (lazy import)

---

## Recommendations

### High Priority
1. **Refactor _run_loop()**
   - Extract phase execution to separate method
   - Use state machine pattern
   - Reduce complexity from 38 to <15

2. **Remove or re-enable disabled arbiter methods**
   - Clean up code
   - Remove dead code
   - Or re-enable if needed

### Medium Priority
1. **Add comprehensive unit tests**
   - Test action determination
   - Test phase selection
   - Test error handling

2. **Improve error handling**
   - More specific exception handling
   - Better error messages
   - Recovery strategies

### Low Priority
1. **Add type hints to all methods**
   - Improve code documentation
   - Enable better IDE support

2. **Add docstrings to all methods**
   - Explain purpose
   - Document parameters
   - Document return values

---

## Next Steps

1. **Continue examination of remaining files**
   - pipeline/phases/debugging.py (1783 lines, complexity 85)
   - pipeline/phases/qa.py (complexity 50)
   - Continue systematic examination

2. **Create refactoring plan for _run_loop()**
   - Design state machine pattern
   - Plan extraction of methods
   - Estimate effort

3. **Verify all integrations**
   - Check message bus usage
   - Verify polytopic integration
   - Test specialist usage

---

**Status**: Complete
**Next Action**: Move to pipeline/phases/debugging.py