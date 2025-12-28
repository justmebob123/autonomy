================================================================================
DEPTH-61 RECURSIVE CALL STACK ANALYSIS REPORT
================================================================================

## SUMMARY
Total Subsystems Analyzed: 5
Total Files Analyzed: 134
Total Classes Found: 183
Integration Mismatches Found: 77

## SUBSYSTEM ANALYSIS

### pipeline
Files: 102
Classes: 133
Unique Variables: 1363

Classes:
  - SignatureExtractor (inherits from: object)
    Methods: 6
  - SyntaxValidator (inherits from: object)
    Methods: 5
  - ToolRegistry (inherits from: object)
    Methods: 15
  - ExecutionPattern (inherits from: object)
    Methods: 2
  - PatternRecognitionSystem (inherits from: object)
    Methods: 13
  - PhaseCoordinator (inherits from: object)
    Methods: 29
  - ModificationFailure (inherits from: object)
    Methods: 2
  - FailureAnalyzer (inherits from: object)
    Methods: 15
  - ToolCallHandler (inherits from: object)
    Methods: 39
  - ImportAnalyzer (inherits from: object)
    Methods: 4

### pipeline/phases
Files: 16
Classes: 16
Unique Variables: 344

Classes:
  - PhaseResult (inherits from: object)
    Methods: 2
  - BasePhase (inherits from: ABC)
    Methods: 15
  - CodingPhase (inherits from: BasePhase, LoopDetectionMixin)
    Methods: 5
  - DebuggingPhase (inherits from: LoopDetectionMixin, BasePhase)
    Methods: 13
  - DocumentationPhase (inherits from: LoopDetectionMixin, BasePhase)
    Methods: 9
  - InvestigationPhase (inherits from: BasePhase)
    Methods: 7
  - LoopDetectionMixin (inherits from: object)
    Methods: 3
  - PlanningPhase (inherits from: BasePhase, LoopDetectionMixin)
    Methods: 6
  - ProjectPlanningPhase (inherits from: LoopDetectionMixin, BasePhase)
    Methods: 13
  - PromptDesignPhase (inherits from: LoopDetectionMixin, BasePhase)
    Methods: 3

### pipeline/orchestration
Files: 12
Classes: 22
Unique Variables: 200

Classes:
  - ArbiterModel (inherits from: object)
    Methods: 14
  - OrchestrationConversationThread (inherits from: object)
    Methods: 6
  - MultiModelConversationManager (inherits from: object)
    Methods: 11
  - PromptContext (inherits from: object)
    Methods: 0
  - PromptSection (inherits from: object)
    Methods: 2
  - DynamicPromptBuilder (inherits from: object)
    Methods: 22
  - UnifiedModelTool (inherits from: object)
    Methods: 8
  - PruningConfig (inherits from: object)
    Methods: 0
  - ConversationPruner (inherits from: object)
    Methods: 8
  - AutoPruningConversationThread (inherits from: object)
    Methods: 7

### pipeline/state
Files: 4
Classes: 12
Unique Variables: 119

Classes:
  - FileTracker (inherits from: object)
    Methods: 16
  - TaskStatus (inherits from: str, Enum)
    Methods: 0
  - FileStatus (inherits from: str, Enum)
    Methods: 0
  - TaskError (inherits from: object)
    Methods: 2
  - TaskState (inherits from: object)
    Methods: 5
  - FileState (inherits from: object)
    Methods: 3
  - PhaseState (inherits from: object)
    Methods: 12
  - PipelineState (inherits from: object)
    Methods: 20
  - StateManager (inherits from: object)
    Methods: 18
  - TaskPriority (inherits from: IntEnum)
    Methods: 0

### pipeline/tools
Files: 0
Classes: 0
Unique Variables: 0

## INTEGRATION MISMATCHES

### variable_type_mismatch
Variable: error_count
Types: sum, len
Instances:
  - pipeline: len
  - pipeline: sum
  - pipeline: sum
  - pipeline/phases: sum

### variable_type_mismatch
Variable: total_tasks
Types: sum, len
Instances:
  - pipeline: len
  - pipeline: sum
  - pipeline: len
  - pipeline/phases: len

### variable_type_mismatch
Variable: failed
Types: sum, int
Instances:
  - pipeline: sum
  - pipeline: int
  - pipeline: int
  - pipeline/phases: int

### variable_type_mismatch
Variable: issues
Types: List[Dict], list
Instances:
  - pipeline: list
  - pipeline: list
  - pipeline: list
  - pipeline: list
  - pipeline: List[Dict]

### variable_type_mismatch
Variable: issue
Types: dict, get_next_issue
Instances:
  - pipeline: dict
  - pipeline: get_next_issue
  - pipeline: get_next_issue
  - pipeline: dict
  - pipeline/phases: get_next_issue

### variable_type_mismatch
Variable: min_indent
Types: float, min, int
Instances:
  - pipeline: float
  - pipeline: int
  - pipeline: float
  - pipeline: min
  - pipeline: int

### variable_type_mismatch
Variable: last_import_line
Types: int, max
Instances:
  - pipeline: int
  - pipeline: max
  - pipeline: max

### variable_type_mismatch
Variable: states
Types: dict, list
Instances:
  - pipeline: list
  - pipeline: dict
  - pipeline/state: dict

### variable_type_mismatch
Variable: functions
Types: sum, list
Instances:
  - pipeline: list
  - pipeline: sum

