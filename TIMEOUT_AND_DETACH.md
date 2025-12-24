# Timeout and Detach Mode Features

## Overview

The debug/QA mode now supports extended monitoring and detach mode for better handling of successful test runs.

## Features

### 1. Success Timeout (Extended Monitoring)

**Problem**: The initial test duration (default 300 seconds) might not be long enough to catch intermittent errors.

**Solution**: Use `--success-timeout` to extend monitoring after the initial test duration passes without errors.

**Usage**:
```bash
./run.py ~/project --debug-qa --command "python app.py" --test-duration 300 --success-timeout 600
```

**Behavior**:
- Initial monitoring runs for `--test-duration` seconds (default: 300)
- If no errors found, monitoring extends for additional time up to `--success-timeout` (default: 600)
- If errors appear during extended monitoring, they are processed normally
- If no errors found after extended monitoring, the program exits successfully

**Example**:
```bash
# Monitor for 5 minutes initially, extend to 10 minutes if successful
./run.py ~/project --debug-qa --command "python app.py" --test-duration 300 --success-timeout 600

# Monitor for 2 minutes initially, extend to 5 minutes if successful
./run.py ~/project --debug-qa --command "python app.py" --test-duration 120 --success-timeout 300
```

### 2. Detach Mode

**Problem**: No way to exit the debug/QA mode if the program runs successfully, forcing you to wait or manually interrupt.

**Solution**: Use `--detach` to exit immediately when tests pass, leaving the program running in the background.

**Usage**:
```bash
./run.py ~/project --debug-qa --command "python app.py" --detach
```

**Behavior**:
- Monitors for errors during the initial test duration
- If no errors found, prints success message and exits immediately
- Leaves the program running in the background
- Provides a command to stop the background process

**Example Output**:
```
✅ No runtime errors detected in 300 seconds

🎉 All tests passed!
✅ Program is running successfully
🔓 Detaching - program will continue running in background

To stop the program, use: pkill -f 'python app.py'
```

## Combining Features

You can combine both features for flexible monitoring:

```bash
# Quick check with detach
./run.py ~/project --debug-qa --command "python app.py" --test-duration 60 --detach

# Extended monitoring without detach (wait for full duration)
./run.py ~/project --debug-qa --command "python app.py" --test-duration 300 --success-timeout 900

# Extended monitoring with detach (exit if successful after initial duration)
./run.py ~/project --debug-qa --command "python app.py" --test-duration 300 --success-timeout 600 --detach
```

## Use Cases

### Development Workflow
```bash
# Quick validation before committing
./run.py ~/project --debug-qa --command "python app.py" --test-duration 60 --detach
```

### CI/CD Pipeline
```bash
# Thorough testing with extended monitoring
./run.py ~/project --debug-qa --command "python app.py" --test-duration 300 --success-timeout 900
```

### Long-Running Services
```bash
# Start service and detach if successful
./run.py ~/project --debug-qa --command "python server.py" --test-duration 120 --detach
```

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--test-duration` | int | 300 | Initial monitoring duration in seconds |
| `--success-timeout` | int | 600 | Extended monitoring duration if no errors found |
| `--detach` | flag | false | Exit immediately on success, leave program running |

## Notes

- If `--success-timeout` is less than or equal to `--test-duration`, no extended monitoring occurs
- Detach mode takes precedence over extended monitoring
- The background process must be manually stopped using the provided command
- Extended monitoring will stop if the program exits or if errors are detected