# Process Awareness and Debugging Tools Requirements

## Critical Issue Identified

**Problem**: The system killed its own monitoring process because it lacked awareness of:
1. Its own process ID and process group
2. Which processes existed before it started
3. Which processes it spawned vs. pre-existing processes
4. Process relationships and hierarchies

## Required Capabilities

### 1. Process Awareness
The system must maintain awareness of:
- Its own PID and PGID
- Parent process information
- Child processes it spawns
- Pre-existing processes (baseline)
- Process relationships and hierarchies

### 2. Resource Monitoring
The system needs tools to monitor:
- Memory usage (per process and total)
- CPU time and utilization
- I/O operations
- Network connections
- File descriptors
- Thread counts

### 3. Debugging Tools
Each phase should have access to:
- Process inspection tools
- Memory profiling tools
- CPU profiling tools
- Stack trace inspection
- Log file analysis
- System resource monitoring

## Implementation Plan

### Phase 1: Process Tracking System

#### A. Process Baseline Capture
```python
class ProcessBaseline:
    """Capture system state before starting work"""
    
    def __init__(self):
        self.own_pid = os.getpid()
        self.own_pgid = os.getpgid(self.own_pid)
        self.parent_pid = os.getppid()
        self.baseline_processes = self._capture_processes()
        self.spawned_processes = set()
    
    def _capture_processes(self):
        """Capture all current processes"""
        # Get all PIDs and their info
        pass
    
    def is_own_process(self, pid):
        """Check if PID belongs to our process tree"""
        pass
    
    def is_spawned_process(self, pid):
        """Check if we spawned this process"""
        pass
    
    def get_safe_to_kill(self):
        """Get processes safe to kill (spawned by us)"""
        pass
```

#### B. Process Group Management
```python
class ProcessGroupManager:
    """Manage process groups safely"""
    
    def __init__(self, baseline: ProcessBaseline):
        self.baseline = baseline
        self.managed_groups = set()
    
    def create_process_group(self):
        """Create a new process group for spawned processes"""
        pass
    
    def kill_managed_group(self, pgid):
        """Kill only managed process groups"""
        if pgid == self.baseline.own_pgid:
            raise ValueError("Cannot kill own process group!")
        pass
    
    def cleanup_all(self):
        """Clean up all managed process groups"""
        pass
```

### Phase 2: Resource Monitoring Tools

#### A. Memory Profiling Tool
```python
{
    "type": "function",
    "function": {
        "name": "get_memory_profile",
        "description": "Get memory usage profile for processes",
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "Process ID (optional, defaults to all)"
                },
                "include_children": {
                    "type": "boolean",
                    "description": "Include child processes"
                }
            }
        }
    }
}
```

#### B. CPU Profiling Tool
```python
{
    "type": "function",
    "function": {
        "name": "get_cpu_profile",
        "description": "Get CPU usage and time for processes",
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "Process ID (optional)"
                },
                "duration": {
                    "type": "integer",
                    "description": "Sampling duration in seconds"
                }
            }
        }
    }
}
```

#### C. Process Inspector Tool
```python
{
    "type": "function",
    "function": {
        "name": "inspect_process",
        "description": "Get detailed information about a process",
        "parameters": {
            "type": "object",
            "required": ["pid"],
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "Process ID to inspect"
                },
                "include_threads": {
                    "type": "boolean",
                    "description": "Include thread information"
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include open file descriptors"
                }
            }
        }
    }
}
```

#### D. System Resource Monitor
```python
{
    "type": "function",
    "function": {
        "name": "get_system_resources",
        "description": "Get overall system resource usage",
        "parameters": {
            "type": "object",
            "properties": {
                "metrics": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["cpu", "memory", "disk", "network"]
                    },
                    "description": "Which metrics to retrieve"
                }
            }
        }
    }
}
```

### Phase 3: Debugging Tools

#### A. Stack Trace Tool
```python
{
    "type": "function",
    "function": {
        "name": "get_stack_trace",
        "description": "Get stack trace for a running process",
        "parameters": {
            "type": "object",
            "required": ["pid"],
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "Process ID"
                },
                "all_threads": {
                    "type": "boolean",
                    "description": "Get traces for all threads"
                }
            }
        }
    }
}
```

