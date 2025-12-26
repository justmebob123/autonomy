# Application Troubleshooting Phase - Comprehensive Proposal

## Executive Summary

We need a new phase that goes beyond syntax/import debugging to perform **deep application-layer troubleshooting**. This phase will analyze custom application errors, trace call chains through multiple files, review change history, and understand architectural intent from MASTER_PLAN.md.

## Current Problem (Real Example)

**Log Error:**
```
2025-12-25 22:36:51,991 - src.execution.server_pool - INFO -   ollama01: 0 models at None
2025-12-25 22:36:51,991 - src.execution.server_pool - INFO -   ollama02: 0 models at None
2025-12-25 22:36:52,175 - src.work_queue.server_selector - ERROR - No available servers found
2025-12-25 22:36:52,176 - src.work_queue.work_queue - ERROR - No available server for job bbb6fb9e
```

**What We Need:**
1. Parse "0 models at None" - servers not configured with URLs
2. Trace back: work_queue → server_selector → server_pool → config loading
3. Find where server URLs should come from (config.yaml? servers.yaml?)
4. Check recent patches - did we break server configuration?
5. Review MASTER_PLAN.md - what's the intended architecture?
6. Fix the root cause, not just the symptom

## Phase Design: APPLICATION_TROUBLESHOOTING

### Phase Characteristics

**Name:** Application Troubleshooting Phase  
**Priority:** Between DEBUG and DEVELOPMENT  
**Trigger:** Custom application errors in logs (not Python exceptions)  
**Duration:** Extended (may require 30+ tool calls)  
**Complexity:** High - requires understanding application architecture

### Core Capabilities

#### 1. Log Analysis & Pattern Recognition
- Parse custom log formats
- Identify error patterns (not just Python tracebacks)
- Extract structured information (timestamps, modules, error codes)
- Detect cascading failures
- Recognize configuration errors vs. code errors

#### 2. Call Chain Tracing
- Start from error location
- Trace backwards through imports and function calls
- Build complete call graph
- Identify all files involved
- Map data flow through the chain

#### 3. Change History Analysis
- Read patch files from `.patch/` directory
- Correlate patches with current errors
- Identify when functionality broke
- Compare before/after states
- Suggest rollback candidates

#### 4. Configuration Investigation
- Parse YAML/JSON/INI config files
- Understand configuration schema
- Detect missing or invalid values
- Trace configuration loading code
- Identify configuration dependencies

#### 5. Architectural Understanding
- Read MASTER_PLAN.md for intended design
- Compare actual vs. intended architecture
- Identify architectural violations
- Understand component relationships
- Detect design pattern issues

### Tools Required (20+ New Tools)

#### Log Analysis Tools (5)
1. **`parse_application_log`** - Parse custom log formats
   - Input: log file path, format pattern
   - Output: structured log entries
   
2. **`extract_error_patterns`** - Find error patterns in logs
   - Input: log entries, error keywords
   - Output: grouped errors with frequencies
   
3. **`trace_log_timeline`** - Build timeline of events
   - Input: log entries, time range
   - Output: chronological event sequence
   
4. **`correlate_log_errors`** - Find related errors
   - Input: primary error, log entries
   - Output: cascading/related errors
   
5. **`analyze_log_context`** - Get context around error
   - Input: error line, context size
   - Output: surrounding log entries

#### Call Chain Tools (5)
6. **`build_call_graph`** - Create call graph from code
   - Input: starting file/function
   - Output: complete call graph
   
7. **`trace_import_chain`** - Follow import dependencies
   - Input: starting module
   - Output: import dependency tree
   
8. **`find_function_callers`** - Find who calls a function
   - Input: function name, project path
   - Output: all call sites
   
9. **`trace_data_flow`** - Follow data through code
   - Input: variable name, starting point
   - Output: data flow path
   
10. **`analyze_execution_path`** - Determine execution path
    - Input: entry point, conditions
    - Output: possible execution paths

#### Change History Tools (4)
11. **`list_patch_files`** - List patches in `.patch/`
    - Input: project path, date range
    - Output: patch file list with metadata
    
12. **`analyze_patch_file`** - Parse patch file
    - Input: patch file path
    - Output: changed files, lines, context
    
13. **`correlate_patch_to_error`** - Match patch to error
    - Input: error location, patch files
    - Output: relevant patches with confidence
    
14. **`suggest_rollback`** - Recommend rollback
    - Input: error, patches
    - Output: patches to revert with reasoning

#### Configuration Tools (3)
15. **`parse_config_file`** - Parse YAML/JSON/INI
    - Input: config file path
    - Output: structured configuration
    
16. **`validate_config_schema`** - Check config validity
    - Input: config data, schema
    - Output: validation errors
    
17. **`trace_config_usage`** - Find where config is used
    - Input: config key, project path
    - Output: code locations using config

#### Architecture Tools (3)
18. **`parse_master_plan`** - Extract architecture from MASTER_PLAN.md
    - Input: MASTER_PLAN.md path
    - Output: component map, relationships
    
19. **`compare_architecture`** - Compare actual vs. intended
    - Input: actual code structure, MASTER_PLAN
    - Output: deviations, violations
    
20. **`suggest_architectural_fix`** - Recommend fixes
    - Input: error, architecture analysis
    - Output: fix strategy aligned with design

### Workflow

