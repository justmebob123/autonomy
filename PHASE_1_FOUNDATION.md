# Phase 1: Foundation & Analysis Tools

**Timeline:** 2-3 weeks  
**Priority:** CRITICAL  
**Dependencies:** None  
**Deliverables:** 7 major components + comprehensive testing

---

## Overview

Phase 1 establishes the foundational tools required for comprehensive system analysis, loop detection, and context gathering. These tools are essential for all subsequent phases and address critical gaps in the current system.

---

## Objectives

1. **Enable Comprehensive Context Gathering**: Provide tools to analyze file structure, schemas, and dependencies
2. **Implement Loop Detection**: Identify infinite loops, circular dependencies, and repeated patterns
3. **Enhance Debugging Capabilities**: Trace call flows, analyze execution paths, track modifications
4. **Improve Patch Management**: Organize, search, and apply patches systematically
5. **Build Dependency Intelligence**: Create and maintain dependency graphs

---

## Component 1: File Structure Analyzer

### Purpose
Provide comprehensive analysis of project file structure, organization, and relationships.

### Capabilities
- **Directory Tree Generation**: Create visual tree representations of project structure
- **File Type Analysis**: Categorize files by type, purpose, and role
- **Size and Complexity Metrics**: Calculate LOC, complexity scores, file sizes
- **Organization Patterns**: Identify architectural patterns (MVC, layered, etc.)
- **Naming Convention Analysis**: Detect and validate naming patterns
- **Module Boundaries**: Identify logical module boundaries and cohesion

### Implementation Details

#### File: `pipeline/analysis/file_structure.py`

```python
class FileStructureAnalyzer:
    """Analyzes project file structure and organization."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.file_tree = {}
        self.metrics = {}
        
    def analyze_structure(self) -> Dict:
        """
        Comprehensive structure analysis.
        
        Returns:
            {
                'tree': nested dict representation,
                'metrics': {
                    'total_files': int,
                    'total_dirs': int,
                    'file_types': {'py': 50, 'md': 10, ...},
                    'total_loc': int,
                    'avg_file_size': float
                },
                'patterns': {
                    'architecture': 'layered|mvc|microservices',
                    'naming_convention': 'snake_case|camelCase',
                    'organization': 'feature|layer|domain'
                },
                'modules': [
                    {
                        'name': 'pipeline',
                        'path': 'pipeline/',
                        'files': 30,
                        'loc': 5000,
                        'cohesion': 0.85
                    }
                ]
            }
        """
        
    def get_file_relationships(self, filepath: str) -> Dict:
        """
        Analyze relationships for a specific file.
        
        Returns:
            {
                'imports': ['module1', 'module2'],
                'imported_by': ['file1.py', 'file2.py'],
                'dependencies': ['dep1', 'dep2'],
                'dependents': ['file3.py'],
                'related_files': ['test_file.py', 'file_config.py']
            }
        """
        
    def find_similar_files(self, filepath: str, threshold: float = 0.7) -> List[Dict]:
        """Find files with similar structure or purpose."""
        
    def suggest_refactoring(self) -> List[Dict]:
        """Suggest refactoring opportunities based on structure analysis."""
```

#### Tool Definition

```python
TOOL_ANALYZE_FILE_STRUCTURE = {
    "type": "function",
    "function": {
        "name": "analyze_file_structure",
        "description": "Analyze project file structure, organization, and relationships. Use this to understand the overall architecture and find related files.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["full", "directory", "file"],
                    "description": "Scope of analysis"
                },
                "path": {
                    "type": "string",
                    "description": "Path to analyze (for directory or file scope)"
                },
                "include_metrics": {
                    "type": "boolean",
                    "description": "Include complexity and size metrics"
                },
                "find_related": {
                    "type": "boolean",
                    "description": "Find related files and dependencies"
                }
            },
            "required": ["scope"]
        }
    }
}
```

