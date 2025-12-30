# Refactoring System Design - Deep Integration

## Executive Summary

Based on deep analysis of the existing polytopic structure, this document provides a comprehensive design for integrating architecture refactoring capabilities into the autonomy pipeline.

---

## Part 1: Deep Polytopic Analysis

### Current Polytopic Structure

**7 Primary Vertices (7D Hyperdimensional Space)**:
```python
vertices = {
    'planning': {
        'type': 'planning',
        'dimensions': {
            'temporal': 0.7,      # Planning takes time
            'functional': 0.3,    # Not much execution
            'data': 0.5,
            'state': 0.5,
            'error': 0.2,         # Low error rate
            'context': 0.8,       # Needs lots of context
            'integration': 0.5
        }
    },
    'coding': {
        'type': 'execution',
        'dimensions': {
            'temporal': 0.4,      # Relatively fast
            'functional': 0.8,    # High functionality
            'data': 0.5,
            'state': 0.5,
            'error': 0.5,         # Medium error potential
            'context': 0.5,
            'integration': 0.6    # Integrates with system
        }
    },
    'qa': {
        'type': 'validation',
        'dimensions': {
            'temporal': 0.3,      # Quick validation
            'functional': 0.6,    # Moderate functionality
            'data': 0.5,
            'state': 0.5,
            'error': 0.3,         # Low error rate
            'context': 0.9,       # Needs full context
            'integration': 0.5
        }
    },
    'debugging': {
        'type': 'correction',
        'dimensions': {
            'temporal': 0.5,
            'functional': 0.7,    # Fixes functionality
            'data': 0.5,
            'state': 0.5,
            'error': 0.9,         # High error focus
            'context': 0.8,       # Needs context
            'integration': 0.5
        }
    },
    'investigation': {
        'type': 'analysis',
        'dimensions': {
            'temporal': 0.6,
            'functional': 0.4,
            'data': 0.7,          # Analyzes data
            'state': 0.6,
            'error': 0.7,
            'context': 0.9,       # Deep context needed
            'integration': 0.5
        }
    },
    'project_planning': {
        'type': 'planning',
        'dimensions': {
            'temporal': 0.8,      # Strategic planning
            'functional': 0.3,
            'data': 0.6,
            'state': 0.5,
            'error': 0.2,
            'context': 0.9,       # Full project context
            'integration': 0.7    # High integration
        }
    },
    'documentation': {
        'type': 'documentation',
        'dimensions': {
            'temporal': 0.4,
            'functional': 0.5,
            'data': 0.6,
            'state': 0.5,
            'error': 0.2,
            'context': 0.7,
            'integration': 0.6
        }
    }
}
```

**Primary Flow Edges**:
```python
edges = {
    # Core development flow
    'planning': ['coding'],
    'coding': ['qa', 'documentation'],
    'qa': ['debugging', 'documentation'],
    
    # Error handling triangle
    'debugging': ['investigation', 'coding'],
    'investigation': ['debugging', 'coding'],
    
    # Documentation flow
    'documentation': ['planning', 'qa'],
    
    # Project management
    'project_planning': ['planning']
}
```

### Specialized Phases (On-Demand)

**6 Specialized Phases** (NOT in polytope):
- `tool_design` - Creates new tools
- `prompt_design` - Designs prompts
- `role_design` - Designs roles
- `tool_evaluation` - Evaluates tools
- `prompt_improvement` - Improves prompts
- `role_improvement` - Improves roles

**Activation Triggers**:
- Loop detection (3+ consecutive failures)
- Capability gaps identified
- Explicit user request

---

## Part 2: Inter-Process Communication (IPC) System

### Document-Based Communication

**Each Phase Has**:
- **READ Document**: Written by other phases, read by this phase
- **WRITE Document**: Written by this phase, read by others

