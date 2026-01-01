# Critical Fix: read_file Parameter Mismatch

## Problem Identified

The AI was experiencing infinite loops and task failures with the error:
```
❌ Result: FAILED
⚠️  Error: No filepath provided
```

## Root Cause

**Parameter Name Mismatch:**
- **Tool Schema Definition**: Expects parameter named `filepath` (no underscore)
- **AI Calling Convention**: Was using `file_path` (with underscore)
- **Handler Implementation**: Only checked for `filepath`

Example of failing call:
```json
{"name": "read_file", "arguments": {"file_path": "visualization/chart_generator.py"}}
```

The handler would receive `{"file_path": "..."}` but only looked for `args.get("filepath")`, resulting in empty string and "No filepath provided" error.

## Solution Implemented

Added backward compatibility to accept both parameter names:

```python
def _handle_read_file(self, args: Dict) -> Dict:
    """Handle read_file tool - read a file from the project."""
    # Accept both 'filepath' and 'file_path' for backward compatibility
    filepath = args.get("filepath") or args.get("file_path", "")
    
    if not filepath:
        return {"tool": "read_file", "success": False, "error": "No filepath provided"}
```

## Impact

### Before Fix
- ❌ Task refactor_0402: Failed 28 times with "No filepath provided"
- ❌ Task refactor_0403: Failed 2 times with "No filepath provided"
- ❌ Task refactor_0404: Failed 2 times with "No filepath provided"
- ❌ All tasks creating issue reports instead of resolving
- ❌ Infinite loop of failures

### After Fix
- ✅ AI can use either `filepath` or `file_path` parameter
- ✅ Tasks will successfully read files
- ✅ Refactoring can proceed normally
- ✅ No more parameter mismatch errors

## Why This Happened

The AI model learned to use `file_path` (with underscore) from:
1. Common Python naming conventions (snake_case)
2. Other tools that might use `file_path`
3. Natural language understanding of "file path" as two words

The tool schema correctly defined `filepath` (no underscore), but the AI's natural tendency was to use the underscored version.

## Prevention

This type of issue can be prevented by:
1. **Parameter Aliases**: Always accept common variations of parameter names
2. **Validation Testing**: Test tools with both expected and common variations
3. **Clear Documentation**: Document exact parameter names in prompts
4. **Error Messages**: Include expected parameter names in error messages

## Files Modified

- `pipeline/handlers.py` - Added backward compatibility for `file_path` parameter

## Commit

- **Hash**: 6739854
- **Message**: "fix: Add backward compatibility for read_file parameter (filepath vs file_path)"
- **Status**: Pushed to GitHub

## Testing

To verify the fix works:
```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

Expected behavior:
- AI calls `read_file` with either `filepath` or `file_path`
- Both parameter names work correctly
- Files are read successfully
- Tasks complete without "No filepath provided" errors