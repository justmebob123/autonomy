"""
System Analyzer Tool Specifications

Tool definitions for the integrated system analyzer.
"""

SYSTEM_ANALYZER_TOOLS = [
    {
        "name": "analyze_connectivity",
        "description": """Analyze the polytopic connectivity of the Autonomy system.
        
Returns comprehensive connectivity metrics including:
- Total vertices and edges
- Connectivity percentage
- Average reachability
- Critical vertices (hubs, bridges, sinks)
- Isolated phases
- Recommendations for improvement

Use this tool when:
- Investigating system architecture issues
- Planning refactoring efforts
- Debugging phase transition problems
- Validating polytopic structure
- Optimizing phase navigation""",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "analyze_integration_depth",
        "description": """Analyze integration depth for a specific phase.

Returns integration metrics including:
- Relative and absolute imports
- Method calls to other subsystems
- Tool calls
- Total integration points
- Complexity level assessment

Use this tool when:
- Assessing phase coupling
- Planning refactoring
- Investigating performance issues
- Validating architecture changes
- Identifying integration bottlenecks""",
        "parameters": {
            "type": "object",
            "properties": {
                "phase_name": {
                    "type": "string",
                    "description": "Name of the phase to analyze (e.g., 'debugging', 'coding')"
                }
            },
            "required": ["phase_name"]
        }
    },
    {
        "name": "trace_variable_flow",
        "description": """Trace how a variable flows through the system.

Returns flow information including:
- Number of functions the variable flows through
- List of functions
- Criticality assessment (HIGH/MEDIUM/LOW)

Use this tool when:
- Debugging variable-related issues
- Understanding data flow
- Identifying critical variables
- Investigating state management
- Planning refactoring""",
        "parameters": {
            "type": "object",
            "properties": {
                "variable_name": {
                    "type": "string",
                    "description": "Name of the variable to trace (e.g., 'filepath', 'state', 'content')"
                }
            },
            "required": ["variable_name"]
        }
    },
    {
        "name": "find_recursive_patterns",
        "description": """Find recursive and circular call patterns in the codebase.

Returns pattern information including:
- Direct recursion functions
- Circular call functions
- Warning flag for high recursion

Use this tool when:
- Investigating infinite loops
- Debugging stack overflow issues
- Analyzing call patterns
- Validating architecture
- Optimizing performance""",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "assess_code_quality",
        "description": """Assess code quality for a specific file.

Returns quality metrics including:
- Lines of code
- Number of classes and functions
- Import count
- Comment ratio
- Average function length
- Overall quality score (0-100)

Use this tool when:
- Reviewing code quality
- Planning refactoring
- Validating changes
- Identifying technical debt
- Assessing maintainability""",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Relative path to the file to analyze (e.g., 'pipeline/phases/debugging.py')"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "get_refactoring_suggestions",
        "description": """Get refactoring suggestions for a specific phase.

Returns actionable suggestions based on:
- Integration complexity
- Connectivity issues
- Recursive patterns
- Code quality metrics

Use this tool when:
- Planning refactoring efforts
- Investigating performance issues
- Improving code quality
- Reducing coupling
- Optimizing architecture""",
        "parameters": {
            "type": "object",
            "properties": {
                "phase_name": {
                    "type": "string",
                    "description": "Name of the phase to analyze (e.g., 'debugging', 'coding')"
                }
            },
            "required": ["phase_name"]
        }
    }
]