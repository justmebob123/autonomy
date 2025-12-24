# Verbosity Levels in Debug/QA Mode

## Overview

The debug/QA mode now supports three verbosity levels that control how much detail is shown about AI activities. This gives you fine-grained control over the amount of information displayed.

## Verbosity Levels

### Level 0: Normal (Default)
**Usage**: No flag needed (default behavior)

**What You See**:
- Tool name with emoji icon
- Primary argument (file path, pattern, etc.)
- Minimal, clean output

**Example**:
```
🔧 [AI Activity] Modifying file: src/example.py
📖 [AI Activity] Reading file: src/utils.py
🔍 [AI Activity] Searching code: class MyClass
📁 [AI Activity] Listing directory: src/
```

**When to Use**:
- Normal operation
- When you just want to know what files are being worked on
- When you trust the AI and don't need details

---

### Level 1: Verbose (`-v`)
**Usage**: Add `-v` flag

**What You See**:
- Everything from Level 0
- Operation type and details
- Code previews (first 60 characters)
- Search patterns and file patterns

**Example**:
```
🔧 [AI Activity] Modifying file: src/example.py
   └─ Operation: str_replace
   └─ Replacing: def old_function():\n    pass...
   └─ With: def new_function():\n    return True...

🔍 [AI Activity] Searching code: class MyClass
   └─ Pattern: class MyClass
   └─ Files: **/*.py
```

**When to Use**:
- When you want to understand what changes are being made
- When debugging why certain fixes aren't working
- When learning how the AI approaches problems
- When you need more context but not overwhelming detail

---

### Level 2: Very Verbose (`-vv`)
**Usage**: Add `-vv` flag (or `-v -v`)

**What You See**:
- Everything from Level 1
- Full arguments in tree format
- Complete code snippets (not truncated)
- All parameters passed to tools

**Example**:
```
🔧 [AI Activity] Modifying file: src/example.py
   └─ Operation: str_replace
   └─ Replacing: def old_function():\n    pass...
   └─ With: def new_function():\n    return True...
   └─ Full arguments:
      ├─ file_path: src/example.py
      ├─ operation: str_replace
      ├─ old_str: def old_function():
    pass
      ├─ new_str: def new_function():
    return True
```

**When to Use**:
- When debugging complex issues
- When you need to see exactly what the AI is doing
- When reporting bugs or issues
- When you want maximum transparency

---

## Activity Log File

Regardless of verbosity level, all activities are logged to `ai_activity.log` in the project directory.

### Log File Format

```
[2024-01-15T12:30:45.123456] MODIFY: src/example.py (str_replace)
     OLD: def old_function():
     NEW: def new_function():

[2024-01-15T12:30:46.234567] READ: src/utils.py

[2024-01-15T12:30:47.345678] SEARCH: class MyClass in **/*.py
```

### Log File Features

- **Timestamped**: Every entry has ISO format timestamp
- **Persistent**: Survives across runs (appends, doesn't overwrite)
- **Gitignored**: Won't be committed to version control
- **Structured**: Easy to parse and analyze
- **Complete**: Contains all AI activities regardless of console verbosity

### Viewing the Log File

```bash
# View in real-time
tail -f <project>/ai_activity.log

# View full history
cat <project>/ai_activity.log

# Search for specific activities
grep "MODIFY" <project>/ai_activity.log

# Count activities by type
grep -o "^\[.*\] [A-Z]*" <project>/ai_activity.log | cut -d' ' -f2 | sort | uniq -c
```

---

## Command Examples

### Normal Verbosity
```bash
python3 run.py --debug-qa \
  --follow ../my_project/.autonomous_logs/autonomous.log \
  --command "./autonomous ../my_project/" \
  ../test-automation/
```

### Verbose Mode
```bash
python3 run.py --debug-qa -v \
  --follow ../my_project/.autonomous_logs/autonomous.log \
  --command "./autonomous ../my_project/" \
  ../test-automation/
```

### Very Verbose Mode
```bash
python3 run.py --debug-qa -vv \
  --follow ../my_project/.autonomous_logs/autonomous.log \
  --command "./autonomous ../my_project/" \
  ../test-automation/
```

---

## Choosing the Right Verbosity Level

| Scenario | Recommended Level | Reason |
|----------|------------------|---------|
| Normal operation | 0 (default) | Clean, minimal output |
| Learning how AI works | 1 (`-v`) | See reasoning without overwhelming detail |
| Debugging AI behavior | 2 (`-vv`) | Full transparency |
| Reporting issues | 2 (`-vv`) | Provide complete context |
| Long-running tasks | 0 (default) | Reduce log clutter |
| Quick fixes | 1 (`-v`) | Balance between detail and brevity |

---

## Technical Details

### Implementation

- Verbosity is controlled by `PipelineConfig.verbose` (int: 0, 1, or 2)
- Passed to `ToolCallHandler` during initialization
- Each tool formats output based on verbosity level
- Console output and log file are independent

### Performance Impact

- **Level 0**: Minimal overhead
- **Level 1**: Slight overhead for string formatting
- **Level 2**: Moderate overhead for tree formatting
- **Log File**: Minimal overhead (async writes)

All levels are suitable for production use.

---

## Related Documentation

- `AI_ACTIVITY_LOGGING.md` - Overview of activity logging system
- `PROCESS_CLEANUP_FIX.md` - Process cleanup improvements
- `DEBUG_QA_MODE.md` - Debug/QA mode overview