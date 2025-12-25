# PROPOSAL: Self-Designing AI Development Pipeline

## Executive Summary

This proposal outlines a **2-week implementation** to transform the existing autonomy pipeline into a **self-designing system** where AI agents can dynamically create their own tools, prompts, and specialist roles. The solution leverages **90% existing infrastructure** and focuses on **sophisticated prompt engineering** with **minimal scaffolding** (10%).

**Key Innovation**: Instead of hardcoding capabilities, we enable AI to design and implement its own capabilities through meta-prompts and lightweight registration systems.

---

## Table of Contents

1. [Current System Analysis](#current-system-analysis)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Integration Points](#integration-points)
5. [Implementation Plan](#implementation-plan)
6. [Success Metrics](#success-metrics)

---

## 1. Current System Analysis

### 1.1 Existing Infrastructure (What We Have)

#### Pipeline Architecture
**File**: `pipeline/coordinator.py` (14,964 bytes)

The system uses a **phase-based coordinator** that orchestrates execution:

```python
class PhaseCoordinator:
    def _init_phases(self) -> Dict:
        return {
            "planning": PlanningPhase(self.config, self.client),
            "coding": CodingPhase(self.config, self.client),
            "qa": QAPhase(self.config, self.client),
            "debugging": DebuggingPhase(self.config, self.client),
            "project_planning": ProjectPlanningPhase(self.config, self.client),
            "documentation": DocumentationPhase(self.config, self.client),
        }
```

**Key Insight**: The coordinator uses a **dictionary-based phase registry**. We can extend this pattern for dynamic phase registration.

**Integration Point #1**: Add `"meta_agent": MetaAgentPhase(...)` to enable dynamic capability creation.

#### Base Phase Architecture
**File**: `pipeline/phases/base.py` (9,027 bytes)

All phases inherit from `BasePhase`:

```python
class BasePhase(ABC):
    def __init__(self, config: PipelineConfig, client: OllamaClient):
        self.config = config
        self.client = client
        self.project_dir = Path(config.project_dir)
        self.state_manager = StateManager(self.project_dir)
        self.parser = ResponseParser(client)
        self._tools_cache: Dict[str, List[Dict]] = {}
    
    @abstractmethod
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        pass
    
    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             task_type: str = None) -> Dict:
        # Lines 169-201: Handles model selection, temperature, timeout
        model_info = self.get_model_for_task(task_type or self.phase_name)
        # ... calls self.client.chat(host, model, messages, tools, temperature, timeout)
```

**Key Insight**: Every phase has access to:
- `self.chat()` - LLM communication
- `self.state_manager` - State persistence
- `self.parser` - Response parsing
- `self._tools_cache` - Tool definitions

**Integration Point #2**: New meta-agent phases can use the same infrastructure without modification.

#### Tool System
**File**: `pipeline/tools.py` (27,454 bytes)
**File**: `pipeline/handlers.py` (44,068 bytes)

Tools are defined as JSON schemas and executed by handlers:

```python
# tools.py - Lines 693-722
def get_tools_for_phase(phase: str) -> List[Dict]:
    phase_tools = {
        "planning": TOOLS_PLANNING,
        "coding": TOOLS_CODING,
        "qa": TOOLS_QA,
        "debugging": TOOLS_DEBUGGING,
        # ...
    }
    tools = phase_tools.get(phase, PIPELINE_TOOLS)
    tools = tools + TOOLS_MONITORING  # Add monitoring to all phases
    return tools
```

```python
# handlers.py - Lines 56-73
class ToolCallHandler:
    def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None):
        self._handlers: Dict[str, Callable] = {
            "create_python_file": self._handle_create_file,
            "modify_python_file": self._handle_modify_file,
            "read_file": self._handle_read_file,
            "search_code": self._handle_search_code,
            "list_directory": self._handle_list_directory,
            # ... monitoring tools
        }
```

**Key Insight**: 
1. Tools are registered in a **dictionary** (`self._handlers`)
2. Tool definitions are **JSON schemas** 
3. Handlers are **simple Python functions**

**Integration Point #3**: We can dynamically add tools by:
1. Adding entries to `self._handlers` dictionary
2. Adding tool schemas to phase tool lists
3. No code changes needed to existing infrastructure

#### Multi-Server Orchestration
**File**: `pipeline/config.py` (4,775 bytes)
**File**: `pipeline/client.py` (35,420 bytes)

The system already supports multiple Ollama servers:

```python
# config.py - Lines 30-42
@dataclass
class PipelineConfig:
    servers: List[ServerConfig] = field(default_factory=lambda: [
        ServerConfig(
            name="ollama01",
            host="ollama01.thiscluster.net",
            capabilities=["coding", "planning", "qa", "debugging"]
        ),
        ServerConfig(
            name="ollama02", 
            host="ollama02.thiscluster.net",
            capabilities=["routing", "quick_fix", "tool_formatting"]
        ),
    ])
    
    # Lines 76-87: Model assignments by task type
    model_assignments: Dict[str, Tuple[str, str]] = field(default_factory=lambda: {
        "planning":   ("qwen2.5:14b", "ollama02.thiscluster.net"),
        "coding":     ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        "debugging":  ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        # ...
    })
```

**Key Insight**: Server selection is **task-based**. We can assign new meta-agent tasks to specific servers.

**Integration Point #4**: Add meta-agent task types to `model_assignments`.

#### Specialist Agent System
**File**: `pipeline/specialist_agents.py` (14,303 bytes)
**File**: `pipeline/conversation_thread.py` (12,982 bytes)

Multi-agent collaboration already exists:

```python
# specialist_agents.py - Lines 17-24
@dataclass
class SpecialistConfig:
    name: str
    model: str
    host: str
    expertise: str
    system_prompt: str
    temperature: float = 0.3

# Lines 31-89
class SpecialistAgent:
    def analyze(self, thread: ConversationThread, tools: List[Dict]) -> Dict:
        # Build prompt with full context
        # Call specialist model
        # Return analysis
```

**Key Insight**: Specialists are **data-driven** - instantiated from `SpecialistConfig` objects.

**Integration Point #5**: Create specialists dynamically by instantiating with config objects.

### 1.2 What's Missing (What We Need to Build)

Based on analysis, we need **5 new components**:

1. **PromptArchitect** - Meta-prompt for designing prompts
2. **ToolDesigner** - Meta-prompt for designing tools
3. **RoleCreator** - Meta-prompt for designing roles
4. **LoopDetector** - Pattern detection to prevent infinite loops
5. **Dynamic Registries** - Lightweight systems to register new capabilities

**Total New Code**: ~6,000 lines (53% meta-prompts, 10% registries, 37% other)

---

## 2. Architecture Overview

### 2.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   META-AGENT LAYER                       │
│         (AI designs tools, prompts, roles)              │
├─────────────────────────────────────────────────────────┤
│  PromptArchitect │ ToolDesigner │ RoleCreator           │
│  LoopDetector    │ TeamOrchestrator                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              REGISTRATION LAYER                          │
│         (Runtime capability management)                 │
├─────────────────────────────────────────────────────────┤
│  PromptRegistry │ ToolRegistry │ RoleRegistry           │
│  (150 lines)    │ (200 lines)  │ (200 lines)            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              EXISTING INFRASTRUCTURE                     │
│  (File ops, tool calling, phases, specialists)          │
├─────────────────────────────────────────────────────────┤
│  BasePhase │ ToolCallHandler │ SpecialistAgent          │
│  StateManager │ OllamaClient │ ConversationThread       │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 PromptArchitect (3 days)

**Purpose**: Enable AI to design optimal prompts for any task or role.

**Files**:
- `pipeline/prompts/prompt_architect.py` (800 lines) - Meta-prompt
- `pipeline/prompt_registry.py` (150 lines) - Registry
- `pipeline/phases/prompt_design.py` (200 lines) - Phase

**Integration**: Uses existing `BasePhase.chat()`, `create_file` tool, prompt structure from `prompts.py`

### 3.2 ToolDesigner (3 days)

**Purpose**: Enable AI to design and implement custom tools.

**Files**:
- `pipeline/prompts/tool_designer.py` (800 lines) - Meta-prompt
- `pipeline/tool_registry.py` (200 lines) - Registry with security validation
- `pipeline/phases/tool_design.py` (200 lines) - Phase

**Integration**: Extends `ToolCallHandler._handlers` dictionary, follows existing tool patterns

### 3.3 RoleCreator (3 days)

**Purpose**: Enable AI to define new specialist roles dynamically.

**Files**:
- `pipeline/prompts/role_creator.py` (800 lines) - Meta-prompt
- `pipeline/role_registry.py` (200 lines) - Registry
- `pipeline/phases/role_design.py` (200 lines) - Phase

**Integration**: Uses existing `SpecialistAgent` class and `SpecialistConfig` dataclass

### 3.4 LoopDetector (2 days)

**Purpose**: Detect and break infinite loops in AI behavior.

**File**: `pipeline/loop_detector.py` (600 lines)

**Features**:
- 6 detection types: action loops, modification loops, conversation loops, circular dependencies, state cycles, pattern repetition
- Intervention system with suggestions
- Integration with ConversationThread

### 3.5 TeamOrchestrator (2 days)

**Purpose**: Coordinate multiple specialists working in parallel.

**Files**:
- `pipeline/prompts/team_orchestrator.py` (800 lines) - Meta-prompt
- `pipeline/team_orchestrator.py` (300 lines) - Coordinator

**Features**:
- Parallel execution across servers
- Result synthesis
- Conflict resolution

---

## 4. Integration Points Summary

### 4.1 Coordinator Integration
Add meta-agent phases to `_init_phases()` dictionary in `coordinator.py`

### 4.2 BasePhase Integration
Add registries to `__init__`: `self.prompt_registry`, `self.tool_registry`, `self.role_registry`

### 4.3 Tools Integration
Modify `get_tools_for_phase()` to include custom tools from registry

### 4.4 Config Integration
Add meta-agent task types to `model_assignments` dictionary

### 4.5 Debugging Phase Integration
Add loop detection and team orchestration to debugging workflow

---

## 5. Implementation Plan

### Week 1: Meta-Prompts + Registries
- **Days 1-2**: PromptArchitect (meta-prompt + registry + phase)
- **Days 3-4**: ToolDesigner (meta-prompt + registry + phase)
- **Day 5**: RoleCreator (meta-prompt + registry + phase)

### Week 2: Detection + Orchestration + Integration
- **Days 6-7**: LoopDetector (detection + intervention)
- **Days 8-9**: TeamOrchestrator (meta-prompt + coordinator)
- **Day 10**: Integration + Testing + Documentation

---

## 6. Success Metrics

### Capability Metrics
- AI creates custom prompts (< 2 min)
- AI creates custom tools (< 3 min)
- AI defines custom roles (< 3 min)
- Loop detection catches 90%+ of loops
- Team coordinates 3-5 specialists

### Quality Metrics
- Custom tools work correctly (80%+ success)
- Custom prompts achieve goals (75%+ effective)
- Custom roles provide value (70%+ useful)

### Performance Metrics
- Prompt creation: < 2 minutes
- Tool creation: < 3 minutes
- Role creation: < 3 minutes
- Loop detection: < 5 seconds
- Team coordination: < 10 minutes

---

## 7. Key Questions Answered

**Q: How does this integrate with existing phases?**
A: All components extend existing infrastructure - new phases inherit from BasePhase, new tools use ToolCallHandler, new roles use SpecialistAgent.

**Q: How are custom capabilities persisted?**
A: Three mechanisms: files in `pipeline/{prompts,tools,roles}/custom/`, registries load on startup, optional state storage.

**Q: How does security work for custom tools?**
A: `ToolRegistry._is_safe()` validates: no dangerous operations, error handling present, input validation, timeout limits.

**Q: How does team orchestration use both servers?**
A: `ThreadPoolExecutor` distributes specialists across servers based on model assignments, runs in parallel, synthesizes results.

**Q: What happens when a loop is detected?**
A: System message added to thread with analysis, suggestions for alternatives, AI can pivot strategy or escalate.

---

## 8. Conclusion

This proposal delivers a **self-designing AI system** in **2 weeks** by:

1. **Leveraging 90% existing infrastructure** (phases, tools, multi-agent, multi-server)
2. **Adding 10% focused scaffolding** (registries, detection, orchestration)
3. **Focusing on prompt engineering** (53% of code is meta-prompts)
4. **Enabling recursive improvement** (AI creates tools that create tools)

**Total New Code**: ~6,000 lines
**Implementation Time**: 2 weeks
**Leverage Factor**: 10x (90% existing, 10% new)