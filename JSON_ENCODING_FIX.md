# JSON Encoding Protocol Fix

## Problem Description

The autonomy system was experiencing systematic corruption of Python code during bidirectional communication through JSON. This manifested as "unexpected character after line continuation character" syntax errors across hundreds of files.

### Root Cause

The issue was in `pipeline/client.py` in the `_convert_python_strings_to_json()` method:

**BEFORE (Broken):**
```python
def replace_triple_quotes(match):
    content = match.group(1)
    content = content.replace('\\', '\\\\')
    content = content.replace('"', r'&quot;')  # ❌ WRONG! HTML entity instead of JSON escape
    content = content.replace('\n', '\\n')
    # ...
    return f'"{content}"'
```

**Problem:** The code was using HTML entity `&quot;` instead of proper JSON escape sequence `&quot;` for quotes. This caused:
1. Quotes in Python code to be replaced with `&quot;`
2. When combined with backslashes (common in Python), this created malformed syntax
3. The reverse operation couldn't properly decode the content

### Impact

This affected:
- All Python code transmitted through the LLM API
- File creation and modification operations
- Code with backslashes (`\n`, `\t`, `\\`, regex patterns, Windows paths, etc.)
- Code with quotes in strings
- Docstrings and multi-line strings

### Solution

**AFTER (Fixed):**
```python
def replace_triple_quotes(match):
    content = match.group(1)
    # Use json.dumps to properly escape the content
    # This handles all special characters correctly
    import json
    return json.dumps(content)
```

**Benefits:**
1. Uses Python's built-in `json.dumps()` which handles ALL special characters correctly
2. Proper JSON escaping for quotes: `"` → `&quot;`
3. Correct handling of backslashes: `\` → `\\`
4. Handles all edge cases (newlines, tabs, unicode, etc.)

## Test Results

Created comprehensive test suite (`test_json_encoding_fix.py`) with 6 test cases:

| Test Case | OLD (HTML entities) | NEW (JSON escaping) |
|-----------|---------------------|---------------------|
| Simple string with backslash-n | ✓ Pass | ✓ Pass |
| Docstring with quotes | ✗ Fail | ✓ Pass |
| Code with multiple backslashes | ✓ Pass | ✓ Pass |
| Mixed special characters | ✓ Pass | ✓ Pass |
| Python code with continuation | ✗ Fail | ✓ Pass |
| Regex pattern with backslashes | ✗ Fail | ✓ Pass |

**Results:**
- OLD version: 3/6 tests passed (50%)
- NEW version: 6/6 tests passed (100%)

## Files Modified

1. **pipeline/client.py**
   - Line ~1054-1062: Fixed `_convert_python_strings_to_json()` method
   - Line ~1029: Fixed decoding to use `&quot;` instead of `&quot;`

## Verification

To verify the fix works:

```bash
cd autonomy
python3 test_json_encoding_fix.py
```

Expected output: All 6 tests should pass with the NEW version.

## Migration Notes

### For Existing Corrupted Files

Files that were already corrupted with `&quot;` entities will need to be regenerated or manually fixed. The corruption pattern looks like:

```python
# Corrupted (OLD):
print(&quot;Hello World&quot;)

# Correct (NEW):
print("Hello World")
```

### For Future Development

- Always use `json.dumps()` for encoding Python code into JSON strings
- Never use HTML entities (`&quot;`, `&amp;`, etc.) in JSON
- Test with code containing backslashes and quotes
- Verify bidirectional encoding/decoding works correctly

## Related Issues

This fix resolves:
- ✓ "unexpected character after line continuation character" errors
- ✓ Syntax errors in generated Python files
- ✓ Corruption of code with backslashes
- ✓ Corruption of code with quotes
- ✓ Integration conflicts caused by malformed code

## Technical Details

### Why HTML Entities Don't Work in JSON

JSON has its own escaping rules defined in RFC 8259:
- `"` must be escaped as `&quot;`
- `\` must be escaped as `\\`
- Control characters must be escaped (e.g., `\n`, `\t`)

HTML entities like `&quot;` are:
1. Not part of the JSON specification
2. Not recognized by JSON parsers
3. Treated as literal text, not escape sequences
4. Cause syntax errors when combined with backslashes

### Proper JSON Escaping Order

When manually escaping (not recommended, use `json.dumps()`):
1. Escape backslashes FIRST: `\` → `\\`
2. Then escape quotes: `"` → `&quot;`
3. Then escape control characters: `\n` → `\\n`

Order matters! If you escape quotes before backslashes, you'll double-escape.

## Conclusion

This fix resolves a fundamental flaw in the JSON communication protocol that was causing systematic corruption of Python code. By using Python's built-in `json.dumps()`, we ensure proper, standards-compliant JSON encoding that works reliably with all types of code.