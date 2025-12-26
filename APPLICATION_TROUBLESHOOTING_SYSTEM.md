# Application Troubleshooting System

## Overview

The Application Troubleshooting System is a comprehensive diagnostic framework designed to perform deep application-layer analysis when runtime errors occur. It goes beyond simple error detection to understand the root causes of failures through multiple analytical lenses.

## Architecture

The system consists of five core components, each analyzing different aspects of the application:

### 1. Log Analyzer (`pipeline/log_analyzer.py`)

**Purpose:** Analyzes application logs to identify error patterns and trends.

**Capabilities:**
- Extracts errors and warnings from log files
- Identifies recurring error patterns
- Builds timeline of events
- Calculates log statistics
- Searches for specific patterns

**Key Methods:**
- `analyze(log_path=None)` - Perform comprehensive log analysis
- `search_logs(pattern, case_sensitive=False)` - Search for specific patterns
- `format_report(results)` - Format results as readable report

**Example Usage:**
```python
from pipeline.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer("/path/to/project")
results = analyzer.analyze()
report = analyzer.format_report(results)
print(report)
```

### 2. Call Chain Tracer (`pipeline/call_chain_tracer.py`)

**Purpose:** Traces execution paths and identifies where errors occur in the application flow.

**Capabilities:**
- Builds call graph from Python code using AST analysis
- Traces function calls and dependencies
- Identifies critical execution paths
- Finds error-prone functions
- Analyzes import dependencies

**Key Methods:**
- `trace(entry_point=None)` - Trace call chains from entry point
- `trace_function_calls(function_name)` - Trace specific function
- `format_report(results)` - Format results as readable report

**Example Usage:**
```python
from pipeline.call_chain_tracer import CallChainTracer

tracer = CallChainTracer("/path/to/project")
results = tracer.trace()
report = tracer.format_report(results)
print(report)
```

### 3. Change History Analyzer (`pipeline/change_history_analyzer.py`)

**Purpose:** Analyzes git history to identify changes that may have introduced issues.

**Capabilities:**
- Analyzes recent git commits
- Identifies risky changes (config, server, API changes)
- Tracks file modifications
- Analyzes git blame information
- Compares commits

**Key Methods:**
- `analyze(days=7)` - Analyze recent changes
- `compare_commits(commit1, commit2)` - Compare two commits
- `format_report(results)` - Format results as readable report

**Example Usage:**
```python
from pipeline.change_history_analyzer import ChangeHistoryAnalyzer

analyzer = ChangeHistoryAnalyzer("/path/to/project")
results = analyzer.analyze(days=7)
report = analyzer.format_report(results)
print(report)
```

### 4. Configuration Investigator (`pipeline/config_investigator.py`)

**Purpose:** Investigates configuration issues in applications.

**Capabilities:**
- Finds and analyzes all configuration files
- Detects configuration issues (empty values, placeholders, hardcoded credentials)
- Analyzes environment variables
- Generates recommendations
- Investigates specific configuration keys

**Key Methods:**
- `investigate()` - Perform comprehensive configuration investigation
- `investigate_specific_config(config_key)` - Investigate specific key
- `format_report(results)` - Format results as readable report

**Example Usage:**
```python
from pipeline.config_investigator import ConfigInvestigator

investigator = ConfigInvestigator("/path/to/project")
results = investigator.investigate()
report = investigator.format_report(results)
print(report)
```

### 5. Architecture Analyzer (`pipeline/architecture_analyzer.py`)

**Purpose:** Analyzes project structure and identifies architectural issues.

**Capabilities:**
- Analyzes project structure and organization
- Identifies architectural patterns
- Detects architectural issues
- Analyzes dependencies
- Generates recommendations

**Key Methods:**
- `analyze()` - Perform comprehensive architecture analysis
- `format_report(results)` - Format results as readable report

**Example Usage:**
```python
from pipeline.architecture_analyzer import ArchitectureAnalyzer

analyzer = ArchitectureAnalyzer("/path/to/project")
results = analyzer.analyze()
report = analyzer.format_report(results)
print(report)
```

