"""
Validation Tool Definitions

Provides tool definitions for comprehensive code validation.
"""

# =============================================================================
# Validation Tools - Phase 1 (Critical)
# =============================================================================

TOOLS_VALIDATION = [
    {
        "type": "function",
        "function": {
            "name": "validate_function_calls",
            "description": "Validate that all function and method calls use correct parameters. Checks for missing required arguments, unexpected keyword arguments, and wrong parameter names. Would have caught estimated_effort_minutes and missing task_id/title errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (optional - analyzes all if not specified)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_method_existence",
            "description": "Validate that methods called on objects actually exist on their classes. Checks that all method calls reference real methods. Would have caught ImportAnalyzer.validate_all_imports() missing method error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (optional - analyzes all if not specified)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_dict_structure",
            "description": "Validate that dictionary access patterns match actual data structures. Checks for accessing keys that don't exist or wrong nested paths. Would have caught result_data.get('gaps') when actual key is 'unused_classes'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (optional - analyzes all if not specified)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_type_usage",
            "description": "Validate that objects are used according to their types. Checks for using dict methods on dataclasses, accessing attributes on dicts, etc. Would have caught conflict.get('description') on IntegrationConflict dataclass.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (optional - analyzes all if not specified)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_attribute_access",
            "description": "Validate all object attribute access patterns in Python files. Checks that accessed attributes exist in class definitions. Would have caught task.target vs task.target_file error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    },
                    "check_all_files": {
                        "type": "boolean",
                        "description": "Check all Python files in project. Default: false"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "verify_import_class_match",
            "description": "Verify that imported names match actual class names in modules. Would have caught ConflictDetector vs IntegrationConflictDetector error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    },
                    "check_all_imports": {
                        "type": "boolean",
                        "description": "Check all imports in file. Default: true"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "check_abstract_methods",
            "description": "Check that all abstract methods from base classes are implemented. Would have caught missing generate_state_markdown method.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file containing class (relative to project root)"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Name of class to check for abstract method implementation"
                    }
                },
                "required": ["filepath", "class_name"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "verify_tool_handlers",
            "description": "Verify all tools have corresponding handlers and are properly registered. Checks tool definitions, handler implementations, and registration in handlers dict.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_module": {
                        "type": "string",
                        "description": "Path to specific tool module to check (optional)"
                    },
                    "check_all": {
                        "type": "boolean",
                        "description": "Check all tool modules. Default: true"
                    }
                }
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "validate_dict_access",
            "description": "Validate dictionary access patterns to prevent KeyError. Checks for proper key existence verification before access (e.g., 'if key in dict' before dict[key]).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to analyze (relative to project root)"
                    },
                    "dict_name": {
                        "type": "string",
                        "description": "Name of dictionary to check (e.g., 'state.phases'). Optional - checks all dicts if not specified"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    
    # Phase 2 tools (to be implemented)
    {
        "type": "function",
        "function": {
            "name": "validate_syntax",
            "description": "Comprehensive syntax validation for Python files. Checks for syntax errors, malformed code, and common syntax issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to validate"
                    },
                    "check_all_files": {
                        "type": "boolean",
                        "description": "Check all Python files in project"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "detect_circular_imports",
            "description": "Detect circular import dependencies in the project. Finds import cycles that could cause runtime errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_module": {
                        "type": "string",
                        "description": "Starting module to check (optional - checks all if not specified)"
                    }
                }
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "validate_all_imports",
            "description": "Comprehensive import validation. Checks all imports exist, are accessible, and match expected names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to Python file to validate"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "validate_imports_comprehensive",
            "description": "Comprehensive import validation for entire codebase. Validates syntax, imports, module existence, and typing imports. Prevents import-related failures before runtime.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_dir": {
                        "type": "string",
                        "description": "Directory to validate (default: 'pipeline')"
                    },
                    "check_syntax": {
                        "type": "boolean",
                        "description": "Check syntax of all files (default: true)"
                    },
                    "check_imports": {
                        "type": "boolean",
                        "description": "Check import statements (default: true)"
                    },
                    "check_modules": {
                        "type": "boolean",
                        "description": "Check module existence (default: true)"
                    },
                    "check_typing": {
                        "type": "boolean",
                        "description": "Check typing imports (default: true)"
                    }
                }
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "fix_html_entities",
            "description": "Fix HTML entity encoding issues in Python files. Detects and fixes malformed docstring quotes, HTML entities in comments, and syntax errors from entity encoding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "File or directory to fix (relative to project root)"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Only detect issues, don't fix (default: false)"
                    },
                    "backup": {
                        "type": "boolean",
                        "description": "Create backup before fixing (default: true)"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Process directories recursively (default: true)"
                    }
                },
                "required": ["target"]
            }
        }
    }
]