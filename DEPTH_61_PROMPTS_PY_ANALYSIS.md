# Depth-61 Analysis: pipeline/prompts.py

**Analysis Date**: 2024-01-XX  
**File Size**: 923 lines  
**Total Functions**: 9  
**Max Complexity**: 20 (_get_runtime_debug_prompt)  
**Average Complexity**: 3.56  

---

## EXECUTIVE SUMMARY

### Overall Assessment: ⚠️ MODERATE COMPLEXITY - MINOR REFACTORING RECOMMENDED

**Key Findings**:
1. **_get_runtime_debug_prompt() has complexity 20** ⚠️ - Slightly high, could be improved
2. **8 out of 9 functions are well-implemented** (complexity ≤10) ✅
3. **Primarily a prompt generation file** - String building with conditional logic
4. **Good separation of concerns** - Each phase has dedicated prompt function
5. **One function needs minor refactoring** - Extract helper methods
6. **Overall good quality** - Clean structure, maintainable

### Complexity Breakdown
- **🔴 CRITICAL (>30)**: 0 functions
- **⚠️ HIGH (11-20)**: 1 function (_get_runtime_debug_prompt - 20)
- **✅ GOOD (≤10)**: 8 functions

---

## FILE STRUCTURE

### Purpose
Centralized prompt generation for all pipeline phases. Provides context-aware prompts for LLM interactions.

### Functions Overview

| Function | Lines | Complexity | Status | Purpose |
|----------|-------|------------|--------|---------|
| `get_planning_prompt` | ~50 | 1 | ✅ GOOD | Generate planning prompts |
| `get_coding_prompt` | ~100 | 2 | ✅ GOOD | Generate coding prompts |
| `get_qa_prompt` | ~150 | 1 | ✅ GOOD | Generate QA prompts |
| `get_debug_prompt` | ~50 | 2 | ✅ GOOD | Generate debug prompts |
| `get_project_planning_prompt` | ~50 | 1 | ✅ GOOD | Generate project planning prompts |
| `get_documentation_prompt` | ~100 | 1 | ✅ GOOD | Generate documentation prompts |
| `_get_syntax_debug_prompt` | ~100 | 3 | ✅ GOOD | Generate syntax error prompts |
| `_get_runtime_debug_prompt` | ~200 | 20 | ⚠️ HIGH | Generate runtime error prompts |
| `get_modification_decision_prompt` | ~50 | 1 | ✅ GOOD | Generate modification decision prompts |

---

## CRITICAL ANALYSIS

### Issue #1: _get_runtime_debug_prompt() Complexity (20) ⚠️

**Location**: Lines 662-850 (~188 lines)

**Problem**: 
- Single function handling too many responsibilities
- Multiple conditional sections for different error contexts
- Inline string building for various error types
- Complex prompt assembly logic

**Responsibilities Identified**:
1. Extract basic error info (line, message)
2. Build base prompt
3. Add call chain section (if available)
4. Add object type section (if available)
5. Add class definition info (if available)
6. Add missing attribute section (if available)
7. Add similar methods section (if available)
8. Add all error locations section (if available)
9. Add file content section
10. Add critical debugging instructions
11. Add related files section (if available)
12. Add task instructions
13. Add tool call format examples
14. Return assembled prompt

**Complexity Breakdown**:
- Base: 1
- if issue.get('call_chain'): +1
- for i, frame in enumerate(...): +1
- if frame.get('code'): +1
- if issue.get('object_type'): +1
- if class_def.get('found'): +1
- if methods: +1
- if len(methods) > 10: +1
- if issue.get('missing_attribute'): +1
- if similar: +1
- if locations and len(locations) > 1: +1
- for i, loc in enumerate(...): +1
- if loc.get('function'): +1
- if loc.get('code'): +1
- if len(locations) > 10: +1
- if related_files: +1
- for file_path, content in ...: +1
- if file_path != filepath: +1
- **Total**: 20 ⚠️

**Recommended Refactoring**:

