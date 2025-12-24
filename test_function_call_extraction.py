#!/usr/bin/env python3
import re
from typing import Optional, Dict

def extract_function_call_syntax(text: str) -> Optional[Dict]:
    """
    Extract tool calls from Python function call syntax.
    """
    # Pattern to match function calls with named arguments
    pattern = r'(\w+)\s*\(\s*([^)]+)\s*\)'
    
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        func_name = match.group(1)
        args_str = match.group(2)
        
        # Only process known tool names
        known_tools = [
            'modify_python_file', 'create_python_file', 'create_file',
            'read_file', 'search_code', 'list_directory', 'report_issue'
        ]
        
        if func_name not in known_tools:
            continue
        
        # Parse the arguments
        arguments = {}
        
        # Pattern to match key="value" or key='value' or key="""value"""
        arg_pattern = r'(\w+)\s*=\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'|"([^"]*)"|\'([^\']*)\')'
        
        for arg_match in re.finditer(arg_pattern, args_str):
            key = arg_match.group(1)
            # Get the value from whichever group matched
            value = (arg_match.group(2) or arg_match.group(3) or 
                    arg_match.group(4) or arg_match.group(5) or "")
            arguments[key] = value
        
        if arguments:
            print(f"✓ Found function call: {func_name}")
            print(f"  Arguments: {list(arguments.keys())}")
            return {
                "function": {
                    "name": func_name,
                    "arguments": arguments
                }
            }
    
    return None

# Test with the actual response
text = '''Step 4: EXECUTE the fix - CALL THE TOOL NOW

```modify_python_file(
    filepath="src/ui/pipeline_ui.py",
    original_code="curses.cbreak()",
    new_code="try:\\n            curses.cbreak()\\n        except curses.error as e:\\n            logger.error(f'Error setting cbreak mode: {e}')"
)
```

This change wraps the `curses.cbreak()` call in a try-except block.'''

print("Testing function call extraction:")
print("=" * 60)

result = extract_function_call_syntax(text)

if result:
    print("\n✓ SUCCESS! Extracted tool call:")
    print(f"  Name: {result['function']['name']}")
    print(f"  Arguments:")
    for key, value in result['function']['arguments'].items():
        print(f"    - {key}: {value[:50]}..." if len(value) > 50 else f"    - {key}: {value}")
else:
    print("\n✗ FAILED: Could not extract tool call")