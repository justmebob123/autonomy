# Detailed Implementation Plan: Application Troubleshooting Phase

## Overview

Based on deep system analysis, we have **62% of required infrastructure** already built. This plan focuses on implementing the **38% missing** (13 new tools) and integrating them into the existing hyper-dimensional phase polytope.

## Phase 1: Foundation & Core Tools (Days 1-3)

### Day 1: Phase Structure & Log Analysis

#### Task 1.1: Create ApplicationTroubleshootingPhase
**File:** `pipeline/phases/application_troubleshooting.py` (NEW)
**Lines:** ~400

```python
"""
Application Troubleshooting Phase

Performs deep application-layer analysis including:
- Log parsing and error pattern recognition
- Call chain tracing through multiple files
- Patch history correlation
- Architecture validation against MASTER_PLAN.md
"""

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from typing import Dict, List, Optional
import logging

class ApplicationTroubleshootingPhase(BasePhase, LoopDetectionMixin):
    """
    Deep application troubleshooting phase.
    
    Triggered by INVESTIGATION phase when application-layer errors detected.
    Returns findings to DEBUGGING phase for fix implementation.
    """
    
    def __init__(self, config, client):
        super().__init__(config, client)
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers (reuse existing + new)
        from ..log_analyzer import LogAnalyzer
        from ..patch_analyzer import PatchAnalyzer
        from ..call_graph_builder import CallGraphBuilder
        from ..architecture_analyzer import ArchitectureAnalyzer
        
        self.log_analyzer = LogAnalyzer(config.project_dir)
        self.patch_analyzer = PatchAnalyzer(config.project_dir)
        self.call_graph = CallGraphBuilder(config.project_dir)
        self.arch_analyzer = ArchitectureAnalyzer(config.project_dir)
    
    def execute(self, context: Dict) -> PhaseResult:
        """
        Execute application troubleshooting workflow.
        
        Workflow:
        1. Parse logs for custom errors
        2. Build call chain from error location
        3. Check patch history for related changes
        4. Validate against MASTER_PLAN.md architecture
        5. Synthesize findings and recommend fix
        """
        # Implementation here
        pass
```

**Integration Point 1:** Add to `pipeline/coordinator.py`
```python
# Line ~70 in _init_phases()
from .phases.application_troubleshooting import ApplicationTroubleshootingPhase

return {
    # ... existing phases ...
    "application_troubleshooting": ApplicationTroubleshootingPhase(self.config, self.client),
}
```

**Integration Point 2:** Add transition in `pipeline/coordinator.py`
```python
# Line ~250 in _determine_next_action()
# After INVESTIGATION phase check:
if investigation_found_application_error:
    return {
        "phase": "application_troubleshooting",
        "task": task,
        "reason": "deep_application_analysis"
    }
```

#### Task 1.2: Create LogAnalyzer Module
**File:** `pipeline/log_analyzer.py` (NEW)
**Lines:** ~300

```python
"""
Log Analysis Module

Parses custom application logs and extracts structured error information.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class LogEntry:
    """Structured log entry"""
    def __init__(self, timestamp, level, module, message):
        self.timestamp = timestamp
        self.level = level
        self.module = module
        self.message = message

class LogAnalyzer:
    """Analyzes application logs for errors and patterns"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def parse_application_log(self, log_file: str, format_pattern: str = None) -> List[LogEntry]:
        """
        Parse custom log format into structured entries.
        
        Default pattern matches Python logging format:
        YYYY-MM-DD HH:MM:SS,mmm - module - LEVEL - message
        """
        # Implementation
        pass
    
    def extract_error_patterns(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """
        Group errors by pattern and frequency.
        
        Returns:
            Dict mapping error pattern to list of occurrences
        """
        # Implementation
        pass
    
    def trace_log_timeline(self, entries: List[LogEntry], start: datetime, end: datetime) -> List[LogEntry]:
        """Build chronological timeline of events"""
        # Implementation
        pass
    
    def correlate_log_errors(self, primary_error: LogEntry, all_entries: List[LogEntry]) -> List[LogEntry]:
        """Find cascading/related errors"""
        # Implementation
        pass
    
    def analyze_log_context(self, error_entry: LogEntry, all_entries: List[LogEntry], context_size: int = 10) -> List[LogEntry]:
        """Get surrounding log entries for context"""
        # Implementation
        pass
```

