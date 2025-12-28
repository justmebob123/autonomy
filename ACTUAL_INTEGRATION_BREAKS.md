# Actual Integration Breaks Found Through Meticulous Tracing

## Critical Bugs Found

### 1. ✅ FIXED: BasePhase.chat_with_history calling client.chat incorrectly
- **Location**: pipeline/phases/base.py line 576
- **Problem**: Called `self.client.chat(messages=messages, tools=tools)` but client.chat requires `host` and `model` as first two positional arguments
- **Impact**: ALL phases would fail immediately with TypeError when trying to call LLM
- **Introduced**: Commit 9ad6269 (Dec 27, 2025)
- **Status**: FIXED - now gets model from conversation.thread.model and host from config.model_assignments
- **How Found**: Traced execution path from run.py → coordinator → phase.run() → chat_with_history → client.chat

### 2. ⚠️ CorrelationEngine initialized but never called
- **Location**: coordinator.py line 105
- **Problem**: `self.correlation_engine = CorrelationEngine()` but never used
- **Integration Point**: Should be called after analyzers collect findings
- **Missing Call**: After `perform_application_troubleshooting()` runs all analyzers, should call:
  ```python
  for component, findings in results.items():
      self.correlation_engine.add_finding(component, findings)
  correlations = self.correlation_engine.correlate()
  ```
- **Impact**: Cross-component insights never generated
- **Status**: NOT FIXED YET

### 3. ⚠️ perform_application_troubleshooting() never called
- **Location**: runtime_tester.py line 567
- **Problem**: Function defined but never invoked
- **What it does**: Runs all analyzers (log, call_chain, change_history, config, architecture)
- **Impact**: All those analyzers never actually run
- **Status**: NOT FIXED YET

## Dead Code Paths Discovered

### 1. Application Troubleshooting System (Entire Subsystem Unused)
- **Files Involved**:
  * runtime_tester.py: perform_application_troubleshooting() (never called)
  * correlation_engine.py: CorrelationEngine (initialized but never used)
  * All analyzer modules (imported but analysis results never used)
- **Impact**: Entire troubleshooting subsystem is disconnected
- **Root Cause**: No integration point between RuntimeTester and the analysis/correlation system

### 2. Analyzer Results Not Used
- **Analyzers That Run But Results Ignored**:
  * LogAnalyzer - analyzes logs
  * CallChainTracer - traces call chains
  * ChangeHistoryAnalyzer - analyzes git history
  * ConfigInvestigator - investigates config
  * ArchitectureAnalyzer - analyzes architecture
- **Problem**: Results collected but never passed to CorrelationEngine or used for decisions

## Integration Gaps

### 1. RuntimeTester → CorrelationEngine
- **Current**: RuntimeTester has perform_application_troubleshooting() that runs analyzers
- **Missing**: No call to this function
- **Missing**: No integration with CorrelationEngine to correlate findings
- **Should Be**: After analyzers run, feed results to CorrelationEngine, then use correlations

### 2. CorrelationEngine → StateManager
- **Current**: StateManager has add_correlation() method ready
- **Missing**: No code path that calls it
- **Should Be**: After CorrelationEngine.correlate(), results should be stored via StateManager.add_correlation()

### 3. Correlations → Decision Making
- **Current**: Correlations would be stored in state
- **Missing**: No code that reads correlations from state to influence decisions
- **Should Be**: Coordinator should consider correlations when deciding next actions

## Pattern of Problems

The pattern I'm seeing is:
1. **Infrastructure exists** (CorrelationEngine, analyzers, state storage)
2. **Integration points defined** (add_correlation method, etc.)
3. **But no actual calls** connecting them together
4. **Result**: Subsystems sit disconnected

This is exactly what you were describing - code that looks integrated at a glance but when you trace actual execution paths, nothing is connected.

## Next Steps

1. Fix perform_application_troubleshooting() - find where it should be called
2. Integrate CorrelationEngine with analyzer results
3. Connect correlations to StateManager
4. Use correlations in decision-making
5. Continue tracing ALL execution paths to find more breaks

## Methodology

Tracing actual execution paths:
- Start from entry point (run.py)
- Follow each function call
- Check parameter passing
- Verify methods exist and are called correctly
- Find where initialized objects are actually used
- Identify dead code paths

This is revealing the actual integration state, not just what the code claims to do.