# Investigation Phase Analysis

## Current State

### Investigation Phase EXISTS ✅
- **Location**: `pipeline/phases/investigation.py`
- **Status**: Fully implemented with comprehensive analysis tools
- **System Prompt**: Defined locally in `_get_system_prompt()` method (line 193)

### Problem: Inconsistent Prompt Management ⚠️
The investigation phase uses a **local system prompt** instead of the centralized `SYSTEM_PROMPTS` dictionary in `prompts.py`.

**Current approach (investigation phase only):**
```python
def _get_system_prompt(self, phase_name: str = None) -> str:
    """Get system prompt for investigation phase"""
    return """You are a senior software engineer investigating a code issue..."""
```

**Standard approach (all other phases):**
```python
# In prompts.py
SYSTEM_PROMPTS = {
    "planning": """...""",
    "coding": """...""",
    "qa": """...""",
    # ... etc
}
```

## Analysis of Current Investigation Prompt

### Strengths ✅
1. **Clear role definition**: "senior software engineer investigating a code issue"
2. **Tool calling requirements**: Explicit instructions for proper tool usage
3. **Investigation process**: 7-step workflow defined
4. **Diagnosis focus**: Emphasizes understanding over fixing

### Weaknesses ⚠️
1. **Missing GOAL statement**: No explicit mission/objective
2. **Limited tool set**: Only mentions 3 tools (read_file, search_code, list_directory)
3. **No workflow examples**: Lacks concrete examples of investigation flow
4. **No warnings about pitfalls**: Missing guidance on common mistakes
5. **Inconsistent with system**: Not in centralized prompts.py
6. **No analysis tool guidance**: Doesn't mention the comprehensive analysis tools available

## Investigation Phase Capabilities

The investigation phase has access to **ALL analysis tools**:
- ComplexityAnalyzer
- DeadCodeDetector
- IntegrationGapFinder
- CallGraphGenerator
- BugDetector
- AntiPatternDetector
- DataFlowAnalyzer

But the prompt doesn't mention these capabilities!

## Recommendations

### 1. Move Prompt to Central Location
Move the investigation prompt from `investigation.py` to `prompts.py` for consistency.

### 2. Enhance Prompt Quality
Add:
- **GOAL statement**: Clear mission and objectives
- **Complete tool inventory**: All available analysis tools
- **Workflow examples**: Concrete investigation scenarios
- **Common pitfalls**: Warnings about infinite analysis loops
- **Integration guidance**: How to use analysis results

### 3. Grade Target: A
Current grade: C (basic prompt, missing key elements)
Target grade: A (comprehensive, with examples and warnings)

## Implementation Plan

1. Create comprehensive investigation prompt in `prompts.py`
2. Update `investigation.py` to use centralized prompt
3. Add goal statements to all other phases
4. Ensure consistency across all 14 phases