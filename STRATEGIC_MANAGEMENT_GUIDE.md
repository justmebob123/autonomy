# Strategic Management System Guide

## Overview

The Strategic Management System transforms the autonomy pipeline from a tactical task processor into a strategic goal-oriented system. It introduces **objectives** as first-class citizens that drive all decision-making.

## Key Concepts

### 1. Objectives

**Objectives** are high-level strategic goals that group related tasks and track progress toward specific outcomes.

**Three Priority Levels:**
- **PRIMARY**: Must-have features critical for basic functionality
- **SECONDARY**: Important features that significantly enhance the project
- **TERTIARY**: Nice-to-have features that improve user experience

**Objective Lifecycle:**
```
PROPOSED → APPROVED → ACTIVE → IN_PROGRESS → COMPLETING → COMPLETED → DOCUMENTED
```

**Special States:**
- **BLOCKED**: Dependencies not met
- **DEGRADING**: Success rate dropping, needs intervention

### 2. Issues

**Issues** are quality problems identified by QA that need to be fixed.

**Issue Severity:**
- **CRITICAL**: System broken, blocks progress
- **HIGH**: Major problems, significant impact
- **MEDIUM**: Minor issues, moderate impact
- **LOW**: Cosmetic issues, minimal impact

**Issue Lifecycle:**
```
OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → VERIFIED → CLOSED
```

### 3. Strategic Decision-Making

The coordinator now makes decisions based on **objectives**, not just task status:

**Strategic Mode** (when objectives exist):
1. Get active objective
2. Analyze objective health
3. Determine what the objective needs
4. Select appropriate phase

**Tactical Mode** (legacy, when no objectives):
1. Check task status
2. Select phase based on task needs

## Architecture

### Three-Layer System

```
┌─────────────────────────────────────┐
│      STRATEGIC LAYER                │
│  ObjectiveManager + Objectives      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      TACTICAL LAYER                 │
│  IssueTracker + Tasks + Files       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      EXECUTION LAYER                │
│  Coordinator + Phases               │
└─────────────────────────────────────┘
```

### Core Components

#### ObjectiveManager
- Loads objectives from markdown files
- Tracks objective health and status
- Determines active objective
- Coordinates objective dependencies
- Triggers phase transitions based on objective needs

#### IssueTracker
- Centralized issue database
- Full lifecycle management
- Priority-based querying
- Issue correlation
- Automatic fix task creation

#### Strategic Coordinator
- Makes objective-driven decisions
- Analyzes objective health
- Passes objective context to phases
- Tracks progress at objective level

## Usage

### Step 1: Define Objectives

Create objective files in your project directory:

**PRIMARY_OBJECTIVES.md:**
```markdown
# Primary Objectives

## 1. Core Infrastructure

**ID**: primary_001
**Status**: approved
**Target Date**: 2024-12-31

### Description
Establish foundational infrastructure.

### Tasks
- [ ] Configuration system (core/config.py)
- [ ] Logging system (core/logger.py)
- [ ] Error handling (core/errors.py)

### Dependencies
- None

### Acceptance Criteria
- All core systems operational
- Full test coverage
- Documentation complete
```

### Step 2: Run Pipeline

The pipeline will automatically:
1. Load objectives from markdown files
2. Sync objectives to state
3. Use strategic decision-making
4. Track progress at objective level

```bash
cd ~/AI/autonomy
./run.py ../your-project/ -vv
```

### Step 3: Monitor Progress

The coordinator logs objective context:
```
🎯 Active objective: Core Infrastructure (primary) - 60% complete
💊 Objective health: healthy - Objective progressing normally
```

### Step 4: Track Issues

When QA finds problems:
1. Issues are created in IssueTracker
2. Issues are linked to tasks and objectives
3. Objective health is updated
4. Debugging phase prioritizes critical issues

### Step 5: Complete Objectives

When all tasks are done:
1. Objective status → COMPLETING
2. Documentation phase documents the objective
3. Objective status → COMPLETED
4. Next objective becomes active

## Integration Points

### Planning Phase
- Receives active objective from coordinator
- Creates tasks linked to objective
- Updates objective's task list
- Tracks objective_id in each task

### QA Phase
- Creates Issue objects when problems found
- Links issues to tasks and objectives
- Updates objective's open_issues list
- Determines issue severity

### Debugging Phase
- Gets issues from IssueTracker by priority
- Marks issues as IN_PROGRESS
- Resolves issues when fixed
- Updates objective's issue lists

### Coordinator
- Loads objectives at startup
- Makes strategic decisions
- Passes objective to phases
- Tracks objective health

## Data Structures

### Objective
```python
{
    "id": "primary_001",
    "level": "primary",
    "title": "Core Infrastructure",
    "status": "in_progress",
    "tasks": ["task_001", "task_002"],
    "completed_tasks": ["task_001"],
    "completion_percentage": 50.0,
    "open_issues": ["issue_001"],
    "critical_issues": [],
    "success_rate": 0.85,
    "depends_on": [],
    "acceptance_criteria": [...]
}
```

