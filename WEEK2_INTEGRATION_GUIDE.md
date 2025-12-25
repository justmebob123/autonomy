# Week 2 Integration Guide

## Overview

This guide covers the integration of all Week 2 components into a cohesive self-designing AI system. Week 2 delivered 5 major systems that work together to create an adaptive, self-improving AI development pipeline.

## Components Overview

### Week 1 Components (Foundation)
1. **PromptArchitect** - AI designs custom prompts
2. **ToolDesigner** - AI creates custom tools
3. **RoleCreator** - AI designs specialist roles

### Week 2 Components (Advanced)
4. **LoopDetector** - Detects and prevents infinite loops
5. **TeamOrchestrator** - Coordinates parallel specialist execution

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Debugging Phase                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Main Execution Loop                        │ │
│  │                                                         │ │
│  │  1. Receive Error                                      │ │
│  │  2. Check Loop Detection ──────────┐                   │ │
│  │  3. Decide Approach                │                   │ │
│  │     ├─ Simple: Direct Fix          │                   │ │
│  │     ├─ Complex: Team Orchestration │                   │ │
│  │     └─ Novel: Create Custom Tools  │                   │ │
│  │  4. Execute Fix                    │                   │ │
│  │  5. Track Actions ─────────────────┘                   │ │
│  │  6. Validate & Continue                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Loop         │  │ Team         │  │ Prompt       │     │
│  │ Detection    │  │ Orchestrator │  │ Architect    │     │
│  │              │  │              │  │              │     │
│  │ - Track      │  │ - Parallel   │  │ - Design     │     │
│  │ - Detect     │  │ - Balance    │  │ - Optimize   │     │
│  │ - Intervene  │  │ - Synthesize │  │ - Validate   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Tool         │  │ Role         │  │ Specialist   │     │
│  │ Designer     │  │ Creator      │  │ Team         │     │
│  │              │  │              │  │              │     │
│  │ - Create     │  │ - Design     │  │ - Syntax     │     │
│  │ - Validate   │  │ - Instantiate│  │ - Whitespace │     │
│  │ - Register   │  │ - Coordinate │  │ - Pattern    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. Loop Detection Integration

**Location:** `pipeline/phases/debugging.py`

**Integration:**
```python
# After tool execution
self._track_tool_calls(tool_calls, results, agent="main")

# Check for loops
intervention = self._check_for_loops()
if intervention and intervention.get('requires_user_input'):
    # Escalate to user
    return PhaseResult(success=False, ...)
```

**Triggers:**
- After every tool execution
- In main fix attempt
- In retry attempt
- In conversation thread

**Actions:**
- Track all actions
- Detect 6 types of loops
- Provide targeted interventions
- Escalate after 3 failed interventions

### 2. Team Orchestrator Integration

**Location:** `pipeline/phases/debugging.py`

**Integration:**
```python
# Initialize in __init__
self.team_orchestrator = TeamOrchestrator(
    self.client,
    self.specialist_team,
    self.logger,
    max_workers=4
)

# Use for complex errors
if error_complexity == 'high':
    plan = self.team_orchestrator.create_orchestration_plan(
        problem=error_description,
        context={'file': filepath, 'thread': thread}
    )
    results = self.team_orchestrator.execute_plan(plan, thread)
```

**Triggers:**
- Complex errors with multiple issues
- Multi-file analysis needed
- Consensus building required
- Performance optimization desired

**Benefits:**
- 2-6x speedup on complex problems
- Multiple perspectives
- Parallel execution
- Better resource utilization

### 3. Prompt Architect Integration

**Location:** `pipeline/phases/debugging.py`

**Integration:**
```python
# Access via prompt_registry
custom_prompt = self.prompt_registry.get_prompt(
    'custom_debugging_prompt',
    variables={'error': error, 'context': context}
)

# Use in AI call
response = self.client.generate(
    prompt=custom_prompt,
    model=model,
    server=server
)
```

**Triggers:**
- Novel problem types
- Existing prompts insufficient
- Need specialized guidance
- Performance optimization

**Benefits:**
- Adaptive prompts for new problems
- Optimized for specific scenarios
- Version management
- Reusable across sessions

### 4. Tool Designer Integration

**Location:** `pipeline/phases/debugging.py`

