#!/usr/bin/env python3
import json
import re

# This is the ACTUAL response from the logs
text = '''The error `_curses.error: cbreak() returned ERR` typically indicates that `curses.cbreak()` was called when the terminal is not in a state where it can handle this operation, such as if the terminal has already been closed or if there's an issue with the terminal settings.

In the provided code, `curses.cbreak()` is called in the `run` method of the `PipelineUI` class. Given that the error occurs at this point, it suggests that the terminal might not be properly initialized or there could be an issue with the terminal state before calling `curses.cbreak()`.

However, since the provided code does not show any issues with the initialization sequence and all necessary setup calls (`initscr`, `noecho`, etc.) are present, another potential cause is that the terminal might have been closed or altered by some other part of the program or environment before reaching this point. Given the context and the typical causes of this error, we should ensure that the terminal is properly initialized and that no conflicting operations occur.

Since there's no clear indication from the provided code that `curses.cbreak()` is being called in an incorrect sequence or with incorrect parameters, a likely fix would be to ensure that all necessary setup calls are correctly placed and executed. However, since the error message suggests a problem with the terminal state, we should also consider adding some basic checks or logging around this call to diagnose further if needed.

Given the provided code and typical causes of this error, let's assume that the issue might be due to an incorrect sequence or missing setup step. We'll ensure all necessary setup calls are correctly placed and executed by checking the order of operations in the `run` method.

Let's proceed with calling `modify_python_file` to ensure the setup is correct:

```json
{
    "name": "modify_python_file",
    "arguments": {
        "filepath": "src/ui/pipeline_ui.py",
        "original_code": """            # Initialize ncurses
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.stdscr.keypad(True)""",
        "new_code": """            # Initialize ncurses
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.stdscr.keypad(True)"""
    }
}
```

Since the original code already seems correct, we'll ensure that no changes are made to it. However, if further debugging is needed, additional logging or checks can be added around this section.

```json
{
    "name": "modify_python_file",
    "arguments": {
        "filepath": "src/ui/pipeline_ui.py",
        "original_code": """            # Initialize ncurses
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.stdscr.keypad(True)""",
        "new_code": """            # Initialize ncurses
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.stdscr.keypad(True)"""
    }
}
```'''

print("Testing extraction from ACTUAL AI response:")
print("=" * 60)

# Pattern: Code blocks
pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
matches = re.findall(pattern, text)
print(f"\nFound {len(matches)} code blocks")

for i, match in enumerate(matches):
    print(f"\n--- Code Block {i+1} ---")
    print(f"Length: {len(match)} chars")
    print(f"Preview: {match[:150]}...")
    
    try:
        data = json.loads(match.strip())
        if 'name' in data and 'arguments' in data:
            print(f"✓ Valid tool call: {data['name']}")
            print(f"✓ Arguments keys: {list(data['arguments'].keys())}")
            
            # Check if it's a valid modify_python_file call
            args = data['arguments']
            if 'filepath' in args and 'original_code' in args and 'new_code' in args:
                print(f"✓ Has all required fields for modify_python_file")
                print(f"  - filepath: {args['filepath']}")
                print(f"  - original_code length: {len(args['original_code'])} chars")
                print(f"  - new_code length: {len(args['new_code'])} chars")
        else:
            print(f"✗ Missing 'name' or 'arguments' keys")
            print(f"  Keys found: {list(data.keys())}")
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        print(f"  Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")