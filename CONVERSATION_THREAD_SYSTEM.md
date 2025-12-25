# Conversation Thread System

## Overview

The Conversation Thread System maintains persistent context across multiple debugging attempts, enabling specialists to collaborate and build on previous analysis. This creates a comprehensive debugging session where all context is preserved and shared.

## Key Components

### 1. ConversationThread (`pipeline/conversation_thread.py`)

Manages a persistent conversation for debugging a single issue.

**Features:**
- Full message history with timestamps
- Attempt tracking with success/failure
- File state snapshots at each attempt
- Patch history
- Specialist consultation records
- Context data accumulation

**Key Methods:**
```python
thread = ConversationThread(issue, project_dir)

# Add messages
thread.add_message(role="user", content="...", tool_calls=[...])

# Record attempts
thread.record_attempt(
    agent_name="Primary Debugger",
    original_code="...",
    replacement_code="...",
    success=False,
    error_message="...",
    analysis={...}
)

# Add specialist analysis
thread.add_specialist_analysis("Whitespace Analyst", analysis)

# Get comprehensive context
context = thread.get_comprehensive_context()

# Save thread
thread.save_thread(output_dir)
```

### 2. SpecialistTeam (`pipeline/specialist_agents.py`)

Manages multiple AI specialists with different expertise.

**Available Specialists:**

1. **Whitespace Analyst** (qwen2.5-coder:32b)
   - Expertise: Whitespace, indentation, formatting
   - Detects: Tab/space issues, indentation levels, line endings
   - Tools: Raw file reading, character analysis

2. **Syntax Analyst** (qwen2.5-coder:32b)
   - Expertise: Python syntax and structure
   - Detects: Missing colons, unmatched brackets, syntax errors
   - Tools: Syntax checking, AST parsing

3. **Pattern Analyst** (deepseek-coder-v2)
   - Expertise: Code patterns and similarity
   - Detects: Similar code blocks, duplication, refactoring needs
   - Tools: Code search, pattern matching

4. **Root Cause Analyst** (qwen2.5:14b)
   - Expertise: Root cause analysis and strategy
   - Detects: Underlying issues, failure patterns
   - Tools: Comprehensive analysis, strategic planning

**Usage:**
```python
team = SpecialistTeam(client, logger)

# Consult single specialist
analysis = team.consult_specialist("Whitespace Analyst", thread, tools)

# Consult entire team
team_analysis = team.consult_team(thread, tools)

# Get best specialist for failure type
specialist = team.get_best_specialist_for_failure("CODE_NOT_FOUND")
```

### 3. Specialized Prompts (`pipeline/failure_prompts.py`)

Provides focused prompts for each failure type.

**Available Prompts:**
- `get_code_not_found_prompt()` - When code isn't found
- `get_syntax_error_prompt()` - For syntax errors
- `get_indentation_error_prompt()` - For indentation issues
- `get_verification_failure_prompt()` - For verification failures
- `get_import_error_prompt()` - For import errors
- `get_retry_prompt()` - For retry attempts with analysis

Each prompt includes:
- Problem description
- Context and history
- Specialist analysis requirements
- Specific tool calls needed
- Success criteria

### 4. Sudo Filter (`pipeline/sudo_filter.py`)

Filters and blocks sudo commands with helpful feedback.

**Features:**
- Detects sudo in various forms (direct, piped, chained)
- Provides clear error messages
- Suggests alternatives
- Tracks blocked commands

**Usage:**
```python
from pipeline.sudo_filter import filter_sudo_from_tool_calls

allowed, blocked, summary = filter_sudo_from_tool_calls(tool_calls)
```

## Workflow

### Standard Debugging Flow

```
1. Create ConversationThread
   ↓
2. Attempt #1: Initial fix
   ↓
3. Record attempt (success/failure)
   ↓
4. If failed:
   a. Analyze failure
   b. Consult specialist
   c. Specialist uses tools
   d. Add analysis to thread
   ↓
5. Attempt #2: Retry with full context
   ↓
6. Repeat until success or max attempts
   ↓
7. Save complete thread
```

### Specialist Consultation Flow

```
1. Failure detected
   ↓
2. Determine best specialist
   ↓
3. Specialist receives:
   - Full conversation history
   - All previous attempts
   - File snapshots
   - Previous analyses
   ↓
4. Specialist analyzes using tools:
   - read_file
   - search_code
   - execute_command
   - etc.
   ↓
5. Specialist provides:
   - Findings
   - Recommendations
   - Tool calls
   - Confidence level
   ↓
6. Results added to thread
   ↓
7. Next attempt uses this context
```

## Example Session

### Attempt #1: Initial Try
```
User: Fix the curses error
AI: [Tries to replace code]
Result: ❌ CODE_NOT_FOUND - Original code not found
```

