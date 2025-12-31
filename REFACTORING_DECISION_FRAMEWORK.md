# Refactoring Decision Framework

## Philosophy: The Mosaic Approach

> "It's like a color by number picture - it is our job to fill in the correct squares to paint the image we need. Like a giant mosaic, every piece has its role and position in the puzzle. We only need to study the plan and architecture to understand its role and purpose in the picture."

## Core Principle

**NOT ALL "DEAD CODE" SHOULD BE REMOVED**

In early development phases, code may appear unused because:
1. **Implementation is incomplete** - Features are planned but not yet integrated
2. **Architecture is evolving** - Components exist but connections aren't built yet
3. **Future integration planned** - Code is ready for upcoming features
4. **Test coverage pending** - Functionality exists but tests aren't written yet

## Decision Categories

### 1. Dead Code Analysis

When AI encounters "dead code", it must determine:

#### A. **Truly Dead** (Remove)
- Deprecated functionality explicitly marked for removal
- Duplicate implementations with no unique value
- Experimental code that failed and was abandoned
- Legacy code replaced by better implementations

**Indicators:**
- Comments like "TODO: Remove", "Deprecated", "Old implementation"
- No references in MASTER_PLAN.md or ARCHITECTURE.md
- Superseded by newer, better code
- No test coverage and no planned tests

**Action:** Remove with documentation of why

#### B. **Needs Integration** (Implement)
- Useful functionality not yet connected to main codebase
- Helper functions/classes ready but not called
- Infrastructure code waiting for features to use it
- Utility code that should be leveraged

**Indicators:**
- Mentioned in MASTER_PLAN.md or ARCHITECTURE.md
- Well-designed, tested, or documented
- Fills a clear architectural need
- Similar to code that IS being used

**Action:** Create integration tasks to connect it properly

#### C. **Needs Refactoring** (Improve)
- Good concept but poor implementation
- Overlapping with other code (needs consolidation)
- Correct functionality but wrong location
- Missing documentation or tests

**Indicators:**
- Duplicates functionality elsewhere
- Violates architecture patterns
- Has bugs or anti-patterns
- Lacks proper error handling

**Action:** Refactor to align with architecture and integrate

#### D. **Future Feature** (Preserve)
- Planned for upcoming development phases
- Part of roadmap but not yet priority
- Infrastructure for future capabilities
- Preparatory code for next milestones

**Indicators:**
- Explicitly mentioned in MASTER_PLAN.md roadmap
- Part of "Phase 2", "Phase 3", etc. plans
- Has TODO comments with future context
- Well-structured and ready for future use

**Action:** Document as "Reserved for Phase X" and preserve

## Required Context for AI Decisions

When AI analyzes any code issue, it MUST have access to:

### 1. **Strategic Documents**
- **MASTER_PLAN.md** - Full project vision, phases, roadmap
- **ARCHITECTURE.md** - Design patterns, conventions, structure
- **ROADMAP.md** (if exists) - Timeline and priorities

### 2. **Analysis Reports**
- **DEAD_CODE_REPORT.txt** - Unused functions, methods, imports
- **COMPLEXITY_REPORT.txt** - Complex functions needing simplification
- **ANTIPATTERN_REPORT.txt** - Design issues and code smells
- **INTEGRATION_GAP_REPORT.txt** - Unused classes and integration opportunities
- **BUG_DETECTION_REPORT.txt** - Potential bugs and issues
- **CALL_GRAPH_REPORT.txt** - Function relationships and dependencies

### 3. **Code Context**
- **Target file content** - The actual code being analyzed
- **Related files** - Files that import or are imported by target
- **Test files** - Existing test coverage
- **Documentation** - Docstrings, comments, README files

### 4. **Project State**
- **Current phase** - Foundation, Integration, Refinement, etc.
- **Completion percentage** - How far along development is
- **Recent changes** - What was recently added or modified
- **Pending tasks** - What's planned for near future

## Decision Workflow

