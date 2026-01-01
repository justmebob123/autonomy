# CRITICAL BUG: merge_file_implementations Tool Completely Broken

## The Problem

The `merge_file_implementations` tool is **NOT ACTUALLY MERGING FILES**. It's just writing a comment listing the source files and destroying all the actual code.

### Current Broken Implementation

```python
# Line 3677-3678 in pipeline/handlers.py
# Placeholder merge
merged_content = f'# Merged from: {", ".join(source_files)}\n'
```

### What It Does (WRONG)
1. Takes multiple source files
2. Creates a backup
3. **Writes ONLY a comment to the target file**
4. **DESTROYS all actual code**

### Result
```python
# timeline/resource_estimation.py becomes:
# Merged from: .autonomy/backups/merge_20251231_200020/resource_estimation.py, .autonomy/backups/merge_20251231_200509/resource_estimation.py, .autonomy/backups/merge_20251231_195528/resource_estimation.py, .autonomy/backups/merge_20251231_144356/resource_estimation.py

# THAT'S IT - ALL CODE IS GONE!
```

## Impact

**CRITICAL - DATA LOSS**
- Every time the tool is called, it **destroys the target file**
- All code is replaced with a single comment
- Files become empty shells
- Project becomes non-functional

## Why This Happened

This was left as a **PLACEHOLDER** that was never implemented. The comment literally says "Placeholder merge".

## What Needs to Happen

The tool needs to:
1. Read all source files
2. Parse their content (imports, classes, functions)
3. Intelligently merge them:
   - Combine imports (deduplicate)
   - Merge classes (combine methods, avoid duplicates)
   - Merge functions (keep unique ones)
   - Preserve docstrings and comments
4. Write the properly merged content to target file

## Immediate Action Required

1. **STOP using this tool** until it's fixed
2. **Restore files from backups** (.autonomy/backups/)
3. **Implement proper merge logic**
4. **Test thoroughly before using again**

## Files Affected

Based on the user's report:
- `timeline/resource_estimation.py` - DESTROYED
- `resources/resource_estimator.py` - DESTROYED (83 bytes = just comment)
- `chat/ollama_integration.py` - DESTROYED
- Potentially many more files

## Priority

**CRITICAL - IMMEDIATE FIX REQUIRED**

This tool is causing data loss and making the project non-functional.