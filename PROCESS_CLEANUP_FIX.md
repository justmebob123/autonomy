# CRITICAL FIX: Process Cleanup in Runtime Testing

## Problem Discovered

When running the debug/QA mode with runtime testing (`--command` flag), the system was **NOT properly killing child processes** when stopping the test program. This caused:

### Symptoms
1. **Multiple copies of the program running simultaneously**
2. **All instances writing to the same log file**
3. **Mixed errors from different program versions in the log**
4. **AI trying to fix errors that were already fixed in current code**
5. **Debugging loop completely broken**

### Example
```bash
$ ps auxf | grep autonomous
logan    1453015  3.8  0.1 682492 124756 pts/1   Sl   05:47   2:37  \_ python3 ./autonomous ../my_project/
logan    1453229  0.0  0.0 638420 54216 pts/1    Sl   05:50   0:02  \_ python3 ./autonomous ../my_project/
logan    1453249  0.0  0.0 638420 54052 pts/1    Sl   05:51   0:01  \_ python3 ./autonomous ../my_project/
logan    1453270  0.0  0.0 638420 53844 pts/1    Sl   05:51   0:01  \_ python3 ./autonomous ../my_project/
logan    1453309  0.0  0.0 638420 53612 pts/1    Sl   05:51   0:01  \_ python3 ./autonomous ../my_project/
logan    1453331  0.0  0.0 638420 53616 pts/1    Sl   05:51   0:01  \_ python3 ./autonomous ../my_project/
logan    1453565  4.1  0.1 674364 118032 pts/1   Sl   05:55   2:28  \_ python3 ./autonomous ../my_project/
logan    1454015  0.0  0.0 638432 55212 pts/1    Sl   06:03   0:01  \_ python3 ./autonomous ../my_project/
logan    1454482  0.0  0.0 638432 56380 pts/1    Sl   06:12   0:01  \_ python3 ./autonomous ../my_project/
logan    1454714  0.4  0.1 639444 68808 pts/1    Sl   06:15   0:09  \_ python3 ./autonomous ../my_project/
logan    1456156  3.8  0.1 660028 101712 pts/1   Sl   06:41   0:34  \_ python3 ./autonomous ../my_project/
logan    1456427  0.0  0.0   2800  1852 pts/1    S    06:45   0:00  \_ /bin/sh -c ./autonomous ../my_project/
logan    1456428  3.7  0.1 657980 97108 pts/1    Sl   06:45   0:22  |   \_ python3 ./autonomous ../my_project/
logan    1456630  0.0  0.0   2800  1856 pts/1    S    06:49   0:00  \_ /bin/sh -c ./autonomous ../my_project/
logan    1456631  4.3  0.1 656968 93004 pts/1    Sl   06:49   0:17      \_ python3 ./autonomous ../my_project/
```

**15+ copies of the same program running!** All writing to the same log file!

## Root Cause

When using `subprocess.Popen()` with `shell=True`, the shell creates child processes. The original code only called `process.terminate()` which:
- Only kills the shell process
- **Does NOT kill child processes spawned by the shell**
- Leaves orphaned processes running in the background

## Solution

### 1. Create Process Group on Startup
```python
self.process = subprocess.Popen(
    self.command,
    shell=True,
    cwd=str(self.working_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    preexec_fn=os.setsid  # Create new process group
)
```

The `preexec_fn=os.setsid` creates a new process group, making all child processes part of the same group.

### 2. Kill Entire Process Group on Stop
```python
def stop(self, timeout: float = 5.0):
    """Stop the running program and all child processes."""
    if not self.running:
        return
    
    self.logger.info("Stopping program...")
    self.running = False
    
    if self.process:
        try:
            # Kill the entire process group
            pgid = os.getpgid(self.process.pid)
            self.logger.info(f"Terminating process group {pgid}...")
            os.killpg(pgid, signal.SIGTERM)
            
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.logger.warning("Process group did not terminate gracefully, forcing kill")
                os.killpg(pgid, signal.SIGKILL)
                self.process.wait()
        except ProcessLookupError:
            # Process already terminated
            self.logger.info("Process already terminated")
        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            # Fallback to regular terminate/kill
            try:
                self.process.terminate()
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
```

### 3. Added Required Imports
```python
import os
import signal
```

## How It Works

1. **Process Group Creation**: `os.setsid()` creates a new session and process group
2. **Group Identification**: `os.getpgid(pid)` gets the process group ID
3. **Group Termination**: `os.killpg(pgid, signal)` sends signal to ALL processes in the group
4. **Graceful → Forceful**: Try SIGTERM first, then SIGKILL if needed
5. **Fallback**: If process group operations fail, fall back to regular terminate/kill

## Testing

Created `test_process_cleanup.py` to verify the fix:
- Spawns a process with multiple children
- Verifies all processes are in the same group
- Kills the process group
- Confirms all processes are terminated

Result: ✅ All processes properly cleaned up

## Impact

This fix is **CRITICAL** for the debug/QA mode to function correctly:
- ✅ Only one copy of the program runs at a time
- ✅ Clean log file with errors from current version only
- ✅ AI sees accurate error state
- ✅ Fixes are properly tested and validated
- ✅ Debugging loop works as intended

## Files Modified

- `autonomy/pipeline/runtime_tester.py`:
  - Added `os` and `signal` imports
  - Modified `ProgramRunner.__init__()` to use `preexec_fn=os.setsid`
  - Rewrote `ProgramRunner.stop()` to kill entire process group

## Commit

```
commit 86817e2
CRITICAL FIX: Properly kill all child processes when stopping runtime tests
```