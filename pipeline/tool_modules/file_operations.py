"""
File Operation Tool Definitions

Provides tool definitions for moving, renaming, and restructuring files
with automatic import updates.
"""

TOOLS_FILE_OPERATIONS = [
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file to a new location and automatically update all imports. Uses git mv to preserve history. CRITICAL: Use this instead of delete+create to maintain git history and update imports automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Current file path (relative to project root, e.g., 'app/utils/database.py')"
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "New file path (relative to project root, e.g., 'app/storage/database.py')"
                    },
                    "update_imports": {
                        "type": "boolean",
                        "description": "If true, automatically update all imports in other files. Default: true"
                    },
                    "create_directories": {
                        "type": "boolean",
                        "description": "If true, create destination directories if they don't exist. Default: true"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation for why the file is being moved (for logging and documentation)"
                    }
                },
                "required": ["source_path", "destination_path", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file and automatically update all imports. Preserves git history. Use this when keeping file in same directory but changing name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Current file path (relative to project root)"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New filename (just the name, not full path, e.g., 'user_model.py')"
                    },
                    "update_imports": {
                        "type": "boolean",
                        "description": "If true, automatically update all imports. Default: true"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation for why the file is being renamed"
                    }
                },
                "required": ["file_path", "new_name", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restructure_directory",
            "description": "Move multiple files according to a restructuring plan and update all imports. Use this for large-scale reorganization. Handles dependencies correctly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restructuring_plan": {
                        "type": "object",
                        "description": "Dictionary mapping old paths to new paths. Example: {'app/old.py': 'app/new/old.py', 'app/other.py': 'app/new/other.py'}"
                    },
                    "update_imports": {
                        "type": "boolean",
                        "description": "If true, automatically update all imports. Default: true"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation for the restructuring"
                    }
                },
                "required": ["restructuring_plan", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_file_placement",
            "description": "Analyze if a file is in the correct location according to ARCHITECTURE.md. Suggests optimal location based on file content and architectural conventions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File to analyze (relative to project root)"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]

TOOLS_IMPORT_OPERATIONS = [
    {
        "type": "function",
        "function": {
            "name": "build_import_graph",
            "description": "Build complete import graph for the project. Shows all import relationships, circular dependencies, and orphaned files. Use this to understand project structure before refactoring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Scope of analysis: 'project' for entire project or specific directory path. Default: 'project'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_import_impact",
            "description": "Analyze the impact of moving, renaming, or deleting a file. Predicts which files will be affected, calculates risk level, and estimates number of changes needed. ALWAYS use this before moving/renaming/deleting files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File to analyze"
                    },
                    "new_path": {
                        "type": "string",
                        "description": "New path (for move/rename operations). Leave empty for delete analysis."
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["move", "rename", "delete"],
                        "description": "Type of operation to analyze. Default: 'move'"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]