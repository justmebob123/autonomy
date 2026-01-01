# DateTime Serialization Fix

## Problem
The system was crashing with the error:
```
TypeError: Object of type datetime is not JSON serializable
```

This occurred when trying to save the pipeline state, specifically when serializing the `TaskAnalysisTracker` data.

## Root Cause
In `pipeline/state/task_analysis_tracker.py`:

1. **Line 132**: The `record_tool_call()` method was storing `datetime.now()` directly in the `tool_calls_history`:
   ```python
   self.tool_calls_history.append({
       "tool": tool_name,
       "arguments": arguments,
       "result": result,
       "timestamp": datetime.now()  # ← Raw datetime object
   })
   ```

2. **Line 394**: The `to_dict()` method was serializing `tool_calls_history` as-is without converting datetime objects to strings:
   ```python
   "tool_calls_history": state.tool_calls_history,  # ← Contains datetime objects
   ```

While the `completed_at` field in checkpoints was properly serialized using `.isoformat()`, the timestamps in tool call history were not.

## Solution
Modified the `to_dict()` method to properly serialize datetime objects in `tool_calls_history`:

```python
"tool_calls_history": [
    {
        **call,
        "timestamp": call["timestamp"].isoformat() if isinstance(call.get("timestamp"), datetime) else call.get("timestamp")
    }
    for call in state.tool_calls_history
],
```

Also updated the `from_dict()` method to properly deserialize the timestamps back to datetime objects:

```python
# Restore tool calls history with timestamp deserialization
state.tool_calls_history = []
for call in state_data.get("tool_calls_history", []):
    restored_call = call.copy()
    timestamp = call.get("timestamp")
    if timestamp and isinstance(timestamp, str):
        try:
            restored_call["timestamp"] = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            # If parsing fails, keep as string
            pass
    state.tool_calls_history.append(restored_call)
```

## Impact
- ✅ State can now be saved without JSON serialization errors
- ✅ Pipeline can continue running without crashes
- ✅ Tool call history timestamps are preserved correctly
- ✅ Backward compatible with existing state files

## Testing
After this fix:
1. The pipeline should save state successfully
2. No more "Object of type datetime is not JSON serializable" errors
3. Task analysis tracking continues to work correctly
4. Timestamps in tool call history are preserved across saves/loads