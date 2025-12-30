# Verbose Logging Enhancement Implementation

## Goal
Improve visibility into long-running model operations, especially for qwen-coder:32b queries that can take hours.

## Phase 1: Enhanced Model Interaction Logging ⚡ PRIORITY
- [x] Add pre-call logging (server, model, context, message count)
- [x] Add post-call logging (duration, tokens, success)
- [ ] Add streaming progress indicators
- [x] Show conversation history size

## Phase 2: Tool Call Verbosity
- [x] Log every tool call with full arguments (when verbose)
- [x] Show tool execution time
- [x] Display detailed tool results
- [ ] Add tool call sequence numbering

## Phase 3: Detailed File Logging
- [ ] Create separate verbose log file (pipeline_verbose.log)
- [ ] Log complete model responses to file
- [ ] Log full tool call details to file
- [ ] Keep terminal output manageable

## Phase 4: Signal Handlers for Status
- [ ] Implement Ctrl+S signal handler for status display
- [ ] Show current phase, task, operation
- [ ] Display elapsed time for current operation
- [ ] Show conversation history stats

## Phase 5: Streaming Indicators
- [ ] Add progress indicator for model calls
- [ ] Show "Model thinking..." with elapsed time
- [ ] Add periodic updates every 30 seconds
- [ ] Display timeout warnings

## Implementation Order
1. Start with Phase 1 (most critical for immediate visibility)
2. Then Phase 5 (streaming indicators)
3. Then Phase 2 (tool verbosity)
4. Then Phase 3 (file logging)
5. Finally Phase 4 (signal handlers)