### Testing Requirements
- Test with various project structures (flat, nested, modular)
- Validate metrics accuracy
- Test relationship detection
- Benchmark performance on large projects (1000+ files)

---

## Component 2: Schema Inspector

### Purpose
Analyze code schemas, class hierarchies, function signatures, and data structures.

### Capabilities
- **Class Hierarchy Analysis**: Build inheritance trees, identify abstract classes
- **Function Signature Extraction**: Parse parameters, return types, decorators
- **Data Structure Mapping**: Identify dataclasses, TypedDicts, Pydantic models
- **API Surface Analysis**: Identify public vs private interfaces
- **Type Annotation Coverage**: Calculate type hint coverage
- **Contract Validation**: Verify interface contracts and protocols

### Implementation Details

#### File: `pipeline/analysis/schema_inspector.py`

```python
class SchemaInspector:
    """Inspects code schemas, types, and structures."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.ast_cache = {}
        
    def analyze_class_hierarchy(self, class_name: str = None) -> Dict:
        """
        Analyze class inheritance and relationships.
        
        Returns:
            {
                'classes': [
                    {
                        'name': 'BasePhase',
                        'file': 'pipeline/phases/base.py',
                        'bases': ['ABC'],
                        'subclasses': ['PlanningPhase', 'CodingPhase'],
                        'methods': [...],
                        'attributes': [...],
                        'abstract': True
                    }
                ],
                'hierarchy': {
                    'BasePhase': {
                        'PlanningPhase': {},
                        'CodingPhase': {}
                    }
                }
            }
        """
        
    def extract_function_signatures(self, module: str = None) -> List[Dict]:
        """
        Extract all function signatures with full type information.
        
        Returns:
            [
                {
                    'name': 'execute',
                    'file': 'pipeline/phases/base.py',
                    'parameters': [
                        {'name': 'state', 'type': 'PipelineState', 'default': None},
                        {'name': 'task', 'type': 'TaskState', 'default': None}
                    ],
                    'return_type': 'PhaseResult',
                    'decorators': ['abstractmethod'],
                    'docstring': '...',
                    'complexity': 5
                }
            ]
        """
        
    def analyze_data_structures(self) -> Dict:
        """Identify and analyze all data structures (dataclasses, TypedDicts, etc.)."""
        
    def get_api_surface(self, module: str) -> Dict:
        """
        Analyze public API surface of a module.
        
        Returns:
            {
                'public_functions': [...],
                'public_classes': [...],
                'exports': [...],
                'entry_points': [...]
            }
        """
        
    def validate_type_coverage(self) -> Dict:
        """Calculate type annotation coverage across project."""
        
    def find_interface_violations(self) -> List[Dict]:
        """Find places where interfaces/protocols are violated."""
```

#### Tool Definition

```python
TOOL_INSPECT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "inspect_schema",
        "description": "Inspect code schemas, class hierarchies, function signatures, and data structures. Use this to understand code organization and interfaces.",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["class_hierarchy", "function_signatures", "data_structures", "api_surface", "type_coverage"],
                    "description": "Type of schema analysis to perform"
                },
                "target": {
                    "type": "string",
                    "description": "Specific class, module, or file to analyze (optional)"
                },
                "include_private": {
                    "type": "boolean",
                    "description": "Include private members in analysis"
                }
            },
            "required": ["analysis_type"]
        }
    }
}
```

### Testing Requirements
- Test with complex class hierarchies
- Validate type extraction accuracy
- Test with various Python versions (3.9+)
- Benchmark AST parsing performance

---

## Component 3: Call Flow Tracer

### Purpose
Trace execution paths, function calls, and control flow through the codebase.

### Capabilities
- **Call Chain Tracing**: Build complete call chains from entry points
- **Execution Path Analysis**: Identify all possible execution paths
- **Dependency Tracking**: Track which functions call which
- **Dead Code Detection**: Identify unreachable code
- **Hotspot Identification**: Find frequently called functions
- **Recursion Detection**: Identify recursive calls and depth

