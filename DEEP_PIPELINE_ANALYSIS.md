# Deep Pipeline Analysis & Scripts Integration Plan

## Executive Summary
This document provides a comprehensive analysis of the entire Autonomy AI pipeline, identifying integration points for scripts/ directory tools and addressing current issues.

## Current Issues Identified

### 1. Custom Tools Directory Problem
- **Issue**: Custom tools still using wrong directory path
- **Root Cause**: Looking in `/home/ai/AI/autonomy/scripts/custom_tools/tools` instead of entire `scripts/` directory
- **Impact**: Limited tool availability, missing valuable analysis tools

### 2. Objectives Expansion Problem
- **Issue**: Planning phase keeps returning same existing objectives
- **Root Cause**: No file update capability, only full file rewrite
- **Impact**: Cannot incrementally update MASTER_PLAN, PRIMARY_OBJECTIVES, etc.

### 3. QA Phase Misunderstanding
- **Issue**: QA finding problems treated as QA phase failure
- **Root Cause**: Confusion between QA process success and code quality issues
- **Impact**: Incorrect phase failure attribution

## Phase-by-Phase Analysis

### Phase 1: Planning Phase
**Location**: `pipeline/phases/planning.py`
**Current Tools**: create_task_plan, read_file, write_file
**Needed Integration**:
- `scripts/analyze_architecture.py` - Map project structure
- `scripts/analyze_dependencies.py` - Understand dependencies
- `scripts/create_dependency_graph.py` - Visualize relationships
- `scripts/find_entry_points.py` - Identify starting points

**Integration Points**:
1. Before creating task plan, analyze architecture
2. Use dependency graph to understand impact
3. Update MASTER_PLAN, PRIMARY_OBJECTIVES based on findings
4. Use entry points to plan execution order

### Phase 2: Coding Phase
**Location**: `pipeline/phases/coding.py`
**Current Tools**: create_file, read_file, write_file, str_replace
**Needed Integration**:
- `scripts/analyze_architecture.py` - Understand where to place code
- `scripts/analyze_dependencies.py` - Check what needs importing
- `scripts/find_entry_points.py` - Understand execution flow

**Integration Points**:
1. Before coding, analyze existing architecture
2. Check dependencies before adding imports
3. Verify placement aligns with architecture

### Phase 3: QA Phase
**Location**: `pipeline/phases/qa.py`
**Current Tools**: approve_code, report_issue, read_file
**Needed Integration**:
- `scripts/analyze_architecture.py` - Verify architectural consistency
- `scripts/analyze_dependencies.py` - Check dependency issues
- `scripts/create_dependency_graph.py` - Visualize impact
- `scripts/analyze_complexity.py` - Check code complexity

**Integration Points**:
1. Architectural consistency checks
2. Dependency validation
3. Complexity analysis
4. **CRITICAL**: QA finding issues means CODE has problems, not QA phase

### Phase 4: Debugging Phase
**Location**: `pipeline/phases/debugging.py`
**Current Tools**: read_file, write_file, str_replace, run_command
**Needed Integration**:
- `scripts/analyze_architecture.py` - Understand system structure
- `scripts/analyze_dependencies.py` - Find dependency issues
- `scripts/create_dependency_graph.py` - Trace issue propagation
- `scripts/find_entry_points.py` - Understand execution paths

**Integration Points**:
1. Architecture analysis for debugging context
2. Dependency tracing for root cause
3. Entry point analysis for execution flow
4. Complexity analysis for refactoring needs

### Phase 5: Project Planning Phase
**Location**: `pipeline/phases/project_planning.py`
**Current Tools**: read_file, write_file
**Needed Integration**:
- **ALL scripts/ tools** - This phase needs comprehensive analysis
- `scripts/analyze_architecture.py` - Map entire project
- `scripts/analyze_dependencies.py` - Understand relationships
- `scripts/create_dependency_graph.py` - Visualize structure
- `scripts/find_entry_points.py` - Identify key components

**Integration Points**:
1. **CRITICAL**: Must be able to UPDATE documents, not just rewrite
2. Use architecture analysis to update ARCHITECTURE.md
3. Use dependency analysis to update MASTER_PLAN.md
4. Use complexity analysis to update SECONDARY_OBJECTIVES.md
5. Use entry points to update PRIMARY_OBJECTIVES.md

## Scripts Directory Analysis

### Available Scripts (scripts/ directory)
```
scripts/
├── analyze_architecture.py      # Maps project structure
├── analyze_complexity.py        # Analyzes code complexity
├── analyze_dependencies.py      # Analyzes dependencies
├── create_dependency_graph.py   # Creates visual graphs
├── find_entry_points.py         # Finds main entry points
└── custom_tools/                # Custom tool framework
    ├── tools/                   # Individual tools
    │   ├── analyze_imports.py
    │   ├── code_complexity.py
    │   ├── find_todos.py
    │   └── test_tool.py
    └── [framework files]
```

### Tool Capabilities Matrix

| Tool | Planning | Coding | QA | Debugging | Project Planning |
|------|----------|--------|----|-----------|--------------------|
| analyze_architecture.py | ✅ High | ✅ High | ✅ High | ✅ Critical | ✅ Critical |
| analyze_dependencies.py | ✅ High | ✅ High | ✅ High | ✅ Critical | ✅ Critical |
| create_dependency_graph.py | ✅ Medium | ❌ Low | ✅ High | ✅ High | ✅ Critical |
| find_entry_points.py | ✅ High | ✅ Medium | ✅ Medium | ✅ High | ✅ Critical |
| analyze_complexity.py | ✅ Medium | ❌ Low | ✅ Critical | ✅ High | ✅ High |

