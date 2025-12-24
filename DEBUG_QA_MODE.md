# Debug/QA Mode Documentation

## Overview

The `--debug-qa` flag enables a comprehensive, AI-powered continuous debugging and quality assurance mode that uses the full pipeline architecture to automatically identify and fix errors in your Python project.

## Purpose

This mode is specifically designed for:
- **Automated Debugging**: AI-powered fixing of syntax errors, import issues, and runtime problems
- **Quality Assurance**: Deep code analysis using the QA phase
- **Continuous Improvement**: Iteratively fixing issues until the codebase is clean
- **Runtime Monitoring**: Optional log file following for runtime error detection
- **Dependency Analysis**: Examines related files and dependencies

**Note**: This mode is NOT for new development - it's exclusively for debugging and QA of existing code.

## Usage

```bash
# Run debug/QA mode on current directory
python run.py . --debug-qa

# Run debug/QA mode on specific project
python run.py /path/to/project --debug-qa

# Follow a log file for runtime errors
python run.py /path/to/project --debug-qa --follow /path/to/app.log
```

## Features

### 1. Multi-Phase Error Detection

The debug/QA mode performs comprehensive scanning:

- **Phase 1: Syntax Scanning**
  - Scans all Python files recursively
  - Uses AST parsing for deep syntax validation
  - Detects missing parentheses, brackets, colons, incorrect indentation
  - Identifies malformed code structures

- **Phase 2: Import Validation**
  - Attempts to import main modules
  - Detects missing dependencies
  - Identifies circular import issues
  - Validates import paths

- **Phase 3: Runtime Error Monitoring** (with `--follow`)
  - Monitors log files in real-time
  - Detects runtime exceptions and errors
  - Tracks error patterns
  - Correlates errors with source files

### 2. AI-Powered Automatic Fixing

Uses the full pipeline architecture:

- **QA Phase Integration**
  - Deep code analysis for each file
  - Identifies code quality issues
  - Examines related files and dependencies
  - Uses tool calling to investigate context

- **Debugging Phase Integration**
  - AI-powered error fixing
  - Examines surrounding code context
  - Considers file dependencies
  - Applies intelligent fixes

- **Iterative Refinement**
  - Re-scans after each fix
  - Tracks progress across iterations
  - Handles multiple errors per file
  - Groups errors by file for efficiency

### 3. Comprehensive Error Reporting

For each error found, the mode provides:

- **File name**: Relative path to the problematic file
- **Error type**: SyntaxError, ImportError, RuntimeError, etc.
- **Line number**: Exact location of the error
- **Error message**: Clear description of the problem
- **Code snippet**: The problematic line of code (when available)
- **Column position**: Precise location within the line
- **Related files**: Dependencies and related modules

### 4. Intelligent Progress Tracking

- **Iteration Counter**: Tracks debugging cycles
- **Success Rate**: Shows fixes applied vs attempted
- **Progress Detection**: Identifies when no progress is being made
- **Auto-Exit**: Stops after 3 iterations without progress
- **Summary Statistics**: Detailed breakdown of errors and fixes

### 5. User-Friendly Interface

```
======================================================================
🔍 DEBUG/QA MODE - Continuous AI-Powered Debugging & QA
======================================================================

Project: /path/to/your/project

This mode will:
  • Scan all Python files for syntax and import errors
  • Use AI pipeline (QA + Debugging) to fix issues
  • Examine related files and dependencies
  • Track runtime errors from log files (if --follow specified)
  • Continue until all errors are resolved

Press Ctrl+C to exit at any time.

🔍 Discovering Ollama servers...
  ✓ ollama01 (ollama01.example.com): 16 models
  ✓ ollama02 (ollama02.example.com): 5 models

======================================================================
🔄 ITERATION 1 - 09:10:42
======================================================================

📁 Phase 1: Scanning Python files for syntax errors...
   Found 277 Python files to check

📦 Phase 2: Checking imports...

======================================================================
📊 SCAN RESULTS
======================================================================

Found 4 total errors:
  • Syntax errors: 3
  • Import errors: 1
  • Runtime errors: 0

1. SyntaxError in analyze_integration_tools.py
   Line 53: unmatched ']'
   Code: execute_pattern = r"self\.tool_executor\.execute\(\s*['"]([^'"]+)['"]"

2. SyntaxError in archive/old_root_files/ollama_tool_calling.py
   Line 53: invalid syntax
   Code: ```

