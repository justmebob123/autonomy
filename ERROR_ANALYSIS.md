# CRITICAL ERROR ANALYSIS

## Error from User's Output

```
14:34:49 [ERROR] Phase planning failed: MessageBus.publish() got an unexpected keyword argument 'source'
Traceback (most recent call last):
  File "/home/ai/AI/autonomy/pipeline/phases/base.py", line 381, in run
    result = self.execute(state, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ai/AI/autonomy/pipeline/phases/planning.py", line 134, in execute
    self._publish_architecture_events(validation, diff)
  File "/home/ai/AI/autonomy/pipeline/phases/planning.py", line 1198, in _publish_architecture_events
    self.message_bus.publish(
TypeError: MessageBus.publish() got an unexpected keyword argument 'source'
```

## Error Details

- **Error Type**: TypeError
- **Location**: `pipeline/phases/planning.py`, line 1198, in `_publish_architecture_events`
- **Root Cause**: Calling `MessageBus.publish()` with a `source` parameter that doesn't exist
- **Impact**: Planning phase completely fails, blocking entire pipeline

## Key Questions

1. What is the actual signature of `MessageBus.publish()`?
2. Where are all the calls to `MessageBus.publish()` with 'source' parameter?
3. Why didn't the method signature validator catch this?
4. How many files have this error?

## Investigation Results

### 1. MessageBus.publish() Signature

**ACTUAL SIGNATURE:**
```
def publish(self, message: Message) -> None:
```

**EXPECTED USAGE:**
- Takes a single `Message` object
- Message object has fields: sender, recipient, message_type, priority, payload, etc.

### 2. Incorrect Usage Pattern Found

**LOCATIONS WITH ERRORS:**
- `pipeline/phases/planning.py`: Lines 1198, 1212, 1225, 1236 (4 calls)
- `pipeline/phases/documentation.py`: Line 711 (1 call)

**INCORRECT PATTERN:**
```
self.message_bus.publish(
    MessageType.SYSTEM_ALERT,  # WRONG - passing MessageType directly
    source=self.phase_name,     # WRONG - 'source' is not a parameter
    payload={...}               # WRONG - 'payload' is not a parameter
)
```

**CORRECT PATTERN:**
```
from ..messaging import Message, MessageType, MessagePriority

self.message_bus.publish(
    Message(
        sender=self.phase_name,
        recipient="broadcast",
        message_type=MessageType.SYSTEM_ALERT,
        priority=MessagePriority.HIGH,
        payload={...}
    )
)
```

### 3. Why Validation Tools Missed This

**CRITICAL FINDING:** The method signature validator is NOT checking:
- Parameter names in method calls
- Whether positional arguments match expected types
- Whether keyword arguments exist in the method signature

The validator only checks:
- If the method exists on the class
- Basic type compatibility (but not for kwargs)

### 4. Total Error Count

**5 CRITICAL ERRORS** across 2 files:
- planning.py: 4 errors
- documentation.py: 1 error