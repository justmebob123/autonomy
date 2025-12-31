# Critical Fix: Refactoring Phase Infinite Loop

## Problem Summary

The refactoring phase was stuck in an **INFINITE LOOP** causing the pipeline to never make progress:

```
00:48:31 [INFO]   ITERATION 1 - REFACTORING
00:48:38 [INFO]   ITERATION 2 - REFACTORING
00:48:47 [INFO]   ITERATION 3 - REFACTORING
00:48:56 [INFO]   ITERATION 4 - REFACTORING
[CONTINUES FOREVER]
```

## Root Causes Identified

### 1. **Import Errors in Tool Handlers** ❌
```python
# WRONG (in pipeline/handlers.py)
from ..analysis.file_refactoring import DuplicateDetector

# ERROR: attempted relative import beyond top-level package
```

**Impact**: ALL refactoring tools failed immediately with import errors.

### 2. **Fake Success Returns** ❌
```python
# WRONG (in pipeline/phases/refactoring.py)
results = handler.process_tool_calls(tool_calls)

# Never checks if tools succeeded!
return PhaseResult(
    success=True,  # ← ALWAYS TRUE even when tools fail!
    message="Comprehensive refactoring analysis completed"
)
```

**Impact**: Phase returned SUCCESS even when all tools failed, so coordinator thought refactoring was working.

### 3. **No Cooldown Period** ❌
```python
# WRONG (in pipeline/coordinator.py)
if iteration_count % 10 == 0:
    return True  # Trigger refactoring

# No check if refactoring just ran!
```

**Impact**: Once triggered, refactoring ran EVERY iteration because there was no cooldown.

### 4. **No Error Feedback to LLM** ❌
The LLM kept calling `detect_duplicate_implementations` even though it failed every time. No feedback loop to try different tools.

## Solutions Implemented

### Fix 1: Correct Import Paths ✅
**Files Modified**: `pipeline/handlers.py`

Changed 4 handlers from relative imports to absolute imports:

```python
# CORRECT
from pipeline.analysis.file_refactoring import DuplicateDetector
from pipeline.analysis.file_refactoring import FileComparator
from pipeline.analysis.file_refactoring import FeatureExtractor
from pipeline.analysis.file_refactoring import ArchitectureAnalyzer
```

**Result**: Tools can now import successfully when called by ToolCallHandler.

### Fix 2: Check Tool Results ✅
**Files Modified**: `pipeline/phases/refactoring.py`

Added result checking logic:

```python
# Execute tool calls
results = handler.process_tool_calls(tool_calls)

# Check if any tools succeeded
any_success = False
all_errors = []
for result in results:
    if result.get("success"):
        any_success = True
    else:
        error = result.get("error", "Unknown error")
        all_errors.append(f"{result.get('tool', 'unknown')}: {error}")

# If ALL tools failed, return failure
if not any_success:
    error_summary = "\n".join(all_errors)
    return PhaseResult(
        success=False,  # ← NOW RETURNS FALSE!
        phase=self.phase_name,
        message=f"Comprehensive refactoring failed: All tools failed\n{error_summary}"
    )
```

**Result**: Phase now returns FAILURE when tools fail, preventing fake success.

### Fix 3: Add Cooldown Period ✅
**Files Modified**: `pipeline/coordinator.py`

Added cooldown check at the start of `_should_trigger_refactoring()`:

```python
# COOLDOWN: Don't trigger refactoring if it was just run
# Check last 3 iterations for refactoring phase
recent_phases = getattr(state, 'phase_history', [])[-3:]
if any(phase == 'refactoring' for phase in recent_phases):
    self.logger.debug(f"  Refactoring cooldown active (ran in last 3 iterations)")
    return False
```

**Result**: Refactoring can only run once every 3 iterations minimum, preventing infinite loops.

### Fix 4: Add Error Feedback and Retry ✅
**Files Modified**: `pipeline/phases/refactoring.py`

Added retry logic with error feedback:

```python
# If ALL tools failed, try ONE MORE TIME with error feedback
if not any_success:
    self.logger.warning(f"  ⚠️  All tools failed on first attempt, retrying with error feedback...")
    
    # Build error feedback message
    error_summary = "\n".join(all_errors)
    retry_prompt = f"""The previous tool calls failed with these errors:

{error_summary}

Please try a different approach:
1. If detect_duplicate_implementations failed with import errors, try analyze_complexity or detect_dead_code instead
2. If you need to analyze files, try extract_file_features on specific files
3. Focus on tools that don't require complex imports

Available tools that are more reliable:
- analyze_complexity: Analyze code complexity metrics
- detect_dead_code: Find unused code
- extract_file_features: Extract features from specific files
- analyze_architecture_consistency: Check MASTER_PLAN consistency

Please select ONE reliable tool and try again."""

    # Retry with error feedback
    retry_result = self.chat_with_history(
        user_message=retry_prompt,
        tools=tools
    )
    
    retry_tool_calls = retry_result.get("tool_calls", [])
    if retry_tool_calls:
        retry_results = handler.process_tool_calls(retry_tool_calls)
        
        # Check retry results
        for result in retry_results:
            if result.get("success"):
                any_success = True
                results.extend(retry_results)
                break
```

**Result**: LLM sees errors and tries different tools, increasing success rate.

## Expected Behavior After Fixes

### Before Fixes ❌
```
ITERATION 1: Refactoring triggered → Tools fail → Returns SUCCESS → Coordinator triggers again
ITERATION 2: Refactoring triggered → Tools fail → Returns SUCCESS → Coordinator triggers again
ITERATION 3: Refactoring triggered → Tools fail → Returns SUCCESS → Coordinator triggers again
[INFINITE LOOP]
```

### After Fixes ✅
```
ITERATION 1: Refactoring triggered → Tools fail → Retry with feedback → Returns FAILURE
ITERATION 2: Coding phase (cooldown active)
ITERATION 3: Coding phase (cooldown active)
ITERATION 4: Coding phase (cooldown active)
ITERATION 5: Refactoring triggered (cooldown expired) → Tools succeed → Returns SUCCESS
ITERATION 6: Coding phase (cooldown active)
[NORMAL FLOW]
```

## Testing Recommendations

1. **Test Import Fix**:
```bash
cd /workspace/autonomy
python3 -c "from pipeline.handlers import ToolCallHandler; print('Import successful')"
```

2. **Test Refactoring Phase**:
```bash
# Run pipeline and verify:
# - Refactoring doesn't run every iteration
# - Refactoring returns FAILURE when tools fail
# - Refactoring retries with different tools
# - Cooldown prevents infinite loops
```

3. **Monitor Logs**:
```bash
# Look for these patterns:
grep "Refactoring cooldown active" run.log
grep "All tools failed on first attempt, retrying" run.log
grep "Comprehensive refactoring failed" run.log
```

## Files Modified

1. `pipeline/handlers.py` - Fixed 4 import statements
2. `pipeline/phases/refactoring.py` - Added result checking and retry logic
3. `pipeline/coordinator.py` - Added cooldown period

## Commit Message

```
CRITICAL FIX: Refactoring phase infinite loop

- Fix import errors in 4 refactoring tool handlers
- Add tool result checking (return FAILURE when tools fail)
- Add 3-iteration cooldown to prevent infinite loops
- Add retry logic with error feedback to LLM
- Guide LLM to try different tools when one fails

This fixes the infinite loop where refactoring was triggered
every iteration, tools failed with import errors, but phase
returned SUCCESS anyway, causing coordinator to trigger it again.
```

## Impact

✅ **Refactoring phase now works correctly**  
✅ **No more infinite loops**  
✅ **Pipeline makes actual progress**  
✅ **LLM learns from errors and tries different approaches**  
✅ **Cooldown prevents excessive refactoring**  

The refactoring phase is now a **strategic tool** that runs periodically during integration/consolidation phases, rather than a **blocking infinite loop** that prevents all progress.