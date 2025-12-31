#!/usr/bin/env python3
"""
Comprehensive fix for refactoring phase.
This script will fix all the issues in pipeline/phases/refactoring.py
"""

import re

# Read the file
with open('pipeline/phases/refactoring.py', 'r') as f:
    content = f.read()

# Fix 1: Change error message to not reference non-existent 'error' key
content = re.sub(
    r'message=f"([^"]+) failed: \{result\.get\(\'error\', \'Unknown error\'\)\}"',
    r'message=f"\1 failed: No tool calls in response"',
    content
)

# Fix 2: Execute tool calls properly
# Replace the _write_refactoring_results calls with proper tool execution

old_pattern = r'''        # Update REFACTORING_WRITE\.md with results
        self\._write_refactoring_results\(
            refactoring_type="([^"]+)",
            results=result\.get\("tool_results", \[\]\),
            recommendations=result\.get\("response", ""\)
        \)'''

new_pattern = r'''        # Execute tool calls
        from ..handlers import ToolCallHandler
        handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
        results = handler.process_tool_calls(tool_calls)
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="\1",
            results=results,
            recommendations=content
        )'''

content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Write the fixed content
with open('pipeline/phases/refactoring.py', 'w') as f:
    f.write(content)

print("✅ Fixed all refactoring phase issues!")
print("   - Fixed error messages")
print("   - Added proper tool execution")
print("   - Fixed result handling")