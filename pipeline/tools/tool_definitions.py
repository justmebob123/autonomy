"""
Additional Tool Definitions for Analysis and File Updates

This module contains tool definitions for:
- Analysis tools (complexity, dead code, integration gaps, etc.)
- File update tools (append, update_section, insert_after, etc.)
"""

# =============================================================================
# Analysis Tools
# =============================================================================

TOOLS_ANALYSIS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_complexity",
            "description": "Analyze code complexity and identify refactoring priorities. Returns complexity metrics, distribution, and effort estimates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_dead_code",
            "description": "Detect unused functions, methods, and imports. Helps identify code that can be safely removed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_integration_gaps",
            "description": "Find integration gaps and incomplete features. Identifies unused classes, classes with many unused methods, and architectural gaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_call_graph",
            "description": "Generate comprehensive call graphs showing function/method relationships. Useful for understanding code flow and dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_enhanced",
            "description": "Run enhanced depth-61 analysis with full AST analysis, variable tracing, and dependency mapping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_improved",
            "description": "Run improved depth-61 analysis with pattern detection and false positive reduction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deep_analyze",
            "description": "Run comprehensive deep analysis with multiple output formats. Unified interface to all analyzers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Optional specific file or directory to analyze (default: entire project)"
                    },
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific checks to run (e.g., ['bugs', 'complexity', 'deadcode'])"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json", "markdown"],
                        "description": "Output format (default: text)"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Analyze recursively (default: true)"
                    }
                }
            }
        }
    }
]

# =============================================================================
# File Update Tools
# =============================================================================

TOOLS_FILE_UPDATES = [
    {
        "type": "function",
        "function": {
            "name": "append_to_file",
            "description": "Append content to the end of a file. Useful for adding new sections to documents without rewriting entire file.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "content"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to project root)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append"
                    },
                    "ensure_newline": {
                        "type": "boolean",
                        "description": "Ensure file ends with newline before appending (default: true)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_section",
            "description": "Update a specific section in a markdown file. Finds section by title and replaces content until next section of same or higher level.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "section_title", "new_content"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to markdown file (relative to project root)"
                    },
                    "section_title": {
                        "type": "string",
                        "description": "Section title (without # markers, e.g., 'Phase 2')"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content for the section"
                    },
                    "create_if_missing": {
                        "type": "boolean",
                        "description": "Create section if it doesn't exist (default: true)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_after",
            "description": "Insert content after a marker line in a file.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "marker", "content"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to project root)"
                    },
                    "marker": {
                        "type": "string",
                        "description": "Marker line to search for"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to insert after marker"
                    },
                    "first_occurrence": {
                        "type": "boolean",
                        "description": "Insert after first occurrence only (default: true)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_before",
            "description": "Insert content before a marker line in a file.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "marker", "content"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to project root)"
                    },
                    "marker": {
                        "type": "string",
                        "description": "Marker line to search for"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to insert before marker"
                    },
                    "first_occurrence": {
                        "type": "boolean",
                        "description": "Insert before first occurrence only (default: true)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replace_between",
            "description": "Replace content between two marker lines in a file.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "start_marker", "end_marker", "new_content"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to project root)"
                    },
                    "start_marker": {
                        "type": "string",
                        "description": "Start marker line"
                    },
                    "end_marker": {
                        "type": "string",
                        "description": "End marker line"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content to insert between markers"
                    },
                    "include_markers": {
                        "type": "boolean",
                        "description": "Replace markers too (default: false, keeps markers)"
                    }
                }
            }
        }
    }
]
# =============================================================================
# Additional Native Analysis Tools
# =============================================================================

ADDITIONAL_NATIVE_ANALYSIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_bugs",
            "description": "Detect potential bugs in Python code including identity comparison issues, bare except clauses, mutable default arguments, and other common mistakes.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_antipatterns",
            "description": "Detect anti-patterns in Python code including too many arguments, long functions, deep nesting, god classes, and other code smells.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_dataflow",
            "description": "Analyze data flow in Python code to detect uninitialized variables, unused assignments, and variable lifecycle issues.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    }
                }
            }
        }
    }
]

# Add additional native analysis tools to the main list
TOOL_DEFINITIONS.extend(ADDITIONAL_NATIVE_ANALYSIS_TOOLS)