### Implementation Details

#### File: `pipeline/analysis/call_flow_tracer.py`

```python
class CallFlowTracer:
    """Traces call flows and execution paths."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.call_graph = nx.DiGraph()
        
    def build_call_graph(self) -> nx.DiGraph:
        """
        Build complete call graph for the project.
        
        Returns:
            NetworkX directed graph where:
            - Nodes are functions/methods
            - Edges represent calls
            - Edge weights represent call frequency (if available)
        """
        
    def trace_call_chain(self, start_function: str, max_depth: int = 10) -> List[List[str]]:
        """
        Trace all call chains starting from a function.
        
        Returns:
            [
                ['main', 'execute', 'run_phase', 'debug'],
                ['main', 'execute', 'run_phase', 'qa'],
                ...
            ]
        """
        
    def find_execution_paths(self, start: str, end: str) -> List[List[str]]:
        """Find all execution paths between two functions."""
        
    def identify_hotspots(self, threshold: int = 10) -> List[Dict]:
        """
        Identify functions called frequently.
        
        Returns:
            [
                {
                    'function': 'execute_tool_call',
                    'call_count': 150,
                    'callers': ['debugging', 'coding', 'qa'],
                    'file': 'pipeline/handlers.py'
                }
            ]
        """
        
    def detect_recursion(self) -> List[Dict]:
        """
        Detect recursive calls and analyze recursion depth.
        
        Returns:
            [
                {
                    'function': 'process_nested',
                    'type': 'direct|indirect',
                    'cycle': ['process_nested', 'helper', 'process_nested'],
                    'max_depth': 5
                }
            ]
        """
        
    def find_dead_code(self) -> List[Dict]:
        """Identify functions that are never called."""
        
    def analyze_call_complexity(self, function: str) -> Dict:
        """
        Analyze complexity of a function's call patterns.
        
        Returns:
            {
                'function': 'execute',
                'calls_made': 15,
                'unique_callees': 8,
                'max_call_depth': 5,
                'cyclomatic_complexity': 12,
                'cognitive_complexity': 18
            }
        """
```

#### Tool Definition

```python
TOOL_TRACE_CALL_FLOW = {
    "type": "function",
    "function": {
        "name": "trace_call_flow",
        "description": "Trace function call flows and execution paths. Use this to understand how code executes and find call chains.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["trace_chain", "find_paths", "identify_hotspots", "detect_recursion", "find_dead_code"],
                    "description": "Type of call flow analysis"
                },
                "start_function": {
                    "type": "string",
                    "description": "Starting function for trace (required for trace_chain and find_paths)"
                },
                "end_function": {
                    "type": "string",
                    "description": "Ending function (required for find_paths)"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to trace (default: 10)"
                }
            },
            "required": ["operation"]
        }
    }
}
```

### Testing Requirements
- Test with complex call chains
- Validate recursion detection
- Test with circular dependencies
- Benchmark graph building performance

---

## Component 4: Loop Detection Engine

### Purpose
**CRITICAL COMPONENT** - Detect infinite loops, circular dependencies, and repeated patterns that cause system failures.

### Capabilities
- **Infinite Loop Detection**: Identify loops that never terminate
- **Circular Dependency Detection**: Find circular imports and call cycles
- **Pattern Repetition Detection**: Identify repeated error patterns
- **State Cycle Detection**: Detect when system returns to previous states
- **Modification Loop Detection**: Identify when same code is modified repeatedly
- **Conversation Loop Detection**: Detect when AI repeats same responses

### Implementation Details

#### File: `pipeline/analysis/loop_detector.py`

