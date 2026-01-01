# Comprehensive Unused Code Analysis System

## Requirements

When encountering "unused" code, the system must:

### 1. Project Context Analysis
- Determine project completion percentage
- Identify current development stage (early/mid/late)
- Understand what's implemented vs planned

### 2. Architecture Alignment Analysis
- Compare unused file against ARCHITECTURE.md
- Determine if it matches intended design patterns
- Check if it's a BETTER implementation than existing code

### 3. Related Files Analysis
- Find all similar/related files
- Compare implementations
- Identify overlapping functionality
- Determine which implementation is superior

### 4. Integration Analysis
- Check if unused file SHOULD be integrated
- Identify files that should be using it
- Determine refactoring needed to integrate it

### 5. Decision Matrix

**If unused file is BETTER than existing:**
→ Refactor existing files to use the better implementation
→ Deprecate inferior implementations
→ Update imports and references

**If unused file is EQUIVALENT:**
→ Merge implementations
→ Consolidate into single solution
→ Update all references

**If unused file is INFERIOR:**
→ Create issue report explaining why
→ Suggest removal only if truly redundant
→ Preserve if part of planned architecture

**If unused file is UNRELATED:**
→ Check if it's future functionality
→ Verify against MASTER_PLAN.md
→ Keep if planned, report if orphaned

## Implementation Needed

1. **Project stage detector** - Analyze completion percentage
2. **Architecture comparator** - Compare against ARCHITECTURE.md patterns
3. **Implementation ranker** - Score implementations by quality
4. **Integration planner** - Generate refactoring plan
5. **Decision engine** - Make intelligent keep/merge/refactor/remove decisions

## Example Scenario

**Unused File**: `core/git/git_integration.py` (GitIntegration class)

**Analysis Steps**:
1. Check project: 25% complete, early stage
2. Check ARCHITECTURE.md: Does it mention git integration? Yes
3. Find related files: Search for other git-related code
4. Compare implementations: Is GitIntegration better than alternatives?
5. Check usage: Should other files be using GitIntegration?
6. Decision: 
   - If better → Refactor other files to use it
   - If equivalent → Merge with existing
   - If planned → Keep and document
   - If orphaned → Report for review

## Current Problem

The system currently just warns "don't remove in early stage" but doesn't:
- ❌ Analyze project completion
- ❌ Compare against architecture
- ❌ Find related implementations
- ❌ Determine which is better
- ❌ Generate refactoring plan
- ❌ Make intelligent decisions

## Solution Needed

Implement comprehensive analysis that makes INTELLIGENT decisions, not just blanket warnings.