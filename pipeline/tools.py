"""
Tool Definitions for LLM Tool Calling

Contains all tool definitions used by pipeline phases:
- Planning tools: create_task_plan
- Coding tools: create_python_file, modify_python_file
- QA tools: report_issue, approve_code
- Project Planning tools: analyze_project_status, propose_expansion_tasks, update_architecture
- Documentation tools: analyze_documentation_needs, update_readme_section, add_readme_section
"""

from typing import List, Dict
from .system_analyzer_tools import SYSTEM_ANALYZER_TOOLS
from .tools.tool_definitions import TOOLS_ANALYSIS, TOOLS_FILE_UPDATES


# =============================================================================
# Core Pipeline Tools
# =============================================================================

TOOLS_PLANNING = [
    {
        "type": "function",
        "function": {
            "name": "create_task_plan",
            "description": "Create a prioritized list of development tasks for the project.",
            "parameters": {
                "type": "object",
                "required": ["tasks"],
                "properties": {
                    "tasks": {
                        "type": "array",
                        "description": "List of tasks to implement",
                        "items": {
                            "type": "object",
                            "required": ["description", "target_file", "priority"],
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "What to implement"
                                },
                                "target_file": {
                                    "type": "string",
                                    "description": "File path to create/modify"
                                },
                                "priority": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 100,
                                    "description": "Priority (1=highest)"
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Files that must exist first"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
]

TOOLS_CODING = [
    {
        "type": "function",
        "function": {
            "name": "create_python_file",
            "description": "Create a new Python file with complete, working code. The code must be syntactically valid Python with all imports included.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "code"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'core/config.py')"
                    },
                    "code": {
                        "type": "string",
                        "description": "Complete Python source code with imports, classes, and functions"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of what this file does"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_python_file",
            "description": "Modify an existing Python file by replacing specific code.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "original_code", "new_code"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to modify"
                    },
                    "original_code": {
                        "type": "string",
                        "description": "Exact code to find and replace"
                    },
                    "new_code": {
                        "type": "string",
                        "description": "New code to replace original with"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this change is being made"
                    }
                }
            }
        }
    }
]

TOOLS_QA = [
    {
        "type": "function",
        "function": {
            "name": "report_issue",
            "description": "Report a code issue found during review.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "issue_type", "description"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "File with the issue"
                    },
                    "issue_type": {
                        "type": "string",
                        "enum": ["syntax_error", "logic_error", "missing_import", 
                                "type_error", "incomplete", "security", "performance"],
                        "description": "Category of issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Approximate line number"
                    },
                    "suggested_fix": {
                        "type": "string",
                        "description": "How to fix this issue"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "approve_code",
            "description": "Approve code that passes all quality checks.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "File being approved"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any notes about the approval"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file to check imports, dependencies, or related code. Use this to verify that imported modules exist, check how other files implement similar functionality, or understand the broader context.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to read (relative to project root)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for code patterns across the project to verify consistency, find where methods/classes are defined, or check architectural patterns. Use this to validate that referenced code actually exists.",
            "parameters": {
                "type": "object",
                "required": ["pattern"],
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to search for (supports regex)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to search in (default: *.py)",
                        "default": "*.py"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List directory contents to verify project structure, check if expected files exist, or explore the codebase organization.",
            "parameters": {
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (relative to project root, use '.' for root)"
                    }
                }
            }
        }
    }
]

TOOLS_DEBUGGING = [
    {
        "type": "function",
        "function": {
            "name": "analyze_missing_import",
            "description": "CRITICAL for import errors! Analyzes where an import should be added. Shows existing imports, suggests proper location (top of file), and provides the correct import statement.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "module_name"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file with missing import"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "Name of the module to import (e.g., 'yaml', 'json')"
                    },
                    "usage_line": {
                        "type": "integer",
                        "description": "Line number where module is used"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_import_scope",
            "description": "Check if an import is in the correct scope. Detects imports inside functions or try blocks that should be at module level.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "import_statement"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file"
                    },
                    "import_statement": {
                        "type": "string",
                        "description": "The import statement to check (e.g., 'import yaml')"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Line number of the import"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "investigate_parameter_removal",
            "description": "CRITICAL: MUST USE BEFORE removing parameters! Investigates what happens if you remove a parameter from a function call. Shows where data comes from, what breaks, and recommends the correct fix.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "function_name", "parameter_name"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file with the function call"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function being called"
                    },
                    "parameter_name": {
                        "type": "string",
                        "description": "Name of the parameter you're considering removing (e.g., 'servers')"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Optional: Class name if it's a method"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "investigate_data_flow",
            "description": "Trace where data comes from and where it goes. CRITICAL for KeyError and missing data issues. Shows data source, transformations, and expected structure.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "variable_name"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file"
                    },
                    "variable_name": {
                        "type": "string",
                        "description": "Name of the variable to trace (e.g., 'servers')"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Optional: Line number where error occurs"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_config_structure",
            "description": "Check if configuration file exists and has expected structure. CRITICAL for KeyError issues related to configuration.",
            "parameters": {
                "type": "object",
                "required": ["config_file"],
                "properties": {
                    "config_file": {
                        "type": "string",
                        "description": "Path to config file (e.g., 'config.yaml')"
                    },
                    "expected_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys that should exist in config (e.g., ['servers', 'database'])"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_signature",
            "description": "Extract function signature to verify what parameters it accepts. USE THIS to check if parameters are valid.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "function_name"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file containing the function (e.g., 'src/execution/job_executor.py')"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function to inspect (e.g., '__init__')"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Optional: Class name if function is a method (e.g., 'JobExecutor')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_function_call",
            "description": "Validate that a function call uses valid parameters. USE THIS to prevent TypeError from invalid parameters.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "function_name", "call_kwargs"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file containing the function"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function being called"
                    },
                    "call_kwargs": {
                        "type": "object",
                        "description": "Dictionary of keyword arguments you plan to pass"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Optional: Class name if function is a method"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command for analysis. Use this to run git commands, linters, tests, grep, find, or other analysis tools. CRITICAL for specialists to gather information.",
            "parameters": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (e.g., 'git log --oneline -10', 'grep -r pattern .', 'find . -name *.py')"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds",
                        "default": 300
                    },
                    "capture_output": {
                        "type": "boolean",
                        "description": "Capture command output",
                        "default": True
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_python_file",
            "description": "Modify an existing Python file by replacing specific code to fix an issue.",
            "parameters": {
                "type": "object",
                "required": ["filepath", "original_code", "new_code"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to modify"
                    },
                    "original_code": {
                        "type": "string",
                        "description": "Exact code to find and replace"
                    },
                    "new_code": {
                        "type": "string",
                        "description": "New code to replace original with"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this change is being made"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the project to examine it. Use this to check related files or see how other parts of the code work.",
            "parameters": {
                "type": "object",
                "required": ["filepath"],
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to read (relative to project root)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for code patterns across the entire project. Use this to find all occurrences of a method, variable, or pattern. Helpful for understanding refactorings.",
            "parameters": {
                "type": "object",
                "required": ["pattern"],
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to search for (supports regex)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to search in (default: *.py)",
                        "default": "*.py"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory to understand project structure.",
            "parameters": {
                "type": "object",
                "required": ["directory"],
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list (relative to project root)"
                    }
                }
            }
        }
    }
]


# =============================================================================
# Project Planning Tools (NEW)
# =============================================================================

TOOLS_PROJECT_PLANNING = [
    {
        "type": "function",
        "function": {
            "name": "analyze_project_status",
            "description": "Report on current project status relative to MASTER_PLAN objectives. Call this FIRST before proposing tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objectives_completed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of MASTER_PLAN objectives that are fully implemented"
                    },
                    "objectives_in_progress": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of objectives that are partially implemented"
                    },
                    "objectives_pending": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of objectives not yet started"
                    },
                    "code_quality_notes": {
                        "type": "string",
                        "description": "Notes on code quality, patterns, and consistency"
                    },
                    "recommended_focus": {
                        "type": "string",
                        "description": "Recommended area to focus on for next expansion"
                    }
                },
                "required": ["objectives_completed", "objectives_in_progress", "objectives_pending", "recommended_focus"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_expansion_tasks",
            "description": "Propose new tasks for project expansion. Each task should be small and focused.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "Clear description of what to implement"
                                },
                                "target_file": {
                                    "type": "string",
                                    "description": "Path to the file to create or modify"
                                },
                                "priority": {
                                    "type": "integer",
                                    "description": "Priority 1-100, lower is higher priority"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["feature", "refactor", "test", "documentation", "bugfix", "integration"],
                                    "description": "Type of task"
                                },
                                "rationale": {
                                    "type": "string",
                                    "description": "Why this task is needed, referencing MASTER_PLAN"
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Files this task depends on"
                                }
                            },
                            "required": ["description", "target_file", "priority", "category", "rationale"]
                        },
                        "description": "List of tasks to create (max 5 per planning cycle)"
                    },
                    "expansion_focus": {
                        "type": "string",
                        "description": "High-level description of what this expansion cycle focuses on"
                    }
                },
                "required": ["tasks", "expansion_focus"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_architecture",
            "description": "Propose updates to ARCHITECTURE.md based on implementation patterns observed",
            "parameters": {
                "type": "object",
                "properties": {
                    "sections_to_add": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "heading": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["heading", "content"]
                        },
                        "description": "New sections to add to ARCHITECTURE.md"
                    },
                    "sections_to_update": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "heading": {"type": "string"},
                                "new_content": {"type": "string"}
                            },
                            "required": ["heading", "new_content"]
                        },
                        "description": "Existing sections to update"
                    }
                },
                "required": []
            }
        }
    }
]