#### Task 1.3: Add Log Analysis Tools
**File:** `pipeline/tools.py` (MODIFY)
**Location:** After line 940 (end of file)
**Lines to add:** ~150

```python
# =============================================================================
# Application Troubleshooting Tools
# =============================================================================

TOOLS_APPLICATION_TROUBLESHOOTING = [
    {
        "type": "function",
        "function": {
            "name": "parse_application_log",
            "description": "Parse custom application log file into structured entries",
            "parameters": {
                "type": "object",
                "required": ["log_file"],
                "properties": {
                    "log_file": {
                        "type": "string",
                        "description": "Path to log file relative to project root"
                    },
                    "format_pattern": {
                        "type": "string",
                        "description": "Optional regex pattern for custom log format"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_error_patterns",
            "description": "Find and group error patterns in log entries",
            "parameters": {
                "type": "object",
                "required": ["log_file"],
                "properties": {
                    "log_file": {
                        "type": "string",
                        "description": "Path to log file"
                    },
                    "error_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to identify errors (default: ['error', 'exception', 'failed'])"
                    }
                }
            }
        }
    },
    # ... 3 more log analysis tools
]
```

**Integration Point 3:** Update `get_tools_for_phase()`
```python
# Line ~900 in tools.py
def get_tools_for_phase(phase: str, tool_registry=None) -> List[Dict]:
    # ... existing code ...
    elif phase == "application_troubleshooting":
        return TOOLS_APPLICATION_TROUBLESHOOTING
```

#### Task 1.4: Add Log Analysis Handlers
**File:** `pipeline/handlers.py` (MODIFY)
**Location:** After line 1473 (end of file)
**Lines to add:** ~200

```python
    def _handle_parse_application_log(self, args: Dict) -> Dict:
        """Parse application log file"""
        log_file = args.get('log_file')
        format_pattern = args.get('format_pattern')
        
        try:
            from .log_analyzer import LogAnalyzer
            analyzer = LogAnalyzer(self.project_dir)
            entries = analyzer.parse_application_log(log_file, format_pattern)
            
            return {
                'success': True,
                'entries': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'level': e.level,
                        'module': e.module,
                        'message': e.message
                    }
                    for e in entries
                ],
                'count': len(entries)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ... 4 more log analysis handlers
```

**Integration Point 4:** Register handlers in `__init__`
```python
# Line ~50 in handlers.py __init__()
self._handlers.update({
    # Log Analysis
    "parse_application_log": self._handle_parse_application_log,
    "extract_error_patterns": self._handle_extract_error_patterns,
    "trace_log_timeline": self._handle_trace_log_timeline,
    "correlate_log_errors": self._handle_correlate_log_errors,
    "analyze_log_context": self._handle_analyze_log_context,
})
```

### Day 2: Patch Analysis & Call Chain Tools

#### Task 2.1: Create PatchAnalyzer Module
**File:** `pipeline/patch_analyzer.py` (NEW)
**Lines:** ~250

