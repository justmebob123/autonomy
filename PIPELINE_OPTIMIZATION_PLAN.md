# Pipeline Optimization Plan

## Issues Identified

### 1. Over-Documentation
- Planning phase spends too much time updating MASTER_PLAN.md
- Coding phase sometimes creates .md files instead of code
- Missing critical documents: PRIMARY_OBJECTIVES.md, SECONDARY_OBJECTIVES.md, TERTIARY_OBJECTIVES.md
- ARCHITECTURE.md is just a placeholder

### 2. Inefficient Phase Balance
- Too much time on QA and documentation
- Not enough time on coding and debugging
- Planning phase creating duplicate tasks

### 3. Missing Strategic Documents
- No PRIMARY_OBJECTIVES.md
- No SECONDARY_OBJECTIVES.md  
- No TERTIARY_OBJECTIVES.md
- Empty ARCHITECTURE.md

## Proposed Solutions

### 1. Limit Documentation Updates
- MASTER_PLAN.md should only be updated when:
  * New major features are added
  * Architecture changes significantly
  * NOT on every planning iteration
- Add rate limiting: max 1 update per 10 iterations

### 2. Restrict Coding Phase File Types
- Coding phase should ONLY create:
  * .py files (Python code)
  * .yaml/.yml files (configuration)
  * .json files (data/config)
- Documentation files (.md) should ONLY be created by documentation phase

### 3. Optimize QA Analysis
- Reduce analysis depth for test files
- Skip analysis for files < 100 lines
- Focus QA on production code, not tests

### 4. Improve Planning Efficiency
- Check for duplicate tasks BEFORE calling LLM
- Limit planning iterations to 2 per cycle
- Skip planning if < 5 tasks remaining

### 5. Create Missing Strategic Documents
- Generate PRIMARY_OBJECTIVES.md with core goals
- Generate SECONDARY_OBJECTIVES.md with supporting goals
- Generate TERTIARY_OBJECTIVES.md with nice-to-have features
- Populate ARCHITECTURE.md with actual architecture

## Implementation Priority

1. **HIGH**: Restrict coding phase to code files only
2. **HIGH**: Create missing strategic documents
3. **MEDIUM**: Limit MASTER_PLAN.md updates
4. **MEDIUM**: Optimize QA for test files
5. **LOW**: Improve planning duplicate detection