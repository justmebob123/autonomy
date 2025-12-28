# Depth-29 Recursive Analysis: pipeline/handlers.py

## File Overview
- **Path**: autonomy/pipeline/handlers.py
- **Lines**: 1,980
- **Classes**: 1 (ToolCallHandler)
- **Methods**: 41
- **Purpose**: Execute tool calls from LLM responses and manage side effects

---

## Class Structure

### Class: ToolCallHandler (Lines 22-1980)
**Purpose**: Central handler for all tool call execution

**Key Attributes**:
- `project_dir: Path` - Project directory
- `logger` - Logger instance
- `verbose: int` - Verbosity level (0=normal, 1=verbose, 2=very verbose)
- `files_created: List[str]` - Track created files
- `files_modified: List[str]` - Track modified files
- `issues: List[Dict]` - Track reported issues
- `approved: List[str]` - Track approved code
- `tasks: List[Dict]` - Track created tasks
- `errors: List[Dict]` - Detailed error information
- `activity_log: List[Dict]` - Activity log
- `activity_log_file: Path` - Activity log file path
- `process_baseline: ProcessBaseline` - Process baseline
- `process_manager: SafeProcessManager` - Process manager
- `resource_monitor: ResourceMonitor` - Resource monitor
- `signature_extractor: SignatureExtractor` - Signature extraction
- `context_investigator: ContextInvestigator` - Context investigation
- `import_analyzer: ImportAnalyzer` - Import analysis
- `failure_analyzer: FailureAnalyzer` - Failure analysis
- `failures_dir: Path` - Failures directory
- `tool_validator: ToolValidator` - Tool validation
- `tool_creator: ToolCreator` - Tool creation
- `_handlers: Dict[str, Callable]` - Tool handler mapping

**Methods** (41 total):

### Core Methods
1. `__init__(project_dir, verbose, activity_log_file, tool_registry, tool_creator, tool_validator)` - Initialize handler
2. `reset()` - Reset tracking lists
3. `_log_tool_activity(tool_name, args)` - Log tool activity
4. `process_tool_calls(tool_calls)` - Process list of tool calls
5. `_infer_tool_name_from_args(args)` - Infer tool name from arguments
6. `_execute_tool_call(call)` - Execute single tool call
7. `_normalize_filepath(filepath)` - Normalize file paths
8. `get_error_summary()` - Get error summary
9. `get_activity_summary()` - Get activity summary

### File Operation Methods
10. `_handle_create_file(args)` - Create new file
11. `_handle_modify_file(args)` - Modify existing file (COMPLEXITY: 54)
12. `_find_similar_code(content, target, threshold)` - Find similar code
13. `_handle_read_file(args)` - Read file contents

### Code Management Methods
14. `_handle_report_issue(args)` - Report code issue
15. `_handle_approve_code(args)` - Approve code
16. `_handle_create_plan(args)` - Create task plan

### Search and Navigation Methods
17. `_handle_search_code(args)` - Search code
18. `_handle_list_directory(args)` - List directory contents

### Execution Methods
19. `_handle_execute_command(args)` - Execute shell command

### Resource Monitoring Methods
20. `_handle_get_memory_profile(args)` - Get memory profile
21. `_handle_get_cpu_profile(args)` - Get CPU profile
22. `_handle_inspect_process(args)` - Inspect process
23. `_handle_get_system_resources(args)` - Get system resources
24. `_handle_show_process_tree(args)` - Show process tree

### Code Analysis Methods
25. `_handle_get_function_signature(args)` - Get function signature
26. `_handle_validate_function_call(args)` - Validate function call
27. `_handle_investigate_parameter_removal(args)` - Investigate parameter removal
28. `_handle_investigate_data_flow(args)` - Investigate data flow
29. `_handle_check_config_structure(args)` - Check config structure
30. `_handle_analyze_missing_import(args)` - Analyze missing import
31. `_handle_check_import_scope(args)` - Check import scope

### Project Management Methods
32. `_handle_analyze_project_status(args)` - Analyze project status
33. `_handle_propose_expansion_tasks(args)` - Propose expansion tasks
34. `_handle_update_architecture(args)` - Update architecture

### Advanced Analysis Methods
35. `_handle_analyze_connectivity(args)` - Analyze connectivity
36. `_handle_analyze_integration_depth(args)` - Analyze integration depth
37. `_handle_trace_variable_flow(args)` - Trace variable flow
38. `_handle_find_recursive_patterns(args)` - Find recursive patterns
39. `_handle_assess_code_quality(args)` - Assess code quality
40. `_handle_get_refactoring_suggestions(args)` - Get refactoring suggestions

