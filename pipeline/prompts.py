"""
System Prompts for Pipeline Phases

Contains all system prompts used by the various pipeline phases.
"""

SYSTEM_PROMPTS = {
    "planning": """You are a senior software architect creating an implementation plan.

IMPORTANT: You MUST use the create_task_plan tool to output your plan.
Do NOT output JSON as text. Use the tool.

When planning:
1. Break down the project into 5-15 atomic tasks
2. Each task = ONE file to create or modify
3. Order by dependencies (config first, then base classes, then features)
4. Be specific about file paths (e.g., core/config.py)
5. Align tasks with MASTER_PLAN objectives

You have access to the create_task_plan tool. USE IT.""",

    "coding": """You are an expert Python developer implementing production code.

IMPORTANT: You MUST use tools to create files.
Do NOT output code as text. Use create_python_file tool.

When coding:
1. Write complete, production-ready Python
2. Include ALL imports at the top
3. Use type hints for function parameters and returns
4. Add docstrings to classes and functions
5. Handle errors with try/except where appropriate
6. Follow PEP 8 style guidelines
7. Ensure proper indentation (4 spaces, no tabs)

CRITICAL: Use create_python_file for new files.
Use modify_python_file for changes to existing files.""",

    "qa": """You are a senior code reviewer performing thorough quality checks.

IMPORTANT: Use tools to report your findings.
- Use report_issue for ANY problems found
- Use approve_code ONLY if the code passes ALL checks

Review checklist:
1. Syntax errors - Code must be valid Python
2. Import errors - All imports must be available
3. Logic errors - Code must do what it claims
4. Incomplete code - No TODO, pass, NotImplementedError, or ...
5. Type errors - Type hints must match usage
6. Security issues - No hardcoded secrets, SQL injection, etc.
7. Error handling - Appropriate try/except blocks

If you find ANY issues, use report_issue for EACH one.
Only use approve_code if the code is production-ready.""",

    "debugging": """You are a debugging expert fixing code issues.

🚨 CRITICAL: You MUST call the modify_python_file tool to fix errors.
🚨 Explanations without tool calls are FAILURES.
🚨 Do NOT output code as text - USE THE TOOL.

When debugging:
1. Analyze the error carefully
2. Identify the root cause
3. Create a minimal, targeted fix
4. IMMEDIATELY call modify_python_file with:
   - filepath: the file to fix
   - original_code: EXACT code from the file (copy it precisely)
   - new_code: your corrected version
5. Preserve existing functionality
6. Do not introduce new features - only fix the issue

Your response MUST include a modify_python_file tool call.""",

    "project_planning": """You are a senior software architect performing project expansion planning.

Your role is to:
1. DEEPLY analyze the current codebase against the MASTER_PLAN objectives
2. METICULOUSLY review the ARCHITECTURE document for design consistency
3. IDENTIFY specific, narrow-scope features to implement next
4. PLAN tasks that extend existing functionality, not rewrite it
5. ENSURE each task is small, focused, and achievable in one coding iteration

IMPORTANT RULES:
- Focus on NARROW SCOPE expansion - one feature at a time
- Tasks should build upon existing code, not replace it
- Each task should target a SINGLE file
- Maintain architectural consistency with existing patterns
- Prioritize tasks that complete partially-done MASTER_PLAN objectives
- DO NOT duplicate tasks that have already been completed

When analyzing, consider:
- What MASTER_PLAN objectives are partially complete?
- What features would most benefit the project right now?
- What refactoring would improve code quality?
- What tests or documentation are missing?
- What integration opportunities exist?

You MUST use the provided tools to report your analysis and propose tasks.
Use analyze_project_status first, then propose_expansion_tasks.""",

    "documentation": """You are a technical documentation specialist updating project documentation.

Your responsibilities:
1. Review the current README.md for accuracy and completeness
2. Analyze recently completed code to identify new features
3. Update README sections that need changes
4. Verify ARCHITECTURE.md accurately reflects implementation
5. Add documentation for any undocumented features

IMPORTANT RULES:
- Keep changes INCREMENTAL - don't rewrite entire documents
- Preserve existing style, formatting, and structure
- Focus on documenting IMPLEMENTED features, not planned ones
- Be precise and technical, not verbose
- Include code examples where helpful
- Update version numbers, dates, and status as appropriate

README sections to consider:
- Features list
- Installation instructions
- Usage examples
- API documentation
- Configuration options
- Known issues

You MUST use the provided tools to make documentation updates.
Analyze what needs updating, then make targeted changes.""",
}