**Phase Documents**:
```python
phase_documents = {
    'planning': {
        'read': 'PLANNING_READ.md',
        'write': 'PLANNING_WRITE.md'
    },
    'coding': {
        'read': 'DEVELOPER_READ.md',
        'write': 'DEVELOPER_WRITE.md'
    },
    'qa': {
        'read': 'QA_READ.md',
        'write': 'QA_WRITE.md'
    },
    'debugging': {
        'read': 'DEBUG_READ.md',
        'write': 'DEBUG_WRITE.md'
    },
    'investigation': {
        'read': 'INVESTIGATION_READ.md',
        'write': 'INVESTIGATION_WRITE.md'
    },
    'documentation': {
        'read': 'DOCUMENTATION_READ.md',
        'write': 'DOCUMENTATION_WRITE.md'
    },
    'project_planning': {
        'read': 'PROJECT_PLANNING_READ.md',
        'write': 'PROJECT_PLANNING_WRITE.md'
    }
}
```

**Strategic Documents** (All phases read):
- `MASTER_PLAN.md` - Project specification
- `PRIMARY_OBJECTIVES.md` - Primary objectives
- `SECONDARY_OBJECTIVES.md` - Secondary objectives
- `TERTIARY_OBJECTIVES.md` - Tertiary objectives
- `ARCHITECTURE.md` - Architecture document

### How Phases Communicate

**Example Flow**:
1. QA phase detects duplicate files
2. QA writes to `INVESTIGATION_READ.md`: "Found duplicate implementations in auth.py and user_manager.py"
3. Investigation phase reads `INVESTIGATION_READ.md`
4. Investigation analyzes and writes to `INVESTIGATION_WRITE.md`: "Recommend refactoring - merge auth.py and user_manager.py"
5. Coordinator reads `INVESTIGATION_WRITE.md` and routes to refactoring phase

---

## Part 3: Existing Analysis Tools

### Available Analysis Tools

**1. Integration Gap Detector** (`pipeline/analysis/integration_gaps.py`):
- Finds unused classes
- Detects classes with unused methods
- Identifies imported but unused code

**2. Integration Conflict Detector** (`pipeline/analysis/integration_conflicts.py`):
- Detects duplicate implementations
- Finds naming inconsistencies
- Identifies feature overlap

**3. Dead Code Detector**:
- Finds unused functions
- Detects unused methods
- Identifies unused imports

**4. Complexity Analyzer**:
- Calculates cyclomatic complexity
- Identifies high-complexity functions
- Recommends refactoring

**5. Call Graph Generator**:
- Maps function calls
- Identifies dependencies
- Visualizes relationships

**6. Deep Analysis**:
- Comprehensive AST analysis
- Variable tracing
- Dependency mapping

**7. Advanced Analysis**:
- Pattern detection
- Template method recognition
- Inheritance analysis

---

## Part 4: New Refactoring Tools Design

### Tool 1: detect_duplicate_implementations

**Purpose**: Find files with duplicate or similar implementations

**Parameters**:
```python
{
    "similarity_threshold": float,  # 0.0-1.0, default 0.75
    "scope": str,                   # "project" or specific directory
    "include_tests": bool           # Include test files, default False
}
```

**Returns**:
```python
{
    "duplicate_sets": [
        {
            "files": ["auth.py", "user_manager.py"],
            "similarity_score": 0.85,
            "common_features": ["login", "logout", "validate_token"],
            "unique_to_file1": ["refresh_token"],
            "unique_to_file2": ["check_session"],
            "recommendation": "merge"
        }
    ],
    "total_duplicates": 2,
    "estimated_reduction": "~150 lines"
}
```

### Tool 2: compare_file_implementations

**Purpose**: Compare two files in detail

**Parameters**:
```python
{
    "file1": str,
    "file2": str,
    "comparison_type": str  # "functions", "classes", "full"
}
```

**Returns**:
```python
{
    "similarity_score": 0.85,
    "common_features": [
        {
            "name": "login",
            "type": "function",
            "in_both": True,
            "implementations_differ": True,
            "file1_lines": 45,
            "file2_lines": 52,
            "recommendation": "merge_with_ai"
        }
    ],
    "unique_to_file1": [...],
    "unique_to_file2": [...],
    "conflicts": [...],
    "merge_strategy": "ai_merge"
}
```

