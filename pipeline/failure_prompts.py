"""
Specialized Prompts for Different Failure Types

Provides focused, detailed prompts for each type of failure scenario.
"""

from typing import Dict


def get_code_not_found_prompt(context: Dict) -> str:
    """Prompt for when original code is not found in file"""
    
    error_msg = context.get('error_message', '')
    suggestion_section = ""
    if "Did you mean" in error_msg:
        # Extract the suggestion
        suggestion_section = f"""
## ⚠️ SYSTEM SUGGESTION (USE THIS!)
The system found similar code in the file:
{error_msg.split('Did you mean:')[1] if 'Did you mean:' in error_msg else ''}

**CRITICAL:** Use the code shown above as your `original_code`. 
This is the ACTUAL code in the file with EXACT indentation.
"""
    
    return f"""# CODE NOT FOUND - Specialized Analysis

## Problem
The code you're trying to replace was not found in the file.

## Context
- **File:** {context.get('filepath')}
- **Error:** {error_msg}
- **Attempted to find:** 
```python
{context.get('intended_original', 'N/A')}
```
{suggestion_section}

## Current File Content
```python
{context.get('file_content', 'N/A')}
```

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Specialist Analysis Required

### 1. Whitespace Analysis
Use tools to examine:
- Exact whitespace in the file (tabs vs spaces)
- Indentation levels
- Line endings (CRLF vs LF)
- Hidden characters

**Tool calls needed:**
- `read_file` with raw mode to see exact bytes
- `execute_command` with `cat -A` to show all characters
- `execute_command` with `file` to check line endings

### 2. Pattern Matching
Find similar code:
- Search for partial matches
- Look for the same logic with different formatting
- Check if code was already modified
- Find surrounding context

**Tool calls needed:**
- `search_code` for similar patterns
- `list_directory` to check file structure
- `read_file` for related files

### 3. Code Evolution
Check if code changed:
- Was this code already fixed?
- Did a previous attempt modify it?
- Is there a different version?

**Tool calls needed:**
- Compare file snapshots from different attempts
- Check patch history

## Your Task
1. **FIRST: Read the file** - Use read_file to see the actual code with proper indentation
2. **Use tools extensively** - Don't guess, investigate with cat -A, grep, etc.
3. **Find the actual code** - It must be there somewhere with its exact indentation
4. **Identify the mismatch** - What's different? Indentation? Whitespace?
5. **Provide exact solution** - Show the correct code WITH PROPER INDENTATION

## CRITICAL: Indentation Matching
- The file uses a specific indentation (spaces or tabs)
- You MUST match this indentation exactly
- Use read_file to see the surrounding code
- Copy the indentation from the actual file
- Include enough context (3-5 lines) to ensure proper indentation

## Output Requirements
- **Findings:** List all discoveries with evidence
- **Exact Code:** Provide the EXACT code from the file (copy-paste with indentation)
- **Recommendations:** Specific steps to fix with proper indentation
- **Tool Calls:** Make all necessary tool calls to investigate
"""


def get_syntax_error_prompt(context: Dict) -> str:
    """Prompt for syntax errors in replacement code"""
    
    return f"""# SYNTAX ERROR - Specialized Analysis

## Problem
The replacement code has a syntax error.

## Error Details
```
{context.get('error_message', 'N/A')}
```

## Problematic Code
```python
{context.get('replacement_code', 'N/A')}
```

## Context
- **File:** {context.get('filepath')}
- **Line:** {context.get('line', 'N/A')}

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Specialist Analysis Required

### 1. Syntax Validation
Check for common issues:
- Missing colons after if/for/while/def/class
- Unmatched brackets: (), [], {{}}
- Unmatched quotes: ', "
- Invalid indentation
- Invalid Python keywords

**Tool calls needed:**
- `execute_command` with `python -m py_compile` to check syntax
- `execute_command` with `python -m ast` to parse AST
- Test the code in isolation

### 2. Context Analysis
Understand the surrounding code:
- What's the indentation level?
- What's the code structure?
- Are there any special requirements?

**Tool calls needed:**
- `read_file` to see surrounding code
- `search_code` to find similar working examples

### 3. Incremental Testing
Test the fix:
- Break down into smaller pieces
- Test each piece separately
- Build up to full solution

**Tool calls needed:**
- `execute_command` to test code snippets
- Create temporary test files

## Your Task
1. **Identify the exact syntax error** - Line and character
2. **Understand why it's wrong** - What rule is violated?
3. **Provide corrected code** - Valid Python syntax
4. **Test the fix** - Verify it works

## Output Requirements
- **Findings:** Specific syntax errors found
- **Corrected Code:** Valid Python code
- **Explanation:** Why the original was wrong
- **Verification:** Proof that fix works
"""