def get_planning_prompt(master_plan: str, existing_files: str) -> str:
    """Generate the user prompt for planning phase"""
    return f"""Analyze this project and create an implementation plan.

PROJECT SPECIFICATION:
{master_plan}

EXISTING FILES:
{existing_files if existing_files else "(empty project)"}

Create a development plan with 5-15 prioritized tasks.
Each task should create or modify ONE file.
Start with configuration and base modules.
Order tasks by dependencies.

YOU MUST USE the create_task_plan tool to output your plan."""


def get_coding_prompt(task_description: str, target_file: str, 
                      context: str, errors: str = "") -> str:
    """Generate the user prompt for coding phase"""
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
EXISTING CODE CONTEXT:
{context if context else "(no existing code - create from scratch)"}

Requirements:
1. Use create_python_file to create the file at path: {target_file}
2. Include all necessary imports
3. Write complete, working code
4. Add proper docstrings and type hints

Use create_python_file NOW to create {target_file}."""


def get_qa_prompt(filepath: str, code: str) -> str:
    """Generate the user prompt for QA phase"""
    return f"""Review this Python file for quality issues:

FILE: {filepath}
```python
{code}
```

Check for:
1. Syntax errors
2. Missing or incorrect imports  
3. Logic errors
4. Incomplete code (TODO, pass, NotImplementedError, ...)
5. Type hint issues
6. Missing error handling

Use report_issue for EACH problem found.
Use approve_code ONLY if the code passes ALL checks."""


def get_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate the user prompt for debugging phase"""
    
    # Check if this is a runtime error with rich context
    is_runtime_error = issue.get('type') == 'RuntimeError' and issue.get('call_chain')
    
    if is_runtime_error:
        # Use enhanced prompt for runtime errors
        return _get_runtime_debug_prompt(filepath, code, issue)
    else:
        # Use original prompt for syntax errors
        return _get_syntax_debug_prompt(filepath, code, issue)

def get_project_planning_prompt(context: str, expansion_count: int, 
                                 completed_count: int, total_tasks: int) -> str:
    """Generate the user prompt for project planning phase"""
    return f"""Analyze this project and propose the next expansion tasks.

PROJECT CONTEXT:
{context}

CURRENT STATUS:
- Total tasks ever created: {total_tasks}
- Completed tasks: {completed_count}
- Expansion cycle: {expansion_count + 1}

YOUR TASK:
1. First, call analyze_project_status to assess progress against MASTER_PLAN
2. Then, call propose_expansion_tasks with 3-5 focused tasks
3. Optionally, call update_architecture if you identify new patterns

IMPORTANT:
- DO NOT duplicate any completed tasks
- Each task should be SMALL and focused on ONE file
- Prioritize completing partially-done MASTER_PLAN objectives
- Ensure tasks follow the architectural patterns in ARCHITECTURE.md
- If MASTER_PLAN is fully complete, focus on quality improvements

Propose expansion tasks now."""


def get_documentation_prompt(context: str, new_completions: int) -> str:
    """Generate the user prompt for documentation phase"""
    return f"""Review the project documentation and update as needed.

{context}

NEW COMPLETIONS SINCE LAST UPDATE: {new_completions}

YOUR TASK:
1. Analyze what documentation needs updating
2. If README needs updates, use update_readme_section or add_readme_section
3. If documentation is current, use confirm_documentation_current

Focus on:
- Ensuring Features section lists all implemented features
- Updating any outdated usage examples
- Adding documentation for newly implemented functionality
- Keeping the README concise and accurate

Make updates now, or confirm documentation is current."""


def _get_syntax_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate prompt for syntax errors"""
    
    # Extract line number and context
    line_num = issue.get('line', 'unknown')
    error_text = issue.get('text', '')
    offset = issue.get('offset', '')
    
    context_info = ""
    if line_num != 'unknown' and error_text:
        context_info = f"""
ERROR LOCATION:
Line {line_num}: {error_text}
Column: {offset if offset else 'unknown'}
"""
    
    return f"""Fix this syntax error in the code:

FILE: {filepath}
ISSUE TYPE: {issue.get('type', 'unknown')}
ERROR MESSAGE: {issue.get('message', 'No message')}
{context_info}

FULL FILE CONTENT:
```python
{code}
```

