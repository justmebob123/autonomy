# Critical Prompt Fix - Root Cause Analysis

## The Problem

The refactoring phase was stuck in an infinite loop where the AI would:
1. Compare files (analysis only)
2. Task fails: "only analysis performed, no action taken"
3. Next iteration: AI does the SAME thing again
4. Eventually succeeds on 2nd or 3rd try

## Root Cause Discovery

After deep analysis, I found a **critical contradiction in the system**:

### What the Prompt Said:
```
ACTION REQUIRED:
1. Use compare_file_implementations to analyze differences
2. Use merge_file_implementations to merge them

EXAMPLE:
compare_file_implementations(file1="...", file2="...")
merge_file_implementations(target="...", source="...")
```

The prompt explicitly told the AI to do **Step 1 (compare) THEN Step 2 (merge)**.

### What the Completion Logic Did:
```python
if only_analysis_tools_used:
    task.fail("only analysis performed, no action taken")
```

The completion logic **failed the task** if only analysis tools (like `compare_file_implementations`) were used.

### The Contradiction:
- **Prompt**: "Do compare first, then merge"
- **Logic**: "If you only did compare, you failed"
- **Result**: AI follows prompt → gets punished → tries again → same result → infinite loop

## The Fix

### 1. Updated Duplicate Handler Prompt
**Before:**
```
ACTION REQUIRED:
1. Use compare_file_implementations to analyze differences
2. Use merge_file_implementations to merge them
```

**After:**
```
ACTION REQUIRED:
Use merge_file_implementations to merge these duplicate files.

OPTIONAL: If you want to understand differences first, you CAN compare,
BUT you MUST still call merge_file_implementations after!
```

**Impact**: AI now knows to merge directly, not compare first.

### 2. Updated Main Prompt Example
**Before:**
```
Step 1: compare_file_implementations(...)
Step 2: merge_file_implementations(...)
```

**After:**
```
CORRECT APPROACH:
merge_file_implementations(...)
Result: ✅ Task RESOLVED

ALSO ACCEPTABLE:
Step 1: compare_file_implementations(...)
Step 2: merge_file_implementations(...)
Result: ✅ Task RESOLVED

WRONG APPROACH:
compare_file_implementations(...) and STOP
Result: ❌ Task FAILED
```

**Impact**: AI sees clear examples of right vs wrong approaches.

### 3. Updated Tool Selection Guide
**Before:**
```
- Duplicates: compare_file_implementations → merge_file_implementations
```

**After:**
```
- Duplicates: merge_file_implementations (compare first if needed, but MUST merge)

⚠️ REMEMBER: compare_file_implementations is for UNDERSTANDING, not RESOLVING.
Always follow it with a resolving tool!
```

**Impact**: AI understands that compare is optional, merge is required.

### 4. Fixed Confusing Task Titles
**Before:**
```
Title: "Merge duplicates: resource_estimator.py ↔ resource_estimator.py"
```
When two files in different directories had the same name, the title showed the same filename twice, which was confusing.

**After:**
```
Title: "Merge duplicates: resources/resource_estimator.py ↔ services/resource_estimator.py"
```
Now shows parent directory + filename, making it clear these are different files.

**Impact**: Task titles are clearer and less confusing.

## Expected Behavior

### Before Fix:
- ❌ AI compares files
- ❌ Task fails: "only analysis performed"
- ❌ Next iteration: AI compares again
- ❌ Infinite loop (or succeeds after 2-3 tries)

### After Fix:
- ✅ AI merges files directly
- ✅ Task completes successfully
- ✅ No infinite loops
- ✅ Efficient refactoring

## Testing

```bash
cd /home/ai/AI/autonomy
git pull origin main
python3 run.py -vv ../web/
```

**Expected results**:
- AI should merge duplicates directly without comparing first
- Tasks should complete on first try
- No more "only analysis performed" failures
- Refactoring phase should progress smoothly

## Files Modified

1. `pipeline/phases/refactoring.py` - Updated prompts and task titles

## Commit

- **Commit**: 2a241a3
- **Message**: "fix: Critical prompt fixes - AI was following contradictory instructions"
- **Status**: ✅ Pushed to GitHub

## Lessons Learned

1. **Prompts and logic must align** - If the prompt says "do X then Y", the completion logic can't fail after X
2. **Be explicit about optional vs required** - Make it crystal clear what's optional and what's mandatory
3. **Provide concrete examples** - Show both correct and incorrect approaches
4. **Test the AI's perspective** - Think about what the AI sees and how it interprets instructions
5. **Task titles matter** - Confusing titles lead to confused AI decisions

This was a **critical system design flaw** where the instructions and enforcement were contradictory, causing the AI to fail repeatedly while following instructions correctly.