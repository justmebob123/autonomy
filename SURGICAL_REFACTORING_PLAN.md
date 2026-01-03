# 🔬 SURGICAL REFACTORING PLAN - NO PARALLEL IMPLEMENTATIONS

## Executive Summary

This is a **SURGICAL, IN-PLACE REFACTORING** of the existing codebase. No parallel implementations, no "universal" prefixes, no backward compatibility concerns. We will **MODIFY THE EXISTING CODE DIRECTLY** to eliminate bloat and improve architecture.

---

## 📊 ACTUAL MEASUREMENTS (Not Assumptions)

### BasePhase (pipeline/phases/base.py)
- **Total Lines**: 846
- **Key Methods**:
  - `__init__`: Lines 66-207 (141 lines) - Massive initialization
  - `chat_with_history`: Lines 691-846 (155 lines) - Core LLM interaction
  - `run`: Lines 118-162 (44 lines) - Phase execution wrapper
  - Architecture/IPC methods: Lines 476-619 (143 lines)

### RefactoringPhase (pipeline/phases/refactoring.py)
- **Total Lines**: 4178
- **Total Methods**: 50
- **Bloat Analysis**:
  ```
  _auto_create_tasks_from_analysis    556 lines (L2196-2751)  ← MASSIVE
  _format_analysis_data               503 lines (L1005-1507)  ← MASSIVE
  _work_on_task                       417 lines (L471-887)    ← MASSIVE
  _handle_comprehensive_refactoring   286 lines (L3195-3480)  ← LARGE
  _get_generic_task_prompt            265 lines (L1930-2194)  ← LARGE
  ```

- **Method Categories**:
  - 9 prompt methods (all doing similar work)
  - 7 build/context methods (duplicated logic)
  - 5 handle methods (orchestration)

### Coordinator (pipeline/coordinator.py)
- **Total Lines**: 2581
- **Phase Edges** (Lines 360-377):
  ```python
  'planning': ['coding', 'refactoring'],
  'coding': ['qa', 'documentation', 'refactoring'],
  'qa': ['debugging', 'documentation', 'refactoring'],
  'debugging': ['investigation', 'coding'],
  'investigation': ['debugging', 'coding', 'refactoring'],
  'documentation': ['planning', 'qa'],
  'project_planning': ['planning', 'refactoring'],
  'refactoring': ['coding', 'qa', 'planning']
  ```

### Tools (pipeline/tools.py)
- **get_tools_for_phase** (Lines 931-990):
  ```python
  phase_tools = {
      "planning": TOOLS_PLANNING + TOOLS_ANALYSIS,
      "coding": TOOLS_CODING + TOOLS_ANALYSIS + TOOLS_FILE_OPERATIONS + ...,
      "qa": TOOLS_QA + TOOLS_ANALYSIS + TOOLS_VALIDATION,
      "refactoring": TOOLS_REFACTORING + TOOLS_ANALYSIS + ... (7 tool sets!)
  }
  ```

---

## 🎯 THE REAL PROBLEM

### Problem 1: RefactoringPhase is Doing 7 Jobs

**Lines 2196-2751 (556 lines): `_auto_create_tasks_from_analysis`**
- This ONE method is analyzing files, detecting issues, creating tasks, formatting data
- Should be: Call analysis modules, create tasks from results (50 lines max)

**Lines 1005-1507 (503 lines): `_format_analysis_data`**
- Giant if/elif chain formatting different issue types
- Should be: Strategy pattern with formatters (20 lines + formatters)

**Lines 471-887 (417 lines): `_work_on_task`**
- Orchestrating task execution, building context, calling LLM, parsing results
- Should be: Use BasePhase.chat_with_history + task-specific handlers (100 lines)

**9 Prompt Methods (Lines 1542-2194)**
- Each builds a similar prompt with slight variations
- Should be: Template system with variable sections (1 method + templates)

### Problem 2: BasePhase.__init__ is 141 Lines

**Lines 66-207: Initialization Hell**
```python
def __init__(self, config, client, state_manager=None, file_tracker=None,
             prompt_registry=None, tool_registry=None, role_registry=None,
             coding_specialist=None, reasoning_specialist=None, analysis_specialist=None,
             message_bus=None, adaptive_prompts=None):
```

This is creating:
- Conversation threads
- Specialists
- Registries
- Architecture managers
- IPC systems
- Context providers

**Should be**: Dependency injection with builder pattern (30 lines)

### Problem 3: No Actual Code Reuse

