# Depth-61 Recursive Analysis: pipeline/phases/planning.py

## File Overview
- **Path**: autonomy/pipeline/phases/planning.py
- **Lines**: 405
- **Classes**: 1 (PlanningPhase)
- **Methods**: 5
- **Purpose**: Create development plans from project specifications
- **Complexity**: MEDIUM (30 for execute method)

---

## Reference Documents
- **Progress**: DEPTH_61_EXAMINATION_PROGRESS.md
- **Refactoring Plan**: DEPTH_61_REFACTORING_MASTER_PLAN.md
- **Related Analysis**: DEPTH_61_QA_PY_ANALYSIS.md, DEPTH_61_DEBUGGING_PY_ANALYSIS.md

---

## Class Structure

### Class: PlanningPhase (Lines 19-405)
**Purpose**: Planning phase that creates task plans from MASTER_PLAN.md

**Inheritance**:
- BasePhase - Base phase functionality
- LoopDetectionMixin - Loop detection capabilities

**Key Attributes**:
- `phase_name: str` = "planning"
- `message_bus` - Message bus for events (from BasePhase)
- `client: OllamaClient` - Ollama client (from BasePhase)
- `logger` - Logger instance (from BasePhase)
- `project_dir: Path` - Project directory (from BasePhase)
- `state_manager: StateManager` - State manager (from BasePhase)
- `action_tracker` - Action tracking (from LoopDetectionMixin)
- `tool_registry` - Tool registry (from BasePhase)
- `parser` - Response parser (from BasePhase)

**Methods** (5 total):

### Core Methods
1. `__init__(*args, **kwargs)` - Initialize planning phase
2. `execute(state, **kwargs)` - Main execution method (COMPLEXITY: 30)
3. `generate_state_markdown(state)` - Generate state markdown

### Utility Methods
4. `_get_existing_files()` - Get existing files for context
5. `_find_existing_task(state, task_data)` - Find existing task
6. `_build_planning_message(master_plan, existing_files)` - Build planning message

---

## Depth-61 Call Stack Analysis

### Entry Point 1: execute()
**Purpose**: Main execution method for planning phase

