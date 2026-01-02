# Document Usage Mapping Across All Phases

## Usage Frequency by Phase

Based on code analysis, here's how frequently each phase uses IPC documents:

| Phase | IPC Calls | Usage Level |
|-------|-----------|-------------|
| planning | 5 | Heavy |
| documentation | 5 | Heavy |
| qa | 4 | Heavy |
| debugging | 4 | Heavy |
| coding | 4 | Heavy |
| tool_design | 3 | Medium |
| project_planning | 3 | Medium |
| investigation | 3 | Medium |
| tool_evaluation | 2 | Light |
| role_improvement | 2 | Light |
| role_design | 2 | Light |
| prompt_improvement | 2 | Light |
| prompt_design | 2 | Light |
| refactoring | ? | Unknown (needs check) |

## Detailed Phase-by-Phase Document Usage

### Heavy Users (5+ IPC calls)

#### 1. Planning Phase
**Reads**:
- Strategic documents (MASTER_PLAN, ARCHITECTURE, etc.)
- QA output (QA_WRITE.md)
- Developer output (DEVELOPER_WRITE.md)
- Debug output (DEBUG_WRITE.md)

**Writes**:
- PLANNING_WRITE.md (task plans)
- Updates strategic documents

**Purpose**: Central coordination - reads all outputs to plan next tasks

#### 2. Documentation Phase
**Reads**:
- Strategic documents
- Planning output (PLANNING_WRITE.md)
- Coding output (DEVELOPER_WRITE.md)
- QA output (QA_WRITE.md)

**Writes**:
- DOCUMENTATION_WRITE.md (documentation updates)

**Purpose**: Synthesizes information from multiple phases to update docs

### Heavy Users (4 IPC calls)

#### 3. QA Phase
**Reads**:
- Strategic documents
- Coding output (DEVELOPER_WRITE.md)
- Planning output (PLANNING_WRITE.md)

**Writes**:
- QA_WRITE.md (quality reports, issues found)

**Purpose**: Reviews code and reports issues

#### 4. Debugging Phase
**Reads**:
- Strategic documents
- QA output (QA_WRITE.md)
- Planning output (PLANNING_WRITE.md)
- Coding output (DEVELOPER_WRITE.md)

**Writes**:
- DEBUG_WRITE.md (fixes applied)

**Purpose**: Fixes issues reported by QA

#### 5. Coding Phase
**Reads**:
- Strategic documents
- Planning output (PLANNING_WRITE.md)
- QA output (QA_WRITE.md)
- Debug output (DEBUG_WRITE.md)

**Writes**:
- DEVELOPER_WRITE.md (code changes)

**Purpose**: Implements tasks from planning

### Medium Users (3 IPC calls)

#### 6. Investigation Phase
**Reads**:
- Strategic documents
- Debugging output (DEBUG_WRITE.md)
- QA output (QA_WRITE.md)

**Writes**:
- INVESTIGATION_WRITE.md (diagnostic reports)

**Purpose**: Diagnoses complex issues before debugging

#### 7. Project Planning Phase
**Reads**:
- Strategic documents
- Planning output (PLANNING_WRITE.md)
- Documentation output (DOCUMENTATION_WRITE.md)

**Writes**:
- PROJECT_PLANNING_WRITE.md (expansion plans)

**Purpose**: Plans project expansions

#### 8. Tool Design Phase
**Reads**:
- Strategic documents
- Tool evaluation output (TOOL_EVALUATION_WRITE.md)

**Writes**:
- TOOL_DESIGN_WRITE.md (new tool designs)

**Purpose**: Designs new tools based on needs

### Light Users (2 IPC calls)

#### 9-13. Specialized Phases
All specialized phases (tool_evaluation, role_improvement, role_design, prompt_improvement, prompt_design) follow similar patterns:

**Reads**:
- Strategic documents
- Related phase output

**Writes**:
- Own WRITE document

**Purpose**: Focused improvements in specific areas

## Communication Flow Patterns

### Pattern 1: Main Development Loop
```
Planning → Coding → QA → Debugging → Planning
   ↓         ↓       ↓        ↓
PLANNING  DEVELOPER  QA    DEBUG
_WRITE.md _WRITE.md _WRITE.md _WRITE.md
```

### Pattern 2: Investigation Support
```
QA finds complex issue → Investigation diagnoses → Debugging fixes
        ↓                        ↓                      ↓
   QA_WRITE.md          INVESTIGATION_WRITE.md    DEBUG_WRITE.md
```

### Pattern 3: Documentation Synthesis
```
Planning + Coding + QA → Documentation updates
    ↓         ↓       ↓           ↓
PLANNING  DEVELOPER  QA    DOCUMENTATION
_WRITE.md _WRITE.md _WRITE.md  _WRITE.md
```

### Pattern 4: Strategic Alignment
```
All Phases → Read MASTER_PLAN.md, ARCHITECTURE.md
Planning → Updates strategic documents
All Phases → Adjust work based on updates
```

## Document Read/Write Matrix

| Phase | Reads From | Writes To |
|-------|-----------|-----------|
| planning | qa, coding, debugging, strategic | PLANNING_WRITE, strategic |
| coding | planning, qa, debugging, strategic | DEVELOPER_WRITE |
| qa | coding, planning, strategic | QA_WRITE |
| debugging | qa, planning, coding, strategic | DEBUG_WRITE |
| investigation | debugging, qa, strategic | INVESTIGATION_WRITE |
| documentation | planning, coding, qa, strategic | DOCUMENTATION_WRITE |
| project_planning | planning, documentation, strategic | PROJECT_PLANNING_WRITE |
| refactoring | TBD | REFACTORING_WRITE |

## Key Insights

### 1. Central Hub Pattern
**Planning phase** acts as a central hub:
- Reads outputs from qa, coding, debugging
- Writes tasks for all phases
- Updates strategic documents

### 2. Feedback Loops
Multiple feedback loops exist:
- **QA → Debugging → QA** (issue reporting and verification)
- **Planning → Coding → QA → Planning** (task execution and quality)
- **Investigation → Debugging → Investigation** (diagnosis and fix)

### 3. Strategic Document Importance
ALL phases read strategic documents, making them critical for:
- System-wide alignment
- Shared understanding of goals
- Consistent decision-making

### 4. Asymmetric Communication
Some phases are primarily **producers** (coding, qa):
- Write more than they read
- Generate information for others

Some phases are primarily **consumers** (planning, documentation):
- Read more than they write
- Synthesize information from multiple sources

### 5. Specialized Phase Isolation
Specialized phases (tool/prompt/role design/improvement) have:
- Limited communication with main development loop
- Focus on meta-improvements
- Less frequent execution

## Recommendations

1. **Monitor Document Size**: Heavy users may create large documents
2. **Implement Archiving**: Rotate old content to keep documents manageable
3. **Add Structured Sections**: Use consistent headers in documents
4. **Track Read Patterns**: Identify which documents are most valuable
5. **Optimize Hot Paths**: Cache frequently-read strategic documents