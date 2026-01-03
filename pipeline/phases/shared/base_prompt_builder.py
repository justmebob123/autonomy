"""
Base prompt builder for all phases.

This module provides a base class for phase-specific prompt builders,
eliminating duplication in context building and message formatting.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import os


class BasePromptBuilder:
    """
    Base class for phase-specific prompt builders.
    
    Provides common functionality for building prompts, contexts, and messages
    across different phases, reducing code duplication.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the prompt builder.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
    
    def read_file_content(self, filepath: str, max_lines: Optional[int] = None) -> str:
        """
        Read file content with optional line limit.
        
        Args:
            filepath: Path to the file (relative to project root)
            max_lines: Maximum number of lines to read (None for all)
            
        Returns:
            File content as string, or error message if file cannot be read
        """
        full_path = os.path.join(self.project_root, filepath)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (truncated after {max_lines} lines)")
                            break
                        lines.append(line)
                    return ''.join(lines)
                else:
                    return f.read()
        except FileNotFoundError:
            return f"[File not found: {filepath}]"
        except Exception as e:
            return f"[Error reading file {filepath}: {str(e)}]"
    
    def build_file_context(
        self,
        filepath: str,
        include_content: bool = True,
        max_lines: Optional[int] = None
    ) -> str:
        """
        Build context for a single file.
        
        Args:
            filepath: Path to the file
            include_content: Whether to include file content
            max_lines: Maximum lines to include from content
            
        Returns:
            Formatted file context string
        """
        context = f"## File: {filepath}\n\n"
        
        if include_content:
            content = self.read_file_content(filepath, max_lines)
            context += f"```\n{content}\n```\n\n"
        
        return context
    
    def build_multiple_files_context(
        self,
        filepaths: List[str],
        include_content: bool = True,
        max_lines_per_file: Optional[int] = None
    ) -> str:
        """
        Build context for multiple files.
        
        Args:
            filepaths: List of file paths
            include_content: Whether to include file contents
            max_lines_per_file: Maximum lines per file
            
        Returns:
            Formatted context for all files
        """
        if not filepaths:
            return ""
        
        context = "## Related Files\n\n"
        for filepath in filepaths:
            context += self.build_file_context(filepath, include_content, max_lines_per_file)
        
        return context
    
    def build_import_context(self, filepath: str, imports: List[str]) -> str:
        """
        Build context for file imports.
        
        Args:
            filepath: Path to the file
            imports: List of import statements or imported modules
            
        Returns:
            Formatted import context
        """
        if not imports:
            return ""
        
        context = f"## Imports in {filepath}\n\n"
        for imp in imports:
            context += f"- {imp}\n"
        context += "\n"
        
        return context
    
    def build_error_context(self, error: Dict) -> str:
        """
        Build context for an error or issue.
        
        Args:
            error: Dictionary containing error details (type, message, line, file, etc.)
            
        Returns:
            Formatted error context
        """
        context = "## Error Details\n\n"
        
        if 'type' in error:
            context += f"**Type**: {error['type']}\n"
        if 'message' in error:
            context += f"**Message**: {error['message']}\n"
        if 'file' in error:
            context += f"**File**: {error['file']}\n"
        if 'line' in error:
            context += f"**Line**: {error['line']}\n"
        if 'severity' in error:
            context += f"**Severity**: {error['severity']}\n"
        
        context += "\n"
        return context
    
    def build_task_context(self, task: Any) -> str:
        """
        Build context for a task.
        
        Args:
            task: Task object with attributes like task_id, description, target_file, etc.
            
        Returns:
            Formatted task context
        """
        context = "## Task Details\n\n"
        
        if hasattr(task, 'task_id'):
            context += f"**Task ID**: {task.task_id}\n"
        if hasattr(task, 'description'):
            context += f"**Description**: {task.description}\n"
        if hasattr(task, 'target_file'):
            context += f"**Target File**: {task.target_file}\n"
        if hasattr(task, 'attempts'):
            context += f"**Attempts**: {task.attempts}\n"
        if hasattr(task, 'status'):
            context += f"**Status**: {task.status}\n"
        
        context += "\n"
        return context
    
    def build_architectural_context(self, architecture_info: Dict) -> str:
        """
        Build context for architectural information.
        
        Args:
            architecture_info: Dictionary containing architecture details
            
        Returns:
            Formatted architectural context
        """
        if not architecture_info:
            return ""
        
        context = "## Architectural Context\n\n"
        
        if 'patterns' in architecture_info:
            context += "**Patterns Used**:\n"
            for pattern in architecture_info['patterns']:
                context += f"- {pattern}\n"
            context += "\n"
        
        if 'dependencies' in architecture_info:
            context += "**Dependencies**:\n"
            for dep in architecture_info['dependencies']:
                context += f"- {dep}\n"
            context += "\n"
        
        if 'structure' in architecture_info:
            context += f"**Structure**: {architecture_info['structure']}\n\n"
        
        return context
    
    def build_validation_context(self, validation_results: List[Dict]) -> str:
        """
        Build context for validation results.
        
        Args:
            validation_results: List of validation result dictionaries
            
        Returns:
            Formatted validation context
        """
        if not validation_results:
            return ""
        
        context = "## Validation Results\n\n"
        
        for i, result in enumerate(validation_results, 1):
            context += f"### Validation {i}\n"
            if 'status' in result:
                context += f"**Status**: {result['status']}\n"
            if 'message' in result:
                context += f"**Message**: {result['message']}\n"
            if 'details' in result:
                context += f"**Details**: {result['details']}\n"
            context += "\n"
        
        return context
    
    def format_list_as_markdown(self, items: List[str], title: str = None) -> str:
        """
        Format a list of items as markdown.
        
        Args:
            items: List of items to format
            title: Optional title for the list
            
        Returns:
            Formatted markdown list
        """
        if not items:
            return ""
        
        result = ""
        if title:
            result += f"## {title}\n\n"
        
        for item in items:
            result += f"- {item}\n"
        
        result += "\n"
        return result