```
1. DETECT APPLICATION ERROR
   ↓
2. PARSE LOG & EXTRACT ERROR
   - parse_application_log
   - extract_error_patterns
   - analyze_log_context
   ↓
3. UNDERSTAND ARCHITECTURE
   - parse_master_plan
   - Read relevant documentation
   ↓
4. TRACE CALL CHAIN
   - build_call_graph
   - trace_import_chain
   - find_function_callers
   ↓
5. ANALYZE CONFIGURATION
   - parse_config_file
   - validate_config_schema
   - trace_config_usage
   ↓
6. CHECK CHANGE HISTORY
   - list_patch_files
   - analyze_patch_file
   - correlate_patch_to_error
   ↓
7. SYNTHESIZE FINDINGS
   - Identify root cause
   - Understand why it broke
   - Determine correct fix
   ↓
8. PROPOSE FIX
   - suggest_architectural_fix
   - Create detailed fix plan
   - Explain reasoning
   ↓
9. IMPLEMENT FIX
   - Apply changes
   - Update configuration
   - Test thoroughly
   ↓
10. VERIFY FIX
    - Re-run application
    - Check logs for errors
    - Confirm resolution
```

### Integration with Existing System

#### Trigger Conditions
- Custom application errors in logs (not Python exceptions)
- Configuration errors
- "No available servers" type errors
- Architectural violations
- Cascading failures

#### Priority
- Runs AFTER debugging phase
- Runs BEFORE development phase
- Can be triggered manually
- Automatic on certain error patterns

#### Coordination
- Shares findings with DEBUG phase
- Provides context to DEVELOPMENT phase
- Updates MASTER_PLAN.md if needed
- Creates patches in `.patch/` directory

### Example: Solving the Server Configuration Error

**Step 1: Parse Log**
```python
parse_application_log("/path/to/autonomous.log")
# Finds: "ollama01: 0 models at None"
# Finds: "No available servers found"
```

**Step 2: Extract Error Pattern**
```python
extract_error_patterns(log_entries, ["server", "model", "None"])
# Pattern: Server initialization with null URLs
# Frequency: 2 servers affected
```

**Step 3: Understand Architecture**
```python
parse_master_plan("pipeline_docs/MASTER_PLAN.md")
# Expected: Servers should load from config.yaml or servers.yaml
# Expected: Each server should have URL and models list
```

**Step 4: Trace Call Chain**
```python
build_call_graph("src/execution/server_pool.py", "ServerPool.__init__")
# Chain: main.py → JobExecutor → ServerPool → load_servers()
# Config loaded in: src/core/config_manager.py
```

**Step 5: Analyze Configuration**
```python
parse_config_file("config.yaml")
# Found: servers section exists but URLs are missing
# Found: servers.yaml mentioned but file doesn't exist
```

**Step 6: Check Change History**
```python
list_patch_files(".patch/", last_7_days)
# Found: patch_20241225_server_config.diff
# Changed: config.yaml server section

analyze_patch_file(".patch/patch_20241225_server_config.diff")
# Removed: server URLs
# Reason: Refactoring to use servers.yaml
# Problem: servers.yaml was never created!
```

**Step 7: Synthesize**
```
ROOT CAUSE: Recent refactoring moved server config to servers.yaml
            but the file was never created. System falls back to
            config.yaml which now has incomplete server definitions.

FIX: Either:
  A) Create servers.yaml with proper server definitions
  B) Restore server URLs in config.yaml
  C) Update code to handle missing servers.yaml gracefully
```

**Step 8: Propose Fix**
```python
suggest_architectural_fix(error, architecture, patches)
# Recommendation: Option A - Create servers.yaml
# Reasoning: Aligns with MASTER_PLAN.md refactoring goal
# Template: Provide servers.yaml template with ollama01/ollama02
```

**Step 9: Implement**
```yaml
# Create servers.yaml
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
    models: [qwen2.5-coder:32b, phi4, ...]
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
    models: [qwen2.5-coder:32b, deepseek-coder-v2, ...]
```

**Step 10: Verify**
```
Re-run application
Check logs: "ollama01: 8 models at http://ollama01..."
Success: Servers properly configured
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- Create ApplicationTroubleshootingPhase class
- Implement log parsing tools (5 tools)
- Basic error pattern recognition
- Integration with existing pipeline

### Phase 2: Call Chain Analysis (Week 1)
- Implement call graph tools (5 tools)
- AST-based analysis
- Import chain tracing
- Data flow analysis

### Phase 3: Change History (Week 2)
- Implement patch analysis tools (4 tools)
- Patch file parsing
- Correlation algorithms
- Rollback suggestions

### Phase 4: Configuration & Architecture (Week 2)
- Implement config tools (3 tools)
- Implement architecture tools (3 tools)
- MASTER_PLAN.md parsing
- Schema validation

### Phase 5: Integration & Testing (Week 3)
- Full pipeline integration
- End-to-end testing
- Documentation
- Performance optimization

## Expected Benefits

1. **Faster Root Cause Identification**: 10x faster than manual investigation
2. **Architectural Alignment**: Fixes respect intended design
3. **Change Awareness**: Understands what broke and why
4. **Comprehensive Analysis**: Examines logs, code, config, and history
5. **Intelligent Fixes**: Proposes solutions based on full context

## Success Metrics

- **Time to Root Cause**: < 5 minutes (vs. 30+ minutes manual)
- **Fix Accuracy**: 90%+ fixes address root cause
- **Architectural Compliance**: 95%+ fixes align with MASTER_PLAN
- **False Positives**: < 5% incorrect diagnoses

## Next Steps

1. Review and approve this proposal
2. Prioritize tool implementation order
3. Begin Phase 1 implementation
4. Test with real application errors
5. Iterate based on results

This phase will transform the system from a code debugger into a true **application troubleshooter** that understands your entire system architecture.