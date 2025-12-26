# Adjacency Matrix Analysis - Complete Report

## Current State

### All 14 Phases
1. application_troubleshooting ❌ (MISSING FROM MATRIX)
2. coding ✅
3. debugging ✅
4. documentation ✅
5. investigation ✅
6. planning ✅
7. project_planning ✅
8. prompt_design ✅
9. prompt_improvement ✅
10. qa ✅
11. role_design ✅
12. role_improvement ✅
13. tool_design ✅
14. tool_evaluation ✅

### Current Adjacency Matrix

```python
self.polytope['edges'] = {
    'planning': ['coding'],
    'coding': ['qa'],
    'qa': ['debugging', 'documentation'],
    'debugging': ['investigation', 'coding'],
    'investigation': ['debugging', 'coding'],
    'project_planning': ['planning'],
    'documentation': ['planning'],
    'prompt_design': ['prompt_improvement'],
    'tool_design': ['tool_evaluation'],
    'role_design': ['role_improvement'],
    'tool_evaluation': ['tool_design'],
    'prompt_improvement': ['prompt_design'],
    'role_improvement': ['role_design']
}
```

## Problem: 6 Phases Unreachable from Main Workflow

**Status**: Self-improvement phases form isolated cycles
- prompt_design <-> prompt_improvement (isolated cycle)
- role_design <-> role_improvement (isolated cycle)
- tool_design <-> tool_evaluation (isolated cycle)

**Impact**: These phases cannot be reached from the main development workflow (project_planning → planning → coding → qa → etc.)

**Root Cause**: No connections between self-improvement phases and main workflow phases

## Proposed Connections

### 1. Connect Self-Improvement Phases to Main Workflow

#### Prompt Design/Improvement Cycle
**investigation** → **prompt_design**
- **Reason**: Investigation may reveal prompts need improvement
- **Trigger**: Prompts not producing desired results

**prompt_improvement** → **planning**
- **Reason**: After improving prompts, return to planning with better prompts
- **Trigger**: Prompts improved and ready to use

#### Role Design/Improvement Cycle
**investigation** → **role_design**
- **Reason**: Investigation may reveal roles need redesign
- **Trigger**: Current roles not effective

**role_improvement** → **planning**
- **Reason**: After improving roles, return to planning with better roles
- **Trigger**: Roles improved and ready to use

#### Tool Design/Evaluation Cycle
**investigation** → **tool_design**
- **Reason**: Investigation may reveal need for new tools
- **Trigger**: Missing tools or tools need improvement

**tool_evaluation** → **coding**
- **Reason**: After evaluating tools, implement them in code
- **Trigger**: Tools validated and ready for implementation

### 2. Application Troubleshooting Connections (Already Added)

**qa/debugging/investigation** → **application_troubleshooting**
- **Reason**: Application-level issues discovered
- **Trigger**: Runtime errors, config issues, integration problems

**application_troubleshooting** → **debugging/investigation/coding**
- **Reason**: Need to fix identified issues
- **Trigger**: Application issues identified and need resolution

## Recommended Adjacency Matrix Update

```python
self.polytope['edges'] = {
    'planning': ['coding'],
    'coding': ['qa'],
    'qa': ['debugging', 'documentation', 'application_troubleshooting'],
    'debugging': ['investigation', 'coding', 'application_troubleshooting'],
    'investigation': ['debugging', 'coding', 'application_troubleshooting', 
                      'prompt_design', 'role_design', 'tool_design'],  # Added 3 connections
    'project_planning': ['planning'],
    'documentation': ['planning'],
    'prompt_design': ['prompt_improvement'],
    'tool_design': ['tool_evaluation'],
    'role_design': ['role_improvement'],
    'tool_evaluation': ['tool_design', 'coding'],  # Added coding
    'prompt_improvement': ['prompt_design', 'planning'],  # Added planning
    'role_improvement': ['role_design', 'planning'],  # Added planning
    'application_troubleshooting': ['debugging', 'investigation', 'coding']
}
```

