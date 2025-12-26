# Polytopic Navigation Paths - Complete Documentation

## Overview
This document maps all navigation paths through the 14-phase hyperdimensional polytope structure.

## Entry Point
**project_planning** - The primary entry point for all workflows

## Complete Adjacency Matrix

```python
edges = {
    'planning': ['coding'],
    'coding': ['qa'],
    'qa': ['debugging', 'documentation', 'application_troubleshooting'],
    'debugging': ['investigation', 'coding', 'application_troubleshooting'],
    'investigation': ['debugging', 'coding', 'application_troubleshooting', 
                      'prompt_design', 'role_design', 'tool_design'],
    'project_planning': ['planning'],
    'documentation': ['planning'],
    'prompt_design': ['prompt_improvement'],
    'tool_design': ['tool_evaluation'],
    'role_design': ['role_improvement'],
    'tool_evaluation': ['tool_design', 'coding'],
    'prompt_improvement': ['prompt_design', 'planning'],
    'role_improvement': ['role_design', 'planning'],
    'application_troubleshooting': ['debugging', 'investigation', 'coding']
}
```

## Navigation Paths by Workflow

### 1. Main Development Workflow
**Path**: project_planning → planning → coding → qa → documentation → planning
**Purpose**: Standard development cycle
**Phases**: 5
```
project_planning
    ↓
planning
    ↓
coding
    ↓
qa
    ↓
documentation
    ↓
planning (cycle back)
```

### 2. Debugging Workflow
**Path**: qa → debugging → investigation → coding
**Purpose**: Fix bugs and issues
**Phases**: 4
```
qa
    ↓
debugging
    ↓
investigation
    ↓
coding (fix implementation)
```

### 3. Application Troubleshooting Workflow
**Path**: qa → application_troubleshooting → investigation → coding
**Purpose**: Fix application-level issues
**Phases**: 4
```
qa
    ↓
application_troubleshooting
    ↓
investigation
    ↓
coding (implement fixes)
```

### 4. Prompt Improvement Workflow
**Path**: investigation → prompt_design → prompt_improvement → planning
**Purpose**: Improve system prompts
**Phases**: 4
```
investigation (identify prompt issues)
    ↓
prompt_design
    ↓
prompt_improvement
    ↓
planning (use improved prompts)
```

### 5. Role Improvement Workflow
**Path**: investigation → role_design → role_improvement → planning
**Purpose**: Improve system roles
**Phases**: 4
```
investigation (identify role issues)
    ↓
role_design
    ↓
role_improvement
    ↓
planning (use improved roles)
```

### 6. Tool Development Workflow
**Path**: investigation → tool_design → tool_evaluation → coding
**Purpose**: Create and validate new tools
**Phases**: 4
```
investigation (identify tool needs)
    ↓
tool_design
    ↓
tool_evaluation
    ↓
coding (implement tools)
```

## Phase-by-Phase Navigation

### project_planning
**Outgoing**: planning
**Incoming**: none (entry point)
**Purpose**: Plan project expansion
**Next Steps**: Always goes to planning

### planning
**Outgoing**: coding
**Incoming**: project_planning, documentation, prompt_improvement, role_improvement
**Purpose**: Plan specific tasks
**Next Steps**: Goes to coding to implement

### coding
**Outgoing**: qa
**Incoming**: planning, debugging, investigation, tool_evaluation, application_troubleshooting
**Purpose**: Implement code
**Next Steps**: Goes to qa for testing

### qa
**Outgoing**: debugging, documentation, application_troubleshooting
**Incoming**: coding
**Purpose**: Test and validate
**Next Steps**: 
- debugging (if bugs found)
- documentation (if tests pass)
- application_troubleshooting (if app-level issues)

### debugging
**Outgoing**: investigation, coding, application_troubleshooting
**Incoming**: qa, investigation, application_troubleshooting
**Purpose**: Fix bugs
**Next Steps**:
- investigation (if root cause unclear)
- coding (if fix identified)
- application_troubleshooting (if app-level issue)

### investigation
**Outgoing**: debugging, coding, application_troubleshooting, prompt_design, role_design, tool_design
**Incoming**: debugging, application_troubleshooting
**Purpose**: Deep analysis
**Next Steps**: Routes to appropriate phase based on findings

### application_troubleshooting
**Outgoing**: debugging, investigation, coding
**Incoming**: qa, debugging, investigation
**Purpose**: Fix application-level issues
**Next Steps**:
- debugging (specific component issues)
- investigation (complex root causes)
- coding (implement fixes)

### documentation
**Outgoing**: planning
**Incoming**: qa
**Purpose**: Document features
**Next Steps**: Returns to planning for next cycle

### prompt_design
**Outgoing**: prompt_improvement
**Incoming**: investigation, prompt_improvement
**Purpose**: Design new prompts
**Next Steps**: Goes to prompt_improvement for refinement

