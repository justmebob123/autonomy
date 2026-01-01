# PARSER FIX PLAN: Support List and Dict Arguments

## Current Parser Limitation

The tool call parser in `pipeline/client.py` only handles string arguments:

```python
arg_pattern = r'(\w+)\s*=\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'|"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')\'
```

This matches:
- ✅ `key="value"`
- ✅ `key='value'`  
- ✅ `key="""value"""`
- ❌ `key=[...]` (LISTS)
- ❌ `key={...}` (DICTS)

## Impact

Tools that require list parameters fail:
- `merge_file_implementations(source_files=[...])` → KeyError: 'source_files'
- `cleanup_redundant_files(files=[...])` → KeyError: 'files'
- `restructure_directory(moves=[...])` → KeyError: 'moves'

## Solution Options

### Option 1: Tell AI to Use JSON Format (IMMEDIATE FIX)

Modify prompts to explicitly request JSON format:

```
⚠️ CRITICAL OUTPUT FORMAT:

You MUST output tool calls in JSON format, NOT Python syntax:

CORRECT:
{
    "name": "merge_file_implementations",
    "arguments": {
        "source_files": ["file1.py", "file2.py"],
        "target_file": "file1.py",
        "strategy": "ai_merge"
    }
}

WRONG:
merge_file_implementations(
    source_files=["file1.py", "file2.py"],
    target_file="file1.py",
    strategy="ai_merge"
)
```

### Option 2: Enhanced Parser (LONG-TERM FIX)

Add support for list and dict parsing using ast.literal_eval():

```python
# After extracting args_str, try to parse as Python literal
try:
    # Wrap in function call for ast.parse
    code = f"f({args_str})"
    tree = ast.parse(code)
    call = tree.body[0].value
    
    arguments = {}
    for keyword in call.keywords:
        arg_name = keyword.arg
        arg_value = ast.literal_eval(keyword.value)
        arguments[arg_name] = arg_value
except:
    # Fall back to regex parsing
    ...
```

## Recommendation

Implement BOTH:
1. **Immediate**: Update prompts to request JSON format
2. **Long-term**: Enhance parser to handle both formats

This provides:
- Immediate fix (prompts)
- Backward compatibility (parser handles both)
- Robustness (works even if AI ignores format instruction)

## Files to Modify

1. **pipeline/prompts.py** - Add JSON format requirement
2. **pipeline/client.py** - Enhance parser (optional but recommended)