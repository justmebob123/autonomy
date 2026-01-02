# Critical Fixes Action Plan

Based on the comprehensive polytopic analysis, here are the critical fixes needed:

## PRIORITY 1: SYNTAX ERROR (BLOCKING ALL ANALYSIS)

### Issue
```
File: app/models/recommendation.py
Line: 30
Error: unterminated f-string literal
```

### Impact
- Blocks all Python AST analysis tools
- Prevents complexity analysis
- Prevents dead code detection
- Prevents bug detection
- Prevents anti-pattern detection

### Solution
Fix the unterminated f-string in the web project.

---

## PRIORITY 2: MISSING METHOD (RUNTIME ERROR)

### Issue
```
File: app/api/v1/recommendations.py:35
Error: Recommendation.to_dict does not exist
```

### Impact
- Runtime error when API endpoint is called
- Prevents recommendation retrieval

### Solution
Implement the `to_dict()` method in the Recommendation model.

---

## PRIORITY 3: TOOL SELECTION PATTERN

### Issue
AI consistently reads files but doesn't use resolution tools.

### Root Cause Analysis
1. **Prompt Weakness**: Current prompts don't explicitly require resolution
2. **Validation Logic**: Completion detection is too strict
3. **Tool Guidance**: No progressive tool suggestions

### Solution Components

#### A. Enhanced Step-Aware Prompts
```python
def _get_integration_conflict_prompt(self, task, state):
    # Check completed steps
    if not tracker.has_completed_checkpoint("read_target_files"):
        return "STEP 1: Read both conflicting files using read_file tool"
    
    if not tracker.has_completed_checkpoint("compare_implementations"):
        return "STEP 2: Compare implementations using compare_file_implementations tool"
    
    if not tracker.has_completed_checkpoint("merge_files"):
        return "STEP 3: CRITICAL - You MUST use merge_file_implementations tool NOW"
    
    return "STEP 4: Mark task complete using mark_task_complete tool"
```

#### B. Tool Requirement Enforcement
```python
# Add to task validation
REQUIRED_TOOLS_BY_TYPE = {
    RefactoringIssueType.CONFLICT: [
        "read_file",
        "compare_file_implementations", 
        "merge_file_implementations",
        "mark_task_complete"
    ],
    RefactoringIssueType.DUPLICATE: [
        "read_file",
        "compare_file_implementations",
        "merge_file_implementations",
        "mark_task_complete"
    ]
}
```

#### C. Completion Validation Enhancement
```python
def _validate_task_completion(self, task, tool_calls):
    """Validate that task used required resolution tools."""
    required_tools = REQUIRED_TOOLS_BY_TYPE.get(task.issue_type, [])
    used_tools = [call['tool'] for call in tool_calls]
    
    # Check if resolution tool was used
    resolution_tools = ["merge_file_implementations", "move_file", "create_issue_report"]
    has_resolution = any(tool in used_tools for tool in resolution_tools)
    
    if not has_resolution:
        return False, "No resolution tool used"
    
    # Check if completion tool was used
    if "mark_task_complete" not in used_tools:
        return False, "Task not marked complete"
    
    return True, "Task completed successfully"
```

---

## PRIORITY 4: TASK ANALYSIS TRACKER IMPROVEMENTS

### Current Issues
1. Checkpoints not properly tracked
2. Tool call history not used for guidance
3. No progressive escalation

### Enhancements Needed

#### A. Checkpoint System
```python
class AnalysisCheckpoint:
    """Enhanced checkpoint with validation."""
    name: str
    description: str
    required_tool: str  # NEW: Tool that completes this checkpoint
    completed: bool = False
    completed_at: Optional[datetime] = None
    
    def validate_completion(self, tool_name: str) -> bool:
        """Check if tool completes this checkpoint."""
        return tool_name == self.required_tool
```

#### B. Progressive Guidance
```python
def get_next_guidance(self, task_id: str, attempt: int) -> str:
    """Get progressively stronger guidance based on attempt."""
    state = self.get_or_create_state(task_id)
    
    if attempt == 1:
        return "Analyze the conflict and determine resolution approach"
    elif attempt == 2:
        return "You've analyzed. Now use resolution tools to fix the issue"
    elif attempt == 3:
        return "CRITICAL: Use merge_file_implementations or create_issue_report NOW"
    else:
        return "ESCALATION: This task may require manual intervention"
```

