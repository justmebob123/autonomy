# Autonomous User Proxy System

## Overview

The Autonomous User Proxy system eliminates ALL human blocking points in the autonomy pipeline. When the system would traditionally require "user intervention", it instead consults an AI specialist that simulates user guidance.

## Key Principle

**THIS IS A FULLY AUTONOMOUS SYSTEM** - There should be NO blocking for human input. Every role, including the "user" role, is played by an AI specialist.

## Architecture

### UserProxyAgent Class

Located in `pipeline/user_proxy.py`, this class:

1. **Creates AI Specialist Role** - Uses RoleCreator to design a "UserProxy" specialist
2. **Consults AI for Guidance** - Gets strategic guidance when loops are detected
3. **Provides Actionable Recommendations** - Returns guidance that helps break loops
4. **Maintains Autonomy** - Never blocks execution waiting for human input

### Integration Points

The UserProxyAgent is integrated at 3 critical points in `pipeline/phases/debugging.py`:

1. **Line ~390** - Main debugging loop detection
2. **Line ~618** - Secondary loop detection
3. **Line ~897** - Conversation thread loop detection

### How It Works

When a loop is detected:

```python
# OLD BEHAVIOR (BLOCKING):
if intervention.get('requires_user_input'):
    return PhaseResult(success=False, message="User intervention required")
    # System stops and waits for human

# NEW BEHAVIOR (AUTONOMOUS):
if intervention.get('requires_user_input'):
    # Consult AI UserProxy specialist
    user_proxy = UserProxyAgent(...)
    guidance_result = user_proxy.get_guidance(
        error_info={...},
        loop_info={...},
        debugging_history=[...],
        context={...}
    )
    
    # Apply AI guidance and continue
    guidance = guidance_result.get('guidance', '')
    self.logger.info(f"✓ AI Guidance: {guidance}")
    # System continues autonomously
```

## UserProxy Specialist Role

The UserProxy specialist is automatically created with:

### Capabilities
- Analyze debugging history and identify why loops are occurring
- Suggest alternative debugging strategies
- Recommend different approaches to problem-solving
- Provide high-level guidance without specific code changes
- Identify when to escalate to different specialists

### Tools Available
- `read_file` - Read source files
- `search_code` - Search codebase
- `list_directory` - List directory contents
- `execute_command` - Run shell commands

### Model Configuration
- **Model**: qwen2.5:14b
- **Server**: ollama02.thiscluster.net
- **Pattern**: Sequential consultation

### Prompt Template

The UserProxy receives:
- Complete debugging history
- Current error information
- Loop pattern details
- Context about what's been tried

And provides:
- Analysis of why the loop is occurring
- Alternative strategies to try
- High-level guidance (not specific code)
- Recommendations for breaking the loop

## Guidance Actions

The UserProxy can recommend three actions:

1. **CONTINUE** - Continue with new approach (default)
   - Provides strategic guidance
   - System incorporates guidance in next iteration

2. **SKIP** - Skip this error and move on
   - Detected when guidance contains: "skip", "move on", "abandon", "give up"
   - System continues to next error

3. **ESCALATE** - Escalate to different specialist
   - Detected when guidance contains: "escalate", "different specialist", "consult", "expert"
   - System engages appropriate specialist

## Benefits

### 1. **True Autonomy**
- No human blocking points
- System operates 24/7 without intervention
- Fully automated debugging pipeline

### 2. **Intelligent Loop Breaking**
- AI analyzes why loops occur
- Provides strategic guidance
- Suggests alternative approaches

### 3. **Continuous Operation**
- Never stops waiting for human input
- Always makes progress
- Can run indefinitely

### 4. **Adaptive Problem Solving**
- UserProxy learns from debugging history
- Suggests context-aware strategies
- Escalates when appropriate

## Example Flow

```
1. AI attempts to fix error
2. Loop detected (same fix tried 5+ times)
3. System triggers UserProxy consultation
4. UserProxy AI specialist:
   - Analyzes debugging history
   - Identifies why loop is occurring
   - Suggests alternative strategy
5. System applies guidance
6. Continues with new approach
7. NO HUMAN INTERVENTION REQUIRED
```

## Configuration

The UserProxy role is created automatically on first use. No configuration needed.

The role specification is stored in `.pipeline/roles/custom/user_proxy.json` after first creation.

## Monitoring

Watch for these log messages:

```
🤖 AUTONOMOUS USER PROXY CONSULTATION
================================================================================
Loop detected - consulting AI specialist for guidance...

✓ UserProxy role created and registered

📋 USER PROXY GUIDANCE:
--------------------------------------------------------------------------------
[AI guidance appears here]
--------------------------------------------------------------------------------

✓ AI Guidance: [guidance summary]
```

## Future Enhancements

### Custom Specialist Creation
The UserProxyAgent has a `create_custom_specialist()` method (not yet implemented) that will:
- Use RoleCreator to design specialists for specific problems
- Create specialized roles on-demand
- Further enhance autonomous problem-solving

### Learning from History
Future versions could:
- Track which guidance strategies work best
- Learn patterns from successful loop breaks
- Improve recommendations over time

## Summary

The Autonomous User Proxy system ensures the autonomy pipeline is **truly autonomous** - operating continuously without human intervention. When guidance is needed, an AI specialist provides it, maintaining the system's ability to operate 24/7 and solve problems independently.

**Key Takeaway**: Every role in the system, including the "user" role, is played by AI specialists. There are NO blocking points for human input.