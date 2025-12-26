# Complete Tool Specifications: Application Troubleshooting

## Overview

This document provides complete specifications for all 13 new tools required for the Application Troubleshooting Phase, including exact function signatures, parameters, return types, and implementation algorithms.

## Log Analysis Tools (5 Tools)

### 1. parse_application_log

**Purpose:** Parse custom application log formats into structured entries

**Signature:**
```python
def parse_application_log(
    log_file: str,
    format_pattern: Optional[str] = None,
    max_entries: int = 10000
) -> List[LogEntry]
```

**Parameters:**
- `log_file` (required): Path to log file relative to project root
- `format_pattern` (optional): Regex pattern for custom format
- `max_entries` (optional): Maximum entries to parse (default: 10000)

**Returns:**
```python
{
    'success': True,
    'entries': [
        {
            'timestamp': '2025-12-25T22:36:51.952',
            'level': 'INFO',
            'module': 'src.main',
            'message': 'System initialized successfully',
            'line_number': 42
        },
        # ... more entries
    ],
    'count': 1523,
    'format_detected': 'python_logging',
    'parse_errors': 0
}
```

**Default Format Pattern:**
```regex
^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^ ]+) - (\w+) - (.+)$
Groups: (timestamp, module, level, message)
```

**Algorithm:**
```
1. Read log file line by line
2. For each line:
   a. Try default pattern
   b. If fails, try custom pattern
   c. If fails, mark as unparsed
3. Create LogEntry objects
4. Return structured list
```

**Error Handling:**
- File not found → Return error
- Parse errors → Include in parse_errors count
- Malformed lines → Skip with warning

---

### 2. extract_error_patterns

**Purpose:** Find and group error patterns in logs

**Signature:**
```python
def extract_error_patterns(
    log_file: str,
    error_keywords: List[str] = ['error', 'exception', 'failed', 'critical'],
    min_frequency: int = 1
) -> Dict[str, List[LogEntry]]
```

**Parameters:**
- `log_file` (required): Path to log file
- `error_keywords` (optional): Keywords to identify errors
- `min_frequency` (optional): Minimum occurrences to include

**Returns:**
```python
{
    'success': True,
    'patterns': {
        'No available servers found': {
            'count': 42,
            'first_seen': '2025-12-25T22:36:52.175',
            'last_seen': '2025-12-25T22:38:15.234',
            'entries': [LogEntry, LogEntry, ...],
            'severity': 'ERROR',
            'modules': ['src.work_queue.server_selector', ...]
        },
        '0 models at None': {
            'count': 2,
            'first_seen': '2025-12-25T22:36:51.991',
            'last_seen': '2025-12-25T22:36:51.991',
            'entries': [LogEntry, LogEntry],
            'severity': 'INFO',
            'modules': ['src.execution.server_pool']
        }
    },
    'total_errors': 44,
    'unique_patterns': 2
}
```

**Algorithm:**
```
1. Parse log file
2. Filter entries by error keywords
3. Extract error message (normalize)
4. Group by normalized message
5. Calculate statistics per pattern
6. Sort by frequency
7. Return grouped patterns
```

---

### 3. trace_log_timeline

**Purpose:** Build chronological timeline of events

**Signature:**
```python
def trace_log_timeline(
    log_file: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_types: List[str] = ['ERROR', 'WARNING', 'INFO']
) -> List[LogEntry]
```

**Returns:**
```python
{
    'success': True,
    'timeline': [
        {
            'timestamp': '2025-12-25T22:36:51.952',
            'event': 'System initialization started',
            'type': 'INFO',
            'module': 'src.main'
        },
        {
            'timestamp': '2025-12-25T22:36:51.991',
            'event': 'Server pool initialized with 0 servers',
            'type': 'WARNING',
            'module': 'src.execution.server_pool'
        },
        {
            'timestamp': '2025-12-25T22:36:52.175',
            'event': 'No available servers found',
            'type': 'ERROR',
            'module': 'src.work_queue.server_selector'
        }
    ],
    'duration': '0.223 seconds',
    'event_count': 3
}
```

---

### 4. correlate_log_errors

**Purpose:** Find cascading and related errors

**Signature:**
```python
def correlate_log_errors(
    primary_error: str,
    log_file: str,
    time_window: int = 60
) -> Dict
```

**Parameters:**
- `primary_error`: The main error message to analyze
- `log_file`: Path to log file
- `time_window`: Seconds before/after to search (default: 60)

