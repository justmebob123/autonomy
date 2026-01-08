# ROOT CAUSE ANALYSIS - AI Infinite Loop Issue

## Problem Statement
The AI was stuck in an infinite loop calling `find_similar_files` repeatedly without making progress on tasks, despite the system prompt explicitly saying "DO NOT call find_similar_files first".

## Root Cause Identified

### The Contradiction
There was a **direct contradiction** between the system prompt and the user message:

**System Prompt (pipeline/prompts.py line 157):**
```
🚨 CRITICAL: CREATE FILES IMMEDIATELY 🚨
When given a task to create a file:
1. DO NOT call find_similar_files first
2. DO NOT call validate_filename first
3. DO NOT call any analysis tools first
4. IMMEDIATELY call create_python_file or modify_python_file
```

**User Message (pipeline/phases/coding.py line 917-946):**
```python
# STEP 1: FILE DISCOVERY - Check for similar files
similar_files = self.file_discovery.find_similar_files(task.target_file)

if similar_files:
    parts.append("## ⚠️ Similar Files Found\n")
    parts.append("Before creating a new file, please review these existing files:\n")
    # ... shows similar files ...
    parts.append("## 🤔 Decision Required\n")
    parts.append("Please decide:")
    parts.append("1. **Modify existing file** - If one of the above files should be updated")
    parts.append("2. **Create new file** - If this is genuinely new functionality")
    parts.append("\nUse `read_file` to examine existing files before deciding.\n")
```

### Why This Caused an Infinite Loop

1. **System prompt says:** "Don't call find_similar_files first"
2. **User message shows:** Similar files and asks AI to "review these existing files"
3. **User message suggests:** "Use `read_file` to examine existing files before deciding"
4. **AI interprets this as:** "I need to review the files by calling find_similar_files"
5. **AI calls:** `find_similar_files` to "review" the files
6. **Tool returns:** Empty result (no similar files for cleanup_report.txt)
7. **AI doesn't understand:** Empty result means "no conflicts, proceed with creation"
8. **AI repeats:** Calls `find_similar_files` again, creating infinite loop

### Why Loop Detection Didn't Catch It

Loop detection wasn't working because of a separate bug in tool name extraction:
- Loop detection was looking for `tool_call.get('tool')` or `tool_call.get('name')`
- But actual structure is `tool_call.get('function', {}).get('name')`
- So loop detection couldn't track which tools were being called
- No intervention occurred to break the loop

## Fixes Applied

### Fix 1: Remove Contradictory User Message (Commit c3aa6bb)
**File:** `pipeline/phases/coding.py` (lines 917-946)

**Change:** Removed the automatic similar file discovery from `_build_user_message()`

**Reason:** This was directly contradicting the system prompt and causing the AI to get stuck

### Fix 2: Add Report Generation Guidance (Commit c3aa6bb)
**File:** `pipeline/prompts.py` (lines 157-180)

**Change:** Added explicit guidance for report generation tasks:
```
🚨 SPECIAL CASE: REPORT GENERATION TASKS 🚨
If the task asks to create a REPORT or ANALYSIS file:
1. Call the analysis tool FIRST (e.g., detect_dead_code)
2. Get the results from the tool
3. IMMEDIATELY call create_python_file with the results as content
4. Format the results as a readable report

DO NOT get stuck calling analysis tools repeatedly without creating the report file!
```

**Reason:** The task "Remove unused functions using detect_dead_code tool" with target "cleanup_report.txt" was confusing because it's a report generation task, not a code modification task.

### Fix 3: Fix Loop Detection Tool Tracking (Commit f6c7c83)
**File:** `pipeline/phases/loop_detection_mixin.py` (line 72)

**Change:** Fixed tool name extraction to handle correct format:
```python
# OLD:
tool_name = tool_call.get('tool') or tool_call.get('name') or 'unspecified_tool'

# NEW:
tool_name = (
    tool_call.get('function', {}).get('name') or 
    tool_call.get('tool') or 
    tool_call.get('name') or 
    'unspecified_tool'
)
```

**Reason:** Loop detection couldn't track tools because it was extracting names from the wrong location in the data structure.

### Fix 4: Fix Tool Call Logging (Commit f6c7c83)
**File:** `pipeline/phases/coding.py` (line 280)

**Change:** Fixed tool name extraction in logging:
```python
# OLD:
tool_name = tc.get("name", "unknown")

# NEW:
tool_name = tc.get("function", {}).get("name") or tc.get("name", "unknown")
```

**Reason:** Tool calls were showing as "unknown" in logs, making debugging difficult.

## Impact

### Before Fixes:
- ❌ AI stuck in infinite loop calling `find_similar_files`
- ❌ Loop detection not working
- ❌ Tool calls showing as "unknown" in logs
- ❌ Tasks failing with "no files created"
- ❌ System unable to make progress

### After Fixes:
- ✅ AI should proceed directly to file creation
- ✅ Loop detection should work and intervene if needed
- ✅ Tool calls show correct names in logs
- ✅ Report generation tasks have clear workflow
- ✅ System should make progress on tasks

## Lessons Learned

1. **System prompts and user messages must be consistent** - Contradictions confuse the AI
2. **Don't show information and then tell AI not to use it** - If you show similar files, AI will try to review them
3. **Loop detection requires correct data extraction** - Tool tracking must use the right data structure
4. **Different task types need different workflows** - Report generation is different from code implementation
5. **Debugging requires good logging** - Tool names showing as "unknown" made root cause analysis harder

## Testing Recommendations

1. Run autonomy system on the web project
2. Verify AI doesn't get stuck in loops
3. Verify loop detection intervenes if needed
4. Verify report generation tasks complete successfully
5. Verify tool calls show correct names in logs
6. Monitor for any remaining issues

## Related Issues

- 541 integration conflicts are LEGITIMATE architectural issues (duplicate class/function names)
- These are NOT related to the JSON encoding bug or the infinite loop issue
- These should be addressed through refactoring, not automated fixes
- The system is correctly detecting them and creating tasks to fix them