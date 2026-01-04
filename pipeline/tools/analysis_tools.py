"""
Analysis Tools - AI-Callable Wrappers for Code Analysis

These tools allow the AI to perform code analysis on-demand with flexible scope:
- Single file analysis
- Directory analysis  
- Project-wide analysis

The AI decides when and what to analyze, rather than having all analysis
dumped into the prompt upfront.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from ..analysis.complexity import ComplexityAnalyzer
from ..analysis.call_graph import CallGraphGenerator
from ..analysis.dead_code import DeadCodeDetector
from ..analysis.integration_gaps import IntegrationGapFinder
from ..analysis.integration_conflicts import IntegrationConflictDetector


logger = logging.getLogger(__name__)


def analyze_complexity(
    project_dir: str,
    filepath: Optional[str] = None,
    directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze code complexity for specified scope.
    
    Args:
        project_dir: Project root directory
        filepath: Single file to analyze (relative to project_dir)
        directory: Directory to analyze (relative to project_dir)
        If neither provided, analyzes entire project
    
    Returns:
        Dictionary with complexity metrics:
        - max_complexity: Highest complexity found
        - average_complexity: Average across all functions
        - high_complexity_functions: List of functions with complexity >= 10
        - total_functions: Total functions analyzed
    
    Example:
        # Analyze single file
        result = analyze_complexity(project_dir, filepath="services/auth.py")
        
        # Analyze directory
        result = analyze_complexity(project_dir, directory="services")
        
        # Analyze entire project
        result = analyze_complexity(project_dir)
    """
    try:
        analyzer = ComplexityAnalyzer(Path(project_dir))
        
        # Determine target
        target = None
        if filepath:
            target = filepath
        elif directory:
            target = directory
        
        result = analyzer.analyze(target)
        
        return {
            "max_complexity": result.max_complexity,
            "average_complexity": result.average_complexity,
            "high_complexity_functions": [
                {
                    "name": r.function_name,
                    "file": str(r.filepath),
                    "complexity": r.complexity,
                    "line": r.line_number
                }
                for r in result.high_complexity_functions
            ],
            "total_functions": result.total_functions,
            "scope": target or "entire project"
        }
    except Exception as e:
        logger.error(f"Complexity analysis failed: {e}")
        return {"error": str(e)}


