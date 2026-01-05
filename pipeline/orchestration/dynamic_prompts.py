"""
Dynamic Prompt Builder

Constructs prompts dynamically based on:
- Task complexity
- Model capabilities
- Recent failures
- Project context
- File characteristics
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
import re

from pipeline.logging_setup import get_logger


@dataclass
class PromptContext:
    """Context for building a prompt."""
    phase: str
    task: Dict[str, Any]
    model_size: str  # "14b", "32b", etc.
    model_capabilities: List[str]
    context_window: int
    recent_failures: List[Dict]
    project_context: Optional[Dict] = None
    file_content: Optional[str] = None
    available_tools: Optional[List[Dict]] = None


class PromptSection:
    """A section of a prompt."""
    
    def __init__(self, name: str, content: str, priority: int = 5):
        """
        Initialize a prompt section.
        
        Args:
            name: Section name
            content: Section content
            priority: Priority (1-10, higher = more important)
        """
        self.name = name
        self.content = content
        self.priority = priority
    
    def estimate_tokens(self) -> int:
        """Estimate token count for this section."""
        # Rough approximation: words * 1.3
        return int(len(self.content.split()) * 1.3)


class DynamicPromptBuilder:
    """
    Builds prompts dynamically based on context.
    
    This replaces static prompts with intelligent, adaptive ones.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize the prompt builder.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        self.project_context = self._load_project_context()
    
    def build_prompt(self, context: PromptContext) -> Union[str, List[Dict]]:
        """
        Build a context-aware prompt.
        
        Args:
            context: Prompt context
        
        Returns:
            Single prompt string or list of messages for chunking
        """
        # Assess complexity
        complexity = self._assess_complexity(context)
        
        self.logger.debug(f"Building prompt for {context.phase} (complexity: {complexity}/10)")
        
        # Build sections
        sections = self._build_sections(context, complexity)
        
        # Estimate total tokens
        total_tokens = sum(s.estimate_tokens() for s in sections)
        
        # Check if chunking needed
        max_prompt_tokens = int(context.context_window * 0.7)  # Leave room for response
        
        if total_tokens > max_prompt_tokens:
            self.logger.info(f"  Prompt too large ({total_tokens} tokens), chunking...")
            return self._chunk_prompt(sections, context)
        
        # Assemble single prompt
        return self._assemble_prompt(sections)
    
    def _assess_complexity(self, context: PromptContext) -> int:
        """
        Assess task complexity (1-10).
        
        Args:
            context: Prompt context
        
        Returns:
            Complexity score
        """
        complexity = 5  # baseline
        
        task = context.task
        
        # File size
        if context.file_content:
            file_size = len(context.file_content)
            if file_size > 5000:
                complexity += 3
            elif file_size > 2000:
                complexity += 2
            elif file_size > 1000:
                complexity += 1
        
        # Dependencies
        dependencies = task.get("dependencies", [])
        complexity += min(2, len(dependencies) * 0.5)
        
        # Recent failures
        attempts = task.get("attempts", 0)
        if attempts > 3:
            complexity += 2
        elif attempts > 1:
            complexity += 1
        
        # Phase-specific complexity
        if context.phase == "debugging":
            complexity += 1
        elif context.phase == "qa":
            complexity += 1
        
        return min(10, int(complexity))
    
    def _build_sections(self, context: PromptContext, complexity: int) -> List[PromptSection]:
        """
        Build prompt sections based on context.
        
        Args:
            context: Prompt context
            complexity: Task complexity
        
        Returns:
            List of PromptSection objects
        """
        sections = []
        
        # 1. Role definition (always included)
        sections.append(self._build_role_section(context))
        
        # 2. Task description (always included)
        sections.append(self._build_task_section(context))
        
        # 3. Context (filtered by relevance)
        if context.file_content:
            sections.append(self._build_file_section(context))
        
        # 4. Tools (filtered by phase and task)
        if context.available_tools:
            sections.append(self._build_tools_section(context))
        
        # 5. Examples (if needed based on failures or model size)
        if self._needs_examples(context):
            sections.append(self._build_examples_section(context))
        
        # 6. Project standards (if available)
        if self.project_context:
            sections.append(self._build_standards_section(context))
        
        # 7. Failure adaptations (if recent failures)
        if context.recent_failures:
            sections.append(self._build_failure_adaptations(context))
        
        return sections
    
    def _build_role_section(self, context: PromptContext) -> PromptSection:
        """Build role definition section."""
        
        # Model-specific role descriptions
        if context.model_size in ["3b", "7b", "14b"]:
            pass
            # Simpler role for smaller models
            role = f"You are a {context.phase} specialist. Your job is to {self._get_simple_job_description(context.phase)}."
        else:
            pass
            # More sophisticated role for larger models
            role = f"You are a senior {context.phase} specialist with deep expertise. {self._get_detailed_job_description(context.phase)}"
        
        return PromptSection("role", role, priority=10)
    
    def _get_simple_job_description(self, phase: str) -> str:
        """Get simple job description for phase."""
        descriptions = {
            "coding": "write Python code",
            "qa": "find issues in code",
            "debugging": "fix code errors",
            "planning": "create task plans",
            "documentation": "write documentation"
        }
        return descriptions.get(phase, "complete tasks")
    
    def _get_detailed_job_description(self, phase: str) -> str:
        """Get detailed job description for phase."""
        descriptions = {
            "coding": "You design and implement production-quality Python code with proper architecture, error handling, and documentation.",
            "qa": "You perform comprehensive code reviews, identifying issues ranging from syntax errors to architectural concerns.",
            "debugging": "You diagnose and fix code issues efficiently, understanding both symptoms and root causes.",
            "planning": "You create strategic implementation plans that balance complexity, dependencies, and project goals.",
            "documentation": "You write clear, comprehensive documentation that helps users understand and use the system."
        }
        return descriptions.get(phase, "You complete tasks with expertise and attention to detail.")
    
    def _build_task_section(self, context: PromptContext) -> PromptSection:
        """Build task description section."""
        
        task = context.task
        description = task.get("description", "")
        target_file = task.get("target_file", "")
        
        content = f"TASK: {description}"
        if target_file:
            content += f"\nFILE: {target_file}"
        
        return PromptSection("task", content, priority=9)
    
    def _build_file_section(self, context: PromptContext) -> PromptSection:
        """Build file content section."""
        
        content = f"```python\n{context.file_content}\n```"
        
        return PromptSection("file", content, priority=8)
    
    def _build_tools_section(self, context: PromptContext) -> PromptSection:
        """Build tools section with filtered, relevant tools."""
        
        # Filter tools by phase and task
        relevant_tools = self._filter_tools(context)
        
        content = "AVAILABLE TOOLS:\n"
        for tool in relevant_tools:
            content += f"\n- {tool['name']}: {tool.get('description', '')}"
        
        content += "\n\nCRITICAL: You MUST use tools. Do not just describe what to do."
        
        return PromptSection("tools", content, priority=7)
    
    def _filter_tools(self, context: PromptContext) -> List[Dict]:
        """Filter tools by relevance to task."""
        
        if not context.available_tools:
            return []
        
        # Phase-specific tool filtering
        phase_tools = {
            "coding": ["create_python_file", "create_file", "modify_python_file", "read_file", "search_code"],
            "qa": ["report_issue", "approve_code", "read_file", "search_code", "list_directory"],
            "debugging": ["modify_python_file", "read_file", "search_code", "execute_command"],
            "planning": ["create_task_plan", "propose_expansion_tasks", "analyze_project_status"],
        }
        
        relevant_names = phase_tools.get(context.phase, [])
        
        # Filter tools
        filtered = [
            tool for tool in context.available_tools
            if tool["name"] in relevant_names
        ]
        
        # If no phase-specific tools, return all
        return filtered if filtered else context.available_tools
    
    def _needs_examples(self, context: PromptContext) -> bool:
        """Determine if examples are needed."""
        
        # Always provide examples for smaller models
        if context.model_size in ["3b", "7b", "14b"]:
            return True
        
        # Provide examples if recent failures
        if context.recent_failures:
            return True
        
        # Provide examples for complex tasks
        complexity = self._assess_complexity(context)
        if complexity >= 7:
            return True
        
        return False
    
    def _build_examples_section(self, context: PromptContext) -> PromptSection:
        """Build examples section based on failures and phase."""
        
        content = "EXAMPLES:\n"
        
        # Phase-specific examples
        if context.phase == "qa":
            content += """
1. Found syntax error:
   Call: report_issue(type="SyntaxError", description="Missing colon after if statement", line=42)

2. Found missing import:
   Call: report_issue(type="ImportError", description="Module 'os' is used but not imported", line=10)

3. Code is perfect:
   Call: approve_code(filepath="example.py")
"""
        
        elif context.phase == "coding":
            content += """
1. Create new file:
   Call: create_python_file(filepath="utils/helper.py", code="...")

2. Modify existing file:
   Call: modify_python_file(filepath="main.py", operation="str_replace", ...)
"""
        
        # Add failure-specific examples
        if context.recent_failures:
            content += "\n" + self._get_failure_examples(context.recent_failures)
        
        return PromptSection("examples", content, priority=6)
    
    def _get_failure_examples(self, failures: List[Dict]) -> str:
        """Get examples based on recent failures."""
        
        examples = []
        
        failure_types = [f.get("type", "") for f in failures]
        
        if "empty_tool_name" in failure_types:
            examples.append("""
WRONG: {"function": {"name": "", "arguments": {...}}}
RIGHT: {"function": {"name": "report_issue", "arguments": {...}}}
""")
        
        if "unknown_tool" in failure_types:
            examples.append("""
WRONG: Using tool names that don't exist
RIGHT: Use ONLY the tools listed in AVAILABLE TOOLS
""")
        
        if "no_tool_calls" in failure_types:
            examples.append("""
WRONG: "I found an issue on line 10"
RIGHT: report_issue(type="...", description="...", line=10)
""")
        
        return "\n".join(examples)
    
    def _build_standards_section(self, context: PromptContext) -> PromptSection:
        """Build project standards section."""
        
        content = "PROJECT STANDARDS:\n"
        
        if self.project_context.get("import_style"):
            content += f"- Imports: {self.project_context['import_style']}\n"
        
        if self.project_context.get("docstring_style"):
            content += f"- Docstrings: {self.project_context['docstring_style']}\n"
        
        if self.project_context.get("common_imports"):
            content += f"- Common imports: {', '.join(self.project_context['common_imports'][:5])}\n"
        
        return PromptSection("standards", content, priority=4)
    
    def _build_failure_adaptations(self, context: PromptContext) -> PromptSection:
        """Build failure adaptation section."""
        
        content = "⚠️ IMPORTANT REMINDERS:\n"
        
        failure_types = [f.get("type", "") for f in context.recent_failures]
        
        if failure_types.count("empty_tool_name") > 1:
            content += "- Tool calls MUST have a name field\n"
        
        if failure_types.count("unknown_tool") > 1:
            content += "- Use ONLY the tools listed above\n"
        
        if failure_types.count("no_tool_calls") > 1:
            content += "- You MUST call tools, not just describe\n"
        
        return PromptSection("adaptations", content, priority=8)
    
    def _assemble_prompt(self, sections: List[PromptSection]) -> str:
        """Assemble sections into a single prompt."""
        
        # Sort by priority (highest first)
        sections.sort(key=lambda s: s.priority, reverse=True)
        
        # Join sections
        return "\n\n".join(s.content for s in sections)
    
    def _chunk_prompt(self, sections: List[PromptSection], 
                     context: PromptContext) -> List[Dict]:
        """
        Chunk prompt into multiple messages.
        
        Args:
            sections: Prompt sections
            context: Prompt context
        
        Returns:
            List of message dicts
        """
        messages = []
        
        # Sort by priority
        sections.sort(key=lambda s: s.priority, reverse=True)
        
        # System message (role)
        role_section = next((s for s in sections if s.name == "role"), None)
        if role_section:
            messages.append({
                "role": "system",
                "content": role_section.content
            })
            sections.remove(role_section)
        
        # Chunk remaining sections
        max_tokens_per_message = int(context.context_window * 0.3)
        current_chunk = []
        current_tokens = 0
        
        for section in sections:
            section_tokens = section.estimate_tokens()
            
            if current_tokens + section_tokens > max_tokens_per_message and current_chunk:
                pass
                # Flush current chunk
                messages.append({
                    "role": "user",
                    "content": "\n\n".join(s.content for s in current_chunk)
                })
                current_chunk = [section]
                current_tokens = section_tokens
            else:
                current_chunk.append(section)
                current_tokens += section_tokens
        
        # Flush remaining
        if current_chunk:
            messages.append({
                "role": "user",
                "content": "\n\n".join(s.content for s in current_chunk)
            })
        
        self.logger.info(f"  Chunked prompt into {len(messages)} messages")
        
        return messages
    
    def _load_project_context(self) -> Dict[str, Any]:
        """Load project-specific context."""
        
        context = {}
        
        # Detect import style
        context["import_style"] = self._detect_import_style()
        
        # Detect docstring style
        context["docstring_style"] = self._detect_docstring_style()
        
        # Get common imports
        context["common_imports"] = self._get_common_imports()
        
        return context
    
    def _detect_import_style(self) -> str:
        """Detect project's import style."""
        # Simple detection - could be more sophisticated
        return "absolute imports preferred"
    
    def _detect_docstring_style(self) -> str:
        """Detect project's docstring style."""
        # Simple detection
        return "Google style"
    
    def _get_common_imports(self) -> List[str]:
        """Get commonly used imports in project."""
        # Simple list - could analyze actual files
        return ["pathlib", "typing", "datetime", "json"]