**Returns:**
```python
{
    'success': True,
    'primary_error': {
        'message': 'No available servers found',
        'timestamp': '2025-12-25T22:36:52.175',
        'module': 'src.work_queue.server_selector'
    },
    'related_errors': [
        {
            'message': '0 models at None',
            'timestamp': '2025-12-25T22:36:51.991',
            'module': 'src.execution.server_pool',
            'relationship': 'CAUSED_BY',
            'confidence': 0.95
        }
    ],
    'cascading_errors': [
        {
            'message': 'No available server for job bbb6fb9e',
            'timestamp': '2025-12-25T22:36:52.176',
            'module': 'src.work_queue.work_queue',
            'relationship': 'CAUSED',
            'confidence': 0.98
        }
    ],
    'root_cause_candidate': '0 models at None'
}
```

**Algorithm:**
```
1. Find primary error in log
2. Get timestamp
3. Search time_window before for potential causes
4. Search time_window after for cascading effects
5. Analyze module relationships
6. Calculate confidence scores
7. Identify root cause candidate
```

---

### 5. analyze_log_context

**Purpose:** Get context around error for understanding

**Signature:**
```python
def analyze_log_context(
    error_line: str,
    log_file: str,
    context_lines: int = 10
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'error_line': {
        'content': 'No available servers found',
        'line_number': 42,
        'timestamp': '2025-12-25T22:36:52.175'
    },
    'context_before': [
        # 10 lines before error
    ],
    'context_after': [
        # 10 lines after error
    ],
    'related_modules': ['server_pool', 'server_selector', 'work_queue'],
    'state_before_error': {
        'servers_initialized': True,
        'models_loaded': False,
        'urls_configured': False
    }
}
```

## Call Chain Tools (3 Tools)

### 6. build_call_graph

**Purpose:** Create complete call graph from starting function

**Signature:**
```python
def build_call_graph(
    starting_file: str,
    starting_function: str,
    max_depth: int = 10,
    include_imports: bool = True
) -> Dict
```

**Parameters:**
- `starting_file`: File containing starting function
- `starting_function`: Function to start tracing from
- `max_depth`: Maximum depth to traverse
- `include_imports`: Include imported functions

**Returns:**
```python
{
    'success': True,
    'graph': {
        'nodes': [
            {
                'id': 'src.main:main',
                'file': 'src/main.py',
                'function': 'main',
                'class': None,
                'line': 100
            },
            {
                'id': 'src.execution.job_executor:JobExecutor.__init__',
                'file': 'src/execution/job_executor.py',
                'function': '__init__',
                'class': 'JobExecutor',
                'line': 50
            },
            # ... more nodes
        ],
        'edges': [
            {
                'from': 'src.main:main',
                'to': 'src.execution.job_executor:JobExecutor.__init__',
                'call_site': 'src/main.py:120',
                'depth': 1
            },
            # ... more edges
        ]
    },
    'depth_reached': 8,
    'total_nodes': 47,
    'total_edges': 89,
    'circular_dependencies': []
}
```

**Algorithm:**
```
1. Parse starting file with AST
2. Find starting function
3. Extract all function calls
4. For each call:
   a. Resolve to actual function (handle imports)
   b. Add node to graph
   c. Add edge from caller to callee
   d. Recursively process callee (if depth < max_depth)
5. Detect circular dependencies
6. Return complete graph
```

**Implementation:**
```python
class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor for building call graphs"""
    
    def visit_Call(self, node):
        # Extract function name
        # Resolve to module
        # Add to graph
        pass
    
    def visit_Import(self, node):
        # Track imports
        pass
    
    def visit_ImportFrom(self, node):
        # Track from imports
        pass
```

---

### 7. trace_import_chain

**Purpose:** Follow import dependencies through codebase

**Signature:**
```python
def trace_import_chain(
    starting_module: str,
    max_depth: int = 10
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'import_tree': {
        'module': 'src.main',
        'file': 'src/main.py',
        'imports': [
            {
                'module': 'src.execution.job_executor',
                'file': 'src/execution/job_executor.py',
                'depth': 1,
                'imports': [
                    {
                        'module': 'src.execution.server_pool',
                        'file': 'src/execution/server_pool.py',
                        'depth': 2,
                        'imports': [...]
                    }
                ]
            }
        ]
    },
    'total_modules': 23,
    'max_depth_reached': 7,
    'circular_imports': []
}
```

---

### 8. find_function_callers

**Purpose:** Find all locations that call a specific function