## Integration with RuntimeTester

The troubleshooting system is integrated into the `RuntimeTester` class in `pipeline/runtime_tester.py`:

### Methods Added:

1. **`perform_application_troubleshooting(working_dir)`**
   - Runs all five troubleshooting components
   - Returns comprehensive results dictionary
   - Handles errors gracefully

2. **`format_troubleshooting_report(results)`**
   - Formats all results into a single comprehensive report
   - Includes sections for each component
   - Returns formatted string

### Example Usage in RuntimeTester:

```python
from pathlib import Path
from pipeline.runtime_tester import RuntimeTester

tester = RuntimeTester(
    command="python app.py",
    working_dir=Path("/path/to/project"),
    log_file=Path("/path/to/log.txt")
)

# When an error occurs
results = tester.perform_application_troubleshooting(
    working_dir=Path("/path/to/project")
)

report = tester.format_troubleshooting_report(results)
print(report)
```

## Integration with run.py

The troubleshooting system is automatically triggered in `run.py` when:
- A process fails to start (exit code -1)
- After the diagnostic report is displayed

### Workflow:

1. Process fails to start (exit code -1)
2. Standard diagnostic report is displayed
3. Application troubleshooting phase is triggered
4. All five components run their analysis
5. Comprehensive report is displayed
6. Report is saved to `troubleshooting_report.txt`

### Command Line Usage:

```bash
# Run with debug/QA mode
python run.py /path/to/project --debug-qa --command "python app.py"

# If the process fails to start, troubleshooting will run automatically
```

## Report Structure

The comprehensive troubleshooting report includes:

1. **Log Analysis Report**
   - Log statistics (files, size, lines, error count)
   - Recent errors with context
   - Recent warnings
   - Common error patterns
   - Most problematic files

2. **Call Chain Trace Report**
   - Entry points
   - Critical execution paths (by type)
   - Error-prone functions with risk scores
   - Import dependencies

3. **Change History Report**
   - Recent commits
   - Most changed files
   - Potentially risky changes
   - Recent contributors

4. **Configuration Investigation Report**
   - Configuration files found
   - Environment variables
   - Configuration issues
   - Recommendations

5. **Architecture Analysis Report**
   - Project structure
   - Identified patterns
   - Architectural issues
   - Dependencies
   - Recommendations

## Benefits

1. **Comprehensive Analysis:** Examines multiple aspects of the application simultaneously
2. **Root Cause Identification:** Goes beyond symptoms to find underlying issues
3. **Actionable Insights:** Provides specific recommendations for fixes
4. **Historical Context:** Considers recent changes that may have introduced issues
5. **Configuration Validation:** Identifies configuration problems that may cause failures
6. **Architectural Understanding:** Ensures the application structure supports its goals

## Future Enhancements

Potential improvements for future versions:

1. **Machine Learning Integration:** Learn from past errors to predict future issues
2. **Automated Fix Suggestions:** Generate code patches for common issues
3. **Performance Analysis:** Add performance profiling capabilities
4. **Security Analysis:** Identify security vulnerabilities
5. **Dependency Analysis:** Analyze external dependencies for issues
6. **Test Coverage Analysis:** Identify untested code paths
7. **Documentation Analysis:** Check for missing or outdated documentation

## Troubleshooting the Troubleshooter

If the troubleshooting system itself encounters errors:

1. Check that all required dependencies are installed
2. Verify that the project directory is accessible
3. Ensure git is available (for change history analysis)
4. Check that log files are readable
5. Verify that Python files can be parsed (for call chain tracing)

Common issues:
- **Git not available:** Change history analysis will be skipped
- **No log files found:** Log analysis will report no logs
- **Parse errors:** Some Python files may be skipped in call chain tracing
- **Permission errors:** Ensure read access to all project files

## Contributing

To add new troubleshooting components:

1. Create a new analyzer class in `pipeline/`
2. Implement `analyze()` and `format_report()` methods
3. Add to `RuntimeTester.perform_application_troubleshooting()`
4. Update this documentation

## License

Part of the Autonomy AI Development Pipeline system.