### Step 1: Gather Full Context
```python
context = {
    'master_plan': read_file('MASTER_PLAN.md'),
    'architecture': read_file('ARCHITECTURE.md'),
    'dead_code_report': read_file('DEAD_CODE_REPORT.txt'),
    'complexity_report': read_file('COMPLEXITY_REPORT.txt'),
    'antipattern_report': read_file('ANTIPATTERN_REPORT.txt'),
    'integration_gaps': read_file('INTEGRATION_GAP_REPORT.txt'),
    'bug_report': read_file('BUG_DETECTION_REPORT.txt'),
    'call_graph': read_file('CALL_GRAPH_REPORT.txt'),
    'target_file': read_file(target_filepath),
    'related_files': get_related_files(target_filepath),
    'project_phase': get_current_phase(),
    'completion': get_completion_percentage(),
}
```

### Step 2: Analyze Against Master Plan
```
Questions to answer:
1. Is this code mentioned in MASTER_PLAN.md?
2. Does it align with stated project goals?
3. Is it part of current or future phases?
4. Does it serve the project vision?
```

### Step 3: Analyze Against Architecture
```
Questions to answer:
1. Does it follow ARCHITECTURE.md patterns?
2. Is it in the correct location/module?
3. Does it use proper abstractions?
4. Does it integrate with existing systems?
```

### Step 4: Analyze Relationships
```
Questions to answer:
1. What other code depends on this?
2. What does this code depend on?
3. Are there similar implementations elsewhere?
4. Could this be integrated with existing code?
```

### Step 5: Determine Action
Based on all context, choose ONE action:

**A. AUTO-FIX** (Simple, clear-cut cases)
- Remove truly dead imports
- Fix obvious bugs
- Consolidate exact duplicates
- Apply standard formatting

**B. CREATE INTEGRATION TASK** (Needs connection)
- Identify where code should be called
- Specify integration points
- Suggest test coverage
- Document expected behavior

**C. CREATE REFACTORING TASK** (Needs improvement)
- Specify what needs to change
- Explain why current approach is wrong
- Suggest better approach aligned with architecture
- Provide examples from existing code

**D. CREATE DEVELOPER REPORT** (Complex decision)
- Explain the situation fully
- Present multiple options with pros/cons
- Highlight architectural implications
- Request developer guidance

**E. PRESERVE WITH DOCUMENTATION** (Future feature)
- Add comment explaining purpose
- Reference MASTER_PLAN.md section
- Mark as "Reserved for Phase X"
- Ensure it doesn't interfere with current code

## Example Decision Trees

### Example 1: Unused Function
```
Function: calculate_project_metrics()
Status: Unused (no callers)

Context Analysis:
- MASTER_PLAN.md mentions "project analytics dashboard" in Phase 2
- ARCHITECTURE.md specifies metrics collection pattern
- Function is well-tested and documented
- Similar functions ARE being used elsewhere

Decision: PRESERVE + CREATE INTEGRATION TASK
Reasoning: This is planned functionality for Phase 2. Create task to integrate
           when dashboard is implemented. Add comment: "Reserved for Phase 2 analytics"
```

### Example 2: Duplicate Implementation
```
Functions: parse_json_config() in utils.py and config.py
Status: Duplicate implementations

Context Analysis:
- ARCHITECTURE.md specifies single source of truth for config parsing
- utils.py version is more robust with error handling
- config.py version is simpler but less safe
- Both are currently being used

Decision: REFACTOR + CONSOLIDATE
Reasoning: Keep utils.py version (more robust), update all callers of config.py
           version to use utils.py, remove config.py version. Aligns with
           architecture principle of single source of truth.
```

### Example 3: Complex Function
```
Function: process_user_request() - 150 lines, complexity 25
Status: High complexity

Context Analysis:
- MASTER_PLAN.md emphasizes maintainability
- ARCHITECTURE.md specifies max complexity of 10
- Function handles multiple concerns (validation, processing, logging)
- No obvious bugs but hard to test

Decision: CREATE REFACTORING TASK
Reasoning: Break into smaller functions following single responsibility:
           - validate_user_request()
           - process_validated_request()
           - log_request_result()
           Aligns with architecture and improves testability.
```