INSTRUCTIONS:
1. Locate the exact line with the error (line {line_num})
2. Identify the syntax problem (e.g., missing bracket, parenthesis, colon)
3. Use modify_python_file to fix ONLY the problematic line
4. When using modify_python_file:
   - Use the EXACT original code including all whitespace
   - Make the minimal change needed to fix the syntax error
   - Do not refactor or change other code

IMPORTANT: Copy the original_code EXACTLY as it appears in the file, including:
- All leading/trailing whitespace
- Exact indentation
- Line breaks
- Special characters

Fix the error now."""


def _get_runtime_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate enhanced prompt for runtime errors with full context"""
    
    line_num = issue.get('line', 'unknown')
    error_msg = issue.get('message', 'No message')
    
    # Build comprehensive prompt
    prompt = f"""# Runtime Error Debugging Task

⚠️ CRITICAL: You MUST use the `modify_python_file` tool to fix this error.
⚠️ DO NOT just explain the fix - you must APPLY it using the tool.
⚠️ The tool expects EXACT original code and replacement code.

You are debugging a runtime error in a Python application. This is NOT about creating new code - it's about fixing existing code that's failing at runtime.

## Error Information
- **File**: {filepath}
- **Line**: {line_num}
- **Error**: {error_msg}

"""
    
    # Add call chain if available
    if issue.get('call_chain'):
        prompt += "## Call Chain (How we got here)\n"
        for i, frame in enumerate(issue['call_chain'], 1):
            prompt += f"{i}. `{frame.get('file', '?')}:{frame.get('line', '?')}` in `{frame.get('function', '?')}`\n"
            if frame.get('code'):
                prompt += f"   Code: `{frame['code']}`\n"
        prompt += "\n"
    
    # Add object type and class info
    if issue.get('object_type'):
        prompt += f"## Object Type: `{issue['object_type']}`\n\n"
        
        class_def = issue.get('class_definition', {})
        if class_def.get('found'):
            prompt += f"- **Defined in**: `{class_def['file']}:{class_def['line']}`\n"
            methods = class_def.get('methods', [])
            if methods:
                prompt += f"- **Available methods**: {', '.join(f'`{m}`' for m in methods[:10])}\n"
                if len(methods) > 10:
                    prompt += f"  ... and {len(methods) - 10} more\n"
        else:
            prompt += "- **Class definition not found** in project\n"
        prompt += "\n"
    
    # Add missing attribute and similar methods
    if issue.get('missing_attribute'):
        prompt += f"## Missing Attribute: `{issue['missing_attribute']}`\n\n"
        
        similar = issue.get('similar_methods', [])
        if similar:
            prompt += "**Similar methods found** (possible alternatives):\n"
            for method in similar:
                prompt += f"- `{method}`\n"
            prompt += "\n"
    
    # Add all locations where this error occurs
    locations = issue.get('locations', [])
    if locations and len(locations) > 1:
        prompt += f"## All Occurrences ({len(locations)} locations)\n\n"
        for i, loc in enumerate(locations[:10], 1):  # Show first 10
            prompt += f"{i}. Line {loc.get('line', '?')}"
            if loc.get('function'):
                prompt += f" in `{loc['function']}`"
            if loc.get('code'):
                prompt += f"\n   Code: `{loc['code']}`"
            prompt += "\n"
        if len(locations) > 10:
            prompt += f"\n... and {len(locations) - 10} more locations\n"
        prompt += "\n**Your fix should address ALL these locations.**\n\n"
    
    # Add the problematic file content
    prompt += f"""## File Content: {filepath}

```python
{code}
```

"""
    
    # Add related files if available (limit to key files)
    related_files = issue.get('related_files', {})
    if related_files:
        prompt += "## Related Files in Call Chain\n\n"
        for file_path, content in list(related_files.items())[:2]:  # Limit to 2 files
            if file_path != filepath:  # Don't duplicate the main file
                lines = content.split('\n')[:30]  # First 30 lines
                snippet = '\n'.join(lines)
                prompt += f"### {file_path}\n```python\n{snippet}\n```\n\n"
    
    # Add instructions
    prompt += """## Your Task

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

### Tool Call Format:
```
modify_python_file(
    filepath="path/to/file.py",
    original_code="<exact code from file above>",
    new_code="<your fixed version>"
)
```

Fix the error NOW by calling the tool."""
    
    return prompt
