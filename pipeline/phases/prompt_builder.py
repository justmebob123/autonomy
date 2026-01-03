"""
Prompt Builder

Builds prompts from templates with variable substitution.
Eliminates duplication across prompt methods.
"""

from pathlib import Path
from typing import Dict, Any
import logging


class PromptBuilder:
    """Builds prompts from templates with variable sections."""
    
    def __init__(self, templates_dir: Path, logger: logging.Logger = None):
        """
        Initialize prompt builder.
        
        Args:
            templates_dir: Directory containing prompt templates
            logger: Logger instance
        """
        self.templates_dir = Path(templates_dir)
        self.logger = logger or logging.getLogger(__name__)
        self.templates = {}
        
        # Load templates if directory exists
        if self.templates_dir.exists():
            self._load_templates()
    
    def _load_templates(self):
        """Load all template files from templates directory."""
        for template_file in self.templates_dir.glob("*.txt"):
            template_name = template_file.stem
            try:
                self.templates[template_name] = template_file.read_text()
                self.logger.debug(f"Loaded template: {template_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load template {template_name}: {e}")
    
    def build(self, template_name: str, **variables) -> str:
        """
        Build prompt from template with variables.
        
        Args:
            template_name: Name of the template to use
            **variables: Variables to substitute in template
        
        Returns:
            Formatted prompt string
        """
        # Get template
        template = self.templates.get(template_name)
        
        if not template:
            self.logger.warning(f"Template '{template_name}' not found, using fallback")
            return self._build_fallback_prompt(**variables)
        
        # Substitute variables
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.error(f"Missing variable in template '{template_name}': {e}")
            return self._build_fallback_prompt(**variables)
    
    def _build_fallback_prompt(self, **variables) -> str:
        """Build a basic fallback prompt when template is missing."""
        context = variables.get('context', '')
        task_type = variables.get('task_type', 'TASK')
        
        return f"""🎯 {task_type.upper()}

{context}

📋 WORKFLOW:

Please analyze the context above and take appropriate action to resolve this task.
"""
    
    def get_template_config(self, issue_type: str) -> Dict[str, Any]:
        """
        Get template configuration for a specific issue type.
        
        Args:
            issue_type: Type of refactoring issue
        
        Returns:
            Dictionary with template variables
        """
        configs = {
            'missing_method': {
                'task_type': 'MISSING METHOD',
                'action': 'IMPLEMENT THE METHOD',
                'critical_note': '⚠️ CRITICAL: This is a SIMPLE task - just implement the missing method!',
                'workflow_label': 'SIMPLE WORKFLOW (2-3 steps)',
                'workflow_steps': self._get_missing_method_steps(),
                'warnings': self._get_missing_method_warnings(),
                'completion_note': '🎯 TAKE ACTION NOW - This should take 1-2 tool calls, not 10+!'
            },
            'duplicate_code': {
                'task_type': 'DUPLICATE CODE',
                'action': 'MERGE THE FILES',
                'critical_note': '',
                'workflow_label': 'SIMPLE WORKFLOW (2-3 steps)',
                'workflow_steps': self._get_duplicate_code_steps(),
                'warnings': self._get_duplicate_code_warnings(),
                'completion_note': '🎯 TAKE ACTION NOW - Merge the files to complete this task!'
            },
            'integration_conflict': {
                'task_type': 'INTEGRATION CONFLICT',
                'action': 'RESOLVE THE CONFLICT',
                'critical_note': '⚠️ STEP-AWARE: Only do what hasn\'t been done yet!',
                'workflow_label': 'WORKFLOW',
                'workflow_steps': self._get_integration_conflict_steps(),
                'warnings': self._get_integration_conflict_warnings(),
                'completion_note': '🎯 TAKE ACTION - Follow the workflow step by step!'
            },
            'dead_code': {
                'task_type': 'DEAD CODE',
                'action': 'ANALYZE AND REPORT',
                'critical_note': '⚠️ CRITICAL: This is an EARLY-STAGE project - DO NOT auto-remove code!',
                'workflow_label': 'SIMPLE WORKFLOW (2-3 steps)',
                'workflow_steps': self._get_dead_code_steps(),
                'warnings': self._get_dead_code_warnings(),
                'completion_note': '🎯 TAKE ACTION NOW - Create the issue report!'
            },
            'complexity': {
                'task_type': 'COMPLEXITY',
                'action': 'REFACTOR OR REPORT',
                'critical_note': '',
                'workflow_label': 'WORKFLOW (try to fix first)',
                'workflow_steps': self._get_complexity_steps(),
                'warnings': self._get_complexity_warnings(),
                'completion_note': '🎯 TAKE ACTION - Try to refactor, or create issue report!'
            },
            'architecture_violation': {
                'task_type': 'ARCHITECTURE VIOLATION',
                'action': 'FIX THE STRUCTURE',
                'critical_note': '',
                'workflow_label': 'WORKFLOW',
                'workflow_steps': self._get_architecture_violation_steps(),
                'warnings': '',
                'completion_note': '🎯 TAKE ACTION - Fix the architecture violation!'
            },
            'bug_fix': {
                'task_type': 'BUG FIX',
                'action': 'FIX THE BUG',
                'critical_note': '',
                'workflow_label': 'SIMPLE WORKFLOW',
                'workflow_steps': self._get_bug_fix_steps(),
                'warnings': '',
                'completion_note': '🎯 TAKE ACTION - Fix the bug!'
            }
        }
        
        return configs.get(issue_type, self._get_generic_config())
    
    def _get_missing_method_steps(self) -> str:
        return """1️⃣ **Read the file** to see the class definition:
   read_file(filepath="<file_path>")

2️⃣ **Implement the method** OR create issue report:
   
   **Option A - Implement directly** (PREFERRED if straightforward):
   - If it's a simple method (getter, setter, utility), implement it
   - Use modify_file or insert_after to add the method
   - Example: Adding a generate_risk_chart method that creates a chart
   
   **Option B - Create issue report** (if requires domain knowledge):
   - Use create_issue_report if you need to understand business logic
   - Provide clear description of what the method should do
   - Include code examples and suggestions"""
    
    def _get_missing_method_warnings(self) -> str:
        return """⚠️ DO NOT:
- List all source files (you already know which file)
- Find related files (not needed for adding a method)
- Map relationships (not needed for this task)
- Compare implementations (nothing to compare)

✅ JUST:
- Read the file
- Implement the method OR create report
- Done!"""
    
    def _get_duplicate_code_steps(self) -> str:
        return """1️⃣ **OPTIONAL: Compare files** to understand differences:
   compare_file_implementations(file1="<file1>", file2="<file2>")
   
2️⃣ **Merge the files** (REQUIRED - this resolves the task):

⚠️ CRITICAL OUTPUT FORMAT - Use JSON, NOT Python syntax:

CORRECT JSON FORMAT:
{
    "name": "merge_file_implementations",
    "arguments": {
        "source_files": ["<file1>", "<file2>"],
        "target_file": "<file1>",
        "strategy": "ai_merge"
    }
}

WRONG (Python syntax - parser cannot handle lists):
merge_file_implementations(
    source_files=["<file1>", "<file2>"],
    target_file="<file1>",
    strategy="ai_merge"
)"""
    
    def _get_duplicate_code_warnings(self) -> str:
        return """⚠️ DO NOT:
- List all source files (you already know which files to merge)
- Find related files (task specifies the files)
- Map relationships (not needed for merging)
- Just compare and stop (that's analysis, not resolution)

✅ WORKFLOW:
- Compare (optional, for understanding)
- Merge (required, resolves the task)
- Done!"""
    
    def _get_integration_conflict_steps(self) -> str:
        return """1️⃣ **Read architecture** (if not done):
   read_file(filepath="ARCHITECTURE.md")

2️⃣ **Read target files** (if not done):
   read_file(filepath="<file1>")
   read_file(filepath="<file2>")

3️⃣ **Compare implementations** (if not done):
   compare_file_implementations(file1="<file1>", file2="<file2>")

4️⃣ **Resolve the conflict**:
   - Use merge_file_implementations for similar files
   - Use create_issue_report for complex conflicts
   - Use modify_file for targeted fixes"""
    
    def _get_integration_conflict_warnings(self) -> str:
        return """⚠️ CHECK WHAT'S BEEN DONE:
- Don't repeat tool calls
- Skip steps that are already complete
- Focus on what's missing"""
    
    def _get_dead_code_steps(self) -> str:
        return """1️⃣ **Search for usages** of the code:
   search_code(pattern="<class_name>", file_types=["py"])

2️⃣ **Create issue report** (REQUIRED for early-stage projects):
   create_issue_report(
       title="Dead Code: <class_name>",
       description="Analysis of <class_name> usage",
       severity="low",
       recommendations=["Keep for now", "Monitor usage", "Remove if still unused after X months"]
   )"""
    
    def _get_dead_code_warnings(self) -> str:
        return """⚠️ DO NOT:
- Auto-remove code (project is early-stage)
- Delete without analysis
- Assume code is unused without searching

✅ DO:
- Search for usages
- Create issue report
- Recommend monitoring"""
    
    def _get_complexity_steps(self) -> str:
        return """1️⃣ **Read the file** to understand the complex function:
   read_file(filepath="<file_path>")

2️⃣ **Try to refactor** if straightforward:
   - Break into smaller functions
   - Extract common logic
   - Simplify conditionals
   - Use modify_file to implement

3️⃣ **Create issue report** if too complex:
   - Describe the complexity
   - Suggest refactoring approaches
   - Provide examples"""
    
    def _get_complexity_warnings(self) -> str:
        return """⚠️ TRY TO FIX FIRST:
- Attempt refactoring if straightforward
- Only create report if truly complex"""
    
    def _get_architecture_violation_steps(self) -> str:
        return """1️⃣ **Check architecture** to understand correct location:
   read_file(filepath="ARCHITECTURE.md")

2️⃣ **Fix the violation**:
   - Use move_file to relocate misplaced files
   - Use rename_file to fix naming issues
   - Use restructure_directory for large changes"""
    
    def _get_bug_fix_steps(self) -> str:
        return """1️⃣ **Read the file** to understand the bug:
   read_file(filepath="<file_path>")

2️⃣ **Fix the bug**:
   - Use modify_file to implement the fix
   - Ensure the fix addresses the root cause"""
    
    def _get_generic_config(self) -> Dict[str, Any]:
        return {
            'task_type': 'REFACTORING',
            'action': 'COMPLETE THE TASK',
            'critical_note': '',
            'workflow_label': 'WORKFLOW',
            'workflow_steps': 'Analyze the task and take appropriate action.',
            'warnings': '',
            'completion_note': '🎯 TAKE ACTION - Complete the task!'
        }