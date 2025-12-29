# Document IPC System Implementation Plan

## Phase 1: Document Infrastructure (IMMEDIATE)

### 1.1 Create Document Initializer
**File**: `pipeline/document_ipc.py` (NEW)
**Purpose**: Initialize and manage IPC documents

```python
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class DocumentIPC:
    """Manage document-based inter-process communication."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.phase_documents = {
            'planning': {'read': 'PLANNING_READ.md', 'write': 'PLANNING_WRITE.md'},
            'coding': {'read': 'DEVELOPER_READ.md', 'write': 'DEVELOPER_WRITE.md'},
            'qa': {'read': 'QA_READ.md', 'write': 'QA_WRITE.md'},
            'debugging': {'read': 'DEBUG_READ.md', 'write': 'DEBUG_WRITE.md'},
        }
        self.strategic_documents = [
            'MASTER_PLAN.md',
            'PRIMARY_OBJECTIVES.md',
            'SECONDARY_OBJECTIVES.md',
            'TERTIARY_OBJECTIVES.md',
            'ARCHITECTURE.md'
        ]
    
    def initialize_documents(self):
        """Create all IPC documents if they don't exist."""
        # Create phase READ/WRITE documents
        for phase, docs in self.phase_documents.items():
            self._create_read_document(phase, docs['read'])
            self._create_write_document(phase, docs['write'])
        
        # Strategic documents created separately by user/planning
    
    def read_own_document(self, phase: str) -> str:
        """Phase reads its own READ document."""
        doc_name = self.phase_documents[phase]['read']
        return self._read_document(doc_name)
    
    def write_own_document(self, phase: str, content: str):
        """Phase writes to its own WRITE document."""
        doc_name = self.phase_documents[phase]['write']
        self._write_document(doc_name, content, phase)
    
    def write_to_phase(self, from_phase: str, to_phase: str, message: str):
        """Write message to another phase's READ document."""
        doc_name = self.phase_documents[to_phase]['read']
        self._append_message(doc_name, from_phase, message)
    
    def read_phase_output(self, phase: str) -> str:
        """Read another phase's WRITE document."""
        doc_name = self.phase_documents[phase]['write']
        return self._read_document(doc_name)
    
    def read_strategic_document(self, doc_name: str) -> str:
        """Read a strategic document."""
        return self._read_document(doc_name)
    
    def update_strategic_document(self, doc_name: str, section: str, content: str):
        """Update a section in a strategic document."""
        # Implementation for section updates
        pass
```

### 1.2 Create Document Templates
**Templates for each document type**

#### READ Document Template
```markdown
# {PHASE}_READ.md

> **Purpose**: Messages and tasks for the {phase} phase
> **Updated By**: Other phases (Planning, QA, Debugging, Developer)
> **Read By**: {Phase} phase only

## Priority Tasks
<!-- High priority tasks from Planning -->

## Requirements
<!-- Specific requirements from other phases -->

## Context
<!-- Relevant context from strategic documents -->

## Messages from Other Phases

### From Planning
<!-- Planning phase messages -->

### From QA
<!-- QA phase messages -->

### From Debugging
<!-- Debugging phase messages -->

### From Developer
<!-- Developer phase messages -->

---
**Last Updated**: {timestamp}
**Updated By**: {phase_name}
```

#### WRITE Document Template
```markdown
# {PHASE}_WRITE.md

> **Purpose**: Status and output from the {phase} phase
> **Updated By**: {Phase} phase only
> **Read By**: All other phases

## Current Status
<!-- Current phase status -->

## Completed Tasks
<!-- List of completed tasks -->

## In Progress
<!-- Tasks currently being worked on -->

## Blockers
<!-- Any blockers encountered -->

## Output Summary
<!-- Summary of work done -->

## Messages to Other Phases

### To Planning
<!-- Messages for planning phase -->

### To Developer
<!-- Messages for developer phase -->

### To QA
<!-- Messages for QA phase -->

### To Debugging
<!-- Messages for debugging phase -->

---
**Last Updated**: {timestamp}
```

### 1.3 Integrate into Base Phase
**File**: `pipeline/phases/base.py`
**Add to BasePhase**:

