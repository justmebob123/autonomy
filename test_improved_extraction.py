#!/usr/bin/env python3
import re
from typing import Optional, Dict

def extract_function_call_syntax(text: str) -> Optional[Dict]:
    """
    Extract tool calls from Python function call syntax.
    """
    known_tools = [
        'modify_python_file', 'create_python_file', 'create_file',
        'read_file', 'search_code', 'list_directory', 'report_issue'
    ]
    
    for tool_name in known_tools:
        # Look for tool_name( ... ) with proper bracket matching
        pattern = rf'{tool_name}\s*\('
        match = re.search(pattern, text)
        
        if not match:
            continue
        
        # Find the matching closing parenthesis
        start = match.end()
        depth = 1
        end = start
        
        for i in range(start, len(text)):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if depth != 0:
            continue
        
        args_str = text[start:end]
        print(f"Found {tool_name} call")
        print(f"Args string length: {len(args_str)} chars")
        print(f"Args preview: {args_str[:100]}...")
        
        # Parse the arguments
        arguments = {}
        
        # Pattern to match key="value" where value can contain escaped quotes
        arg_pattern = r'(\w+)\s*=\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'|"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')'
        
        matches = list(re.finditer(arg_pattern, args_str))
        print(f"Found {len(matches)} argument matches")
        
        for arg_match in matches:
            key = arg_match.group(1)
            value = (arg_match.group(2) or arg_match.group(3) or 
                    arg_match.group(4) or arg_match.group(5) or "")
            
            # Unescape if needed
            if arg_match.group(4) or arg_match.group(5):
                value = value.replace('\\n', '\n')
                value = value.replace('\\t', '\t')
                value = value.replace('\&quot;', '"')
                value = value.replace("\\'", "'")
                value = value.replace('\\\\', '\\')
            
            arguments[key] = value
            print(f"  - {key}: {len(value)} chars")
        
        if arguments:
            return {
                "function": {
                    "name": tool_name,
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

This change wraps the `curses.cbreak()` call.'''

print("Testing improved function call extraction:")
print("=" * 60)
print()

result = extract_function_call_syntax(text)

if result:
    print("\n✓ SUCCESS! Extracted tool call:")
    print(f"  Name: {result['function']['name']}")
    print(f"  Arguments:")
    for key, value in result['function']['arguments'].items():
        preview = value[:80].replace('\n', '\\n') if len(value) > 80 else value.replace('\n', '\\n')
        print(f"    - {key}: {preview}...")
else:
    print("\n✗ FAILED: Could not extract tool call")