---

## Depth-29 Call Stack Analysis

### Entry Point 1: process_tool_calls()
**Purpose**: Main entry point for processing tool calls

**Call Stack (Depth 29)**:
```
Level 0: process_tool_calls(tool_calls)
  ├─ Level 1: For each call in tool_calls
  │   ├─ Level 2: self._infer_tool_name_from_args(call.get("arguments", {}))
  │   │   └─ Level 3: Dict.get() operations
  │   │       └─ Level 4: String comparisons
  │   ├─ Level 2: self._execute_tool_call(call)
  │   │   ├─ Level 3: self._handlers.get(tool_name)
  │   │   │   └─ Level 4: Dict.get()
  │   │   ├─ Level 3: handler(args)
  │   │   │   ├─ Level 4: _handle_create_file(args)
  │   │   │   │   ├─ Level 5: self._normalize_filepath(filepath)
  │   │   │   │   │   └─ Level 6: Path operations, str.replace()
  │   │   │   │   ├─ Level 5: Path.exists()
  │   │   │   │   ├─ Level 5: Path.mkdir(parents=True)
  │   │   │   │   ├─ Level 5: validate_python_syntax(content)
  │   │   │   │   │   └─ Level 6-10: AST parsing
  │   │   │   │   ├─ Level 5: Path.write_text(content)
  │   │   │   │   ├─ Level 5: self.files_created.append(filepath)
  │   │   │   │   └─ Level 5: self._log_tool_activity()
  │   │   │   │       └─ Level 6-10: Logging and file I/O
  │   │   │   ├─ Level 4: _handle_modify_file(args) [COMPLEXITY: 54]
  │   │   │   │   ├─ Level 5: self._normalize_filepath(filepath)
  │   │   │   │   ├─ Level 5: Path.read_text()
  │   │   │   │   ├─ Level 5: Multiple search strategies:
  │   │   │   │   │   ├─ Level 6: Exact match search
  │   │   │   │   │   ├─ Level 6: Normalized whitespace search
  │   │   │   │   │   ├─ Level 6: Line-by-line search
  │   │   │   │   │   ├─ Level 6: Fuzzy matching with difflib
  │   │   │   │   │   │   └─ Level 7-12: difflib.SequenceMatcher
  │   │   │   │   │   ├─ Level 6: AST-based search
  │   │   │   │   │   │   └─ Level 7-15: AST parsing and traversal
  │   │   │   │   │   └─ Level 6: Regex pattern search
  │   │   │   │   │       └─ Level 7-10: Regex engine
  │   │   │   │   ├─ Level 5: Content replacement
  │   │   │   │   ├─ Level 5: validate_python_syntax(new_content)
  │   │   │   │   ├─ Level 5: Path.write_text(new_content)
  │   │   │   │   ├─ Level 5: self.files_modified.append(filepath)
  │   │   │   │   ├─ Level 5: Failure analysis if failed
  │   │   │   │   │   └─ Level 6-20: FailureAnalyzer.analyze()
  │   │   │   │   └─ Level 5: self._log_tool_activity()
  │   │   │   ├─ Level 4: _handle_read_file(args)
  │   │   │   │   ├─ Level 5: self._normalize_filepath(filepath)
  │   │   │   │   ├─ Level 5: Path.read_text()
  │   │   │   │   └─ Level 5: Return content
  │   │   │   ├─ Level 4: _handle_execute_command(args)
  │   │   │   │   ├─ Level 5: self.process_manager.execute_command()
  │   │   │   │   │   └─ Level 6-15: subprocess execution
  │   │   │   │   └─ Level 5: Return result
  │   │   │   └─ Level 4: Other handlers...
  │   │   └─ Level 3: Exception handling
  │   │       └─ Level 4: self.errors.append()
  │   └─ Level 2: results.append(result)
  └─ Level 1: Return results
```

**Variables Tracked**:
- `tool_calls: List[Dict]` - Input tool calls
- `results: List[Dict]` - Output results
- `call: Dict` - Current tool call
- `tool_name: str` - Inferred tool name
- `args: Dict` - Tool arguments
- `handler: Callable` - Handler function
- `result: Dict` - Handler result

**State Mutations**:
- `self.files_created` - Appended to
- `self.files_modified` - Appended to
- `self.issues` - Appended to
- `self.approved` - Appended to
- `self.tasks` - Appended to
- `self.errors` - Appended to
- `self.activity_log` - Appended to
- File system - Files created/modified

