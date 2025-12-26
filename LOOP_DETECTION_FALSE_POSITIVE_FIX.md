# Loop Detection False Positive Fix

## CRITICAL ISSUE

Loop detection system is **incorrectly flagging normal coding work as a loop**, blocking all development!

### User Report

> "Oh for fucks sake, why does it think coding is a loop?! ITS SUPPOSED TO LOOP. THATS WORKING ON MULTIPLE FILES."

### What's Happening

```
Iteration 1: Coding → Creates syntax_validator.py ✅
  → Loop detector: "PATTERN REPETITION DETECTED" ❌
  
Iteration 2: Coding → Creates config_loader.py ✅
  → Loop detector: "PATTERN REPETITION DETECTED" ❌
  
Iteration 3: Coding → Creates import_validator.py ✅
  → Loop detector: "LOOP DETECTED - USER INTERVENTION REQUIRED" ❌
  
System: BLOCKED from continuing development!
```

## Root Causes

### 1. Action History Persists Across Runs
```python
# In loop_detection_mixin.py
history_file=logs_dir / "action_history.jsonl"
```

**Problem**: Action history is saved to file and loaded on next run
- Old actions from previous debug phase still in history
- Loop detector sees "debug:unknown" actions from days ago
- Thinks current coding phase is repeating those old actions

### 2. No Phase-Specific History
All phases share the same action history file:
- Coding phase actions mixed with debug phase actions
- QA phase actions mixed with documentation actions
- Loop detector can't distinguish between phases

### 3. Wrong Loop Detection Logic for Coding
Coding phase **SHOULD** repeat actions:
- Create file 1
- Create file 2
- Create file 3
- ...

This is **NORMAL DEVELOPMENT**, not a loop!

### 4. "unknown()" Tool Calls
Loop detector seeing "unknown()" tool calls:
```
Pattern: unknown() -> unknown()
Cycles: 10
```

These are likely from:
- Old action history
- Improperly tracked tool calls
- Missing tool names

## Solutions

### Solution 1: Clear Action History on Fresh Start (CRITICAL)

When starting a new run, clear old action history:

```python
# In loop_detection_mixin.py
def init_loop_detection(self):
    """Initialize loop detection system"""
    logs_dir = self.project_dir / ".autonomous_logs"
    logs_dir.mkdir(exist_ok=True)
    
    history_file = logs_dir / "action_history.jsonl"
    
    # CLEAR old history on initialization
    if history_file.exists():
        # Archive old history
        archive_file = logs_dir / f"action_history_{int(time.time())}.jsonl"
        history_file.rename(archive_file)
        self.logger.info(f"Archived old action history to {archive_file.name}")
    
    # Create fresh action tracker
    self.action_tracker = ActionTracker(history_file=history_file)
    ...
```

### Solution 2: Phase-Specific Loop Detection

Different phases need different loop detection rules:

```python
# In pattern_detector.py
def detect_all_loops(self) -> List[LoopDetection]:
    """Run all loop detection algorithms"""
    
    # Get current phase from recent actions
    recent = self.tracker.get_recent_actions(5)
    current_phase = recent[-1].phase if recent else 'unknown'
    
    # CODING PHASE: Only detect if SAME file modified repeatedly
    if current_phase == 'coding':
        return self.detect_coding_loops()
    
    # QA PHASE: Only detect if no files to review repeatedly
    elif current_phase == 'qa':
        return self.detect_qa_loops()
    
    # DOCUMENTATION PHASE: Only detect if no updates repeatedly
    elif current_phase == 'documentation':
        return self.detect_documentation_loops()
    
    # Other phases: Use standard detection
    else:
        return self._detect_standard_loops()

def detect_coding_loops(self) -> List[LoopDetection]:
    """Detect loops specific to coding phase"""
    detections = []
    
    recent = self.tracker.get_recent_actions(20)
    coding_actions = [a for a in recent if a.phase == 'coding']
    
    # Only flag if SAME file modified 5+ times
    file_modifications = defaultdict(int)
    for action in coding_actions:
        if action.file_path and action.tool in ['str_replace', 'full_file_rewrite']:
            file_modifications[action.file_path] += 1
    
    for file_path, count in file_modifications.items():
        if count >= 5:
            detections.append(LoopDetection(
                loop_type='coding_loop',
                severity='high',
                description=f'Same file modified {count} times: {file_path}',
                evidence=[f'File: {file_path}', f'Modifications: {count}'],
                suggestion='File being modified repeatedly. Check if changes are effective.',
                actions_involved=[]
            ))
    
    return detections
```