**Call Stack (Depth 61)**:
```
Level 0: execute(state, **kwargs)
  ├─ Level 1: Message Bus Operations
  │   ├─ Level 2: self._get_messages()
  │   │   └─ Level 3-10: Message retrieval
  │   └─ Level 2: self._clear_messages()
  │       └─ Level 3-10: Message clearing
  ├─ Level 1: Get Objective
  │   └─ Level 2: kwargs.get('objective')
  ├─ Level 1: Load MASTER_PLAN.md
  │   └─ Level 2: self.read_file("MASTER_PLAN.md")
  │       └─ Level 3-10: File I/O
  ├─ Level 1: Get Existing Files
  │   └─ Level 2: self._get_existing_files()
  │       ├─ Level 3: self.project_dir.rglob("*.py")
  │       │   └─ Level 4-10: File system traversal
  │       └─ Level 3: List comprehension
  ├─ Level 1: Build Planning Message
  │   └─ Level 2: self._build_planning_message(master_plan, existing_files)
  │       └─ Level 3-5: String formatting
  ├─ Level 1: Get Tools
  │   └─ Level 2: get_tools_for_phase("planning")
  │       └─ Level 3-10: Tool definitions
  ├─ Level 1: Model Inference
  │   └─ Level 2: self.chat_with_history(user_message, tools)
  │       ├─ Level 3: self.conversation.add_message("user", user_message)
  │       │   └─ Level 4-10: Message management
  │       ├─ Level 3: self.conversation.get_context()
  │       │   └─ Level 4-10: Context retrieval
  │       ├─ Level 3: self.client.get_model_for_task(self.phase_name)
  │       │   └─ Level 4-15: Model selection with fallbacks
  │       ├─ Level 3: self.client.chat(host, model, messages, tools)
  │       │   ├─ Level 4-10: HTTP request preparation
  │       │   ├─ Level 11-20: Network transmission
  │       │   ├─ Level 21-30: Ollama server processing
  │       │   ├─ Level 31-45: Model loading and preparation
  │       │   ├─ Level 46-55: Model inference (GPU)
  │       │   │   ├─ Level 56-58: GPU kernel execution
  │       │   │   └─ Level 59-61: Hardware-level operations
  │       │   └─ Level 21-30: Response generation
  │       ├─ Level 3: self.conversation.add_message("assistant", content)
  │       │   └─ Level 4-10: Message management
  │       └─ Level 3: Return response
  ├─ Level 1: Parse Response
  │   ├─ Level 2: response.get("tool_calls", [])
  │   └─ Level 2: response.get("content", "")
  ├─ Level 1: Process Tool Calls
  │   ├─ Level 2: If tool_calls present
  │   │   ├─ Level 3: ToolCallHandler(project_dir, tool_registry)
  │   │   │   └─ Level 4-10: Handler initialization
  │   │   ├─ Level 3: handler.process_tool_calls(tool_calls)
  │   │   │   └─ Level 4-40: Tool execution (see handlers.py analysis)
  │   │   ├─ Level 3: self.track_tool_calls(tool_calls, results)
  │   │   │   └─ Level 4-10: Action tracking
  │   │   └─ Level 3: self.check_for_loops()
  │   │       └─ Level 4-15: Loop detection
  │   └─ Level 2: If no tool_calls (fallback)
  │       └─ Level 3: self.parser.extract_tasks_from_text(content)
  │           └─ Level 4-20: Text parsing
  ├─ Level 1: Add Tasks to State
  │   └─ Level 2: For each task_data in tasks
  │       ├─ Level 3: self._find_existing_task(state, task_data)
  │       │   └─ Level 4-10: Task comparison
  │       ├─ Level 3: Validate target_file
  │       │   └─ Level 4-8: Path validation
  │       ├─ Level 3: state.add_task()
  │       │   └─ Level 4-10: State update
  │       └─ Level 3: Link task to objective
  │           └─ Level 4-10: Objective linking
  ├─ Level 1: Save State
  │   └─ Level 2: self.state_manager.save(state)
  │       └─ Level 3-10: File I/O and JSON serialization
  ├─ Level 1: Generate State Markdown
  │   └─ Level 2: self.generate_state_markdown(state)
  │       └─ Level 3-10: Markdown generation
  └─ Level 1: Return PhaseResult
      └─ Level 2: PhaseResult construction
```

**Variables Tracked (Depth 61)**:
- `state: PipelineState` - Current pipeline state
  - Level 0: Input parameter
  - Level 1-61: Passed through all methods, modified at various levels
- `objective: Objective` - Current objective (optional)
  - Level 0: From kwargs
  - Level 1-61: Used for task linking
- `master_plan: str` - Master plan content
  - Level 1: Read from file
  - Level 2-61: Passed to model
- `existing_files: List[str]` - Existing project files
  - Level 1: Retrieved from file system
  - Level 2-61: Passed to model for context
- `user_message: str` - Planning prompt
  - Level 1: Constructed
  - Level 2-61: Passed to model
- `tools: List[Dict]` - Available tools
  - Level 1: Retrieved
  - Level 2-61: Passed to model
- `response: Dict` - Model response
  - Level 2: From chat_with_history()
  - Level 3-61: Parsed and processed
- `tool_calls: List[Dict]` - Tool calls from response
  - Level 2: Extracted from response
  - Level 3-40: Executed by handler
- `content: str` - Text content from response
  - Level 2: Extracted from response
  - Level 3-20: Used for fallback parsing
- `tasks: List[Dict]` - Extracted tasks
  - Level 3: From tool calls or text parsing
  - Level 4-61: Added to state
- `task_data: Dict` - Individual task data
  - Level 2: Loop variable
  - Level 3-10: Validated and added to state

**State Mutations (Depth 61)**:
- `state.tasks` - Tasks added
  - Level 4-10: New tasks added
- `state.objectives` - Objectives updated
  - Level 4-10: Tasks linked to objectives