```python
"""
Patch Analysis Module

Extends PatchManager with analysis capabilities for correlating
patches with errors and suggesting rollbacks.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .patch_manager import PatchManager

class PatchAnalyzer:
    """Analyzes patch history to correlate with errors"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.patch_manager = PatchManager(self.project_root / '.patches')
    
    def list_patch_files(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Dict]:
        """
        List patches with metadata.
        
        Returns:
            List of dicts with: filename, timestamp, file_modified, change_number
        """
        # Implementation
        pass
    
    def analyze_patch_file(self, patch_file: str) -> Dict:
        """
        Parse patch file and extract changes.
        
        Returns:
            Dict with: files_changed, lines_added, lines_removed, context
        """
        # Implementation
        pass
    
    def correlate_patch_to_error(self, error_location: str, error_message: str, patches: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Match patches to error with confidence scores.
        
        Returns:
            List of (patch, confidence) tuples sorted by confidence
        """
        # Implementation
        pass
    
    def suggest_rollback(self, error_info: Dict, patches: List[Dict]) -> List[Dict]:
        """
        Recommend patches to revert with reasoning.
        
        Returns:
            List of dicts with: patch, reason, confidence, impact
        """
        # Implementation
        pass
```

#### Task 2.2: Create CallGraphBuilder Module
**File:** `pipeline/call_graph_builder.py` (NEW)
**Lines:** ~350

```python
"""
Call Graph Builder

Uses AST analysis to build complete call graphs and trace
execution paths through the codebase.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

class CallGraphNode:
    """Node in call graph"""
    def __init__(self, module: str, function: str, class_name: Optional[str] = None):
        self.module = module
        self.function = function
        self.class_name = class_name
        self.callers = []
        self.callees = []

class CallGraphBuilder:
    """Builds call graphs using AST analysis"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.graph = {}
    
    def build_call_graph(self, starting_file: str, starting_function: str) -> Dict:
        """
        Build complete call graph from starting point.
        
        Uses AST to traverse:
        1. Function calls within file
        2. Imported functions from other files
        3. Class method calls
        4. Recursive calls
        
        Returns:
            Dict representing call graph with nodes and edges
        """
        # Implementation using ast.NodeVisitor
        pass
    
    def trace_import_chain(self, starting_module: str) -> Dict:
        """
        Follow import dependencies.
        
        Returns:
            Tree of imports with depth and circular dependency detection
        """
        # Implementation
        pass
    
    def find_function_callers(self, function_name: str, class_name: Optional[str] = None) -> List[Dict]:
        """
        Find all locations that call a function.
        
        Returns:
            List of call sites with file, line, context
        """
        # Implementation
        pass
```

#### Task 2.3: Add Patch & Call Chain Tools
**File:** `pipeline/tools.py` (MODIFY)
**Location:** Append to TOOLS_APPLICATION_TROUBLESHOOTING
**Lines to add:** ~200

```python
    # Patch Analysis Tools
    {
        "type": "function",
        "function": {
            "name": "list_patch_files",
            "description": "List patch files with metadata from .patches/ directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)"
                    }
                }
            }
        }
    },
    # ... 2 more patch tools
    
    # Call Chain Tools
    {
        "type": "function",
        "function": {
            "name": "build_call_graph",
            "description": "Build complete call graph from starting function",
            "parameters": {
                "type": "object",
                "required": ["starting_file", "starting_function"],
                "properties": {
                    "starting_file": {
                        "type": "string",
                        "description": "File containing starting function"
                    },
                    "starting_function": {
                        "type": "string",
                        "description": "Function to start tracing from"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to traverse (default: 10)"
                    }
                }
            }
        }
    },
    # ... 2 more call chain tools
]
```

#### Task 2.4: Add Patch & Call Chain Handlers
**File:** `pipeline/handlers.py` (MODIFY)
**Lines to add:** ~300

```python
    # Patch Analysis Handlers
    def _handle_list_patch_files(self, args: Dict) -> Dict:
        """List patch files with metadata"""
        # Implementation
        pass
    
    def _handle_analyze_patch_file(self, args: Dict) -> Dict:
        """Analyze specific patch file"""
        # Implementation
        pass
    
    def _handle_correlate_patch_to_error(self, args: Dict) -> Dict:
        """Correlate patches with error"""
        # Implementation
        pass
    
    # Call Chain Handlers
    def _handle_build_call_graph(self, args: Dict) -> Dict:
        """Build call graph"""
        # Implementation
        pass
    
    def _handle_trace_import_chain(self, args: Dict) -> Dict:
        """Trace import dependencies"""
        # Implementation
        pass
    
    def _handle_find_function_callers(self, args: Dict) -> Dict:
        """Find function call sites"""
        # Implementation
        pass
```

