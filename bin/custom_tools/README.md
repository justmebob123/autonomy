# Custom Tools System

## Overview

The Custom Tools System allows you to create and integrate custom tools into the Autonomy AI pipeline. Tools are automatically discovered, validated, and made available to the AI agent.

## Features

- ✅ **Automatic Discovery**: Tools are automatically discovered from `scripts/custom_tools/tools/`
- ✅ **Process Isolation**: Tools run in isolated subprocess for safety
- ✅ **Timeout Enforcement**: Configurable timeouts prevent hanging
- ✅ **Live Reload**: Tools are reloaded on file changes (no restart needed)
- ✅ **Security Sandboxing**: Resource limits and permission controls
- ✅ **Standard Interface**: All tools use BaseTool with consistent API
- ✅ **OpenAI Compatible**: Tool definitions work with LLM tool calling

## Quick Start

### 1. Create a New Tool

```python
#!/usr/bin/env python3
"""
Example Custom Tool - Analyzes Python imports
"""

from pathlib import Path
import ast
from core.base import BaseTool, ToolResult


class AnalyzeImports(BaseTool):
    """Analyze import statements in a Python file."""
    
    # Tool metadata (REQUIRED)
    name = "analyze_imports"
    description = "Analyze import statements in a Python file and detect issues"
    version = "1.0.0"
    category = "analysis"
    author = "Your Name"
    
    # Security settings (OPTIONAL)
    requires_filesystem = True
    requires_network = False
    requires_subprocess = False
    timeout_seconds = 30
    max_file_size_mb = 10
    
    def execute(self, filepath: str) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            filepath: Path to Python file (relative to project root)
            
        Returns:
            ToolResult with success, result, error, metadata
        """
        try:
            # Validate input
            if not filepath.endswith('.py'):
                return ToolResult(
                    success=False,
                    error="File must be a Python file (.py)"
                )
            
            # Get full path
            full_path = self.project_dir / filepath
            
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {filepath}"
                )
            
            # Analyze imports
            content = full_path.read_text()
            tree = ast.parse(content)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
            
            # Return result
            return ToolResult(
                success=True,
                result={
                    'filepath': filepath,
                    'total_imports': len(imports),
                    'imports': imports
                },
                metadata={
                    'filepath': filepath,
                    'lines_analyzed': len(content.splitlines())
                }
            )
            
        except SyntaxError as e:
            return ToolResult(
                success=False,
                error=f"Syntax error in file: {e}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Analysis failed: {e}"
            )


# CLI interface for subprocess execution
if __name__ == '__main__':
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-dir', required=True)
    parser.add_argument('--args', required=True)
    args = parser.parse_args()
    
    # Parse arguments
    tool_args = json.loads(args.args)
    
    # Create and run tool
    tool = AnalyzeImports(args.project_dir)
    result = tool.run(**tool_args)
    
    # Output result as JSON
    print(json.dumps(result.to_dict()))
    sys.exit(0 if result.success else 1)
```

### 2. Save the Tool

Save your tool to `scripts/custom_tools/tools/analyze_imports.py`

### 3. Test the Tool

The tool is automatically discovered and available to the AI agent!

You can test it manually:

```bash
cd /project
python scripts/custom_tools/tools/analyze_imports.py \
    --project-dir . \
    --args '{"filepath": "main.py"}'
```

## Tool Structure

### Required Components

1. **Inherit from BaseTool**
   ```python
   from core.base import BaseTool, ToolResult
   
   class MyTool(BaseTool):
       ...
   ```

2. **Set Tool Metadata**
   ```python
   name = "my_tool"              # Tool name (required)
   description = "What it does"  # Description (required)
   version = "1.0.0"             # Version (required)
   category = "utility"          # Category (required)
   author = "Your Name"          # Author (optional)
   ```

3. **Implement execute() Method**
   ```python
   def execute(self, **kwargs) -> ToolResult:
       # Your tool logic here
       return ToolResult(
           success=True,
           result=your_result,
           metadata={'key': 'value'}
       )
   ```