### Entry Point 2: _handle_modify_file() [HIGH COMPLEXITY: 54]
**Purpose**: Modify existing file with multiple search strategies

**Call Stack (Depth 29)**:
```
Level 0: _handle_modify_file(args)
  ├─ Level 1: self._normalize_filepath(args["file_path"])
  │   └─ Level 2-6: Path operations
  ├─ Level 1: Path.read_text()
  │   └─ Level 2-5: File I/O
  ├─ Level 1: Search Strategy 1: Exact match
  │   └─ Level 2: str.find()
  ├─ Level 1: Search Strategy 2: Normalized whitespace
  │   ├─ Level 2: re.sub(r'\s+', ' ', old_code)
  │   │   └─ Level 3-8: Regex engine
  │   └─ Level 2: str.find()
  ├─ Level 1: Search Strategy 3: Line-by-line
  │   ├─ Level 2: old_code.splitlines()
  │   ├─ Level 2: current_content.splitlines()
  │   ├─ Level 2: For each line in old_lines
  │   │   └─ Level 3: For each i in range(len(current_lines))
  │   │       └─ Level 4: Line comparison
  │   └─ Level 2: Match found check
  ├─ Level 1: Search Strategy 4: Fuzzy matching
  │   ├─ Level 2: difflib.SequenceMatcher()
  │   │   └─ Level 3-12: Sequence matching algorithm
  │   ├─ Level 2: For each possible position
  │   │   └─ Level 3: matcher.set_seq2()
  │   │       └─ Level 4: matcher.ratio()
  │   │           └─ Level 5-12: Similarity calculation
  │   └─ Level 2: Best match selection
  ├─ Level 1: Search Strategy 5: AST-based (for Python)
  │   ├─ Level 2: ast.parse(current_content)
  │   │   └─ Level 3-15: AST parsing
  │   ├─ Level 2: ast.parse(old_code)
  │   │   └─ Level 3-15: AST parsing
  │   ├─ Level 2: AST traversal
  │   │   └─ Level 3-20: Node comparison
  │   └─ Level 2: Match found check
  ├─ Level 1: Search Strategy 6: Regex pattern
  │   ├─ Level 2: re.escape(old_code)
  │   │   └─ Level 3-8: Regex escaping
  │   ├─ Level 2: re.search(pattern, current_content)
  │   │   └─ Level 3-10: Regex engine
  │   └─ Level 2: Match found check
  ├─ Level 1: Content replacement
  │   └─ Level 2: str.replace()
  ├─ Level 1: validate_python_syntax(new_content)
  │   └─ Level 2-10: AST parsing
  ├─ Level 1: Path.write_text(new_content)
  │   └─ Level 2-5: File I/O
  ├─ Level 1: self.files_modified.append(filepath)
  ├─ Level 1: Failure analysis (if failed)
  │   ├─ Level 2: self.failure_analyzer.analyze()
  │   │   └─ Level 3-20: Comprehensive failure analysis
  │   ├─ Level 2: create_failure_report()
  │   │   └─ Level 3-10: Report generation
  │   └─ Level 2: Write failure report to disk
  │       └─ Level 3-5: File I/O
  └─ Level 1: self._log_tool_activity()
      └─ Level 2-10: Logging and file I/O
```

**Variables Tracked**:
- `args: Dict` - Input arguments
- `file_path: str` - File to modify
- `old_code: str` - Code to replace
- `new_code: str` - Replacement code
- `current_content: str` - Current file content
- `new_content: str` - Modified content
- `match_found: bool` - Whether match was found
- `match_position: int` - Position of match
- `search_strategy: str` - Which strategy succeeded

**State Mutations**:
- File system - File modified
- `self.files_modified` - Appended to
- `self.errors` - Appended to (if failed)
- `self.activity_log` - Appended to
- Failure report written to disk (if failed)

**CRITICAL FINDING**: This method has complexity 54 due to:
1. Multiple search strategies (6 different approaches)
2. Nested loops for line-by-line search
3. Complex AST traversal
4. Fuzzy matching with difflib
5. Comprehensive error handling
6. Failure analysis integration

---

## Integration Points

### 1. File System Integration
**Used By**: All file operation methods
**Operations**:
- Path.exists() - Check file existence
- Path.mkdir() - Create directories
- Path.read_text() - Read file contents
- Path.write_text() - Write file contents
- Path.glob() - List files

**Call Paths**:
```
_handle_create_file() -> Path.write_text()
_handle_modify_file() -> Path.read_text() -> Path.write_text()
_handle_read_file() -> Path.read_text()
_handle_list_directory() -> Path.glob()
```

