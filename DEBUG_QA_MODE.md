# Debug/QA Mode Documentation

## Overview

The `--debug-qa` flag enables a continuous debugging and quality assurance mode that helps identify and fix errors in your Python project before running the full development pipeline.

## Purpose

This mode is specifically designed for:
- **Debugging**: Identifying syntax errors, import issues, and other problems
- **Quality Assurance**: Ensuring code quality before deployment
- **Continuous Improvement**: Iteratively fixing issues until the codebase is clean

**Note**: This mode is NOT for new development - it's exclusively for debugging and QA of existing code.

## Usage

```bash
# Run debug/QA mode on current directory
python run.py . --debug-qa

# Run debug/QA mode on specific project
python run.py /path/to/project --debug-qa
```

## Features

### 1. Comprehensive Error Detection

The debug/QA mode checks for:

- **Syntax Errors**: Missing parentheses, brackets, colons, incorrect indentation
- **Import Errors**: Missing modules, incorrect import paths
- **AST Parsing Errors**: Deep syntax validation using Python's Abstract Syntax Tree
- **Runtime Issues**: Detectable problems that would cause runtime failures

### 2. Continuous Loop

The mode operates in a continuous loop:

1. **Scan**: Checks all Python files in the project
2. **Report**: Displays all errors and warnings found
3. **Wait**: Pauses for you to fix the issues
4. **Re-check**: Automatically re-scans after you press Enter
5. **Success**: Exits when no errors are found

### 3. Detailed Error Reporting

For each error found, the mode provides:

- **File name**: Relative path to the problematic file
- **Error type**: SyntaxError, ImportError, etc.
- **Line number**: Exact location of the error
- **Error message**: Clear description of the problem
- **Code snippet**: The problematic line of code (when available)
- **Column position**: Precise location within the line

### 4. User-Friendly Interface

```
======================================================================
🔍 DEBUG/QA MODE - Continuous Error Detection
======================================================================

Project: /path/to/your/project

This mode will continuously check for:
  • Syntax errors in Python files
  • Import errors
  • Runtime errors (when possible)

Press Ctrl+C to exit at any time.

──────────────────────────────────────────────────────────────────────
🔄 Iteration 1 - 09:10:42
──────────────────────────────────────────────────────────────────────

📁 Found 32 Python files to check

🔍 Checking imports...

======================================================================
📊 RESULTS
======================================================================

❌ ERRORS FOUND: 2

1. SyntaxError in test_file.py
   Line 8: '(' was never closed
   Code: print("Missing closing parenthesis"
   Position: column 5

2. ImportError in main.py
   ModuleNotFoundError: No module named 'nonexistent_module'

──────────────────────────────────────────────────────────────────────
🔧 Please fix the errors above, then press Enter to re-check...
   Or press Ctrl+C to exit
──────────────────────────────────────────────────────────────────────
```

## Example Workflow

### Step 1: Start Debug/QA Mode

```bash
cd /path/to/autonomy
python run.py . --debug-qa
```

### Step 2: Review Errors

The mode will scan all Python files and report any issues:

```
❌ ERRORS FOUND: 3

1. SyntaxError in config/settings.py
   Line 45: invalid syntax
   
2. ImportError in pipeline/handlers.py
   ModuleNotFoundError: No module named 'requests'
   
3. SyntaxError in utils/helpers.py
   Line 12: expected ':'
```

### Step 3: Fix the Errors

Open the files and fix the reported issues:

```bash
# Fix missing import
pip install requests

# Fix syntax errors in your editor
vim config/settings.py
vim utils/helpers.py
```

### Step 4: Re-check

Press Enter in the debug/QA mode terminal. It will automatically re-scan:

```
🔄 Iteration 2 - 09:15:30
──────────────────────────────────────────────────────────────────────

📁 Found 32 Python files to check

🔍 Checking imports...

======================================================================
📊 RESULTS
======================================================================

✅ SUCCESS! No errors or warnings found.

🎉 All checks passed! The application appears to be error-free.

You can now run the application normally.
```

### Step 5: Exit

The mode automatically exits when all errors are resolved, or you can press Ctrl+C at any time.

## What Gets Checked

### Python Files
- All `.py` files in the project directory
- Recursively scans subdirectories
- Skips `__pycache__`, `venv`, and `.venv` directories

### Error Types

1. **Syntax Errors**
   - Missing/extra parentheses, brackets, braces
   - Missing colons after function/class definitions
   - Incorrect indentation
   - Invalid Python syntax

2. **Import Errors**
   - Missing required modules
   - Incorrect import paths
   - Circular import issues

3. **AST Parsing Errors**
   - Deep syntax validation
   - Structural issues in code

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