def analyze_call_graph(
    project_dir: str,
    filepath: Optional[str] = None,
    directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze function call relationships.
    
    Args:
        project_dir: Project root directory
        filepath: Single file to analyze
        directory: Directory to analyze
    
    Returns:
        Dictionary with call graph information:
        - total_functions: Number of functions found
        - total_calls: Number of function calls
        - orphaned_functions: Functions never called
        - call_chains: Function call chains
    
    Example:
        # Check if a function is called
        result = analyze_call_graph(project_dir, filepath="services/auth.py")
        if result["orphaned_functions"]:
            print("These functions are never called:", result["orphaned_functions"])
    """
    try:
        generator = CallGraphGenerator(Path(project_dir))
        
        target = filepath or directory
        result = generator.analyze(target)
        
        return {
            "total_functions": result.total_functions,
            "total_calls": result.total_calls,
            "orphaned_functions": [
                {
                    "name": func,
                    "file": str(file)
                }
                for file, func in result.orphaned_functions
            ],
            "call_chains": result.call_chains,
            "scope": target or "entire project"
        }
    except Exception as e:
        logger.error(f"Call graph analysis failed: {e}")
        return {"error": str(e)}


def detect_dead_code(
    project_dir: str,
    filepath: Optional[str] = None,
    directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detect unused functions, methods, classes, and imports.
    
    Args:
        project_dir: Project root directory
        filepath: Single file to check
        directory: Directory to check
    
    Returns:
        Dictionary with dead code findings:
        - unused_functions: Functions never called
        - unused_methods: Methods never called
        - unused_classes: Classes never instantiated
        - unused_imports: Imports never used
    
    Example:
        # Check for dead code in a file
        result = detect_dead_code(project_dir, filepath="services/auth.py")
        if result["unused_functions"]:
            print("Can remove:", result["unused_functions"])
    """
    try:
        detector = DeadCodeDetector(Path(project_dir))
        
        target = filepath or directory
        result = detector.analyze(target)
        
        return {
            "unused_functions": [
                {
                    "name": func,
                    "file": str(file)
                }
                for file, func in result.unused_functions
            ],
            "unused_methods": [
                {
                    "class": cls,
                    "method": method,
                    "file": str(file)
                }
                for file, cls, method in result.unused_methods
            ],
            "unused_classes": [
                {
                    "name": cls,
                    "file": str(file)
                }
                for file, cls in result.unused_classes
            ],
            "unused_imports": [
                {
                    "import": imp,
                    "file": str(file)
                }
                for file, imp in result.unused_imports
            ],
            "total_unused_functions": result.total_unused_functions,
            "total_unused_methods": result.total_unused_methods,
            "total_unused_classes": result.total_unused_classes,
            "total_unused_imports": result.total_unused_imports,
            "scope": target or "entire project"
        }
    except Exception as e:
        logger.error(f"Dead code detection failed: {e}")
        return {"error": str(e)}


def find_integration_gaps(
    project_dir: str,
    directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find missing integrations and unused components.
    
    Args:
        project_dir: Project root directory
        directory: Specific directory to analyze (optional)
    
    Returns:
        Dictionary with integration gap findings:
        - unused_classes: Classes defined but never used
        - missing_integrations: Components that should be integrated
        - integration_points: Known integration points (should be skipped)
    
    Example:
        # Find gaps in services directory
        result = find_integration_gaps(project_dir, directory="services")
        if result["missing_integrations"]:
            print("Need to integrate:", result["missing_integrations"])
    """
    try:
        finder = IntegrationGapFinder(Path(project_dir))
        
        result = finder.analyze(directory)
        
        return {
            "unused_classes": [
                {
                    "name": cls,
                    "file": str(file)
                }
                for file, cls in result.unused_classes
            ],
            "missing_integrations": [
                {
                    "component": comp,
                    "file": str(file)
                }
                for file, comp in result.missing_integrations
            ],
            "total_gaps": len(result.unused_classes) + len(result.missing_integrations),
            "scope": directory or "entire project"
        }
    except Exception as e:
        logger.error(f"Integration gap analysis failed: {e}")
        return {"error": str(e)}


def find_integration_conflicts(
    project_dir: str
) -> Dict[str, Any]:
    """
    Find integration conflicts and circular dependencies.
    
    Args:
        project_dir: Project root directory
    
    Returns:
        Dictionary with conflict findings:
        - duplicate_definitions: Same name defined in multiple places
        - circular_dependencies: Circular import chains
        - conflicting_interfaces: Incompatible interfaces
    
    Example:
        # Check for conflicts
        result = find_integration_conflicts(project_dir)
        if result["circular_dependencies"]:
            print("Circular deps found:", result["circular_dependencies"])
    """
    try:
        detector = IntegrationConflictDetector(Path(project_dir))
        
        result = detector.analyze()
        
        return {
            "duplicate_definitions": result.duplicate_definitions,
            "circular_dependencies": result.circular_dependencies,
            "conflicting_interfaces": result.conflicting_interfaces,
            "total_conflicts": result.total_conflicts
        }
    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        return {"error": str(e)}


# Tool registry for AI
ANALYSIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_complexity",
            "description": "Analyze code complexity for a file, directory, or entire project. Use this to check if high complexity is contributing to bugs or if code needs refactoring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Single file to analyze (relative path, optional)"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to analyze (relative path, optional)"
                    }
                },
                "required": ["project_dir"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_call_graph",
            "description": "Analyze function call relationships to understand code flow and find orphaned functions. Use this to check if a function is called anywhere or to understand call chains.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Single file to analyze (optional)"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to analyze (optional)"
                    }
                },
                "required": ["project_dir"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_dead_code",
            "description": "Detect unused functions, methods, classes, and imports. Use this to find code that can be safely removed or to verify if something is actually used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Single file to check (optional)"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to check (optional)"
                    }
                },
                "required": ["project_dir"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_integration_gaps",
            "description": "Find missing integrations and unused components. Use this to understand if a component should be integrated or is waiting for future integration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Specific directory to analyze (optional)"
                    }
                },
                "required": ["project_dir"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_integration_conflicts",
            "description": "Find integration conflicts and circular dependencies. Use this to identify architectural issues that need resolution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Project root directory"
                    }
                },
                "required": ["project_dir"]
            }
        }
    }
]


def get_analysis_tools() -> List[Dict[str, Any]]:
    """Get list of analysis tools for AI."""
    return ANALYSIS_TOOLS


def get_analysis_tool_functions() -> Dict[str, callable]:
    """Get mapping of tool names to functions."""
    return {
        "analyze_complexity": analyze_complexity,
        "analyze_call_graph": analyze_call_graph,
        "detect_dead_code": detect_dead_code,
        "find_integration_gaps": find_integration_gaps,
        "find_integration_conflicts": find_integration_conflicts
    }