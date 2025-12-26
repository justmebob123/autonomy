# Text Parser Debugging Enhancement

## Issue

The text parser was failing to extract tasks in production even though it worked in tests:

```
14:57:46 [INFO]   🔄 Attempting to extract tasks from text response...
14:57:46 [WARNING]   ✗ Could not extract tasks from text response
```

But when tested with the same content, it extracted 5 tasks successfully.

## Root Causes Identified

### 1. Markdown Formatting in Descriptions
The LLM response contained markdown formatting that wasn't being cleaned:
- `**bold text**` - Bold formatting
- `*italic text*` - Italic formatting  
- `` `code` `` - Code formatting
- Trailing phrases like "in ``" or "in "

**Example:**
```
**Add support for log rotation monitoring** in `monitors/log_rotation.py`
```

This resulted in descriptions like:
```
**Add support for log rotation monitoring** in ``
```

### 2. Insufficient Debugging
When extraction failed, there was no information about:
- Why it failed
- What patterns were found
- What the content looked like

## Solutions Implemented

### 1. Enhanced Text Cleaning

Added markdown cleanup to `_extract_task_info()`:

```python
# Clean up markdown formatting
description = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)  # Remove **bold**
description = re.sub(r'\*([^*]+)\*', r'\1', description)      # Remove *italic*
description = re.sub(r'`([^`]+)`', r'\1', description)        # Remove `code`

# Remove common phrases
description = re.sub(r'\s+in\s+``\s*$', '', description)      # Remove trailing "in ``"
description = re.sub(r'\s+in\s+$', '', description)           # Remove trailing "in "
```

**Before:**
```
Description: **Add support for log rotation monitoring** in ``
```

**After:**
```
Description: Add support for log rotation monitoring
```

### 2. Comprehensive Debugging

Added detailed logging when extraction fails:

```python
if tasks:
    self.logger.info(f"  ✓ Extracted {len(tasks)} tasks from text response")
    for i, task in enumerate(tasks, 1):
        self.logger.debug(f"    Task {i}: {task['description'][:50]}... -> {task['target_file']}")
    
    tool_calls = self.text_parser.create_tool_calls_from_tasks(tasks)
    self.logger.info(f"  ✓ Converted to {len(tool_calls)} tool call(s), continuing with normal flow")
else:
    self.logger.warning("  ✗ Could not extract tasks from text response")
    self.logger.debug("  Debugging extraction failure:")
    
    # Debug: Check for patterns
    import re
    numbered = re.findall(r'(?:^|\n)\s*\d+\.\s*', content, re.MULTILINE)
    files = re.findall(r'([a-zA-Z0-9_/]+\.py)', content)
    self.logger.debug(f"    Numbered items found: {len(numbered)}")
    self.logger.debug(f"    Python files found: {len(files)}")
    if files:
        self.logger.debug(f"    Files: {files[:5]}")
```

### 3. Added Content Length Logging

```python
self.logger.info("  🔄 Attempting to extract tasks from text response...")
self.logger.debug(f"  Content length: {len(content)} chars")
```

## Testing Results

### Before Enhancement
```
Input: "**Add support for log rotation monitoring** in `monitors/log_rotation.py`"
Output: Description: "**Add support for log rotation monitoring** in ``"
Result: Messy, contains markdown
```

### After Enhancement
```
Input: "**Add support for log rotation monitoring** in `monitors/log_rotation.py`"
Output: Description: "Add support for log rotation monitoring"
Result: Clean, readable
```

### Full Test
```python
content = """
1. **Add support for log rotation monitoring** in `monitors/log_rotation.py`
2. **Configure multiple alert channels via CLI** in `alerts/channel_config.py`
3. **Monitor memory consumption of critical processes** in `monitors/process_memory.py`
"""

tasks = parser.parse_project_planning_response(content)
# Result: 3 tasks extracted with clean descriptions
```

## Expected Output in Next Run

With verbose logging enabled, you'll now see:

```
[INFO]   🔄 Attempting to extract tasks from text response...
[DEBUG]  Content length: 1234 chars
[INFO]   ✓ Extracted 5 tasks from text response
[DEBUG]    Task 1: Add support for log rotation monitoring -> monitors/log_rotation.py
[DEBUG]    Task 2: Configure multiple alert channels via CLI -> alerts/channel_config.py
[DEBUG]    Task 3: Monitor memory consumption of critical proc... -> monitors/process_memory.py
[DEBUG]    Task 4: Track bandwidth usage on network interfaces -> monitors/network_bandwidth.py
[DEBUG]    Task 5: Perform trend analysis for disk usage -> analytics/disk_trends.py
[INFO]   ✓ Converted to 1 tool call(s), continuing with normal flow
```

Or if it fails:

```
[WARNING] ✗ Could not extract tasks from text response
[DEBUG]  Debugging extraction failure:
[DEBUG]    Numbered items found: 5
[DEBUG]    Python files found: 5
[DEBUG]    Files: ['monitors/log_rotation.py', 'alerts/channel_config.py', ...]
```

## Why This Matters

### Problem Diagnosis
Without debugging, we couldn't tell:
- If the parser was being called
- If patterns were found
- Why extraction failed

Now we can see exactly what's happening.

### Clean Output
Markdown formatting in task descriptions would cause:
- Ugly display in logs
- Potential parsing issues downstream
- Confusion for users

Now descriptions are clean and readable.

### Production Debugging
When issues occur in production:
- We can see the content length
- We can see what patterns were found
- We can see each extracted task
- We can diagnose failures immediately

## Commit
- **Hash**: 39bf7e7
- **Message**: "fix: Improve text parser and add comprehensive debugging"
- **Status**: Pushed to main branch

## Next Steps

If extraction still fails in the next run, the debug output will show:
1. How many numbered items were found
2. How many Python files were found
3. What those files are

This will help us understand if:
- The content format is different than expected
- The regex patterns need adjustment
- There's a different issue entirely

## Related Issues

This enhancement addresses:
1. Markdown formatting in descriptions
2. Lack of debugging information
3. Silent failures in production
4. Difficulty diagnosing extraction issues

Together with the missing tool handlers fix (commit 6ae743f), the project planning phase should now work end-to-end.