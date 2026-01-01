#!/usr/bin/env python3
"""Fix refactoring.py to enable continuous mode (no attempt limits)."""

import re

with open('pipeline/phases/refactoring.py', 'r') as f:
    content = f.read()

# Pattern to find the max_attempts check block
pattern = r'''                    # Check retry count
                    if task\.attempts >= task\.max_attempts:
                        # After max attempts, auto-create report.*?
                    else:
                        # RETRY with stronger guidance
                        self\.logger\.warning\(f"  ⚠️  Task \{task\.task_id\}: Only compared files without reading them - RETRYING \(attempt \{task\.attempts \+ 1\}/\{task\.max_attempts\}\)"\)'''

# Replacement - just the retry logic without the max_attempts check
replacement = '''                    # CONTINUOUS MODE: No max attempts - keep retrying with progressively stronger guidance
                    # RETRY with stronger guidance
                    self.logger.warning(f"  ⚠️  Task {task.task_id}: Only compared files without reading them - RETRYING (attempt {task.attempts + 1})")'''

# Use DOTALL flag to match across newlines
content_new = re.sub(pattern, replacement, content, flags=re.DOTALL)

if content_new != content:
    with open('pipeline/phases/refactoring.py', 'w') as f:
        f.write(content_new)
    print("✅ Successfully updated refactoring.py for continuous mode")
else:
    print("❌ Pattern not found - manual fix needed")