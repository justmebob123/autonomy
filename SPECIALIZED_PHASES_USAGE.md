# Specialized Phases Usage Guide

## Overview

The Autonomy AI pipeline includes **specialized phases** that are designed for dynamic expansion and capability enhancement. These phases are **NOT part of the normal development flow** and are only activated on-demand when specific conditions are met.

## Specialized Phases

### 1. Tool Design & Evaluation
- **tool_design**: Creates new custom tools when capabilities are missing
- **tool_evaluation**: Validates and tests newly created tools

**Use Cases:**
- Missing functionality that existing tools don't provide
- Repeated failures due to lack of appropriate tools
- Complex operations that need specialized tooling

### 2. Prompt Design & Improvement
- **prompt_design**: Creates new prompts for specialized tasks
- **prompt_improvement**: Refines existing prompts that aren't working well

**Use Cases:**
- Unclear or ambiguous prompts causing confusion
- Prompts that don't provide enough guidance
- Need for specialized instructions for complex tasks

### 3. Role Design & Improvement
- **role_design**: Creates new specialist roles/personas
- **role_improvement**: Enhances existing specialist roles

**Use Cases:**
- Need for domain-specific expertise not covered by existing specialists
- Complex tasks requiring specialized knowledge
- Repeated failures in specific domains

## Normal Pipeline Flow

The primary pipeline handles 95%+ of development work:

```
Planning → Coding → QA → Debugging → Investigation → Documentation
```

**These phases are always active and handle:**
- Task planning and prioritization
- Code implementation
- Quality assurance
- Bug fixing
- Problem investigation
- Documentation generation

## Activation Triggers

Specialized phases are **automatically activated** when:

### 1. Failure Loop Detection (Highest Priority)
- **Condition**: Task fails 3+ consecutive times
- **Action**: Coordinator analyzes error pattern and activates appropriate specialized phase
- **Example**: If errors mention "missing tool", activates `tool_design`

### 2. Capability Gap Detection
- **Condition**: Phase result indicates missing capability
- **Triggers**:
  - "missing tool" or "need tool" → `tool_design`
  - "unclear prompt" or "prompt issue" → `prompt_improvement`
  - "missing specialist" or "need expert" → `role_design`

### 3. Investigation Recommendations
- **Condition**: Investigation phase identifies need for specialized capability
- **Action**: Investigation recommends, coordinator decides whether to activate
- **Note**: Recommendations don't force activation, just suggest it

### 4. Explicit User Request
- **Condition**: User explicitly requests tool/prompt/role creation
- **Action**: Coordinator directly activates appropriate specialized phase

## How It Works

### Detection Flow

```
1. Coordinator checks for specialized needs BEFORE normal phase selection
2. If failure loop detected (3+ failures):
   - Analyze error pattern
   - Determine which specialized phase needed
   - Activate specialized phase
3. If capability gap detected:
   - Check phase result message
   - Activate appropriate specialized phase
4. Otherwise, proceed with normal polytope flow
```

### Activation Flow

```
1. Specialized phase activated (e.g., tool_design)
2. Phase creates new capability (e.g., custom tool)
3. Capability validated (e.g., tool_evaluation)
4. Return to normal flow with new capability available
5. Retry original task with enhanced capabilities
```

## Example Scenarios

### Scenario 1: Missing Tool

```
1. Coding phase tries to use non-existent tool "analyze_dependencies"
2. Task fails with "tool not found" error
3. Task fails again (failure_count = 2)
4. Task fails third time (failure_count = 3)
5. Coordinator detects failure loop
6. Coordinator activates tool_design phase
7. tool_design creates "analyze_dependencies" tool
8. tool_evaluation validates the new tool
9. Coordinator retries coding phase with new tool
10. Task succeeds
```

### Scenario 2: Unclear Prompt

```
1. Investigation phase produces unclear analysis
2. Debugging phase can't understand investigation output
3. Multiple cycles of investigation → debugging with poor results
4. Investigation phase detects prompt issue
5. Investigation recommends prompt_improvement
6. Coordinator detects repeated poor results
7. Coordinator activates prompt_improvement
8. prompt_improvement refines investigation prompt
9. Investigation phase produces clearer analysis
10. Debugging phase successfully fixes issues
```

