# CRITICAL BUG: Tool Call Parser Cannot Handle List Arguments

## The Problem

The AI is stuck in an infinite loop because the tool call parser cannot extract list arguments:

**AI Output:**
```python
merge_file_implementations(
    source_files=["services/resource_estimator.py", "core/resource/resource_estimator.py"],
    target_file="services/resource_estimator.py",
    strategy="ai_merge"
)
```

**What Gets Parsed:**
```python
{
    "target_file": "services/resource_estimator.py",
    "strategy": "ai_merge"
    # source_files is MISSING!
}
```

**Result:**
```
KeyError: 'source_files'
```

## Root Cause

File: `pipeline/client.py`
Method: `_extract_function_call_syntax()`

The argument parser regex only handles string values:

```python
arg_pattern = r'(\w+)\s*=\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'|"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')\'
```

This matches:
- ✅ `key="value"`
- ✅ `key='value'`
- ✅ `key="""value"""`
- ❌ `key=[...]` (LISTS NOT SUPPORTED!)
- ❌ `key={...}` (DICTS NOT SUPPORTED!)

## Impact

**Affected Tools:**
- `merge_file_implementations` (requires `source_files` list)
- `cleanup_redundant_files` (requires `files` list)
- `restructure_directory` (requires `moves` list)
- Any tool with list or dict parameters

**Current Behavior:**
1. AI outputs correct tool call with list parameter
2. Parser extracts only string parameters
3. Tool execution fails with KeyError
4. Task marked as failed
5. System creates issue report and moves on
6. Next iteration: Analysis runs again, creates same tasks
7. Infinite loop of analysis → tasks → failures → analysis

## The Fix Needed

The parser needs to handle list and dict arguments. Options:

### Option 1: Enhanced Regex (Complex)
Add patterns to match lists and dicts

### Option 2: AST Parsing (Robust)
Use Python's ast.parse() to properly parse function calls

### Option 3: JSON Format (Simple)
Tell AI to output JSON format instead of Python syntax

### Option 4: Hybrid (Best)
Try JSON first, fall back to enhanced parsing

## Immediate Workaround

Tell the AI to use JSON format in prompts:

```
OUTPUT FORMAT:
{
    "name": "merge_file_implementations",
    "arguments": {
        "source_files": ["file1.py", "file2.py"],
        "target_file": "file1.py",
        "strategy": "ai_merge"
    }
}
```

## Why 12 Tasks Keep Appearing

1. Analysis runs, creates 63 tasks
2. AI works on tasks, but merge operations fail (parser bug)
3. Tasks marked as FAILED
4. When all pending tasks are done, analysis runs AGAIN
5. Creates same 63 tasks (duplicates, conflicts, etc.)
6. Loop repeats

The system is designed to re-analyze when no pending tasks remain, but it's not checking if tasks were already created for the same issues.

## Multiple Bugs Cascading

1. **Parser bug**: Can't extract list arguments
2. **Validation bug**: Still applying wrong requirements (my fix didn't work)
3. **Task deduplication bug**: Re-creates same tasks every analysis
4. **Prompt bug**: AI not told to use JSON format

All four need to be fixed for the system to work.