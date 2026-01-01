"""
Custom Tools Directory

This directory is for user-defined custom tools that can be dynamically
loaded by the pipeline at runtime.

To create a custom tool:
1. Create a Python file in this directory (e.g., my_tool.py)
2. Define a class that inherits from BaseTool
3. Implement the required methods
4. The pipeline will automatically discover and register it

See bin/custom_tools/ for examples of tool implementations.
"""