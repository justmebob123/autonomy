# Forced Resolution System Design

## Problem Statement
The AI is currently allowed to:
1. Call only analysis tools (compare_file_implementations) without taking action
2. Skip reading files and just create reports
3. Not check ARCHITECTURE.md before making decisions
4. Give up after 3 attempts without exhausting all analysis options

## Solution: Mandatory Tool Usage Checklist

### Phase 1: Pre-Execution Validation
Before allowing ANY resolving action (merge, report, etc.), the system MUST verify:

1. **File Understanding** - AI MUST have read the target files
   - Required: `read_file` called for each target file
   - Validation: Check tool call history for read_file calls
   - If missing: Force retry with error message

2. **Architecture Check** - AI MUST have checked ARCHITECTURE.md
   - Required: `read_file` called for ARCHITECTURE.md
   - Validation: Check tool call history
   - If missing: Force retry with error message

3. **Comprehensive Analysis** - AI MUST have used appropriate analysis tools
   - For duplicates: MUST call compare_file_implementations
   - For integration conflicts: MUST call analyze_import_impact
   - For complexity: MUST call analyze_complexity
   - Validation: Check tool call history for required tools
   - If missing: Force retry with error message

### Phase 2: Forced Iteration Loop
Instead of allowing 3 attempts with same behavior, force progressive analysis:

**Attempt 1**: Basic analysis
- Allow AI to explore freely
- Track which tools were used

**Attempt 2**: Enforce missing analysis
- If AI didn't read files → Force read_file calls
- If AI didn't check architecture → Force ARCHITECTURE.md read
- Provide specific error: "You MUST read the files before deciding"

**Attempt 3**: Comprehensive analysis required
- Require ALL analysis tools to be used
- Block any resolving action until checklist complete
- Provide checklist: "✓ Read files, ✓ Check architecture, ✗ Compare implementations"

**Attempt 4+**: Guided resolution
- All analysis complete, now MUST take action
- Only allow resolving tools (merge, report, review)
- Block analysis tools (already done)

### Phase 3: Tool Call Validation
Add validation BEFORE executing tool calls:

```python
def validate_tool_calls_before_execution(task, tool_calls, attempt_number):
    """
    Validate that AI has completed required analysis before allowing resolution.
    
    Returns:
        (valid, error_message)
    """
    # Get tool call history for this task
    history = get_tool_history_for_task(task)
    
    # Check if AI is trying to resolve without analysis
    resolving_tools = {"merge_file_implementations", "create_issue_report", "request_developer_review"}
    is_resolving = any(tc["function"]["name"] in resolving_tools for tc in tool_calls)
    
    if is_resolving and attempt_number <= 3:
        # Check required analysis completed
        required_checks = {
            "read_target_files": False,
            "read_architecture": False,
            "compare_implementations": False
        }
        
        # Check history
        for tool_call in history:
            tool_name = tool_call["function"]["name"]
            
            if tool_name == "read_file":
                args = tool_call["function"]["arguments"]
                file_path = args.get("file_path", "")
                
                if any(target in file_path for target in task.target_files):
                    required_checks["read_target_files"] = True
                if "ARCHITECTURE.md" in file_path:
                    required_checks["read_architecture"] = True
            
            if tool_name == "compare_file_implementations":
                required_checks["compare_implementations"] = True
        
        # Check if all required
        missing = [k for k, v in required_checks.items() if not v]
        
        if missing:
            return False, f"ANALYSIS INCOMPLETE. You MUST complete these steps first: {', '.join(missing)}"
    
    return True, None
```

### Phase 4: Mandatory Checklist in Prompt
Update prompt to show checklist and current status:

```
📋 MANDATORY ANALYSIS CHECKLIST (Attempt {attempt}/{max_attempts}):

{checklist_status}

⚠️ You CANNOT create reports or merge files until ALL checklist items are complete!

Current Status:
✓ Read target files: {status}
✓ Read ARCHITECTURE.md: {status}
✓ Compare implementations: {status}
✗ Take resolving action: BLOCKED until above complete

NEXT STEP: {next_required_step}
```

## Implementation Plan

1. Add `TaskAnalysisTracker` class to track tool usage per task
2. Add `validate_tool_calls_before_execution()` to refactoring phase
3. Update `_work_on_task()` to use validation
4. Update `_build_task_prompt()` to include checklist
5. Add forced iteration logic with progressive requirements
6. Test with real tasks

## Expected Behavior

### Before
```
Attempt 1: compare_file_implementations → create_issue_report
Result: ❌ Task failed (didn't read files)

Attempt 2: compare_file_implementations → create_issue_report
Result: ❌ Task failed (still didn't read files)

Attempt 3: compare_file_implementations → create_issue_report
Result: ❌ Max attempts, auto-create report
```

### After
```
Attempt 1: compare_file_implementations → create_issue_report
Result: ❌ BLOCKED - "You MUST read the target files first"

Attempt 2: read_file(file1) → read_file(file2) → compare_file_implementations
Result: ❌ BLOCKED - "You MUST read ARCHITECTURE.md to understand design"

Attempt 3: read_file(ARCHITECTURE.md) → analyze complete
Result: ✅ Checklist complete, now you can take action

Attempt 4: merge_file_implementations OR create_issue_report
Result: ✅ Task resolved with full context
```

## Benefits

1. **Forces comprehensive analysis** - AI cannot skip steps
2. **Prevents lazy reports** - Must understand before documenting
3. **Ensures architecture alignment** - Always checks ARCHITECTURE.md
4. **Progressive guidance** - Each attempt adds more requirements
5. **No infinite loops** - Clear path to resolution
6. **Better decisions** - AI has full context before acting