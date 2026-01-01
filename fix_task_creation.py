#!/usr/bin/env python3
"""
Script to add validation checks after all task creation calls in refactoring.py
"""

import re

# Read the file
with open('pipeline/phases/refactoring.py', 'r') as f:
    content = f.read()

# Pattern to find task creation followed by tasks_created += 1
# The closing ) might be on a different line, so we need to handle multi-line
pattern = r'(task = manager\.create_task\((?:[^)]|\n)*?\))\n(\s+)tasks_created \+= 1'

# Replacement with validation check
replacement = r'\1\n\2if task:  # Only count if task was created (validation passed)\n\2    tasks_created += 1'

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Count how many replacements were made
count = len(re.findall(pattern, content, flags=re.MULTILINE))

# Write back
with open('pipeline/phases/refactoring.py', 'w') as f:
    f.write(new_content)

print(f"✅ Added validation checks after {count} task creation calls")