# =============================================================================
# Documentation Tools (NEW)
# =============================================================================

TOOLS_DOCUMENTATION = [
    {
        "type": "function",
        "function": {
            "name": "analyze_documentation_needs",
            "description": "Analyze what documentation needs to be updated based on recent changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "readme_needs_update": {
                        "type": "boolean",
                        "description": "Whether README.md needs updates"
                    },
                    "readme_sections_outdated": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of README sections that need updating"
                    },
                    "architecture_needs_update": {
                        "type": "boolean",
                        "description": "Whether ARCHITECTURE.md needs updates"
                    },
                    "new_features_to_document": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New features that should be documented"
                    },
                    "documentation_quality_notes": {
                        "type": "string",
                        "description": "Notes on overall documentation quality"
                    }
                },
                "required": ["readme_needs_update", "architecture_needs_update"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_readme_section",
            "description": "Update a specific section of README.md",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_heading": {
                        "type": "string",
                        "description": "The heading of the section to update (e.g., 'Features', 'Installation')"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "The new content for this section"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["replace", "append", "prepend"],
                        "description": "How to apply the update"
                    }
                },
                "required": ["section_heading", "new_content", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_readme_section",
            "description": "Add a new section to README.md",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_heading": {
                        "type": "string",
                        "description": "The heading for the new section"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content for the new section"
                    },
                    "after_section": {
                        "type": "string",
                        "description": "Insert after this section heading (optional)"
                    }
                },
                "required": ["section_heading", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_documentation_current",
            "description": "Confirm that documentation is up-to-date and no changes are needed",
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "string",
                        "description": "Notes about why documentation is current"
                    }
                },
                "required": []
            }
        }
    }
]