**Signature:**
```python
def find_function_callers(
    function_name: str,
    class_name: Optional[str] = None,
    search_path: Optional[str] = None
) -> List[Dict]
```

**Returns:**
```python
{
    'success': True,
    'function': 'ServerPool.__init__',
    'callers': [
        {
            'file': 'src/main.py',
            'line': 120,
            'function': 'main',
            'context': 'self.server_pool = ServerPool(servers)',
            'call_type': 'direct'
        },
        {
            'file': 'src/execution/job_executor.py',
            'line': 85,
            'function': 'JobExecutor.__init__',
            'context': 'self.pool = ServerPool(config.servers)',
            'call_type': 'direct'
        }
    ],
    'total_callers': 2
}
```

**Algorithm:**
```
1. Search all Python files in project
2. Parse each file with AST
3. Find Call nodes matching function_name
4. If class_name provided, filter by class
5. Extract context (surrounding lines)
6. Return all call sites
```

## Patch Analysis Tools (3 Tools)

### 9. list_patch_files

**Purpose:** List patches from .patches/ directory with metadata

**Signature:**
```python
def list_patch_files(
    days_back: int = 7,
    file_filter: Optional[str] = None
) -> List[Dict]
```

**Returns:**
```python
{
    'success': True,
    'patches': [
        {
            'filename': 'change_0042_20241225_143022_server_pool_line85.patch',
            'change_number': 42,
            'timestamp': '2025-12-25T14:30:22',
            'file_modified': 'src/execution/server_pool.py',
            'line_modified': 85,
            'age_hours': 8.5,
            'size_bytes': 1234
        },
        # ... more patches
    ],
    'total_patches': 15,
    'date_range': '2025-12-18 to 2025-12-25'
}
```

**Algorithm:**
```
1. List files in .patches/ directory
2. Parse filename for metadata:
   - change_NNNN_YYYYMMDD_HHMMSS_filename_lineNN.patch
3. Calculate age from timestamp
4. Filter by days_back
5. Filter by file_filter if provided
6. Sort by timestamp (newest first)
7. Return list with metadata
```

---

### 10. analyze_patch_file

**Purpose:** Parse patch file and extract detailed changes

**Signature:**
```python
def analyze_patch_file(
    patch_file: str
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'patch_file': 'change_0042_20241225_143022_server_pool_line85.patch',
    'files_changed': ['src/execution/server_pool.py'],
    'changes': [
        {
            'file': 'src/execution/server_pool.py',
            'line_number': 85,
            'old_code': '        self.servers = servers',
            'new_code': '        self.servers = servers or []',
            'context_before': [
                '    def __init__(self, servers):',
                '        """Initialize server pool"""',
            ],
            'context_after': [
                '        self.logger = logging.getLogger(__name__)',
            ]
        }
    ],
    'lines_added': 1,
    'lines_removed': 1,
    'lines_changed': 1,
    'change_type': 'modification',
    'impact': 'low'
}
```

**Algorithm:**
```
1. Read patch file
2. Parse unified diff format:
   - Extract file paths
   - Extract line numbers
   - Extract old/new code
   - Extract context
3. Classify change type:
   - addition (+ lines only)
   - deletion (- lines only)
   - modification (both)
4. Estimate impact:
   - low: 1-5 lines
   - medium: 6-20 lines
   - high: 21+ lines
5. Return structured analysis
```

---

### 11. correlate_patch_to_error

**Purpose:** Match patches to errors with confidence scores

**Signature:**
```python
def correlate_patch_to_error(
    error_location: str,
    error_message: str,
    days_back: int = 7
) -> List[Tuple[Dict, float]]
```

**Parameters:**
- `error_location`: File:line where error occurred
- `error_message`: The error message
- `days_back`: How far back to search patches

**Returns:**
```python
{
    'success': True,
    'error': {
        'location': 'src/execution/server_pool.py:85',
        'message': 'No available servers found'
    },
    'correlated_patches': [
        {
            'patch': {
                'filename': 'change_0042_20241225_143022_server_pool_line85.patch',
                'timestamp': '2025-12-25T14:30:22',
                'file': 'src/execution/server_pool.py',
                'line': 85
            },
            'confidence': 0.95,
            'reasons': [
                'Exact file match',
                'Exact line match',
                'Recent change (8 hours ago)',
                'Modified server initialization'
            ]
        },
        {
            'patch': {
                'filename': 'change_0038_20241225_120015_config_manager_line120.patch',
                'timestamp': '2025-12-25T12:00:15',
                'file': 'src/core/config_manager.py',
                'line': 120
            },
            'confidence': 0.72,
            'reasons': [
                'Related module (config)',
                'Modified server loading',
                'Recent change (10 hours ago)'
            ]
        }
    ],
    'total_candidates': 2,
    'recommendation': 'Review change_0042 first (95% confidence)'
}
```