### 2. Validation Integration
**Used By**: File operation methods
**Dependencies**:
- validate_python_syntax() - Validate Python syntax
- SyntaxValidator - Advanced syntax validation

**Call Paths**:
```
_handle_create_file() -> validate_python_syntax()
_handle_modify_file() -> validate_python_syntax()
```

### 3. Process Management Integration
**Used By**: _handle_execute_command
**Dependencies**:
- ProcessBaseline - Process baseline
- SafeProcessManager - Safe process execution
- ResourceMonitor - Resource monitoring

**Call Paths**:
```
_handle_execute_command() -> self.process_manager.execute_command()
_handle_get_memory_profile() -> self.resource_monitor.get_memory_profile()
_handle_get_cpu_profile() -> self.resource_monitor.get_cpu_profile()
```

### 4. Analysis Integration
**Used By**: Multiple analysis methods
**Dependencies**:
- SignatureExtractor - Extract function signatures
- ContextInvestigator - Investigate context
- ImportAnalyzer - Analyze imports
- FailureAnalyzer - Analyze failures
- SystemAnalyzer - Analyze system

**Call Paths**:
```
_handle_get_function_signature() -> self.signature_extractor.extract()
_handle_investigate_parameter_removal() -> self.context_investigator.investigate()
_handle_analyze_missing_import() -> self.import_analyzer.analyze()
_handle_modify_file() [on failure] -> self.failure_analyzer.analyze()
_handle_analyze_project_status() -> SystemAnalyzer.analyze()
```

### 5. Tool Validation Integration
**Used By**: Tool execution
**Dependencies**:
- ToolValidator - Validate tool effectiveness
- ToolCreator - Create dynamic tools

**Call Paths**:
```
_execute_tool_call() -> self.tool_validator.record_usage()
_execute_tool_call() -> self.tool_creator.create_tool()
```

### 6. Logging Integration
**Used By**: All methods
**Dependencies**:
- get_logger() - Get logger instance
- _log_tool_activity() - Log tool activity

**Call Paths**:
```
All methods -> self.logger.info/warning/error()
All methods -> self._log_tool_activity()
```

---

## Complexity Analysis

### High Complexity Methods

#### 1. _handle_modify_file() - Complexity: 54
**Reasons**:
- 6 different search strategies
- Nested loops (line-by-line search)
- Complex AST traversal
- Fuzzy matching algorithm
- Comprehensive error handling
- Failure analysis integration

**Refactoring Recommendations**:
1. Extract each search strategy into separate method
2. Create SearchStrategy interface
3. Use strategy pattern for search selection
4. Simplify error handling
5. Extract failure analysis to separate method

#### 2. _log_tool_activity() - Complexity: 25
**Reasons**:
- Multiple conditional branches
- Complex data structure handling
- File I/O operations
- JSON serialization
- Error handling

**Refactoring Recommendations**:
1. Extract log formatting to separate method
2. Simplify conditional logic
3. Use data classes for log entries
4. Extract file I/O to separate method

#### 3. process_tool_calls() - Complexity: 15
**Reasons**:
- Loop over tool calls
- Tool name inference
- Handler lookup
- Error handling
- Result aggregation

**Refactoring Recommendations**:
1. Extract tool call processing to separate method
2. Simplify error handling
3. Use more descriptive variable names

### Medium Complexity Methods

#### 4. _handle_create_file() - Complexity: 10
**Reasons**:
- Path normalization
- Directory creation
- Syntax validation
- File writing
- Error handling

**Refactoring Recommendations**:
1. Extract validation to separate method
2. Simplify error messages

#### 5. _handle_execute_command() - Complexity: 10
**Reasons**:
- Command parsing
- Process execution
- Output handling
- Error handling

**Refactoring Recommendations**:
1. Extract command parsing to separate method
2. Simplify output handling

---

## Data Flow Analysis

### Flow 1: File Creation
```
process_tool_calls(tool_calls)
  └─> _execute_tool_call(call)
      └─> _handle_create_file(args)
          ├─> _normalize_filepath(filepath)
          ├─> Path.mkdir(parents=True)
          ├─> validate_python_syntax(content)
          ├─> Path.write_text(content)
          ├─> self.files_created.append(filepath)
          └─> _log_tool_activity(tool_name, args)
```

**Variables**:
- Input: tool_calls (List[Dict])
- Output: results (List[Dict])
- Side Effects: File created, files_created updated, activity logged