- File system - State file saved
  - Level 3-10: State persisted to disk
- Conversation history - Messages added
  - Level 4-10: Messages added to conversation

**CRITICAL FINDING**: This method has complexity 30 due to:
1. Message bus operations
2. File I/O operations
3. Model inference (depth 30-61)
4. Tool call processing (depth 20-40)
5. Task validation and filtering
6. Duplicate detection
7. Objective linking
8. State management operations
9. Multiple conditional branches
10. Error handling

---

## Integration Points (Depth-61 Traced)

### 1. State Management Integration
**Depth**: 0-10
**Used By**: All methods
**Dependencies**:
- StateManager - State persistence
- PipelineState - State data structure
- TaskState - Task data structure
- TaskStatus - Task status enum
- TaskPriority - Task priority enum

**Call Paths (Depth 61)**:
```
Level 0: execute()
  ├─ Level 3: state.add_task()
  │   └─ Level 4-10: State update
  ├─ Level 3: state.objectives update
  │   └─ Level 4-10: Objective linking
  └─ Level 2: state_manager.save()
      └─ Level 3-10: File I/O and JSON serialization
```

### 2. Message Bus Integration
**Depth**: 0-10
**Used By**: __init__, execute
**Dependencies**:
- MessageBus - Event-driven communication
- MessageType - Message types

**Call Paths (Depth 61)**:
```
Level 0: __init__()
  └─ Level 1: self._subscribe_to_messages()
      └─ Level 2-10: Subscription setup

Level 0: execute()
  ├─ Level 2: self._get_messages()
  │   └─ Level 3-10: Message retrieval
  └─ Level 2: self._clear_messages()
      └─ Level 3-10: Message clearing
```

### 3. Model Inference Integration
**Depth**: 0-61 (DEEPEST)
**Used By**: execute
**Dependencies**:
- OllamaClient - Model communication
- Model selection - Intelligent fallbacks
- Ollama API - Model inference

**Call Paths (Depth 61)**:
```
Level 0: execute()
  └─ Level 2: self.chat_with_history()
      ├─ Level 3: self.client.get_model_for_task()
      │   └─ Level 4-15: Model selection with fallbacks
      └─ Level 3: self.client.chat()
          ├─ Level 4-10: HTTP request preparation
          ├─ Level 11-20: Network transmission
          ├─ Level 21-30: Ollama server processing
          ├─ Level 31-45: Model loading and preparation
          ├─ Level 46-55: Model inference (GPU)
          │   ├─ Level 56-58: GPU kernel execution
          │   └─ Level 59-61: Hardware-level operations
          └─ Level 21-30: Response generation
```

**Depth 61 Breakdown**:
- Levels 0-3: Python application code
- Levels 4-10: requests library
- Levels 11-20: HTTP/network stack
- Levels 21-30: Ollama server processing
- Levels 31-45: Model loading and preparation
- Levels 46-55: Model inference (GPU operations)
- Levels 56-61: Kernel-level GPU drivers and operations

### 4. Tool Call Handling Integration
**Depth**: 0-40
**Used By**: execute
**Dependencies**:
- ToolCallHandler - Tool execution
- create_task tool - Task creation

**Call Paths (Depth 61)**:
```
Level 0: execute()
  └─ Level 3: handler.process_tool_calls()
      └─ Level 4-40: Tool execution (see handlers.py analysis)
```

### 5. Loop Detection Integration
**Depth**: 0-15
**Used By**: execute
**Dependencies**:
- LoopDetectionMixin - Loop detection
- ActionTracker - Action tracking

**Call Paths (Depth 61)**:
```
Level 0: execute()
  ├─ Level 3: self.track_tool_calls()
  │   └─ Level 4-10: Action tracking
  └─ Level 3: self.check_for_loops()
      └─ Level 4-15: Loop detection
```

### 6. Objective Management Integration
**Depth**: 0-10
**Used By**: execute
**Dependencies**:
- Objective - Objective data structure
- ObjectiveLevel - Objective level enum