```python
class LoopDetector:
    """Detects various types of loops and circular patterns."""
    
    def __init__(self, project_dir: Path, history_window: int = 100):
        self.project_dir = project_dir
        self.history_window = history_window
        self.action_history = deque(maxlen=history_window)
        self.state_history = deque(maxlen=history_window)
        self.modification_history = {}
        
    def detect_action_loop(self, current_action: Dict) -> Optional[Dict]:
        """
        Detect if current action is part of a loop.
        
        Returns:
            {
                'loop_detected': True,
                'loop_type': 'exact_repetition|similar_pattern|state_cycle',
                'loop_length': 5,
                'loop_start': 10,
                'loop_actions': [...],
                'confidence': 0.95,
                'recommendation': 'Break loop by trying alternative approach'
            }
        """
        
    def detect_modification_loop(self, filepath: str, modification: str) -> Optional[Dict]:
        """
        Detect if same file is being modified repeatedly without progress.
        
        Returns:
            {
                'loop_detected': True,
                'file': 'pipeline_ui.py',
                'modification_count': 5,
                'modifications': [
                    {'attempt': 1, 'change': 'wrapped in try/except', 'result': 'failed'},
                    {'attempt': 2, 'change': 'wrapped in try/except', 'result': 'failed'},
                    ...
                ],
                'pattern': 'repeated_wrapping',
                'recommendation': 'Try different approach - wrapping not working'
            }
        """
        
    def detect_conversation_loop(self, messages: List[Dict]) -> Optional[Dict]:
        """
        Detect if AI is repeating same responses.
        
        Returns:
            {
                'loop_detected': True,
                'loop_type': 'exact_repetition|semantic_similarity',
                'repeated_message': '...',
                'repetition_count': 3,
                'similarity_scores': [0.95, 0.92, 0.98],
                'recommendation': 'Inject new context or change approach'
            }
        """
        
    def detect_circular_dependency(self) -> List[Dict]:
        """
        Detect circular dependencies in imports.
        
        Returns:
            [
                {
                    'cycle': ['module_a', 'module_b', 'module_c', 'module_a'],
                    'type': 'import|call',
                    'severity': 'high|medium|low',
                    'impact': 'Prevents proper initialization'
                }
            ]
        """
        
    def detect_state_cycle(self, current_state: Dict) -> Optional[Dict]:
        """
        Detect if system has returned to a previous state.
        
        Returns:
            {
                'cycle_detected': True,
                'previous_state_index': 15,
                'cycle_length': 8,
                'state_similarity': 0.98,
                'actions_in_cycle': [...],
                'recommendation': 'System is cycling - need different strategy'
            }
        """
        
    def analyze_loop_pattern(self, loop_data: Dict) -> Dict:
        """
        Analyze a detected loop to understand its cause.
        
        Returns:
            {
                'root_cause': 'verification_logic_bug',
                'contributing_factors': ['wrapping_not_detected', 'false_positive'],
                'suggested_fixes': [
                    'Fix verification logic to handle wrapping',
                    'Add wrapping detection',
                    'Skip verification for wrapping operations'
                ],
                'priority': 'critical'
            }
        """
        
    def get_loop_breaking_suggestions(self, loop_data: Dict) -> List[str]:
        """Generate specific suggestions for breaking the detected loop."""
```

#### Tool Definition

```python
TOOL_DETECT_LOOPS = {
    "type": "function",
    "function": {
        "name": "detect_loops",
        "description": "Detect infinite loops, circular dependencies, and repeated patterns. CRITICAL for preventing system failures.",
        "parameters": {
            "type": "object",
            "properties": {
                "detection_type": {
                    "type": "string",
                    "enum": ["action_loop", "modification_loop", "conversation_loop", "circular_dependency", "state_cycle", "all"],
                    "description": "Type of loop to detect"
                },
                "context": {
                    "type": "object",
                    "description": "Context for detection (current action, file, messages, etc.)"
                },
                "history_window": {
                    "type": "integer",
                    "description": "Number of recent actions to analyze (default: 100)"
                }
            },
            "required": ["detection_type"]
        }
    }
}
```

### Integration Points

**1. Debugging Phase Integration:**
```python
# In debugging.py, before each fix attempt:
loop_check = loop_detector.detect_modification_loop(filepath, proposed_change)
if loop_check and loop_check['loop_detected']:
    # Alert architect agent
    # Try alternative approach
    # Or escalate to user
```

