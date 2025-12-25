# FIX ALL INTEGRATION GAPS - COMPLETE PLAN

## User Requirement
"FUCKING UPDATE ALL CODE TO THE NEW DESIGN" - NOT backward compatibility, FULL INTEGRATION

## Execution Plan

### STEP 1: DELETE DEAD CODE ✅
- Delete pipeline/agents.py (315 lines of unused code)

### STEP 2: FIX DOCUMENTATION PHASE
**File:** pipeline/phases/documentation.py

**Changes:**
1. Import ToolCallHandler
2. Replace manual tool processing (lines 70-110) with:
   ```python
   handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
   results = handler.process_tool_calls(tool_calls)
   ```
3. Add loop detection mixin
4. Replace hardcoded SYSTEM_PROMPTS with prompt_registry lookup

### STEP 3: FIX PROJECT_PLANNING PHASE
**File:** pipeline/phases/project_planning.py

**Changes:**
1. Import ToolCallHandler
2. Replace manual tool processing (lines 90-150) with ToolCallHandler
3. Add loop detection mixin
4. Replace hardcoded SYSTEM_PROMPTS with prompt_registry lookup

### STEP 4: FIX ALL PHASES - PROMPT REGISTRY
**Files:** coding.py, debugging.py, planning.py, qa.py, documentation.py, project_planning.py

**Changes for EACH file:**
```python
# Add method to BasePhase or each phase:
def _get_system_prompt(self, phase_name: str) -> str:
    """Get system prompt from registry or fallback to hardcoded"""
    custom_prompt = self.prompt_registry.get_prompt(f"{phase_name}_system")
    if custom_prompt:
        self.logger.debug(f"  Using custom prompt for {phase_name}")
        return custom_prompt
    return SYSTEM_PROMPTS[phase_name]

# Replace all:
{"role": "system", "content": SYSTEM_PROMPTS["phase_name"]}

# With:
{"role": "system", "content": self._get_system_prompt("phase_name")}
```

### STEP 5: ADD LOOP DETECTION TO ALL PHASES
**Files:** documentation.py, project_planning.py, prompt_design.py, tool_design.py, role_design.py, prompt_improvement.py, tool_evaluation.py, role_improvement.py

**Changes for EACH file:**
1. Import LoopDetectionMixin
2. Add mixin to class definition
3. Add __init__ with action_tracker initialization
4. Add track_tool_calls() after each tool execution
5. Add check_for_loops() before each iteration

## IMPLEMENTATION ORDER

1. Delete agents.py (1 file)
2. Fix documentation.py (4 changes)
3. Fix project_planning.py (4 changes)
4. Add _get_system_prompt() to base.py (1 change)
5. Update 6 phases to use _get_system_prompt() (6 files)
6. Add loop detection to 8 phases (8 files)

**Total:** 20 files to modify
**Estimated Time:** 30-45 minutes
**Impact:** 100% integration with new self-designing system