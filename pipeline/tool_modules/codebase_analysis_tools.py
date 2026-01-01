"""
Codebase Analysis Tools

Provides comprehensive tools for deep codebase analysis:
- List all source files with metadata
- Cross-reference files against architecture
- Map file relationships and dependencies
- Force iterative deep analysis
"""

TOOLS_CODEBASE_ANALYSIS = [
    {
        "type": "function",
        "function": {
            "name": "list_all_source_files",
            "description": "Get complete inventory of all source files in the codebase with metadata. Use this to understand the full scope of the codebase before making decisions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File extensions to include (e.g., ['py', 'js', 'ts']). Default: ['py']"
                    },
                    "include_tests": {
                        "type": "boolean",
                        "description": "Include test files in results. Default: false"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include file metadata (size, lines, imports, classes, functions). Default: true"
                    },
                    "directory_filter": {
                        "type": "string",
                        "description": "Only include files in this directory (e.g., 'core/', 'services/'). Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cross_reference_file",
            "description": "Analyze a file against ARCHITECTURE.md and MASTER_PLAN.md to validate placement, purpose, naming, and dependencies. Use this to understand if a file is in the right place and serves the right purpose.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to analyze (relative to project root)"
                    },
                    "check_placement": {
                        "type": "boolean",
                        "description": "Check if file is in correct directory per ARCHITECTURE.md. Default: true"
                    },
                    "check_purpose": {
                        "type": "boolean",
                        "description": "Check if file purpose matches MASTER_PLAN.md. Default: true"
                    },
                    "check_naming": {
                        "type": "boolean",
                        "description": "Check if file name follows conventions. Default: true"
                    },
                    "check_dependencies": {
                        "type": "boolean",
                        "description": "Check if dependencies are appropriate. Default: true"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "map_file_relationships",
            "description": "Map all relationships for a file: what it imports, what imports it, similar files, and dependency graph. Use this to understand how a file fits into the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to analyze (relative to project root)"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "How many levels deep to analyze dependencies. Default: 2"
                    },
                    "find_similar": {
                        "type": "boolean",
                        "description": "Find files with similar names or functionality. Default: true"
                    },
                    "analyze_usage": {
                        "type": "boolean",
                        "description": "Analyze how the file is used by other files. Default: true"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_all_related_files",
            "description": "Find ALL files related to a given file or pattern. Use this to ensure you examine every relevant file before making a decision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to find related files for. Optional if using pattern."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to match (e.g., 'risk_assessment', '*_service'). Optional if using file_path."
                    },
                    "include_similar_names": {
                        "type": "boolean",
                        "description": "Include files with similar names. Default: true"
                    },
                    "include_same_class": {
                        "type": "boolean",
                        "description": "Include files defining same class names. Default: true"
                    },
                    "include_importers": {
                        "type": "boolean",
                        "description": "Include files that import this file. Default: true"
                    },
                    "include_imported": {
                        "type": "boolean",
                        "description": "Include files imported by this file. Default: true"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_file_purpose",
            "description": "Deeply analyze a file to understand its purpose, functionality, and role in the codebase. Use this to understand what a file actually does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to analyze (relative to project root)"
                    },
                    "extract_classes": {
                        "type": "boolean",
                        "description": "Extract all class definitions. Default: true"
                    },
                    "extract_functions": {
                        "type": "boolean",
                        "description": "Extract all function definitions. Default: true"
                    },
                    "extract_imports": {
                        "type": "boolean",
                        "description": "Extract all imports. Default: true"
                    },
                    "analyze_complexity": {
                        "type": "boolean",
                        "description": "Analyze code complexity. Default: true"
                    },
                    "extract_docstrings": {
                        "type": "boolean",
                        "description": "Extract docstrings to understand purpose. Default: true"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_multiple_files",
            "description": "Compare multiple files (3+) to find similarities, differences, and determine which should be kept/merged/moved. Use this when you have more than 2 similar files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to compare (minimum 2, recommended 3+)"
                    },
                    "compare_structure": {
                        "type": "boolean",
                        "description": "Compare file structure (classes, functions). Default: true"
                    },
                    "compare_functionality": {
                        "type": "boolean",
                        "description": "Compare actual functionality. Default: true"
                    },
                    "compare_quality": {
                        "type": "boolean",
                        "description": "Compare code quality (docs, types, tests). Default: true"
                    },
                    "recommend_action": {
                        "type": "boolean",
                        "description": "Provide recommendation on what to do. Default: true"
                    }
                },
                "required": ["file_paths"]
            }
        }
    }
]