---

## PRIORITY 5: REFACTORING PHASE ENHANCEMENTS

### A. Auto-Resolution for Simple Cases
```python
def _attempt_auto_resolution(self, task):
    """Attempt automatic resolution for simple cases."""
    if task.issue_type == RefactoringIssueType.DEAD_CODE:
        # Can automatically remove dead code
        return self._auto_remove_dead_code(task)
    
    if task.issue_type == RefactoringIssueType.DUPLICATE:
        # Check if files are identical
        if self._files_are_identical(task.target_files):
            return self._auto_merge_identical_files(task)
    
    return None  # Requires AI intervention
```

### B. Task Prioritization
```python
def _select_next_task(self, manager):
    """Select next task with intelligent prioritization."""
    pending = [t for t in manager.tasks.values() if t.status == TaskStatus.NEW]
    
    # Priority 1: Syntax errors (block everything)
    syntax_errors = [t for t in pending if "syntax" in t.title.lower()]
    if syntax_errors:
        return syntax_errors[0]
    
    # Priority 2: Missing methods (runtime errors)
    missing_methods = [t for t in pending if "missing method" in t.title.lower()]
    if missing_methods:
        return missing_methods[0]
    
    # Priority 3: Integration conflicts (block development)
    conflicts = [t for t in pending if t.issue_type == RefactoringIssueType.CONFLICT]
    if conflicts:
        return conflicts[0]
    
    # Priority 4: Duplicates (code quality)
    duplicates = [t for t in pending if t.issue_type == RefactoringIssueType.DUPLICATE]
    if duplicates:
        return duplicates[0]
    
    # Priority 5: Everything else
    return pending[0] if pending else None
```

---

## IMPLEMENTATION SEQUENCE

### Phase 1: Critical Fixes (Immediate)
1. Fix syntax error in recommendation.py
2. Implement Recommendation.to_dict() method
3. Test that analysis tools work

### Phase 2: Prompt Enhancements (High Priority)
1. Implement enhanced step-aware prompts
2. Add tool requirement enforcement
3. Improve completion validation

### Phase 3: Tracker Improvements (Medium Priority)
1. Enhance checkpoint system
2. Add progressive guidance
3. Implement tool call validation

### Phase 4: Phase Enhancements (Low Priority)
1. Add auto-resolution for simple cases
2. Improve task prioritization
3. Add escalation mechanisms

---

## TESTING STRATEGY

### Test 1: Syntax Error Fix
```bash
cd ~/code/AI/web
python -m py_compile app/models/recommendation.py
```

### Test 2: Analysis Tools
```bash
cd ~/code/AI/autonomy_intelligence
python -c "
from pipeline.handlers import ToolCallHandler
handler = ToolCallHandler('/home/logan/code/AI/web')
result = handler._handle_analyze_complexity({})
print('Success!' if result['success'] else 'Failed')
"
```

### Test 3: Task Completion
```bash
# Run pipeline and verify tasks complete
python run.py -vv ../web/
# Check that tasks progress beyond "read files"
```

---

## SUCCESS CRITERIA

1. ✅ No syntax errors in web project
2. ✅ All analysis tools execute successfully
3. ✅ Tasks progress through all checkpoints
4. ✅ Tasks use resolution tools
5. ✅ Tasks marked complete successfully
6. ✅ Refactoring phase completes without infinite loops

---

## MONITORING

### Key Metrics
- Task completion rate
- Average attempts per task
- Tool usage patterns
- Checkpoint completion rates
- Error frequencies

### Alerts
- Task stuck after 5 attempts
- No resolution tool used after 3 attempts
- Same error repeated 3 times
- Analysis tool failures

---

## ROLLBACK PLAN

If issues occur:
1. Revert to previous commit
2. Disable refactoring phase temporarily
3. Fix issues in isolation
4. Re-enable with monitoring

---

## NEXT STEPS

1. **Immediate**: Fix syntax error in web project
2. **Today**: Implement missing method
3. **This Week**: Enhance prompts and validation
4. **Next Week**: Improve tracker and phase logic