```python
def _get_runtime_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate enhanced prompt for runtime errors with full context"""
    
    # Build prompt sections
    sections = []
    
    # Base error info
    sections.append(self._build_base_error_section(filepath, issue))
    
    # Optional sections based on available data
    if issue.get('call_chain'):
        sections.append(self._build_call_chain_section(issue))
    
    if issue.get('object_type'):
        sections.append(self._build_object_type_section(issue))
    
    if issue.get('missing_attribute'):
        sections.append(self._build_missing_attribute_section(issue))
    
    if issue.get('locations') and len(issue['locations']) > 1:
        sections.append(self._build_locations_section(issue))
    
    # File content
    sections.append(self._build_file_content_section(filepath, code))
    
    # Related files
    if issue.get('related_files'):
        sections.append(self._build_related_files_section(issue, filepath))
    
    # Instructions
    sections.append(self._build_instructions_section())
    
    return '\n\n'.join(sections)

def _build_base_error_section(self, filepath: str, issue: dict) -> str:
    """Build base error information section"""
    line_num = issue.get('line', 'unknown')
    error_msg = issue.get('message', 'No message')
    
    return f"""
FIX THIS ERROR IN {filepath}

Error Line: {line_num}

ERROR:
{error_msg}

THE FILE CONTENT IS BELOW. 

IMPORTANT: If an ERROR-SPECIFIC STRATEGY appears above, you MUST follow it first.
Otherwise, find line {line_num}, understand the error, and call modify_python_file to fix it.
"""

def _build_call_chain_section(self, issue: dict) -> str:
    """Build call chain section"""
    lines = ["## Call Chain (How we got here)\n"]
    
    for i, frame in enumerate(issue['call_chain'], 1):
        lines.append(f"{i}. `{frame.get('file', '?')}:{frame.get('line', '?')}` in `{frame.get('function', '?')}`")
        if frame.get('code'):
            lines.append(f"   Code: `{frame['code']}`")
    
    return '\n'.join(lines)

def _build_object_type_section(self, issue: dict) -> str:
    """Build object type and class info section"""
    lines = [f"## Object Type: `{issue['object_type']}`\n"]
    
    class_def = issue.get('class_definition', {})
    if class_def.get('found'):
        lines.append(f"- **Defined in**: `{class_def['file']}:{class_def['line']}`")
        
        methods = class_def.get('methods', [])
        if methods:
            method_list = ', '.join(f'`{m}`' for m in methods[:10])
            lines.append(f"- **Available methods**: {method_list}")
            if len(methods) > 10:
                lines.append(f"  ... and {len(methods) - 10} more")
    else:
        lines.append("- **Class definition not found** in project")
    
    return '\n'.join(lines)

def _build_missing_attribute_section(self, issue: dict) -> str:
    """Build missing attribute section"""
    lines = [f"## Missing Attribute: `{issue['missing_attribute']}`\n"]
    
    similar = issue.get('similar_methods', [])
    if similar:
        lines.append("**Similar methods found** (possible alternatives):")
        for method in similar:
            lines.append(f"- `{method}`")
    
    return '\n'.join(lines)

def _build_locations_section(self, issue: dict) -> str:
    """Build all error locations section"""
    locations = issue['locations']
    lines = [f"## All Occurrences ({len(locations)} locations)\n"]
    
    for i, loc in enumerate(locations[:10], 1):
        line = f"{i}. Line {loc.get('line', '?')}"
        if loc.get('function'):
            line += f" in `{loc['function']}`"
        if loc.get('code'):
            line += f"\n   Code: `{loc['code']}`"
        lines.append(line)
    
    if len(locations) > 10:
        lines.append(f"\n... and {len(locations) - 10} more locations")
    
    lines.append("\n**Your fix should address ALL these locations.**")
    
    return '\n'.join(lines)

def _build_file_content_section(self, filepath: str, code: str) -> str:
    """Build file content section with debugging instructions"""
    return f"""## File Content: {filepath}

```python
{code}
```

## ⚠️ CRITICAL DEBUGGING INSTRUCTIONS ⚠️

**STEP 1: VALIDATE FUNCTION PARAMETERS FIRST**
If you're modifying a function CALL, use get_function_signature to verify what parameters it accepts.
Example: If fixing JobExecutor(...), first call get_function_signature to see what __init__ accepts.

**STEP 2: READ THE FILE IF NEEDED**
Use read_file tool to see the EXACT code with proper indentation (if not already provided).

**STEP 3: USE A LARGER CODE BLOCK (5-10 lines)**
DO NOT replace just one line. Replace a block that includes surrounding context.

❌ WRONG: original_code = "curses.cbreak()"
✅ CORRECT: original_code with 5-10 lines including context and indentation

**STEP 4: MATCH INDENTATION EXACTLY**
Count the spaces in the file. Match them exactly in your replacement.

**STEP 5: VERIFY YOUR FIX WON'T INTRODUCE NEW ERRORS**
- If adding parameters to a function call, verify they exist in the signature
- If removing parameters, ensure they're not required
- Use validate_function_call to check before applying the fix
"""

def _build_related_files_section(self, issue: dict, filepath: str) -> str:
    """Build related files section"""
    related_files = issue['related_files']
    lines = ["## Related Files in Call Chain\n"]
    
    for file_path, content in list(related_files.items())[:2]:
        if file_path != filepath:
            snippet_lines = content.split('\n')[:30]
            snippet = '\n'.join(snippet_lines)
            lines.append(f"### {file_path}\n```python\n{snippet}\n```\n")
    
    return '\n'.join(lines)

def _build_instructions_section(self) -> str:
    """Build task instructions section"""
    return """## Your Task

Analyze this runtime error and determine the best fix:

### Possible Scenarios:

1. **Method was renamed or doesn't exist**
   - Check if a similar method exists (see "Similar methods" above)
   - Update the calling code to use the correct method name
   - Use `modify_python_file` to fix the call

2. **Method is missing and needs to be created**
   - Determine what the method should do based on usage
   - Create the method in the target class
   - Use `modify_python_file` to add the method

3. **Wrong object type**
   - The object might be the wrong type
   - Check where the object is created/assigned
   - Fix the object creation or type

4. **Import or initialization issue**
   - The class might not be imported correctly
   - Check imports and fix if needed

### Instructions:

1. **Analyze the full context** - Look at the call chain, available methods, and related files
2. **Determine the root cause** - Is it a renamed method? Missing method? Wrong object?
3. **Choose the best fix** - Update calling code OR create missing method OR fix object type
4. **IMMEDIATELY call modify_python_file** - Use EXACT original code from the file above
5. **Explain your reasoning** - Why did you choose this fix?

### CRITICAL REQUIREMENTS:
- You MUST call the `modify_python_file` tool - explanations alone are NOT sufficient
- Copy the EXACT original code from the file content above (including whitespace)
- Provide the corrected replacement code
- Make minimal changes - don't refactor unnecessarily
- This is EXISTING code that's failing - understand what it's trying to do

### Tool Call Format (USE JSON):

**REQUIRED FORMAT - Use this exact JSON structure:**

```json
{
    "name": "modify_python_file",
    "arguments": {
        "filepath": "path/to/file.py",
        "original_code": "exact code from file above",
        "new_code": "your fixed version"
    }
}
```

**IMPORTANT:**
- Use JSON format with "name" and "arguments" fields
- Put the JSON in a ```json code block
- Use regular JSON strings with \\n for newlines (NOT Python triple quotes)
- Make sure all quotes are properly escaped