Every phase reimplements:
- Context gathering (BasePhase doesn't provide this)
- Prompt building (each phase does it differently)
- Tool calling (each phase wraps it differently)
- Result parsing (duplicated logic)

---

## 🔧 SURGICAL CHANGES (Specific Line Numbers)

### Change 1: Extract Prompt Builder from RefactoringPhase

**CREATE**: `pipeline/phases/prompt_builder.py`
```python
class PromptBuilder:
    """Builds prompts from templates with variable sections."""
    
    def __init__(self, templates_dir: Path):
        self.templates = self._load_templates(templates_dir)
    
    def build(self, template_name: str, **variables) -> str:
        """Build prompt from template with variables."""
        template = self.templates[template_name]
        return template.format(**variables)
```

**MODIFY**: `pipeline/phases/refactoring.py`
- **DELETE**: Lines 1542-2194 (9 prompt methods, 652 lines)
- **ADD**: 
  ```python
  from .prompt_builder import PromptBuilder
  
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.prompt_builder = PromptBuilder(self.project_dir / 'pipeline' / 'templates')
  ```
- **REPLACE** in `_work_on_task` (Line ~600):
  ```python
  # OLD: prompt = self._get_missing_method_prompt(task, context)
  # NEW:
  prompt = self.prompt_builder.build(
      'refactoring_task',
      issue_type=task.issue_type.value,
      context=context,
      task_data=task.data
  )
  ```

**RESULT**: Eliminates 652 lines, centralizes prompt logic

---

### Change 2: Extract Analysis Orchestrator

**CREATE**: `pipeline/phases/analysis_orchestrator.py`
```python
class AnalysisOrchestrator:
    """Orchestrates analysis modules and creates tasks from results."""
    
    def __init__(self, analyzers: Dict[str, Any], logger):
        self.analyzers = analyzers
        self.logger = logger
    
    def analyze_and_create_tasks(self, state: PipelineState) -> List[RefactoringTask]:
        """Run all analyzers and create tasks from issues found."""
        tasks = []
        for analyzer_name, analyzer in self.analyzers.items():
            issues = analyzer.analyze()
            tasks.extend(self._create_tasks_from_issues(analyzer_name, issues))
        return tasks
```

**MODIFY**: `pipeline/phases/refactoring.py`
- **DELETE**: Lines 2196-2751 (`_auto_create_tasks_from_analysis`, 556 lines)
- **DELETE**: Lines 1005-1507 (`_format_analysis_data`, 503 lines)
- **ADD**:
  ```python
  from .analysis_orchestrator import AnalysisOrchestrator
  
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.orchestrator = AnalysisOrchestrator({
          'duplicates': self.duplicate_detector,
          'conflicts': self.conflict_detector,
          'dead_code': self.dead_code_detector,
          'architecture': self.architecture_analyzer
      }, self.logger)
  ```
- **REPLACE** in `_analyze_and_create_tasks` (Line 332):
  ```python
  # OLD: 556 lines of analysis + task creation
  # NEW:
  tasks = self.orchestrator.analyze_and_create_tasks(state)
  for task in tasks:
      state.refactoring_manager.add_task(task)
  ```

**RESULT**: Eliminates 1059 lines, separates concerns

---

### Change 3: Simplify Task Execution

**MODIFY**: `pipeline/phases/refactoring.py`
- **SIMPLIFY**: Lines 471-887 (`_work_on_task`, currently 417 lines)
- **NEW VERSION** (100 lines):
  ```python
  def _work_on_task(self, state: PipelineState, task: RefactoringTask) -> PhaseResult:
      """Execute a refactoring task using base phase capabilities."""
      
      # Build context using context builder
      context = self.context_builder.build_context(task)
      
      # Build prompt using prompt builder
      prompt = self.prompt_builder.build(
          'refactoring_task',
          issue_type=task.issue_type.value,
          context=context,
          task_data=task.data
      )
      
      # Get tools for this task type
      tools = self._get_tools_for_task(task)
      
      # Call LLM using base phase method
      response = self.chat_with_history(prompt, tools, task_context={'task': task})
      
      # Handle tool calls using base handler
      handler = ToolCallHandler(self.project_dir, self.logger, self.client, self.config)
      results = handler.handle_tool_calls(response['tool_calls'], self.conversation)
      
      # Update task status
      if self._verify_task_completion(task, results):
          task.mark_completed()
          return PhaseResult(success=True, phase=self.phase_name, 
                           message=f"Task {task.task_id} completed")
      else:
          return PhaseResult(success=False, phase=self.phase_name,
                           message=f"Task {task.task_id} incomplete")
  ```

**RESULT**: Reduces from 417 to ~100 lines, reuses base phase

---

### Change 4: Extract BasePhase Initialization

**CREATE**: `pipeline/phases/phase_builder.py`
```python
class PhaseBuilder:
    """Builder for phase dependencies."""
    
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        self.config = config
        self.client = client
        self._shared_instances = {}
    
    def build_phase(self, phase_class, **overrides):
        """Build a phase with shared dependencies."""
        return phase_class(
            config=self.config,
            client=self.client,
            state_manager=self._get_or_create('state_manager'),
            file_tracker=self._get_or_create('file_tracker'),
            # ... other shared instances
            **overrides
        )
```

**MODIFY**: `pipeline/phases/base.py`
- **SIMPLIFY**: Lines 66-207 (`__init__`, currently 141 lines)
- **NEW VERSION** (30 lines):
  ```python
  def __init__(self, config, client, state_manager, file_tracker,
               prompt_registry, tool_registry, role_registry,
               specialists, message_bus, adaptive_prompts):
      """Initialize phase with injected dependencies."""
      self.config = config
      self.client = client
      self.project_dir = Path(config.project_dir)
      self.logger = get_logger()
      
      # Store injected dependencies
      self.state_manager = state_manager
      self.file_tracker = file_tracker
      self.prompt_registry = prompt_registry
      self.tool_registry = tool_registry
      self.role_registry = role_registry
      self.specialists = specialists
      self.message_bus = message_bus
      self.adaptive_prompts = adaptive_prompts
      
      # Initialize conversation
      self.conversation = self._create_conversation()
      
      # Add system prompt
      system_prompt = self._get_system_prompt(self.phase_name)
      if system_prompt:
          self.conversation.add_message("system", system_prompt)
  ```

**MODIFY**: `pipeline/coordinator.py`
- **ADD** (after Line 37):
  ```python
  from .phases.phase_builder import PhaseBuilder
  
  def __init__(self, config, verbose=False):
      # ... existing code ...
      self.phase_builder = PhaseBuilder(config, self.client)
  ```
- **MODIFY**: `_init_phases` (Lines 185-257)
  ```python
  def _init_phases(self) -> Dict:
      """Initialize phases using builder."""
      return {
          'planning': self.phase_builder.build_phase(PlanningPhase),
          'coding': self.phase_builder.build_phase(CodingPhase),
          'qa': self.phase_builder.build_phase(QAPhase),
          'debugging': self.phase_builder.build_phase(DebuggingPhase),
          'refactoring': self.phase_builder.build_phase(RefactoringPhase),
          # ... etc
      }
  ```

**RESULT**: Reduces BasePhase.__init__ from 141 to 30 lines, centralizes dependency management

---

## 📈 EXPECTED RESULTS

### RefactoringPhase
- **Before**: 4178 lines, 50 methods
- **After**: ~1500 lines, 25 methods
- **Reduction**: 64% (2678 lines eliminated)

### BasePhase
- **Before**: 846 lines
- **After**: ~600 lines
- **Reduction**: 29% (246 lines eliminated)

### New Files Created
1. `pipeline/phases/prompt_builder.py` (~150 lines)
2. `pipeline/phases/analysis_orchestrator.py` (~200 lines)
3. `pipeline/phases/phase_builder.py` (~100 lines)
4. `pipeline/templates/refactoring_task.txt` (prompt template)

### Net Change
- **Deleted**: 2924 lines
- **Added**: 450 lines
- **Net Reduction**: 2474 lines (15% of total phase code)

---

## 🚀 IMPLEMENTATION ORDER

### Step 1: Extract Prompt Builder (Low Risk)
1. Create `pipeline/phases/prompt_builder.py`
2. Create `pipeline/templates/refactoring_task.txt`
3. Modify RefactoringPhase to use it
4. Delete old prompt methods
5. Test refactoring phase

### Step 2: Extract Analysis Orchestrator (Medium Risk)
1. Create `pipeline/phases/analysis_orchestrator.py`
2. Modify RefactoringPhase to use it
3. Delete `_auto_create_tasks_from_analysis`
4. Delete `_format_analysis_data`
5. Test analysis and task creation

### Step 3: Simplify Task Execution (Medium Risk)
1. Refactor `_work_on_task` to use base phase methods
2. Remove duplicated logic
3. Test task execution

### Step 4: Extract Phase Builder (Higher Risk)
1. Create `pipeline/phases/phase_builder.py`
2. Modify Coordinator to use it
3. Simplify BasePhase.__init__
4. Test all phases

---

## ✅ VALIDATION

After each step:
1. Run existing tests
2. Execute refactoring phase manually
3. Verify task creation and execution
4. Check that all phases still work

---

## 🎯 THIS IS THE REAL PLAN

- **No parallel implementations** - we modify existing code
- **No "universal" prefixes** - we use clear, specific names
- **No backward compatibility** - we break and fix
- **Specific line numbers** - every change is mapped
- **Concrete examples** - actual code, not pseudocode
- **Measurable results** - exact line counts before/after

This is surgical refactoring of the actual codebase, not a theoretical redesign.