### Tool 3: extract_file_features

**Purpose**: Extract specific features from a file

**Parameters**:
```python
{
    "source_file": str,
    "features": List[str],          # Function/class names
    "include_dependencies": bool    # Include dependent code
}
```

**Returns**:
```python
{
    "extracted_features": {
        "login": {
            "type": "function",
            "code": "def login(...)...",
            "dependencies": ["validate_credentials", "create_session"],
            "imports": ["hashlib", "jwt"],
            "line_range": [45, 67]
        }
    },
    "total_lines": 23,
    "dependencies_resolved": True
}
```

### Tool 4: analyze_architecture_consistency

**Purpose**: Analyze if codebase matches MASTER_PLAN and ARCHITECTURE

**Parameters**:
```python
{
    "check_master_plan": bool,
    "check_architecture": bool,
    "check_objectives": bool
}
```

**Returns**:
```python
{
    "consistency_score": 0.75,
    "issues": [
        {
            "type": "missing_implementation",
            "objective": "User authentication system",
            "expected_files": ["auth_service.py"],
            "found_files": ["auth.py", "user_manager.py"],
            "recommendation": "merge_or_refactor"
        },
        {
            "type": "duplicate_implementation",
            "feature": "login functionality",
            "files": ["auth.py", "user_manager.py"],
            "recommendation": "consolidate"
        }
    ],
    "refactoring_needed": True,
    "priority": "high"
}
```

### Tool 5: suggest_refactoring_plan

**Purpose**: Generate refactoring plan based on analysis

**Parameters**:
```python
{
    "analysis_results": Dict,       # From analyze_architecture_consistency
    "priority": str,                # "high", "medium", "low", "all"
    "max_steps": int                # Maximum refactoring steps
}
```

**Returns**:
```python
{
    "refactoring_plan": [
        {
            "step": 1,
            "action": "merge_files",
            "source_files": ["auth.py", "user_manager.py"],
            "target_file": "auth_service.py",
            "reason": "Duplicate login functionality",
            "estimated_effort": "medium",
            "dependencies": []
        },
        {
            "step": 2,
            "action": "update_imports",
            "affected_files": ["api/routes.py", "tests/test_auth.py"],
            "old_import": "from auth import login",
            "new_import": "from auth_service import login",
            "dependencies": [1]
        }
    ],
    "total_steps": 2,
    "estimated_time": "30 minutes"
}
```

### Tool 6: merge_file_implementations

**Purpose**: Merge multiple files into one using AI

**Parameters**:
```python
{
    "source_files": List[str],
    "target_file": str,
    "merge_strategy": str,          # "keep_all", "prefer_newer", "ai_merge"
    "preserve_comments": bool,
    "preserve_docstrings": bool
}
```

**Returns**:
```python
{
    "success": True,
    "merged_file": "auth_service.py",
    "features_merged": 12,
    "conflicts_resolved": 3,
    "lines_added": 245,
    "lines_removed": 0,
    "backup_created": True,
    "backup_path": ".autonomy/backups/merge_20241230_153045/"
}
```

### Tool 7: validate_refactoring

**Purpose**: Validate refactoring didn't break anything

**Parameters**:
```python
{
    "refactored_files": List[str],
    "run_tests": bool,
    "check_imports": bool,
    "check_syntax": bool
}
```

**Returns**:
```python
{
    "valid": True,
    "syntax_errors": [],
    "import_errors": [],
    "test_results": {
        "passed": 45,
        "failed": 0,
        "skipped": 2
    },
    "warnings": [
        "Function 'old_login' is no longer used"
    ]
}
```

### Tool 8: cleanup_redundant_files

**Purpose**: Remove files that have been successfully refactored

**Parameters**:
```python
{
    "files_to_remove": List[str],
    "reason": str,
    "create_backup": bool,
    "update_git": bool
}
```

**Returns**:
```python
{
    "success": True,
    "files_removed": ["auth.py", "user_manager.py"],
    "backup_location": ".autonomy/backups/cleanup_20241230_153045/",
    "git_updated": True,
    "references_updated": 15
}
```