## Integration Strategy

### Strategy 1: Direct Module Import (RECOMMENDED)
**Approach**: Import scripts as Python modules
**Advantages**:
- Fast execution
- Direct access to functions
- Type safety
- Better error handling

**Implementation**:
```python
# In pipeline/tools.py
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import tools
from analyze_architecture import analyze_architecture
from analyze_dependencies import analyze_dependencies
from create_dependency_graph import create_dependency_graph
from find_entry_points import find_entry_points
from analyze_complexity import analyze_complexity
```

### Strategy 2: Executable Wrapper (FALLBACK)
**Approach**: Run scripts as executables
**Advantages**:
- Process isolation
- Works with any script
- No import issues

**Implementation**:
```python
def run_script_tool(script_name: str, *args):
    script_path = scripts_dir / f"{script_name}.py"
    result = subprocess.run(
        [sys.executable, str(script_path), *args],
        capture_output=True,
        text=True
    )
    return result.stdout
```

### Strategy 3: Hybrid Approach (OPTIMAL)
**Approach**: Use module import with executable fallback
**Advantages**:
- Best of both worlds
- Resilient to failures
- Maximum flexibility

## File Update Capability

### Current Problem
- Only have `write_file` (full rewrite) and `str_replace` (exact match)
- Cannot incrementally update structured documents
- Planning phase cannot expand objectives

### Solution: Add Update Tools

#### 1. append_to_file Tool
```python
def append_to_file(filepath: str, content: str, section: str = None):
    """Append content to file, optionally under a section"""
    pass
```

#### 2. update_section Tool
```python
def update_section(filepath: str, section: str, content: str):
    """Update a specific section in a markdown file"""
    pass
```

#### 3. insert_after Tool
```python
def insert_after(filepath: str, marker: str, content: str):
    """Insert content after a marker line"""
    pass
```

## Implementation Plan

### Phase 1: Fix Custom Tools Directory (IMMEDIATE)
1. Update `pipeline/custom_tools/registry.py`
2. Update `pipeline/custom_tools/handler.py`
3. Change from `scripts/custom_tools/tools/` to entire `scripts/` directory
4. Support both module import and executable modes

### Phase 2: Add File Update Tools (IMMEDIATE)
1. Create `pipeline/tools/file_updates.py`
2. Implement append_to_file, update_section, insert_after
3. Add to planning phase tools
4. Add to project_planning phase tools

### Phase 3: Integrate Scripts as Primary Tools (HIGH PRIORITY)
1. Create `pipeline/tools/analysis_tools.py`
2. Import all scripts/ tools
3. Create tool definitions for each
4. Add to appropriate phases

### Phase 4: Update Phase Prompts (HIGH PRIORITY)
1. Update planning phase prompt with analysis tools
2. Update QA phase prompt to clarify issue attribution
3. Update project_planning phase prompt with update capabilities
4. Update debugging phase prompt with analysis tools

### Phase 5: Test Integration (CRITICAL)
1. Test each tool in each phase
2. Verify file updates work correctly
3. Verify QA phase correctly attributes issues
4. Verify planning phase can expand objectives

## Detailed Integration Specifications

### Planning Phase Integration
```python
# Add to pipeline/phases/planning.py
PLANNING_TOOLS = [
    'create_task_plan',
    'read_file',
    'write_file',
    'append_to_file',           # NEW
    'update_section',           # NEW
    'analyze_architecture',     # NEW
    'analyze_dependencies',     # NEW
    'find_entry_points',        # NEW
]
```

### QA Phase Clarification
```python
# Update QA phase logic
# When report_issue is called:
# - Issue is with the CODE, not the QA phase
# - QA phase succeeded in finding the issue
# - Mark task as needs_fix, not QA as failed
```

### Project Planning Phase Enhancement
```python
# Add to pipeline/phases/project_planning.py
PROJECT_PLANNING_TOOLS = [
    'read_file',
    'write_file',
    'append_to_file',           # NEW
    'update_section',           # NEW
    'insert_after',             # NEW
    'analyze_architecture',     # NEW
    'analyze_dependencies',     # NEW
    'create_dependency_graph',  # NEW
    'find_entry_points',        # NEW
    'analyze_complexity',       # NEW
]
```

## Success Metrics

### Integration Success
- ✅ All scripts/ tools available in appropriate phases
- ✅ Tools can be called as modules or executables
- ✅ File update tools work correctly
- ✅ Planning phase can expand objectives
- ✅ QA phase correctly attributes issues

### Performance Metrics
- Tool discovery: < 10ms
- Module import: < 50ms
- Executable fallback: < 500ms
- File updates: < 100ms

## Next Steps

1. **IMMEDIATE**: Fix custom tools directory path
2. **IMMEDIATE**: Add file update tools
3. **HIGH**: Integrate scripts as primary tools
4. **HIGH**: Update phase prompts
5. **CRITICAL**: Test all integrations

## Conclusion

This integration will transform the pipeline from using limited custom tools to having full access to comprehensive analysis capabilities. The scripts/ directory contains valuable tools that should be first-class citizens in the pipeline, not external utilities.