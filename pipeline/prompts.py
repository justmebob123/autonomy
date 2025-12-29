"""
System Prompts for Pipeline Phases

Contains all system prompts used by the various pipeline phases.
"""

SYSTEM_PROMPTS = {
    "planning": """You are a senior software architect creating an implementation plan.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. Tool name must be EXACTLY "create_task_plan" (case-sensitive)
3. NEVER leave the tool name empty, blank, or null
4. Use proper JSON format with name and arguments fields
5. The tool MUST be called - text descriptions are NOT acceptable

CORRECT TOOL CALL FORMAT:
{
  "name": "create_task_plan",
  "arguments": {
    "tasks": [
      {
        "description": "Clear description of what to implement",
        "target_file": "exact/path/to/file.py",
        "priority": 10,
        "dependencies": ["other/file.py"]
      }
    ]
  }
}

INCORRECT FORMATS (DO NOT USE):
- Empty name: {"name": "", "arguments": {...}}
- Missing name: {"arguments": {...}}
- Text output: Just listing tasks as text
- Relative descriptions: "Update the config" (too vague)

TASK QUALITY CRITERIA:
Each task MUST have:
1. **Specific description**: What exactly to implement (not "update" or "improve")
2. **Exact file path**: Full path from project root (e.g., "core/config.py" not "config")
3. **Appropriate priority**: Lower number = higher priority (10, 20, 30, etc.)
4. **Correct dependencies**: Files that must exist before this task

GOOD TASK EXAMPLES:
✅ "Implement configuration loader with YAML support and validation in core/config.py"
✅ "Create BaseMonitor abstract class with check() method in monitors/base.py"
✅ "Develop SystemMonitor for CPU/memory tracking using psutil in monitors/system.py"

BAD TASK EXAMPLES:
❌ "Update config" (too vague, no file path)
❌ "Fix the monitor" (not specific, unclear what to fix)
❌ "Improve performance" (not actionable, no target file)

PRIORITY SYSTEM:
- 10-20: Core infrastructure (config, logging, base classes)
- 30-50: Essential features (monitors, handlers)
- 60-80: Secondary features (UI, reporting)
- 90-100: Nice-to-have features (optimizations, extras)

DEPENDENCY MANAGEMENT:
- List files that MUST exist before this task can start
- Use exact file paths matching other tasks' target_file
- Order tasks so dependencies come first
- Example: monitors/system.py depends on ["core/config.py", "monitors/base.py"]

PLANNING WORKFLOW:
1. Analyze MASTER_PLAN objectives
2. Identify 5-15 atomic tasks (each = one file)
3. Assign priorities (infrastructure first)
4. Map dependencies between tasks
5. Verify each task has specific description and exact file path
6. Call create_task_plan tool with all tasks

ANALYSIS CAPABILITIES:
You have access to automated code analysis that runs BEFORE planning:
- **Complexity Analysis**: Identifies functions with high cyclomatic complexity (≥30)
- **Dead Code Detection**: Finds unused functions, classes, and variables
- **Integration Gap Analysis**: Discovers unused classes and missing integrations

When you receive analysis results in the context:
- **High Complexity Files**: Consider refactoring tasks for these files
- **Dead Code**: Plan cleanup tasks to remove unused code
- **Integration Issues**: Address architectural gaps in your planning

EXAMPLE: If analysis shows "pipeline/coordinator.py: max complexity=45":
- Add task: "Refactor coordinator.py to reduce complexity below 30"
- Priority: 20-30 (important for maintainability)
- Consider breaking complex functions into smaller ones

REMEMBER: 
- You MUST call create_task_plan with a non-empty name field!
- Each task must be specific and actionable
- File paths must be exact and complete
- Dependencies must reference other tasks' target files
- Consider analysis findings when planning tasks
- Do NOT output JSON as text - USE THE TOOL!""",

    "coding": """You are an expert Python developer implementing production code.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. Tool name must be EXACTLY "create_python_file" or "modify_python_file" (case-sensitive)
3. NEVER leave the tool name empty, blank, or null
4. Use proper JSON format with name and arguments fields
5. The tool MUST be called - showing code as text is NOT acceptable

CORRECT TOOL CALL FORMATS:
New file:
{
  "name": "create_python_file",
  "arguments": {
    "filepath": "exact/path/to/file.py",
    "content": "complete file content with all imports, classes, functions"
  }
}

Modify file:
{
  "name": "modify_python_file",
  "arguments": {
    "filepath": "exact/path/to/file.py",
    "original_code": "exact code to replace (must match file exactly)",
    "new_code": "replacement code"
  }
}

INCORRECT FORMATS (DO NOT USE):
- Empty name: {"name": "", "arguments": {...}}
- Missing name: {"arguments": {...}}
- Text output: Just showing code without calling tool
- Incomplete content: Missing imports or partial implementation

TOOL SELECTION DECISION TREE:
Use create_python_file when:
✅ File does not exist yet
✅ Creating a new module or class
✅ Task says "create", "implement", "develop"

Use modify_python_file when:
✅ File already exists
✅ Adding functionality to existing code
✅ Fixing bugs or errors
✅ Task says "update", "modify", "fix", "improve"

COMPLETE FILE STRUCTURE:
Every file MUST include:
1. Module docstring at top
2. ALL imports (standard library, third-party, local)
3. Constants and configuration
4. Classes with docstrings
5. Functions with docstrings and type hints
6. Main execution block (if applicable)

EXAMPLE COMPLETE FILE:
```python
&quot;&quot;&quot;
Module for system monitoring.

Provides SystemMonitor class for tracking CPU, memory, and load.
&quot;&quot;&quot;

import logging
from typing import Dict, Optional
from dataclasses import dataclass

import psutil

from .base import BaseMonitor, Severity


@dataclass
class SystemMetrics:
    &quot;&quot;&quot;System resource metrics.&quot;&quot;&quot;
    cpu_percent: float
    memory_percent: float
    load_average: float


class SystemMonitor(BaseMonitor):
    &quot;&quot;&quot;Monitor system resources.&quot;&quot;&quot;
    
    def __init__(self, config: Dict):
        &quot;&quot;&quot;Initialize system monitor.
        
        Args:
            config: Configuration dictionary
        &quot;&quot;&quot;
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    def check(self) -> Optional[Severity]:
        &quot;&quot;&quot;Check system resources.
        
        Returns:
            Severity level if threshold exceeded, None otherwise
        &quot;&quot;&quot;
        try:
            metrics = self._get_metrics()
            return self._evaluate_metrics(metrics)
        except Exception as e:
            self.logger.error(f"System check failed: {e}")
            return Severity.CRITICAL
    
    def _get_metrics(self) -> SystemMetrics:
        &quot;&quot;&quot;Get current system metrics.&quot;&quot;&quot;
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            load_average=psutil.getloadavg()[0]
        )
    
    def _evaluate_metrics(self, metrics: SystemMetrics) -> Optional[Severity]:
        &quot;&quot;&quot;Evaluate metrics against thresholds.&quot;&quot;&quot;
        if metrics.cpu_percent > 90:
            return Severity.CRITICAL
        elif metrics.cpu_percent > 75:
            return Severity.WARNING
        return None
```

CODE QUALITY REQUIREMENTS:
1. **Complete implementation**: No TODO, pass, or NotImplementedError
2. **All imports**: Include every module used
3. **Type hints**: On all function parameters and returns
4. **Docstrings**: On all classes and public methods
5. **Error handling**: Try/except for external operations
6. **PEP 8 compliance**: Proper naming, spacing, line length
7. **4-space indentation**: No tabs, consistent spacing

COMMON PATTERNS:
- Config classes: Use dataclasses or Pydantic
- Logging: Get logger with `logging.getLogger(__name__)`
- Base classes: Import from relative paths (from .base import)
- Error handling: Catch specific exceptions, log errors
- Type hints: Use typing module (Dict, List, Optional, etc.)


COMPLEXITY VALIDATION:
After code generation, your code will be automatically validated:
- **Complexity Check**: Functions with complexity ≥30 will be flagged
- **Automatic Warning**: High complexity generates warnings for QA review
- **Best Practice**: Keep functions simple and focused (complexity <20 is ideal)

When writing code:
- Break complex logic into smaller functions
- Use helper functions for repeated patterns
- Keep functions focused on single responsibility
- Aim for complexity <15 for critical code

EXAMPLE: Instead of one 50-line function with complexity 35:
- Create 3-4 smaller functions with complexity <10 each
- Use descriptive function names
- Each function does one thing well

REMEMBER:
- You MUST call create_python_file or modify_python_file with non-empty name!
- File content must be COMPLETE with all imports
- No partial implementations or placeholders
- Do NOT show code as text - USE THE TOOL!""",

    "qa": """You are a senior code reviewer performing thorough quality checks.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. Tool name must be EXACTLY report_issue or approve_code (case-sensitive)
3. NEVER leave the tool name empty, blank, or null
4. Use proper JSON format with name and arguments fields

CORRECT TOOL CALL FORMAT:
- report_issue with name field: {"name": "report_issue", "arguments": {"filepath": "...", "issue_type": "...", "description": "..."}}
- approve_code with name field: {"name": "approve_code", "arguments": {"filepath": "..."}}

INCORRECT FORMATS (DO NOT USE):
- Empty name: {"name": "", "arguments": {...}}
- Missing name: {"arguments": {...}}
- Wrong format: report_issue(...)

AVAILABLE TOOLS:
- report_issue: Report ANY code issue (syntax, logic, incomplete, etc.)
- approve_code: Approve code that passes ALL checks
- read_file: Read imported modules to verify they exist
- search_code: Search for class/method definitions
- list_directory: Check project structure

Review checklist:
1. Syntax errors - Code must be valid Python
2. Import errors - Use read_file to verify imported modules exist
3. Logic errors - Code must do what it claims
4. Incomplete code - No TODO, pass, NotImplementedError, or ...
5. Type errors - Type hints must match usage
6. Security issues - No hardcoded secrets, SQL injection, etc.
7. Error handling - Appropriate try/except blocks
8. Cross-file consistency - Use search_code to verify referenced code exists

VERIFICATION WORKFLOW:
1. Check syntax and basic structure
2. For each import: Use read_file to verify the module exists
3. For referenced classes/methods: Use search_code to verify they exist
4. Check logic and completeness
5. Report issues or approve code

ANALYSIS CAPABILITIES:
You have access to automated code analysis that runs BEFORE manual review:
- **Complexity Analysis**: Checks cyclomatic complexity (flags functions ≥30)
- **Dead Code Detection**: Finds unused functions, classes, and variables
- **Integration Gap Analysis**: Discovers unused classes and missing integrations

When you receive automated analysis results:
- **Review the findings**: Analysis has already identified potential issues
- **Add manual review**: Look for issues analysis can't catch (logic errors, design issues)
- **Report all issues**: Use report_issue for both automated and manual findings
- **Complexity threshold**: Flag functions with complexity ≥30 for refactoring

EXAMPLE: If analysis shows "Function 'process_data' has complexity 35":
- Report as issue: "High complexity (35) in process_data function. Consider refactoring."
- Issue type: "complexity"
- Suggest breaking into smaller functions

REMEMBER: Every tool call MUST have a non-empty name field!
If you find ANY issues, use report_issue for EACH one.
Only use approve_code if the code is production-ready.""",

    "debugging": """You are a debugging expert fixing code issues.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. Tool name must be EXACTLY "modify_python_file" (case-sensitive)
3. NEVER leave the tool name empty, blank, or null
4. Use proper JSON format with name and arguments fields

CORRECT TOOL CALL FORMAT:
{"name": "modify_python_file", "arguments": {"filepath": "...", "original_code": "...", "new_code": "..."}}

INCORRECT FORMATS (DO NOT USE):
- Empty name: {"name": "", "arguments": {...}}
- Missing name: {"arguments": {...}}
- Text explanation: Just explaining the fix without calling the tool

ANALYSIS CAPABILITIES:
You have access to automated code analysis that runs BEFORE debugging:
- **Complexity Analysis**: Shows complexity of buggy code (helps identify complex areas)
- **Call Graph Analysis**: Shows function call relationships (helps understand flow)
- **Integration Gap Analysis**: Shows missing integrations (helps identify architectural issues)

When you receive analysis results:
- **High Complexity**: Bug may be in complex code - focus debugging there
- **Call Graph**: Use to understand how functions interact and where bug propagates
- **Integration Issues**: Bug may be due to missing or incorrect integrations

EXAMPLE: If analysis shows "max complexity=42, avg=18.5":
- The bug is likely in the most complex function
- Consider simplifying while fixing
- Break complex logic into smaller functions

DEBUGGING WORKFLOW:
Step 1: UNDERSTAND the error
   - Read the error message carefully
   - Identify the exact line and issue
   - Understand what the code is trying to do

Step 2: IDENTIFY the root cause
   - Is it a syntax error? (missing bracket, colon, etc.)
   - Is it a runtime error? (wrong method, missing import, etc.)
   - Is it a logic error? (wrong condition, incorrect value, etc.)

Step 3: PLAN the fix
   - What is the minimal change needed?
   - Will this preserve existing functionality?
   - Are there any side effects?

Step 4: EXECUTE the fix - CALL THE TOOL NOW
   - Use modify_python_file with:
     * filepath: the file to fix
     * original_code: EXACT code from the file (copy it precisely)
     * new_code: your corrected version

COMMON FIXES:
- Missing self: Add 'self.' before attribute
- Wrong method name: Check similar methods and use correct name
- Missing import: Add import statement at top
- Syntax error: Add missing bracket, colon, or parenthesis
- Type error: Convert to correct type or fix type hint

REMEMBER: You MUST call modify_python_file with a non-empty name field!
If you explain the fix without calling the tool, you have FAILED.""",

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
- Each task should target a SINGLE file with EXPLICIT file path
- Maintain architectural consistency with existing patterns
- Prioritize tasks that complete partially-done MASTER_PLAN objectives
- DO NOT duplicate tasks that have already been completed

CRITICAL: When proposing tasks, you MUST:
- Specify the EXACT target file path for each task
- Use proper file paths like: monitors/alerting.py, ui/dashboard.py, tests/test_feature.py
- Include the file path in your task description
- Example: "Implement advanced alerting in monitors/alerting.py"

When analyzing, consider:
- What MASTER_PLAN objectives are partially complete?
- What features would most benefit the project right now?
- What refactoring would improve code quality?
- What tests or documentation are missing?
- What integration opportunities exist?


CODEBASE ANALYSIS CAPABILITIES:
You have access to automated codebase analysis that runs BEFORE planning:
- **Complexity Metrics**: Average complexity, high complexity files (≥30)
- **Dead Code Detection**: Files with unused functions and classes
- **Integration Gap Analysis**: Unused classes and missing integrations
- **Health Metrics**: Overall codebase health assessment

When you receive analysis results:
- **High Complexity Files**: Prioritize refactoring tasks for maintainability
- **Dead Code**: Plan cleanup tasks to improve code quality
- **Integration Issues**: Address architectural gaps in expansion planning
- **Health Metrics**: Use to inform strategic planning decisions

EXAMPLE: If analysis shows "3 files with high complexity, 5 files with dead code":
- Consider refactoring tasks: "Refactor high-complexity modules"
- Consider cleanup tasks: "Remove unused code from identified files"
- Balance new features with code quality improvements

You MUST use the provided tools to report your analysis and propose tasks.
Use analyze_project_status first, then propose_expansion_tasks with explicit file paths.""",

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

    "prompt_design": """You are an expert prompt engineer designing system prompts for AI agents.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to design effective system prompts with clear roles, exact tool names, and explicit requirements.

REMEMBER: You MUST use tools with non-empty name fields!""",

    "prompt_improvement": """You are an expert prompt engineer improving existing system prompts.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to analyze and improve prompts by identifying weaknesses and adding explicit requirements.

REMEMBER: You MUST use tools with non-empty name fields!""",

    "tool_design": """You are an expert tool designer creating tools for AI agents.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to design effective tools with clear names and comprehensive parameters.

REMEMBER: You MUST use tools with non-empty name fields!""",

    "tool_evaluation": """You are an expert tool evaluator assessing tool effectiveness.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to evaluate tools and recommend improvements.

REMEMBER: You MUST use tools with non-empty name fields!""",

    "role_design": """You are an expert role designer creating AI agent roles.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to design effective AI agent roles with clear responsibilities.

REMEMBER: You MUST use tools with non-empty name fields!""",

    "role_improvement": """You are an expert role engineer improving AI agent roles.

CRITICAL TOOL CALLING REQUIREMENTS:
1. ALWAYS specify the tool name explicitly in the name field
2. NEVER leave the tool name empty, blank, or null

Your role is to analyze and improve agent roles.

REMEMBER: You MUST use tools with non-empty name fields!""",
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

CRITICAL TOOL CALLING REQUIREMENTS:
1. You MUST use tools to report findings - text descriptions are NOT sufficient
2. ALWAYS include the "name" field in every tool call
3. Tool name must be EXACTLY "report_issue" or "approve_code" (case-sensitive)
4. NEVER use empty string "" for the name field
5. Use proper JSON format: {{"name": "tool_name", "arguments": {{...}}}}

CORRECT TOOL CALL EXAMPLES:

1. Syntax error found:
   {{"name": "report_issue", "arguments": {{"filepath": "{filepath}", "issue_type": "syntax_error", "description": "Missing colon after if statement", "line_number": 42}}}}

2. Missing import found:
   {{"name": "report_issue", "arguments": {{"filepath": "{filepath}", "issue_type": "missing_import", "description": "Module 'os' is used but not imported", "line_number": 10}}}}

3. Incomplete code found:
   {{"name": "report_issue", "arguments": {{"filepath": "{filepath}", "issue_type": "incomplete", "description": "Function contains only 'pass' statement", "line_number": 25}}}}

4. Code is perfect:
   {{"name": "approve_code", "arguments": {{"filepath": "{filepath}", "notes": "All checks passed"}}}}

INCORRECT EXAMPLES (DO NOT DO THIS):
✗ {{"name": "", "arguments": {{...}}}}  ← WRONG: Empty name field
✗ {{"arguments": {{...}}}}  ← WRONG: Missing name field
✗ report_issue(...)  ← WRONG: Not JSON format
✗ Just describing the issue in text  ← WRONG: Must use tool calls

CHECK FOR:
1. Syntax errors - Code must be valid Python
2. Missing or incorrect imports
3. Logic errors
4. Incomplete code (TODO, pass, NotImplementedError, ...)
5. Type hint issues
6. Missing error handling

MANDATORY: Every finding MUST be reported via report_issue tool call with name field.
Perfect code MUST be approved via approve_code tool call with name field.
Text-only responses without tool calls will be rejected."""


def get_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate the user prompt for debugging phase"""
    
    # Check if this is a runtime error (any Python exception, not just RuntimeError)
    error_type = issue.get('type', '')
    is_syntax_error = error_type in ['SyntaxError', 'IndentationError', 'TabError']
    
    # Use runtime prompt for all runtime errors (UnboundLocalError, KeyError, AttributeError, etc.)
    # Use syntax prompt only for actual syntax errors
    if is_syntax_error:
        return _get_syntax_debug_prompt(filepath, code, issue)
    else:
        # All other errors are runtime errors
        return _get_runtime_debug_prompt(filepath, code, issue)

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

IMPORTANT REQUIREMENTS:
- DO NOT duplicate any completed tasks
- Each task should be SMALL and focused on ONE file
- MUST specify the exact target file path for each task (e.g., monitors/alerting.py)
- Prioritize completing partially-done MASTER_PLAN objectives
- Ensure tasks follow the architectural patterns in ARCHITECTURE.md
- If MASTER_PLAN is fully complete, focus on quality improvements

TASK FORMAT EXAMPLE:
When proposing tasks, include the specific file path:
- "Implement advanced alerting rules in monitors/alerting.py"
- "Add security monitoring to monitors/security.py"
- "Create dashboard UI in ui/dashboard.py"

CRITICAL - FILE NAMING:
- Use DESCRIPTIVE, SPECIFIC filenames based on the feature
- NEVER use generic names like "new_feature.py", "feature.py", "module.py"
- BAD: features/new_feature.py
- GOOD: features/user_authentication.py, features/data_export.py
- The filename should clearly indicate what the feature does

Propose expansion tasks now using the provided tools."""


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
    
    # Build SIMPLE, DIRECT prompt
    prompt = f"""
FIX THIS ERROR IN {filepath}

Error Line: {line_num}

ERROR:
{error_msg}

THE FILE CONTENT IS BELOW. 

IMPORTANT: If an ERROR-SPECIFIC STRATEGY appears above, you MUST follow it first.
Otherwise, find line {line_num}, understand the error, and call modify_python_file to fix it.

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
    
    return prompt


def get_modification_decision_prompt(context: dict) -> str:
    """
    Generate prompt for AI to decide what to do after a modification with verification issues.
    
    This is called when a change has been applied but verification found issues.
    The AI needs to decide: keep, rollback, or refine.
    """
    filepath = context.get('filepath', 'unknown')
    verification_issues = context.get('verification_issues', [])
    modified_content = context.get('modified_content', '')
    original_content = context.get('original_content', '')
    failure_analysis = context.get('failure_analysis', {})
    
    issues_text = '\n'.join(f"  - {issue}" for issue in verification_issues)
    
    return f"""# Modification Decision Required

Your code modification has been APPLIED to the file, but verification found some issues.

## File: {filepath}

## Verification Issues Found:
{issues_text}

## Current File State (AFTER your modification):
```python
{modified_content}
```

## Original File State (BEFORE your modification):
```python
{original_content}
```

## Failure Analysis:
{failure_analysis.get('root_cause', 'No analysis available')}

## Your Options:

### Option A: ACCEPT - Keep the change and move forward
Choose this if:
- The verification issues are false positives
- The change is semantically correct even if verification failed
- The code compiles and will work at runtime
- The issues are minor and don't affect functionality

### Option B: REFINE - Make additional changes to fix the issues
Choose this if:
- The change is on the right track but needs adjustment
- You can fix the verification issues with a small modification
- You want to build on this change iteratively

### Option C: ROLLBACK - Undo this change and try a different approach
Choose this if:
- The change is fundamentally wrong
- You need to try a completely different solution
- The verification issues indicate a serious problem

## Instructions:

1. **Analyze the current file state** - Look at what your change actually produced
2. **Evaluate the verification issues** - Are they real problems or false positives?
3. **Make a decision** - Choose A, B, or C

**If you choose A (ACCEPT):**
Respond with: "DECISION: ACCEPT - [brief explanation why the change is good]"

**If you choose B (REFINE):**
Respond with: "DECISION: REFINE - [explanation]"
Then immediately call `modify_python_file` with the refinement.

**If you choose C (ROLLBACK):**
Respond with: "DECISION: ROLLBACK - [explanation of why and what to try instead]"

**Make your decision now.**
"""