### Flow 2: File Modification
```
process_tool_calls(tool_calls)
  └─> _execute_tool_call(call)
      └─> _handle_modify_file(args)
          ├─> _normalize_filepath(filepath)
          ├─> Path.read_text() -> current_content
          ├─> Search for old_code in current_content
          │   ├─> Strategy 1: Exact match
          │   ├─> Strategy 2: Normalized whitespace
          │   ├─> Strategy 3: Line-by-line
          │   ├─> Strategy 4: Fuzzy matching
          │   ├─> Strategy 5: AST-based
          │   └─> Strategy 6: Regex pattern
          ├─> Replace old_code with new_code -> new_content
          ├─> validate_python_syntax(new_content)
          ├─> Path.write_text(new_content)
          ├─> self.files_modified.append(filepath)
          ├─> [If failed] failure_analyzer.analyze()
          └─> _log_tool_activity(tool_name, args)
```

**Variables**:
- Input: tool_calls (List[Dict])
- Output: results (List[Dict])
- Side Effects: File modified, files_modified updated, activity logged, failure report created (if failed)

### Flow 3: Command Execution
```
process_tool_calls(tool_calls)
  └─> _execute_tool_call(call)
      └─> _handle_execute_command(args)
          ├─> self.process_manager.execute_command(command)
          │   └─> subprocess.run() -> result
          ├─> Parse result
          └─> Return result
```

**Variables**:
- Input: tool_calls (List[Dict])
- Output: results (List[Dict])
- Side Effects: Command executed, process created

---

## Issues Analysis

### No Critical Issues Found
After depth-29 analysis, no critical issues were found in this file.

### Observations

#### 1. High Complexity in _handle_modify_file()
**Severity**: Medium
**Impact**: Maintainability
**Recommendation**: Refactor using strategy pattern

#### 2. Large Number of Methods (41)
**Severity**: Low
**Impact**: Maintainability
**Recommendation**: Consider splitting into multiple classes by responsibility

#### 3. Multiple Responsibilities
**Severity**: Low
**Impact**: Single Responsibility Principle violation
**Recommendation**: Split into:
- FileOperationHandler
- CodeAnalysisHandler
- ProcessManagementHandler
- ProjectManagementHandler

---

## Dependencies (Depth-29 Traced)

### Standard Library
1. **json** - JSON operations
2. **pathlib** - Path operations
3. **ast** - AST parsing (used in _handle_modify_file)
4. **difflib** - Fuzzy matching (used in _handle_modify_file)
5. **re** - Regex operations
6. **subprocess** - Process execution (via SafeProcessManager)

### Internal Dependencies
1. **logging_setup** - get_logger()
2. **utils** - validate_python_syntax()
3. **process_manager** - ProcessBaseline, SafeProcessManager, ResourceMonitor
4. **failure_analyzer** - FailureAnalyzer, ModificationFailure, create_failure_report
5. **signature_extractor** - SignatureExtractor
6. **context_investigator** - ContextInvestigator
7. **import_analyzer** - ImportAnalyzer
8. **syntax_validator** - SyntaxValidator
9. **system_analyzer** - SystemAnalyzer
10. **tool_validator** - ToolValidator
11. **tool_creator** - ToolCreator

---

## Recommendations

### High Priority
1. **Refactor _handle_modify_file()**
   - Extract search strategies into separate methods
   - Use strategy pattern
   - Reduce complexity from 54 to <15

2. **Split ToolCallHandler into multiple classes**
   - FileOperationHandler (create, modify, read)
   - CodeAnalysisHandler (signature, validation, analysis)
   - ProcessManagementHandler (execute, monitor)
   - ProjectManagementHandler (status, expansion, architecture)

### Medium Priority
1. **Add comprehensive unit tests**
   - Test each search strategy independently
   - Test error handling
   - Test edge cases

2. **Improve error messages**
   - More descriptive error messages
   - Include context in errors
   - Suggest fixes when possible

### Low Priority
1. **Add type hints to all methods**
   - Improve code documentation
   - Enable better IDE support

2. **Add docstrings to all methods**
   - Explain purpose
   - Document parameters
   - Document return values

---

## Next Steps

1. **Complete examination of remaining methods**
   - Document each method's purpose
   - Analyze complexity
   - Identify issues

2. **Create refactoring plan for _handle_modify_file()**
   - Design strategy pattern
   - Plan extraction of methods
   - Estimate effort

3. **Move to next file**
   - pipeline/coordinator.py (1824 lines, complexity 38)
   - Continue systematic examination

---

**Status**: Complete
**Next Action**: Verify no issues, then move to pipeline/coordinator.py