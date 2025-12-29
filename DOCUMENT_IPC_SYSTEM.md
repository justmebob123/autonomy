# Document-Based Inter-Process Communication System

## Overview
Each phase communicates through a document-based IPC system with clear read/write boundaries.

## Document Structure

### Phase-Specific Documents

#### Planning Phase
- **PLANNING_READ.md** (Planning reads ONLY, others write)
  - Messages from QA about quality issues
  - Messages from Debugging about fixes needed
  - Messages from Developer about blockers
  - System alerts and priorities

- **PLANNING_WRITE.md** (Planning writes ONLY, others read)
  - Current planning decisions
  - Task prioritization
  - Resource allocation
  - Next phase recommendations

#### Developer/Coding Phase
- **DEVELOPER_READ.md** (Developer reads ONLY, others write)
  - Implementation requirements from Planning
  - Bug fixes needed from Debugging
  - Quality requirements from QA
  - Architecture constraints

- **DEVELOPER_WRITE.md** (Developer writes ONLY, others read)
  - Implementation status
  - Technical decisions made
  - Blockers encountered
  - Code changes summary

#### QA Phase
- **QA_READ.md** (QA reads ONLY, others write)
  - Files to review from Developer
  - Quality criteria from Planning
  - Known issues from Debugging
  - Test requirements

- **QA_WRITE.md** (QA writes ONLY, others read)
  - Quality issues found
  - Test results
  - Code review feedback
  - Approval status

#### Debugging Phase
- **DEBUG_READ.md** (Debugging reads ONLY, others write)
  - Bugs reported from QA
  - Issues from Developer
  - Priority fixes from Planning
  - Error logs and traces

- **DEBUG_WRITE.md** (Debugging writes ONLY, others read)
  - Fixes implemented
  - Root cause analysis
  - Remaining issues
  - Fix verification status

### Strategic Documents (Planning updates, all read)

- **MASTER_PLAN.md**
  - High-level vision and goals
  - Updated by Planning at 95% completion only
  - Read by all phases for direction

- **PRIMARY_OBJECTIVES.md**
  - Core functional requirements
  - Updated by Planning
  - Read by all phases for context

- **SECONDARY_OBJECTIVES.md**
  - Architectural changes needed
  - Testing requirements
  - Reported failures
  - Integration issues
  - Updated by Planning after analysis
  - Read by all phases for implementation details

- **TERTIARY_OBJECTIVES.md**
  - Specific code examples
  - Component-level fixes
  - Design pattern improvements
  - Detailed implementation guidance
  - Updated by Planning after deep analysis
  - Read by all phases for specifics

- **ARCHITECTURE.md**
  - Current architecture state
  - Intended architecture
  - Design patterns
  - Module structure
  - Updated by Planning
  - Read by all phases for design guidance

## IPC Patterns

### Pattern 1: Issue Reporting (QA → Planning → Debugging)
```
1. QA finds issue in code
2. QA writes to QA_WRITE.md:
   "Issue: Memory leak in monitors/cpu.py line 45"
3. Planning reads QA_WRITE.md
4. Planning analyzes and writes to DEBUG_READ.md:
   "Priority: HIGH - Fix memory leak in monitors/cpu.py"
5. Planning updates SECONDARY_OBJECTIVES.md:
   "## Known Issues\n- Memory leak in CPU monitor"
6. Debugging reads DEBUG_READ.md
7. Debugging fixes issue
8. Debugging writes to DEBUG_WRITE.md:
   "Fixed: Memory leak in monitors/cpu.py - added cleanup"
9. Planning reads DEBUG_WRITE.md
10. Planning writes to QA_READ.md:
    "Verify fix: monitors/cpu.py memory leak"
```

### Pattern 2: Feature Implementation (Planning → Developer → QA)
```
1. Planning analyzes MASTER_PLAN.md
2. Planning writes to DEVELOPER_READ.md:
   "Implement: Email alert handler in alerts/email.py"
3. Planning updates TERTIARY_OBJECTIVES.md with code example
4. Developer reads DEVELOPER_READ.md + TERTIARY_OBJECTIVES.md
5. Developer implements feature
6. Developer writes to DEVELOPER_WRITE.md:
   "Implemented: Email alert handler with SMTP support"
7. Planning reads DEVELOPER_WRITE.md
8. Planning writes to QA_READ.md:
   "Review: alerts/email.py - check SMTP error handling"
9. QA reads QA_READ.md
10. QA reviews code
11. QA writes to QA_WRITE.md:
    "Approved: alerts/email.py - good error handling"
```

### Pattern 3: Blocker Resolution (Developer → Planning → All)
```
1. Developer encounters blocker
2. Developer writes to DEVELOPER_WRITE.md:
   "Blocker: Missing database schema for alerts table"
3. Planning reads DEVELOPER_WRITE.md
4. Planning analyzes and updates SECONDARY_OBJECTIVES.md:
   "## Database Changes Needed\n- Create alerts table schema"
5. Planning writes to DEVELOPER_READ.md:
   "Priority: Create database migration for alerts table"
6. Developer reads DEVELOPER_READ.md
7. Developer implements migration
8. Developer writes to DEVELOPER_WRITE.md:
   "Resolved: Created alerts table migration"
```

## Phase Execution Flow

