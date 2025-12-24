# Enhanced AI Debugging Pipeline

## Overview

This document describes the enhanced debugging capabilities added to the autonomous development pipeline to address complex debugging scenarios and improve fix success rates.

## Problem Statement

The original debugging pipeline was failing to fix certain errors because:

1. **Limited Context**: AI went straight to fixing without understanding the problem
2. **No Tool Calls**: AI would explain fixes but not execute them
3. **Poor Logging**: Couldn't diagnose why AI wasn't calling tools
4. **No Escalation**: Stuck in loops with no alternative strategies
5. **Model Issues**: Using smaller fallback models instead of configured larger models

## Solution Architecture

### 1. Enhanced Logging System

**Location**: `pipeline/phases/debugging.py`

**Features**:
- Full AI response logging to `ai_activity.log`
- Response analysis to understand why no tool calls were made
- Model selection path tracking
- Detailed error context

**Usage**:
```python
# Automatic logging when AI doesn't make tool calls
# Check ai_activity.log for full responses and analysis
```

**Benefits**:
- Understand AI reasoning process
- Identify prompt issues
- Debug tool calling problems
- Track model selection decisions

### 2. Investigation Phase

**Location**: `pipeline/phases/investigation.py`

**Purpose**: Diagnose problems before attempting fixes

**Features**:
- Gathers comprehensive context using tools
- Examines related files and dependencies
- Tests hypotheses about root cause
- Generates diagnostic report
- Recommends fix strategies

**Workflow**:
```
1. Receive error report
2. Use read_file to examine related code
3. Use search_code to find patterns
4. Analyze error in full context
5. Identify root cause
6. Recommend fix strategy
7. Pass findings to debugging phase
```

**Usage**:
```python
from pipeline.phases.investigation import InvestigationPhase

investigation = InvestigationPhase(config, client)
result = investigation.execute(state, issue=error_dict)

if result.success:
    findings = result.data['findings']
    print(f"Root cause: {findings['root_cause']}")
    print(f"Recommended fix: {findings['recommended_fix']}")
```

### 3. Multi-Agent Consultation System

**Location**: `pipeline/agents/`

**Components**:

#### 3.1 Tool Advisor (FunctionGemma)
**File**: `pipeline/agents/tool_advisor.py`

**Capabilities**:
- Suggests appropriate tools for tasks
- Validates tool call syntax
- Fixes malformed tool calls
- Explains tool usage

**Usage**:
```python
from pipeline.agents import ToolAdvisor

advisor = ToolAdvisor(client, config)

# Suggest tools
tools = advisor.suggest_tools("Fix a syntax error", available_tools)

# Validate tool call
is_valid, error = advisor.validate_tool_call(tool_call, tool_def)

# Fix malformed call
fixed = advisor.fix_tool_call(malformed_string, available_tools)
```

#### 3.2 Consultation Manager
**File**: `pipeline/agents/consultation.py`

**Specialists**:
- **Code Analyst**: Uses deepseek-coder-v2 for code quality analysis
- **Problem Solver**: Uses phi4/qwen2.5:14b for complex problem solving

**Usage**:
```python
from pipeline.agents import ConsultationManager

manager = ConsultationManager(client, config)

# Consult code analyst
analysis = manager.consult_code_analyst(code, issue)

# Consult problem solver
solution = manager.consult_problem_solver(problem_desc, context)

# Consult all specialists
consultations = manager.consult_all_specialists(code, issue, context)

# Synthesize recommendations
recommendation = manager.synthesize_consultations(consultations)
```

### 4. Enhanced Prompts

**Location**: `pipeline/prompts.py`

**Improvements**:
- Step-by-step debugging workflow
- Concrete tool call examples
- Decision tree for common errors
- Clearer instructions
- Emphasis on tool usage

**Key Changes**:
```python
# Before: Generic instructions
"You are a debugging expert. Fix the error."

# After: Detailed workflow with examples
"""
DEBUGGING WORKFLOW:
Step 1: UNDERSTAND the error
Step 2: IDENTIFY the root cause
Step 3: PLAN the fix
Step 4: EXECUTE the fix - CALL THE TOOL NOW

EXAMPLE TOOL CALL:
modify_python_file(
    filepath="src/example.py",
    original_code="def broken():\n    return value",
    new_code="def broken():\n    return self.value"
)
"""
```

### 5. Model Selection Enhancements

**Location**: `pipeline/client.py`

**Features**:
- Detailed logging of model selection process
- Tracks why fallbacks are used
- Shows selection path for debugging
- Warns when using last resort models

**Output Example**:
```
Model selection: Using preferred qwen2.5-coder:14b on ollama02
# or
Model selection: Using fallback qwen2.5-coder:7b on ollama01
Selection path: Preferred: qwen2.5-coder:14b on ollama02 -> 
                Preferred host unavailable -> 
                Using fallback
```

## Integration Guide

### Using Investigation Phase Before Debugging

```python
# In your debugging workflow
from pipeline.phases.investigation import InvestigationPhase
from pipeline.phases.debugging import DebuggingPhase

# 1. Investigate first
investigation = InvestigationPhase(config, client)
inv_result = investigation.execute(state, issue=error)

# 2. Use findings in debugging
if inv_result.success:
    findings = inv_result.data['findings']
    
    # Pass findings to debugging phase
    debug = DebuggingPhase(config, client)
    debug_result = debug.execute(
        state, 
        issue=error,
        investigation_findings=findings  # Enhanced context
    )
```

