# Inter-Process Communication (IPC) System - Deep Analysis

## Overview

The autonomy system uses a **document-based IPC mechanism** where phases communicate through markdown files rather than direct function calls or message queues.

## Core Architecture

### Document Types

#### 1. Phase-Specific Documents (READ/WRITE pairs)
Each of the 14 phases has two documents:

**READ Documents** (Input):
- Written BY other phases
- Read BY the phase itself
- Contains tasks, requests, and information FOR this phase

**WRITE Documents** (Output):
- Written BY the phase itself
- Read BY other phases
- Contains results, findings, and information FROM this phase

**Phase Document Mappings**:
```python
{
    'planning': {'read': 'PLANNING_READ.md', 'write': 'PLANNING_WRITE.md'},
    'coding': {'read': 'DEVELOPER_READ.md', 'write': 'DEVELOPER_WRITE.md'},
    'qa': {'read': 'QA_READ.md', 'write': 'QA_WRITE.md'},
    'debugging': {'read': 'DEBUG_READ.md', 'write': 'DEBUG_WRITE.md'},
    'investigation': {'read': 'INVESTIGATION_READ.md', 'write': 'INVESTIGATION_WRITE.md'},
    'documentation': {'read': 'DOCUMENTATION_READ.md', 'write': 'DOCUMENTATION_WRITE.md'},
    'project_planning': {'read': 'PROJECT_PLANNING_READ.md', 'write': 'PROJECT_PLANNING_WRITE.md'},
    'refactoring': {'read': 'REFACTORING_READ.md', 'write': 'REFACTORING_WRITE.md'},
    # Specialized phases
    'tool_design': {'read': 'TOOL_DESIGN_READ.md', 'write': 'TOOL_DESIGN_WRITE.md'},
    'tool_evaluation': {'read': 'TOOL_EVALUATION_READ.md', 'write': 'TOOL_EVALUATION_WRITE.md'},
    'prompt_design': {'read': 'PROMPT_DESIGN_READ.md', 'write': 'PROMPT_DESIGN_WRITE.md'},
    'prompt_improvement': {'read': 'PROMPT_IMPROVEMENT_READ.md', 'write': 'PROMPT_IMPROVEMENT_WRITE.md'},
    'role_design': {'read': 'ROLE_DESIGN_READ.md', 'write': 'ROLE_DESIGN_WRITE.md'},
    'role_improvement': {'read': 'ROLE_IMPROVEMENT_READ.md', 'write': 'ROLE_IMPROVEMENT_WRITE.md'},
}
```

#### 2. Strategic Documents (Shared, Planning-managed)
These are read by ALL phases but primarily updated by planning:

1. **MASTER_PLAN.md** - Overall project objectives and goals
2. **PRIMARY_OBJECTIVES.md** - High-priority goals
3. **SECONDARY_OBJECTIVES.md** - Medium-priority goals
4. **TERTIARY_OBJECTIVES.md** - Low-priority goals
5. **ARCHITECTURE.md** - System design and structure

## Communication Patterns

### Pattern 1: Phase-to-Phase Communication
```
QA Phase finds bug → Writes to QA_WRITE.md
                   → Debugging reads QA_WRITE.md
                   → Debugging writes fix to DEBUG_WRITE.md
                   → QA reads DEBUG_WRITE.md to verify
```

### Pattern 2: Strategic Document Updates
```
Planning Phase → Updates MASTER_PLAN.md
              → All phases read MASTER_PLAN.md
              → Phases align their work with plan
```

### Pattern 3: Cross-Phase Coordination
```
Investigation Phase → Writes findings to INVESTIGATION_WRITE.md
                   → Debugging reads INVESTIGATION_WRITE.md
                   → Debugging implements fix
                   → Writes result to DEBUG_WRITE.md
                   → Investigation reads DEBUG_WRITE.md to verify
```

## Document IPC Class Structure

### Key Methods

1. **initialize_documents()** - Creates all IPC documents
2. **read_own_document(phase)** - Phase reads its READ document
3. **write_own_document(phase, content)** - Phase writes to its WRITE document
4. **write_to_phase(from_phase, to_phase, message)** - Direct phase-to-phase messaging
5. **read_phase_output(from_phase, to_phase)** - Read another phase's WRITE document
6. **read_strategic_document(doc_name)** - Read strategic documents
7. **update_strategic_document(doc_name, content)** - Update strategic documents

## Integration with Polytopic Structure

### How IPC Relates to Polytopic Vertices

The polytopic structure defines **which phases can communicate** (edges), while the IPC system defines **how they communicate** (documents).

**Example**:
```
Polytopic Edge: debugging → investigation
IPC Mechanism: debugging writes to DEBUG_WRITE.md
              investigation reads DEBUG_WRITE.md
```

### Dimensional Alignment and IPC

The dimensional alignment system scores phase transitions. IPC documents provide the **context** for these transitions:

1. **Error Dimension** → Debugging reads QA_WRITE.md (error reports)
2. **Complexity Dimension** → Refactoring reads analysis results
3. **Progress Dimension** → Planning reads all WRITE documents

## Document Lifecycle

### Creation
```python
def _create_read_document(self, phase: str, doc_name: str):
    """Create READ document with template"""
    # Creates document with instructions for other phases
    # Explains what information this phase needs
```

### Reading
```python
def read_own_document(self, phase: str) -> str:
    """Phase reads its own READ document"""
    # Returns content written by other phases
    # Phase uses this to understand what work is needed
```

### Writing
```python
def write_own_document(self, phase: str, content: str):
    """Phase writes to its own WRITE document"""
    # Appends timestamped content
    # Other phases can read this to see results
```

### Archiving
Documents are timestamped and can be archived for historical analysis.

## Strengths of Document-Based IPC

1. **Transparency** - All communication is visible and auditable
2. **Persistence** - Communication history is preserved
3. **Asynchronous** - Phases don't need to be running simultaneously
4. **Debuggable** - Easy to inspect what was communicated
5. **Human-readable** - Developers can read and understand communication
6. **Version-controllable** - Documents can be tracked in git

## Weaknesses and Limitations

1. **File I/O overhead** - Reading/writing files is slower than memory
2. **No real-time signaling** - Phases must poll for updates
3. **Potential conflicts** - Multiple phases writing simultaneously
4. **Size growth** - Documents can grow large over time
5. **No structured validation** - Content format not enforced

## Integration with Learning Process

### How IPC Supports Learning

1. **Pattern Recognition** - Patterns are detected from WRITE documents
2. **Self-Awareness** - System reads its own outputs to understand behavior
3. **Adaptation** - Phases adjust based on feedback in READ documents
4. **Historical Analysis** - Past communications inform future decisions

### Learning Feedback Loop
```
Phase executes → Writes results to WRITE document
              → Pattern detector analyzes WRITE documents
              → Patterns stored in analytics
              → Self-awareness system reads patterns
              → Prompts adapted based on patterns
              → Phase executes with improved prompt
```

## Next Analysis Steps

1. Map exact document usage by each phase
2. Analyze document read/write frequency
3. Identify communication bottlenecks
4. Examine document size growth patterns
5. Review integration with learning system