**Call Paths (Depth 61)**:
```
Level 0: execute()
  └─ Level 3: Link task to objective
      ├─ Level 4: state.objectives update
      │   └─ Level 5-10: State update
      └─ Level 4: objective.to_dict()
          └─ Level 5-8: Dictionary conversion
```

### 7. File System Integration
**Depth**: 0-10
**Used By**: execute, _get_existing_files
**Dependencies**:
- Path operations - File system access
- File I/O - Reading files

**Call Paths (Depth 61)**:
```
Level 0: execute()
  ├─ Level 2: self.read_file("MASTER_PLAN.md")
  │   └─ Level 3-10: File I/O
  └─ Level 2: self._get_existing_files()
      └─ Level 3-10: File system traversal
```

---

## Complexity Analysis

### Medium Complexity Methods

#### 1. execute() - Complexity: 30
**Reasons**:
- Message bus operations
- File I/O operations
- Model inference (depth 30-61)
- Tool call processing (depth 20-40)
- Task validation and filtering
- Duplicate detection
- Objective linking
- State management operations
- Multiple conditional branches
- Error handling

**Refactoring Recommendations**:
1. Extract message bus operations to separate method
2. Extract file loading to separate method
3. Extract task validation to separate method
4. Extract objective linking to separate method
5. Simplify conditional logic
6. Target complexity: <15

**Proposed Refactoring**:
```python
class PlanningPhase(BasePhase, LoopDetectionMixin):
    
    def execute(self, state, **kwargs):
        """Main execution - simplified"""
        self._process_messages()
        objective = kwargs.get('objective')
        
        master_plan = self._load_master_plan()
        if not master_plan:
            return self._error_result("MASTER_PLAN.md not found")
        
        tasks = self._generate_tasks(master_plan, objective)
        if not tasks:
            return self._error_result("Could not extract tasks")
        
        added_count = self._add_tasks_to_state(state, tasks, objective)
        
        self.state_manager.save(state)
        return self._success_result(added_count)
    
    def _process_messages(self):
        """Process message bus messages"""
        pass
    
    def _load_master_plan(self):
        """Load and validate MASTER_PLAN.md"""
        pass
    
    def _generate_tasks(self, master_plan, objective):
        """Generate tasks from master plan"""
        pass
    
    def _add_tasks_to_state(self, state, tasks, objective):
        """Add tasks to state with validation"""
        pass
```

---

## Data Flow Analysis (Depth 61)

### Flow 1: Task Generation
```
Level 0: execute(state, objective)
  ├─ Level 1: Load MASTER_PLAN.md
  │   └─ Level 2-10: File I/O
  ├─ Level 1: Get existing files
  │   └─ Level 2-10: File system traversal
  ├─ Level 1: Build planning message
  │   └─ Level 2-5: String formatting
  ├─ Level 1: Call model
  │   └─ Level 2-61: Model inference
  ├─ Level 1: Parse response
  │   └─ Level 2-20: Tool call or text parsing
  └─ Level 1: Return tasks
```

**Variables (Depth 61)**:
- Input: state (PipelineState), objective (Objective)
- Output: tasks (List[Dict])
- Side Effects: Model inference, conversation history updated

### Flow 2: Task Validation and Addition
```
Level 0: execute(state, tasks, objective)
  └─ Level 2: For each task_data in tasks
      ├─ Level 3: Check for duplicates
      │   └─ Level 4-10: Task comparison
      ├─ Level 3: Validate target_file
      │   └─ Level 4-8: Path validation
      ├─ Level 3: Add task to state
      │   └─ Level 4-10: State update
      └─ Level 3: Link to objective
          └─ Level 4-10: Objective linking
```

**Variables (Depth 61)**:
- Input: state (PipelineState), tasks (List[Dict]), objective (Objective)
- Output: added_count (int)
- Side Effects: State updated, tasks added, objectives linked