### variable_type_mismatch
Variable: queue
Types: deque, List[Dict]
Instances:
  - pipeline: deque
  - pipeline: List[Dict]
  - pipeline/state: List[Dict]

### variable_type_mismatch
Variable: metadata
Types: Dict, Dict[str, Any]
Instances:
  - pipeline: Dict[str, Any]
  - pipeline: Dict
  - pipeline: Dict[str, Any]
  - pipeline/state: Dict[str, Any]

### variable_type_mismatch
Variable: py_files
Types: sorted, list
Instances:
  - pipeline: list
  - pipeline: list
  - pipeline: sorted
  - pipeline/phases: list
  - pipeline/phases: sorted

### variable_type_mismatch
Variable: by_type
Types: dict, defaultdict
Instances:
  - pipeline: dict
  - pipeline: defaultdict

### variable_type_mismatch
Variable: agent_name
Types: str, Optional[str]
Instances:
  - pipeline: Optional[str]
  - pipeline: str

### variable_type_mismatch
Variable: attempt
Types: int, AttemptRecord
Instances:
  - pipeline: AttemptRecord
  - pipeline: int
  - pipeline/state: int

### variable_type_mismatch
Variable: code_snippet
Types: str, Optional[str]
Instances:
  - pipeline: str
  - pipeline: Optional[str]
  - pipeline/state: Optional[str]

### variable_type_mismatch
Variable: context_window
Types: int, getattr
Instances:
  - pipeline: getattr
  - pipeline: int
  - pipeline/phases: getattr
  - pipeline/orchestration: int

### variable_type_mismatch
Variable: constraints
Types: List[str], list
Instances:
  - pipeline: list
  - pipeline: List[str]
  - pipeline: List[str]
  - pipeline/phases: list
  - pipeline/orchestration: List[str]

### variable_type_mismatch
Variable: fix_history
Types: List[Dict], list
Instances:
  - pipeline: list
  - pipeline: List[Dict]
  - pipeline/phases: list
  - pipeline/state: List[Dict]

### variable_type_mismatch
Variable: decision_context
Types: dict, NoneType
Instances:
  - pipeline: NoneType
  - pipeline: dict
  - pipeline/phases: NoneType
  - pipeline/phases: dict

### variable_type_mismatch
Variable: by_priority
Types: dict, Dict[int, List[TaskState]]
Instances:
  - pipeline: Dict[int, List[TaskState]]
  - pipeline: dict
  - pipeline/phases: Dict[int, List[TaskState]]
  - pipeline/state: dict

### variable_type_mismatch
Variable: expansion_count
Types: int, getattr
Instances:
  - pipeline: getattr
  - pipeline: getattr
  - pipeline: getattr
  - pipeline: int
  - pipeline/phases: getattr

### variable_type_mismatch
Variable: IN_PROGRESS
Types: str, int
Instances:
  - pipeline: str
  - pipeline: int
  - pipeline/state: str
  - pipeline/state: int

### variable_type_mismatch
Variable: DEBUG_PENDING
Types: str, int
Instances:
  - pipeline: str
  - pipeline: int
  - pipeline/state: str
  - pipeline/state: int

### variable_type_mismatch
Variable: successes
Types: sum, int
Instances:
  - pipeline: int
  - pipeline: sum
  - pipeline/state: int
  - pipeline/state: sum

### variable_type_mismatch
Variable: total_tokens
Types: sum, int
Instances:
  - pipeline: int
  - pipeline: sum
  - pipeline/orchestration: int
  - pipeline/orchestration: sum

### variable_type_mismatch
Variable: _registry
Types: SpecialistRegistry, NoneType
Instances:
  - pipeline: NoneType
  - pipeline: SpecialistRegistry
  - pipeline/orchestration: NoneType
  - pipeline/orchestration: SpecialistRegistry

### duplicate_class
Class: PhaseResult
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: BasePhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: CodingPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: DebuggingPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: DocumentationPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: InvestigationPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: LoopDetectionMixin
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: PlanningPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: ProjectPlanningPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: PromptDesignPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: PromptImprovementPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: QAPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: RoleDesignPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: RoleImprovementPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: ToolDesignPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: ToolEvaluationPhase
Implementations: 2
  - pipeline
  - pipeline/phases

### duplicate_class
Class: FileTracker
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: TaskStatus
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: FileStatus
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: TaskError
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: TaskState
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: FileState
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: PhaseState
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: PipelineState
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: StateManager
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: TaskPriority
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: PriorityItem
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: PriorityQueue
Implementations: 2
  - pipeline
  - pipeline/state

### duplicate_class
Class: ArbiterModel
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: OrchestrationConversationThread
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: MultiModelConversationManager
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: PromptContext
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: PromptSection
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: DynamicPromptBuilder
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: UnifiedModelTool
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: PruningConfig
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: ConversationPruner
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: AutoPruningConversationThread
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: ModelTool
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: SpecialistRegistry
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: AnalysisType
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: AnalysisTask
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: AnalysisSpecialist
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: CodingTask
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: CodingSpecialist
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: InterpretationRequest
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: FunctionGemmaMediator
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: ReasoningType
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: ReasoningTask
Implementations: 2
  - pipeline
  - pipeline/orchestration

### duplicate_class
Class: ReasoningSpecialist
Implementations: 2
  - pipeline
  - pipeline/orchestration