3. SyntaxError in examples/week1_integration_example.py
   Line 170: invalid syntax
   Code: </file_path>

4. ImportError in src/execution/ai_components.py
   ModuleNotFoundError: No module named 'requests'

======================================================================
🤖 AI PIPELINE - Fixing Errors
======================================================================

📄 Processing analyze_integration_tools.py (1 errors)...
   🔍 Running QA analysis...
   ⚠️  QA found issues: Found syntax error
   🔧 Fixing: SyntaxError at line 53
      ✅ Fixed successfully

📄 Processing archive/old_root_files/ollama_tool_calling.py (1 errors)...
   🔍 Running QA analysis...
   ⚠️  QA found issues: Invalid markdown in code
   🔧 Fixing: SyntaxError at line 53
      ✅ Fixed successfully

📄 Processing examples/week1_integration_example.py (1 errors)...
   🔍 Running QA analysis...
   ⚠️  QA found issues: XML tag in Python code
   🔧 Fixing: SyntaxError at line 170
      ✅ Fixed successfully

📄 Processing src/execution/ai_components.py (1 errors)...
   🔍 Running QA analysis...
   ⚠️  QA found issues: Missing import
   🔧 Fixing: ImportError
      ⚠️  Could not fix: Missing dependency needs manual installation

======================================================================
📊 ITERATION SUMMARY
======================================================================
  Errors found: 4
  Fixes attempted: 4
  Fixes applied: 3
  Success rate: 3/4 (75%)
======================================================================

🔄 Re-scanning for errors...

======================================================================
🔄 ITERATION 2 - 09:11:15
======================================================================

📁 Phase 1: Scanning Python files for syntax errors...
   Found 277 Python files to check

📦 Phase 2: Checking imports...

======================================================================
📊 SCAN RESULTS
======================================================================

Found 1 total errors:
  • Syntax errors: 0
  • Import errors: 1
  • Runtime errors: 0

1. ImportError in src/execution/ai_components.py
   ModuleNotFoundError: No module named 'requests'

[User installs requests: pip install requests]

======================================================================
🔄 ITERATION 3 - 09:12:30
======================================================================

📁 Phase 1: Scanning Python files for syntax errors...
   Found 277 Python files to check

📦 Phase 2: Checking imports...

======================================================================
📊 SCAN RESULTS
======================================================================

✅ SUCCESS! No errors found.

🎉 All errors resolved after 3 iterations!