```python
from ..document_ipc import DocumentIPC

class BasePhase:
    def __init__(self, ...):
        # ... existing code ...
        self.doc_ipc = DocumentIPC(self.project_dir)
    
    def read_own_tasks(self) -> str:
        """Read tasks from own READ document."""
        return self.doc_ipc.read_own_document(self.phase_name)
    
    def write_own_status(self, status: str):
        """Write status to own WRITE document."""
        self.doc_ipc.write_own_document(self.phase_name, status)
    
    def send_message_to_phase(self, to_phase: str, message: str):
        """Send message to another phase."""
        self.doc_ipc.write_to_phase(self.phase_name, to_phase, message)
    
    def read_phase_output(self, phase: str) -> str:
        """Read another phase's output."""
        return self.doc_ipc.read_phase_output(phase)
    
    def read_strategic_docs(self) -> Dict[str, str]:
        """Read all strategic documents."""
        return {
            'master_plan': self.doc_ipc.read_strategic_document('MASTER_PLAN.md'),
            'primary': self.doc_ipc.read_strategic_document('PRIMARY_OBJECTIVES.md'),
            'secondary': self.doc_ipc.read_strategic_document('SECONDARY_OBJECTIVES.md'),
            'tertiary': self.doc_ipc.read_strategic_document('TERTIARY_OBJECTIVES.md'),
            'architecture': self.doc_ipc.read_strategic_document('ARCHITECTURE.md'),
        }
```

## Phase 2: Update Planning Phase (HIGH PRIORITY)

### 2.1 Planning Phase Execution Flow
**File**: `pipeline/phases/planning.py`

```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # 1. Read all phase outputs
    qa_output = self.read_phase_output('qa')
    dev_output = self.read_phase_output('coding')
    debug_output = self.read_phase_output('debugging')
    
    # 2. Read strategic documents
    strategic_docs = self.read_strategic_docs()
    
    # 3. Perform deep analysis
    analysis_results = self._perform_deep_analysis()
    
    # 4. Update strategic documents
    self._update_secondary_objectives(analysis_results, qa_output, debug_output)
    self._update_tertiary_objectives(analysis_results, dev_output)
    self._update_architecture(analysis_results)
    
    # 5. Check 95% completion for MASTER_PLAN
    if self._check_completion_threshold(state):
        self._update_master_plan(state)
    
    # 6. Create tasks based on analysis
    tasks = self._create_tasks_from_analysis(analysis_results, strategic_docs)
    
    # 7. Write to other phases' READ documents
    self._write_developer_tasks(tasks)
    self._write_qa_requirements(tasks)
    self._write_debug_priorities(analysis_results)
    
    # 8. Write own status
    self.write_own_status(self._format_planning_status(tasks, analysis_results))
    
    return PhaseResult(...)
```

### 2.2 Deep Analysis Method
```python
def _perform_deep_analysis(self) -> Dict:
    """Perform comprehensive codebase analysis."""
    results = {
        'complexity_issues': [],
        'dead_code': [],
        'integration_gaps': [],
        'architectural_issues': [],
        'test_gaps': [],
        'failures': []
    }
    
    # Get all Python files
    python_files = self._get_python_files()
    
    for filepath in python_files:
        # Complexity analysis
        complexity = self.complexity_analyzer.analyze(filepath)
        for func in complexity.results:
            if func.complexity >= 30:
                results['complexity_issues'].append({
                    'file': filepath,
                    'function': func.name,
                    'complexity': func.complexity,
                    'line': func.line,
                    'recommendation': f"Refactor - estimated {func.effort_days} days"
                })
        
        # Dead code detection
        dead_code = self.dead_code_detector.detect(filepath)
        if dead_code.unused_functions:
            for func_name, file, line in dead_code.unused_functions:
                results['dead_code'].append({
                    'file': filepath,
                    'type': 'function',
                    'name': func_name,
                    'line': line,
                    'recommendation': 'Remove or add usage'
                })
        
        # Integration gaps
        gaps = self.gap_finder.find_gaps(filepath)
        if gaps.unused_classes:
            for class_name, file, line in gaps.unused_classes:
                results['integration_gaps'].append({
                    'file': filepath,
                    'type': 'class',
                    'name': class_name,
                    'line': line,
                    'recommendation': 'Complete integration or remove'
                })
    
    return results
```

