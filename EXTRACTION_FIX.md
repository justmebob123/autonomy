# Tool Call Extraction Fix

## Issue Discovered During Testing

When running the pipeline, the AI was correctly formatting tool calls as Python function syntax:
```python
create_issue_report(
    task_id="refactor_0294",
    severity="low",
    impact_analysis="...",
    ...
)
```

But the system reported:
```
🔧 Tool calls: None
⚠️  Task refactor_0294 failed: No tool calls
```

## Root Cause

The `_extract_function_call_syntax` method in `pipeline/client.py` only checked for 7 hardcoded tool names:
```python
known_tools = [
    'modify_python_file', 'create_python_file', 'create_file',
    'read_file', 'search_code', 'list_directory', 'report_issue'
]
```

It was missing:
- `create_issue_report` ❌
- `request_developer_review` ❌
- `merge_file_implementations` ❌
- `cleanup_redundant_files` ❌
- All other refactoring tools ❌

## Solution Implemented

### 1. Pattern-Based Extraction
Changed from hardcoded list to pattern matching:
```python
# Match any valid Python function name followed by opening parenthesis
tool_pattern = r'([a-z_][a-z0-9_]*)\s*\('
matches = re.finditer(tool_pattern, text)
potential_tools = [m.group(1) for m in matches]
```

### 2. Prioritized Tool List
Added all refactoring tools to priority list:
```python
known_tools = [
    'create_issue_report', 'request_developer_review', 
    'merge_file_implementations', 'cleanup_redundant_files',
    'compare_file_implementations', 'detect_duplicate_implementations',
    'modify_python_file', 'create_python_file', 'create_file',
    'read_file', 'search_code', 'list_directory', 'report_issue',
    'move_file', 'rename_file', 'restructure_directory'
]
```

### 3. Fallback to Any Tool
```python
# Check known tools first, then any other potential tools
tools_to_check = known_tools + [t for t in potential_tools if t not in known_tools]
```

## Expected Behavior After Fix

### Before:
```
AI: create_issue_report(task_id="...", severity="low", ...)
System: 🔧 Tool calls: None
Result: ❌ Task failed: No tool calls
```

### After:
```
AI: create_issue_report(task_id="...", severity="low", ...)
System: 🔧 Tool calls: 1
System: 🔧 EXECUTING TOOL: create_issue_report
Result: ✅ Tool executed successfully
```

## Files Modified

- `pipeline/client.py` - Enhanced `_extract_function_call_syntax` method
- `todo.md` - Added Phase 9 tracking

## Commit Information

**Commit**: f571878
**Message**: "fix: Expand tool call extraction to include all refactoring tools"
**Pushed**: ✅ Yes

## Testing Recommendation

Run the pipeline again:
```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

Expected results:
- ✅ Tool calls extracted from text responses
- ✅ create_issue_report executes successfully
- ✅ Tasks complete or fail with proper tool execution
- ✅ No more "No tool calls" errors

## Related Issues Fixed

This fix addresses the same class of issues as the previous fixes:
1. **Bug #1**: KeyError: 'impact_analysis' - Parameter mismatch
2. **Bug #2**: Unknown tool 'unknown' - Malformed tool call structure
3. **Bug #3**: Tool call extraction failure - Missing tools in extraction list ← **THIS FIX**

All three bugs were preventing the refactoring phase from working correctly.