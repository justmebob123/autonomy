# CRITICAL FIX: Error Strategy Prompt Ordering

## Problem Identified

The system was stuck in a loop where the AI would:
1. Fix one error (e.g., `UnboundLocalError` with yaml import)
2. Introduce a new error (e.g., `TypeError: unexpected keyword argument 'servers'`)
3. Make superficial fixes without investigation (just remove the parameter)
4. Introduce yet another error (cascading failures)

**Root Cause:** The error-specific strategies were being **APPENDED** to the prompt, appearing AFTER the generic instructions that said "DO NOT call search_code or read_file - you already have everything you need below."

## The Cascade of Failures

### What Was Happening:

```
PROMPT STRUCTURE (BEFORE FIX):
┌─────────────────────────────────────────┐
│ YOU MUST FIX THIS ERROR BY CALLING      │
│ modify_python_file                      │
│                                         │
│ DO NOT call search_code or read_file   │  ← AI sees this FIRST
│ - you already have everything below.    │
│                                         │
│ [File content here]                     │
│                                         │
│ ## ERROR-SPECIFIC STRATEGY: TypeError   │  ← AI sees this LAST
│                                         │
│ STEP 1: Use investigate_parameter_      │  ← Too late! Already
│ removal to understand what 'servers'    │     decided to skip
│ does                                    │     investigation
└─────────────────────────────────────────┘
```

**Result:** AI followed the emphatic "DO NOT call other tools" instruction and ignored the strategy that came later.

### Example from User's Output:

**Iteration 6:**
```
TypeError: JobExecutor.__init__() got an unexpected keyword argument 'servers'
```

**What AI Did:**
1. Saw "DO NOT call search_code or read_file"
2. Called `modify_python_file` immediately
3. Removed `servers` parameter without investigation
4. Introduced new error (because `servers` data was needed elsewhere)

**What AI SHOULD Have Done:**
1. See TypeError strategy FIRST
2. Call `investigate_parameter_removal(parameter_name='servers')`
3. Understand where `servers` data comes from
4. Fix the data source OR remove parameter based on investigation
5. Make informed decision

## The Fix

Changed `error_strategies.py` to **PREPEND** the strategy instead of appending:

```python
# BEFORE (BROKEN):
return base_prompt + enhancement  # Strategy at END

# AFTER (FIXED):
return enhancement + base_prompt  # Strategy at BEGINNING
```

Also updated the enhancement to be more emphatic:

```python
enhancement = f"""
## ⚠️ ERROR-SPECIFIC STRATEGY: {self.error_type} ⚠️

### MANDATORY Investigation Steps (DO THESE FIRST):
{investigation}

### Recommended Fix Approaches:
{approaches}

## ⚠️ YOU MUST FOLLOW THE STRATEGY ABOVE BEFORE MAKING ANY CHANGES ⚠️

"""
```

And softened the generic prompt to defer to strategies:

```python
# BEFORE (BROKEN):
DO NOT call search_code or read_file - you already have everything you need below.

# AFTER (FIXED):
IMPORTANT: If an ERROR-SPECIFIC STRATEGY appears above, you MUST follow it first.
Otherwise, find line {line_num}, understand the error, and call modify_python_file to fix it.
```

## New Prompt Structure

```
PROMPT STRUCTURE (AFTER FIX):
┌─────────────────────────────────────────┐
│ ⚠️ ERROR-SPECIFIC STRATEGY: TypeError ⚠️│  ← AI sees this FIRST
│                                         │
│ MANDATORY Investigation Steps:          │
│ 1. CRITICAL: This is a function call    │
│    parameter error                      │
│ 2. STEP 1: Use investigate_parameter_   │
│    removal to understand what 'servers' │
│    does                                 │
│ 3. STEP 2: Check where data comes from  │
│                                         │
│ ⚠️ YOU MUST FOLLOW THE STRATEGY ABOVE ⚠️│
│                                         │
│ FIX THIS ERROR IN src/main.py           │  ← Generic instructions
│                                         │     come AFTER
│ IMPORTANT: If an ERROR-SPECIFIC         │
│ STRATEGY appears above, you MUST        │
│ follow it first.                        │
│                                         │
│ [File content here]                     │
└─────────────────────────────────────────┘
```

## Expected Behavior After Fix

**Iteration 6 (with fix):**
```
TypeError: JobExecutor.__init__() got an unexpected keyword argument 'servers'
```

**What AI Will Now Do:**
1. ✅ See TypeError strategy FIRST (at top of prompt)
2. ✅ Read "MANDATORY Investigation Steps (DO THESE FIRST)"
3. ✅ Call `investigate_parameter_removal(parameter_name='servers')`
4. ✅ Investigation shows: "servers data comes from config, used in 3 places"
5. ✅ Investigation recommends: "Fix data source, don't remove parameter"
6. ✅ AI fixes the actual root cause instead of making superficial change
7. ✅ No cascading errors!

## Files Modified

1. **pipeline/error_strategies.py**
   - Changed `enhance_prompt()` to prepend strategy instead of append
   - Added emphatic warnings with ⚠️ symbols
   - Made investigation steps "MANDATORY"

2. **pipeline/prompts.py**
   - Removed "DO NOT call other tools" instruction
   - Added "If strategy appears above, follow it first"
   - Made generic instructions defer to strategies

## Commit

```
commit 7221aa2
CRITICAL: Prepend error strategies so AI sees them FIRST before generic instructions
```

## Testing

User should now test with:
```bash
cd ~/code/AI/autonomy
git pull origin main
python3 run.py --debug-qa -vv --follow /path/to/log --command "./autonomous ../my_project/" ../test-automation/
```

**Expected Result:**
- AI will see TypeError strategy first
- AI will call `investigate_parameter_removal` before making changes
- AI will make informed decisions based on investigation
- No more cascading errors from superficial fixes

## Why This Matters

This is a **fundamental architectural fix** to how the AI processes instructions:

**Before:** Generic instructions → Specific strategy (ignored)
**After:** Specific strategy → Generic instructions (deferred to strategy)

This ensures that error-specific expertise is always applied BEFORE generic approaches, preventing the superficial fixes that were causing infinite loops.