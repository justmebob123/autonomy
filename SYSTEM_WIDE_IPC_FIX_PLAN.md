# System-Wide IPC Document Usage Fix Plan

## Problem

Currently, phases READ strategic documents but don't actually USE them effectively:

1. **QA Phase**: Mentions SECONDARY_OBJECTIVES in prompt but doesn't include content
2. **Coding Phase**: Reads strategic docs but doesn't use them in prompts
3. **Debugging Phase**: Reads strategic docs but doesn't use them in prompts
4. **Refactoring Phase**: Reads some objectives but not all three tiers
5. **Investigation Phase**: Reads strategic docs but doesn't use them

## Solution: System-Wide Integration

### Phase-by-Phase Integration Plan

#### 1. QA Phase
**Current**: Mentions documents in prompt guidance
**Fix**: Include actual content from SECONDARY_OBJECTIVES and TERTIARY_OBJECTIVES

```python
# In QA prompt
secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')
tertiary_objectives = strategic_docs.get('TERTIARY_OBJECTIVES.md', '')

prompt += f"""
## Quality Standards (from SECONDARY_OBJECTIVES.md)
{secondary_objectives}

## Known Issues to Check (from TERTIARY_OBJECTIVES.md)
{tertiary_objectives}
"""
```

#### 2. Coding Phase
**Current**: Reads strategic docs but doesn't use them
**Fix**: Include PRIMARY_OBJECTIVES for feature context and TERTIARY_OBJECTIVES for implementation details

```python
# In Coding prompt
primary_objectives = strategic_docs.get('PRIMARY_OBJECTIVES.md', '')
tertiary_objectives = strategic_docs.get('TERTIARY_OBJECTIVES.md', '')

prompt += f"""
## Features to Implement (from PRIMARY_OBJECTIVES.md)
{primary_objectives}

## Specific Implementation Steps (from TERTIARY_OBJECTIVES.md)
{tertiary_objectives}
"""
```

#### 3. Debugging Phase
**Current**: Reads strategic docs but doesn't use them
**Fix**: Include SECONDARY_OBJECTIVES for known failures and TERTIARY_OBJECTIVES for specific fixes

```python
# In Debugging prompt
secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')
tertiary_objectives = strategic_docs.get('TERTIARY_OBJECTIVES.md', '')

prompt += f"""
## Known Failures (from SECONDARY_OBJECTIVES.md)
{secondary_objectives}

## Specific Fixes Needed (from TERTIARY_OBJECTIVES.md)
{tertiary_objectives}
"""
```

#### 4. Refactoring Phase
**Current**: Reads PRIMARY and SECONDARY but not TERTIARY
**Fix**: Include all three tiers plus ARCHITECTURE.md

```python
# In Refactoring prompt
primary_objectives = strategic_docs.get('PRIMARY_OBJECTIVES.md', '')
secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')
tertiary_objectives = strategic_docs.get('TERTIARY_OBJECTIVES.md', '')
architecture = strategic_docs.get('ARCHITECTURE.md', '')

prompt += f"""
## Strategic Context

### Features (PRIMARY_OBJECTIVES.md)
{primary_objectives}

### Architectural Changes Needed (SECONDARY_OBJECTIVES.md)
{secondary_objectives}

### Specific Refactoring Steps (TERTIARY_OBJECTIVES.md)
{tertiary_objectives}

### Intended vs Actual Design (ARCHITECTURE.md)
{architecture}
"""
```

#### 5. Investigation Phase
**Current**: Reads strategic docs but doesn't use them
**Fix**: Include all objectives for context

```python
# In Investigation prompt
primary_objectives = strategic_docs.get('PRIMARY_OBJECTIVES.md', '')
secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')

prompt += f"""
## Investigation Context

### System Goals (PRIMARY_OBJECTIVES.md)
{primary_objectives}

### Known Issues (SECONDARY_OBJECTIVES.md)
{secondary_objectives}
"""
```

#### 6. Documentation Phase
**Current**: Reads ARCHITECTURE.md but not objectives
**Fix**: Include all documents for comprehensive documentation

```python
# In Documentation prompt
primary_objectives = strategic_docs.get('PRIMARY_OBJECTIVES.md', '')
secondary_objectives = strategic_docs.get('SECONDARY_OBJECTIVES.md', '')
architecture = strategic_docs.get('ARCHITECTURE.md', '')

prompt += f"""
## Documentation Context

### Features to Document (PRIMARY_OBJECTIVES.md)
{primary_objectives}

### Quality Standards (SECONDARY_OBJECTIVES.md)
{secondary_objectives}

### Architecture (ARCHITECTURE.md)
{architecture}
"""
```

### Files to Modify

1. **pipeline/prompts.py**
   - Update `get_qa_prompt()` to include SECONDARY and TERTIARY content
   - Update `get_coding_prompt()` to include PRIMARY and TERTIARY content
   - Update `get_debugging_prompt()` to include SECONDARY and TERTIARY content
   - Update `get_refactoring_prompt()` to include all objectives
   - Update `get_investigation_prompt()` to include objectives
   - Update `get_documentation_prompt()` to include objectives

2. **pipeline/phases/qa.py**
   - Pass strategic_docs to prompt builder
   - Extract SECONDARY and TERTIARY content

3. **pipeline/phases/coding.py**
   - Pass strategic_docs to prompt builder
   - Extract PRIMARY and TERTIARY content

4. **pipeline/phases/debugging.py**
   - Pass strategic_docs to prompt builder
   - Extract SECONDARY and TERTIARY content

5. **pipeline/phases/refactoring.py**
   - Already reads objectives, ensure all three tiers are used
   - Pass to prompt builder

6. **pipeline/phases/investigation.py**
   - Pass strategic_docs to prompt builder
   - Extract PRIMARY and SECONDARY content

7. **pipeline/phases/documentation.py**
   - Pass strategic_docs to prompt builder
   - Extract all objectives and architecture

### Implementation Order

1. **First**: Update `pipeline/prompts.py` to accept strategic_docs parameter
2. **Second**: Update each phase to pass strategic_docs to prompts
3. **Third**: Test each phase to ensure documents are used
4. **Fourth**: Verify prompt sizes don't exceed limits

### Prompt Size Management

Since including full documents could make prompts large:

1. **Truncate if needed**: Limit each document to first 2000 characters
2. **Summarize**: Extract key sections only
3. **Conditional inclusion**: Only include if document exists and has content

### Success Criteria

- [ ] QA phase uses SECONDARY and TERTIARY objectives
- [ ] Coding phase uses PRIMARY and TERTIARY objectives
- [ ] Debugging phase uses SECONDARY and TERTIARY objectives
- [ ] Refactoring phase uses all three tiers plus ARCHITECTURE
- [ ] Investigation phase uses PRIMARY and SECONDARY objectives
- [ ] Documentation phase uses all documents
- [ ] All phases log when they use strategic documents
- [ ] Prompt sizes remain manageable (<100KB)