### 2.3 Strategic Document Updates
```python
def _update_secondary_objectives(self, analysis: Dict, qa_output: str, debug_output: str):
    """Update SECONDARY_OBJECTIVES.md with findings."""
    content = []
    
    # Architectural changes needed
    if analysis['complexity_issues']:
        content.append("## Architectural Changes Needed\n")
        for issue in analysis['complexity_issues']:
            content.append(f"- **{issue['file']}**: {issue['function']} "
                         f"(complexity {issue['complexity']}) - {issue['recommendation']}\n")
    
    # Testing requirements
    if analysis['test_gaps']:
        content.append("\n## Testing Requirements\n")
        for gap in analysis['test_gaps']:
            content.append(f"- {gap['description']}\n")
    
    # Reported failures (from QA and Debugging)
    if qa_output or debug_output:
        content.append("\n## Reported Failures\n")
        # Parse QA and Debug outputs for failures
        # Add to content
    
    # Integration issues
    if analysis['integration_gaps']:
        content.append("\n## Integration Issues\n")
        for gap in analysis['integration_gaps']:
            content.append(f"- **{gap['file']}**: {gap['name']} "
                         f"({gap['type']}) - {gap['recommendation']}\n")
    
    # Update document
    self.file_updater.update_section(
        "SECONDARY_OBJECTIVES.md",
        "## Current Analysis Findings",
        "\n".join(content)
    )
```

## Phase 3: Update Other Phases (HIGH PRIORITY)

### 3.1 Coding Phase
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # 1. Read own tasks
    my_tasks = self.read_own_tasks()
    
    # 2. Read strategic documents
    strategic_docs = self.read_strategic_docs()
    
    # 3. Read other phases for context
    qa_feedback = self.read_phase_output('qa')
    debug_info = self.read_phase_output('debugging')
    
    # 4. Extract relevant context for current task
    relevant_context = self._extract_relevant_context(
        task,
        strategic_docs,
        my_tasks
    )
    
    # 5. Implement task
    # ... existing implementation ...
    
    # 6. Write own status
    self.write_own_status(self._format_dev_status(task, files_created))
    
    # 7. Notify other phases
    if files_created:
        self.send_message_to_phase('qa', f"Ready for review: {', '.join(files_created)}")
    
    return PhaseResult(...)
```

### 3.2 QA Phase
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # 1. Read own tasks
    review_requests = self.read_own_tasks()
    
    # 2. Read strategic documents for criteria
    strategic_docs = self.read_strategic_docs()
    
    # 3. Read developer output
    dev_changes = self.read_phase_output('coding')
    
    # 4. Review code
    issues = self._review_code(filepath, strategic_docs)
    
    # 5. Write own status
    self.write_own_status(self._format_qa_status(issues))
    
    # 6. Notify other phases
    if issues:
        self.send_message_to_phase('debugging', f"Issues found in {filepath}")
        self.send_message_to_phase('planning', f"Quality concerns: {len(issues)} issues")
    else:
        self.send_message_to_phase('planning', f"Approved: {filepath}")
    
    return PhaseResult(...)
```

### 3.3 Debugging Phase
```python
def execute(self, state: PipelineState, task: TaskState = None, **kwargs) -> PhaseResult:
    # 1. Read own tasks
    bugs_to_fix = self.read_own_tasks()
    
    # 2. Read strategic documents
    strategic_docs = self.read_strategic_docs()
    
    # 3. Read QA findings
    qa_issues = self.read_phase_output('qa')
    
    # 4. Fix bugs
    fixes = self._fix_issues(bugs_to_fix, strategic_docs['tertiary'])
    
    # 5. Write own status
    self.write_own_status(self._format_debug_status(fixes))
    
    # 6. Notify other phases
    self.send_message_to_phase('qa', f"Please verify fixes: {', '.join(fixes)}")
    self.send_message_to_phase('planning', f"Fixed {len(fixes)} issues")
    
    return PhaseResult(...)
```

## Phase 4: Update Prompts (MEDIUM PRIORITY)