**2. Conversation Thread Integration:**
```python
# In conversation_thread.py, after each message:
loop_check = loop_detector.detect_conversation_loop(thread.messages)
if loop_check and loop_check['loop_detected']:
    # Inject new context
    # Change strategy
    # Consult different specialist
```

**3. Coordinator Integration:**
```python
# In coordinator.py, after each iteration:
loop_check = loop_detector.detect_action_loop(current_action)
if loop_check and loop_check['loop_detected']:
    # Log warning
    # Change phase
    # Consult architect
```

### Testing Requirements
- Test with known infinite loop scenarios
- Validate detection accuracy (minimize false positives)
- Test with various loop patterns
- Benchmark detection performance
- Test integration with existing phases

---

## Component 5: Pattern Recognition System

### Purpose
Identify patterns in code, errors, fixes, and system behavior.

### Capabilities
- **Error Pattern Recognition**: Identify recurring error patterns
- **Fix Pattern Recognition**: Identify successful fix patterns
- **Code Pattern Recognition**: Identify common code patterns
- **Behavioral Pattern Recognition**: Identify system behavior patterns
- **Anti-Pattern Detection**: Identify problematic patterns
- **Pattern Learning**: Learn from successful and failed patterns

### Implementation Details

#### File: `pipeline/analysis/pattern_recognizer.py`

```python
class PatternRecognizer:
    """Recognizes patterns in code, errors, and system behavior."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.pattern_db = PatternDatabase()
        self.ml_model = PatternLearningModel()
        
    def recognize_error_pattern(self, error: Dict) -> Optional[Dict]:
        """
        Recognize if error matches known patterns.
        
        Returns:
            {
                'pattern_matched': True,
                'pattern_name': 'curses_initialization_error',
                'pattern_id': 'ERR_001',
                'confidence': 0.92,
                'similar_errors': [...],
                'known_fixes': [
                    {
                        'fix_description': 'Call curses.initscr() before cbreak()',
                        'success_rate': 0.85,
                        'applicable': True
                    }
                ],
                'recommendation': 'Apply known fix pattern'
            }
        """
        
    def recognize_fix_pattern(self, fix: Dict, result: str) -> Dict:
        """
        Recognize and learn from fix patterns.
        
        Returns:
            {
                'pattern_recognized': True,
                'pattern_type': 'wrapping|replacement|refactoring',
                'effectiveness': 'high|medium|low',
                'similar_fixes': [...],
                'lessons_learned': [...]
            }
        """
        
    def recognize_code_pattern(self, code: str) -> List[Dict]:
        """
        Recognize code patterns (design patterns, idioms, anti-patterns).
        
        Returns:
            [
                {
                    'pattern': 'singleton',
                    'location': 'line 50-75',
                    'confidence': 0.88,
                    'quality': 'good|acceptable|poor'
                }
            ]
        """
        
    def detect_anti_patterns(self) -> List[Dict]:
        """
        Detect anti-patterns in codebase.
        
        Returns:
            [
                {
                    'anti_pattern': 'god_object',
                    'file': 'handlers.py',
                    'class': 'ToolCallHandler',
                    'severity': 'high',
                    'recommendation': 'Split into smaller classes'
                }
            ]
        """
        
    def learn_from_history(self, history: List[Dict]) -> Dict:
        """
        Learn patterns from historical data.
        
        Returns:
            {
                'patterns_learned': 15,
                'patterns_updated': 8,
                'new_insights': [...]
            }
        """
        
    def suggest_pattern_application(self, context: Dict) -> List[Dict]:
        """Suggest applicable patterns for current context."""
```

#### Tool Definition

