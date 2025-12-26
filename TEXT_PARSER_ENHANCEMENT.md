# Text Parser Enhancement - Task Extraction Without File Paths

## Problem

The text parser was failing to extract tasks from model responses that didn't include explicit file paths. This occurred with models like qwen2.5:32b that generate high-level strategic task descriptions.

### Example Response Format
```
### Propose Expansion Tasks

Here are 3-5 focused tasks:

1. **Implement Advanced Alerting Rules**: Develop more sophisticated alerting rules...
2. **Enhance Security Monitoring**: Add additional security checks...
3. **Optimize Performance Metrics Collection**: Refine the performance metrics...
```

### Previous Parser Limitations
The parser expected one of these patterns:
- `1. Description in file.py` (file path in same line)
- `Task: X\nFile: file.py` (explicit Task/File labels)
- `file.py - Description` (file path first)

**Result**: Parser failed because no file paths were present in the response.

## Solution

Enhanced the text parser with intelligent file path inference:

### 1. New Method: `_extract_task_without_file()`
- Extracts task information even when no file path is present
- Handles markdown formatting (`**bold**`, `*italic*`, `` `code` ``)
- Splits on colon to separate task name from description
- Infers appropriate file path based on task content

### 2. New Method: `_infer_file_path()`
Intelligently maps task descriptions to appropriate file paths based on keywords:

| Keywords | Inferred Path |
|----------|---------------|
| alert, alerting, notification | `monitors/alerting.py` |
| security, threat, vulnerability | `monitors/security.py` |
| performance, metric, optimize | `monitors/performance.py` |
| dashboard, ui, interface, web | `ui/dashboard.py` |
| integration, external, api | `integrations/external.py` |
| log, logging | `utils/logging.py` |
| config, configuration | `config/settings.py` |
| test, testing | `tests/test_new_feature.py` |
| monitor, monitoring | `monitors/system.py` |
| (default) | `features/new_feature.py` |

### 3. Enhanced `parse_project_planning_response()`
- First tries to extract with explicit file path
- Falls back to extraction without file path if needed
- Maintains backward compatibility with existing patterns

## Results

### Test with Actual Response
```python
✓ Extracted 5 tasks:

1. Develop more sophisticated alerting rules...
   File: monitors/alerting.py
   Category: feature
   Priority: 50

2. Add additional security checks and integrate...
   File: monitors/security.py
   Category: refactor
   Priority: 50

3. Refine the performance metrics collection...
   File: monitors/performance.py
   Category: refactor
   Priority: 50

4. Create a web-based dashboard...
   File: ui/dashboard.py
   Category: feature
   Priority: 50

5. Establish integrations with external systems...
   File: integrations/external.py
   Category: feature
   Priority: 50

✓ Created 1 tool call(s)
   Tool: propose_expansion_tasks
   Tasks in call: 5
```

## Benefits

1. **Model Flexibility**: Works with models that generate natural language responses
2. **Strategic Thinking**: Allows models to focus on high-level task descriptions
3. **Intelligent Inference**: Maps tasks to appropriate file locations automatically
4. **Backward Compatible**: Still works with explicit file paths when provided
5. **Robust Parsing**: Handles various markdown formatting styles

## Impact

This enhancement enables the system to work with a wider range of language models, including those that prefer generating natural language descriptions over structured formats. The intelligent file path inference ensures tasks are still properly organized and actionable.

## Commit

- **Hash**: c247439
- **Message**: "feat: Improve text parser to handle tasks without explicit file paths"
- **Files Changed**: `pipeline/text_tool_parser.py`
- **Lines Added**: +72
- **Lines Removed**: -2