### 4.1 Planning Phase Prompt
Add to system prompt:
```
You are the Planning phase. Your responsibilities:

1. READ all phase outputs:
   - QA_WRITE.md for quality issues
   - DEVELOPER_WRITE.md for implementation status
   - DEBUG_WRITE.md for fix status

2. ANALYZE codebase deeply:
   - Run complexity analysis
   - Detect dead code
   - Find integration gaps
   - Identify architectural issues

3. UPDATE strategic documents:
   - SECONDARY_OBJECTIVES.md with architectural changes, testing needs, failures
   - TERTIARY_OBJECTIVES.md with specific code examples and fixes
   - ARCHITECTURE.md with current vs intended state
   - MASTER_PLAN.md only at 95% completion

4. WRITE to other phases:
   - DEVELOPER_READ.md with implementation tasks
   - QA_READ.md with review requirements
   - DEBUG_READ.md with priority fixes

5. WRITE own status to PLANNING_WRITE.md
```

### 4.2 Coding Phase Prompt
Add to system prompt:
```
You are the Developer/Coding phase. Your responsibilities:

1. READ your tasks from DEVELOPER_READ.md

2. READ strategic documents for context:
   - PRIMARY_OBJECTIVES.md for requirements
   - SECONDARY_OBJECTIVES.md for implementation details
   - TERTIARY_OBJECTIVES.md for code examples
   - ARCHITECTURE.md for design patterns

3. READ other phases for context:
   - QA_WRITE.md for feedback
   - DEBUG_WRITE.md for known issues

4. IMPLEMENT the task following guidance from documents

5. WRITE your status to DEVELOPER_WRITE.md

6. WRITE to other phases:
   - QA_READ.md when ready for review
   - PLANNING_READ.md for blockers or questions
```

### 4.3 QA Phase Prompt
Add to system prompt:
```
You are the QA phase. Your responsibilities:

1. READ your tasks from QA_READ.md

2. READ strategic documents for criteria:
   - PRIMARY_OBJECTIVES.md for functional requirements
   - SECONDARY_OBJECTIVES.md for quality standards
   - ARCHITECTURE.md for design compliance

3. READ developer output from DEVELOPER_WRITE.md

4. REVIEW code against all criteria

5. WRITE your findings to QA_WRITE.md

6. WRITE to other phases:
   - DEBUG_READ.md for bugs found
   - PLANNING_READ.md for quality concerns or approvals
```

### 4.4 Debugging Phase Prompt
Add to system prompt:
```
You are the Debugging phase. Your responsibilities:

1. READ your tasks from DEBUG_READ.md

2. READ strategic documents for context:
   - SECONDARY_OBJECTIVES.md for known issues
   - TERTIARY_OBJECTIVES.md for specific fixes

3. READ QA findings from QA_WRITE.md

4. FIX the issues

5. WRITE your fixes to DEBUG_WRITE.md

6. WRITE to other phases:
   - QA_READ.md for verification requests
   - PLANNING_READ.md for fix summaries
```

## Implementation Order

### Day 1: Infrastructure
1. Create `pipeline/document_ipc.py`
2. Create document templates
3. Integrate into BasePhase
4. Initialize documents on first run

### Day 2: Planning Phase
1. Add deep analysis methods
2. Add strategic document update methods
3. Add phase communication methods
4. Update planning execution flow

### Day 3: Other Phases
1. Update Coding phase
2. Update QA phase
3. Update Debugging phase
4. Test inter-phase communication

### Day 4: Prompts & Testing
1. Update all phase prompts
2. Test complete workflow
3. Verify document updates
4. Verify phase communication

## Testing Plan

1. **Document Creation**: Verify all 12 documents created
2. **Phase Reading**: Each phase reads correct documents
3. **Phase Writing**: Each phase writes to correct documents
4. **Communication Flow**: Messages flow between phases
5. **Strategic Updates**: Planning updates strategic docs
6. **95% Threshold**: MASTER_PLAN only updates at 95%

## Success Criteria

- ✅ All 12 phase documents exist and initialized
- ✅ Each phase reads its own READ document
- ✅ Each phase writes to its own WRITE document
- ✅ Phases communicate through documents
- ✅ Planning updates strategic documents
- ✅ All phases read strategic documents
- ✅ No phase writes to its own READ document
- ✅ No phase writes to another's WRITE document
- ✅ Communication is traceable and auditable
- ✅ System works asynchronously