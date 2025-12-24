"""
Pipeline Agents

Specialized agents for different pipeline phases:
- PlanningAgent: Creates development plans from specifications
- CodingAgent: Implements code based on task descriptions
- QAAgent: Reviews code for quality issues
- DebugAgent: Fixes code issues
"""

from typing import Dict, List, Tuple

from .config import PipelineConfig
from .client import OllamaClient, ResponseParser
from .handlers import ToolCallHandler
from .project import ProjectFiles
from .tools import get_tools_for_phase
from .prompts import (
    SYSTEM_PROMPTS, 
    get_planning_prompt, 
    get_coding_prompt,
    get_qa_prompt,
    get_debug_prompt
)
from .logging_setup import get_logger


class BaseAgent:
    """Base class for pipeline agents"""
    
    def __init__(self, client: OllamaClient, project: ProjectFiles, config: PipelineConfig):
        self.client = client
        self.project = project
        self.config = config
        self.logger = get_logger()
        self.parser = ResponseParser()


class PlanningAgent(BaseAgent):
    """Creates development plans from project specifications"""
    
    def create_plan(self, master_plan: str) -> List[Dict]:
        """
        Create a task plan from MASTER_PLAN.md
        
        Returns:
            List of task dictionaries with description, target_file, priority
        """
        self.logger.info("\n📋 PLANNING PHASE")
        
        # Get model for planning
        model_info = self.client.get_model_for_task("planning")
        if not model_info:
            self.logger.error("No model available for planning")
            return []
        
        host, model = model_info
        self.logger.info(f"  Using: {model} on {host}")
        
        # Build context
        existing_files = self.project.list_files([".py"])
        existing_list = "\n".join([
            f"  - {f.relative_to(self.project.project_dir)}" 
            for f in existing_files[:10]
        ]) or "(no files yet)"
        
        # Create messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["planning"]},
            {"role": "user", "content": get_planning_prompt(master_plan, existing_list)}
        ]
        
        # Get tools for planning phase
        tools = get_tools_for_phase("planning")
        
        # Send request - timeout from config (None = wait forever)
        temperature = self.config.temperatures.get("planning", 0.5)
        timeout = self.config.planning_timeout
        
        response = self.client.chat(host, model, messages, tools, temperature, timeout)
        
        if "error" in response:
            self.logger.error(f"Planning failed: {response['error']}")
            return []
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if tool_calls:
            # Process tool calls
            handler = ToolCallHandler(self.project.project_dir)
            handler.process_tool_calls(tool_calls)
            
            if handler.tasks:
                return handler.tasks
        
        # Fallback: try to parse tasks from text content
        if content:
            self.logger.warning("  Model returned text instead of tool call")
            self.logger.debug(f"  Content: {content[:300]}...")
            
            tasks = self.parser.extract_tasks_from_text(content)
            if tasks:
                self.logger.info(f"  Extracted {len(tasks)} tasks from text")
                return tasks
        
        self.logger.error("  Could not extract tasks from response")
        return []


class CodingAgent(BaseAgent):
    """Implements code based on task descriptions"""
    
    def implement_task(self, task: Dict, previous_errors: List[str] = None) -> Tuple[bool, List[Dict]]:
        """
        Implement a single development task.
        
        Args:
            task: Task dictionary with description, target_file
            previous_errors: List of error messages from previous attempts
            
        Returns:
            Tuple of (success, results)
        """
        description = task.get("description", "")[:60]
        self.logger.info(f"\n🔨 IMPLEMENTING: {description}...")
        
        # Get model for coding
        model_info = self.client.get_model_for_task("coding")
        if not model_info:
            self.logger.error("No model available for coding")
            return False, []
        
        host, model = model_info
        self.logger.info(f"  Using: {model} on {host}")
        
        # Build context
        context = self.project.get_context(max_files=3, max_chars=3000)
        
        error_context = ""
        if previous_errors:
            error_context = "\n".join(f"- {e}" for e in previous_errors[-3:])
        
        # Create messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["coding"]},
            {"role": "user", "content": get_coding_prompt(
                task.get("description", ""),
                task.get("target_file", ""),
                context,
                error_context
            )}
        ]
        
        # Get tools
        tools = get_tools_for_phase("coding")
        
        # Send request - timeout from config (None = wait forever)
        temperature = self.config.temperatures.get("coding", 0.2)
        timeout = self.config.coding_timeout
        
        response = self.client.chat(host, model, messages, tools, temperature, timeout)
        
        if "error" in response:
            self.logger.error(f"Coding failed: {response['error']}")
            return False, []
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No tool calls in response")
            if content:
                self.logger.debug(f"  Content: {content[:200]}...")
            return False, []
        
        # Execute tool calls
        handler = ToolCallHandler(self.project.project_dir)
        results = handler.process_tool_calls(tool_calls)
        
        # Check if any files were created successfully
        success = len(handler.files_created) > 0 or len(handler.files_modified) > 0
        
        return success, results


