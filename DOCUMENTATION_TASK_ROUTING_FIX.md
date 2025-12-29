# Documentation Task Routing Issue

## Problem
Documentation tasks (creating .md files) are being assigned to the coding phase, which correctly refuses to create them. This causes tasks to fail unnecessarily.

## Examples from Log
```
Task: Write full documentation including installation, configurati...
Target: docs/installation.md
Phase: CODING (WRONG!)
Result: ❌ Coding phase cannot create .md files - use documentation phase instead
```

## Root Cause
The coordinator's task routing logic doesn't check the target file extension or task description to determine if it's a documentation task.

## Solution
Add logic to automatically route documentation tasks to the documentation phase:

1. Check if target_file ends with .md
2. Check if task description contains "documentation", "write docs", etc.
3. If yes, route to documentation phase instead of coding phase

## Implementation Needed
- Modify coordinator's `_determine_next_action()` method
- Add documentation task detection
- Route to documentation phase when detected