### Using Multi-Agent Consultation

```python
from pipeline.agents import ConsultationManager

# When debugging fails or issue is complex
if not debug_result.success or issue_is_complex:
    manager = ConsultationManager(client, config)
    
    # Get specialist opinions
    consultations = manager.consult_all_specialists(
        code=file_content,
        issue=error,
        context={'previous_attempts': 3, 'complexity': 'high'}
    )
    
    # Synthesize and retry with enhanced context
    recommendation = manager.synthesize_consultations(consultations)
    
    # Retry debugging with specialist input
    debug_result = debug.execute(
        state,
        issue=error,
        specialist_recommendations=recommendation
    )
```

### Using Tool Advisor

```python
from pipeline.agents import ToolAdvisor

advisor = ToolAdvisor(client, config)

# Before sending tools to AI
suggested_tools = advisor.suggest_tools(
    task_description="Fix runtime error in Python file",
    available_tools=all_tools
)

# Only send relevant tools to reduce confusion
response = client.chat(messages, tools=suggested_tools)

# After receiving response, validate tool calls
for tool_call in response_tool_calls:
    is_valid, error = advisor.validate_tool_call(tool_call, tool_def)
    if not is_valid:
        # Try to fix
        fixed = advisor.fix_tool_call(str(tool_call), all_tools)
        if fixed:
            tool_call = fixed
```

## Configuration

### Enable Enhanced Features

In your `PipelineConfig`:

```python
config = PipelineConfig(
    # Use larger models for debugging
    model_assignments={
        "debugging": ("qwen2.5-coder:14b", "ollama02.thiscluster.net"),
        "investigation": ("qwen2.5:14b", "ollama02.thiscluster.net"),
    },
    
    # Enable verbose logging
    verbose=2,  # 0=normal, 1=verbose, 2=very verbose
    
    # Longer timeouts for complex debugging
    debug_timeout=120,  # seconds
)
```

### Activity Logging

Enhanced logging writes to `ai_activity.log` in your project directory:

```bash
# View recent debugging attempts
tail -f ai_activity.log

# Search for specific issues
grep "NO TOOL CALLS" ai_activity.log

# Analyze model selection
grep "Model selection" ai_activity.log
```

## Troubleshooting

### AI Not Making Tool Calls

**Check**:
1. Review `ai_activity.log` for full AI response
2. Check model selection - is it using 14b or 7b?
3. Review prompt effectiveness
4. Try consulting specialists

**Solutions**:
```python
# 1. Use investigation phase first
inv_result = investigation.execute(state, issue=error)

# 2. Consult specialists
consultations = manager.consult_all_specialists(code, issue, context)

# 3. Use tool advisor to validate
suggested = advisor.suggest_tools(task_desc, tools)

# 4. Try different model
config.model_assignments["debugging"] = ("phi4", "ollama02")
```

### Wrong Model Being Used

**Check**:
```bash
# Look for model selection logs
grep "Model selection" logs/pipeline.log
```

**Common Causes**:
1. Preferred model not available on server
2. Model name mismatch
3. Server connection issues

**Solutions**:
```python
# Verify models are available
client.discover_servers()
print(client.available_models)

# Check model assignments
print(config.model_assignments)

# Verify model names match
# Config: "qwen2.5-coder:14b"
# Available: "qwen2.5-coder:14b" ✓
# Available: "qwen2.5-coder" ✗ (won't match)
```

### Investigation Phase Not Helping

**Check**:
1. Are tools being called during investigation?
2. Is the AI examining related files?
3. Are findings being passed to debugging?

**Solutions**:
```python
# Enable verbose logging
config.verbose = 2

# Check investigation results
if inv_result.success:
    findings = inv_result.data['findings']
    print(f"Root cause: {findings.get('root_cause')}")
    print(f"Related files: {findings.get('related_files')}")
    
    # If findings are empty, investigation didn't work
    if not findings.get('root_cause'):
        # Try with more specific prompt
        # or consult specialists directly
```

## Performance Metrics

Track these metrics to measure improvement:

1. **Fix Success Rate**: % of errors fixed on first attempt
2. **Tool Call Rate**: % of debugging attempts that make tool calls
3. **Investigation Effectiveness**: % of investigations that identify root cause
4. **Consultation Value**: % of consultations that lead to successful fixes
5. **Model Selection Accuracy**: % of times preferred model is used

## Future Enhancements

### Planned Features

1. **Escalation System**: Automatic escalation when stuck
2. **Alternative Strategies**: Multiple fix approaches
3. **Learning System**: Learn from past failures
4. **Prompt Optimization**: Auto-improve prompts based on results
5. **Response Analysis**: Deep analysis of AI reasoning

### Experimental Features

1. **Conversation Threading**: Multi-turn agent discussions
2. **Hypothesis Testing**: Automated hypothesis validation
3. **Fix Verification**: Automated testing of fixes
4. **Context Caching**: Reuse context across attempts

## Contributing

When adding new features:

1. Add comprehensive logging
2. Document in this file
3. Add usage examples
4. Include troubleshooting guide
5. Update metrics tracking

## References

- [FunctionGemma Documentation](https://ai.google.dev/gemma/docs/functiongemma)
- [Original Issue Analysis](../analysis/COMPREHENSIVE_ANALYSIS.md)
- [Implementation Plan](../implementation/IMPLEMENTATION_PLAN.md)