**Confidence Scoring Algorithm:**
```
Base score: 0.0

+0.50 if exact file match
+0.30 if same directory
+0.10 if related module

+0.30 if exact line match
+0.20 if within 10 lines
+0.10 if within 50 lines

+0.20 if < 24 hours old
+0.10 if < 7 days old
+0.05 if < 30 days old

+0.10 if error keywords in patch
+0.05 if related keywords

Max score: 1.00
Threshold for relevance: 0.50
```

## Architecture Analysis Tools (3 Tools)

### 12. parse_master_plan

**Purpose:** Extract architecture from MASTER_PLAN.md

**Signature:**
```python
def parse_master_plan(
    master_plan_path: Optional[str] = None
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'architecture': {
        'components': [
            {
                'name': 'ServerPool',
                'purpose': 'Manage Ollama server connections',
                'location': 'src/execution/server_pool.py',
                'dependencies': ['ConfigManager'],
                'configuration': {
                    'source': 'servers.yaml or config.yaml',
                    'required_fields': ['name', 'url', 'models']
                }
            },
            # ... more components
        ],
        'relationships': [
            {
                'from': 'JobExecutor',
                'to': 'ServerPool',
                'type': 'uses',
                'description': 'JobExecutor uses ServerPool for model routing'
            }
        ],
        'data_flow': [
            {
                'source': 'config.yaml',
                'destination': 'ServerPool',
                'data': 'server definitions',
                'path': 'ConfigManager → JobExecutor → ServerPool'
            }
        ]
    },
    'version': '1.0',
    'last_updated': '2025-12-20'
}
```

**Parsing Strategy:**
```
1. Read MASTER_PLAN.md
2. Extract sections:
   - ## Components
   - ## Architecture
   - ## Data Flow
   - ## Configuration
3. Parse markdown structure
4. Extract component definitions
5. Parse relationships
6. Build architecture model
7. Return structured data
```

---

### 13. compare_architecture

**Purpose:** Compare actual implementation vs. intended architecture

**Signature:**
```python
def compare_architecture(
    actual_structure: Optional[Dict] = None
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'comparison': {
        'matches': [
            {
                'component': 'ServerPool',
                'status': 'IMPLEMENTED',
                'location': 'src/execution/server_pool.py',
                'compliance': 0.85
            }
        ],
        'deviations': [
            {
                'component': 'ServerPool',
                'issue': 'Configuration source',
                'expected': 'Load from servers.yaml with fallback to config.yaml',
                'actual': 'Only loads from config.yaml',
                'severity': 'HIGH',
                'impact': 'Servers not properly configured'
            }
        ],
        'violations': [
            {
                'rule': 'All servers must have URL',
                'violated_by': 'ServerPool initialization',
                'location': 'src/execution/server_pool.py:85',
                'severity': 'CRITICAL'
            }
        ],
        'missing_components': []
    },
    'overall_compliance': 0.78,
    'critical_issues': 1
}
```

---

### 14. suggest_architectural_fix

**Purpose:** Recommend fix aligned with architecture

**Signature:**
```python
def suggest_architectural_fix(
    error_info: Dict,
    architecture: Dict
) -> Dict
```

**Returns:**
```python
{
    'success': True,
    'error': 'No available servers found',
    'root_cause': 'ServerPool initialized with servers that have no URLs',
    'architectural_context': {
        'component': 'ServerPool',
        'intended_behavior': 'Load servers from servers.yaml with proper URLs',
        'actual_behavior': 'Servers loaded but URLs are None'
    },
    'recommended_fix': {
        'strategy': 'CREATE_MISSING_CONFIG',
        'description': 'Create servers.yaml with proper server definitions',
        'files_to_create': ['servers.yaml'],
        'files_to_modify': [],
        'template': '''
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
    models: [qwen2.5-coder:32b, phi4, ...]
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
    models: [qwen2.5-coder:32b, deepseek-coder-v2, ...]
        ''',
        'reasoning': [
            'MASTER_PLAN.md specifies servers.yaml as primary config source',
            'Code expects servers with URL and models fields',
            'Creating servers.yaml aligns with intended architecture'
        ],
        'confidence': 0.95
    },
    'alternative_fixes': [
        {
            'strategy': 'MODIFY_EXISTING_CONFIG',
            'description': 'Add server URLs to config.yaml',
            'confidence': 0.70
        }
    ]
}
```

