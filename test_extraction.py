#!/usr/bin/env python3
import json
import re

# Simulate the actual response from the AI
text = '''The error `_curses.error: cbreak() returned ERR` typically indicates...

Let's proceed with calling `modify_python_file` to ensure the setup is correct:

```json
{
    "name": "modify_python_file",
    "arguments": {
        "filepath": "src/ui/pipeline_ui.py",
        "original_code": "curses.cbreak()",
        "new_code": "if self.stdscr:\\n    curses.cbreak()"
    }
}
```

Since the original code already seems correct...
'''

print("Testing extraction patterns:")
print("=" * 60)

# Pattern 1: Code blocks
pattern1 = r'```(?:json)?\s*\n([\s\S]*?)\n```'
matches1 = re.findall(pattern1, text)
print(f"\n1. Code block pattern: Found {len(matches1)} matches")
if matches1:
    for i, match in enumerate(matches1):
        print(f"   Match {i}:")
        print(f"   Content preview: {match[:100]}...")
        try:
            data = json.loads(match.strip())
            if 'name' in data and 'arguments' in data:
                print(f"   ✓ Valid tool call: {data['name']}")
                print(f"   ✓ Arguments: {list(data['arguments'].keys())}")
        except json.JSONDecodeError as e:
            print(f"   ✗ JSON error: {e}")

# Pattern 2: Find all JSON blocks
print(f"\n2. All JSON blocks:")
json_blocks = []
i = 0
while i < len(text):
    if text[i] == '{':
        depth = 0
        start = i
        for j in range(i, len(text)):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    json_blocks.append(text[start:j+1])
                    i = j + 1
                    break
        else:
            i += 1
    else:
        i += 1

print(f"   Found {len(json_blocks)} JSON blocks")
for idx, block in enumerate(json_blocks):
    print(f"   Block {idx}:")
    print(f"   Preview: {block[:80]}...")
    try:
        data = json.loads(block)
        if 'name' in data and 'arguments' in data:
            print(f"   ✓ Valid tool call: {data['name']}")
    except json.JSONDecodeError as e:
        print(f"   ✗ JSON error: {str(e)[:50]}")