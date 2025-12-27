# Deep Analysis: QA Phase Failures

## Investigation Questions

### 1. Empty Tool Names - Is the AI Really Generating Them?

**Current Evidence:**
- Logs show: `🤖 [AI Activity] Calling tool: ` (empty string after colon)
- This happens in `_log_tool_activity()` which receives `tool_name` parameter
- The tool_name comes from `func.get("name", "unknown")` in `_execute_tool_call()`

**Key Question:** Is the model actually returning `{"function": {"name": ""}}` or is something else happening?

**Need to Check:**
1. The raw response from Ollama API
2. The parsed tool_calls structure
3. Whether the parser is incorrectly extracting empty names

**Hypothesis:** The model might be:
- Returning malformed JSON
- Returning text that the parser can't extract from
- Actually generating empty tool names (unlikely but possible)

### 2. Why Stuck at Exactly 20 Failures?

**Observation:** User reports system "stuck at 20 consecutive failures"

**Current Logic:**
- Threshold is set to 2 (was 3, now 2)
- Should force transition after 2 consecutive failures
- But user saw 20 failures

**Possible Explanations:**

A. **Counter Not Being Incremented Properly:**
```python
# In state/manager.py - PhaseState.get_consecutive_failures()
# Does this actually count correctly?
```

B. **Counter Being Reset Incorrectly:**
```python
# After forcing transition, counter should be reset
# But is it being reset at the right time?
```

C. **The "20" Might Not Be Consecutive Failures:**
- Could be total runs (20 runs, some successful, some failed)
- Could be the phase_state.runs counter, not consecutive_failures

**Need to Verify:**
1. What counter is actually showing "20"?
2. Is it `phase_state.runs` or `get_consecutive_failures()`?
3. Are failures being recorded correctly in run_history?

### 3. Model Selection - Why Using 14b Instead of 32b?

**Current Configuration (config.py):**
```python
"qa": ("qwen2.5:14b", "ollama01.thiscluster.net"),
```

**User's Expectation:**
- ollama02 has 32b model
- Should use more capable model for QA

**Issue:** QA is hardcoded to use 14b on ollama01

**Recommendation:** Change to:
```python
"qa": ("qwen2.5:32b", "ollama02.thiscluster.net"),
```

### 4. Context Window / Token Limits

**Current Implementation:**
```python
payload = {
    "model": model,
    "messages": messages,
    "stream": False,
    "options": {"temperature": temperature}
}
```

**Missing:** No `num_ctx` parameter!

**Ollama Default:** Usually 2048 tokens

**Recommendation:** Add context window configuration:
```python
"options": {
    "temperature": temperature,
    "num_ctx": 8192  # or 16384 for larger models
}
```

### 5. Why Did It Break Out of Development?

**Need to Investigate:**
1. What was the last successful development task?
2. What triggered the transition to QA?
3. Was there a task marked as QA_PENDING?
4. Did the coordinator force a transition?

**Possible Causes:**
- A task was completed and marked QA_PENDING
- The development phase returned a result with next_phase="qa"
- The coordinator's selection logic chose QA

### 6. FunctionGemma Usage

**Current Implementation:**
```python
# In client.py ResponseParser
if self.gemma_formatter and tools:
    self.logger.debug("  Trying functiongemma for formatting...")
    gemma_result = self.gemma_formatter.format_tool_call(content, tools)
```

**Questions:**
1. Is FunctionGemma being used as a fallback or primary?
2. Should it be a tool call itself?
3. Is it being invoked correctly?

**User's Idea:** "couldn't functiongemma be a tool call?"

**Analysis:** 
- Currently it's a formatter/parser
- Could be exposed as a tool that other models call
- Would allow explicit invocation: "use functiongemma to format this"

### 7. Verbose Logging for Failed Tool Calls

**Current Logging:**
```python
self.logger.warning(f"Unknown tool: {name}")
self.logger.warning(f"  Available tools: {', '.join(sorted(self._handlers.keys()))}")
self.logger.warning(f"  Args provided: {list(args.keys())}")
```

**Missing:**
- The raw response text from the model
- The raw JSON structure of the tool call
- The full message content before parsing

**Recommendation:** Add detailed logging:
```python
self.logger.warning(f"Tool call failed:")
self.logger.warning(f"  Raw response text: {response.get('message', {}).get('content', '')[:1000]}")
self.logger.warning(f"  Tool call structure: {json.dumps(call, indent=2)}")
self.logger.warning(f"  Function object: {json.dumps(func, indent=2)}")
```

## Recommended Fixes

### Fix 1: Add Context Window Configuration
```python
# In client.py
payload = {
    "model": model,
    "messages": messages,
    "stream": False,
    "options": {
        "temperature": temperature,
        "num_ctx": 8192  # Configurable per model
    }
}
```

### Fix 2: Use 32b Model for QA
```python
# In config.py
"qa": ("qwen2.5:32b", "ollama02.thiscluster.net"),
```

### Fix 3: Enhanced Error Logging
```python
# In handlers.py _execute_tool_call()
if not name or name.strip() == "":
    self.logger.error(f"Tool call has empty name field")
    self.logger.error(f"  Full call structure: {json.dumps(call, indent=2)}")
    self.logger.error(f"  Function object: {json.dumps(func, indent=2)}")
    # Also log the original response if available
```

### Fix 4: Better Prompt Engineering for QA

**Current QA Prompt Issues:**
- Might be too complex for 14b model
- Doesn't provide examples of tool usage
- Doesn't emphasize the importance of using tools

**Recommendation:** Add examples and simplify:
```python
"""Review this Python file for quality issues:

FILE: {filepath}
```python
{code}
```

IMPORTANT: You MUST use tools to report your findings.

EXAMPLES:
1. If you find a syntax error:
   - Call report_issue with type="SyntaxError" and description
   
2. If you find a missing import:
   - Call report_issue with type="ImportError" and description
   
3. If the code is perfect:
   - Call approve_code

DO NOT just describe issues - USE THE TOOLS.
"""
```

### Fix 5: Investigate Run History Counter

Need to add debug logging to see what's actually being counted:
```python
# In coordinator.py _should_force_transition()
consecutive_failures = phase_state.get_consecutive_failures()
self.logger.debug(f"Phase {current_phase} consecutive failures: {consecutive_failures}")
self.logger.debug(f"Phase {current_phase} total runs: {phase_state.runs}")
self.logger.debug(f"Phase {current_phase} run history: {phase_state.run_history[-10:]}")
```

## Next Steps

1. Add verbose logging for tool call failures
2. Increase context window to 8192
3. Switch QA to 32b model on ollama02
4. Improve QA prompt with examples
5. Add debug logging for failure counters
6. Investigate why development phase transitioned to QA
7. Consider making FunctionGemma a callable tool