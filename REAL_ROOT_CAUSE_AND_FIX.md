# REAL Root Cause Analysis and Fix

## The Actual Problem

The system is stuck in an infinite loop because:

**Task**: Create `architecture/integration_plan.md` (MARKDOWN file)
**Phase**: Coding (expects PYTHON files)
**Prompt**: "You are an expert Python developer implementing production code"
**Model**: Confused - reads Python files, never creates markdown
**Result**: Empty error, task fails, reactivates infinitely

## Root Cause #1: PROMPT MISMATCH

### The Evidence
From `pipeline/prompts.py` line 30-80:
```python
"coding": """🎯 YOUR PRIMARY MISSION: IMPLEMENT PRODUCTION-READY CODE

You are an expert Python developer implementing production code.

✅ create_python_file - Create a new Python file
✅ modify_python_file - Modify existing Python file
```

The prompt ONLY mentions Python files. No mention of markdown, documentation, or other file types.

### Why This Causes the Loop
1. Task target: `architecture/integration_plan.md`
2. Model sees: "create Python files"
3. Model thinks: "This doesn't match, let me read related files"
4. Model calls: `read_file("services/integration_gap_analysis.py")`
5. Model never creates the markdown file
6. Task fails with empty error
7. Task gets reactivated
8. Loop repeats 500+ times

### The Fix
**Option A**: Update coding prompt to handle markdown files
```python
"coding": """🎯 YOUR PRIMARY MISSION: IMPLEMENT CODE AND DOCUMENTATION

You are an expert developer implementing code and documentation.

IMPORTANT: Check the target file extension:
- .py files: Create Python code
- .md files: Create markdown documentation
- Other: Ask for clarification

✅ create_python_file - Create Python files (.py)
✅ create_file - Create any file type (markdown, config, etc.)
```

**Option B**: Reject markdown files in coding phase
```python
# In pipeline/phases/coding.py, line ~230
if task.target_file.endswith('.md'):
    # Check if it's an analysis file (already handled)
    if not any(keyword in task.target_file.lower() 
               for keyword in ['analysis', 'gap', 'report', 'findings']):
        # This is a general markdown file - reject it
        task.status = TaskStatus.SKIPPED
        return PhaseResult(
            success=True,
            message="Markdown files should be handled by documentation phase",
            next_phase="documentation"
        )
```

**Option C**: Add 'plan' to the analysis keywords
```python
# In pipeline/phases/coding.py, line 206
if task.target_file.endswith('.md') and any(keyword in task.target_file.lower() 
                                             for keyword in ['analysis', 'gap', 'report', 'findings', 'plan']):
```

## Root Cause #2: INCOMPLETE KEYWORD LIST

### The Evidence
From `pipeline/phases/coding.py` line 206:
```python
if task.target_file.endswith('.md') and any(keyword in task.target_file.lower() 
                                             for keyword in ['analysis', 'gap', 'report', 'findings']):
```

The file `architecture/integration_plan.md` contains "plan" but the keyword list only has:
- analysis
- gap
- report  
- findings

So it doesn't match and falls through to normal Python file handling.

### The Fix
Add 'plan' to the keyword list:
```python
for keyword in ['analysis', 'gap', 'report', 'findings', 'plan', 'architecture', 'design']:
```

## Root Cause #3: NO FILE TYPE GUIDANCE IN USER MESSAGE

### The Evidence
From `pipeline/phases/coding.py` line 860:
```python
parts.append(f"**Target file:** {task.target_file}")
```

The user message tells the model the target file but doesn't say:
- What TYPE of file it is
- What CONTENT should be in it
- What FORMAT to use

### The Fix
Add file type guidance:
```python
# Determine file type
file_ext = task.target_file.split('.')[-1] if '.' in task.target_file else 'unknown'

if file_ext == 'md':
    parts.append(f"**Target file:** {task.target_file} (MARKDOWN documentation)")
    parts.append("**Format:** Use markdown syntax with headers, lists, and code blocks")
    parts.append("**Content:** Create a comprehensive plan/document as described")
elif file_ext == 'py':
    parts.append(f"**Target file:** {task.target_file} (Python code)")
    parts.append("**Format:** Use proper Python syntax with docstrings")
else:
    parts.append(f"**Target file:** {task.target_file}")
```

## Recommended Fix Strategy

### Immediate Fix (Stops the loop)
1. Add 'plan' to keyword list in line 206
2. This makes `architecture/integration_plan.md` match the special handling
3. Task gets marked complete through IPC system
4. Loop stops

### Proper Fix (Prevents future issues)
1. Update coding prompt to mention markdown files
2. Add file type guidance in user message
3. Expand keyword list to cover more documentation types
4. Add validation to reject unsupported file types

### Long-term Fix (Architectural)
1. Create a file type router
2. Route .md files to documentation phase
3. Route .py files to coding phase
4. Route .json/.yaml to configuration phase
5. Clear separation of concerns

## Implementation Plan

### Step 1: Quick Fix (5 minutes)
```python
# File: pipeline/phases/coding.py, line 206
if task.target_file.endswith('.md') and any(keyword in task.target_file.lower() 
                                             for keyword in ['analysis', 'gap', 'report', 'findings', 'plan', 'architecture', 'design', 'integration']):
```

### Step 2: Better Error Messages (10 minutes)
```python
# File: pipeline/phases/coding.py, after line 360
if not files_created and not files_modified:
    analysis_tools = ['find_similar_files', 'validate_filename', 'compare_files', 
                     'find_all_conflicts', 'detect_naming_violations', 'read_file']
    only_analysis = all(
        call.get("function", {}).get("name") in analysis_tools 
        for call in tool_calls
    )
    
    if only_analysis:
        tools_called = [call.get('function', {}).get('name') for call in tool_calls]
        file_type = "markdown" if task.target_file.endswith('.md') else "Python"
        
        task.add_error(
            "incomplete_action",
            f"You called {', '.join(tools_called)} but didn't create the target file.\n"
            f"Target: {task.target_file} ({file_type} file)\n"
            f"Required action: Use create_file or create_python_file to create this {file_type} file.",
            phase="coding"
        )
```

### Step 3: Prompt Update (15 minutes)
Update `pipeline/prompts.py` to mention markdown files and provide clear guidance.

## Testing Plan

1. Revert the artificial loop-breaking changes
2. Apply Step 1 (quick fix)
3. Run the system
4. Verify the task completes
5. Check logs for clear error messages
6. Apply Steps 2 and 3
7. Test with various file types

## Success Criteria

✅ Task `architecture/integration_plan.md` completes successfully
✅ No infinite loops
✅ Clear error messages when files aren't created
✅ Model understands what type of file to create
✅ Proper routing of different file types