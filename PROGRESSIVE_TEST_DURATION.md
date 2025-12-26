# Progressive Test Duration Feature

## Overview

The autonomy system now includes a progressive test duration feature that automatically increases the test duration when no errors are found, allowing for increasingly thorough testing up to 48 hours.

## How It Works

### Initial State
- Starts with default test duration (5 minutes / 300 seconds)
- Can be customized with `--test-duration` argument

### Progressive Increase
When no errors are detected:
1. **First success**: Test duration doubles to 10 minutes
2. **Second success**: Test duration doubles to 20 minutes
3. **Third success**: Test duration doubles to 40 minutes
4. **Fourth success**: Test duration doubles to 1.3 hours
5. **Continues doubling** until reaching maximum of 48 hours

### Reset on Error
- If any error is detected, the counter resets
- Test duration returns to initial value (5 minutes)
- Progressive testing starts over from the beginning

## Usage Examples

### Basic Usage (Default 5 Minutes)
```bash
python3 run.py --debug-qa --command "./myapp" /path/to/project
```

### Custom Initial Duration (Start with 10 Minutes)
```bash
python3 run.py --debug-qa --test-duration 600 --command "./myapp" /path/to/project
```

### With Auto-Detection
```bash
python3 run.py --debug-qa /path/to/project
# Command auto-detected, progressive testing enabled
```

## Example Output

### First Success (5 Minutes)
```
✅ No runtime errors detected in 301 seconds

📈 Progressive Testing Success!
   Consecutive successes: 1
   Next test duration: 600 seconds
   (Will continue doubling until reaching 48 hours)
```

### Second Success (10 Minutes)
```
✅ No runtime errors detected in 602 seconds

📈 Progressive Testing Success!
   Consecutive successes: 2
   Next test duration: 1200 seconds
   (Will continue doubling until reaching 48 hours)
```

### After Multiple Successes (Hours)
```
✅ No runtime errors detected in 4803 seconds

📈 Progressive Testing Success!
   Consecutive successes: 5
   Next test duration: 2.7 hours
   (Will continue doubling until reaching 48 hours)
```

### Maximum Reached (48 Hours)
```
✅ No runtime errors detected in 172801 seconds

🏆 Maximum test duration reached (48 hours)
   Consecutive successes: 10
```

## Benefits

1. **Thorough Testing**: Automatically increases test coverage over time
2. **Catches Rare Bugs**: Long-running tests can expose timing issues, memory leaks, race conditions
3. **Confidence Building**: Each successful iteration builds confidence in stability
4. **Automatic**: No manual intervention required
5. **Smart Reset**: Returns to quick iterations when errors are found

## Duration Progression Table

| Success # | Duration | Time |
|-----------|----------|------|
| 0 (start) | 300s | 5 minutes |
| 1 | 600s | 10 minutes |
| 2 | 1,200s | 20 minutes |
| 3 | 2,400s | 40 minutes |
| 4 | 4,800s | 1.3 hours |
| 5 | 9,600s | 2.7 hours |
| 6 | 19,200s | 5.3 hours |
| 7 | 38,400s | 10.7 hours |
| 8 | 76,800s | 21.3 hours |
| 9 | 153,600s | 42.7 hours |
| 10+ | 172,800s | 48 hours (max) |

## Implementation Details

### Variables Tracked
- `consecutive_successes`: Number of successful tests in a row
- `current_test_duration`: Current test duration (doubles on success)
- `max_test_duration`: Maximum duration (48 hours = 172,800 seconds)

### Reset Conditions
- Any runtime error detected
- Any syntax error found
- Any import error found
- Program crashes

## Best Practices

1. **Start Small**: Use default 5-minute initial duration
2. **Monitor Progress**: Watch for patterns in when errors appear
3. **Use Detach**: For long tests, use `--detach` to free terminal
4. **Combine with CI**: Integrate into CI/CD for automated long-running tests
5. **Review Logs**: Check logs after long tests for warnings