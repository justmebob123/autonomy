# Critical System Fixes Required

## Issue 1: Empty Error Messages in Coding Phase

**Problem**: When the model calls `read_file` but doesn't follow up with file creation, the error message is empty.

**Root Cause**: The error detection in `pipeline/phases/coding.py` doesn't properly capture what went wrong.

**Fix Location**: `pipeline/phases/coding.py` - Need to add better error detection for when model only calls analysis tools.

## Issue 2: Infinite Task Reactivation Loop

**Problem**: The same task keeps getting reactivated and failing repeatedly (500+ iterations).

**Root Cause**: Task reactivation logic doesn't check if a task has failed multiple times recently.

**Fix Location**: `pipeline/objective_manager.py` - Add failure count tracking and prevent reactivation of repeatedly failing tasks.

## Issue 3: Syntax Errors Never Fixed

**Problem**: 30+ files have syntax errors that are never addressed:
- Unterminated strings
- Invalid syntax
- Unexpected characters after line continuation

**Root Cause**: The system doesn't prioritize fixing syntax errors before creating new features.

**Fix Location**: Need a dedicated "syntax repair" phase or priority system.

## Issue 4: Model Not Creating Files

**Problem**: Model calls `read_file` but never calls `create_python_file` or `full_file_rewrite`.

**Root Cause**: 
1. The task target is `architecture/integration_plan.md` (markdown file)
2. Model is reading a Python file instead
3. No clear instruction to create the markdown file

**Fix Location**: 
- `pipeline/phases/coding.py` - Better handling of markdown/documentation tasks
- Task description needs to be clearer about what to create

## Issue 5: Progress Percentage Stuck

**Problem**: Project at 14%, objective at 98% for hundreds of iterations.

**Root Cause**: Completion calculation doesn't account for failed tasks properly.

**Fix Location**: `pipeline/objective_manager.py` - Fix progress calculation to handle failed tasks.

## Immediate Actions Needed

1. **Stop the infinite loop**: Add max failure count per task
2. **Fix syntax errors**: Create priority tasks to fix all syntax errors
3. **Clear task description**: Make it clear what file to create and how
4. **Better error messages**: Capture actual error when model doesn't create files
5. **Task blacklisting**: Prevent repeatedly failing tasks from being reactivated

## Recommended Approach

1. First, fix all syntax errors in the codebase
2. Then, implement task failure tracking
3. Add better error messages for incomplete actions
4. Improve task descriptions for clarity
5. Add a "stuck detection" mechanism that forces phase change after N failures