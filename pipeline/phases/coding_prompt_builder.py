"""
Coding Phase Prompt Builder.

Handles all prompt and context building for the Coding phase,
extracted from the CodingPhase class to reduce complexity.
"""

from typing import List, Dict, Optional
from .shared.base_prompt_builder import BasePromptBuilder


class CodingPromptBuilder(BasePromptBuilder):
    """
    Prompt builder specifically for Coding phase operations.
    
    Handles building contexts for imports, architecture, validation,
    and user messages for the coding phase.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize Coding prompt builder.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
    
    def build_context(
        self,
        task,  # TaskState
        related_files: List[str] = None
    ) -> str:
        """
        Build comprehensive context for a coding task.
        
        Args:
            task: TaskState object with task details
            related_files: Optional list of related files to include
            
        Returns:
            Formatted context string
        """
        context = self.build_task_context(task)
        
        # Add target file content if it exists
        if task.target_file:
            context += self.build_file_context(
                task.target_file,
                include_content=True,
                max_lines=500
            )
        
        # Add related files if provided
        if related_files:
            context += self.build_multiple_files_context(
                related_files,
                include_content=True,
                max_lines_per_file=200
            )
        
        return context
    
    def build_import_context(self, filepath: str) -> str:
        """
        Build context for imports in a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Formatted import context
        """
        import ast
        import os
        
        full_path = os.path.join(self.project_root, filepath)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            if imports:
                return self.build_import_context(filepath, imports)
            else:
                return ""
                
        except Exception as e:
            return f"## Import Analysis\n\nCould not analyze imports: {str(e)}\n\n"
    
    def build_architectural_context(self, architecture_info: Dict) -> str:
        """
        Build architectural context for coding decisions.
        
        Args:
            architecture_info: Dictionary with architecture details
            
        Returns:
            Formatted architectural context
        """
        if not architecture_info:
            return ""
        
        context = "## Architectural Guidelines\n\n"
        
        if 'patterns' in architecture_info:
            context += "**Design Patterns to Follow**:\n"
            for pattern in architecture_info['patterns']:
                context += f"- {pattern}\n"
            context += "\n"
        
        if 'conventions' in architecture_info:
            context += "**Coding Conventions**:\n"
            for convention in architecture_info['conventions']:
                context += f"- {convention}\n"
            context += "\n"
        
        if 'structure' in architecture_info:
            context += f"**Project Structure**: {architecture_info['structure']}\n\n"
        
        if 'dependencies' in architecture_info:
            context += "**Allowed Dependencies**:\n"
            for dep in architecture_info['dependencies']:
                context += f"- {dep}\n"
            context += "\n"
        
        return context
    
    def build_user_message(
        self,
        task,  # TaskState
        context: str,
        import_context: str = "",
        architectural_context: str = ""
    ) -> str:
        """
        Build the complete user message for the AI.
        
        Args:
            task: TaskState object
            context: Main context string
            import_context: Import context string
            architectural_context: Architectural context string
            
        Returns:
            Complete formatted user message
        """
        message = f"""# Coding Task

{self.build_task_context(task)}

{context}

{import_context}

{architectural_context}

## Instructions

Please implement the requested changes following these guidelines:

1. **Code Quality**: Write clean, maintainable, well-documented code
2. **Error Handling**: Include appropriate error handling and validation
3. **Testing**: Consider testability in your implementation
4. **Performance**: Be mindful of performance implications
5. **Architecture**: Follow the project's architectural patterns

## Deliverables

- Implement the required functionality
- Add appropriate documentation/comments
- Ensure code follows project conventions
- Handle edge cases and errors appropriately

"""
        return message
    
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
        
        context = "## Previous Validation Results\n\n"
        context += "The following issues were found in previous attempts:\n\n"
        
        for i, result in enumerate(validation_results, 1):
            context += f"### Attempt {i}\n"
            if 'status' in result:
                status_icon = "✅" if result['status'] == 'passed' else "❌"
                context += f"{status_icon} **Status**: {result['status']}\n"
            if 'issues' in result:
                context += "**Issues Found**:\n"
                for issue in result['issues']:
                    context += f"- {issue}\n"
            if 'message' in result:
                context += f"**Message**: {result['message']}\n"
            context += "\n"
        
        context += "Please address these issues in your implementation.\n\n"
        return context
    
    def build_filename_issue_context(
        self,
        filepath: str,
        issue_description: str
    ) -> str:
        """
        Build context for filename-related issues.
        
        Args:
            filepath: Path to the file with issues
            issue_description: Description of the filename issue
            
        Returns:
            Formatted filename issue context
        """
        context = f"""## Filename Issue Detected

**File**: {filepath}
**Issue**: {issue_description}

### Common Filename Issues

1. **Naming Conventions**: Files should follow project naming conventions (e.g., snake_case for Python)
2. **Descriptive Names**: Filenames should clearly indicate the file's purpose
3. **Avoid Special Characters**: Use only alphanumeric characters, underscores, and hyphens
4. **Appropriate Extension**: Ensure the file extension matches the content type

### Recommendations

- Review the filename and ensure it follows project conventions
- Consider if the filename accurately describes the file's purpose
- Check if the file is in the correct directory according to the architecture

"""
        return context
    
    def build_qa_phase_message(
        self,
        filepath: str,
        task_id: str,
        timestamp: str
    ) -> str:
        """
        Build message to send to QA phase after coding completion.
        
        Args:
            filepath: Path to the completed file
            task_id: ID of the completed task
            timestamp: Timestamp of completion
            
        Returns:
            Formatted message for QA_READ.md
        """
        message = f"""
## Coding Task Completed - {timestamp}

**File**: {filepath}
**Task ID**: {task_id}
**Status**: ✅ Ready for QA Review

### Changes Made

The coding task has been completed and the file is ready for quality assurance review.

### Next Steps

1. Review the code for quality issues
2. Check for potential bugs or edge cases
3. Verify adherence to coding standards
4. Run automated analysis tools
5. Approve or send back for fixes

**Priority**: Please review at your earliest convenience.

"""
        return message