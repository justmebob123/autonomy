# 🚨 CRITICAL INFINITE LOOP BUG FIX

## Problem Analysis

The system is stuck in an infinite loop at iteration 9200+ with this pattern:

```
tool_design fails (no tool name) 
→ force transition to planning
→ detect loop on task 2de01f5b9102
→ suggest tool_design to break loop
→ activate tool_design
→ REPEAT
```

## Root Causes

### 1. Loop Detection Suggests Failing Phase
**Location**: `coordinator.py` line 853-900 (`_detect_failure_loop`)

The logic suggests `tool_design` when it detects 'tool' in error message, but this creates a loop when tool_design itself is the failing phase.

### 2. Tool Design Phase Missing Required Parameter
**Location**: Tool design phase execution

The phase expects `tool_name` parameter but coordinator doesn't provide it when activating specialized phases.

### 3. No Blacklist for Recently Failed Phases
**Location**: `coordinator.py` line 924-943 (`_should_activate_specialized_phase`)

When a specialized phase fails 20+ times, it should be blacklisted temporarily, but there's no such mechanism.

## Solution - EMERGENCY FIX

**DISABLE SPECIALIZED PHASE ACTIVATION ENTIRELY**

This is the fastest way to stop the infinite loop. Specialized phases are causing more harm than good and should only be manually invoked.

```python
def _should_activate_specialized_phase(self, state: PipelineState, last_result) -> Optional[str]:
    # EMERGENCY FIX: Disable specialized phase activation
    # These phases are causing infinite loops and should be manually invoked only
    # TODO: Fix the root causes and re-enable with proper safeguards
    return None
```

## Implementation

Apply this one-line change to `coordinator.py` at line ~924.