**Alternative formats also accepted:**
- Python function call: `modify_python_file(filepath="...", original_code="...", new_code="...")`
- But JSON format is PREFERRED

Fix the error NOW by calling the tool."""
```

**Benefits of Refactoring**:
1. **Reduced complexity**: Main method drops from 20 to ~5
2. **Better testability**: Each section builder can be tested independently
3. **Improved readability**: Clear separation of prompt sections
4. **Easier maintenance**: Changes isolated to specific sections
5. **Better reusability**: Section builders can be reused

**Estimated Effort**: 1-2 days (low priority)

---

## INTEGRATION ANALYSIS

### Dependencies

**External Libraries**: None

**Internal Modules**: None (standalone prompt generation)

### Integration Points

1. **Used By**:
   - All pipeline phases (planning, coding, qa, debugging, documentation, project_planning)
   - Phase implementations call prompt functions to get context-aware prompts

2. **Call Relationships**:
   - **Called By**: Phase implementations
   - **Calls To**: None (pure string generation)

---

## DESIGN PATTERNS

### 1. Factory Pattern (Implicit) ✅
- Each function is a factory for phase-specific prompts
- Generates prompts based on context
- Clean separation by phase

### 2. Template Pattern ✅
- Prompts follow consistent structure
- Common sections across prompts
- Phase-specific customization

### 3. Builder Pattern (Implicit) ✅
- Prompts built incrementally
- Conditional sections added based on context
- Final assembly of complete prompt

---

## STRENGTHS ✅

1. **Clear Organization**
   - One function per phase
   - Consistent naming conventions
   - Easy to find prompts

2. **Context-Aware Prompts**
   - Prompts adapt to available information
   - Conditional sections based on context
   - Rich debugging information

3. **Comprehensive Instructions**
   - Detailed task descriptions
   - Step-by-step guidance
   - Tool call format examples

4. **Maintainability**
   - Easy to update prompts
   - Clear structure
   - Well-commented

5. **Good Separation**
   - Each phase has dedicated function
   - Private helpers for complex prompts
   - Clean interfaces

---

## AREAS FOR IMPROVEMENT ⚠️

1. **_get_runtime_debug_prompt() Complexity**
   - Complexity 20 is slightly high
   - Could be split into section builders
   - Would improve testability

2. **String Concatenation**
   - Some long string building
   - Could use template engine
   - Would improve readability

3. **Duplication**
   - Some common patterns repeated
   - Could extract common sections
   - Would reduce duplication

---

## TESTING RECOMMENDATIONS

### Unit Tests Needed

1. **Prompt Generation Tests**
   - Test each prompt function
   - Verify output format
   - Test with various contexts

2. **Section Builder Tests** (after refactoring)
   - Test each section builder
   - Verify conditional logic
   - Test edge cases

3. **Integration Tests**
   - Test prompts with real phase data
   - Verify LLM can parse prompts
   - Test tool call extraction

---

## PERFORMANCE CONSIDERATIONS

### Current Performance: ✅ GOOD

- **No performance issues** - String generation is fast
- **Minimal memory usage** - Strings are temporary
- **No bottlenecks** - Simple operations

---

## SECURITY CONSIDERATIONS

### Current Security: ✅ GOOD

**Strengths**:
1. **No user input** - Prompts generated from internal data
2. **No injection risks** - Controlled string building
3. **No sensitive data** - Public code and error messages

**No security issues identified**

---

## CODE QUALITY METRICS

### Strengths ✅

1. **Good documentation** - Clear docstrings
2. **Consistent structure** - Uniform prompt format
3. **Comprehensive prompts** - Detailed instructions
4. **Low average complexity** - 3.56 average
5. **8 out of 9 functions well-implemented** - 89% good

### Metrics

- **Lines of Code**: 923
- **Functions**: 9
- **Max Complexity**: 20
- **Average Complexity**: 3.56
- **Well-Implemented**: 8/9 (89%)

---

## REFACTORING PRIORITY

### Priority 1: LOW-MEDIUM (1-2 days effort)
**Refactor _get_runtime_debug_prompt()** - Complexity 20 → ~5
- Extract section builder methods
- Improve testability
- Reduce complexity

### Priority 2: OPTIONAL (ongoing)
**Add comprehensive tests**
- Unit tests for all functions
- Integration tests with phases
- Prompt validation tests

---

## COMPARISON WITH OTHER FILES

### This File vs Others

**prompts.py**:
- Max Complexity: 20 ⚠️
- Status: MODERATE
- Type: Prompt generation file
- Refactoring Needed: MINOR (1 function)

**Similar Files**:
- tools.py: Max Complexity 4 ✅ (data definition)
- coding.py: Max Complexity 20 ✅ (acceptable)
- documentation.py: Max Complexity 25 ✅ (acceptable)

**Assessment**: This file is **mostly well-implemented** with one function needing minor refactoring.

---

## CONCLUSION

### Overall Assessment: ⚠️ MODERATE COMPLEXITY - MINOR REFACTORING RECOMMENDED

**Key Points**:
1. **Mostly well-implemented** - 8 out of 9 functions are good
2. **One function needs minor refactoring** - _get_runtime_debug_prompt (complexity 20)
3. **Good prompt quality** - Comprehensive, context-aware prompts
4. **Easy to maintain** - Clear structure, good organization
5. **Low priority refactoring** - Not urgent, but would improve quality

**Estimated Refactoring Effort**: 1-2 days (low priority)

**Risk Level**: LOW

**Recommendation**: 
- **Minor refactoring recommended** - Extract section builders from _get_runtime_debug_prompt()
- **Not urgent** - Can be done during next maintenance cycle
- **Low priority** - Focus on higher complexity issues first
- Consider this a **low-priority** refactoring task

---

**Analysis Complete** ✅  
**Next File**: Continue with remaining 159 files (90.3% remaining)

---

## LESSONS LEARNED

This file demonstrates:

1. **Good Prompt Engineering**
   - Context-aware prompts
   - Detailed instructions
   - Tool call examples

2. **Acceptable Complexity**
   - Most functions simple
   - One function slightly high
   - Overall good quality

3. **Maintainable Structure**
   - Clear organization
   - Easy to update
   - Good separation

**This file is mostly well-implemented with minor room for improvement.**