4. **Add CLI Interface**
   ```python
   if __name__ == '__main__':
       # Standard CLI interface (copy from template)
       ...
   ```

### Optional Components

1. **Custom Validation**
   ```python
   def validate_inputs(self, **kwargs):
       if 'required_param' not in kwargs:
           return False, "required_param is missing"
       return True, None
   ```

2. **Security Settings**
   ```python
   requires_filesystem = True    # Needs file access
   requires_network = False      # Needs network access
   requires_subprocess = False   # Needs subprocess
   timeout_seconds = 60          # Custom timeout
   max_file_size_mb = 50         # Max file size
   ```

## Tool Categories

Organize tools by category:

- **analysis**: Code analysis tools
- **testing**: Testing and validation tools
- **documentation**: Documentation generation tools
- **refactoring**: Code refactoring tools
- **utility**: General utility tools
- **data**: Data processing tools
- **integration**: External integration tools

## Best Practices

### 1. Error Handling

Always return ToolResult with proper error messages:

```python
try:
    # Your logic
    return ToolResult(success=True, result=data)
except FileNotFoundError:
    return ToolResult(success=False, error="File not found")
except Exception as e:
    return ToolResult(success=False, error=f"Unexpected error: {e}")
```

### 2. Input Validation

Validate inputs before processing:

```python
def execute(self, filepath: str) -> ToolResult:
    # Validate
    if not filepath:
        return ToolResult(success=False, error="filepath is required")
    
    if not filepath.endswith('.py'):
        return ToolResult(success=False, error="Must be a Python file")
    
    # Process
    ...
```

### 3. Use Relative Paths

Always use paths relative to project_dir:

```python
# Good
full_path = self.project_dir / filepath

# Bad
full_path = Path(filepath)  # Might be absolute
```

### 4. Provide Metadata

Include useful metadata in results:

```python
return ToolResult(
    success=True,
    result=data,
    metadata={
        'filepath': filepath,
        'lines_processed': line_count,
        'processing_time': elapsed_time
    }
)
```

### 5. Set Appropriate Timeouts

Set realistic timeouts based on tool complexity:

```python
# Quick analysis
timeout_seconds = 10

# File processing
timeout_seconds = 30

# Complex operations
timeout_seconds = 60
```

## Security

### Process Isolation

Tools run in isolated subprocess:
- Tool crash doesn't crash pipeline
- Resource limits enforced
- Timeout protection
- Clean environment

### Permission System

Control tool capabilities:

```python
requires_filesystem = True   # Can read/write files
requires_network = True      # Can make network requests
requires_subprocess = True   # Can spawn processes
```

### Resource Limits

Prevent resource exhaustion:

```python
timeout_seconds = 30        # Max execution time
max_file_size_mb = 10       # Max file size to process
```

## Integration with Pipeline

### Automatic Discovery

Tools are automatically discovered on:
- Pipeline startup
- Every 5 seconds (auto-refresh)
- Manual reload request

### Tool Availability

Tools are available to:
- All pipeline phases
- LLM tool calling
- Manual execution
- Testing framework

### Tool Definitions

Tools are automatically converted to OpenAI-compatible definitions:

```json
{
  "type": "function",
  "function": {
    "name": "analyze_imports",
    "description": "Analyze import statements in a Python file",
    "parameters": {
      "type": "object",
      "properties": {
        "filepath": {
          "type": "string",
          "description": "Path to Python file"
        }
      },
      "required": ["filepath"]
    }
  }
}
```

## Advanced Features

### Live Reload

Tools are automatically reloaded when files change:

```python
# Edit your tool
vim scripts/custom_tools/tools/my_tool.py

# Changes are automatically detected
# No restart needed!
```

### Tool Registry

Access tool information programmatically:

