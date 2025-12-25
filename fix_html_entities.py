#!/usr/bin/env python3
"""
Tool to fix HTML entities in Python files.
Replaces &quot; &amp; &lt; &gt; with actual characters.
"""

import sys
import os

def fix_html_entities(filepath):
    """Fix HTML entities in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace HTML entities
    replacements = {
        '&quot;': '"',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&#39;': "'",
        '&apos;': "'"
    }
    
    original = content
    for entity, char in replacements.items():
        content = content.replace(entity, char)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 fix_html_entities.py <file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    if fix_html_entities(filepath):
        print(f"✓ Fixed HTML entities in {filepath}")
    else:
        print(f"No HTML entities found in {filepath}")