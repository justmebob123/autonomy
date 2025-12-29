# Deep Phase Analysis

## Phase Inventory

### Core Phases (Main Pipeline)
1. **planning.py** - Creates task plans from MASTER_PLAN
2. **coding.py** - Implements code for tasks
3. **qa.py** - Reviews code quality
4. **debugging.py** - Fixes code issues
5. **project_planning.py** - Expands project with new features

### Specialized Phases
6. **tool_design.py** - Designs new tools
7. **tool_evaluation.py** - Evaluates tool effectiveness
8. **documentation.py** - Updates documentation
9. **investigation.py** - Investigates issues

### Meta Phases (Prompt/Role Design)
10. **prompt_design.py** - Designs system prompts
11. **prompt_improvement.py** - Improves existing prompts
12. **role_design.py** - Designs agent roles
13. **role_improvement.py** - Improves agent roles

### Support
14. **base.py** - Base phase class
15. **loop_detection_mixin.py** - Loop detection

## Analysis Checklist

For each phase, verify:
- [ ] Has analysis tools imported (if applicable)
- [ ] Uses analysis in execute() method
- [ ] System prompt mentions analysis capabilities
- [ ] Conversation handling is correct
- [ ] Tool calling is properly implemented
- [ ] Error handling is comprehensive
- [ ] Loop detection is integrated

## Phase-by-Phase Analysis

### 1. Planning Phase
**Status:** ✅ Partially Integrated
**Analysis Tools:** complexity_analyzer, dead_code_detector, gap_finder, file_updater
**Issues:**
- Analysis tools imported but not fully utilized in execute()
- Prompt needs update with analysis guidance
- Should run analysis BEFORE planning

### 2. Coding Phase  
**Status:** ✅ Integrated
**Analysis Tools:** complexity_analyzer, dead_code_detector
**Issues:**
- Complexity validation after code generation ✅
- Could add more validation

### 3. QA Phase
**Status:** ✅ Integrated
**Analysis Tools:** All analyzers + run_comprehensive_analysis()
**Issues:**
- Comprehensive analysis before review ✅
- Good integration

### 4. Debugging Phase
**Status:** ✅ Integrated
**Analysis Tools:** complexity_analyzer, call_graph, gap_finder
**Issues:**
- Analysis before debugging ✅
- Good integration

### 5. Project Planning Phase
**Status:** ✅ Integrated
**Analysis Tools:** All analyzers + file_updater
**Issues:**
- Codebase analysis for planning ✅
- Good integration

### 6. Tool Design Phase
**Status:** ⚠️ Needs Review
**Analysis Tools:** None
**Issues:**
- Should have analysis capabilities
- Needs prompt update

### 7. Tool Evaluation Phase
**Status:** ⚠️ Needs Review
**Analysis Tools:** None
**Issues:**
- Should have analysis capabilities
- Needs prompt update

### 8. Documentation Phase
**Status:** ⚠️ Needs Review
**Analysis Tools:** None
**Issues:**
- Could benefit from analysis
- Needs prompt update

### 9. Investigation Phase
**Status:** ⚠️ Needs Review
**Analysis Tools:** None
**Issues:**
- Should have ALL analysis tools
- Critical for investigation
- Needs full integration

## Prompt Analysis

Need to examine:
1. System prompts structure
2. Tool guidance
3. Analysis capabilities mentioned
4. Conversation flow
5. Context management

## Conversation System Analysis

Need to verify:
1. chat_with_history() usage
2. Conversation thread management
3. Context preservation
4. Message formatting
5. Tool call handling