**Integration:**
```python
# Tools automatically available after creation
# AI can propose new tools during execution

# Example: AI proposes custom analysis tool
if need_custom_tool:
    # AI designs tool using ToolDesigner meta-prompt
    # Tool is validated and registered
    # Tool becomes available immediately
    result = self.handler.execute_tool('custom_analysis_tool', args)
```

**Triggers:**
- Existing tools insufficient
- Novel analysis needed
- Specialized processing required
- Performance optimization

**Benefits:**
- Adaptive toolset
- Problem-specific tools
- Security validated
- Immediately available

### 5. Role Creator Integration

**Location:** `pipeline/phases/debugging.py`

**Integration:**
```python
# Access via role_registry
specialist = self.role_registry.consult_specialist(
    'custom_specialist',
    thread=thread,
    tools=tools
)

# Use specialist's analysis
findings = specialist['findings']
recommendations = specialist['recommendations']
```

**Triggers:**
- Novel problem requiring specialized expertise
- Existing specialists insufficient
- Need domain-specific analysis
- Complex multi-faceted problems

**Benefits:**
- Adaptive specialist team
- Problem-specific expertise
- Flexible team composition
- Reusable specialists

## Execution Workflows

### Workflow 1: Simple Error (Direct Fix)

```
1. Receive Error
   ↓
2. Track Action (Loop Detection)
   ↓
3. Check Loop Status
   ├─ No Loop: Continue
   └─ Loop Detected: Intervene
   ↓
4. Generate Fix (Standard Prompt)
   ↓
5. Execute Fix
   ↓
6. Track Action
   ↓
7. Validate
   ↓
8. Complete
```

**Duration:** 30-60s
**Components Used:** Loop Detection

### Workflow 2: Complex Error (Team Orchestration)

```
1. Receive Complex Error
   ↓
2. Track Action
   ↓
3. Check Loop Status
   ↓
4. Create Orchestration Plan
   ├─ Wave 1: Parallel Analysis (4 specialists)
   ├─ Wave 2: Synthesis (1 specialist)
   └─ Wave 3: Implementation (2 specialists)
   ↓
5. Execute Plan (Parallel)
   ↓
6. Track Actions
   ↓
7. Synthesize Results
   ↓
8. Apply Fix
   ↓
9. Validate
   ↓
10. Complete
```

**Duration:** 60-120s (vs 180-300s sequential)
**Components Used:** Loop Detection, Team Orchestrator

### Workflow 3: Novel Problem (Self-Designing)

```
1. Receive Novel Problem
   ↓
2. Track Action
   ↓
3. Check Loop Status
   ↓
4. Recognize Novel Problem
   ↓
5. Design Custom Prompt (PromptArchitect)
   ↓
6. Design Custom Tool (ToolDesigner)
   ↓
7. Design Custom Specialist (RoleCreator)
   ↓
8. Execute with Custom Components
   ↓
9. Track Actions
   ↓
10. Validate
   ↓
11. Save Components for Reuse
   ↓
12. Complete
```

**Duration:** 120-180s (first time), 60-90s (subsequent)
**Components Used:** All 5 systems

## Configuration

### Loop Detection Configuration

```python
# In PatternDetector
self.thresholds = {
    'action_repeat': 3,           # Same action 3+ times
    'modification_repeat': 4,     # Same file modified 4+ times
    'conversation_repeat': 3,     # Same conversation 3+ times
    'pattern_cycles': 2,          # Pattern repeats 2+ times
    'time_window': 300.0,         # 5 minute window
}

# In LoopInterventionSystem
self.max_interventions = 3  # Escalate after 3 interventions
```

### Team Orchestrator Configuration

```python
# In TeamOrchestrator
self.max_workers = 4  # Maximum parallel tasks
self.servers = [
    "ollama01.thiscluster.net",
    "ollama02.thiscluster.net"
]
```

### Prompt/Tool/Role Configuration

```python
# Registries automatically manage persistence
# Custom components saved to:
# - pipeline/prompts/custom/
# - pipeline/tools/custom/
# - pipeline/roles/custom/
```

## Testing Strategy

### Unit Tests

**Loop Detection:**
```python
def test_action_loop_detection():
    tracker = ActionTracker()
    detector = PatternDetector(tracker)
    
    # Simulate repeated actions
    for i in range(5):
        tracker.track_action('debug', 'main', 'str_replace', {})
    
    # Detect loop
    detections = detector.detect_all_loops()
    assert len(detections) > 0
    assert detections[0].loop_type == 'action_loop'
```

