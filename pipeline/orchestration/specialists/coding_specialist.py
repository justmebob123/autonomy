"""
Coding Specialist

Expert model for complex code implementation tasks.
Uses qwen2.5-coder:32b on ollama02 for maximum coding capability.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodingTask:
    """Represents a coding task with context"""
    file_path: str
    task_type: str  # 'create', 'modify', 'refactor', 'fix'
    description: str
    context: Dict[str, Any]
    dependencies: List[str] = None
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.constraints is None:
            self.constraints = []


class CodingSpecialist:
    """
    Specialist for complex code implementation.
    
    Capabilities:
    - Write new code from specifications
    - Modify existing code with precision
    - Refactor code for better quality
    - Fix bugs with root cause analysis
    - Ensure code quality and best practices
    """
    
    def __init__(self, model_tool):
        """
        Initialize coding specialist.
        
        Args:
            model_tool: ModelTool instance configured for coding
        """
        self.model_tool = model_tool
        self.coding_standards = self._load_coding_standards()
        
    def _load_coding_standards(self) -> Dict[str, Any]:
        """Load project coding standards"""
        return {
            "python": {
                "style": "PEP 8",
                "max_line_length": 100,
                "docstring_style": "Google",
                "type_hints": "required",
                "imports": {
                    "order": ["standard", "third_party", "local"],
                    "grouping": "required"
                }
            },
            "quality": {
                "complexity": "max_10_per_function",
                "duplication": "avoid",
                "error_handling": "explicit",
                "logging": "structured"
            }
        }
    
    def get_system_prompt(self, task: CodingTask) -> str:
        """
        Generate specialized system prompt for coding task.
        
        Args:
            task: The coding task to perform
            
        Returns:
            Specialized system prompt
        """
        base_prompt = """You are an expert coding specialist with deep knowledge of software engineering best practices.

Your responsibilities:
1. Write clean, maintainable, well-documented code
2. Follow project coding standards strictly
3. Implement proper error handling and logging
4. Consider edge cases and potential issues
5. Ensure code is testable and modular
6. Use appropriate design patterns
7. Optimize for readability and performance

"""
        
        # Add task-specific guidance
        task_guidance = self._get_task_guidance(task.task_type)
        
        # Add coding standards
        standards = f"""
Coding Standards:
- Style: {self.coding_standards['python']['style']}
- Max line length: {self.coding_standards['python']['max_line_length']}
- Docstrings: {self.coding_standards['python']['docstring_style']} style
- Type hints: {self.coding_standards['python']['type_hints']}
- Import order: {', '.join(self.coding_standards['python']['imports']['order'])}

Quality Requirements:
- Max complexity: {self.coding_standards['quality']['complexity']}
- Error handling: {self.coding_standards['quality']['error_handling']}
- Logging: {self.coding_standards['quality']['logging']}
"""
        
        # Add constraints if any
        constraints_text = ""
        if task.constraints:
            constraints_text = "\nConstraints:\n" + "\n".join(f"- {c}" for c in task.constraints)
        
        return base_prompt + task_guidance + standards + constraints_text
    
    def _get_task_guidance(self, task_type: str) -> str:
        """Get specific guidance for task type"""
        guidance = {
            "create": """
Task Type: CREATE NEW CODE
- Start with clear interface design
- Implement incrementally with tests
- Document all public APIs
- Consider future extensibility
""",
            "modify": """
Task Type: MODIFY EXISTING CODE
- Understand existing implementation first
- Preserve backward compatibility
- Update related documentation
- Maintain consistent style
""",
            "refactor": """
Task Type: REFACTOR CODE
- Preserve existing functionality
- Improve code structure and readability
- Reduce complexity and duplication
- Add tests if missing
""",
            "fix": """