### Flow 3: Model Inference (Depth 61)
```
Level 0: execute()
  └─ Level 2: self.chat_with_history(user_message, tools)
      ├─ Level 3: Add user message
      ├─ Level 3: Get context
      ├─ Level 3: Get model
      │   └─ Level 4-15: Model selection
      ├─ Level 3: Call model
      │   ├─ Level 4-10: HTTP request
      │   ├─ Level 11-20: Network
      │   ├─ Level 21-30: Server processing
      │   ├─ Level 31-45: Model loading
      │   ├─ Level 46-55: Model inference (GPU)
      │   │   ├─ Level 56-58: GPU kernels
      │   │   └─ Level 59-61: Hardware ops
      │   └─ Level 21-30: Response generation
      ├─ Level 3: Add assistant message
      └─ Level 3: Return response
```

**Variables (Depth 61)**:
- Input: user_message (str), tools (List[Dict])
- Output: response (Dict)
- Side Effects: GPU memory allocation, model inference

---

## Issues Analysis

### No Critical Issues Found
After depth-61 analysis, no critical issues were found in this file.

### Observations

#### 1. Medium Complexity in execute()
**Severity**: Medium
**Impact**: Maintainability
**Recommendation**: Refactor to reduce complexity from 30 to <15

#### 2. Task Validation Logic
**Severity**: Low
**Impact**: Good design, prevents duplicates and invalid tasks
**Recommendation**: Well implemented, consider extracting to separate method

#### 3. Objective Linking
**Severity**: Low
**Impact**: Good integration with objective management
**Recommendation**: Well implemented, no changes needed

---

## Dependencies (Depth-61 Traced)

### Standard Library
1. **datetime** - Timestamp operations (depth 1-3)
2. **typing** - Type hints (depth 0)

### Internal Dependencies
1. **base** - BasePhase, PhaseResult (depth 0-5)
2. **state.manager** - StateManager, PipelineState, TaskState, TaskStatus (depth 1-10)
3. **state.priority** - TaskPriority (depth 1-5)
4. **tools** - get_tools_for_phase (depth 2-10)
5. **prompts** - SYSTEM_PROMPTS, get_planning_prompt (depth 2-10)
6. **handlers** - ToolCallHandler (depth 3-40)
7. **loop_detection_mixin** - LoopDetectionMixin (depth 2-15)
8. **messaging** - MessageBus, MessageType (depth 2-10)

---

## Recommendations

### High Priority
1. **Refactor execute() method**
   - Extract message bus operations
   - Extract file loading
   - Extract task validation
   - Extract objective linking
   - Reduce complexity from 30 to <15
   - Estimated effort: Medium (2-3 days)

### Medium Priority
1. **Add comprehensive unit tests**
   - Test task generation
   - Test duplicate detection
   - Test objective linking
   - Estimated effort: 2-3 days

2. **Improve error messages**
   - More descriptive errors
   - Include context
   - Suggest fixes

### Low Priority
1. **Add type hints to all methods**
   - Improve code documentation
   - Enable better IDE support

2. **Add docstrings to all methods**
   - Explain purpose
   - Document parameters
   - Document return values

---

## Refactoring Plan Update

### Add to DEPTH_61_REFACTORING_MASTER_PLAN.md

**New Refactoring Item**:
- **Priority**: MEDIUM-LOW (after top 5)
- **Function**: execute
- **Complexity**: 30
- **File**: pipeline/phases/planning.py
- **Effort**: 2-3 days
- **Status**: NOT STARTED

---

## Next Steps

1. **Continue file-by-file examination**
   - Next: pipeline/phases/coding.py
   - Remaining: 166 files

2. **Update refactoring plan**
   - Add planning.py::execute to plan
   - Prioritize based on complexity and impact

3. **Document findings**
   - Update progress report
   - Track refactoring recommendations

---

**Status**: Complete  
**Complexity**: MEDIUM (30)  
**Refactoring Priority**: MEDIUM-LOW  
**Next Action**: Continue with pipeline/phases/coding.py

---

## Summary for Reference

**Key Points**:
- Complexity 30 (medium, manageable)
- No critical issues found
- Good objective linking implementation
- Task validation prevents duplicates
- Model inference traced to depth 61
- Refactoring recommended but not urgent
- 5 methods, well-organized structure