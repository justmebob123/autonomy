# CRITICAL INTEGRATION AUDIT

## User Requirement
"FUCKING UPDATE ALL CODE TO THE NEW DESIGN" - NOT maintain backward compatibility, FULLY INTEGRATE.

## New Design Components (Self-Designing AI System)
1. **PromptArchitect** - AI designs custom prompts
2. **ToolDesigner** - AI creates custom tools  
3. **RoleCreator** - AI designs specialist roles
4. **LoopDetector** - Detects and breaks infinite loops
5. **TeamOrchestrator** - Coordinates parallel specialists across servers
6. **Self-Improvement** - AI evaluates and improves its own creations

## CRITICAL FINDINGS - OLD CODE NEVER UPDATED

### pipeline/agents.py - COMPLETELY OUTDATED ❌

**Problem:** This file contains OLD agent classes (PlanningAgent, CodingAgent, QAAgent, DebugAgent) that:
1. ❌ Do NOT use tool_registry
2. ❌ Do NOT use prompt_registry  
3. ❌ Do NOT use role_registry
4. ❌ Do NOT use loop detection
5. ❌ Do NOT use team orchestration
6. ❌ Create ToolCallHandler WITHOUT registries (4 locations)
7. ❌ Use hardcoded SYSTEM_PROMPTS instead of prompt_registry
8. ❌ Use hardcoded get_tools_for_phase() instead of custom tools

**Lines with Issues:**
- Line 91: handler = ToolCallHandler(self.project.project_dir) - NO tool_registry
- Line 178: handler = ToolCallHandler(self.project.project_dir) - NO tool_registry
- Line 244: handler = ToolCallHandler(self.project.project_dir) - NO tool_registry
- Line 312: handler = ToolCallHandler(self.project.project_dir) - NO tool_registry
- Line 31-36: BaseAgent.__init__ does NOT accept registries
- Line 69: Uses SYSTEM_PROMPTS["planning"] instead of prompt_registry
- Line 70: Uses get_planning_prompt() instead of custom prompts
- Line 75: Uses get_tools_for_phase() instead of tool_registry

**Impact:** These old agents are COMPLETELY BYPASSING the new self-designing system!

**Status:** ✅ GOOD NEWS - These agents are NOT USED anywhere in the codebase!
- No imports of PlanningAgent, CodingAgent, QAAgent, DebugAgent found
- The new Phase-based system (planning.py, coding.py, qa.py, debugging.py) is being used instead
- **ACTION:** DELETE pipeline/agents.py entirely - it's dead code

### Checking All Phase Files for Registry Integration

**Phase Integration Status:**

✅ **base.py** - Initializes all 3 registries (lines 88-93)
✅ **coding.py** - Uses tool_registry (line 122)
✅ **debugging.py** - Uses all 3 registries (lines 124, 126, 151, 379, 575)
✅ **investigation.py** - Uses tool_registry (line 96)
✅ **planning.py** - Uses tool_registry (line 80)
✅ **qa.py** - Uses tool_registry (line 122)
✅ **prompt_design.py** - Uses tool_registry and prompt_registry (lines 67, 130, 157, 217-218)
✅ **tool_design.py** - Uses tool_registry (lines 68, 131, 173, 235-236)
✅ **role_design.py** - Uses tool_registry and role_registry (lines 69, 132, 171, 233-234)

❌ **documentation.py** - Does NOT use ToolCallHandler at all (processes tool calls manually)
❌ **project_planning.py** - Does NOT use ToolCallHandler at all (processes tool calls manually)

### Critical Finding: Two Phases NOT Using ToolCallHandler

**Problem:** documentation.py and project_planning.py process tool calls manually instead of using ToolCallHandler.

**Impact:**
- These phases CANNOT use custom tools from tool_registry
- They bypass the entire tool registration system
- They use hardcoded tool processing logic

**Lines to Check:**
- documentation.py: Lines 70-110 (manual tool call processing)
- project_planning.py: Lines 90-150 (manual tool call processing)

### Critical Finding: ALL Phases Using Hardcoded SYSTEM_PROMPTS

**Problem:** ALL phases use `SYSTEM_PROMPTS["phase_name"]` instead of checking prompt_registry first.

**Files Using Hardcoded Prompts (13 locations):**
1. pipeline/agents.py - 4 locations (but this file is unused dead code)
2. pipeline/phases/coding.py - Line 1 location
3. pipeline/phases/debugging.py - 4 locations
4. pipeline/phases/documentation.py - 1 location
5. pipeline/phases/planning.py - 1 location
6. pipeline/phases/project_planning.py - 1 location
7. pipeline/phases/qa.py - 1 location

**Impact:**
- Custom prompts from PromptArchitect are NEVER USED
- prompt_registry.get_prompt() is only called in debugging.py (line 151) but AFTER hardcoded prompt already used
- The entire PromptArchitect system is bypassed

**What Should Happen:**
```python
# WRONG (current):
{"role": "system", "content": SYSTEM_PROMPTS["debugging"]}

# RIGHT (should be):
system_prompt = self.prompt_registry.get_prompt("debugging_system") or SYSTEM_PROMPTS["debugging"]
{"role": "system", "content": system_prompt}
```

## SUMMARY OF CRITICAL INTEGRATION GAPS

### 1. Dead Code - DELETE
- ❌ **pipeline/agents.py** - 315 lines of unused old agent code

### 2. Missing ToolCallHandler Integration
- ❌ **documentation.py** - Manual tool processing (lines 70-110)
- ❌ **project_planning.py** - Manual tool processing (lines 90-150)

### 3. Missing prompt_registry Integration  
- ❌ **coding.py** - Uses hardcoded SYSTEM_PROMPTS
- ❌ **debugging.py** - Uses hardcoded SYSTEM_PROMPTS (4 locations)
- ❌ **documentation.py** - Uses hardcoded SYSTEM_PROMPTS
- ❌ **planning.py** - Uses hardcoded SYSTEM_PROMPTS
- ❌ **project_planning.py** - Uses hardcoded SYSTEM_PROMPTS
- ❌ **qa.py** - Uses hardcoded SYSTEM_PROMPTS

### 4. Missing Loop Detection Integration
- ❌ **documentation.py** - No loop detection
- ❌ **project_planning.py** - No loop detection
- ❌ **prompt_design.py** - No loop detection
- ❌ **tool_design.py** - No loop detection
- ❌ **role_design.py** - No loop detection
- ❌ **prompt_improvement.py** - No loop detection
- ❌ **tool_evaluation.py** - No loop detection
- ❌ **role_improvement.py** - No loop detection

## TOTAL INTEGRATION GAPS: 20+ locations need fixing