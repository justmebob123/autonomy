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
- [x] Update other phases to use conversation
  - CodingPhase ✅
  - QAPhase ✅
  - DebuggingPhase ✅
  - PlanningPhase ✅
  - InvestigationPhase ✅
  - DocumentationPhase ✅
- [x] Simplify prompts
  - Created _build_user_message() with simple, focused prompts
  - Removed specialist overhead
  - Let conversation history provide context

## Phase 2: Make Specialists Optional Helpers
- [x] Remove mandatory specialist calls from phases
  - CodingPhase now calls model directly with conversation
  - QAPhase now calls model directly with conversation
  - DebuggingPhase now calls model directly with conversation
  - PlanningPhase now calls model directly with conversation
  - InvestigationPhase now calls model directly with conversation
  - DocumentationPhase now calls model directly with conversation
- [x] Add specialist request mechanism
  - ✅ Created SpecialistRequestHandler
  - ✅ Detects when model requests help (regex patterns)
  - ✅ Routes to appropriate specialist (coding, reasoning, analysis)
  - ✅ Adds specialist response to conversation
  - ✅ Model continues with specialist input
  - ✅ Comprehensive test suite (100% pass rate)
- [x] Keep specialists as available tools
  - Specialist infrastructure still exists
  - Made optional, not mandatory
  - Called only when model explicitly requests help

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
- [x] Test conversation history works
  - ConversationThread initializes correctly
  - Messages can be added to conversation
  - Context can be retrieved with token limits
  - chat_with_history() method works
- [x] Test initialization
  - All phases initialize with conversation thread
  - Correct model assigned from config.model_assignments
  - Context window set correctly (8192 default)
- [ ] Test with real tasks (needs live Ollama servers)
  - Run actual coding task with conversation
  - Verify model sees previous exchanges
  - Confirm specialists not called by default

## Phase 5: Documentation
- [x] Document conversation-based architecture
  - Created ARCHITECTURE_CLARIFICATION.md
  - Created IMPLEMENTATION_PLAN_CONVERSATION_ARCHITECTURE.md
  - Created CONVERSATION_ARCHITECTURE_COMPLETE.md
- [ ] Update README with new approach (if needed)
- [ ] Document specialist invocation mechanism (future work)

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