---

## Part 5: Refactoring Phase Design

### Phase Name: `refactoring`

### Dimensional Profile

```python
'refactoring': {
    'type': 'refactoring',
    'dimensions': {
        'temporal': 0.7,      # Refactoring takes time
        'functional': 0.8,    # High functionality changes
        'data': 0.6,          # Analyzes code data
        'state': 0.7,         # Changes system state
        'error': 0.4,         # Medium error potential
        'context': 0.9,       # Needs full context
        'integration': 0.9    # High integration impact
    }
}
```

### Polytopic Integration

**Add to vertices**:
```python
phase_types['refactoring'] = 'refactoring'
```

**Add edges**:
```python
edges = {
    'planning': ['coding', 'refactoring'],           # Can detect need for refactoring
    'coding': ['qa', 'documentation', 'refactoring'], # May need refactoring
    'qa': ['debugging', 'documentation', 'refactoring'], # Detects duplicates
    'debugging': ['investigation', 'coding', 'refactoring'], # May need refactoring
    'investigation': ['debugging', 'coding', 'refactoring'], # Recommends refactoring
    'documentation': ['planning', 'qa'],
    'project_planning': ['planning', 'refactoring'],  # Strategic refactoring
    'refactoring': ['coding', 'qa']                   # After refactoring, verify
}
```

### IPC Documents

**Add to phase_documents**:
```python
'refactoring': {
    'read': 'REFACTORING_READ.md',
    'write': 'REFACTORING_WRITE.md'
}
```

### Phase Execution Flow

```python
class RefactoringPhase(BasePhase):
    """
    Refactoring phase for architecture consistency and code quality.
    
    Responsibilities:
    1. Detect duplicate implementations
    2. Compare and analyze files
    3. Merge files using AI
    4. Update references
    5. Validate refactoring
    6. Clean up redundant files
    """
    
    def execute(self, state: PipelineState):
        """
        Main execution flow:
        
        1. Read REFACTORING_READ.md for requests
        2. Analyze architecture consistency
        3. Detect duplicates and conflicts
        4. Generate refactoring plan
        5. Execute refactoring with AI
        6. Validate results
        7. Clean up
        8. Write to REFACTORING_WRITE.md
        9. Suggest next phase
        """
```

---

## Part 6: Phase Interactions

### Planning → Refactoring

**Trigger**: Planning detects architecture inconsistencies

**Flow**:
1. Planning reads MASTER_PLAN.md
2. Planning calls `analyze_architecture_consistency`
3. If `refactoring_needed: True`, write to REFACTORING_READ.md
4. Return `next_phase: 'refactoring'`

### Coding → Refactoring

**Trigger**: Coding creates file that duplicates existing functionality

**Flow**:
1. Coding creates new file
2. Coding calls `detect_duplicate_implementations`
3. If duplicates found, write to REFACTORING_READ.md
4. Return `next_phase: 'refactoring'`

### QA → Refactoring

**Trigger**: QA detects duplicate implementations or conflicts

**Flow**:
1. QA reviews code
2. QA calls `detect_duplicate_implementations`
3. If duplicates found, write to REFACTORING_READ.md
4. Return `next_phase: 'refactoring'`

### Investigation → Refactoring

**Trigger**: Investigation recommends refactoring

**Flow**:
1. Investigation analyzes issues
2. Investigation determines refactoring would help
3. Write to REFACTORING_READ.md
4. Return `next_phase: 'refactoring'`

### Project Planning → Refactoring

**Trigger**: Strategic refactoring needed

**Flow**:
1. Project Planning reviews MASTER_PLAN.md and ARCHITECTURE.md
2. Project Planning calls `analyze_architecture_consistency`
3. If major refactoring needed, write to REFACTORING_READ.md
4. Return `next_phase: 'refactoring'`

### Refactoring → Coding

**Trigger**: Refactoring needs new implementation