```python
TOOL_RECOGNIZE_PATTERNS = {
    "type": "function",
    "function": {
        "name": "recognize_patterns",
        "description": "Recognize patterns in code, errors, and fixes. Use this to learn from history and apply proven solutions.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern_type": {
                    "type": "string",
                    "enum": ["error", "fix", "code", "anti_pattern", "all"],
                    "description": "Type of pattern to recognize"
                },
                "context": {
                    "type": "object",
                    "description": "Context for pattern recognition (error, code, fix, etc.)"
                },
                "learn": {
                    "type": "boolean",
                    "description": "Whether to learn from this pattern"
                }
            },
            "required": ["pattern_type"]
        }
    }
}
```

### Testing Requirements
- Test with known patterns
- Validate pattern matching accuracy
- Test learning capabilities
- Benchmark recognition performance

---

## Component 6: Patch File Manager

### Purpose
Organize, search, and manage patch files systematically.

### Capabilities
- **Patch Organization**: Organize patches by file, date, type
- **Patch Search**: Search patches by content, file, author
- **Patch Application**: Apply patches selectively
- **Patch Rollback**: Rollback patches safely
- **Patch Analysis**: Analyze patch effectiveness
- **Patch Recommendations**: Recommend relevant patches

### Implementation Details

#### File: `pipeline/analysis/patch_manager.py`

```python
class EnhancedPatchManager:
    """Enhanced patch file management with search and analysis."""
    
    def __init__(self, patches_dir: Path):
        self.patches_dir = patches_dir
        self.patch_index = {}
        self.patch_metadata = {}
        
    def index_patches(self) -> Dict:
        """
        Build searchable index of all patches.
        
        Returns:
            {
                'total_patches': 150,
                'by_file': {'pipeline_ui.py': 25, ...},
                'by_date': {'2024-12': 50, ...},
                'by_type': {'fix': 100, 'feature': 30, ...}
            }
        """
        
    def search_patches(self, query: Dict) -> List[Dict]:
        """
        Search patches by various criteria.
        
        Args:
            query: {
                'file': 'pipeline_ui.py',
                'date_range': ('2024-12-01', '2024-12-25'),
                'content': 'curses',
                'type': 'fix',
                'author': 'AI'
            }
            
        Returns:
            [
                {
                    'patch_file': 'change_0017_20241225_014345_pipeline_ui.patch',
                    'file': 'pipeline_ui.py',
                    'date': '2024-12-25',
                    'type': 'fix',
                    'lines_added': 10,
                    'lines_removed': 5,
                    'summary': 'Fixed curses initialization',
                    'success': True
                }
            ]
        """
        
    def analyze_patch_effectiveness(self, patch_file: str) -> Dict:
        """
        Analyze effectiveness of a patch.
        
        Returns:
            {
                'patch': 'change_0017_...',
                'applied': True,
                'success': True,
                'impact': 'high|medium|low',
                'side_effects': [],
                'reverted': False,
                'similar_patches': [...]
            }
        """
        
    def recommend_patches(self, context: Dict) -> List[Dict]:
        """
        Recommend relevant patches for current context.
        
        Returns:
            [
                {
                    'patch': 'change_0015_...',
                    'relevance': 0.92,
                    'reason': 'Similar error pattern',
                    'applicable': True
                }
            ]
        """
        
    def apply_patch(self, patch_file: str, dry_run: bool = True) -> Dict:
        """Apply a patch with optional dry-run."""
        
    def rollback_patch(self, patch_file: str) -> Dict:
        """Rollback a previously applied patch."""
        
    def get_patch_history(self, filepath: str) -> List[Dict]:
        """Get complete patch history for a file."""
```

#### Tool Definition

```python
TOOL_MANAGE_PATCHES = {
    "type": "function",
    "function": {
        "name": "manage_patches",
        "description": "Search, analyze, and manage patch files. Use this to find relevant patches and learn from previous fixes.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["search", "analyze", "recommend", "apply", "rollback", "history"],
                    "description": "Patch management operation"
                },
                "query": {
                    "type": "object",
                    "description": "Search query or operation parameters"
                },
                "patch_file": {
                    "type": "string",
                    "description": "Specific patch file (for analyze, apply, rollback)"
                }
            },
            "required": ["operation"]
        }
    }
}
```