### Example 4: Unused Class
```
Class: CacheManager
Status: Unused (no instantiations)

Context Analysis:
- MASTER_PLAN.md mentions caching in Phase 1 (current phase)
- ARCHITECTURE.md specifies caching layer
- Class is well-designed and tested
- Similar pattern used elsewhere successfully

Decision: CREATE INTEGRATION TASK
Reasoning: This should be integrated NOW (Phase 1). Create task to:
           1. Identify cacheable operations
           2. Integrate CacheManager at appropriate points
           3. Add cache configuration
           4. Update tests to verify caching
```

### Example 5: Anti-pattern
```
Pattern: God class (ProjectManager with 50 methods)
Status: Anti-pattern detected

Context Analysis:
- ARCHITECTURE.md specifies separation of concerns
- Class handles database, API, validation, logging, etc.
- Violates single responsibility principle
- Hard to test and maintain

Decision: CREATE REFACTORING TASK
Reasoning: Split into focused classes following architecture:
           - ProjectRepository (database)
           - ProjectValidator (validation)
           - ProjectAPI (API endpoints)
           - ProjectLogger (logging)
           Each class has single, clear responsibility.
```

## AI Prompt Template

When AI analyzes code issues, use this template:

```
You are analyzing code in an early-stage project (Phase: {phase}, {completion}% complete).

CONTEXT PROVIDED:
1. MASTER_PLAN.md - Project vision and roadmap
2. ARCHITECTURE.md - Design patterns and conventions
3. Analysis reports - Dead code, complexity, bugs, etc.
4. Target code - The specific code being analyzed
5. Related code - Dependencies and dependents

YOUR TASK:
Analyze the following issue and determine the appropriate action.

ISSUE:
{issue_description}

TARGET CODE:
{target_code}

MASTER PLAN EXCERPT:
{relevant_master_plan_section}

ARCHITECTURE EXCERPT:
{relevant_architecture_section}

ANALYSIS REPORTS:
{relevant_analysis_findings}

DECISION FRAMEWORK:
Consider these questions:
1. Is this code mentioned in the master plan?
2. Does it align with the architecture?
3. Is it truly dead or just not yet integrated?
4. Should it be removed, improved, or integrated?
5. Is this a current phase or future phase concern?

AVAILABLE ACTIONS:
A. AUTO-FIX - Simple, clear-cut fix (remove dead import, fix obvious bug)
B. CREATE INTEGRATION TASK - Code is good but needs connection
C. CREATE REFACTORING TASK - Code needs improvement to align with architecture
D. CREATE DEVELOPER REPORT - Complex decision requiring human judgment
E. PRESERVE WITH DOCUMENTATION - Future feature, mark and preserve

PROVIDE YOUR DECISION:
Action: [A/B/C/D/E]
Reasoning: [Explain your decision based on the context]
Implementation: [Specific steps to take]
```

## Success Metrics

A good refactoring decision should:
1. ✅ Align with MASTER_PLAN.md vision
2. ✅ Follow ARCHITECTURE.md patterns
3. ✅ Consider project phase and maturity
4. ✅ Preserve valuable future functionality
5. ✅ Remove truly obsolete code
6. ✅ Improve code quality and maintainability
7. ✅ Enable rather than block development progress

## Anti-Patterns to Avoid

❌ **Premature Deletion** - Removing code that's planned for near future
❌ **Blind Automation** - Applying fixes without understanding context
❌ **Architecture Violation** - Making changes that break design patterns
❌ **Context Ignorance** - Deciding without reading master plan/architecture
❌ **Phase Confusion** - Treating early-stage code like mature codebase
❌ **Over-Optimization** - Refactoring code that's still evolving rapidly
❌ **Under-Documentation** - Making changes without explaining reasoning

## Summary

Every refactoring decision must be made with:
- **Full context** from strategic documents and analysis reports
- **Clear reasoning** based on project vision and architecture
- **Appropriate action** for the current development phase
- **Detailed documentation** of why the decision was made

Remember: We're painting a mosaic. Every piece has its place. Our job is to understand the picture and place each piece correctly.