class QAAgent(BaseAgent):
    """Reviews code for quality issues"""
    
    def review_file(self, filepath: str) -> Tuple[bool, List[Dict]]:
        """
        Review a single file for quality issues.
        
        Args:
            filepath: Path to file to review
            
        Returns:
            Tuple of (passed, issues)
        """
        self.logger.info(f"\n🔍 REVIEWING: {filepath}")
        
        # Read file
        content = self.project.read(filepath)
        if not content:
            return False, [{"error": f"File not found: {filepath}"}]
        
        # Get model for QA
        model_info = self.client.get_model_for_task("qa")
        if not model_info:
            self.logger.error("No model available for QA")
            return False, []
        
        host, model = model_info
        self.logger.info(f"  Using: {model} on {host}")
        
        # Create messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["qa"]},
            {"role": "user", "content": get_qa_prompt(filepath, content)}
        ]
        
        # Get tools
        tools = get_tools_for_phase("qa")
        
        # Send request - timeout from config (None = wait forever)
        temperature = self.config.temperatures.get("qa", 0.3)
        timeout = self.config.qa_timeout
        
        response = self.client.chat(host, model, messages, tools, temperature, timeout)
        
        if "error" in response:
            self.logger.error(f"QA failed: {response['error']}")
            return False, []
        
        # Parse response
        tool_calls, content = self.parser.parse_response(response)
        
        if not tool_calls:
            # No tool calls could mean approval by omission
            self.logger.info("  No issues reported (implicit approval)")
            return True, []
        
        # Execute tool calls
        handler = ToolCallHandler(self.project.project_dir)
        handler.process_tool_calls(tool_calls)
        
        # Check results
        if handler.approved:
            return True, []
        
        return len(handler.issues) == 0, handler.issues


class DebugAgent(BaseAgent):
    """Fixes code issues"""
    
    def fix_issue(self, issue: Dict) -> bool:
        """
        Fix a reported issue.
        
        Args:
            issue: Issue dictionary from QA
            
        Returns:
            True if fix was successful
        """
        filepath = issue.get("filepath")
        self.logger.info(f"\n🔧 FIXING: {filepath} - {issue.get('type', 'unknown')}")
        
        # Read file
        content = self.project.read(filepath)
        if not content:
            self.logger.error(f"File not found: {filepath}")
            return False
        
        # Get model for debugging
        model_info = self.client.get_model_for_task("debugging")
        if not model_info:
            self.logger.error("No model available for debugging")
            return False
        
        host, model = model_info
        self.logger.info(f"  Using: {model} on {host}")
        
        # Create messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["debugging"]},
            {"role": "user", "content": get_debug_prompt(filepath, content, issue)}
        ]
        
        # Get tools
        tools = get_tools_for_phase("debugging")
        
        # Send request - no timeout (wait forever)
        temperature = self.config.temperatures.get("debugging", 0.2)
        timeout = self.config.request_timeout
        
        response = self.client.chat(host, model, messages, tools, temperature, timeout)
        
        if "error" in response:
            self.logger.error(f"Debug failed: {response['error']}")
            return False
        
        # Parse response
        tool_calls, _ = self.parser.parse_response(response)
        
        if not tool_calls:
            self.logger.warning("  No fix applied")
            return False
        
        # Execute tool calls
        handler = ToolCallHandler(self.project.project_dir)
        handler.process_tool_calls(tool_calls)
        
        return len(handler.files_modified) > 0
