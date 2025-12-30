# Verbose Logging Enhancement Plan

## User Requirements

1. **Model Interaction Visibility**
   - Show when conversation initiated with model
   - Display which server is being used
   - Show every tool call and response
   - Display all arguments for each tool
   - Indicate when model is "typing" (streaming tokens)

2. **Response Logging**
   - Log full responses to file when verbose mode enabled
   - Keep terminal output manageable
   - Provide way to view full output on demand

3. **Runtime Status Display**
   - Add hotkey (Ctrl+S) to show current status
   - Display what the model is currently doing
   - Show progress without flooding terminal

4. **Current Issues**
   - qwen-coder:32b running for 2+ hours
   - No indication if it's stuck or still processing
   - Need to know if subsequent queries are being sent
   - Want to see streaming progress

## Implementation Plan

### Phase 1: Enhanced Model Interaction Logging
- Add detailed logging before/after each model call
- Show server, model, context size
- Display message count and tool count
- Add streaming indicators

### Phase 2: Tool Call Verbosity
- Log every tool call with full arguments
- Show tool execution time
- Display tool results (success/failure)
- Add tool call sequence numbering

### Phase 3: Response Logging to File
- Create separate detailed log file for verbose mode
- Log complete model responses
- Log full tool call details
- Maintain structured format for analysis

### Phase 4: Signal Handlers
- Implement Ctrl+S for status display
- Show current phase, task, model call status
- Display elapsed time for current operation
- Show conversation history size

### Phase 5: Streaming Indicators
- Add progress dots/spinner for long operations
- Show token count if available from Ollama
- Display estimated time remaining
- Add timeout warnings

## Files to Modify

1. `pipeline/client.py` - Model interaction logging
2. `pipeline/handlers.py` - Tool call logging
3. `pipeline/logging_setup.py` - Enhanced logging configuration
4. `pipeline/coordinator.py` - Status display handler
5. `pipeline/phases/base.py` - Phase-level logging

## Success Criteria

- Can see exactly what model is doing at any time
- Full responses logged to file without terminal flood
- Hotkey provides instant status update
- Streaming indicators show progress
- No more wondering if system is stuck