def get_indentation_error_prompt(context: Dict) -> str:
    """Prompt for indentation-related errors"""
    
    return f"""# INDENTATION ERROR - Specialized Analysis

## Problem
Indentation mismatch between original and replacement code.

## Context
- **File:** {context.get('filepath')}
- **Original indentation:** {context.get('original_indent', 'Unknown')}
- **Replacement indentation:** {context.get('replacement_indent', 'Unknown')}

## Original Code
```python
{context.get('intended_original', 'N/A')}
```

## Replacement Code
```python
{context.get('replacement_code', 'N/A')}
```

## File Context
```python
{context.get('file_context', 'N/A')}
```

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Specialist Analysis Required

### 1. Indentation Detection
Analyze exact indentation:
- Count spaces/tabs
- Check consistency
- Identify the pattern

**Tool calls needed:**
- `execute_command` with `cat -A` to see tabs/spaces
- `execute_command` with `expand -t 4` to convert tabs
- `read_file` to examine raw content

### 2. Context Matching
Match surrounding code:
- What indentation do neighbors use?
- Is there a consistent pattern?
- Are there mixed tabs/spaces?

**Tool calls needed:**
- `read_file` with context lines
- `search_code` for similar code blocks
- Check file-wide indentation style

### 3. Correction Strategy
Determine the fix:
- Should we use tabs or spaces?
- How many spaces per level?
- Do we need to adjust multiple lines?

**Tool calls needed:**
- Test different indentation levels
- Verify with syntax checker

## Your Task
1. **Detect exact indentation** - Tabs? Spaces? How many?
2. **Match the file's style** - Be consistent
3. **Provide correctly indented code** - Exact spacing
4. **Verify it works** - Test the indentation

## Output Requirements
- **Findings:** Exact indentation analysis
- **Corrected Code:** Properly indented
- **Indentation Guide:** "Use X spaces" or "Use tabs"
- **Verification:** Proof of correct indentation
"""


def get_verification_failure_prompt(context: Dict) -> str:
    """Prompt for post-modification verification failures"""
    
    return f"""# VERIFICATION FAILURE - Specialized Analysis

## Problem
The modification was applied but failed verification checks.

## Verification Errors
{context.get('verification_errors', 'N/A')}

## Context
- **File:** {context.get('filepath')}
- **Intended change:** Applied
- **Verification:** Failed

## What Was Intended
```python
{context.get('intended_original', 'N/A')}
```
↓
```python
{context.get('replacement_code', 'N/A')}
```

## What Actually Happened
```python
{context.get('actual_content', 'N/A')}
```

## Diff (Intended vs Actual)
```diff
{context.get('diff', 'N/A')}
```

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Specialist Analysis Required

### 1. Change Verification
Compare intended vs actual:
- Did the change apply correctly?
- Is the original code still there?
- Is the new code present?
- Are there unexpected changes?

**Tool calls needed:**
- `read_file` to see current state
- Compare with previous snapshots
- Generate diffs

### 2. Side Effects Analysis
Check for unintended effects:
- Did we break imports?
- Did we affect other code?
- Are there syntax errors?
- Are there logical errors?

**Tool calls needed:**
- `execute_command` with syntax checker
- `search_code` for affected references
- Test imports

### 3. Root Cause Investigation
Why did verification fail?
- What check failed?
- What was expected?
- What was found?
- Why the discrepancy?

**Tool calls needed:**
- Re-run verification checks
- Examine verification logic
- Test specific conditions

## Your Task
1. **Understand what went wrong** - Why did verification fail?
2. **Identify the discrepancy** - Intended vs actual
3. **Determine the fix** - How to correct it?
4. **Verify the solution** - Will it pass checks?

## Output Requirements
- **Findings:** What went wrong and why
- **Root Cause:** The underlying issue
- **Corrected Approach:** How to fix it properly
- **Verification Plan:** How to ensure it works
"""


