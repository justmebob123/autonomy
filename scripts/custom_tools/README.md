# Custom Tools Directory

This directory is for **user-defined custom tools** that can be dynamically loaded by the pipeline at runtime.

## Purpose

The custom tools system allows you to extend the pipeline with your own tools without modifying the core codebase. Tools placed here will be automatically discovered and made available to the AI agents.

## Directory Structure

```
scripts/custom_tools/
├── __init__.py
├── README.md (this file)
└── tools/           # Place your custom tool files here
    ├── __init__.py
    └── (your_tool.py files)
```

## Creating a Custom Tool

1. Create a Python file in the `tools/` directory (e.g., `my_tool.py`)
2. Define a class that inherits from `BaseTool`
3. Implement the required methods:
   - `execute()` - Main tool logic
   - `get_definition()` - OpenAI function definition
4. The pipeline will automatically discover and register it

## Example

See `bin/custom_tools/tools/` for example implementations:
- `analyze_imports.py` - Analyzes import statements
- `code_complexity.py` - Calculates code complexity
- `find_todos.py` - Finds TODO comments

## Note

This is different from `bin/custom_tools/` which contains **manual CLI tools** for developers to run directly. Tools in `scripts/custom_tools/` are loaded by the pipeline at runtime.

## Current Status

The custom tools feature is currently **disabled** in the pipeline (see `pipeline/handlers.py`). To enable it, uncomment the CustomToolHandler initialization code.