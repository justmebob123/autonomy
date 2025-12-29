# Phase Integration Implementation Plan

## Current Status

### ✅ Already Implemented
1. **Native Analysis Tools** (pipeline/analysis/)
   - ComplexityAnalyzer
   - DeadCodeDetector
   - IntegrationGapFinder
   - CallGraphGenerator

2. **External Script Handlers** (pipeline/handlers.py)
   - analyze_enhanced (ENHANCED_DEPTH_61_ANALYZER.py)
   - analyze_improved (IMPROVED_DEPTH_61_ANALYZER.py)
   - deep_analyze (deep_analyze.py)

3. **Tool Definitions** (pipeline/tools/tool_definitions.py)
   - All external scripts have OpenAI-compatible definitions

4. **Custom Tools** (scripts/custom_tools/tools/)
   - code_complexity.py
   - find_todos.py
   - analyze_imports.py
   - Automatically discovered and registered via ToolRegistry

5. **File Update Tools** (pipeline/tools/file_updates.py)
   - append_to_file
   - update_section
   - insert_after/before
   - replace_between

6. **Direct Phase Access**
   - Planning: complexity_analyzer, dead_code_detector, gap_finder, file_updater
   - QA: All analyzers + run_comprehensive_analysis()
   - Debugging: complexity_analyzer, call_graph_generator, gap_finder
   - Coding: complexity_analyzer, dead_code_detector
   - Project Planning: All analyzers + file_updater

## What's Missing

### 1. Phase Execute() Integration
Phases have analyzers imported but DON'T USE THEM in execute() logic.

**Need to add:**
- Planning: Run analysis before planning to inform decisions
- QA: Use comprehensive analysis in review process
- Debugging: Analyze buggy code to understand issues
- Coding: Validate complexity after code generation
- Project Planning: Analyze codebase structure

### 2. Phase Prompt Updates
Phase prompts don't mention analysis capabilities or guide LLM on usage.

**Need to add:**
- When to use analysis tools
- How to interpret results
- What thresholds to enforce
- Examples of analysis usage

### 3. Other Phases Review
Need to check if other phases could benefit from analysis:
- tool_design
- tool_evaluation
- documentation

## Implementation Tasks

### Task 1: Add Analysis to Planning Phase Execute()
```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # BEFORE calling LLM, run analysis on existing code
    if self._should_analyze_existing_code(state):
        analysis_results = self._analyze_existing_codebase()
        # Add analysis results to context for LLM
        
    # Continue with normal planning...
```

### Task 2: Add Analysis to QA Phase Execute()
```python
def execute(self, state: PipelineState, filepath: str = None, **kwargs) -> PhaseResult:
    # AFTER reading file, run comprehensive analysis
    if content:
        issues = self.run_comprehensive_analysis(filepath)
        if issues:
            # Report issues found by analysis
            # LLM can add additional issues
```

### Task 3: Add Analysis to Debugging Phase Execute()
```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # BEFORE debugging, analyze the buggy code
    if filepath:
        complexity = self.complexity_analyzer.analyze(filepath)
        call_graph = self.call_graph_generator.generate(filepath)
        # Use analysis to understand the bug
```

### Task 4: Add Analysis to Coding Phase Execute()
```python
def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
    # AFTER code generation, validate complexity
    if new_code_created:
        complexity = self.complexity_analyzer.analyze(filepath)
        if complexity.max_complexity > 30:
            # Flag for refactoring
```

### Task 5: Update Phase Prompts
Add analysis guidance to each phase's system prompt:

**Planning Phase:**
```
You have access to code analysis tools:
- analyze_complexity: Check cyclomatic complexity
- detect_dead_code: Find unused code
- find_integration_gaps: Find architectural issues

Use these BEFORE planning to understand the codebase.
```

**QA Phase:**
```
You have comprehensive analysis capabilities:
- run_comprehensive_analysis(): Checks complexity, dead code, integration gaps
- Use this to find issues beyond manual review
- Complexity threshold: Flag functions with complexity ≥30
```

**Debugging Phase:**
```
Use analysis tools to understand bugs:
- analyze_complexity: Find complex code that may contain bugs
- generate_call_graph: Understand code flow
- find_integration_gaps: Check for architectural issues
```

## Implementation Order

1. ✅ Native analysis tools (DONE)
2. ✅ External script handlers (DONE)
3. ✅ Tool definitions (DONE)
4. ✅ Custom tools registration (DONE - automatic via ToolRegistry)
5. ⏳ Planning phase execute() integration (NEXT)
6. ⏳ QA phase execute() integration (NEXT)
7. ⏳ Debugging phase execute() integration (NEXT)
8. ⏳ Coding phase execute() integration (NEXT)
9. ⏳ Project Planning phase execute() integration (NEXT)
10. ⏳ Phase prompt updates (NEXT)
11. ⏳ Testing and validation (NEXT)

## Success Criteria

- [ ] All phases use analysis in execute() logic
- [ ] Phase prompts guide LLM on analysis usage
- [ ] Analysis results inform phase decisions
- [ ] Comprehensive testing completed
- [ ] No regressions in existing functionality