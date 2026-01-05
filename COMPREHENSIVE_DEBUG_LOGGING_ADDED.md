# Comprehensive Debug Logging Added - Complete Variable Trace

**Date:** 2026-01-05 02:05:00  
**Issue:** Planning loop - objectives show 0% complete despite 138 tasks existing  
**Solution:** Added comprehensive debug logging to trace EVERY variable transition

---

## Changes Made

### 1. ObjectiveManager.load_objectives() - COMPREHENSIVE TRACE

**File:** `pipeline/objective_manager.py` (lines 232-330)

**Added logging for:**
- **STEP 1:** Inspect `state.objectives` structure BEFORE parsing markdown
  - Shows type, keys, and content of each level
  - Shows task lists for each objective in state
  - Identifies missing keys or wrong types
  
- **STEP 2:** Parse markdown files
  - Shows how many objectives parsed from each file
  - Shows initial task lists (should be empty from markdown)
  
- **STEP 3:** Merge task lists from state
  - For EACH objective:
    - Shows before/after merge
    - Checks if level exists in state
    - Checks if obj_id exists in state
    - Shows state_obj type and keys
    - Shows tasks list type, length, and content
    - Shows successful merge or failure reason

**Output format:**
```
================================================================================
🔍 LOAD_OBJECTIVES() - COMPREHENSIVE TRACE
================================================================================

📊 STEP 1: Inspecting state.objectives structure
   state.objectives type: <class 'dict'>
   state.objectives keys: ['primary', 'secondary', 'tertiary']
   
   Level 'primary':
      Type: <class 'dict'>
      Count: 3 objectives
      
      Objective 'primary_002':
         Type: <class 'dict'>
         Keys: ['id', 'title', 'tasks', 'total_tasks']
         tasks type: <class 'list'>
         tasks length: 120
         tasks content: ['task_001', 'task_002', ...]

================================================================================
📄 STEP 2: Parsing markdown files
================================================================================
   Parsing primary objectives from PRIMARY_OBJECTIVES.md
   ✓ Parsed 3 objectives
      primary_002: tasks=[] (length: 0)

================================================================================
🔀 STEP 3: Merging task lists from state
================================================================================
   🎯 Processing primary objective: primary_002
      Before merge: obj.tasks = [] (length: 0)
      ✓ Level 'primary' found in state.objectives
      ✓ ID 'primary_002' found in state.objectives[primary]
      state_obj type: <class 'dict'>
      state_obj keys: ['id', 'title', 'tasks', 'total_tasks']
      ✓ 'tasks' key found
      tasks type: <class 'list'>
      tasks length: 120
      tasks content: ['task_001', 'task_002', ...]
      ✅ After merge: obj.tasks = ['task_001', ...] (length: 120)

================================================================================
✅ LOAD_OBJECTIVES() COMPLETE
================================================================================
```

---

### 2. PlanningPhase - Task Linking Debug Logging

**File:** `pipeline/phases/planning.py` (lines 348-375)

**Added logging for:**
- When linking task to objective
- Creating new objective entry in state
- Before/after state.objectives dict update
- Before/after objective object update

**Output format:**
```
🔗 Linking task task_139 to objective primary_002
   Creating new objective entry in state.objectives[primary][primary_002]
   Before: state.objectives[primary][primary_002]['tasks'] = ['task_001', ...]
   Created empty tasks list
   ✅ Added task to STATE: state.objectives[primary][primary_002]['tasks'] = ['task_001', ..., 'task_139']
   Before: objective.tasks = ['task_001', ...]
   ✅ Added task to OBJECT: objective.tasks = ['task_001', ..., 'task_139']
```

---

### 3. StateManager.save() - Save Verification

**File:** `pipeline/state/manager.py` (lines 752-785)

**Added logging for:**
- Complete state.objectives structure BEFORE saving to disk
- Shows task counts for each objective
- Shows actual task IDs being saved

**Output format:**
```
================================================================================
💾 SAVING STATE - OBJECTIVES STRUCTURE
================================================================================
   primary: 3 objectives
      primary_002: 120 tasks
         Task IDs: ['task_001', 'task_002', 'task_003', 'task_004', 'task_005']
   secondary: 2 objectives
      secondary_001: 15 tasks
         Task IDs: ['task_121', 'task_122', ...]
================================================================================
```

---

## What This Will Reveal

### Scenario 1: Tasks Not Being Saved to State
**Symptoms:**
- Planning phase shows: "✅ Added task to STATE"
- StateManager.save() shows: "primary_002: 0 tasks"

**Root Cause:** Task list not persisting to state dict

---

### Scenario 2: Tasks Lost During Load
**Symptoms:**
- StateManager shows: "primary_002: 120 tasks" (saved correctly)
- load_objectives() STEP 1 shows: "primary_002: 0 tasks" (lost on load)

**Root Cause:** State deserialization issue

---

### Scenario 3: Merge Logic Failing
**Symptoms:**
- load_objectives() STEP 1 shows: "primary_002: 120 tasks" (state has data)
- load_objectives() STEP 3 shows: "✗ 'tasks' key NOT FOUND" (merge fails)

**Root Cause:** Merge logic not finding tasks in state

---

### Scenario 4: Wrong Objective Being Used
**Symptoms:**
- load_objectives() shows: "primary_002: 120 tasks" (merge succeeds)
- get_objective_action() shows: "Objective.tasks list: 0 task IDs" (wrong object)

**Root Cause:** Coordinator using different objective instance

---

## Expected Output

When user runs the pipeline, they will see:

1. **At startup:** Complete state.objectives structure from disk
2. **During planning:** Task linking operations with before/after states
3. **After planning:** State save with complete objectives structure
4. **Next iteration:** Complete load_objectives trace showing merge process
5. **In coordinator:** get_objective_action showing final objective state

This will pinpoint EXACTLY where task lists are being lost.

---

## Files Modified

1. `pipeline/objective_manager.py` - Added 80 lines of debug logging
2. `pipeline/phases/planning.py` - Added 20 lines of debug logging
3. `pipeline/state/manager.py` - Added 20 lines of debug logging

**Total:** 120 lines of comprehensive debug logging

---

## Next Steps

1. User runs pipeline with these changes
2. Examine output to identify exact failure point
3. Implement targeted fix based on findings
4. Remove debug logging once issue is resolved

---

## Status

✅ All debug logging added  
✅ Covers complete variable lifecycle  
✅ Traces every state transition  
✅ Ready for testing