**Team Orchestrator:**
```python
def test_parallel_execution():
    orchestrator = TeamOrchestrator(client, team, logger)
    
    # Create plan with parallel tasks
    plan = orchestrator.create_orchestration_plan(
        problem="Test parallel execution"
    )
    
    # Execute
    results = orchestrator.execute_plan(plan)
    
    # Verify parallelism
    assert results['statistics']['parallel_efficiency'] > 1.5
```

### Integration Tests

**Full Workflow:**
```python
def test_complex_error_workflow():
    # Setup
    phase = DebuggingPhase(client, handler, logger)
    error = create_complex_error()
    
    # Execute
    result = phase.execute(state, issue=error)
    
    # Verify
    assert result.success
    assert 'loop_detection' in result.data
    assert 'team_orchestration' in result.data
```

### Performance Tests

**Speedup Measurement:**
```python
def test_parallel_speedup():
    # Sequential execution
    start = time.time()
    sequential_result = execute_sequential()
    sequential_time = time.time() - start
    
    # Parallel execution
    start = time.time()
    parallel_result = execute_parallel()
    parallel_time = time.time() - start
    
    # Verify speedup
    speedup = sequential_time / parallel_time
    assert speedup >= 2.0  # At least 2x speedup
```

## Monitoring & Metrics

### Key Metrics to Track

**Loop Detection:**
- Loop detection rate (loops per 100 actions)
- Intervention success rate
- Escalation rate
- Average actions before loop detection

**Team Orchestrator:**
- Parallel efficiency (speedup factor)
- Server utilization (%)
- Task success rate
- Average wave duration

**Self-Designing:**
- Custom prompt creation rate
- Custom tool creation rate
- Custom role creation rate
- Component reuse rate

### Logging

**Action Tracking:**
```
.autonomous_logs/action_history.jsonl
```

**Activity Log:**
```
ai_activity.log
```

**Performance Metrics:**
```python
stats = {
    'loop_detection': loop_intervention.get_intervention_status(),
    'team_orchestration': team_orchestrator.get_statistics(),
    'custom_components': {
        'prompts': len(prompt_registry.list_prompts()),
        'tools': len(tool_registry.list_tools()),
        'roles': len(role_registry.list_roles())
    }
}
```

## Troubleshooting

### Issue: High Loop Detection Rate

**Symptoms:**
- Many loops detected
- Frequent interventions
- Slow progress

**Solutions:**
1. Review loop thresholds
2. Improve prompts
3. Add more tools
4. Consult specialists earlier

### Issue: Low Parallel Efficiency

**Symptoms:**
- Speedup < 2x
- Unbalanced server load
- Long wave durations

**Solutions:**
1. Increase parallelism
2. Balance task durations
3. Reduce dependencies
4. Optimize task distribution

### Issue: Custom Components Not Working

**Symptoms:**
- Tools not found
- Prompts not loading
- Roles not instantiating

**Solutions:**
1. Check registry initialization
2. Verify file permissions
3. Validate component format
4. Check security sandbox

## Best Practices

### DO:
✅ Track all actions for loop detection
✅ Use team orchestration for complex problems
✅ Create custom components for novel problems
✅ Monitor performance metrics
✅ Balance load across servers
✅ Handle failures gracefully
✅ Validate all custom components
✅ Document custom components

### DON'T:
❌ Ignore loop warnings
❌ Overload single server
❌ Skip validation steps
❌ Create redundant components
❌ Ignore performance metrics
❌ Bypass security checks
❌ Forget to track statistics

## Production Readiness Checklist

- [ ] All components tested individually
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Error handling comprehensive
- [ ] Logging configured
- [ ] Metrics tracked
- [ ] Documentation complete
- [ ] Security validated
- [ ] Configuration reviewed
- [ ] Monitoring enabled

## Conclusion

The Week 2 integration creates a powerful self-designing AI system that:
- **Prevents infinite loops** with intelligent detection and intervention
- **Accelerates execution** with parallel specialist coordination
- **Adapts to novel problems** by creating custom prompts, tools, and roles
- **Maintains high quality** through comprehensive validation
- **Scales efficiently** across multiple servers

This system represents a significant advancement in autonomous AI development capabilities, enabling the pipeline to handle increasingly complex problems while maintaining reliability and performance.