### prompt_improvement
**Outgoing**: prompt_design, planning
**Incoming**: prompt_design
**Purpose**: Refine prompts
**Next Steps**:
- prompt_design (iterate)
- planning (use improved prompts)

### role_design
**Outgoing**: role_improvement
**Incoming**: investigation, role_improvement
**Purpose**: Design new roles
**Next Steps**: Goes to role_improvement for refinement

### role_improvement
**Outgoing**: role_design, planning
**Incoming**: role_design
**Purpose**: Refine roles
**Next Steps**:
- role_design (iterate)
- planning (use improved roles)

### tool_design
**Outgoing**: tool_evaluation
**Incoming**: investigation, tool_evaluation
**Purpose**: Design new tools
**Next Steps**: Goes to tool_evaluation for validation

### tool_evaluation
**Outgoing**: tool_design, coding
**Incoming**: tool_design
**Purpose**: Validate tools
**Next Steps**:
- tool_design (iterate)
- coding (implement validated tools)

## Shortest Paths from Entry Point

From **project_planning** to each phase:

| Target Phase | Shortest Path | Distance |
|--------------|---------------|----------|
| planning | project_planning → planning | 1 |
| coding | project_planning → planning → coding | 2 |
| qa | project_planning → planning → coding → qa | 3 |
| debugging | project_planning → planning → coding → qa → debugging | 4 |
| documentation | project_planning → planning → coding → qa → documentation | 4 |
| application_troubleshooting | project_planning → planning → coding → qa → application_troubleshooting | 4 |
| investigation | project_planning → planning → coding → qa → debugging → investigation | 5 |
| prompt_design | project_planning → planning → coding → qa → debugging → investigation → prompt_design | 6 |
| role_design | project_planning → planning → coding → qa → debugging → investigation → role_design | 6 |
| tool_design | project_planning → planning → coding → qa → debugging → investigation → tool_design | 6 |
| prompt_improvement | project_planning → planning → coding → qa → debugging → investigation → prompt_design → prompt_improvement | 7 |
| role_improvement | project_planning → planning → coding → qa → debugging → investigation → role_design → role_improvement | 7 |
| tool_evaluation | project_planning → planning → coding → qa → debugging → investigation → tool_design → tool_evaluation | 7 |

## Cycles in the Graph

### Self-Improvement Cycles
1. **Prompt Cycle**: prompt_design ↔ prompt_improvement
2. **Role Cycle**: role_design ↔ role_improvement
3. **Tool Cycle**: tool_design ↔ tool_evaluation

### Main Workflow Cycles
1. **Development Cycle**: planning → coding → qa → documentation → planning
2. **Debug Cycle**: debugging ↔ investigation
3. **Troubleshooting Cycle**: debugging ↔ application_troubleshooting

## Critical Hubs (High Connectivity)

### investigation (6 outgoing edges)
**Most connected phase** - Routes to:
- debugging, coding, application_troubleshooting (main workflow)
- prompt_design, role_design, tool_design (self-improvement)

**Role**: Central decision point for routing to appropriate improvement or fix workflow

### coding (5 incoming edges)
**Most incoming connections** - Receives from:
- planning (normal flow)
- debugging, investigation (fixes)
- tool_evaluation (tool implementation)
- application_troubleshooting (app fixes)

**Role**: Central implementation point for all code changes

## Reachability Matrix

All phases reachable from project_planning: ✅ 14/14 (100%)

```
✅ project_planning → planning (1 hop)
✅ project_planning → coding (2 hops)
✅ project_planning → qa (3 hops)
✅ project_planning → debugging (4 hops)
✅ project_planning → documentation (4 hops)
✅ project_planning → application_troubleshooting (4 hops)
✅ project_planning → investigation (5 hops)
✅ project_planning → prompt_design (6 hops)
✅ project_planning → role_design (6 hops)
✅ project_planning → tool_design (6 hops)
✅ project_planning → prompt_improvement (7 hops)
✅ project_planning → role_improvement (7 hops)
✅ project_planning → tool_evaluation (7 hops)
```

## Graph Properties

- **Vertices**: 14
- **Directed Edges**: 28
- **Average Out-Degree**: 2.00
- **Maximum Out-Degree**: 6 (investigation)
- **Maximum In-Degree**: 5 (coding)
- **Strongly Connected Components**: 3 (main workflow + 3 self-improvement cycles)
- **Diameter**: 7 (longest shortest path)
- **Density**: 0.154 (28 edges out of 182 possible)

## Usage Recommendations

### For Standard Development
Start: project_planning → planning → coding → qa → documentation

### For Bug Fixing
Enter: qa → debugging → investigation → coding

### For Application Issues
Enter: qa → application_troubleshooting → investigation → coding

### For System Improvement
Enter: investigation → [prompt_design | role_design | tool_design]

### For Iterative Refinement
Use cycles: design ↔ improvement → planning

## Conclusion

The polytopic structure is now complete with 100% reachability. All 14 phases are accessible from the entry point (project_planning), and the graph supports multiple workflows including development, debugging, troubleshooting, and self-improvement.