# =============================================================================
# Resource Monitoring and Debugging Tools
# =============================================================================

TOOLS_MONITORING = [
    {
        "type": "function",
        "function": {
            "name": "get_memory_profile",
            "description": "Get memory usage profile for a process or system-wide. Use this to check for memory leaks or high memory usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID to check (omit for system-wide)"
                    },
                    "include_children": {
                        "type": "boolean",
                        "description": "Include child processes in memory calculation",
                        "default": False
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cpu_profile",
            "description": "Get CPU usage and time for a process or system-wide. Use this to identify CPU-intensive operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID to check (omit for system-wide)"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Sampling duration in seconds",
                        "default": 1.0
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_process",
            "description": "Get detailed information about a running process including PID, memory, CPU, and command line.",
            "parameters": {
                "type": "object",
                "required": ["pid"],
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID to inspect"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_resources",
            "description": "Get overall system resource usage including CPU, memory, disk, and network.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["cpu", "memory", "disk", "network"]
                        },
                        "description": "Which metrics to retrieve (default: all)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_process_tree",
            "description": "Show process tree to understand process relationships and hierarchies. Useful for debugging process management issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_pid": {
                        "type": "integer",
                        "description": "Root process ID (omit for current process)"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Tree depth to show",
                        "default": 3
                    }
                }
            }
        }
    }
]

# =============================================================================
# Combined Tools List (for backward compatibility)
# =============================================================================

PIPELINE_TOOLS: List[Dict] = (
    TOOLS_PLANNING + 
    TOOLS_CODING + 
    TOOLS_QA +
    TOOLS_MONITORING
)


# =============================================================================
# Tool Getter Function
# =============================================================================

def get_tools_for_phase(phase: str, tool_registry=None) -> List[Dict]:
    """
    Get tools appropriate for a pipeline phase.
    
    All phases get monitoring tools for resource awareness.
    Custom tools from ToolRegistry are added if registry provided.
    
    Args:
        phase: Name of the phase
        tool_registry: Optional ToolRegistry instance for custom tools
        
    Returns:
        List of tool definitions for that phase
        
    Integration Point #3: Custom tools added from registry
    """
    # Base tools for each phase
    phase_tools = {
        "planning": TOOLS_PLANNING + TOOLS_ANALYSIS + TOOLS_FILE_UPDATES,
        "coding": TOOLS_CODING + TOOLS_ANALYSIS,
        "qa": TOOLS_QA + TOOLS_ANALYSIS,
        "debugging": TOOLS_DEBUGGING + TOOLS_ANALYSIS,
        "debug": TOOLS_DEBUGGING + TOOLS_ANALYSIS,  # Alias
        "project_planning": TOOLS_PROJECT_PLANNING + TOOLS_ANALYSIS + TOOLS_FILE_UPDATES,
        "documentation": TOOLS_DOCUMENTATION + TOOLS_FILE_UPDATES,
    }
    
    # Get base tools for this phase
    tools = phase_tools.get(phase, PIPELINE_TOOLS)
    
    # Add monitoring tools to all phases for resource awareness
    tools = tools + TOOLS_MONITORING
    
    # Add system analyzer tools to all phases for self-analysis
    tools = tools + SYSTEM_ANALYZER_TOOLS
    
    # Add custom tools from registry (Integration Point #3)
    if tool_registry:
        try:
            # New ToolRegistry API (scripts/custom_tools/)
            if hasattr(tool_registry, 'get_tools_for_phase'):
                custom_tools = tool_registry.get_tools_for_phase(phase)
                if custom_tools:
                    tools = tools + custom_tools
            # Legacy API (pipeline/tools/custom/)
            elif hasattr(tool_registry, 'tools'):
                for tool_name in tool_registry.tools:
                    tool_def = tool_registry.get_tool_definition(tool_name)
                    if tool_def:
                        tools.append(tool_def)
        except Exception as e:
            # Log error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load custom tools: {e}")
    
    return tools