### Planning Phase
```python
def execute(self):
    # 1. Read all phase WRITE documents
    qa_messages = read("QA_WRITE.md")
    dev_messages = read("DEVELOPER_WRITE.md")
    debug_messages = read("DEBUG_WRITE.md")
    
    # 2. Read strategic documents
    master_plan = read("MASTER_PLAN.md")
    primary = read("PRIMARY_OBJECTIVES.md")
    secondary = read("SECONDARY_OBJECTIVES.md")
    tertiary = read("TERTIARY_OBJECTIVES.md")
    architecture = read("ARCHITECTURE.md")
    
    # 3. Perform deep analysis
    analysis = analyze_codebase()
    
    # 4. Update strategic documents
    update("SECONDARY_OBJECTIVES.md", analysis)
    update("TERTIARY_OBJECTIVES.md", specific_fixes)
    update("ARCHITECTURE.md", current_state)
    
    # 5. Check 95% completion
    if completion >= 0.95:
        update("MASTER_PLAN.md", achievements)
    
    # 6. Write to other phases' READ documents
    write("DEVELOPER_READ.md", implementation_tasks)
    write("QA_READ.md", review_requirements)
    write("DEBUG_READ.md", priority_fixes)
    
    # 7. Write own status
    write("PLANNING_WRITE.md", planning_decisions)
```

### Developer Phase
```python
def execute(self):
    # 1. Read own READ document
    tasks = read("DEVELOPER_READ.md")
    
    # 2. Read strategic documents for context
    primary = read("PRIMARY_OBJECTIVES.md")
    secondary = read("SECONDARY_OBJECTIVES.md")
    tertiary = read("TERTIARY_OBJECTIVES.md")
    architecture = read("ARCHITECTURE.md")
    
    # 3. Read other phases' WRITE documents for context
    qa_feedback = read("QA_WRITE.md")
    debug_info = read("DEBUG_WRITE.md")
    
    # 4. Implement task
    implement_feature(tasks, tertiary)
    
    # 5. Write own status
    write("DEVELOPER_WRITE.md", implementation_status)
    
    # 6. Write to other phases' READ documents if needed
    if has_questions:
        write("PLANNING_READ.md", questions)
    if ready_for_review:
        write("QA_READ.md", review_request)
```

### QA Phase
```python
def execute(self):
    # 1. Read own READ document
    review_tasks = read("QA_READ.md")
    
    # 2. Read strategic documents for criteria
    primary = read("PRIMARY_OBJECTIVES.md")
    secondary = read("SECONDARY_OBJECTIVES.md")
    architecture = read("ARCHITECTURE.md")
    
    # 3. Read developer output
    dev_changes = read("DEVELOPER_WRITE.md")
    
    # 4. Review code
    issues = review_code(review_tasks, secondary)
    
    # 5. Write own status
    write("QA_WRITE.md", issues)
    
    # 6. Write to other phases' READ documents
    if has_issues:
        write("DEBUG_READ.md", bugs_found)
        write("PLANNING_READ.md", quality_concerns)
    else:
        write("PLANNING_READ.md", approval)
```

### Debugging Phase
```python
def execute(self):
    # 1. Read own READ document
    bugs = read("DEBUG_READ.md")
    
    # 2. Read strategic documents for context
    secondary = read("SECONDARY_OBJECTIVES.md")
    tertiary = read("TERTIARY_OBJECTIVES.md")
    
    # 3. Read QA findings
    qa_issues = read("QA_WRITE.md")
    
    # 4. Fix bugs
    fixes = fix_issues(bugs, tertiary)
    
    # 5. Write own status
    write("DEBUG_WRITE.md", fixes)
    
    # 6. Write to other phases' READ documents
    write("QA_READ.md", verification_requests)
    write("PLANNING_READ.md", fix_summary)
```

## Document Format Standards

### READ Documents Format
```markdown
# [PHASE]_READ.md

## Priority Tasks
- [ ] Task 1 (from Planning)
- [ ] Task 2 (from QA)

## Context
- Relevant information from other phases

## Requirements
- Specific requirements for this phase

## Notes
- Additional guidance

---
Last Updated: [timestamp]
Updated By: [phase_name]
```

### WRITE Documents Format
```markdown
# [PHASE]_WRITE.md

## Status
Current phase status

## Completed
- [x] Task 1 - details
- [x] Task 2 - details

## In Progress
- [ ] Task 3 - current status

## Blockers
- Issue 1 - description
- Issue 2 - description

## Messages to Other Phases
### To Planning
- Message 1

### To QA
- Message 2

---
Last Updated: [timestamp]
```

## Implementation Requirements

### 1. Document Initialization
Create all 12 documents on first run:
- 4 READ documents (one per phase)
- 4 WRITE documents (one per phase)
- 5 strategic documents (if not exist)

### 2. Phase Modifications
Each phase needs:
- Read own READ document at start
- Read relevant strategic documents
- Read other phases' WRITE documents for context
- Write to own WRITE document at end
- Write to other phases' READ documents as needed

### 3. Planning Phase Special Responsibilities
- Read ALL phase WRITE documents
- Analyze codebase deeply
- Update strategic documents
- Write to ALL phase READ documents
- Check 95% completion for MASTER_PLAN

### 4. Locking and Idempotency
- Each phase owns its WRITE document (exclusive write)
- All phases can read any document (shared read)
- Documents are append-friendly (idempotent)
- Timestamps track updates

## Benefits

1. **Clear Ownership**: Each phase owns its WRITE document
2. **Flexible Communication**: Any phase can write to any READ document
3. **Traceability**: All communication is documented
4. **Idempotency**: Documents can be read multiple times safely
5. **Locking**: Write ownership prevents conflicts
6. **Asynchronous**: Phases don't need to be running simultaneously
7. **Persistent**: Communication survives restarts
8. **Auditable**: Full history of inter-phase communication

## Success Criteria

- ✅ All 12 phase documents exist
- ✅ Each phase reads its own READ document
- ✅ Each phase writes to its own WRITE document
- ✅ Phases write to other phases' READ documents
- ✅ Planning updates strategic documents
- ✅ All phases read strategic documents
- ✅ Communication flows between phases
- ✅ No phase writes to its own READ document
- ✅ No phase writes to another's WRITE document