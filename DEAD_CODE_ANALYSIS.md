# Dead Code Analysis - 76.6% Unused

## Reality Check

Out of 111 modules, only **26 are actually used** (23.4%). The rest is dead code.

## Core Used Modules (26)

### Entry & Config (3)
- pipeline.coordinator
- pipeline.config  
- pipeline.client

### State Management (2)
- pipeline.state.manager
- pipeline.state.file_tracker

### Context (2)
- pipeline.context.error
- pipeline.context.code

### Core Phases (8)
- pipeline.phases.base
- pipeline.phases.planning
- pipeline.phases.coding
- pipeline.phases.qa
- pipeline.phases.debugging
- pipeline.phases.investigation
- pipeline.phases.project_planning
- pipeline.phases.documentation

### Meta Phases (6)
- pipeline.phases.prompt_design
- pipeline.phases.tool_design
- pipeline.phases.role_design
- pipeline.phases.tool_evaluation
- pipeline.phases.prompt_improvement
- pipeline.phases.role_improvement

### Support (5)
- pipeline.logging_setup
- pipeline.tools
- pipeline.user_proxy
- pipeline.conversation_thread
- pipeline.agents.tool_advisor

## Dead Code to Delete (85 modules - 76.6%)

### Parallel/Duplicate Systems
- pipeline.orchestration/* (entire parallel system)
- pipeline.background_arbiter
- pipeline.continuous_monitor
- pipeline.action_tracker

### Unused Analysis Tools
- pipeline.architecture_analyzer
- pipeline.call_chain_tracer
- pipeline.call_graph_builder
- pipeline.change_history_analyzer
- pipeline.code_search
- pipeline.correlation_engine
- pipeline.failure_analyzer
- pipeline.import_analyzer
- pipeline.log_analyzer

### Unused Context/Debug
- pipeline.debug_context
- pipeline.debugging_support
- pipeline.debugging_utils
- pipeline.context_investigator
- pipeline.config_investigator

### Unused Error Handling
- pipeline.error_dedup
- pipeline.error_signature
- pipeline.error_strategies
- pipeline.failure_prompts

### Unused Pattern/Tool Systems
- pipeline.pattern_recognition (not integrated)
- pipeline.pattern_detector (not integrated)
- pipeline.pattern_optimizer (just created, not integrated)
- pipeline.tool_creator (not integrated)
- pipeline.tool_registry (not integrated)
- pipeline.tool_analyzer (not integrated)
- pipeline.tool_validator (just created, not integrated)

### Unused Prompts
- pipeline.prompts/* (most unused)

### Other Dead Code
- pipeline.handlers
- pipeline.line_fixer
- pipeline.loop_detection_system
- pipeline.command_detector
- pipeline.progress_display
- pipeline.system_analyzer_tools
- pipeline.text_tool_parser
- And 40+ more...

## What Actually Runs

```
run.py
  → pipeline.coordinator.PhaseCoordinator
    → pipeline.config.PipelineConfig
    → pipeline.client.OllamaClient
    → pipeline.state.manager.StateManager
    → pipeline.phases.* (13 phase classes)
      → pipeline.phases.base.BasePhase
        → pipeline.context.error.ErrorContext
        → pipeline.context.code.CodeContext
        → pipeline.tools (handlers)
        → pipeline.conversation_thread
```

That's it. Everything else is unreachable.

## Missing Integration Points

### Pattern System (Dead)
- Created but never called
- No integration with phases
- No integration with coordinator

### Tool Validation (Dead)
- Created but never called
- No integration with tool creation
- No integration with phases

### Orchestration System (Dead)
- Entire parallel implementation
- Specialists never used
- Arbiter never called

### Self-Development (Dead)
- Pattern recognition not integrated
- Tool creation not integrated
- Background monitoring not integrated

## Action Plan

1. **Delete 85 unused modules** (76.6% of code)
2. **Keep only the 26 used modules**
3. **Integrate pattern system properly** (if we want it)
4. **Integrate tool validation properly** (if we want it)
5. **Delete all parallel/duplicate implementations**

## The Real Problem

We have:
- Multiple coordinator implementations
- Multiple state management systems
- Multiple tool systems
- Multiple pattern systems
- Multiple prompt systems

But only ONE is actually used. The rest is architectural sprawl.