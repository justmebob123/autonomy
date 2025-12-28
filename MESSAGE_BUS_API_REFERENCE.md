# Message Bus System - API Reference

## Overview

The Message Bus System provides structured, event-driven communication between phases in the autonomy pipeline. This document provides complete API reference for all classes and methods.

## Table of Contents

1. [Message Class](#message-class)
2. [MessageType Enum](#messagetype-enum)
3. [MessagePriority Enum](#messagepriority-enum)
4. [MessageBus Class](#messagebus-class)
5. [MessageAnalytics Class](#messageanalytics-class)
6. [BasePhase Integration](#basephase-integration)

---

## Message Class

Represents a single message in the message bus system.

### Constructor

```python
Message(
    id: str = auto_generated,
    timestamp: datetime = now,
    sender: str = "",
    recipient: str = "",
    message_type: MessageType = MessageType.SYSTEM_INFO,
    priority: MessagePriority = MessagePriority.NORMAL,
    payload: Dict[str, Any] = {},
    objective_id: Optional[str] = None,
    task_id: Optional[str] = None,
    issue_id: Optional[str] = None,
    file_path: Optional[str] = None,
    requires_response: bool = False,
    response_timeout: Optional[int] = None,
    in_response_to: Optional[str] = None,
    tags: list = [],
    metadata: Dict[str, Any] = {}
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | str | Unique message identifier (auto-generated UUID) |
| `timestamp` | datetime | Message creation timestamp |
| `sender` | str | Phase name that sent the message |
| `recipient` | str | Phase name or "broadcast" for all phases |
| `message_type` | MessageType | Type of message (enum) |
| `priority` | MessagePriority | Message priority (enum) |
| `payload` | Dict | Message content/data |
| `objective_id` | Optional[str] | Related objective ID |
| `task_id` | Optional[str] | Related task ID |
| `issue_id` | Optional[str] | Related issue ID |
| `file_path` | Optional[str] | Related file path |
| `requires_response` | bool | Whether message expects a response |
| `response_timeout` | Optional[int] | Response timeout in seconds |
| `in_response_to` | Optional[str] | ID of message this responds to |
| `tags` | list | Custom tags for categorization |
| `metadata` | Dict | Additional metadata |

### Methods

#### `to_dict() -> Dict[str, Any]`
Convert message to dictionary for serialization.

**Returns**: Dictionary representation of message

**Example**:
```python
msg_dict = message.to_dict()
```

#### `from_dict(data: Dict[str, Any]) -> Message` (classmethod)
Create message from dictionary.

**Parameters**:
- `data`: Dictionary with message data

**Returns**: Message instance

**Example**:
```python
message = Message.from_dict(msg_dict)
```

#### `is_broadcast() -> bool`
Check if this is a broadcast message.

**Returns**: True if broadcast, False otherwise

**Example**:
```python
if message.is_broadcast():
    print("Broadcast message")
```

#### `is_for_recipient(recipient: str) -> bool`
Check if message is for the given recipient.

**Parameters**:
- `recipient`: Phase name to check

**Returns**: True if for recipient or broadcast

**Example**:
```python
if message.is_for_recipient("qa"):
    process_message(message)
```

#### `is_critical() -> bool`
Check if message has critical priority.

**Returns**: True if CRITICAL priority

**Example**:
```python
if message.is_critical():
    handle_immediately(message)
```

#### `is_high_priority() -> bool`
Check if message has high or critical priority.

**Returns**: True if HIGH or CRITICAL priority

**Example**:
```python
if message.is_high_priority():
    prioritize(message)
```

---

## MessageType Enum

Enumeration of all message types in the system.

### Task Lifecycle
- `TASK_CREATED` - New task created
- `TASK_STARTED` - Task execution started
- `TASK_COMPLETED` - Task completed successfully
- `TASK_FAILED` - Task execution failed
- `TASK_BLOCKED` - Task blocked by dependencies

### Issue Lifecycle
- `ISSUE_FOUND` - Quality issue detected
- `ISSUE_ASSIGNED` - Issue assigned to phase
- `ISSUE_IN_PROGRESS` - Issue being fixed
- `ISSUE_RESOLVED` - Issue fixed
- `ISSUE_VERIFIED` - Fix verified by QA
- `ISSUE_CLOSED` - Issue closed
- `ISSUE_REOPENED` - Issue reopened

### Objective Lifecycle
- `OBJECTIVE_ACTIVATED` - Objective activated
- `OBJECTIVE_BLOCKED` - Objective blocked
- `OBJECTIVE_DEGRADING` - Objective health degrading
- `OBJECTIVE_CRITICAL` - Objective in critical state
- `OBJECTIVE_COMPLETED` - Objective completed
- `OBJECTIVE_DOCUMENTED` - Objective documented

### Phase Coordination
- `PHASE_TRANSITION` - Phase transition occurring
- `PHASE_STARTED` - Phase execution started
- `PHASE_COMPLETED` - Phase execution completed
- `PHASE_ERROR` - Phase encountered error
- `PHASE_REQUEST` - Phase requesting action
- `PHASE_RESPONSE` - Phase responding to request
- `PHASE_TIMEOUT` - Phase operation timed out

### System Events
- `SYSTEM_ALERT` - System-level alert
- `SYSTEM_WARNING` - System warning
- `SYSTEM_INFO` - System information
- `HEALTH_CHECK` - Health check message
- `HEALTH_DEGRADED` - System health degraded
- `HEALTH_RECOVERED` - System health recovered

### File Events
- `FILE_CREATED` - File created
- `FILE_MODIFIED` - File modified
- `FILE_DELETED` - File deleted
- `FILE_QA_PASSED` - File passed QA
- `FILE_QA_FAILED` - File failed QA

### Analytics Events
- `PREDICTION_GENERATED` - Prediction generated
- `ANOMALY_DETECTED` - Anomaly detected
- `TREND_IDENTIFIED` - Trend identified
- `METRIC_UPDATED` - Metric updated

---

## MessagePriority Enum

Message priority levels.

| Priority | Value | Description |
|----------|-------|-------------|
| `CRITICAL` | 0 | Immediate attention required |
| `HIGH` | 1 | Important, handle soon |
| `NORMAL` | 2 | Standard priority |
| `LOW` | 3 | Can be deferred |

---

## MessageBus Class

Central message bus for phase-to-phase communication.

### Constructor

```python
MessageBus(state_manager=None)
```

**Parameters**:
- `state_manager`: Optional StateManager for message persistence

### Publishing Methods

#### `publish(message: Message) -> None`
Publish a message to the bus.

**Parameters**:
- `message`: Message to publish

**Example**:
```python
message = Message(sender="planning", recipient="broadcast", ...)
bus.publish(message)
```

#### `send_direct(sender: str, recipient: str, message_type: MessageType, payload: Dict, priority: MessagePriority = NORMAL, **kwargs) -> Message`
Send a direct message to a specific phase.

**Parameters**:
- `sender`: Sending phase name
- `recipient`: Receiving phase name
- `message_type`: Type of message
- `payload`: Message payload
- `priority`: Message priority (default: NORMAL)
- `**kwargs`: Additional message fields

**Returns**: Created message

**Example**:
```python
msg = bus.send_direct(
    sender="planning",
    recipient="coding",
    message_type=MessageType.TASK_CREATED,
    payload={'task_id': 'task_001'},
    priority=MessagePriority.HIGH,
    task_id='task_001'
)
```

#### `broadcast(sender: str, message_type: MessageType, payload: Dict, priority: MessagePriority = NORMAL, **kwargs) -> Message`
Broadcast a message to all subscribers.

**Parameters**:
- `sender`: Sending phase name
- `message_type`: Type of message
- `payload`: Message payload
- `priority`: Message priority (default: NORMAL)
- `**kwargs`: Additional message fields

**Returns**: Created message

**Example**:
```python
msg = bus.broadcast(
    sender="qa",
    message_type=MessageType.ISSUE_FOUND,
    payload={'issue_id': 'issue_001', 'severity': 'critical'},
    priority=MessagePriority.CRITICAL,
    issue_id='issue_001'
)
```

#### `request_response(sender: str, recipient: str, message_type: MessageType, payload: Dict, timeout: int = 60, priority: MessagePriority = NORMAL) -> Optional[Message]`
Send a message and wait for a response.

**Parameters**:
- `sender`: Sending phase name
- `recipient`: Receiving phase name
- `message_type`: Type of message
- `payload`: Message payload
- `timeout`: Timeout in seconds (default: 60)
- `priority`: Message priority (default: NORMAL)

**Returns**: Response message or None if timeout

**Example**:
```python
response = bus.request_response(
    sender="planning",
    recipient="coding",
    message_type=MessageType.PHASE_REQUEST,
    payload={'action': 'get_status'},
    timeout=30
)

if response:
    status = response.payload['status']
```

#### `send_response(original_message: Message, sender: str, payload: Dict) -> Message`
Send a response to a message that requires a response.

**Parameters**:
- `original_message`: Message being responded to
- `sender`: Sending phase name
- `payload`: Response payload

**Returns**: Response message

**Example**:
```python
response = bus.send_response(
    original_message=request,
    sender="coding",
    payload={'status': 'ready', 'tasks_pending': 5}
)
```

### Subscription Methods

#### `subscribe(phase_name: str, message_types: List[MessageType]) -> None`
Subscribe a phase to specific message types.

**Parameters**:
- `phase_name`: Name of subscribing phase
- `message_types`: List of message types to subscribe to

**Example**:
```python
bus.subscribe("qa", [
    MessageType.TASK_COMPLETED,
    MessageType.FILE_MODIFIED
])
```

#### `unsubscribe(phase_name: str, message_types: Optional[List[MessageType]] = None) -> None`
Unsubscribe a phase from message types.

**Parameters**:
- `phase_name`: Name of phase
- `message_types`: List of types to unsubscribe from, or None for all

**Example**:
```python
# Unsubscribe from specific types
bus.unsubscribe("qa", [MessageType.TASK_COMPLETED])

# Unsubscribe from all
bus.unsubscribe("qa")
```

### Retrieval Methods

#### `get_messages(phase_name: str, since: Optional[datetime] = None, message_types: Optional[List[MessageType]] = None, priority: Optional[MessagePriority] = None, limit: Optional[int] = None) -> List[Message]`
Get messages for a specific phase.

**Parameters**:
- `phase_name`: Name of phase
- `since`: Only messages after this timestamp
- `message_types`: Filter by message types
- `priority`: Filter by priority
- `limit`: Maximum number of messages

**Returns**: List of messages (sorted by priority then timestamp)

**Example**:
```python
# Get all messages
messages = bus.get_messages("qa")

# Get recent critical messages
messages = bus.get_messages(
    "qa",
    since=datetime.now() - timedelta(hours=1),
    priority=MessagePriority.CRITICAL,
    limit=10
)
```

#### `search_messages(sender: Optional[str] = None, recipient: Optional[str] = None, message_types: Optional[List[MessageType]] = None, since: Optional[datetime] = None, until: Optional[datetime] = None, objective_id: Optional[str] = None, task_id: Optional[str] = None, issue_id: Optional[str] = None, limit: Optional[int] = None) -> List[Message]`
Search message history with various filters.

**Parameters**:
- `sender`: Filter by sender
- `recipient`: Filter by recipient
- `message_types`: Filter by message types
- `since`: Messages after this time
- `until`: Messages before this time
- `objective_id`: Filter by objective
- `task_id`: Filter by task
- `issue_id`: Filter by issue
- `limit`: Maximum results

**Returns**: List of matching messages (sorted newest first)

**Example**:
```python
# Search by objective
messages = bus.search_messages(
    objective_id="primary_001",
    message_types=[MessageType.ISSUE_FOUND],
    since=datetime.now() - timedelta(days=1)
)

# Complex search
messages = bus.search_messages(
    sender="qa",
    recipient="debugging",
    message_types=[MessageType.ISSUE_FOUND, MessageType.ISSUE_RESOLVED],
    task_id="task_001",
    limit=50
)
```

#### `clear_messages(phase_name: str, message_ids: Optional[List[str]] = None) -> int`
Clear messages from a phase's queue.

**Parameters**:
- `phase_name`: Name of phase
- `message_ids`: Specific message IDs to clear, or None for all

**Returns**: Number of messages cleared

**Example**:
```python
# Clear specific messages
cleared = bus.clear_messages("qa", ['msg_001', 'msg_002'])

# Clear all messages
cleared = bus.clear_messages("qa")
```

### Management Methods

#### `register_handler(phase_name: str, message_type: MessageType, handler: Callable[[Message], None]) -> None`
Register a handler function for a message type.

**Parameters**:
- `phase_name`: Name of phase
- `message_type`: Type of message to handle
- `handler`: Callback function that takes a Message

**Example**:
```python
def handle_issue(message: Message):
    issue_id = message.payload['issue_id']
    print(f"Handling issue: {issue_id}")

bus.register_handler("debugging", MessageType.ISSUE_FOUND, handle_issue)
```

#### `get_statistics() -> Dict`
Get message bus statistics.

**Returns**: Dictionary with statistics

**Example**:
```python
stats = bus.get_statistics()
print(f"Total published: {stats['total_published']}")
print(f"Total delivered: {stats['total_delivered']}")
print(f"By type: {stats['by_type']}")
```

---

## MessageAnalytics Class

Analytics engine for message bus.

### Constructor

```python
MessageAnalytics(message_bus: MessageBus)
```

**Parameters**:
- `message_bus`: MessageBus instance to analyze

### Methods

#### `get_frequency_analysis(time_window: Optional[timedelta] = None) -> Dict`
Analyze message frequency.

**Parameters**:
- `time_window`: Time window to analyze (None = all time)

**Returns**: Dictionary with frequency metrics

**Example**:
```python
analytics = MessageAnalytics(bus)
freq = analytics.get_frequency_analysis(timedelta(hours=24))

print(f"Total messages: {freq['total_messages']}")
print(f"Messages/hour: {freq['messages_per_hour']}")
print(f"Top types: {freq['by_type']}")
```

#### `detect_patterns(time_window: timedelta = timedelta(hours=1)) -> Dict`
Detect patterns in message flow.

**Parameters**:
- `time_window`: Time window to analyze

**Returns**: Dictionary with detected patterns

**Example**:
```python
patterns = analytics.detect_patterns(timedelta(hours=1))

for error in patterns['repeated_errors']:
    print(f"Repeated error: {error['sender']} - {error['type']}")

for burst in patterns['message_bursts']:
    print(f"Message burst: {burst['count']} messages at {burst['time']}")
```

#### `get_performance_metrics(time_window: Optional[timedelta] = None) -> Dict`
Calculate performance metrics.

**Parameters**:
- `time_window`: Time window to analyze

**Returns**: Dictionary with performance metrics

**Example**:
```python
perf = analytics.get_performance_metrics(timedelta(hours=24))

print(f"Processing rate: {perf['processing_rate']:.2f} msg/sec")
print(f"Critical ratio: {perf['critical_message_ratio']:.2%}")
print(f"Avg response time: {perf['response_times']['avg']:.2f}s")
```

#### `get_trend_analysis(time_windows: List[timedelta]) -> Dict`
Analyze trends over multiple time windows.

**Parameters**:
- `time_windows`: List of time windows to compare

**Returns**: Dictionary with trend analysis

**Example**:
```python
trends = analytics.get_trend_analysis([
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(hours=24)
])

for volume in trends['message_volume']:
    print(f"{volume['window']}: {volume['count']} messages")
```

#### `get_phase_communication_matrix() -> Dict`
Generate communication matrix between phases.

**Returns**: Dictionary with phase-to-phase communication counts

**Example**:
```python
matrix = analytics.get_phase_communication_matrix()

for sender, recipients in matrix['matrix'].items():
    for recipient, count in recipients.items():
        print(f"{sender} → {recipient}: {count} messages")
```

#### `get_objective_message_analysis() -> Dict`
Analyze messages by objective.

**Returns**: Dictionary with objective-level message analysis

**Example**:
```python
obj_analysis = analytics.get_objective_message_analysis()

for obj_id, data in obj_analysis.items():
    print(f"Objective {obj_id}:")
    print(f"  Total messages: {data['total']}")
    print(f"  Critical: {data['critical_count']}")
```

#### `generate_report(time_window: timedelta = timedelta(hours=24)) -> str`
Generate comprehensive analytics report.

**Parameters**:
- `time_window`: Time window for analysis

**Returns**: Formatted report string

**Example**:
```python
report = analytics.generate_report(timedelta(hours=24))
print(report)
```

---

## BasePhase Integration

Helper methods available in all phases for message bus interaction.

### Methods

#### `_publish_message(message_type, payload: Dict, recipient: str = "broadcast", priority=None, **kwargs)`
Publish a message to the message bus.

**Parameters**:
- `message_type`: MessageType enum value
- `payload`: Message payload dictionary
- `recipient`: Recipient phase name or "broadcast" (default: "broadcast")
- `priority`: MessagePriority enum value (default: NORMAL)
- `**kwargs`: Additional message fields

**Example**:
```python
# In a phase
self._publish_message(
    message_type=MessageType.TASK_CREATED,
    payload={'task_id': task.task_id, 'description': task.description},
    recipient="broadcast",
    priority=MessagePriority.NORMAL,
    task_id=task.task_id,
    objective_id=objective_id
)
```

#### `_subscribe_to_messages(message_types: List)`
Subscribe this phase to specific message types.

**Parameters**:
- `message_types`: List of MessageType enum values

**Example**:
```python
# In phase __init__
if self.message_bus:
    from ..messaging import MessageType
    self._subscribe_to_messages([
        MessageType.TASK_COMPLETED,
        MessageType.FILE_MODIFIED,
        MessageType.SYSTEM_ALERT,
    ])
```

#### `_get_messages(**kwargs)`
Get messages for this phase.

**Parameters**:
- `**kwargs`: Filtering options (since, message_types, priority, limit)

**Returns**: List of Message objects

**Example**:
```python
# In phase execute()
if self.message_bus:
    messages = self._get_messages(
        message_types=[MessageType.ISSUE_FOUND],
        priority=MessagePriority.CRITICAL,
        limit=10
    )
    for msg in messages:
        handle_message(msg)
```

#### `_clear_messages(message_ids=None)`
Clear messages from this phase's queue.

**Parameters**:
- `message_ids`: Specific message IDs to clear, or None for all

**Returns**: Number of messages cleared

**Example**:
```python
# After processing messages
processed_ids = [msg.id for msg in messages]
self._clear_messages(processed_ids)
```

---

## Usage Examples

See [MESSAGE_BUS_USAGE_GUIDE.md](MESSAGE_BUS_USAGE_GUIDE.md) for comprehensive usage examples and best practices.

---

## Performance Characteristics

- **Throughput**: 35,000+ messages/second
- **Search**: <1ms for typical queries
- **Memory**: Controlled with configurable limits
- **Thread Safety**: Full thread-safe operation
- **Scalability**: Tested with 10+ concurrent phases

---

## Configuration

### MessageBus Configuration

```python
# Default configuration
bus.max_history_size = 10000  # Maximum messages in history
bus.max_queue_size = 1000     # Maximum messages in queue
bus.message_ttl = timedelta(hours=24)  # Message expiration time
```

### Customization

```python
# Create bus with custom configuration
bus = MessageBus(state_manager=state_manager)
bus.max_history_size = 50000  # Increase history
bus.message_ttl = timedelta(days=7)  # Keep messages longer
```

---

## Error Handling

All methods handle errors gracefully:
- Invalid message types are logged
- Missing recipients are handled
- Timeout conditions are managed
- Thread safety is maintained

---

## Best Practices

1. **Always check if message_bus exists** before using it
2. **Clear processed messages** to prevent memory bloat
3. **Use appropriate priorities** for messages
4. **Subscribe only to relevant message types**
5. **Include context** (objective_id, task_id, etc.) in messages
6. **Handle timeouts** in request-response patterns
7. **Monitor critical messages** in coordinator
8. **Use analytics** to detect patterns and issues

---

## Version

Message Bus System v1.0
- Core Infrastructure: Complete
- Phase Integration: Complete
- Advanced Features: Complete
- Documentation: Complete

---

*For usage examples and tutorials, see [MESSAGE_BUS_USAGE_GUIDE.md](MESSAGE_BUS_USAGE_GUIDE.md)*