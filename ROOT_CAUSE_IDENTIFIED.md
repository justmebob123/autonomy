# ROOT CAUSE IDENTIFIED - Parallel Objective Systems

**Date:** 2026-01-05 02:15:00  
**Issue:** Planning loop caused by TWO separate objective selection systems

---

## 🔥 THE ACTUAL PROBLEM

There are **TWO SEPARATE OBJECTIVE SELECTION SYSTEMS** that are NOT synchronized:

### System 1: PolytopicManager (Coordinator)
**Location:** `pipeline/coordinator.py` line 1777

```python
def _determine_next_action_strategic(self, state: PipelineState) -> Dict:
    # Load objectives into polytopic space
    objectives_by_level = self.objective_manager.load_objectives(state)
    
    # Use 7D navigation to find optimal objective
    optimal_objective = self.objective_manager.find_optimal_objective(state)
    
    # Returns optimal_objective based on 7D dimensional space
```

**This selects:** The objective with best dimensional profile (complexity, risk, readiness)

### System 2: Planning Phase (kwargs)
**Location:** `pipeline/phases/planning.py` line 189

```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # Check if we have an active objective (strategic mode)
    objective = kwargs.get('objective')
    if objective:
        self.logger.info(f"  🎯 Planning for objective: {objective.title}")
```

**This uses:** Whatever objective is passed in kwargs from coordinator

---

## 📊 WHAT THE LOGS SHOW

### Iteration 1:
```
🎯 Optimal objective (7D selection): Success Criteria (primary_003)
   Planning for objective: Success Criteria
   🔗 Linking task 075b6693dce7 to objective primary_003
   ✅ Added task to STATE: primary_003['tasks'] = ['075b6693dce7', ...]
   ✅ Added task to OBJECT: objective.tasks = ['075b6693dce7', ...]
```
**Result:** Tasks added to primary_003 ✅

### Iteration 2:
```
🎯 Optimal objective (7D selection): Architectural Changes Needed (secondary_001)
   Planning for objective: Architectural Changes Needed
   🔍 Checking objective 'Architectural Changes Needed' (ID: secondary_001)
      Objective.tasks list: 0 task IDs  ← EMPTY!
```
**Result:** Coordinator selected secondary_001 (which has NO tasks) ❌

---

## 🎯 WHY THIS HAPPENS

**The coordinator's 7D selection algorithm picks different objectives each iteration:**

1. **Iteration 1:** Picks primary_003 (Success Criteria)
   - Planning adds 3 tasks to primary_003
   - primary_003 now has 3 tasks

2. **Iteration 2:** Picks secondary_001 (Architectural Changes Needed)
   - Why? Because dimensional profile changed:
     - primary_003 now has tasks (less "ready")
     - secondary_001 has 0 tasks (more "ready")
   - Planning tries to add tasks to secondary_001
   - But secondary_001 has 0 tasks, so it looks like it needs more

3. **Iteration 3:** Might pick primary_001 or primary_002
   - Keeps cycling through objectives
   - Never finishes any of them

---

## 🔧 THE FIX

**Option 1: Stick with ONE objective until complete**

```python
def _determine_next_action_strategic(self, state: PipelineState) -> Dict:
    # Check if we have an IN-PROGRESS objective
    in_progress_objective = self._get_in_progress_objective(state)
    
    if in_progress_objective:
        # Continue with current objective until complete
        optimal_objective = in_progress_objective
    else:
        # Only select new objective if none in progress
        optimal_objective = self.objective_manager.find_optimal_objective(state)
```

**Option 2: Only select objectives with existing tasks**

```python
def find_optimal_objective(self, state: PipelineState) -> Optional[Objective]:
    # Filter to objectives that have tasks
    objectives_with_tasks = [
        obj for obj in all_objectives 
        if len(obj.tasks) > 0
    ]
    
    if not objectives_with_tasks:
        # No objectives have tasks yet - pick any
        return self._select_by_dimensional_profile(all_objectives)
    
    # Only consider objectives with tasks
    return self._select_by_dimensional_profile(objectives_with_tasks)
```

**Option 3: Mark objective as "active" and stick with it**

```python
class Objective:
    status: str  # "pending", "active", "completed"

def _determine_next_action_strategic(self, state: PipelineState) -> Dict:
    # Find active objective
    active_objective = self._get_active_objective(state)
    
    if not active_objective:
        # Select new objective and mark as active
        optimal_objective = self.objective_manager.find_optimal_objective(state)
        optimal_objective.status = "active"
    else:
        # Continue with active objective
        optimal_objective = active_objective
```

---

## 🎯 RECOMMENDED FIX

**Use Option 3 (Mark as active)** because:
1. Clear state management (pending → active → completed)
2. Prevents objective switching mid-work
3. Allows explicit completion before moving on
4. Matches user's mental model

---

## 📝 IMPLEMENTATION

1. Add `status` field to Objective class (if not present)
2. Modify `_determine_next_action_strategic()` to:
   - Check for active objective first
   - Only select new objective if none active
   - Mark selected objective as active
3. Add completion logic:
   - When objective reaches 80%+ completion
   - Mark as "completed"
   - Select next objective

---

## ✅ EXPECTED RESULT

**After fix:**
```
Iteration 1: Select primary_003, mark as ACTIVE
Iteration 2: Continue with primary_003 (still ACTIVE)
Iteration 3: Continue with primary_003 (still ACTIVE)
...
Iteration N: primary_003 reaches 80% → mark COMPLETED
Iteration N+1: Select secondary_001, mark as ACTIVE
```

**No more objective switching!**

---

## 🚨 CRITICAL INSIGHT

This is NOT a bug in the code logic - it's a **design flaw** in the objective selection algorithm.

The 7D dimensional space is WORKING AS DESIGNED - it's selecting the "optimal" objective based on dimensional profile. But "optimal" changes every iteration as tasks are added, causing constant switching.

**The fix is to add PERSISTENCE** - once an objective is selected, stick with it until complete.