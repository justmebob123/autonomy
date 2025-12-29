# Complete Scripts Integration Plan

## Current State Analysis

### What We Have
1. **Native Analysis Tools** (pipeline/analysis/):
   - complexity.py - Cyclomatic complexity analyzer
   - dead_code.py - Unused code detector
   - integration_gaps.py - Architectural gap finder
   - call_graph.py - Call graph generator

2. **External Analysis Scripts** (scripts/analysis/):
   - COMPLEXITY_ANALYZER.py
   - DEAD_CODE_DETECTOR.py
   - INTEGRATION_GAP_FINDER.py
   - CALL_GRAPH_GENERATOR.py
   - ENHANCED_DEPTH_61_ANALYZER.py
   - IMPROVED_DEPTH_61_ANALYZER.py
   - deep_analyze.py (in scripts/)

3. **Custom Tools** (scripts/custom_tools/tools/):
   - code_complexity.py
   - find_todos.py
   - analyze_imports.py
   - test_tool.py

4. **File Update Tools** (pipeline/tools/):
   - file_updates.py (5 tools for file manipulation)

### What's Missing

#### 1. External Scripts Not Integrated
- ENHANCED_DEPTH_61_ANALYZER.py - Deep recursive analysis
- IMPROVED_DEPTH_61_ANALYZER.py - Improved deep analysis
- deep_analyze.py - Unified analysis CLI

#### 2. Phase Integration Incomplete
- Phases have analyzers imported but NOT USED in execute() logic
- Phase prompts don't mention analysis capabilities
- No guidance on when/how to use analysis tools

#### 3. Custom Tools Not Exposed
- Custom tools exist but not registered in handlers
- No tool definitions for LLM to call them

## Integration Tasks

### Task 1: Add External Script Tool Handlers ⏳
Create handlers for:
- analyze_enhanced (ENHANCED_DEPTH_61_ANALYZER.py)
- analyze_improved (IMPROVED_DEPTH_61_ANALYZER.py)
- deep_analyze (deep_analyze.py)

### Task 2: Update Phase Execute() Logic ⏳
For each phase, add analysis calls at appropriate points:

**Planning Phase**:
- Run complexity analysis on existing code
- Check for integration gaps
- Use results to inform planning decisions

**QA Phase**:
- Run comprehensive analysis
- Check complexity thresholds
- Detect dead code
- Find integration gaps
- Generate call graphs for complex modules

**Debugging Phase**:
- Analyze complexity of buggy code
- Generate call graphs to understand flow
- Check for integration issues

**Coding Phase**:
- Check complexity after code generation
- Detect potential dead code
- Validate against thresholds

**Project Planning Phase**:
- Analyze entire codebase structure
- Find architectural gaps
- Plan improvements based on analysis

### Task 3: Update Phase Prompts ⏳
Add analysis guidance to each phase's system prompt:
- When to use analysis tools
- How to interpret results
- What thresholds to enforce
- How to act on findings

### Task 4: Register Custom Tools ⏳
- Add custom tool definitions to handlers
- Ensure LLM can discover and call them
- Test tool calling flow

### Task 5: Create Unified Analysis Interface ⏳
- Single entry point for all analysis
- Consistent result format
- Easy to use from any phase

## Implementation Order

1. ✅ Native analysis tools (DONE)
2. ✅ File update tools (DONE)
3. ✅ Direct phase access (DONE)
4. ⏳ External script handlers (NEXT)
5. ⏳ Phase execute() integration (NEXT)
6. ⏳ Phase prompt updates (NEXT)
7. ⏳ Custom tools registration (NEXT)
8. ⏳ Testing and validation (NEXT)

## Success Criteria

- [ ] All scripts/ tools accessible via tool calling
- [ ] All phases use analysis in execute() logic
- [ ] Phase prompts guide LLM on analysis usage
- [ ] Custom tools properly registered
- [ ] Comprehensive testing completed
- [ ] Documentation updated