def get_import_error_prompt(context: Dict) -> str:
    """Prompt for import-related errors"""
    
    return f"""# IMPORT ERROR - Specialized Analysis

## Problem
Import-related error in the code.

## Error Details
```
{context.get('error_message', 'N/A')}
```

## Context
- **File:** {context.get('filepath')}
- **Import:** {context.get('import_name', 'N/A')}

## Code Context
```python
{context.get('code_context', 'N/A')}
```

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Specialist Analysis Required

### 1. Import Availability
Check if import exists:
- Is the module installed?
- Is it in the right location?
- Is the import path correct?

**Tool calls needed:**
- `execute_command` with `python -c "import X"`
- `list_directory` to check file structure
- `search_code` to find the module

### 2. Import Usage
Analyze how it's used:
- What's being imported?
- How is it used in the code?
- Are there alternatives?

**Tool calls needed:**
- `read_file` to see usage
- `search_code` for similar imports
- Check documentation

### 3. Fix Strategy
Determine the solution:
- Add the import?
- Fix the import path?
- Use a different import?
- Install a package?

**Tool calls needed:**
- Test import statements
- Check available modules
- Verify fix works

## Your Task
1. **Identify the import issue** - What's missing or wrong?
2. **Find the correct import** - What should it be?
3. **Provide the fix** - Correct import statement
4. **Verify it works** - Test the import

## Output Requirements
- **Findings:** Import issue details
- **Corrected Import:** Proper import statement
- **Explanation:** Why this import is correct
- **Verification:** Proof it works
"""


def get_generic_failure_prompt(context: Dict) -> str:
    """Generic prompt for unknown failure types"""
    
    return f"""# GENERAL FAILURE ANALYSIS

## Problem
{context.get('error_message', 'Unknown error')}

## Context
- **File:** {context.get('filepath')}
- **Type:** {context.get('failure_type', 'Unknown')}

## What Was Attempted
```python
{context.get('intended_original', 'N/A')}
```
↓
```python
{context.get('replacement_code', 'N/A')}
```

## Current File State
```python
{context.get('file_content', 'N/A')}
```

## Previous Attempts
{context.get('attempt_summary', 'No previous attempts')}

## Comprehensive Analysis Required

### 1. Problem Identification
Understand the issue:
- What exactly failed?
- What was expected?
- What actually happened?
- Why did it fail?

**Tool calls needed:**
- `read_file` to examine current state
- `execute_command` to test hypotheses
- `search_code` to find related code

### 2. Context Gathering
Collect all relevant information:
- File structure
- Related files
- Dependencies
- Environment

**Tool calls needed:**
- `list_directory` for structure
- `read_file` for related files
- `execute_command` for environment checks

### 3. Solution Development
Develop a fix:
- Identify root cause
- Design solution
- Test approach
- Verify fix

**Tool calls needed:**
- Test potential solutions
- Verify with tools
- Check for side effects

## Your Task
1. **Investigate thoroughly** - Use all available tools
2. **Understand the problem** - Get to the root cause
3. **Develop a solution** - Specific and actionable
4. **Verify it works** - Test before recommending

## Output Requirements
- **Findings:** Detailed investigation results
- **Root Cause:** The underlying issue
- **Solution:** Specific fix with code
- **Verification:** Proof it will work
"""


def get_retry_prompt(context: Dict, failure_analysis: Dict) -> str:
    """Prompt for retry attempt with failure analysis"""
    
    failure_type = failure_analysis.get('failure_type', 'UNKNOWN')
    
    # Get specialized prompt based on failure type
    prompt_map = {
        'CODE_NOT_FOUND': get_code_not_found_prompt,
        'SYNTAX_ERROR': get_syntax_error_prompt,
        'INDENTATION_ERROR': get_indentation_error_prompt,
        'VERIFICATION_FAILURE': get_verification_failure_prompt,
        'IMPORT_ERROR': get_import_error_prompt
    }
    
    specialized_prompt = prompt_map.get(failure_type, get_generic_failure_prompt)(context)
    
    # Add failure analysis
    retry_prompt = f"""# RETRY WITH COMPREHENSIVE ANALYSIS

## Previous Attempt Failed
{failure_analysis.get('root_cause', 'Unknown cause')}

## Failure Analysis
{failure_analysis.get('ai_feedback', 'No detailed analysis available')}

---

{specialized_prompt}

---

## Critical Instructions for Retry

1. **READ the failure analysis carefully** - Understand what went wrong
2. **USE TOOLS EXTENSIVELY** - Don't guess, investigate with tool calls
3. **FOLLOW the specialized guidance** - Each failure type has specific steps
4. **VERIFY before applying** - Test your solution
5. **LEARN from previous attempts** - Don't repeat the same mistake

## Collaboration
You're working with specialist agents who have analyzed this issue.
Their findings are in the conversation history. Build on their analysis.

## Success Criteria
- Code modification succeeds
- Verification passes
- No new errors introduced
- Problem is actually solved

Now proceed with your analysis and fix attempt.
"""
    
    return retry_prompt


# Export all prompt functions
__all__ = [
    'get_code_not_found_prompt',
    'get_syntax_error_prompt',
    'get_indentation_error_prompt',
    'get_verification_failure_prompt',
    'get_import_error_prompt',
    'get_generic_failure_prompt',
    'get_retry_prompt'
]