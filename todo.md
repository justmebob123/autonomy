# TODO: Restore Conversation-Based Architecture

## Current State Analysis ✅
- [x] Examined existing conversation infrastructure
  - ConversationThread exists in `pipeline/orchestration/conversation_manager.py`
  - ConversationThread supports message history with token management
  - MultiModelConversationManager exists for model-to-model communication
- [x] Reviewed current phase execution
  - Phases currently use specialists directly (mandatory calls)
  - No conversation history maintained in phases
  - Specialists called for every task execution
- [x] Identified the problem
  - Specialists are mandatory, not optional
  - No conversation context maintained
  - Phases don't maintain history with models

## Phase 1: Restore Conversation-Based Phase Execution
- [x] Add conversation thread to BasePhase
  - Initialize ConversationThread in `__init__`
  - Maintain conversation history per phase instance
  - Use conversation context when calling model
- [x] Add chat_with_history() method to BasePhase
  - Adds user message to conversation
  - Gets conversation context (respects token limits)
  - Calls model with history
  - Adds assistant response to conversation
  - Returns parsed response with tool calls
- [x] Update CodingPhase to use conversation
  - Removed mandatory specialist call
  - Uses chat_with_history() instead
  - Builds simple, focused user message
  - Model sees previous exchanges in conversation
- [ ] Update other phases to use conversation
  - QAPhase
  - DebuggingPhase
  - PlanningPhase
  - (others as needed)
- [x] Simplify prompts
  - Created _build_user_message() with simple, focused prompts
  - Removed specialist overhead
  - Let conversation history provide context

## Phase 2: Make Specialists Optional Helpers
- [x] Remove mandatory specialist calls from phases
  - CodingPhase now calls model directly with conversation
  - QAPhase now calls model directly with conversation
  - DebuggingPhase now calls model directly with conversation
- [ ] Add specialist request mechanism (Future)
  - Detect when model requests help (e.g., "I need to validate this")
  - Call appropriate specialist
  - Add specialist response to conversation
  - Continue with model
- [x] Keep specialists as available tools
  - Specialist infrastructure still exists
  - Made optional, not mandatory

## Phase 3: Simplify Phase Progression
- [x] Review coordinator's `_determine_next_action()`
  - Confirmed arbiter is NOT making decisions
  - Already uses simple task-status-based logic
- [x] Simple progression already implemented
  - if needs_fixes: debugging
  - if qa_pending: qa
  - if pending: coding
  - if no tasks: planning
  - if all complete: complete
- [x] Arbiter not used for decision-making
  - Arbiter infrastructure exists for future observer role
  - Not used for phase transitions

## Phase 4: Test and Verify
- [ ] Test conversation history works
  - Model can reference previous exchanges
  - Context builds from history
- [ ] Test optional specialists
  - Phases work without specialists
  - Specialists called only when needed
- [ ] Test simple progression
  - Phases transition based on task status
  - No complex decision logic

## Phase 5: Documentation
- [ ] Document conversation-based architecture
- [ ] Document specialist invocation mechanism
- [ ] Update README with new approach

## Future Work (Not Now)
- Background arbiter observer (separate thread)
- Self-development infrastructure
- Pattern recognition system
- Tool creation capability
- Hyperdimensional polytopic analysis

## Notes
- Focus on conversation history first
- Make specialists optional, not mandatory
- Keep prompts simple
- Trust the model to learn from history
- Don't over-engineer