### Scenario 3: Domain Expertise Needed

```
1. Complex machine learning task assigned
2. Coding phase struggles with ML-specific patterns
3. Multiple failures on ML implementation
4. Coordinator detects failure loop
5. Error pattern suggests need for specialist
6. Coordinator activates role_design
7. role_design creates "ML Specialist" role
8. ML Specialist handles ML-specific tasks
9. Implementation succeeds
```

## Benefits

### 1. Non-Intrusive
- Specialized phases don't interfere with normal development
- Only activated when truly needed
- Pipeline remains efficient for standard tasks

### 2. Self-Improving
- Pipeline can expand its own capabilities
- Learns from failures and adapts
- Becomes more capable over time

### 3. Focused Activation
- Clear triggers prevent unnecessary activation
- Failure loops are broken systematically
- Capability gaps are filled proactively

### 4. Maintainable
- Specialized phases are isolated from main flow
- Easy to add new specialized phases
- Clear separation of concerns

## Configuration

### Failure Loop Threshold
Default: 3 consecutive failures

To adjust, modify `_detect_failure_loop()` in `pipeline/coordinator.py`:

```python
if failure_count >= 3:  # Change this threshold
    # Activate specialized phase
```

### Capability Gap Keywords
Default keywords for detection:

- **Tool gaps**: "missing tool", "need tool", "tool not found"
- **Prompt gaps**: "unclear prompt", "need guidance", "prompt issue"
- **Role gaps**: "missing specialist", "need expert", "role not found"

To adjust, modify `_detect_capability_gap()` in `pipeline/coordinator.py`.

## Monitoring

### Logs
Specialized phase activations are logged with 🎯 emoji:

```
🎯 Activating tool_design to break failure loop
🎯 Activating prompt_improvement to fill capability gap
```

### State Tracking
- `task.failure_count`: Tracks consecutive failures per task
- `state._last_phase_result`: Stores last phase result for gap detection
- Phase history shows when specialized phases were activated

## Best Practices

### 1. Let the System Decide
- Don't manually force specialized phase activation
- Trust the automatic detection system
- Only explicitly request when you know a capability is missing

### 2. Monitor Failure Patterns
- Watch for repeated failures on same tasks
- Check if specialized phases are being activated appropriately
- Adjust thresholds if needed

### 3. Review Created Capabilities
- Periodically review custom tools created by tool_design
- Check if prompts improved by prompt_improvement are effective
- Validate that specialist roles are being used appropriately

### 4. Keep Primary Flow Clean
- Don't add specialized phase logic to primary phases
- Maintain clear separation between normal and specialized flows
- Let coordinator handle all specialized phase decisions

## Troubleshooting

### Specialized Phase Not Activating
**Problem**: Task failing repeatedly but specialized phase not activated

**Solutions:**
1. Check `task.failure_count` is being incremented
2. Verify failure threshold (default: 3)
3. Check error messages contain trigger keywords
4. Review coordinator logs for detection attempts

### Specialized Phase Activating Too Often
**Problem**: Specialized phases activating when not needed

**Solutions:**
1. Increase failure threshold (e.g., 3 → 5)
2. Review capability gap keywords (may be too broad)
3. Check if primary phases are returning appropriate error messages
4. Add more specific trigger conditions

### Created Capabilities Not Working
**Problem**: tool_design creates tool but it doesn't work

**Solutions:**
1. Check tool_evaluation phase is running
2. Review tool validation logic
3. Ensure tool is properly registered
4. Check tool has correct signature and implementation

## Summary

Specialized phases are a powerful feature for dynamic pipeline expansion, but they should remain **secondary systems** that only activate on-demand. The primary pipeline (Planning → Coding → QA → Debugging) handles normal development, while specialized phases handle exceptional cases requiring new capabilities.

**Key Principle**: Normal flow first, specialized phases only when needed.