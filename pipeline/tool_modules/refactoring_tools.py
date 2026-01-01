"""
Refactoring Tool Definitions

Provides tool definitions for architecture refactoring and file reconciliation.
"""

# =============================================================================
# Refactoring Tools
# =============================================================================

TOOLS_REFACTORING = [
    {
        "type": "function",
        "function": {
            "name": "validate_architecture",
            "description": "Validate codebase against MASTER_PLAN.md and ARCHITECTURE.md. Checks file locations, naming conventions, missing files, and implementation alignment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "check_locations": {
                        "type": "boolean",
                        "description": "Check if files are in correct directories"
                    },
                    "check_naming": {
                        "type": "boolean",
                        "description": "Check if files follow naming conventions"
                    },
                    "check_missing": {
                        "type": "boolean",
                        "description": "Check for missing files that should exist"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_refactoring_task",
            "description": "Create a new refactoring task to track work across iterations. Use this when you identify an issue that needs to be fixed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "enum": ["duplicate", "complexity", "dead_code", "architecture", "conflict", "integration", "naming", "structure"],
                        "description": "Type of refactoring issue"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title for the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue and what needs to be done"
                    },
                    "target_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files affected by this issue"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "Priority level (default: medium)"
                    },
                    "fix_approach": {
                        "type": "string",
                        "enum": ["autonomous", "developer_review", "needs_new_code"],
                        "description": "How to handle this task (default: autonomous)"
                    }
                },
                "required": ["issue_type", "title", "description", "target_files"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_refactoring_task",
            "description": "Update the status or details of a refactoring task. Use this to mark progress, add details, or change priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["new", "in_progress", "completed", "failed", "blocked"],
                        "description": "New status"
                    },
                    "fix_details": {
                        "type": "string",
                        "description": "Details about the fix applied"
                    },
                    "error_message": {
                        "type": "string",
                        "description": "Error message if task failed"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "New priority"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_refactoring_tasks",
            "description": "List refactoring tasks with optional filtering. Use this to see what work remains.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["new", "in_progress", "completed", "failed", "blocked", "pending"],
                        "description": "Filter by status (pending = can be executed now)"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "Filter by priority"
                    },
                    "issue_type": {
                        "type": "string",
                        "enum": ["duplicate", "complexity", "dead_code", "architecture", "conflict", "integration", "naming", "structure"],
                        "description": "Filter by issue type"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_refactoring_progress",
            "description": "Get overall refactoring progress statistics. Use this to check if refactoring is complete.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue_report",
            "description": "Create a comprehensive issue report for a complex refactoring task that needs developer review. Use this when a task is too complex for autonomous fixing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the refactoring task"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "Severity level of the issue"
                    },
                    "impact_analysis": {
                        "type": "string",
                        "description": "Analysis of what breaks or degrades if not fixed"
                    },
                    "recommended_approach": {
                        "type": "string",
                        "description": "Recommended approach to fix the issue"
                    },
                    "code_examples": {
                        "type": "string",
                        "description": "Relevant code snippets showing the issue"
                    },
                    "estimated_effort": {
                        "type": "string",
                        "description": "Estimated effort (e.g., '2 hours', '1 day')"
                    },
                    "alternatives": {
                        "type": "string",
                        "description": "Alternative approaches to consider"
                    }
                },
                "required": ["task_id", "severity", "impact_analysis", "recommended_approach"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_developer_review",
            "description": "Request developer input on a blocked refactoring task. Use this when you need human guidance to proceed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the refactoring task"
                    },
                    "question": {
                        "type": "string",
                        "description": "Specific question for the developer"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of possible approaches or options"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context to help developer understand the issue"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "How urgent is the review needed"
                    }
                },
                "required": ["task_id", "question", "options"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_duplicate_implementations",
            "description": "Find files with duplicate or similar implementations. Returns duplicate sets with similarity scores, common features, and merge recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0-1.0) to consider files as duplicates. Default: 0.75"
                    },
                    "scope": {
                        "type": "string",
                        "description": "Scope of analysis: 'project' for entire project or specific directory path"
                    },
                    "include_tests": {
                        "type": "boolean",
                        "description": "Whether to include test files in analysis. Default: false"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_file_implementations",
            "description": "Compare two files in detail to identify common features, unique features, and conflicts. Returns detailed comparison with merge strategy recommendation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file1": {
                        "type": "string",
                        "description": "Path to first file (relative to project root)"
                    },
                    "file2": {
                        "type": "string",
                        "description": "Path to second file (relative to project root)"
                    },
                    "comparison_type": {
                        "type": "string",
                        "enum": ["functions", "classes", "full"],
                        "description": "Type of comparison: 'functions', 'classes', or 'full'. Default: 'full'"
                    }
                },
                "required": ["file1", "file2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_file_features",
            "description": "Extract specific features (functions/classes) from a file with their dependencies. Useful for preparing features for merging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {
                        "type": "string",
                        "description": "Path to source file (relative to project root)"
                    },
                    "features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of function/class names to extract"
                    },
                    "include_dependencies": {
                        "type": "boolean",
                        "description": "Whether to include dependent code. Default: true"
                    }
                },
                "required": ["source_file", "features"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_architecture_consistency",
            "description": "Analyze if codebase matches MASTER_PLAN.md and ARCHITECTURE.md. Identifies missing implementations, duplicates, and inconsistencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "check_master_plan": {
                        "type": "boolean",
                        "description": "Check consistency with MASTER_PLAN.md. Default: true"
                    },
                    "check_architecture": {
                        "type": "boolean",
                        "description": "Check consistency with ARCHITECTURE.md. Default: true"
                    },
                    "check_objectives": {
                        "type": "boolean",
                        "description": "Check consistency with objectives. Default: true"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_refactoring_plan",
            "description": "Generate a refactoring plan based on analysis results. Creates step-by-step plan with priorities and dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_results": {
                        "type": "object",
                        "description": "Results from analyze_architecture_consistency or detect_duplicate_implementations"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low", "all"],
                        "description": "Priority level of issues to include. Default: 'high'"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Maximum number of refactoring steps. Default: 10"
                    }
                },
                "required": ["analysis_results"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "merge_file_implementations",
            "description": "Merge multiple Python files into one by combining their imports, classes, and functions. Automatically deduplicates imports, preserves unique classes and functions (first occurrence wins), and maintains code structure. Creates backups before merging. Use this to consolidate duplicate implementations or merge related functionality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of source file paths to merge"
                    },
                    "target_file": {
                        "type": "string",
                        "description": "Path for the merged output file"
                    },
                    "merge_strategy": {
                        "type": "string",
                        "enum": ["keep_all", "prefer_newer", "ai_merge"],
                        "description": "Merge strategy: 'keep_all' (include all features), 'prefer_newer' (prefer newer implementations), 'ai_merge' (use AI to resolve conflicts). Default: 'ai_merge'"
                    },
                    "preserve_comments": {
                        "type": "boolean",
                        "description": "Preserve comments from source files. Default: true"
                    },
                    "preserve_docstrings": {
                        "type": "boolean",
                        "description": "Preserve docstrings from source files. Default: true"
                    }
                },
                "required": ["source_files", "target_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_refactoring",
            "description": "Validate that refactoring didn't break anything. Checks syntax, imports, and optionally runs tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "refactored_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files that were refactored"
                    },
                    "run_tests": {
                        "type": "boolean",
                        "description": "Whether to run tests. Default: false"
                    },
                    "check_imports": {
                        "type": "boolean",
                        "description": "Check for broken imports. Default: true"
                    },
                    "check_syntax": {
                        "type": "boolean",
                        "description": "Check for syntax errors. Default: true"
                    }
                },
                "required": ["refactored_files"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cleanup_redundant_files",
            "description": "Remove files that have been successfully refactored and merged. Creates backups before deletion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "files_to_remove": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to remove"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for removal (for logging and backup)"
                    },
                    "create_backup": {
                        "type": "boolean",
                        "description": "Create backup before deletion. Default: true"
                    },
                    "update_git": {
                        "type": "boolean",
                        "description": "Stage deletions in git. Default: false"
                    }
                },
                "required": ["files_to_remove", "reason"]
            }
        }
    }
]