# Phase 4: Prompt Updates for IPC System

## Overview
Update the system prompts for Coding, QA, and Debugging phases to include guidance on using the Document IPC system.

## Prompt Update Strategy

### Common IPC Guidance to Add
All three phase prompts should include:

1. **Document Awareness**
   - Explain that the phase has access to strategic documents
   - Describe what information is available in each document
   - Guide on when to reference these documents

2. **Communication Protocol**
   - Explain the READ/WRITE document system
   - Clarify that status updates are automatically written
   - Note that messages are automatically sent to other phases

3. **Context Integration**
   - Encourage using strategic documents for decision-making
   - Reference SECONDARY_OBJECTIVES for architectural guidance
   - Reference TERTIARY_OBJECTIVES for specific implementation details

## Phase-Specific Updates

### 1. Coding Phase Prompt (`get_coding_prompt`)

**Current Focus**: Task implementation with error handling

**IPC Additions Needed**:
```
DOCUMENT CONTEXT AVAILABLE:
- SECONDARY_OBJECTIVES: Architectural changes, testing requirements, reported failures
- TERTIARY_OBJECTIVES: Specific code examples and implementation guidance
- ARCHITECTURE: Current vs intended architecture, design patterns
- QA_WRITE: Recent quality feedback on your code
- DEBUG_WRITE: Recent bug fixes and known issues

GUIDANCE:
- Review TERTIARY_OBJECTIVES for specific implementation examples
- Check SECONDARY_OBJECTIVES for architectural requirements
- Consider recent QA feedback when implementing
- Follow patterns described in ARCHITECTURE document
- Your completion status will be automatically sent to QA phase
```

### 2. QA Phase Prompt (`get_qa_prompt`)

**Current Focus**: Code quality review with tool calling

**IPC Additions Needed**:
```
DOCUMENT CONTEXT AVAILABLE:
- SECONDARY_OBJECTIVES: Quality standards, testing requirements
- TERTIARY_OBJECTIVES: Known issues and specific checks needed
- ARCHITECTURE: Expected design patterns and structure
- DEVELOPER_WRITE: Recent code changes and developer notes
- DEBUG_WRITE: Recently fixed bugs to verify

GUIDANCE:
- Use SECONDARY_OBJECTIVES to determine quality criteria
- Check TERTIARY_OBJECTIVES for specific issues to look for
- Verify code follows ARCHITECTURE patterns
- Review DEVELOPER_WRITE for context on recent changes
- Your findings will be automatically sent to debugging phase
- Approvals will be automatically sent to developer phase
```

### 3. Debugging Phase Prompt (`get_debug_prompt`)

**Current Focus**: Bug fixing with runtime/syntax error handling

**IPC Additions Needed**:
```
DOCUMENT CONTEXT AVAILABLE:
- SECONDARY_OBJECTIVES: Known architectural issues
- TERTIARY_OBJECTIVES: Specific bug patterns and fixes
- ARCHITECTURE: Intended design to guide fixes
- QA_WRITE: Reported bugs and quality issues
- DEVELOPER_WRITE: Recent code changes that may have introduced bugs

GUIDANCE:
- Check TERTIARY_OBJECTIVES for known bug patterns
- Use SECONDARY_OBJECTIVES for architectural context
- Review QA_WRITE for detailed bug reports
- Consider DEVELOPER_WRITE for recent changes
- Your fix status will be automatically sent to QA for verification
- Architectural changes will be sent to developer phase
```

## Implementation Approach

### Option 1: Add IPC Section to Each Prompt
Add a dedicated section at the beginning or end of each prompt explaining the IPC system.

**Pros**: Clear, explicit, easy to understand
**Cons**: Makes prompts longer

### Option 2: Integrate IPC Guidance Throughout
Weave IPC references naturally into existing prompt sections.

**Pros**: More natural, doesn't increase length significantly
**Cons**: Less explicit, might be overlooked

### Option 3: Hybrid Approach (RECOMMENDED)
- Add a brief IPC overview section
- Integrate specific references where relevant
- Keep it concise but informative

## Example Implementation

### Coding Phase Prompt Enhancement:

```python
def get_coding_prompt(task_description: str, target_file: str, 
                      context: str, errors: str = "") -> str:
    """Generate the user prompt for coding phase"""
    
    ipc_guidance = """
STRATEGIC CONTEXT:
You have access to strategic documents that guide your implementation:
- SECONDARY_OBJECTIVES: Architectural requirements and testing needs
- TERTIARY_OBJECTIVES: Specific implementation examples and patterns
- ARCHITECTURE: Design patterns and structure guidelines

Review these documents to ensure your implementation aligns with project goals.
Your completion status will be automatically communicated to the QA phase.
"""
    
    error_section = ""
    if errors:
        error_section = f"""
PREVIOUS ERRORS (you MUST fix these!):
{errors}
"""
    
    return f"""Implement this task:

TASK: {task_description}
TARGET FILE: {target_file}
{error_section}
{ipc_guidance}

EXISTING CODE CONTEXT:
{context if context else "(no existing code - create from scratch)"}

Requirements:
1. Use create_python_file to create the file at path: {target_file}
2. Include all necessary imports
3. Write complete, working code
4. Add proper docstrings and type hints
5. Follow architectural patterns from ARCHITECTURE document
6. Consider guidance from TERTIARY_OBJECTIVES

Use create_python_file NOW to create {target_file}."""
```

## Testing Strategy

After updating prompts:
1. Test each phase with IPC-aware prompts
2. Verify phases reference strategic documents
3. Confirm communication messages are clear
4. Ensure no confusion about automatic vs manual operations

## Success Criteria

- [ ] Coding prompt includes IPC guidance
- [ ] QA prompt includes IPC guidance
- [ ] Debugging prompt includes IPC guidance
- [ ] Prompts explain document availability
- [ ] Prompts clarify automatic communication
- [ ] Prompts encourage strategic document usage
- [ ] Prompts remain concise and clear

---
**Status**: Ready for Implementation
**Approach**: Hybrid (brief overview + integrated references)
