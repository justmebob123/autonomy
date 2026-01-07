# Root Cause Analysis - Infinite Loop Issue (DEEP ANALYSIS)

## CRITICAL: Focusing on REAL Root Causes, Not Band-Aids

## The Actual Problem from Logs

```
Task: Develop a plan to integrate identified components with existing architecture
Target: architecture/integration_plan.md
Phase: CODING
Model Action: read_file("services/integration_gap_analysis.py")
Result: ❌ File operation failed: (empty error message)
Status: Task FAILED, gets reactivated, repeats 500+ times
```

## Root Cause #1: WRONG PHASE FOR TASK TYPE

### The Problem
A **documentation task** (create markdown plan) is being handled by the **coding phase** (creates Python files).

### Evidence
- Target file: `architecture/integration_plan.md` (MARKDOWN)
- Phase: coding (expects PYTHON files)
- Task description: "Develop a plan..." (PLANNING/DOCUMENTATION task)

### Why This Happens
Looking at the task creation in planning phase:
1. Planning phase creates tasks with various target files
2. No validation that target file type matches phase capabilities
3. Coding phase accepts ANY task with a target file
4. No routing logic based on file extension

### The Real Fix
**Option A**: Documentation phase should handle `.md` files
- Check: Does documentation phase exist and handle markdown?
- Check: Is there routing logic for file extensions?

**Option B**: Coding phase should reject non-Python targets
- Add validation: if target ends with `.md`, reject or redirect
- Return clear error: "This is a documentation task, not a coding task"

**Option C**: Planning phase should route tasks correctly
- When creating tasks, check target file extension
- Route `.md` files to documentation phase
- Route `.py` files to coding phase

## Root Cause #2: MODEL DOESN'T UNDERSTAND WHAT TO CREATE

### The Problem
Model reads a Python file when it should create a markdown file.

### Evidence
- Reads: `services/integration_gap_analysis.py` (Python)
- Should create: `architecture/integration_plan.md` (Markdown)
- No logical connection between input and output

### Why This Happens
Looking at the coding phase prompt:
1. Prompt says "create Python files"
2. Task says "create architecture/integration_plan.md"
3. Model is confused: Python or Markdown?
4. Model defaults to reading related files
5. Never actually creates the target file

### The Real Fix
**Fix the prompt to handle markdown files**:
```python
if task.target_file.endswith('.md'):
    prompt = "Create a markdown document at {target_file}. This is DOCUMENTATION, not code."
else:
    prompt = "Create Python code at {target_file}."
```

OR **Reject markdown files entirely**:
```python
if task.target_file.endswith('.md'):
    return PhaseResult(
        success=False,
        message="Coding phase cannot create markdown files. Route to documentation phase."
    )
```

## Root Cause #3: EMPTY ERROR MESSAGES

### The Problem
When model calls `read_file` but doesn't create files, error message is empty.

### Evidence
```
❌ File operation failed: 
```
(nothing after the colon)

### Why This Happens
1. Model calls `read_file` successfully
2. No files created or modified
3. `handler.errors` is empty (no tool errors)
4. `handler.get_error_summary()` returns empty string
5. Error log shows empty message

### The Real Fix (ALREADY PARTIALLY DONE)
Commit f0b52df added `read_file` to analysis tools list, but we need to verify:
1. Is the fix actually working?
2. Is the error message now clear?
3. Does it prevent the infinite loop?

## Investigation Plan

### Step 1: Check Task Routing
```bash
# Find where tasks are created
grep -r "architecture/integration_plan.md" pipeline/

# Find where phase is selected for tasks
grep -r "def.*select.*phase" pipeline/

# Check if there's file extension routing
grep -r "\.md\|\.py" pipeline/phases/
```

### Step 2: Check Phase Capabilities
```bash
# What does coding phase accept?
grep -r "def run" pipeline/phases/coding.py

# What does documentation phase accept?
grep -r "def run" pipeline/phases/documentation.py

# Is there validation for file types?
grep -r "target_file.*endswith\|file.*extension" pipeline/phases/
```

### Step 3: Check Model Prompts
```bash
# What does coding phase tell the model?
grep -r "system.*prompt\|You are" pipeline/phases/coding.py

# Does it mention markdown files?
grep -r "markdown\|\.md" pipeline/phases/coding.py
```

## What We Should NOT Do

❌ Add failure count limits (hides the problem)
❌ Force phase transitions (masks the issue)  
❌ Add artificial loop breaking (band-aid fix)
❌ Reduce thresholds (doesn't fix root cause)

## What We SHOULD Do

✅ Fix task routing based on file type
✅ Add validation in coding phase for file types
✅ Improve prompts to clarify task requirements
✅ Ensure error messages are always actionable
✅ Add logging to understand task flow

## Next Steps

1. Examine task creation in planning phase
2. Check phase selection logic
3. Verify file type handling in each phase
4. Fix routing or add validation
5. Test with the actual failing task