**Flow**:
1. Refactoring merges files
2. Refactoring identifies missing features
3. Write to DEVELOPER_READ.md
4. Return `next_phase: 'coding'`

### Refactoring → QA

**Trigger**: Refactoring complete, needs verification

**Flow**:
1. Refactoring completes merge
2. Write to QA_READ.md
3. Return `next_phase: 'qa'`

### Refactoring ↔ Refactoring (Oscillation)

**Trigger**: Complex refactoring needs multiple passes

**Flow**:
1. Refactoring completes step 1
2. Validates and finds more work needed
3. Continues to step 2
4. May oscillate 2-3 times for complex refactoring

---

## Part 7: Integration with Project Planning

### Project Planning's Role

**Current Responsibilities**:
- Analyze codebase against MASTER_PLAN
- Generate expansion tasks
- Update ARCHITECTURE.md
- Manage objectives

**New Responsibilities**:
- Call `analyze_architecture_consistency` periodically
- Use refactoring tools to inform decisions
- Recommend strategic refactoring
- Track refactoring progress

### Enhanced Project Planning Flow

```python
def execute(self, state: PipelineState):
    # ... existing code ...
    
    # NEW: Analyze architecture consistency
    consistency = self._analyze_architecture_consistency()
    
    if consistency['refactoring_needed']:
        self.logger.info("🔄 Architecture refactoring recommended")
        
        # Generate refactoring plan
        plan = self._generate_refactoring_plan(consistency)
        
        # Write to REFACTORING_READ.md
        self._write_refactoring_request(plan)
        
        return {
            'success': True,
            'next_phase': 'refactoring',
            'reason': 'architecture_consistency'
        }
    
    # ... rest of existing code ...
```

---

## Part 8: Implementation Priority

### Phase 1: New Tools (Week 1)

**Priority Order**:
1. `detect_duplicate_implementations` - Most critical
2. `compare_file_implementations` - Needed for analysis
3. `analyze_architecture_consistency` - Strategic importance
4. `extract_file_features` - Needed for merging
5. `suggest_refactoring_plan` - Planning support
6. `merge_file_implementations` - Core functionality
7. `validate_refactoring` - Safety check
8. `cleanup_redundant_files` - Cleanup

### Phase 2: Refactoring Phase (Week 2)

1. Create RefactoringPhase class
2. Implement execute() method
3. Add to polytopic structure
4. Create IPC documents
5. Test basic flow

### Phase 3: Phase Integration (Week 3)

1. Integrate with Planning
2. Integrate with Coding
3. Integrate with QA
4. Integrate with Investigation
5. Integrate with Project Planning

### Phase 4: Testing & Refinement (Week 4)

1. Test all phase transitions
2. Test oscillation scenarios
3. Test with real projects
4. Refine based on results

---

## Part 9: Success Criteria

### Functional Requirements
- ✅ Detect duplicate implementations automatically
- ✅ Compare files in detail
- ✅ Merge files using AI
- ✅ Validate refactoring results
- ✅ Clean up redundant files
- ✅ Integrate with all phases
- ✅ Use IPC system correctly

### Quality Requirements
- ✅ No data loss during refactoring
- ✅ All features preserved
- ✅ Proper backup creation
- ✅ Comprehensive validation
- ✅ Clear error messages
- ✅ Detailed logging

### Performance Requirements
- ✅ Detect duplicates in < 10 seconds
- ✅ Compare files in < 5 seconds
- ✅ Merge files in < 60 seconds
- ✅ Handle projects with 200+ files

---

## Conclusion

This design deeply integrates the refactoring system into the existing polytopic structure, leveraging:

1. ✅ 7D hyperdimensional phase management
2. ✅ Document-based IPC system
3. ✅ Existing analysis tools
4. ✅ Strategic documents (MASTER_PLAN, ARCHITECTURE)
5. ✅ Phase-to-phase communication
6. ✅ Intelligent phase transitions

The refactoring phase becomes the **8th primary vertex** in the polytope, with natural edges to/from planning, coding, QA, investigation, and project_planning.

**Ready for implementation.**