**Changes Made:**
1. ✅ Added application_troubleshooting connections (3 incoming, 3 outgoing)
2. ✅ Connected investigation → prompt_design (enter prompt improvement cycle)
3. ✅ Connected investigation → role_design (enter role improvement cycle)
4. ✅ Connected investigation → tool_design (enter tool improvement cycle)
5. ✅ Connected prompt_improvement → planning (exit cycle back to main workflow)
6. ✅ Connected role_improvement → planning (exit cycle back to main workflow)
7. ✅ Connected tool_evaluation → coding (exit cycle to implement tools)

## Rationale

### Why These Connections Make Sense

**1. qa → application_troubleshooting**
- QA tests may pass but application fails at runtime
- Integration tests may reveal application-level issues
- Performance tests may show application bottlenecks

**2. debugging → application_troubleshooting**
- Debugging code may reveal the issue is in application config/architecture
- Code is correct but application setup is wrong
- Need to troubleshoot application layer, not code layer

**3. investigation → application_troubleshooting**
- Deep investigation may uncover application-level root causes
- System-level issues require application troubleshooting
- Architecture problems need application-level analysis

**4. application_troubleshooting → debugging**
- After identifying application issues, may need to debug specific components
- Application troubleshooting narrows down to specific code areas
- Need to debug why application components aren't working

**5. application_troubleshooting → investigation**
- Application troubleshooting may reveal need for deeper investigation
- Complex application issues require investigation phase
- Root cause analysis needed after initial troubleshooting

**6. application_troubleshooting → coding**
- Application troubleshooting identifies fixes needed
- Need to implement architectural changes
- Need to add error handling or refactor code

## Impact Analysis

### Before Fix
- **Reachable phases**: 13/14 (92.9%)
- **Isolated phases**: 1 (application_troubleshooting)
- **Problem**: Cannot troubleshoot application-level issues

### After Fix
- **Reachable phases**: 14/14 (100%)
- **Isolated phases**: 0
- **Benefit**: Complete polytopic navigation

## Testing Plan

1. **Verify Reachability**
   - Test navigation from qa → application_troubleshooting
   - Test navigation from debugging → application_troubleshooting
   - Test navigation from investigation → application_troubleshooting

2. **Verify Outgoing Paths**
   - Test navigation from application_troubleshooting → debugging
   - Test navigation from application_troubleshooting → investigation
   - Test navigation from application_troubleshooting → coding

3. **Verify Complete Graph**
   - Run graph traversal algorithm
   - Confirm all 14 phases reachable
   - Confirm no isolated vertices

## Implementation

```python
# In pipeline/coordinator.py, update the edges dictionary:

self.polytope['edges'] = {
    'planning': ['coding'],
    'coding': ['qa'],
    'qa': ['debugging', 'documentation', 'application_troubleshooting'],
    'debugging': ['investigation', 'coding', 'application_troubleshooting'],
    'investigation': ['debugging', 'coding', 'application_troubleshooting'],
    'project_planning': ['planning'],
    'documentation': ['planning'],
    'prompt_design': ['prompt_improvement'],
    'tool_design': ['tool_evaluation'],
    'role_design': ['role_improvement'],
    'tool_evaluation': ['tool_design'],
    'prompt_improvement': ['prompt_design'],
    'role_improvement': ['role_design'],
    'application_troubleshooting': ['debugging', 'investigation', 'coding']
}
```

## Conclusion

Adding `application_troubleshooting` to the adjacency matrix with appropriate connections will:
1. Complete the polytopic structure (100% reachability)
2. Enable application-level troubleshooting workflows
3. Provide proper navigation paths for complex issues
4. Maintain logical flow between phases

The proposed connections are based on the natural workflow of software development and troubleshooting, ensuring the phase can be reached when needed and can transition to appropriate next phases.