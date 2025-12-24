#!/usr/bin/env python3
import json
import re

def convert_python_strings_to_json(text: str) -> str:
    """
    Convert Python-style triple-quoted strings to JSON-compatible format.
    """
    def replace_triple_quotes(match):
        content = match.group(1)
        # Escape backslashes and quotes for JSON
        content = content.replace('\\', '\\\\')
        content = content.replace('"', '\&quot;')
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        return f'"{content}"'
    
    # Match triple-quoted strings (both """ and ''')
    text = re.sub(r'"""([\s\S]*?)"""', replace_triple_quotes, text)
    text = re.sub(r"'''([\s\S]*?)'''", replace_triple_quotes, text)
    
    return text

# Test with the actual problematic JSON
test_json = '''{
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
}'''

print("Original JSON (with Python triple quotes):")
print("=" * 60)
print(test_json[:200] + "...")
print()

print("Converting Python strings to JSON format...")
converted = convert_python_strings_to_json(test_json)
print()

print("Converted JSON:")
print("=" * 60)
print(converted[:300] + "...")
print()

print("Attempting to parse...")
try:
    data = json.loads(converted)
    print("✓ SUCCESS! JSON parsed correctly")
    print(f"  - Tool name: {data['name']}")
    print(f"  - Arguments: {list(data['arguments'].keys())}")
    print(f"  - Filepath: {data['arguments']['filepath']}")
    print(f"  - Original code length: {len(data['arguments']['original_code'])} chars")
    print(f"  - New code length: {len(data['arguments']['new_code'])} chars")
except json.JSONDecodeError as e:
    print(f"✗ FAILED: {e}")
    print(f"  Position: {e.pos}")