### Issue
```python
{
    "id": "issue_001",
    "issue_type": "incomplete",
    "severity": "high",
    "file": "core/config.py",
    "title": "Missing validation",
    "description": "Config validation not implemented",
    "status": "open",
    "related_task": "task_001",
    "related_objective": "primary_001",
    "reported_by": "qa"
}
```

### Task (Enhanced)
```python
{
    "task_id": "task_001",
    "description": "Implement config system",
    "target_file": "core/config.py",
    "status": "completed",
    "objective_id": "primary_001",  # NEW
    "objective_level": "primary"    # NEW
}
```

## Benefits

### Strategic Alignment
- All work tied to business goals
- Clear understanding of "why" tasks exist
- Progress tracked at objective level

### Intelligent Prioritization
- Critical issues fixed before new features
- Objective health drives decisions
- Dependencies respected

### Health Monitoring
- Real-time objective health tracking
- Degrading objectives trigger intervention
- Blocked objectives identified early

### Issue Management
- Centralized issue tracking
- Full lifecycle management
- Priority-based fixing
- Issue correlation

### Progress Visibility
- Clear completion metrics
- Objective-level progress tracking
- Acceptance criteria validation

## Backward Compatibility

The system maintains full backward compatibility:

**Without Objectives:**
- Falls back to tactical decision-making
- Uses task status to select phases
- Works exactly as before

**With Objectives:**
- Uses strategic decision-making
- Objective-driven phase selection
- Enhanced progress tracking

## Migration Guide

### Existing Projects

1. **Continue as-is**: No changes needed, system works in tactical mode
2. **Add objectives gradually**: Create objective files when ready
3. **Full migration**: Define all objectives, link existing tasks

### New Projects

1. **Start with objectives**: Define PRIMARY_OBJECTIVES.md first
2. **Let planning create tasks**: Tasks automatically linked to objectives
3. **Monitor progress**: Track completion at objective level

## Troubleshooting

### Objectives Not Loading

**Problem**: Coordinator not using strategic mode

**Solution**:
1. Check objective files exist (PRIMARY_OBJECTIVES.md, etc.)
2. Verify file format matches template
3. Check logs for parsing errors

### Issues Not Tracked

**Problem**: QA phase not creating Issue objects

**Solution**:
1. Verify coordinator has issue_tracker initialized
2. Check QA phase has access to coordinator
3. Review logs for issue creation messages

### Objective Health Always Healthy

**Problem**: Health analysis not detecting problems

**Solution**:
1. Verify issues are linked to objectives
2. Check task success rates
3. Review objective's task list

## Advanced Features

### Objective Dependencies

Define dependencies between objectives:
```markdown
### Dependencies
- primary_001 (Core Infrastructure)
```

The system will:
- Block dependent objectives until dependencies complete
- Show blocking dependencies in health analysis
- Prevent work on blocked objectives

### Issue Correlation

The IssueTracker automatically correlates related issues:
- Same file: Multiple issues in one file
- Same type: Similar issues across files
- Same function: Issues in related code

### Objective Health Analysis

Health analysis considers:
- Success rate of tasks
- Number of open issues
- Critical issues blocking progress
- Consecutive failures
- Dependency status

## Best Practices

### Defining Objectives

1. **Be Specific**: Clear, measurable objectives
2. **Set Priorities**: Use PRIMARY/SECONDARY/TERTIARY correctly
3. **Define Criteria**: Clear acceptance criteria
4. **Track Dependencies**: Explicit dependency declarations

### Managing Issues

1. **Triage Quickly**: Set correct severity
2. **Link to Objectives**: Always link issues to objectives
3. **Fix Critical First**: Let priority system work
4. **Verify Fixes**: QA verifies resolved issues

### Monitoring Progress

1. **Check Objective Health**: Monitor health status
2. **Track Completion**: Watch completion percentages
3. **Review Issues**: Regular issue review
4. **Validate Criteria**: Check acceptance criteria

## Future Enhancements

### Planned Features

1. **Message Bus**: Structured phase-to-phase communication
2. **Polytopic Integration**: Objectives in 7D space
3. **Advanced Analytics**: Objective completion predictions
4. **Automated Reporting**: Progress reports and dashboards

### Experimental Features

1. **Objective Recommendations**: AI suggests next objectives
2. **Issue Prediction**: Predict issues before they occur
3. **Resource Allocation**: Optimize phase resource usage
4. **Dependency Analysis**: Automatic dependency detection

## Support

For questions or issues:
1. Review this guide
2. Check DEEP_REASSESSMENT_ANALYSIS.md for design details
3. Review FINAL_COMPREHENSIVE_PROPOSAL.md for implementation
4. Check logs for detailed execution information

## References

- **DEEP_REASSESSMENT_ANALYSIS.md**: Complete design analysis
- **FINAL_COMPREHENSIVE_PROPOSAL.md**: Implementation details
- **PRIMARY_OBJECTIVES.md.template**: Objective file template
- **SECONDARY_OBJECTIVES.md.template**: Secondary objectives template
- **TERTIARY_OBJECTIVES.md.template**: Tertiary objectives template