### Testing Requirements
- Test with large patch collections (1000+ patches)
- Validate search accuracy
- Test patch application and rollback
- Benchmark indexing performance

---

## Component 7: Dependency Graph Builder

### Purpose
Build and maintain comprehensive dependency graphs for the project.

### Capabilities
- **Import Dependency Graph**: Track import relationships
- **Call Dependency Graph**: Track function call relationships
- **Data Dependency Graph**: Track data flow dependencies
- **Module Dependency Graph**: Track module-level dependencies
- **Dependency Analysis**: Analyze dependency health
- **Dependency Visualization**: Generate visual representations

### Implementation Details

#### File: `pipeline/analysis/dependency_graph.py`

```python
class DependencyGraphBuilder:
    """Builds and analyzes dependency graphs."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.import_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.data_graph = nx.DiGraph()
        
    def build_import_graph(self) -> nx.DiGraph:
        """
        Build import dependency graph.
        
        Returns:
            NetworkX directed graph where:
            - Nodes are modules
            - Edges represent imports
            - Edge attributes include import type (absolute/relative)
        """
        
    def build_call_graph(self) -> nx.DiGraph:
        """Build function call dependency graph."""
        
    def build_data_graph(self) -> nx.DiGraph:
        """Build data flow dependency graph."""
        
    def analyze_dependencies(self) -> Dict:
        """
        Comprehensive dependency analysis.
        
        Returns:
            {
                'total_dependencies': 150,
                'circular_dependencies': [...],
                'dependency_depth': {
                    'max': 8,
                    'avg': 3.5,
                    'modules': {'pipeline': 5, ...}
                },
                'coupling': {
                    'high': ['handlers.py', 'client.py'],
                    'medium': [...],
                    'low': [...]
                },
                'cohesion': {
                    'pipeline': 0.85,
                    'phases': 0.92,
                    ...
                },
                'health_score': 0.78
            }
        """
        
    def find_dependency_path(self, source: str, target: str) -> List[List[str]]:
        """Find all dependency paths between two modules."""
        
    def identify_dependency_issues(self) -> List[Dict]:
        """
        Identify dependency-related issues.
        
        Returns:
            [
                {
                    'issue': 'circular_dependency',
                    'modules': ['a', 'b', 'c', 'a'],
                    'severity': 'high',
                    'recommendation': 'Break cycle by introducing interface'
                }
            ]
        """
        
    def suggest_refactoring(self) -> List[Dict]:
        """Suggest refactoring to improve dependency structure."""
        
    def visualize_graph(self, graph_type: str, output_file: str) -> str:
        """Generate visual representation of dependency graph."""
```

#### Tool Definition

```python
TOOL_ANALYZE_DEPENDENCIES = {
    "type": "function",
    "function": {
        "name": "analyze_dependencies",
        "description": "Analyze project dependencies and relationships. Use this to understand coupling, cohesion, and dependency health.",
        "parameters": {
            "type": "object",
            "properties": {
                "graph_type": {
                    "type": "string",
                    "enum": ["import", "call", "data", "all"],
                    "description": "Type of dependency graph to analyze"
                },
                "operation": {
                    "type": "string",
                    "enum": ["build", "analyze", "find_path", "identify_issues", "suggest_refactoring"],
                    "description": "Dependency analysis operation"
                },
                "source": {
                    "type": "string",
                    "description": "Source module (for find_path)"
                },
                "target": {
                    "type": "string",
                    "description": "Target module (for find_path)"
                }
            },
            "required": ["operation"]
        }
    }
}
```

### Testing Requirements
- Test with complex dependency structures
- Validate circular dependency detection
- Test path finding algorithms
- Benchmark graph building performance

---

## Integration Strategy