### Specialist Consultation
```
System: Consulting Whitespace Analyst...
Specialist: [Uses tools to examine file]
  - read_file with raw mode
  - execute_command: cat -A file.py
Findings:
  - File uses 12 spaces for indentation
  - AI provided code with 0 spaces
  - Exact match failed due to whitespace
Recommendations:
  - Copy exact code with indentation
  - Use larger code block with context
```

### Attempt #2: Retry with Context
```
User: [Retry prompt with specialist analysis]
AI: [Reads file, copies exact code with indentation]
Result: ✅ SUCCESS
```

### Thread Saved
```
conversation_threads/thread_src_main_20240115_143022.json
Contains:
- All 2 attempts
- Specialist analysis
- File snapshots
- Tool calls and results
- Complete conversation
```

## Benefits

### 1. Persistent Context
- No information loss between attempts
- Specialists build on previous analysis
- Full history available for debugging

### 2. Collaborative Intelligence
- Multiple AI models working together
- Each specialist adds unique perspective
- Consensus recommendations

### 3. Tool-Driven Analysis
- Specialists actively investigate
- Use execute_command for exploration
- Gather evidence before recommending

### 4. Complete Audit Trail
- Every attempt recorded
- All tool calls logged
- Specialist analyses saved
- File evolution tracked

### 5. Improved Success Rate
- Learn from failures
- Specialist guidance
- Comprehensive context
- Multiple perspectives

## Configuration

### Max Attempts
```python
debug_result = debug_phase.execute_with_conversation_thread(
    state,
    issue=issue,
    max_attempts=5  # Default: 5
)
```

### Specialist Selection
```python
# Consult specific specialists
team.consult_team(thread, tools, specialists=[
    "Whitespace Analyst",
    "Syntax Analyst"
])

# Or let system choose based on failure type
specialist = team.get_best_specialist_for_failure(failure_type)
```

### Thread Storage
```python
# Threads saved to:
project_dir/conversation_threads/thread_<id>.json
```

## Thread File Format

```json
{
  "thread_id": "src_main_20240115_143022",
  "issue": {
    "filepath": "src/main.py",
    "type": "AttributeError",
    "message": "...",
    "line": 1018
  },
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "2024-01-15T14:30:22",
      "tool_calls": [],
      "tool_results": []
    },
    {
      "role": "specialist",
      "content": "...",
      "agent_name": "Whitespace Analyst",
      "timestamp": "2024-01-15T14:30:45"
    }
  ],
  "attempts": [
    {
      "attempt_number": 1,
      "agent_name": "Primary Debugger",
      "success": false,
      "error_message": "...",
      "analysis": {...}
    }
  ],
  "file_snapshots": {
    "0": "original content",
    "1": "after attempt 1"
  },
  "specialists_consulted": [
    "Whitespace Analyst",
    "Syntax Analyst"
  ],
  "specialist_analyses": {...}
}
```

## Tool Access for Specialists

All specialists have access to:

### File Operations
- `read_file` - Read file contents
- `list_directory` - List directory contents
- `search_code` - Search for code patterns

### Command Execution
- `execute_command` - Run shell commands (non-sudo)
- Examples:
  - `cat -A file.py` - Show all characters
  - `file file.py` - Check file type
  - `python -m py_compile file.py` - Check syntax
  - `grep -n "pattern" file.py` - Search patterns

### Analysis Tools
- `get_memory_profile` - Memory usage
- `get_cpu_profile` - CPU usage
- `inspect_process` - Process details
- `show_process_tree` - Process hierarchy

### Sudo Filtering
- All `sudo` commands are blocked
- Clear error messages provided
- Alternatives suggested
- Security maintained

## Best Practices

### 1. Let Specialists Investigate
Don't assume - let specialists use tools to gather evidence.

### 2. Build on Previous Analysis
Each attempt should reference previous findings.

### 3. Use Specialized Prompts
Different failure types need different approaches.

### 4. Save Threads
Always save threads for post-mortem analysis.

### 5. Consult Multiple Specialists
Different perspectives lead to better solutions.

## Troubleshooting

### Issue: Specialists not being consulted
**Check:** Is failure analysis being generated?
**Solution:** Ensure failure_analyzer is integrated in handlers.py

### Issue: Thread not saving
**Check:** Does conversation_threads/ directory exist?
**Solution:** Directory is created automatically, check permissions

### Issue: Sudo commands being attempted
**Check:** Is sudo filter active?
**Solution:** Filter is automatic, check blocked_calls in results

### Issue: Too many attempts
**Check:** Max attempts setting
**Solution:** Adjust max_attempts parameter (default: 5)

## Related Documentation

- `FAILURE_ANALYSIS_SYSTEM.md` - Failure analysis details
- `ENHANCED_DEBUGGING.md` - Overall debugging system
- `MULTI_FORMAT_PARSER.md` - Response parsing
- `SMART_WHITESPACE_HANDLING.md` - Whitespace matching