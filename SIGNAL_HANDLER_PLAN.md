# Signal Handler Implementation Plan

## Correct Key Binding

**AVOID**: Ctrl+S (used for XOFF - stops terminal output)

**USE**: Ctrl+T or Ctrl+\ or SIGUSR1

### Option 1: Ctrl+T (Recommended)
- Not commonly used in terminals
- Easy to remember (T for "status")
- Standard signal: SIGINFO (BSD) or custom handler

### Option 2: Ctrl+\ 
- Sends SIGQUIT by default
- Can be caught and handled
- Less intuitive

### Option 3: SIGUSR1
- Send via: `kill -USR1 <pid>`
- Clean, no terminal conflicts
- Requires knowing PID

## Implementation

```python
import signal
import sys

def status_handler(signum, frame):
    """Handle status request signal"""
    print("\n" + "="*70)
    print("📊 CURRENT STATUS")
    print("="*70)
    print(f"  Phase: {current_phase}")
    print(f"  Task: {current_task}")
    print(f"  Operation: {current_operation}")
    print(f"  Elapsed: {elapsed_time}")
    print("="*70 + "\n")

# Register handler
signal.signal(signal.SIGUSR1, status_handler)
```

## Usage

### From Another Terminal
```bash
# Find PID
ps aux | grep "python3 run.py"

# Send signal
kill -USR1 <pid>
```

### With Hotkey (if terminal supports)
Configure terminal to send SIGUSR1 on Ctrl+T

## Benefits
- No conflict with terminal control sequences
- Clean implementation
- Works across all terminals
- Can be triggered externally