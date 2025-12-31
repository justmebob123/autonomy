# Refactoring Phase Complete Redesign - Implementation Plan

## Executive Summary

Complete redesign of refactoring phase from "quick analysis tool" to "major development phase" that can run for dozens of iterations rebuilding the entire codebase.

## Current State Analysis

### What's Wrong
1. ❌ Runs for only 1 iteration
2. ❌ Has 3-iteration cooldown preventing continuous work
3. ❌ No task system for tracking refactoring work
4. ❌ No conversation continuity between iterations
5. ❌ No progress tracking
6. ❌ Returns immediately after analysis
7. ❌ Treats refactoring as "quick check" not "major work"

### What's Right
1. ✅ Tool system works (detect duplicates, analyze complexity, etc.)
2. ✅ IPC document system works
3. ✅ Integration with coordinator works
4. ✅ Error handling works

## Implementation Phases

### Phase 1: Remove Cooldown and Fix Trigger Logic (IMMEDIATE)

**Goal**: Allow refactoring to run continuously

**Changes**:
1. Remove cooldown check from `_should_trigger_refactoring()`
2. Change trigger logic from periodic to quality-based
3. Allow refactoring to continue until complete

**Files to Modify**:
- `pipeline/coordinator.py`

**Code Changes**:
```python
# REMOVE THIS
recent_phases = state.phase_history[-3:]
if any(phase == 'refactoring' for phase in recent_phases):
    return False  # Cooldown active

# ADD QUALITY-BASED TRIGGERS
def _should_trigger_refactoring(self, state: PipelineState) -> bool:
    # Only trigger if refactoring is already running OR quality issues detected
    
    # If refactoring is currently running, continue it
    if state.current_phase == 'refactoring':
        return True
    
    # Check for quality issues
    if self._has_quality_issues(state):
        return True
    
    return False

def _has_quality_issues(self, state: PipelineState) -> bool:
    # Check for architectural problems
    # Check for duplicate code
    # Check for high complexity
    # Check for dead code
    # Return True if any issues found
```

### Phase 2: Add Refactoring Task System (WEEK 1)

**Goal**: Track refactoring work like coding tasks

**Changes**:
1. Create `RefactoringTask` class
2. Add task creation in refactoring phase
3. Track tasks in state manager
4. Add task status tracking

**Files to Create**:
- `pipeline/state/refactoring_task.py`

**Code Structure**:
```python
@dataclass
class RefactoringTask:
    task_id: str
    issue_type: str  # duplicate, complexity, dead_code, architecture, conflict
    target_files: List[str]
    description: str
    priority: str  # critical, high, medium, low
    fix_approach: str  # autonomous, developer_review, needs_new_code
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    fix_details: Optional[str]
```

**Files to Modify**:
- `pipeline/state/manager.py` - Add refactoring task tracking
- `pipeline/phases/refactoring.py` - Create tasks from analysis

### Phase 3: Multi-Iteration Refactoring Loop (WEEK 1)

**Goal**: Make refactoring run for many iterations like coding

**Changes**:
1. Refactor `execute()` method to support continuous operation
2. Add conversation continuity
3. Add progress tracking
4. Add completion detection

**Files to Modify**:
- `pipeline/phases/refactoring.py`

**Code Structure**:
```python
class RefactoringPhase(BasePhase):
    def execute(self, state: PipelineState) -> PhaseResult:
        # Check if we have pending refactoring tasks
        pending_tasks = self._get_pending_refactoring_tasks(state)
        
        if not pending_tasks:
            # No pending tasks, do initial analysis
            analysis_result = self._analyze_codebase(state)
            
            if not analysis_result.issues_found:
                # No issues found, refactoring complete
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message="No refactoring issues found",
                    next_phase="coding"
                )
            
            # Create tasks from issues
            tasks = self._create_tasks_from_issues(analysis_result.issues)
            self._add_tasks_to_state(state, tasks)
            pending_tasks = tasks
        
        # Work on next task
        task = self._select_next_task(pending_tasks)
        result = self._work_on_task(state, task)
        
        if result.success:
            task.status = TaskStatus.COMPLETED
            self._update_task(state, task)
            
            # Check if more tasks remain
            remaining = self._get_pending_refactoring_tasks(state)
            if remaining:
                # More work to do, continue refactoring
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message=f"Task {task.task_id} completed, {len(remaining)} tasks remaining",
                    next_phase="refactoring"  # Continue refactoring
                )
            else:
                # All tasks complete, re-analyze
                return PhaseResult(
                    success=True,
                    phase=self.phase_name,
                    message="All tasks completed, re-analyzing",
                    next_phase="refactoring"  # Re-analyze
                )
        else:
            # Task failed
            task.status = TaskStatus.FAILED
            task.error_message = result.message
            self._update_task(state, task)
            
            # Continue with next task
            return PhaseResult(
                success=True,
                phase=self.phase_name,
                message=f"Task {task.task_id} failed, continuing with next task",
                next_phase="refactoring"
            )
```

### Phase 4: Issue Reporting Mode (WEEK 2)

