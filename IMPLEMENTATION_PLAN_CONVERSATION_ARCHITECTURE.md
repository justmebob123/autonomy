# Implementation Plan: Conversation-Based Architecture

## Overview
Restore the conversation-based architecture where phases maintain conversation history with models, specialists are optional helpers, and the arbiter observes rather than controls.

---

## Phase 1: Restore Conversation-Based Phase Execution

### Current State Analysis
Need to examine how phases currently execute and what conversation infrastructure exists.

### Tasks
1. **Examine existing conversation infrastructure**
   - Check if `ConversationThread` and `MultiModelConversationManager` exist
   - Review current phase execution in `pipeline/phases/base.py`
   - Identify what needs to be restored vs. built new

2. **Implement conversation history in phases**
   - Each phase maintains its own conversation thread
   - Model sees previous exchanges in the phase
   - Context built from history, not massive prompts

3. **Simplify phase prompts**
   - Remove system explanations
   - Focus on immediate task
   - Let history provide context

### Expected Changes
- Modify `BasePhase` to maintain conversation thread
- Update phase `execute()` methods to use conversation history
- Simplify prompt generation

---

## Phase 2: Make Specialists Optional Helpers

### Current State
Specialists are currently initialized in all phases and may be called automatically.

### Tasks
1. **Remove mandatory specialist calls**
   - Specialists should NOT be called by default
   - Only called when phase explicitly requests help

2. **Add specialist invocation mechanism**
   - Phase can request specialist help: "I need to validate this code"
   - Specialist joins conversation temporarily
   - Specialist uses tools to investigate
   - Returns insight to conversation
   - Leaves conversation

3. **Keep specialist tools available**
   - Specialists remain available as tools
   - Not removed, just made optional

### Expected Changes
- Remove automatic specialist calls from phases
- Add explicit specialist request mechanism
- Specialists become tools that phases can invoke

---

## Phase 3: Simplify Phase Progression Logic

### Current State
Phase progression may have complex arbiter-based decision making.

### Tasks
1. **Restore simple status-based logic**
   ```python
   if needs_fixes:     → debugging
   if qa_pending:      → qa
   if pending:         → coding
   if no tasks:        → planning
   if all complete:    → complete
   ```

2. **Remove arbiter from decision-making**
   - Arbiter should NOT decide phase transitions
   - Simple task status determines next phase

### Expected Changes
- Simplify `_determine_next_action()` in coordinator
- Remove arbiter decision-making
- Use task status for phase progression

---

## Phase 4: Background Arbiter Observer (Future)

### Design
- Arbiter runs in separate thread
- Watches conversation streams
- Only intercedes when detecting problems
- Does NOT make decisions

### Implementation (Later)
- Thread-based arbiter monitoring
- Conversation stream observation
- Intervention mechanism for clarity/simplification

---

## Phase 5: Self-Development Infrastructure (Future)

### Components
1. **Pattern Recognition**
   - Analyze execution patterns
   - Identify common issues
   - Learn from successes/failures

2. **Tool Creation**
   - Detect when new tools needed
   - Generate tool specifications
   - Implement and test new tools

3. **Hyperdimensional Polytopic Analysis**
   - Understand component relationships
   - Navigate solution space
   - Optimize execution paths

### Implementation (Later)
- Pattern analysis system
- Tool generation infrastructure
- Polytopic relationship mapping

---

## Immediate Next Steps

1. Examine current codebase structure
2. Identify conversation infrastructure
3. Plan minimal changes to restore conversation-based execution
4. Implement Phase 1 (conversation history)
5. Implement Phase 2 (optional specialists)
6. Implement Phase 3 (simple progression)

---

## Success Criteria

✅ Phases maintain conversation history with models
✅ Models can reference previous exchanges
✅ Specialists are optional, not mandatory
✅ Phase progression based on simple task status
✅ Prompts are simple and focused
✅ System learns from conversation history
✅ No hardcoded complex decision logic

---

This plan focuses on restoring the intended conversation-based architecture first, with self-development infrastructure to follow.