### Phase 1A: Core Implementation (Week 1)
1. Implement FileStructureAnalyzer
2. Implement SchemaInspector
3. Implement CallFlowTracer
4. Create tool definitions
5. Add to tools.py

### Phase 1B: Loop Detection (Week 2)
1. Implement LoopDetector (CRITICAL)
2. Implement PatternRecognizer
3. Integrate with debugging phase
4. Integrate with conversation threads
5. Add monitoring and alerts

### Phase 1C: Management Tools (Week 3)
1. Implement EnhancedPatchManager
2. Implement DependencyGraphBuilder
3. Create comprehensive tests
4. Integration testing
5. Documentation

---

## Testing Strategy

### Unit Tests
- Test each component independently
- Mock external dependencies
- Achieve 90%+ code coverage

### Integration Tests
- Test tool integration with phases
- Test cross-component interactions
- Test with real project data

### Performance Tests
- Benchmark each component
- Test with large projects (1000+ files)
- Optimize bottlenecks

### Validation Tests
- Validate accuracy of analysis
- Test with known patterns
- Compare with manual analysis

---

## Success Criteria

### Functional Requirements
- ✅ All 7 components implemented and tested
- ✅ All tools integrated into pipeline
- ✅ Loop detection working with 95%+ accuracy
- ✅ Pattern recognition identifying known patterns
- ✅ Dependency analysis complete and accurate

### Performance Requirements
- ✅ File structure analysis: < 5 seconds for 1000 files
- ✅ Schema inspection: < 10 seconds for full project
- ✅ Call flow tracing: < 15 seconds for complete graph
- ✅ Loop detection: < 1 second per check
- ✅ Pattern recognition: < 2 seconds per pattern

### Quality Requirements
- ✅ 90%+ code coverage
- ✅ All tests passing
- ✅ Documentation complete
- ✅ No critical bugs

---

## Deliverables

### Code Deliverables
1. `pipeline/analysis/file_structure.py`
2. `pipeline/analysis/schema_inspector.py`
3. `pipeline/analysis/call_flow_tracer.py`
4. `pipeline/analysis/loop_detector.py`
5. `pipeline/analysis/pattern_recognizer.py`
6. `pipeline/analysis/patch_manager.py`
7. `pipeline/analysis/dependency_graph.py`
8. Updated `pipeline/tools.py` with new tool definitions
9. Updated `pipeline/handlers.py` with new tool handlers
10. Comprehensive test suite

### Documentation Deliverables
1. API documentation for all components
2. Usage examples and tutorials
3. Integration guide
4. Performance benchmarks
5. Troubleshooting guide

---

## Dependencies

### Python Packages
- `networkx` - Graph analysis
- `ast` - Python AST parsing (built-in)
- `pathlib` - File system operations (built-in)
- `difflib` - Patch analysis (built-in)
- `scikit-learn` - Pattern learning (optional)
- `graphviz` - Graph visualization (optional)

### System Requirements
- Python 3.9+
- 4GB+ RAM for large projects
- Disk space for patch storage

---

## Risk Mitigation

### Risk 1: Performance on Large Projects
**Mitigation:**
- Implement caching
- Use incremental analysis
- Optimize graph algorithms
- Add progress indicators

### Risk 2: False Positives in Loop Detection
**Mitigation:**
- Tune detection thresholds
- Implement confidence scores
- Allow manual override
- Continuous learning

### Risk 3: Integration Complexity
**Mitigation:**
- Phased integration
- Comprehensive testing
- Fallback mechanisms
- Clear documentation

---

## Next Phase

Upon completion of Phase 1, proceed to:
**[PHASE_2_ARCHITECTURE.md](PHASE_2_ARCHITECTURE.md)** - Multi-Agent Architecture Enhancement

---

**Phase Owner:** Development Team  
**Reviewers:** Technical Lead, AI/ML Engineer  
**Approval Required:** Yes  
**Estimated Effort:** 2-3 weeks (1 developer full-time)
</file_path>