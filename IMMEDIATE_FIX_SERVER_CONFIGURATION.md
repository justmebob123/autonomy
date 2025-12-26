# Immediate Fix: Server Configuration Error

## Problem Analysis

### Error in Logs
```
2025-12-25 22:36:51,991 - src.execution.server_pool - INFO -   ollama01: 0 models at None
2025-12-25 22:36:51,991 - src.execution.server_pool - INFO -   ollama02: 0 models at None
2025-12-25 22:36:52,175 - src.work_queue.server_selector - ERROR - No available servers found
2025-12-25 22:36:52,176 - src.work_queue.work_queue - ERROR - No available server for job bbb6fb9e
```

### Root Cause
The application is loading servers but they have:
- **0 models** - No models configured
- **URL: None** - No server URLs configured

This means the configuration is incomplete or not being loaded properly.

### Investigation Path

1. **Check config.yaml** - Does it have server definitions?
2. **Check servers.yaml** - Does this file exist? (Log says "servers.yaml not found")
3. **Check recent patches** - Did we break server configuration?
4. **Trace code** - How does ServerPool load servers?

## Immediate Actions

### Action 1: Examine Configuration Files

**Check what's in the project:**
```bash
cd /home/ai/AI/my_project
cat config.yaml | grep -A 20 "servers:"
ls -la servers.yaml  # Does it exist?
```

### Action 2: Check Recent Patches

**Look for server-related changes:**
```bash
cd /home/ai/AI/my_project
find . -name ".patch" -type d
ls -la .patch/*.diff | grep -i server
```

### Action 3: Trace Server Loading Code

**Files to examine:**
1. `src/execution/server_pool.py` - ServerPool initialization
2. `src/core/config_manager.py` - Configuration loading
3. `src/work_queue/server_selector.py` - Server selection
4. `src/main.py` - How servers are passed to components

### Action 4: Compare with Working System

**The autonomy system itself uses servers successfully:**
```
22:01:43 [INFO]   ✓ ollama01 (ollama01.thiscluster.net): 8 models
22:01:43 [INFO]   ✓ ollama02 (ollama02.thiscluster.net): 15 models
```

**Check autonomy's config:**
```bash
cd /home/ai/AI/autonomy
cat pipeline/config.py | grep -A 10 "servers"
```

## Expected Fix

Based on the logs, the fix will likely be ONE of:

### Option A: Create servers.yaml
```yaml
# /home/ai/AI/my_project/servers.yaml
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
    models:
      - qwen2.5-coder:32b
      - qwen2.5-coder:14b
      - phi4
      - qwen2.5:14b
  
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
    models:
      - qwen2.5-coder:32b
      - deepseek-coder-v2
      - qwen2.5:14b
      - llama3.1:70b
```

### Option B: Fix config.yaml
```yaml
# /home/ai/AI/my_project/config.yaml
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
```

### Option C: Fix Code to Load Servers Properly
If the config files are correct but not being loaded, fix the loading code.

## Tools Needed for Investigation

### Existing Tools (Can Use Now)
1. `read_file` - Read config files
2. `search_code` - Find server-related code
3. `list_directory` - Check for .patch directory
4. `execute_command` - Run grep/find commands

### New Tools (Need to Create)
1. `parse_yaml_config` - Parse YAML with validation
2. `trace_config_loading` - Follow config loading code
3. `compare_configs` - Compare working vs. broken config
4. `analyze_patch_impact` - See what patches changed

## Recommended Approach

### Step 1: Quick Manual Fix (5 minutes)
1. Check if servers.yaml exists
2. If not, create it with proper server definitions
3. Restart application
4. Verify servers load correctly

### Step 2: Understand Root Cause (15 minutes)
1. Read server_pool.py to understand loading logic
2. Check config_manager.py for configuration parsing
3. Review recent patches for server-related changes
4. Document what broke and why

### Step 3: Implement Proper Fix (30 minutes)
1. Fix the root cause (not just symptoms)
2. Add validation to prevent this in future
3. Update documentation
4. Create test to catch this error

### Step 4: Implement Troubleshooting Phase (Long-term)
1. Create tools for log analysis
2. Create tools for call chain tracing
3. Create tools for patch analysis
4. Automate this entire investigation process

## Testing the Fix

### Verification Steps
1. **Check logs** - Should see:
   ```
   ollama01: 8 models at http://ollama01.thiscluster.net:11434
   ollama02: 15 models at http://ollama02.thiscluster.net:11434
   ```

2. **Check server selection** - Should NOT see:
   ```
   ERROR - No available servers found
   ```

3. **Check job execution** - Jobs should be assigned to servers

4. **Monitor for 10 minutes** - Ensure no recurring errors

## Prevention

### Add Validation
```python
# In server_pool.py
def validate_server_config(server):
    if not server.get('url'):
        raise ValueError(f"Server {server['name']} missing URL")
    if not server.get('models'):
        logger.warning(f"Server {server['name']} has no models configured")
```

### Add Configuration Schema
```yaml
# schema.yaml
server:
  type: object
  required: [name, url]
  properties:
    name:
      type: string
    url:
      type: string
      pattern: "^https?://"
    models:
      type: array
      items:
        type: string
```

### Add Startup Checks
```python
# In main.py
def validate_configuration():
    """Validate configuration before starting"""
    if not servers:
        raise ConfigurationError("No servers configured")
    for server in servers:
        if not server.url:
            raise ConfigurationError(f"Server {server.name} missing URL")
```

## Next Steps

1. **IMMEDIATE**: Manually fix the configuration (Option A or B)
2. **SHORT-TERM**: Understand and document root cause
3. **MEDIUM-TERM**: Add validation and tests
4. **LONG-TERM**: Implement Application Troubleshooting Phase

This error is a perfect example of why we need the Application Troubleshooting Phase - it would have automatically:
1. Parsed the logs
2. Identified the configuration issue
3. Traced the code
4. Checked patches
5. Proposed the fix
6. Implemented and verified

All in under 5 minutes instead of requiring manual investigation.