### Day 3: Architecture Analysis & Integration

#### Task 3.1: Create ArchitectureAnalyzer Module
**File:** `pipeline/architecture_analyzer.py` (NEW)
**Lines:** ~300

```python
"""
Architecture Analyzer

Parses MASTER_PLAN.md and compares actual implementation
against intended architecture.
"""

from pathlib import Path
from typing import Dict, List, Optional
import re

class ArchitectureAnalyzer:
    """Analyzes architecture against MASTER_PLAN.md"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.master_plan_path = self.project_root / 'pipeline_docs' / 'MASTER_PLAN.md'
    
    def parse_master_plan(self) -> Dict:
        """
        Extract architecture from MASTER_PLAN.md.
        
        Parses:
        - Component definitions
        - Relationships
        - Data flow
        - Configuration requirements
        
        Returns:
            Dict with components, relationships, requirements
        """
        # Implementation
        pass
    
    def compare_architecture(self, actual_structure: Dict) -> Dict:
        """
        Compare actual vs. intended architecture.
        
        Returns:
            Dict with: matches, deviations, violations, missing_components
        """
        # Implementation
        pass
    
    def suggest_architectural_fix(self, error_info: Dict, architecture: Dict) -> Dict:
        """
        Recommend fix aligned with architecture.
        
        Returns:
            Dict with: recommended_fix, reasoning, architectural_alignment
        """
        # Implementation
        pass
```

#### Task 3.2: Add Architecture Tools & Handlers
**File:** `pipeline/tools.py` (MODIFY)
**Lines to add:** ~100

**File:** `pipeline/handlers.py` (MODIFY)
**Lines to add:** ~150

#### Task 3.3: Complete Phase Integration
**File:** `pipeline/phases/application_troubleshooting.py` (MODIFY)
**Complete the execute() method with full workflow**

#### Task 3.4: Update Investigation Phase Trigger
**File:** `pipeline/phases/investigation.py` (MODIFY)
**Add detection for application-layer errors:**

```python
# Line ~150 in execute()
def _is_application_layer_error(self, findings: Dict) -> bool:
    """
    Detect if error is application-layer (not code syntax/logic).
    
    Application-layer indicators:
    - Configuration errors
    - "No available servers"
    - Missing resources
    - Architectural violations
    """
    error_message = findings.get('error_message', '').lower()
    
    application_patterns = [
        'no available servers',
        'configuration',
        'not configured',
        'missing url',
        '0 models at none',
        'server not found',
    ]
    
    return any(pattern in error_message for pattern in application_patterns)

# At end of execute():
if self._is_application_layer_error(findings):
    return PhaseResult(
        success=True,
        next_phase="application_troubleshooting",
        data=findings,
        message="Application-layer error detected, triggering deep troubleshooting"
    )
```

## Phase 2: Testing & Optimization (Days 4-5)

### Day 4: Integration Testing

#### Test 1: Server Configuration Error (Real Example)
**Test Case:** Reproduce the actual error from user's logs
```python
# test_application_troubleshooting.py
def test_server_configuration_error():
    """Test with real server configuration error"""
    # Setup: Create project with broken config
    # Execute: Run APPLICATION_TROUBLESHOOTING phase
    # Verify: Detects missing server URLs
    # Verify: Traces to config loading code
    # Verify: Suggests creating servers.yaml
    pass
```

#### Test 2: End-to-End Workflow
```python
def test_full_workflow():
    """Test complete workflow from error to fix"""
    # INVESTIGATION → APP_TROUBLESHOOTING → DEBUGGING
    pass
```

#### Test 3: Tool Integration
```python
def test_all_tools():
    """Test each tool individually"""
    # Test all 13 new tools
    pass
```

### Day 5: Performance Optimization

