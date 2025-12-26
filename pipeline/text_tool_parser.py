"""
Text-based Tool Call Parser

Fallback parser for models that generate tool calls as text instead of structured format.
Extracts tool call information from natural language responses.
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from .logging_setup import get_logger


class TextToolParser:
    """Parse tool calls from text responses"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def parse_project_planning_response(self, content: str) -> List[Dict]:
        """
        Parse project planning tool calls from text response.
        
        Looks for patterns like:
        - Task descriptions
        - Target files
        - Priorities
        - Categories
        """
        tasks = []
        
        # Pattern 1: Look for numbered task lists
        # Example: "1. Implement X in file.py"
        task_pattern = r'(?:^|\n)\s*\d+\.\s*(.+?)(?=\n\s*\d+\.|$)'
        matches = re.finditer(task_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            task_text = match.group(1).strip()
            task = self._extract_task_info(task_text)
            if task:
                tasks.append(task)
        
        # Pattern 2: Look for explicit task proposals
        # Example: "Task: Implement X\nFile: file.py\nPriority: 50"
        task_blocks = re.finditer(
            r'(?:Task|Description):\s*(.+?)\n(?:.*?)(?:File|Target):\s*(.+?)(?:\n|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        for match in task_blocks:
            description = match.group(1).strip()
            target_file = match.group(2).strip()
            
            # Extract priority if present
            priority_match = re.search(r'Priority:\s*(\d+)', content[match.start():match.end()])
            priority = int(priority_match.group(1)) if priority_match else 50
            
            tasks.append({
                "description": description,
                "target_file": target_file,
                "priority": priority,
                "category": self._infer_category(description),
                "rationale": "Extracted from text response"
            })
        
        # Pattern 3: Look for file paths with descriptions
        # Example: "monitors/hardware.py - Implement hardware monitoring"
        file_desc_pattern = r'([a-zA-Z0-9_/]+\.py)\s*[-:]\s*(.+?)(?=\n|$)'
        matches = re.finditer(file_desc_pattern, content)
        
        for match in matches:
            target_file = match.group(1).strip()
            description = match.group(2).strip()
            
            # Avoid duplicates
            if not any(t['target_file'] == target_file for t in tasks):
                tasks.append({
                    "description": description,
                    "target_file": target_file,
                    "priority": 50,
                    "category": self._infer_category(description),
                    "rationale": "Extracted from text response"
                })
        
        return tasks[:5]  # Limit to 5 tasks
    
    def _extract_task_info(self, task_text: str) -> Optional[Dict]:
        """Extract task information from a single task description"""
        
        # Look for file path in the text
        file_match = re.search(r'([a-zA-Z0-9_/]+\.py)', task_text)
        if not file_match:
            return None
        
        target_file = file_match.group(1)
        
        # Extract description (text before or after file path)
        description = task_text.replace(target_file, '').strip()
        description = re.sub(r'^[-:]\s*', '', description)
        description = re.sub(r'\s*[-:]\s*$', '', description)
        
        # Clean up markdown formatting
        description = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)  # Remove **bold**
        description = re.sub(r'\*([^*]+)\*', r'\1', description)      # Remove *italic*
        description = re.sub(r'`([^`]+)`', r'\1', description)        # Remove `code`
        
        # Remove common phrases
        description = re.sub(r'\s+in\s+``\s*$', '', description)      # Remove trailing "in ``"
        description = re.sub(r'\s+in\s+$', '', description)           # Remove trailing "in "
        
        description = description.strip()
        
        if not description or len(description) < 10:
            return None
        
        # Extract priority if mentioned
        priority = 50
        priority_match = re.search(r'priority\s*[:=]?\s*(\d+)', task_text, re.IGNORECASE)
        if priority_match:
            priority = int(priority_match.group(1))
        
        return {
            "description": description,
            "target_file": target_file,
            "priority": priority,
            "category": self._infer_category(description),
            "rationale": "Extracted from text response"
        }
    
    def _infer_category(self, description: str) -> str:
        """Infer task category from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['test', 'testing', 'unit test', 'integration test']):
            return "test"
        elif any(word in desc_lower for word in ['document', 'readme', 'docs']):
            return "documentation"
        elif any(word in desc_lower for word in ['fix', 'bug', 'error', 'issue']):
            return "bugfix"
        elif any(word in desc_lower for word in ['refactor', 'cleanup', 'improve', 'optimize']):
            return "refactor"
        elif any(word in desc_lower for word in ['integrate', 'connect', 'link']):
            return "integration"
        else:
            return "feature"
    
    def create_tool_calls_from_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Convert extracted tasks into tool call format"""
        if not tasks:
            return []
        
        # Create a propose_expansion_tasks tool call
        tool_call = {
            "function": {
                "name": "propose_expansion_tasks",
                "arguments": {
                    "tasks": tasks,
                    "expansion_focus": "Extracted from text response - continuing project development"
                }
            }
        }
        
        return [tool_call]