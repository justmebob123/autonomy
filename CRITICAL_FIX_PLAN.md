# Critical Fix Plan - Tool Call Extraction

## Root Cause Analysis

The AI **IS** returning valid tool calls, but the parser is failing to extract them. Here's what's happening:

### What the AI Returns:
```json
{
  "name": "modify_python_file",
  "arguments": {
    "filepath": "src/ui/pipeline_ui.py",
    "original_code": "curses.cbreak()",
    "new_code": "if self.stdscr:\n    curses.cbreak()"
  }
}
```

### Why It Fails:
1. The response is wrapped in markdown code blocks: ` ```json ... ``` `
2. The `_try_standard_json` method looks for `{"name": ..., "arguments": ...}` but doesn't strip markdown first
3. The `_clean_json` method exists but is only called AFTER the regex match succeeds
4. The regex fails because it's matching against the markdown-wrapped text

## The Fix

### 1. Strip Markdown Code Blocks FIRST
Before any parsing attempts, strip markdown code blocks from the content.

### 2. Remove Non-Tool-Supporting Models from Fallbacks
Models returning HTTP 400 "does not support tools":
- phi4:latest
- deepseek-coder-v2:latest  
- deepseek-coder-v2:16b

### 3. Increase Timeouts
- Current: 180s for retries
- Needed: 600s (10 minutes) for CPU inference on ollama01

## Implementation Steps

1. Fix `_try_standard_json` to clean markdown BEFORE regex matching
2. Update fallback model list in config.py
3. Increase retry timeout from 180s to 600s
4. Add better logging to show what's being parsed

## Expected Outcome

After these fixes:
✅ Tool calls will be extracted from markdown-wrapped JSON
✅ No more HTTP 400 errors from unsupported models
✅ Sufficient time for CPU inference
✅ The curses error will actually get fixed!