#### Optimization 1: Caching
- Cache parsed logs
- Cache call graphs
- Cache patch analysis

#### Optimization 2: Parallel Execution
- Parse logs in parallel
- Build call graphs concurrently
- Analyze patches in parallel

#### Optimization 3: Resource Limits
- Limit log file size
- Limit call graph depth
- Timeout long operations

## Phase 3: Documentation & Deployment (Days 6-7)

### Day 6: Documentation

#### Doc 1: User Guide
**File:** `APPLICATION_TROUBLESHOOTING_USER_GUIDE.md`

#### Doc 2: API Documentation
**File:** `APPLICATION_TROUBLESHOOTING_API.md`

#### Doc 3: Integration Guide
**File:** `APPLICATION_TROUBLESHOOTING_INTEGRATION.md`

### Day 7: Final Integration & Testing

#### Final Test 1: Solve Server Configuration Error
- Run on actual user project
- Verify automatic detection
- Verify correct diagnosis
- Verify fix suggestion

#### Final Test 2: Performance Benchmarks
- Measure phase execution time
- Measure tool execution time
- Verify resource usage

#### Final Test 3: Edge Cases
- Empty logs
- Malformed patches
- Missing MASTER_PLAN.md
- Circular dependencies

## File Summary

### New Files (7)
1. `pipeline/phases/application_troubleshooting.py` (~400 lines)
2. `pipeline/log_analyzer.py` (~300 lines)
3. `pipeline/patch_analyzer.py` (~250 lines)
4. `pipeline/call_graph_builder.py` (~350 lines)
5. `pipeline/architecture_analyzer.py` (~300 lines)
6. `tests/test_application_troubleshooting.py` (~500 lines)
7. `APPLICATION_TROUBLESHOOTING_USER_GUIDE.md` (~200 lines)

**Total New Code:** ~2,300 lines

### Modified Files (5)
1. `pipeline/coordinator.py` (+20 lines)
2. `pipeline/tools.py` (+450 lines)
3. `pipeline/handlers.py` (+650 lines)
4. `pipeline/phases/investigation.py` (+30 lines)
5. `pipeline/phases/__init__.py` (+2 lines)

**Total Modified:** +1,152 lines

### Grand Total
**New + Modified:** ~3,452 lines of production code
**Tests:** ~500 lines
**Documentation:** ~200 lines
**Total Project:** ~4,152 lines

## Integration Checklist

- [ ] ApplicationTroubleshootingPhase created
- [ ] LogAnalyzer module implemented
- [ ] PatchAnalyzer module implemented
- [ ] CallGraphBuilder module implemented
- [ ] ArchitectureAnalyzer module implemented
- [ ] 13 new tools defined in tools.py
- [ ] 13 new handlers implemented in handlers.py
- [ ] Phase registered in coordinator
- [ ] Transition added from INVESTIGATION
- [ ] Investigation phase updated with trigger
- [ ] All tools tested individually
- [ ] End-to-end workflow tested
- [ ] Performance optimized
- [ ] Documentation complete
- [ ] Server configuration error solved

## Success Criteria

### Functional
- [ ] Can parse custom application logs
- [ ] Can build complete call graphs
- [ ] Can analyze patch history
- [ ] Can validate against MASTER_PLAN.md
- [ ] Can solve server configuration error automatically

### Performance
- [ ] Phase completes in < 15 minutes
- [ ] Tools execute in < 30 seconds each
- [ ] Memory usage < 500MB
- [ ] No resource leaks

### Integration
- [ ] Seamlessly integrates with existing phases
- [ ] No breaking changes to existing code
- [ ] Maintains system architecture
- [ ] Follows coding standards

## Timeline

**Total:** 7 days (1 week)
- Days 1-3: Implementation (60%)
- Days 4-5: Testing & Optimization (30%)
- Days 6-7: Documentation & Deployment (10%)

**Aggressive but achievable with focused effort.**

This is a **surgical addition** to an already sophisticated system, not a major rewrite.