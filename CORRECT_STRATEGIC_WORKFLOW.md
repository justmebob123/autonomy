# Correct Strategic Document Workflow

## Document Hierarchy (Increasing Detail)

### 1. MASTER_PLAN.md
- **Purpose**: High-level vision and goals
- **Updated**: Only when ~95% of objectives complete
- **Content**: Project vision, core goals, success criteria
- **Stability**: Most stable - rarely changes

### 2. PRIMARY_OBJECTIVES.md
- **Purpose**: Core functional requirements
- **Updated**: By planning when major features change
- **Content**: What needs to be built (high-level features)
- **Detail Level**: Functional requirements

### 3. SECONDARY_OBJECTIVES.md
- **Purpose**: Detailed implementation specifics
- **Updated**: By planning after each analysis cycle
- **Content**:
  - Architectural changes needed
  - Testing requirements and gaps
  - Reported failures and inconsistencies
  - Specific integration requirements
  - References to existing design and code
  - Component-level issues
- **Detail Level**: Implementation specifics

### 4. TERTIARY_OBJECTIVES.md
- **Purpose**: Fine-grained implementation details
- **Updated**: By planning after deep analysis
- **Content**:
  - Specific code examples
  - Detailed integration patterns
  - Component-level design flaws
  - Misdesigned components needing fixes
  - Concrete implementation guidance
  - Line-by-line fixes needed
- **Detail Level**: Code-level specifics

### 5. ARCHITECTURE.md
- **Purpose**: Current architectural state and intended design
- **Updated**: By planning to reflect reality
- **Content**:
  - Current architecture
  - Intended architecture
  - Gaps between current and intended
  - Design patterns in use
  - Module structure
- **Detail Level**: System design

## Planning Phase Workflow

### Step 1: Load and Analyze
```
1. Load MASTER_PLAN.md (guidance)
2. Load PRIMARY_OBJECTIVES.md (what to build)
3. Load SECONDARY_OBJECTIVES.md (how to build)
4. Load TERTIARY_OBJECTIVES.md (specific details)
5. Load ARCHITECTURE.md (current state)
```

### Step 2: Deep Codebase Analysis
```
1. Run complexity analysis on all code
2. Detect dead code and unused components
3. Find integration gaps
4. Identify architectural inconsistencies
5. Check for design pattern violations
6. Analyze test coverage
7. Review error logs and failures
```

### Step 3: Compare Actual vs Intended
```
1. Compare actual architecture vs ARCHITECTURE.md
2. Identify deviations
3. Find misdesigned components
4. Detect architectural drift
5. Note missing components
```

### Step 4: Update Strategic Documents

#### Update SECONDARY_OBJECTIVES.md
```
Add sections for:
- Architectural Changes Needed
  * Component X needs refactoring (complexity 45)
  * Module Y has integration gaps
  * Service Z missing error handling
  
- Testing Requirements
  * Unit tests needed for modules A, B, C
  * Integration tests missing for workflow D
  * Coverage gaps in components E, F
  
- Reported Failures
  * Bug #123: Memory leak in component X
  * Issue #456: Race condition in module Y
  * Error: Timeout in service Z
  
- Integration Issues
  * Component A doesn't integrate with B
  * Missing API endpoints for feature C
  * Database schema mismatch in module D
```

#### Update TERTIARY_OBJECTIVES.md
```
Add sections for:
- Specific Code Examples
  ```python
  # Fix for component X
  class ImprovedComponent:
      def method(self):
          # Specific implementation
  ```
  
- Component-Level Fixes
  * File: monitors/cpu.py, Line 45
    Problem: Inefficient loop
    Fix: Use list comprehension
    
  * File: alerts/email.py, Line 78
    Problem: Missing error handling
    Fix: Add try-except block
    
- Design Pattern Improvements
  * Replace singleton with dependency injection
  * Add observer pattern for event handling
  * Implement factory for monitor creation
```

#### Update ARCHITECTURE.md
```
Update sections:
- Current Architecture (what exists)
- Intended Architecture (what should exist)
- Gaps (what's missing)
- Migration Path (how to get there)
```

### Step 5: Check MASTER_PLAN Update Threshold
```
1. Count completed objectives
2. If >= 95% complete:
   - Update MASTER_PLAN.md with achievements
   - Set new high-level goals
   - Reset objective counters
3. Else:
   - Keep MASTER_PLAN.md stable
```

### Step 6: Create Tasks
```
1. Read SECONDARY_OBJECTIVES for what needs doing
2. Read TERTIARY_OBJECTIVES for how to do it
3. Create specific, actionable tasks
4. Reference relevant document sections in task descriptions
```

## All Phases Should Use These Documents

### Coding Phase
```
When implementing task:
1. Read PRIMARY_OBJECTIVES for context
2. Read SECONDARY_OBJECTIVES for requirements
3. Read TERTIARY_OBJECTIVES for specific guidance
4. Read ARCHITECTURE.md for design patterns
5. Implement according to guidance
```

### QA Phase
```
When reviewing code:
1. Check against PRIMARY_OBJECTIVES (does it meet requirements?)
2. Check against SECONDARY_OBJECTIVES (correct implementation?)
3. Check against TERTIARY_OBJECTIVES (specific details correct?)
4. Check against ARCHITECTURE.md (follows design patterns?)
```

### Debugging Phase
```
When fixing issues:
1. Check SECONDARY_OBJECTIVES for known issues
2. Check TERTIARY_OBJECTIVES for specific fixes
3. Update documents with new findings
```

## Inter-Process Communication

These documents serve as **shared memory** between phases:
- Planning writes analysis results
- Coding reads implementation guidance
- QA reads quality criteria
- Debugging reads known issues
- All phases contribute findings

## Implementation Requirements

### Planning Phase Enhancements Needed
1. Add deep codebase analysis
2. Add architecture comparison logic
3. Add document update logic
4. Add 95% completion check
5. Add document reading for all phases

### Tool Requirements
- File update tools (append, update_section, etc.)
- Analysis tools (complexity, dead code, gaps)
- Architecture analysis tools
- Document parsing tools

### Prompt Updates Needed
- Planning prompt: Add document analysis instructions
- Coding prompt: Add document reference instructions
- QA prompt: Add document checking instructions
- Debugging prompt: Add document update instructions

## Success Criteria

Planning phase should:
- ✅ Analyze codebase deeply
- ✅ Update SECONDARY_OBJECTIVES with findings
- ✅ Update TERTIARY_OBJECTIVES with specifics
- ✅ Update ARCHITECTURE.md with current state
- ✅ Only update MASTER_PLAN at 95% completion
- ✅ Create tasks based on document guidance

All phases should:
- ✅ Read relevant document sections
- ✅ Use documents to guide work
- ✅ Reference documents in decisions
- ✅ Contribute findings back to documents