Task Type: FIX BUG
- Identify root cause first
- Fix the cause, not symptoms
- Add test to prevent regression
- Document the fix
"""
        }
        return guidance.get(task_type, "")
    
    def get_available_tools(self, task: CodingTask) -> List[Dict[str, Any]]:
        """
        Get tools available for this coding task.
        
        Args:
            task: The coding task
            
        Returns:
            List of tool definitions
        """
        # Base tools always available
        base_tools = [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "search_code",
                "description": "Search for code patterns in files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to search for"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to search in (e.g., '*.py')"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        ]
        
        # Add task-specific tools
        if task.task_type in ["modify", "refactor", "fix"]:
            base_tools.append({
                "name": "get_file_context",
                "description": "Get context about a file (imports, classes, functions)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file"
                        }
                    },
                    "required": ["file_path"]
                }
            })
        
        if task.task_type == "fix":
            base_tools.append({
                "name": "run_tests",
                "description": "Run tests to verify fix",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_path": {
                            "type": "string",
                            "description": "Path to test file or directory"
                        }
                    },
                    "required": ["test_path"]
                }
            })
        
        return base_tools
    
    def execute_task(self, task: CodingTask) -> Dict[str, Any]:
        """
        Execute a coding task.
        
        Args:
            task: The coding task to execute
            
        Returns:
            Result with code, tool calls, and metadata
        """
        logger.info(f"CodingSpecialist executing {task.task_type} task for {task.file_path}")
        
        # Build context message
        context_parts = [
            f"Task: {task.task_type.upper()}",
            f"File: {task.file_path}",
            f"Description: {task.description}"
        ]
        
        if task.dependencies:
            context_parts.append(f"Dependencies: {', '.join(task.dependencies)}")
        
        if task.context:
            context_parts.append(f"\nContext:\n{self._format_context(task.context)}")
        
        context_message = "\n".join(context_parts)
        
        # Get system prompt and tools
        system_prompt = self.get_system_prompt(task)
        tools = self.get_available_tools(task)
        
        # Execute with model tool
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": context_message}],
            system_prompt=system_prompt,
            tools=tools
        )
        
        # Analyze result
        analysis = self._analyze_result(result, task)
        
        return {
            "success": result.get("success", False),
            "response": result.get("response", ""),
            "tool_calls": result.get("tool_calls", []),
            "analysis": analysis,
            "task": task
        }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}:")
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _analyze_result(self, result: Dict[str, Any], task: CodingTask) -> Dict[str, Any]:
        """
        Analyze coding result for quality and completeness.
        
        Args:
            result: Result from model execution
            task: Original task
            
        Returns:
            Analysis with quality metrics
        """
        analysis = {
            "complete": False,
            "quality_score": 0.0,
            "issues": [],
            "suggestions": []
        }
        
        # Check if task appears complete
        tool_calls = result.get("tool_calls", [])
        response = result.get("response", "")
        
        # Basic completeness check
        has_write = any(tc.get("name") == "write_file" for tc in tool_calls)
        has_explanation = len(response) > 100
        
        if has_write and has_explanation:
            analysis["complete"] = True
            analysis["quality_score"] = 0.7  # Base score
        
        # Check for quality indicators in response
        quality_indicators = [
            ("error handling", 0.1),
            ("type hint", 0.05),
            ("docstring", 0.1),
            ("test", 0.05),
            ("logging", 0.05)
        ]
        
        response_lower = response.lower()
        for indicator, score_boost in quality_indicators:
            if indicator in response_lower:
                analysis["quality_score"] += score_boost
        
        # Cap at 1.0
        analysis["quality_score"] = min(1.0, analysis["quality_score"])
        
        # Check for potential issues
        if not has_write:
            analysis["issues"].append("No file write operation performed")
        
        if len(response) < 50:
            analysis["issues"].append("Response too brief, may lack detail")
        
        if analysis["quality_score"] < 0.5:
            analysis["suggestions"].append("Consider adding more quality features (error handling, tests, docs)")
        
        return analysis
    
    def review_code(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Review code for quality and best practices.
        
        Args:
            file_path: Path to the code file
            code: Code content to review
            
        Returns:
            Review with issues and suggestions
        """
        logger.info(f"CodingSpecialist reviewing code in {file_path}")
        
        review_prompt = f"""Review the following code for quality and best practices:

File: {file_path}

Code:
```python
{code}
```

Provide a detailed review covering:
1. Code quality and style
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Be specific and actionable in your feedback."""

        result = self.model_tool.execute(
            messages=[{"role": "user", "content": review_prompt}],
            system_prompt=self.get_system_prompt(CodingTask(
                file_path=file_path,
                task_type="review",
                description="Code review",
                context={}
            ))
        )
        
        return {
            "file_path": file_path,
            "review": result.get("response", ""),
            "success": result.get("success", False)
        }


def create_coding_specialist(model_tool) -> CodingSpecialist:
    """
    Factory function to create a coding specialist.
    
    Args:
        model_tool: ModelTool instance configured for coding
        
    Returns:
        CodingSpecialist instance
    """
    return CodingSpecialist(model_tool)