#### B. Log Analysis Tool
```python
{
    "type": "function",
    "function": {
        "name": "analyze_logs",
        "description": "Analyze log files for patterns and errors",
        "parameters": {
            "type": "object",
            "required": ["log_file"],
            "properties": {
                "log_file": {
                    "type": "string",
                    "description": "Path to log file"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for"
                },
                "last_n_lines": {
                    "type": "integer",
                    "description": "Analyze last N lines"
                }
            }
        }
    }
}
```

#### C. Process Tree Visualizer
```python
{
    "type": "function",
    "function": {
        "name": "show_process_tree",
        "description": "Show process tree starting from a PID",
        "parameters": {
            "type": "object",
            "properties": {
                "root_pid": {
                    "type": "integer",
                    "description": "Root process (defaults to current)"
                },
                "depth": {
                    "type": "integer",
                    "description": "Tree depth to show"
                }
            }
        }
    }
}
```

## Tool Availability by Phase

### All Phases Should Have:
- `inspect_process` - Inspect any process
- `get_memory_profile` - Check memory usage
- `get_cpu_profile` - Check CPU usage
- `get_system_resources` - Overall system state
- `show_process_tree` - Visualize process relationships

### Debugging Phase Additional Tools:
- `get_stack_trace` - Debug running processes
- `analyze_logs` - Parse log files
- `attach_debugger` - Attach to running process (advanced)

## Safety Mechanisms

### 1. Process Protection
```python
class ProcessProtection:
    """Prevent killing critical processes"""
    
    PROTECTED_PIDS = set()
    
    @classmethod
    def protect(cls, pid):
        """Mark a PID as protected"""
        cls.PROTECTED_PIDS.add(pid)
    
    @classmethod
    def is_protected(cls, pid):
        """Check if PID is protected"""
        return pid in cls.PROTECTED_PIDS
    
    @classmethod
    def safe_kill(cls, pid, signal=signal.SIGTERM):
        """Kill only if not protected"""
        if cls.is_protected(pid):
            raise ValueError(f"Cannot kill protected process {pid}")
        os.kill(pid, signal)
```

### 2. Process Group Protection
```python
class ProcessGroupProtection:
    """Prevent killing own process group"""
    
    def __init__(self):
        self.own_pgid = os.getpgid(os.getpid())
        self.protected_pgids = {self.own_pgid}
    
    def safe_killpg(self, pgid, signal=signal.SIGTERM):
        """Kill process group only if not protected"""
        if pgid in self.protected_pgids:
            raise ValueError(f"Cannot kill protected process group {pgid}")
        os.killpg(pgid, signal)
```

## Implementation Priority

### Critical (Immediate):
1. ✅ Process baseline capture
2. ✅ Own process protection
3. ✅ Process group management
4. ✅ Safe kill operations

### High Priority:
1. Memory profiling tool
2. CPU profiling tool
3. Process inspector tool
4. System resource monitor

### Medium Priority:
1. Stack trace tool
2. Log analysis tool
3. Process tree visualizer

### Low Priority:
1. Advanced debugging tools
2. Performance profiling
3. Network monitoring

## Testing Requirements

### Test Cases:
1. ✅ System doesn't kill its own process
2. ✅ System doesn't kill parent process
3. ✅ System only kills spawned processes
4. ✅ Process groups are properly isolated
5. Memory profiling returns accurate data
6. CPU profiling returns accurate data
7. Process inspection works for all processes
8. System resources are monitored correctly

## Usage Examples

### Example 1: Check Memory Before/After
```python
# Before operation
before = get_memory_profile()

# Do work
run_tests()

# After operation
after = get_memory_profile()

# Compare
memory_increase = after['total'] - before['total']
if memory_increase > threshold:
    report_issue("Memory leak detected")
```

### Example 2: Monitor CPU Usage
```python
# Start monitoring
cpu_before = get_cpu_profile(duration=5)

# Run operation
execute_code()

# Check CPU usage
cpu_after = get_cpu_profile(duration=5)

if cpu_after['usage'] > 90:
    report_issue("High CPU usage detected")
```

### Example 3: Inspect Hung Process
```python
# Process seems hung
if not is_responding(pid):
    # Get stack trace
    trace = get_stack_trace(pid, all_threads=True)
    
    # Analyze
    if "lock" in trace:
        report_issue("Deadlock detected")
```

## Conclusion

The system needs comprehensive process awareness and debugging tools to:
1. Avoid killing its own processes
2. Monitor resource usage
3. Debug issues effectively
4. Provide visibility into system state

This should be implemented as a high priority to prevent the critical issue of self-termination.