## Tool Dependencies

### Reusable Components

**From existing codebase:**
- `read_file` (handlers.py) - Read any file
- `search_code` (handlers.py) - Search codebase
- `list_directory` (handlers.py) - List files
- `execute_command` (handlers.py) - Run shell commands
- `PatchManager` (patch_manager.py) - Patch operations
- `ContextInvestigator` (context_investigator.py) - Data flow analysis
- AST parsing (multiple files) - Code analysis

**New dependencies:**
- `LogAnalyzer` - Log parsing
- `PatchAnalyzer` - Patch analysis
- `CallGraphBuilder` - Call graph construction
- `ArchitectureAnalyzer` - MASTER_PLAN parsing

## Implementation Complexity

| Tool | Complexity | Lines | Dependencies | Reuse % |
|------|-----------|-------|--------------|---------|
| parse_application_log | Medium | 80 | None | 20% |
| extract_error_patterns | Medium | 60 | LogAnalyzer | 40% |
| trace_log_timeline | Low | 40 | LogAnalyzer | 60% |
| correlate_log_errors | High | 100 | LogAnalyzer | 30% |
| analyze_log_context | Low | 50 | LogAnalyzer | 50% |
| build_call_graph | Very High | 200 | ast | 10% |
| trace_import_chain | High | 120 | ast | 20% |
| find_function_callers | Medium | 80 | ast, search_code | 40% |
| list_patch_files | Low | 60 | PatchManager | 70% |
| analyze_patch_file | Medium | 80 | PatchManager | 60% |
| correlate_patch_to_error | High | 120 | PatchAnalyzer | 30% |
| parse_master_plan | Medium | 100 | None | 30% |
| compare_architecture | High | 150 | ArchitectureAnalyzer | 20% |
| suggest_architectural_fix | Very High | 180 | All analyzers | 40% |

**Total:** ~1,420 lines of tool implementation
**Average Reuse:** 37% (leveraging existing infrastructure)

## Testing Strategy

### Unit Tests (Per Tool)
```python
def test_parse_application_log():
    # Test with sample log
    # Verify parsing
    # Check edge cases
    pass

# ... 13 unit tests
```

### Integration Tests
```python
def test_log_to_patch_correlation():
    # Parse log
    # Find error
    # Correlate with patches
    # Verify results
    pass

def test_call_graph_to_architecture():
    # Build call graph
    # Parse MASTER_PLAN
    # Compare
    # Verify deviations detected
    pass
```

### End-to-End Test
```python
def test_server_configuration_error():
    """Test with real server configuration error"""
    # Setup: Broken config
    # Execute: Full troubleshooting workflow
    # Verify: Correct diagnosis
    # Verify: Correct fix suggested
    # Apply: Fix
    # Verify: Error resolved
    pass
```

## Performance Targets

| Tool | Target Time | Max Memory | Max Depth |
|------|-------------|------------|-----------|
| parse_application_log | < 5s | 100MB | N/A |
| extract_error_patterns | < 3s | 50MB | N/A |
| trace_log_timeline | < 2s | 50MB | N/A |
| correlate_log_errors | < 5s | 100MB | N/A |
| analyze_log_context | < 1s | 10MB | N/A |
| build_call_graph | < 30s | 200MB | 10 |
| trace_import_chain | < 15s | 100MB | 10 |
| find_function_callers | < 10s | 100MB | N/A |
| list_patch_files | < 1s | 10MB | N/A |
| analyze_patch_file | < 2s | 20MB | N/A |
| correlate_patch_to_error | < 5s | 50MB | N/A |
| parse_master_plan | < 3s | 20MB | N/A |
| compare_architecture | < 10s | 100MB | N/A |
| suggest_architectural_fix | < 5s | 50MB | N/A |

**Total Phase Time:** < 2 minutes for all tools

## Summary

This specification provides:
- ✅ Complete function signatures
- ✅ Detailed parameter descriptions
- ✅ Exact return formats
- ✅ Implementation algorithms
- ✅ Error handling strategies
- ✅ Performance targets
- ✅ Testing strategies
- ✅ Reuse percentages

**Ready for immediate implementation.**