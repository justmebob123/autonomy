# CRITICAL FIX: stdout/stderr Crash Detection

## Problem Identified

The autonomy system was reporting "No runtime errors detected" even when the program crashed with a `KeyError: 'url'` during initialization. 

**Root Cause:**
- The `RuntimeTester` only monitored the log file for errors
- When programs crash during initialization (before logging starts), errors go to stdout/stderr
- These errors were captured by `ProgramRunner` but never checked
- Result: Silent failures that appeared as "success"

## Example of Missed Error

```
Traceback (most recent call last):
  File "/home/ai/AI/test-automation/src/main.py", line 208, in initialize
    self.job_executor = JobExecutor(
  File "/home/ai/AI/test-automation/src/execution/job_executor.py", line 146, in __init__
    self.server_pool = ServerPool(servers)
  File "/home/ai/AI/test-automation/src/execution/server_pool.py", line 72, in __init__
    url=server['url'],
KeyError: 'url'

ERROR: System initialization failed
```

**What Happened:**
- Program crashed with exit code != 0
- Error printed to stderr
- Log file never created/written
- System reported: "✅ No runtime errors detected"

## Solution Implemented

### 1. Enhanced RuntimeTester.get_errors()

**Before:**
```python
def get_errors(self) -> List[Dict]:
    """Get all detected errors."""
    errors = []
    while not self.error_queue.empty():
        errors.append(self.error_queue.get())
    return errors
```

**After:**
```python
def get_errors(self) -> List[Dict]:
    """Get all detected errors from both log file and stdout/stderr."""
    errors = []
    
    # Get errors from log file monitoring
    while not self.error_queue.empty():
        errors.append(self.error_queue.get())
    
    # CRITICAL: Also check stdout/stderr for errors that didn't make it to log file
    if not self.program_runner.is_running() and self.program_runner.exit_code != 0:
        # Check stderr for tracebacks
        stderr_text = ''.join(self.program_runner.stderr_lines)
        if 'Traceback' in stderr_text or 'Error:' in stderr_text:
            errors.append({
                'type': 'stderr_exception',
                'line': 'Program crashed before logging started',
                'context': self.program_runner.stderr_lines[-50:],
                'exit_code': self.program_runner.exit_code
            })
        
        # Check stdout for errors too
        stdout_text = ''.join(self.program_runner.stdout_lines)
        if 'Traceback' in stdout_text or 'Error:' in stdout_text:
            errors.append({
                'type': 'stdout_exception',
                'line': 'Program crashed before logging started',
                'context': self.program_runner.stdout_lines[-50:],
                'exit_code': self.program_runner.exit_code
            })
    
    return errors
```

### 2. Added Output Access Methods

```python
def get_stdout(self) -> List[str]:
    """Get captured stdout lines."""
    return self.program_runner.stdout_lines.copy()

def get_stderr(self) -> List[str]:
    """Get captured stderr lines."""
    return self.program_runner.stderr_lines.copy()

def get_exit_code(self) -> Optional[int]:
    """Get program exit code."""
    return self.program_runner.exit_code
```

### 3. Enhanced run.py to Check stdout/stderr

Added check after program stops but before reporting success:

```python
# CRITICAL: Check if program crashed but no errors in log file
if not runtime_errors_found and not tester.is_running():
    exit_code = tester.get_exit_code()
    if exit_code and exit_code != 0:
        print(f"\n⚠️  Program exited with code {exit_code} but no errors in log file")
        print("   Checking stdout/stderr for crash information...")
        
        stderr = tester.get_stderr()
        stdout = tester.get_stdout()
        
        # Check stderr for errors
        if stderr and any('Traceback' in line or 'Error' in line for line in stderr):
            print(f"\n❌ Found crash in stderr output!")
            print("\n📋 Program Output (stderr):")
            for line in stderr[-30:]:
                print(f"   {line.rstrip()}")
            
            # Force error detection
            runtime_errors_found.append({
                'type': 'stderr_crash',
                'line': 'Program crashed during initialization',
                'context': stderr[-30:],
                'exit_code': exit_code
            })
```

## Expected Behavior Now

### Before Fix:
```
▶️  Starting program execution...
   Monitoring for runtime errors (300 seconds)...

⚠️  Program exited after 1 seconds

✅ No runtime errors detected in 1 seconds

🎉 All tests passed!
✅ Program ran successfully for 1 seconds
```

### After Fix:
```
▶️  Starting program execution...
   Monitoring for runtime errors (300 seconds)...

⚠️  Program exited after 1 seconds

⚠️  Program exited with code 1 but no errors in log file
   Checking stdout/stderr for crash information...

❌ Found crash in stderr output!

📋 Program Output (stderr):
   Traceback (most recent call last):
     File "/home/ai/AI/test-automation/src/main.py", line 208, in initialize
       self.job_executor = JobExecutor(
     File "/home/ai/AI/test-automation/src/execution/job_executor.py", line 146, in __init__
       self.server_pool = ServerPool(servers)
     File "/home/ai/AI/test-automation/src/execution/server_pool.py", line 72, in __init__
       url=server['url'],
   KeyError: 'url'
   
   ERROR: System initialization failed

❌ Found 1 runtime error(s)!

🔄 Will attempt to fix runtime errors...
```

## Files Modified

1. **pipeline/runtime_tester.py**
   - Enhanced `get_errors()` to check stdout/stderr
   - Added `get_stdout()`, `get_stderr()`, `get_exit_code()` methods

2. **run.py**
   - Added stdout/stderr checking when program exits with non-zero code
   - Display crash information before reporting success
   - Force error detection for initialization crashes

## Impact

✅ **Now Detects:**
- Initialization crashes before logging starts
- KeyError, AttributeError, ImportError during startup
- Any exception that goes to stdout/stderr
- Programs that exit with non-zero code

✅ **Enables AI to Fix:**
- Configuration errors (missing keys, wrong types)
- Import errors during initialization
- Startup crashes
- Any error that prevents logging from starting

## Testing

```bash
cd ~/code/AI/autonomy
git pull origin main

# Test with the crashing program
python3 run.py --debug-qa -vv --follow /home/ai/AI/my_project/.autonomous_logs/autonomous.log \
  --command "./autonomous ../my_project/" ../test-automation/
```

**Expected Result:**
- System detects the KeyError: 'url' crash
- Shows full traceback from stderr
- AI attempts to fix the error in server_pool.py

## Commit

**Commit:** ee39403
**Branch:** main
**Status:** ✅ Pushed to GitHub