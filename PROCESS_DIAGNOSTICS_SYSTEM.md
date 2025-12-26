# Process Diagnostics System

## Overview

The Process Diagnostics System provides comprehensive analysis of why processes fail to start or exit prematurely. This is critical for debugging issues where programs exit with code -1 or crash before logging starts.

## Problem Solved

### Before
```
⚠️  Program exited with code -1 but no errors in log file
   Checking stdout/stderr for crash information...
✅ No runtime errors detected in 301 seconds
🎉 All tests passed!
```

**Issues:**
- Exit code -1 indicates failure, but system reported success
- No diagnostic information about WHY the process failed
- User left guessing what went wrong

### After
```
⚠️  Program exited with code -1 but no errors in log file
   Checking stdout/stderr for crash information...

======================================================================
🚨 CRITICAL: Process failed to start (exit code -1)
======================================================================

Running comprehensive diagnostics...

======================================================================
🔍 PROCESS DIAGNOSTIC REPORT
======================================================================

Command: ./autonomous --no-ui ../my_project/
Working Directory: /home/ai/AI/test-automation

📦 Executable Information:
  Name: ./autonomous
  Found: ✅ Yes
  Path: /home/ai/AI/test-automation/autonomous
  Is File: ✅ Yes
  Executable: ❌ No
  Size: 12345 bytes

❌ Issues Found:
  • Executable not executable: /home/ai/AI/test-automation/autonomous

💡 Recommendations:
  • Run: chmod +x /home/ai/AI/test-automation/autonomous

🔢 Exit Code Analysis:
  Code: -1
  Meaning: Process failed to start or was killed before starting
  Category: STARTUP_FAILURE
  Likely Causes:
    • Executable not found
    • Permission denied
    • Invalid command syntax
    • Missing dependencies
    • Working directory doesn't exist
  Recommendations:
    • Check if executable exists and is executable
    • Verify working directory exists
    • Check command syntax
    • Review stderr output for error messages

❌ Cannot continue - process failed to start
   Please fix the issues above and try again
```

## Components

### 1. ProcessDiagnostics Class

Located in `pipeline/process_diagnostics.py`

**Key Methods:**

#### `diagnose_command(command, working_dir)`
Performs comprehensive diagnosis of a command:
- Parses command to extract executable
- Checks if executable exists and is executable
- Verifies working directory
- Checks for common issues (shell operators, quotes, etc.)
- Detects Python/Node.js availability

**Returns:** Dictionary with diagnostic information

#### `analyze_exit_code(exit_code)`
Analyzes exit codes to determine what went wrong:
- Exit code 0: Success
- Exit code -1: Startup failure
- Exit code 1: General error
- Exit code 2: Usage error
- Exit code 126: Permission denied
- Exit code 127: Command not found
- Exit codes 129-192: Terminated by signal
- Exit code 255: Out of range

**Returns:** Dictionary with analysis

#### `format_diagnostic_report(diagnostics, exit_code)`
Formats diagnostic information as a readable report with:
- Command and working directory
- Executable information
- Environment information
- Issues found
- Warnings
- Recommendations
- Exit code analysis

**Returns:** Formatted string

### 2. RuntimeTester Integration

**New Features:**

#### Diagnostic Instance
```python
self.diagnostics = ProcessDiagnostics(logger)
```

#### `get_diagnostic_report()`
Returns comprehensive diagnostic report including:
- Command diagnosis
- Exit code analysis
- Recent stderr output (last 20 lines)
- Recent stdout output (last 20 lines)

### 3. run.py Integration

**Exit Code -1 Detection:**
When exit code is -1:
1. Displays critical failure message
2. Runs comprehensive diagnostics
3. Shows full diagnostic report
4. **Exits with code 1** (does not continue)
5. Prevents false "All tests passed!" message

## Exit Code Reference

