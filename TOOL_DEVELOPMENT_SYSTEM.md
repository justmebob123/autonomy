# Tool Development System - Complete Guide

## Overview

The Autonomy system includes a **self-expanding capability** that automatically creates new tools when unknown tools are requested. This meta-capability allows the system to grow its functionality dynamically without manual intervention.

## Architecture

### Components

1. **ToolCallHandler** (`pipeline/handlers.py`)
   - Detects unknown tool calls
   - Returns structured error with `error_type: "unknown_tool"`

2. **BasePhase** (`pipeline/phases/base.py`)
   - `check_for_unknown_tools()` - Scans tool results for unknown tool errors
   - `create_unknown_tool_result()` - Creates PhaseResult with `requires_tool_development=True`

3. **PhaseCoordinator** (`pipeline/coordinator.py`)
   - `_develop_tool()` - Orchestrates tool development workflow
   - Detects `requires_tool_development` flag
   - Routes to tool_design → tool_evaluation → retry

4. **ToolDesignPhase** (`pipeline/phases/tool_design.py`)
   - Creates tool specification
   - Generates Python implementation
   - Saves to `pipeline/tools/custom/`
   - Registers with ToolRegistry

5. **ToolEvaluationPhase** (`pipeline/phases/tool_evaluation.py`)
   - Tests new tool with sample inputs
   - Validates security constraints
   - Confirms tool functionality

6. **ToolRegistry** (`pipeline/tool_registry.py`)
   - Manages custom tools
   - Loads tools from `pipeline/tools/custom/`
   - Provides tool lookup and validation

## Workflow

### Automatic Tool Development Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Phase Execution                                              │
│    • Any phase calls unknown tool (e.g., analyze_docs())       │
│    • LLM returns tool call in response                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Unknown Tool Detection                                       │
│    • ToolCallHandler processes tool call                       │
│    • Tool handler not found                                    │
│    • Returns: {"error_type": "unknown_tool", "tool_name": ...}│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Phase Error Handling                                         │
│    • BasePhase.check_for_unknown_tools() detects error         │
│    • Creates PhaseResult with requires_tool_development=True   │
│    • Includes tool context (name, args, usage)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Coordinator Intervention                                     │
│    • PhaseCoordinator detects requires_tool_development flag   │
│    • Calls _develop_tool(tool_name, context)                   │
│    • Routes to tool_design phase                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Tool Design Phase                                            │
│    • Analyzes tool requirements from context                   │
│    • Generates tool specification:                             │
│      - Name, description, parameters                           │
│      - Python implementation code                              │
│      - Security level, version                                 │
│    • Saves to pipeline/tools/custom/{tool_name}.py             │
│    • Registers with ToolRegistry                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Tool Evaluation Phase                                        │
│    • Loads newly created tool                                  │
│    • Tests with sample inputs                                  │
│    • Validates:                                                │
│      - Output format correctness                               │
│      - Security constraints                                    │
│      - Error handling                                          │
│    • Marks tool as validated                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Original Phase Retry                                         │
│    • Coordinator routes back to original phase                 │
│    • Phase retries execution                                   │
│    • ToolCallHandler finds tool in registry                    │
│    • Tool executes successfully                                │
│    • Phase completes with new capability                       │
└─────────────────────────────────────────────────────────────────┘
```

## Example: analyze_documentation_needs Tool

### Scenario
Documentation phase needs to analyze codebase for documentation gaps but the tool doesn't exist.

### Step-by-Step

**1. Initial Call**
```python
# Documentation phase LLM response includes:
<analyze_documentation_needs project_dir="/workspace/project">
</analyze_documentation_needs>
```

**2. Unknown Tool Error**
```python
{
    "error_type": "unknown_tool",
    "tool_name": "analyze_documentation_needs",
    "args": {"project_dir": "/workspace/project"},
    "message": "Unknown tool: analyze_documentation_needs"
}
```

**3. Tool Development Triggered**
- PhaseCoordinator detects unknown tool
- Routes to tool_design phase with context

**4. Tool Design Creates**
```python
# pipeline/tools/custom/analyze_documentation_needs.py
def analyze_documentation_needs(project_dir: str) -> dict:
    """
    Analyze codebase to identify documentation gaps.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        Dictionary with documentation analysis results
    """
    import os
    from pathlib import Path
    
    results = {
        "files_analyzed": 0,
        "missing_docstrings": [],
        "missing_readme": False,
        "recommendations": []
    }
    
    # Scan Python files
    for py_file in Path(project_dir).rglob("*.py"):
        results["files_analyzed"] += 1
        # Check for docstrings...
        
    return results
```

**5. Tool Evaluation Tests**
- Calls tool with sample project
- Validates output structure
- Confirms security (no dangerous operations)

**6. Tool Available**
- ToolRegistry loads tool
- Documentation phase retries
- Tool executes successfully

## Tool Specification Format

Custom tools must follow this structure:

```python
# pipeline/tools/custom/my_tool.py

def my_tool(param1: str, param2: int = 0) -> dict:
    """
    Brief description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (optional)
        
    Returns:
        Dictionary with results
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Implementation
    result = {
        "status": "success",
        "data": {}
    }
    return result

# Tool metadata (optional)
__tool_metadata__ = {
    "name": "my_tool",
    "version": "1.0.0",
    "security_level": "safe",  # safe|restricted|dangerous
    "description": "Brief description",
    "parameters": {
        "param1": {"type": "string", "required": True},
        "param2": {"type": "integer", "required": False, "default": 0}
    }
}
```

## Security Levels

- **safe**: No file system access, no network, no subprocess
- **restricted**: Limited file system access (read-only), no network
- **dangerous**: Full access (requires explicit approval)

## Polytopic Adjacency

Tool development follows these adjacency relationships:

```
Any Phase → tool_design (when unknown tool detected)
tool_design → tool_evaluation
tool_design → tool_registry
tool_evaluation → original_phase (retry)
tool_evaluation → tool_improvement (if issues found)
```

## Custom Directories

- `pipeline/tools/custom/` - Custom tool implementations
- `pipeline/prompts/custom/` - Custom prompt templates
- `pipeline/roles/custom/` - Custom specialist roles

## Benefits

1. **Self-Expanding**: System grows capabilities automatically
2. **Context-Aware**: Tools created based on actual usage context
3. **Validated**: All tools tested before deployment
4. **Persistent**: Tools saved and reused across runs
5. **Safe**: Security validation prevents dangerous operations

## Integration with Other Systems

### Prompt Design
Similar workflow for custom prompts when standard prompts insufficient.

### Role Design
Similar workflow for custom specialist roles when expertise needed.

### Project Planning
Triggers tool/prompt/role design when expansion opportunities identified.

## Current Status

✅ **Fully Implemented**
- Unknown tool detection
- Automatic routing to tool_design
- Tool creation and registration
- Tool evaluation and validation
- Original phase retry with new tool

✅ **Directory Structure**
- Custom directories created
- Ready for tool storage

✅ **Integration Complete**
- PhaseCoordinator routing
- BasePhase error detection
- ToolRegistry management

## Next Steps

The system is ready for production use. When any phase encounters an unknown tool:
1. It will automatically trigger tool development
2. Create and validate the tool
3. Retry with the new capability
4. Tool persists for future use

This meta-capability enables unlimited system expansion through actual usage patterns.