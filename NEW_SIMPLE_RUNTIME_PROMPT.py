def _get_runtime_debug_prompt_simple(filepath: str, code: str, issue: dict) -> str:
    """Generate SIMPLE, DIRECT prompt for runtime errors"""
    
    line_num = issue.get('line', 'unknown')
    error_msg = issue.get('message', 'No message')
    
    return f"""
CALL modify_python_file NOW TO FIX THIS ERROR

File: {filepath}
Error at line: {line_num}

ERROR OUTPUT:
{error_msg}

FILE CONTENT:
```python
{code}
```

YOUR TASK:
1. Look at line {line_num} in the file above
2. Understand what's wrong
3. Copy lines {max(1, line_num-5)} to {line_num+5} EXACTLY from the file
4. Fix the error in those lines
5. Call modify_python_file with:
   {{
     "name": "modify_python_file",
     "arguments": {{
       "filepath": "{filepath}",
       "original_code": "the exact 10 lines you copied",
       "new_code": "your fixed version"
     }}
   }}

DO NOT call search_code or read_file - everything is above.
CALL modify_python_file NOW.
"""