```python
from pipeline.custom_tools import ToolRegistry

registry = ToolRegistry('/project')
registry.discover_tools()

# List all tools
tools = registry.list_tools()

# Get tool metadata
metadata = registry.get_tool_metadata('analyze_imports')

# Get tool definition
definition = registry.get_tool_definition('analyze_imports')
```

### Custom Tool Handler

Execute tools programmatically:

```python
from pipeline.custom_tools import CustomToolHandler, ToolRegistry

registry = ToolRegistry('/project')
handler = CustomToolHandler('/project', registry)

# Execute tool
result = handler.execute_tool('analyze_imports', {
    'filepath': 'main.py'
})

if result['success']:
    print(result['result'])
```

## Troubleshooting

### Tool Not Found

1. Check file location: `scripts/custom_tools/tools/your_tool.py`
2. Check file name matches tool name
3. Check tool inherits from BaseTool
4. Check tool has required metadata

### Tool Execution Fails

1. Check tool has CLI interface (`if __name__ == '__main__'`)
2. Check tool returns ToolResult
3. Check tool handles errors properly
4. Check timeout is sufficient

### Tool Not Appearing

1. Wait 5 seconds for auto-discovery
2. Check logs for discovery errors
3. Manually trigger discovery
4. Check tool file has no syntax errors

## Examples

See `scripts/custom_tools/tools/` for example tools:

- `analyze_imports.py` - Import analysis
- More examples coming soon!

## API Reference

### BaseTool

Base class for all custom tools.

**Class Attributes:**
- `name: str` - Tool name (required)
- `description: str` - Tool description (required)
- `version: str` - Tool version (required)
- `category: str` - Tool category (required)
- `author: str` - Tool author (optional)
- `requires_filesystem: bool` - Needs file access (default: False)
- `requires_network: bool` - Needs network (default: False)
- `requires_subprocess: bool` - Needs subprocess (default: False)
- `timeout_seconds: int` - Timeout in seconds (default: 30)
- `max_file_size_mb: int` - Max file size (default: 10)

**Methods:**
- `execute(**kwargs) -> ToolResult` - Execute tool (must implement)
- `validate_inputs(**kwargs) -> Tuple[bool, str]` - Validate inputs (optional)
- `run(**kwargs) -> ToolResult` - Run with validation and timeout (automatic)
- `get_metadata() -> Dict` - Get tool metadata (automatic)

### ToolResult

Result object returned by tools.

**Attributes:**
- `success: bool` - Whether tool succeeded
- `result: Any` - Tool output (any type)
- `error: str` - Error message if failed
- `metadata: Dict` - Additional information
- `execution_time: float` - Time taken to execute

**Methods:**
- `to_dict() -> Dict` - Convert to dictionary

### ToolRegistry

Registry for discovering and managing tools.

**Methods:**
- `discover_tools(force=False) -> int` - Discover all tools
- `get_tool_metadata(name) -> ToolMetadata` - Get tool metadata
- `get_tool_definition(name) -> Dict` - Get OpenAI definition
- `list_tools(category=None) -> List[ToolMetadata]` - List all tools
- `reload_tool(name) -> bool` - Reload a tool
- `tool_exists(name) -> bool` - Check if tool exists

### CustomToolHandler

Handler for executing custom tools.

**Methods:**
- `execute_tool(name, args, timeout=None) -> Dict` - Execute tool
- `validate_tool_call(name, args) -> Dict` - Validate without executing
- `is_custom_tool(name) -> bool` - Check if custom tool
- `list_custom_tools(category=None) -> List` - List all custom tools
- `reload_tool(name) -> bool` - Reload a tool

## Contributing

To contribute a new tool:

1. Create tool in `scripts/custom_tools/tools/`
2. Follow tool structure guidelines
3. Test thoroughly
4. Document parameters and behavior
5. Submit pull request

## Support

For issues or questions:
- Check troubleshooting section
- Review example tools
- Check logs for errors
- Open GitHub issue

---

**Version**: 1.0.0  
**Last Updated**: December 28, 2024  
**Maintainer**: NinjaTech AI Team