### Solution 3: Disable Loop Detection for Normal Coding

Coding phase creating multiple files is **NOT a loop**:

```python
# In loop_detection_mixin.py
def check_for_loops(self) -> Optional[Dict]:
    """Check for loops and intervene if necessary"""
    
    # CODING PHASE: Only check for same-file loops
    if self.phase_name == 'coding':
        # Get recent actions for this phase
        recent = self.action_tracker.get_recent_actions(10)
        coding_actions = [a for a in recent if a.phase == 'coding']
        
        # Check if working on different files (NORMAL)
        files = set(a.file_path for a in coding_actions if a.file_path)
        if len(files) > 1:
            # Working on multiple files = NORMAL DEVELOPMENT
            return None
        
        # Only check for loops if working on SAME file repeatedly
        if len(files) == 1:
            same_file_actions = [a for a in coding_actions if a.file_path == list(files)[0]]
            if len(same_file_actions) >= 5:
                # Same file modified 5+ times = potential loop
                return self.loop_intervention.check_and_intervene()
        
        return None
    
    # Other phases: Use standard loop detection
    return self.loop_intervention.check_and_intervene()
```

### Solution 4: Fix "unknown()" Tool Tracking

Ensure tool names are properly tracked:

```python
# In loop_detection_mixin.py
def track_tool_calls(self, tool_calls: List[Dict], results: List[Dict], agent: str = "main"):
    """Track tool calls for loop detection"""
    for tool_call, result in zip(tool_calls, results):
        # FIX: Ensure tool name is never "unknown"
        tool_name = tool_call.get('tool') or tool_call.get('name') or 'unspecified_tool'
        
        # Don't track if tool name is still unknown
        if tool_name in ['unknown', 'unspecified_tool']:
            self.logger.warning(f"Skipping tracking of unknown tool: {tool_call}")
            continue
        
        args = tool_call.get('args', {})
        
        # Extract file path
        file_path = args.get('file_path') or args.get('filepath')
        
        # Track the action
        self.action_tracker.track_action(
            phase=self.phase_name,
            agent=agent,
            tool=tool_name,
            args=args,
            result=result,
            file_path=file_path,
            success=result.get('success', False)
        )
```

## Implementation Priority

### IMMEDIATE (Blocks all development)
1. **Disable loop detection for coding phase when working on different files**
2. **Clear action history on initialization**

### HIGH (Prevents false positives)
3. **Add phase-specific loop detection**
4. **Fix "unknown()" tool tracking**

### MEDIUM (Improves accuracy)
5. **Add same-file detection for coding loops**
6. **Archive old history instead of deleting**

## Testing

After implementing:

```bash
# Test 1: Multiple file creation (should NOT trigger loop)
python3 run.py /path/to/project
# Expected: Creates file1, file2, file3 without loop warnings

# Test 2: Same file modification (should trigger loop after 5 times)
# Manually modify same file 5+ times
# Expected: Loop warning after 5th modification

# Test 3: Fresh start (should have clean history)
python3 run.py /path/to/project --fresh
# Expected: No old actions in history
```

## User Impact

**Before Fix**:
- ❌ System blocks after creating 3 files
- ❌ False positive loop warnings
- ❌ Cannot continue development
- ❌ User frustrated: "why does it think coding is a loop?!"

**After Fix**:
- ✅ System continues creating files
- ✅ Only warns on actual loops (same file 5+ times)
- ✅ Normal development proceeds
- ✅ User happy: coding works as expected

## Critical Quote

> "ITS SUPPOSED TO LOOP. THATS WORKING ON MULTIPLE FILES."

User is 100% correct. Coding phase creating multiple files is **NORMAL BEHAVIOR**, not a loop!