**Goal**: Create comprehensive reports for complex issues

**Changes**:
1. Detect when issues are too complex for autonomous fixing
2. Create detailed issue reports
3. Add developer review workflow
4. Generate REFACTORING_REPORT.md

**Files to Modify**:
- `pipeline/phases/refactoring.py`

**Code Structure**:
```python
def _work_on_task(self, state: PipelineState, task: RefactoringTask) -> PhaseResult:
    # Analyze task complexity
    if task.fix_approach == "developer_review":
        # Too complex for autonomous fixing
        return self._create_issue_report(state, task)
    
    # Try autonomous fixing
    result = self._fix_issue_autonomously(state, task)
    
    if result.success:
        return result
    
    # Autonomous fixing failed, create report
    task.fix_approach = "developer_review"
    return self._create_issue_report(state, task)

def _create_issue_report(self, state: PipelineState, task: RefactoringTask) -> PhaseResult:
    # Generate detailed report
    report = {
        "issue_type": task.issue_type,
        "affected_files": task.target_files,
        "description": task.description,
        "priority": task.priority,
        "recommended_fix": self._generate_fix_recommendation(task),
        "impact_analysis": self._analyze_impact(task),
        "effort_estimate": self._estimate_effort(task)
    }
    
    # Write to REFACTORING_REPORT.md
    self._write_report(report)
    
    return PhaseResult(
        success=True,
        phase=self.phase_name,
        message=f"Issue report created for {task.task_id}",
        needs_developer_review=True
    )
```

### Phase 5: Coordinator Integration (WEEK 2)

**Goal**: Update coordinator to support continuous refactoring

**Changes**:
1. Remove periodic triggers
2. Add quality-based triggers
3. Support refactoring continuation
4. Handle developer review workflow

**Files to Modify**:
- `pipeline/coordinator.py`

**Code Changes**:
```python
def _select_next_phase(self, state: PipelineState) -> str:
    # If refactoring is running and has pending tasks, continue it
    if state.current_phase == 'refactoring':
        pending_tasks = self._get_pending_refactoring_tasks(state)
        if pending_tasks:
            return 'refactoring'
    
    # Check if refactoring should be triggered
    if self._should_trigger_refactoring(state):
        return 'refactoring'
    
    # Normal phase selection
    return self._tactical_decision_tree(state)

def _should_trigger_refactoring(self, state: PipelineState) -> bool:
    # Don't trigger during foundation phase
    if state.project_phase == 'foundation':
        return False
    
    # Trigger during integration phase if quality issues detected
    if state.project_phase == 'integration':
        if self._has_quality_issues(state):
            return True
    
    # Trigger during consolidation phase (aggressive refactoring)
    if state.project_phase == 'consolidation':
        if self._has_quality_issues(state):
            return True
    
    return False
```

## Testing Plan

### Test 1: Continuous Refactoring
```bash
# Create project with many quality issues
# Run pipeline
# Verify refactoring runs for multiple iterations
# Verify refactoring fixes issues
# Verify refactoring completes when no issues remain
```

### Test 2: Issue Reporting
```bash
# Create project with complex architectural issues
# Run pipeline
# Verify refactoring creates issue reports
# Verify reports are comprehensive
# Verify developer review workflow triggers
```

### Test 3: Task Tracking
```bash
# Run refactoring
# Verify tasks are created
# Verify task status updates
# Verify progress tracking works
```

### Test 4: Conversation Continuity
```bash
# Run refactoring for multiple iterations
# Verify conversation history maintained
# Verify context preserved between iterations
```

## Success Criteria

1. ✅ Refactoring can run for 20+ iterations
2. ✅ Refactoring creates and tracks tasks
3. ✅ Refactoring fixes issues autonomously
4. ✅ Refactoring creates reports for complex issues
5. ✅ Refactoring maintains conversation continuity
6. ✅ Refactoring tracks progress
7. ✅ Refactoring completes when no issues remain
8. ✅ No cooldown prevents continuous work

## Timeline

- **Phase 1**: 1 day (remove cooldown, fix triggers)
- **Phase 2**: 3 days (add task system)
- **Phase 3**: 3 days (multi-iteration loop)
- **Phase 4**: 3 days (issue reporting)
- **Phase 5**: 2 days (coordinator integration)
- **Testing**: 2 days

**Total**: 2 weeks

## Next Steps

1. **IMMEDIATE**: Remove cooldown and fix trigger logic
2. **Week 1**: Implement task system and multi-iteration loop
3. **Week 2**: Implement issue reporting and coordinator integration
4. **Testing**: Comprehensive testing with real projects

## Questions for User

1. Should refactoring always try autonomous fixing first, or should some issues go directly to developer review?
2. What's the maximum number of iterations refactoring should run before forcing developer review?
3. Should refactoring create a single comprehensive report or multiple smaller reports?
4. Should refactoring pause for developer review or continue with other tasks?

## Conclusion

This redesign transforms refactoring from a "quick check" into a "major development phase" that can rebuild entire codebases over many iterations, matching the user's vision.