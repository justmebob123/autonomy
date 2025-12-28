# Message Bus System - Usage Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Publishing Messages](#publishing-messages)
4. [Subscribing to Messages](#subscribing-to-messages)
5. [Handling Messages](#handling-messages)
6. [Request-Response Pattern](#request-response-pattern)
7. [Message Search and Filtering](#message-search-and-filtering)
8. [Analytics and Monitoring](#analytics-and-monitoring)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)
11. [Troubleshooting](#troubleshooting)

---

## Getting Started

The Message Bus System is automatically initialized in the Coordinator and passed to all phases. No manual setup is required.

### Checking Message Bus Availability

```python
# In any phase
if self.message_bus:
    # Message bus is available
    self._publish_message(...)
else:
    # Message bus not available (backward compatibility mode)
    pass
```

---

## Basic Usage

### Example: Planning Phase Publishing Task Created

```python
class PlanningPhase(BasePhase):
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        # Create task
        task = state.add_task(
            description="Implement feature X",
            target_file="src/feature.py",
            priority=TaskPriority.NEW_TASK
        )
        
        # Publish TASK_CREATED message
        from ..messaging import MessageType, MessagePriority
        self._publish_message(
            message_type=MessageType.TASK_CREATED,
            payload={
                'task_id': task.task_id,
                'description': task.description,
                'target_file': task.target_file,
                'priority': str(task.priority)
            },
            recipient="broadcast",
            priority=MessagePriority.NORMAL,
            task_id=task.task_id,
            objective_id=objective_id,
            file_path=task.target_file
        )
        
        return PhaseResult(success=True, ...)
```

---

## Publishing Messages

### Broadcast Messages

Send to all subscribers:

```python
from ..messaging import MessageType, MessagePriority

# Broadcast task completion
self._publish_message(
    message_type=MessageType.TASK_COMPLETED,
    payload={
        'task_id': 'task_001',
        'file': 'src/feature.py',
        'lines_added': 150
    },
    recipient="broadcast",
    priority=MessagePriority.NORMAL,
    task_id='task_001',
    file_path='src/feature.py'
)
```

### Direct Messages

Send to specific phase:

```python
# Send directly to debugging phase
self._publish_message(
    message_type=MessageType.ISSUE_FOUND,
    payload={
        'issue_id': 'issue_001',
        'severity': 'critical',
        'description': 'Null pointer exception'
    },
    recipient="debugging",  # Direct to debugging
    priority=MessagePriority.CRITICAL,
    issue_id='issue_001',
    task_id='task_001'
)
```

### Priority Levels

Choose appropriate priority:

```python
# CRITICAL - Immediate attention required
self._publish_message(
    message_type=MessageType.OBJECTIVE_BLOCKED,
    payload={'objective_id': 'primary_001', 'reason': 'Missing dependencies'},
    priority=MessagePriority.CRITICAL
)

# HIGH - Important, handle soon
self._publish_message(
    message_type=MessageType.ISSUE_FOUND,
    payload={'issue_id': 'issue_001', 'severity': 'high'},
    priority=MessagePriority.HIGH
)

# NORMAL - Standard priority (default)
self._publish_message(
    message_type=MessageType.TASK_CREATED,
    payload={'task_id': 'task_001'},
    priority=MessagePriority.NORMAL
)

# LOW - Can be deferred
self._publish_message(
    message_type=MessageType.SYSTEM_INFO,
    payload={'info': 'Cache cleared'},
    priority=MessagePriority.LOW
)
```

---

## Subscribing to Messages

### In Phase __init__

Subscribe to relevant message types:

```python
class QAPhase(BasePhase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
                MessageType.TASK_COMPLETED,
                MessageType.FILE_CREATED,
                MessageType.FILE_MODIFIED,
                MessageType.SYSTEM_ALERT,
            ])
```

### Subscription Guidelines

**Planning Phase** should subscribe to:
- `OBJECTIVE_ACTIVATED` - New objective activated
- `OBJECTIVE_BLOCKED` - Objective blocked
- `SYSTEM_ALERT` - System alerts

**QA Phase** should subscribe to:
- `TASK_COMPLETED` - Task ready for review
- `FILE_CREATED` - New file to review
- `FILE_MODIFIED` - Modified file to review
- `SYSTEM_ALERT` - System alerts

**Debugging Phase** should subscribe to:
- `ISSUE_FOUND` - New issue to fix
- `TASK_FAILED` - Failed task to debug
- `PHASE_ERROR` - Phase errors
- `SYSTEM_ALERT` - System alerts

**Coordinator** should subscribe to:
- `OBJECTIVE_BLOCKED` - Blocked objectives
- `OBJECTIVE_CRITICAL` - Critical objectives
- `PHASE_ERROR` - Phase errors
- `SYSTEM_ALERT` - System alerts
- `HEALTH_DEGRADED` - Health issues
- `ISSUE_FOUND` - Critical issues

---

## Handling Messages

### In Phase execute()

Check for and process messages:

```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # Check for relevant messages
    if self.message_bus:
        from ..messaging import MessageType, MessagePriority
        
        messages = self._get_messages(
            message_types=[MessageType.ISSUE_FOUND, MessageType.TASK_FAILED],
            limit=10
        )
        
        if messages:
            self.logger.info(f"  📨 Received {len(messages)} messages")
            
            # Count critical messages
            critical_count = sum(
                1 for m in messages 
                if m.priority == MessagePriority.CRITICAL
            )
            
            if critical_count > 0:
                self.logger.warning(f"    ⚠️ {critical_count} CRITICAL messages")
            
            # Log first few messages
            for msg in messages[:3]:
                self.logger.info(
                    f"    • {msg.message_type.value}: "
                    f"{msg.payload.get('issue_id', 'N/A')}"
                )
            
            # Clear processed messages
            self._clear_messages([msg.id for msg in messages])
    
    # Continue with phase execution
    ...
```

### Processing Message Content

```python
# Extract data from messages
for msg in messages:
    if msg.message_type == MessageType.ISSUE_FOUND:
        issue_id = msg.payload['issue_id']
        severity = msg.payload['severity']
        file_path = msg.file_path
        
        # Process the issue
        self.fix_issue(issue_id, severity, file_path)
    
    elif msg.message_type == MessageType.TASK_FAILED:
        task_id = msg.payload['task_id']
        error = msg.payload.get('error', 'Unknown error')
        
        # Handle the failure
        self.handle_failure(task_id, error)
```

---

## Request-Response Pattern

### Sending a Request

```python
# Request status from another phase
if self.message_bus:
    from ..messaging import MessageType
    
    response = self.message_bus.request_response(
        sender=self.phase_name,
        recipient="coding",
        message_type=MessageType.PHASE_REQUEST,
        payload={'action': 'get_status'},
        timeout=30  # Wait up to 30 seconds
    )
    
    if response:
        status = response.payload['status']
        tasks_pending = response.payload['tasks_pending']
        self.logger.info(f"Coding phase status: {status}, pending: {tasks_pending}")
    else:
        self.logger.warning("Request timed out")
```

### Responding to a Request

```python
# In phase execution, check for requests
messages = self._get_messages(
    message_types=[MessageType.PHASE_REQUEST]
)

for request in messages:
    if request.requires_response:
        # Process request
        action = request.payload['action']
        
        if action == 'get_status':
            # Send response
            self.message_bus.send_response(
                original_message=request,
                sender=self.phase_name,
                payload={
                    'status': 'ready',
                    'tasks_pending': len(self.pending_tasks)
                }
            )
```

---

## Message Search and Filtering

### Basic Filtering

```python
# Get messages by type
messages = self._get_messages(
    message_types=[MessageType.ISSUE_FOUND, MessageType.ISSUE_RESOLVED]
)

# Get messages by priority
critical_messages = self._get_messages(
    priority=MessagePriority.CRITICAL
)

# Get recent messages
recent_messages = self._get_messages(
    since=datetime.now() - timedelta(hours=1),
    limit=20
)
```

### Advanced Search

```python
# Search across all messages
from ..messaging import MessageType

# Search by objective
obj_messages = self.message_bus.search_messages(
    objective_id="primary_001",
    message_types=[MessageType.TASK_CREATED, MessageType.TASK_COMPLETED],
    since=datetime.now() - timedelta(days=1)
)

# Search by task
task_messages = self.message_bus.search_messages(
    task_id="task_001",
    limit=50
)

# Complex search
results = self.message_bus.search_messages(
    sender="qa",
    recipient="debugging",
    message_types=[MessageType.ISSUE_FOUND],
    since=datetime.now() - timedelta(hours=6),
    until=datetime.now() - timedelta(hours=1),
    priority=MessagePriority.CRITICAL
)
```

---

## Analytics and Monitoring

### Frequency Analysis

```python
from ..messaging import MessageAnalytics
from datetime import timedelta

analytics = MessageAnalytics(self.message_bus)

# Analyze last 24 hours
freq = analytics.get_frequency_analysis(timedelta(hours=24))

print(f"Total messages: {freq['total_messages']}")
print(f"Messages/hour: {freq['messages_per_hour']:.2f}")
print(f"Top message types:")
for msg_type, count in list(freq['by_type'].items())[:5]:
    print(f"  {msg_type}: {count}")
```

### Pattern Detection

```python
# Detect patterns in last hour
patterns = analytics.detect_patterns(timedelta(hours=1))

# Check for repeated errors
if patterns['repeated_errors']:
    print("⚠️ Repeated errors detected:")
    for error in patterns['repeated_errors']:
        print(f"  {error['sender']}: {error['type']} ({error['count']} times)")

# Check for message bursts
if patterns['message_bursts']:
    print("📈 Message bursts detected:")
    for burst in patterns['message_bursts']:
        print(f"  {burst['time']}: {burst['count']} messages")

# Check for slow responses
if patterns['slow_responses']:
    print("🐌 Slow responses detected:")
    for slow in patterns['slow_responses']:
        print(f"  {slow['sender']} → {slow['recipient']}: {slow['delay_seconds']:.1f}s")
```

### Performance Metrics

```python
# Get performance metrics
perf = analytics.get_performance_metrics(timedelta(hours=24))

print(f"Processing rate: {perf['processing_rate']:.2f} msg/sec")
print(f"Critical message ratio: {perf['critical_message_ratio']:.2%}")

if perf['response_times']:
    rt = perf['response_times']
    print(f"Response times:")
    print(f"  Average: {rt['avg']:.2f}s")
    print(f"  Median: {rt['median']:.2f}s")
    print(f"  Min: {rt['min']:.2f}s")
    print(f"  Max: {rt['max']:.2f}s")
```

### Generate Report

```python
# Generate comprehensive report
report = analytics.generate_report(timedelta(hours=24))
print(report)

# Save report to file
with open('message_bus_report.txt', 'w') as f:
    f.write(report)
```

---

## Best Practices

### 1. Always Check Message Bus Availability

```python
# Good
if self.message_bus:
    self._publish_message(...)

# Bad - will fail if message bus not available
self._publish_message(...)
```

### 2. Use Appropriate Priorities

```python
# Critical - system broken, immediate attention
MessagePriority.CRITICAL

# High - important issue, handle soon
MessagePriority.HIGH

# Normal - standard operation (default)
MessagePriority.NORMAL

# Low - informational, can wait
MessagePriority.LOW
```

### 3. Include Context in Messages

```python
# Good - includes all context
self._publish_message(
    message_type=MessageType.ISSUE_FOUND,
    payload={'issue_id': 'issue_001', 'description': '...'},
    task_id='task_001',
    objective_id='primary_001',
    file_path='src/feature.py',
    issue_id='issue_001'
)

# Bad - missing context
self._publish_message(
    message_type=MessageType.ISSUE_FOUND,
    payload={'issue_id': 'issue_001'}
)
```

### 4. Clear Processed Messages

```python
# Good - clear after processing
messages = self._get_messages(...)
for msg in messages:
    process(msg)
self._clear_messages([msg.id for msg in messages])

# Bad - messages accumulate
messages = self._get_messages(...)
for msg in messages:
    process(msg)
# Messages never cleared!
```

### 5. Subscribe Only to Relevant Types

```python
# Good - only what you need
self._subscribe_to_messages([
    MessageType.TASK_COMPLETED,
    MessageType.FILE_MODIFIED
])

# Bad - subscribing to everything
self._subscribe_to_messages(list(MessageType))
```

### 6. Handle Timeouts in Request-Response

```python
# Good - handle timeout
response = self.message_bus.request_response(...)
if response:
    process(response)
else:
    self.logger.warning("Request timed out")
    handle_timeout()

# Bad - assume response always arrives
response = self.message_bus.request_response(...)
process(response)  # Will fail if None!
```

### 7. Log Message Activity

```python
# Good - log for visibility
if messages:
    self.logger.info(f"📨 Received {len(messages)} messages")
    for msg in messages[:3]:
        self.logger.info(f"  • {msg.message_type.value}")

# Bad - silent processing
if messages:
    for msg in messages:
        process(msg)
```

---

## Common Patterns

### Pattern 1: Task Lifecycle

```python
# Planning creates task
self._publish_message(
    message_type=MessageType.TASK_CREATED,
    payload={'task_id': 'task_001'},
    task_id='task_001'
)

# Coding starts task
self._publish_message(
    message_type=MessageType.TASK_STARTED,
    payload={'task_id': 'task_001'},
    task_id='task_001'
)

# Coding completes task
self._publish_message(
    message_type=MessageType.TASK_COMPLETED,
    payload={'task_id': 'task_001', 'file': 'src/feature.py'},
    task_id='task_001',
    file_path='src/feature.py'
)
```

### Pattern 2: Issue Lifecycle

```python
# QA finds issue
self._publish_message(
    message_type=MessageType.ISSUE_FOUND,
    payload={'issue_id': 'issue_001', 'severity': 'high'},
    priority=MessagePriority.HIGH,
    issue_id='issue_001',
    task_id='task_001'
)

# Debugging starts fixing
self._publish_message(
    message_type=MessageType.ISSUE_IN_PROGRESS,
    payload={'issue_id': 'issue_001'},
    issue_id='issue_001'
)

# Debugging resolves issue
self._publish_message(
    message_type=MessageType.ISSUE_RESOLVED,
    payload={'issue_id': 'issue_001', 'resolution': 'Fixed null check'},
    issue_id='issue_001'
)

# QA verifies fix
self._publish_message(
    message_type=MessageType.ISSUE_VERIFIED,
    payload={'issue_id': 'issue_001'},
    issue_id='issue_001'
)
```

### Pattern 3: Objective Monitoring

```python
# Coordinator activates objective
self.message_bus.broadcast(
    sender="coordinator",
    message_type=MessageType.OBJECTIVE_ACTIVATED,
    payload={'objective_id': 'primary_001', 'title': 'Core Features'},
    objective_id='primary_001'
)

# Phase detects objective blocked
self._publish_message(
    message_type=MessageType.OBJECTIVE_BLOCKED,
    payload={'objective_id': 'primary_001', 'reason': 'Missing dependencies'},
    priority=MessagePriority.CRITICAL,
    objective_id='primary_001'
)

# Coordinator monitors and responds
messages = self.message_bus.get_messages(
    "coordinator",
    message_types=[MessageType.OBJECTIVE_BLOCKED],
    priority=MessagePriority.CRITICAL
)
```

### Pattern 4: Health Monitoring

```python
# System detects degraded health
self._publish_message(
    message_type=MessageType.HEALTH_DEGRADED,
    payload={'component': 'database', 'metric': 'response_time', 'value': 5000},
    priority=MessagePriority.HIGH
)

# System recovers
self._publish_message(
    message_type=MessageType.HEALTH_RECOVERED,
    payload={'component': 'database', 'metric': 'response_time', 'value': 100},
    priority=MessagePriority.NORMAL
)
```

---

## Troubleshooting

### Messages Not Being Received

**Problem**: Phase not receiving expected messages

**Solutions**:
1. Check subscription:
```python
# Verify subscription in __init__
if self.message_bus:
    self._subscribe_to_messages([MessageType.TASK_COMPLETED])
```

2. Check message type matches:
```python
# Sender uses TASK_COMPLETED
self._publish_message(message_type=MessageType.TASK_COMPLETED, ...)

# Receiver subscribes to TASK_COMPLETED
self._subscribe_to_messages([MessageType.TASK_COMPLETED])
```

3. Check recipient:
```python
# For broadcast, use "broadcast"
self._publish_message(recipient="broadcast", ...)

# For direct, use exact phase name
self._publish_message(recipient="qa", ...)
```

### Messages Accumulating

**Problem**: Message queue growing too large

**Solutions**:
1. Clear processed messages:
```python
messages = self._get_messages(...)
# Process messages
self._clear_messages([msg.id for msg in messages])
```

2. Use message limits:
```python
# Only get recent messages
messages = self._get_messages(
    since=datetime.now() - timedelta(hours=1),
    limit=100
)
```

### Request-Response Timeout

**Problem**: Request-response always timing out

**Solutions**:
1. Increase timeout:
```python
response = self.message_bus.request_response(
    ...,
    timeout=120  # Increase from default 60
)
```

2. Check recipient is processing requests:
```python
# In recipient phase
messages = self._get_messages(
    message_types=[MessageType.PHASE_REQUEST]
)
for request in messages:
    if request.requires_response:
        self.message_bus.send_response(...)
```

### Performance Issues

**Problem**: Message bus slowing down system

**Solutions**:
1. Limit message history:
```python
self.message_bus.max_history_size = 5000  # Reduce from 10000
```

2. Reduce message TTL:
```python
self.message_bus.message_ttl = timedelta(hours=12)  # Reduce from 24
```

3. Clear old messages:
```python
# Periodically clear old messages
self._clear_messages()
```

---

## Additional Resources

- [API Reference](MESSAGE_BUS_API_REFERENCE.md) - Complete API documentation
- [PHASE1_WEEK1_COMPLETE.md](PHASE1_WEEK1_COMPLETE.md) - Core infrastructure details
- [PHASE1_WEEK2_COMPLETE.md](PHASE1_WEEK2_COMPLETE.md) - Phase integration details
- [PHASE1_WEEK3_COMPLETE.md](PHASE1_WEEK3_COMPLETE.md) - Advanced features details

---

*Message Bus System v1.0 - Complete implementation with analytics and monitoring*