You can now run the application normally.
```

## Example Workflows

### Workflow 1: Basic Debugging

```bash
# Start debug/QA mode on a project
python run.py /path/to/project --debug-qa
```

The AI will:
1. Scan all Python files for errors
2. Automatically fix syntax errors using the debugging phase
3. Report any errors that need manual intervention (like missing dependencies)
4. Continue iterating until all errors are resolved

### Workflow 2: With Log File Monitoring

```bash
# Monitor runtime errors from a log file
python run.py /path/to/project --debug-qa --follow /var/log/app.log
```

The AI will:
1. Scan for syntax and import errors
2. Monitor the log file for runtime errors in real-time
3. Correlate log errors with source files
4. Fix both static and runtime errors
5. Continue until the application runs cleanly

### Workflow 3: Verbose Mode for Debugging

```bash
# See detailed AI reasoning and tool calls
python run.py /path/to/project --debug-qa -v
```

This shows:
- AI prompts and responses
- Tool calls being executed
- Detailed error traces
- File modifications being made

### Workflow 4: With Custom Ollama Servers

```bash
# Use specific Ollama servers for debugging
python run.py /path/to/project --debug-qa --server ollama01.example.com --server ollama02.example.com
```

### Step-by-Step Example

**Initial State**: Project with multiple errors

```bash
$ python run.py ../test-automation --debug-qa
```

**Iteration 1**: AI detects and fixes 3 out of 4 errors
- Fixed: Unmatched bracket in regex
- Fixed: Markdown code block in Python file
- Fixed: XML tag in Python code
- Manual: Missing 'requests' module

**User Action**: Install missing dependency
```bash
$ pip install requests
```

**Iteration 2**: AI re-scans and confirms all errors resolved
```
✅ SUCCESS! No errors found.
🎉 All errors resolved after 2 iterations!
```

## What Gets Checked

### Python Files
- All `.py` files in the project directory
- Recursively scans subdirectories
- Skips `__pycache__`, `venv`, `.venv`, `.git`, `node_modules` directories
- Groups errors by file for efficient processing

### Error Types

1. **Syntax Errors** (Phase 1)
   - Missing/extra parentheses, brackets, braces
   - Missing colons after function/class definitions
   - Incorrect indentation
   - Invalid Python syntax
   - Malformed code structures
   - AST parsing errors

2. **Import Errors** (Phase 2)
   - Missing required modules
   - Incorrect import paths
   - Circular import issues
   - Module not found errors
   - Only checked if no syntax errors exist

3. **Runtime Errors** (Phase 3 - with `--follow`)
   - Exceptions from log files
   - Traceback analysis
   - Error pattern detection
   - Real-time monitoring

### AI Pipeline Integration

The mode uses the full pipeline architecture:

1. **QA Phase**
   - Analyzes each file with errors
   - Examines code context and dependencies
   - Uses tool calling to read related files
   - Identifies root causes
   - Provides detailed issue reports

2. **Debugging Phase**
   - Receives issues from QA phase
   - Analyzes error context
   - Examines related files and imports
   - Applies intelligent fixes
   - Validates fixes with syntax checking
   - Updates file state tracking

3. **State Management**
   - Tracks all files and their status
   - Records fix attempts and results
   - Maintains history across iterations
   - Enables resume capability

## Exit Options

- **Automatic Exit**: When all errors are resolved
- **Manual Exit**: Press Ctrl+C at any time
- **Exit Code**: Returns 0 on success, 1 on error

## Integration with Development Pipeline

The debug/QA mode is separate from the main development pipeline:

```bash
# First: Debug and fix all errors
python run.py . --debug-qa

# Then: Run the normal development pipeline
python run.py .
```

## Best Practices

1. **Run Before Development**: Use debug/QA mode before starting new development
2. **Fix Incrementally**: Address errors one at a time for clarity
3. **Verify Imports**: Ensure all required packages are installed
4. **Check Regularly**: Run periodically during development
5. **Clean Exit**: Let the mode confirm success before proceeding

## Limitations

- Does not catch logical errors or runtime bugs
- Cannot detect issues that only appear during execution
- Limited to static analysis capabilities
- Does not run unit tests (use separate test commands)

## Troubleshooting

### "No Python files found"
- Ensure you're in the correct directory
- Check that `.py` files exist in the project

### "Import check timed out"
- Large projects may take longer to import
- Consider breaking up large modules
- Check for infinite loops in module initialization

### Persistent Errors
- Verify the error message carefully
- Check file permissions
- Ensure Python version compatibility
- Look for hidden characters or encoding issues

## Command Reference

```bash
# Basic usage
python run.py . --debug-qa

# With specific project path
python run.py /path/to/project --debug-qa

# View help
python run.py --help
```

## See Also

- `README.md` - Main project documentation
- `MASTER_PLAN.md` - Development pipeline overview
- `QA_STEPS.md` - Quality assurance checklist
- `DEBUG_STEPS.md` - Debugging workflow