| Code | Meaning | Category | Action |
|------|---------|----------|--------|
| 0 | Success | SUCCESS | Continue |
| -1 | Failed to start | STARTUP_FAILURE | **STOP - Show diagnostics** |
| 1 | General error | RUNTIME_ERROR | Debug application |
| 2 | Usage error | USAGE_ERROR | Check arguments |
| 126 | Not executable | PERMISSION_ERROR | chmod +x |
| 127 | Not found | NOT_FOUND | Check PATH |
| 128 | Invalid exit | INVALID_EXIT | Check code |
| 129-192 | Signal (N-128) | SIGNAL | Check signal |
| 255 | Out of range | OUT_OF_RANGE | Check code |

## Common Issues Detected

### 1. Executable Not Found
```
❌ Issues Found:
  • Executable not found: ./myapp

💡 Recommendations:
  • Check if './myapp' is installed or in PATH
```

### 2. Permission Denied
```
❌ Issues Found:
  • Executable not executable: /path/to/myapp

💡 Recommendations:
  • Run: chmod +x /path/to/myapp
```

### 3. Working Directory Missing
```
❌ Issues Found:
  • Working directory does not exist: /path/to/dir
```

### 4. Invalid Command Syntax
```
❌ Issues Found:
  • Unmatched quotes in command
```

### 5. Missing Dependencies
```
❌ Issues Found:
  • Python not available in PATH
```

## Usage Examples

### Automatic (Integrated)
The system automatically runs diagnostics when exit code is -1:

```bash
python3 run.py --debug-qa --command "./myapp" /path/to/project
```

If the process fails to start, you'll see the full diagnostic report.

### Manual (Programmatic)
```python
from pipeline.process_diagnostics import ProcessDiagnostics
from pathlib import Path

# Create diagnostics instance
diagnostics = ProcessDiagnostics()

# Diagnose command
diag_info = diagnostics.diagnose_command(
    "./myapp --arg1 --arg2",
    Path("/path/to/working/dir")
)

# Analyze exit code
analysis = diagnostics.analyze_exit_code(-1)

# Format report
report = diagnostics.format_diagnostic_report(diag_info, -1)
print(report)
```

## Benefits

1. **Immediate Problem Identification**: Know exactly why a process failed
2. **Actionable Recommendations**: Get specific steps to fix the issue
3. **No False Positives**: Exit code -1 now properly detected as failure
4. **Comprehensive Analysis**: Checks executable, permissions, environment, syntax
5. **Time Savings**: No more guessing or trial-and-error debugging

## Implementation Details

### Detection Strategy
1. Parse command to extract executable
2. Search for executable in:
   - Absolute path (if starts with /)
   - Relative to working directory
   - System PATH
3. Check file properties:
   - Exists
   - Is file
   - Is executable
   - Size
4. Check environment:
   - Working directory exists
   - Working directory readable/writable
   - Python/Node.js available (if needed)
5. Check command syntax:
   - Shell operators
   - Environment variables
   - Quote matching

### Exit Code Analysis
Uses standard Unix exit code conventions:
- 0: Success
- 1-2: Application errors
- 126-127: Shell errors
- 128+N: Terminated by signal N
- -1: Special case for startup failure

### Output Formatting
- Clear sections with emoji icons
- Bullet points for issues/recommendations
- Color-coded (via emoji) for quick scanning
- Includes both high-level and detailed information

## Testing

The system has been tested with:
- ✅ Missing executables
- ✅ Permission denied errors
- ✅ Invalid working directories
- ✅ Malformed commands
- ✅ Missing dependencies
- ✅ Various exit codes

## Future Enhancements

Planned improvements:
- Dependency checking (ldd, otool)
- Environment variable validation
- Configuration file validation
- Network connectivity checks
- Resource availability checks (disk space, memory)
- Historical failure analysis
- Suggested fixes with confidence scores

## Related Documentation

- `PROGRESSIVE_TEST_DURATION.md` - Progressive testing feature
- `COMMAND_DETECTION.md` - Automatic command detection
- `SESSION_SUMMARY_DEC26.md` - Recent changes summary