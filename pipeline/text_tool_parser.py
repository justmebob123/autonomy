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
        
        # Pattern 1: Look for numbered task lists (with or without file paths)
        # Example: "1. **Implement X**: Description..." or "1. Implement X in file.py"
        task_pattern = r'(?:^|\n)\s*\d+\.\s*(.+?)(?=\n\s*\d+\.|$)'
        matches = re.finditer(task_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            task_text = match.group(1).strip()
            # Try to extract with file path first
            task = self._extract_task_info(task_text)
            if task:
                tasks.append(task)
            else:
                # If no file path found, extract task without file path
                task = self._extract_task_without_file(task_text)
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
    
    def _extract_task_without_file(self, task_text: str) -> Optional[Dict]:
        """
        Extract task information when no file path is present.
        Infer a reasonable file path based on the task description.
        """
        # Clean up markdown formatting
        description = re.sub(r'\*\*([^*]+)\*\*', r'\1', task_text)  # Remove **bold**
        description = re.sub(r'\*([^*]+)\*', r'\1', description)      # Remove *italic*
        description = re.sub(r'`([^`]+)`', r'\1', description)        # Remove `code`
        
        # Split on colon if present (e.g., "**Task Name**: Description")
        if ':' in description:
            parts = description.split(':', 1)
            task_name = parts[0].strip()
            task_desc = parts[1].strip() if len(parts) > 1 else task_name
        else:
            task_name = description.strip()
            task_desc = description.strip()
        
        # Limit description length
        if len(task_desc) > 200:
            task_desc = task_desc[:200] + "..."
        
        if len(task_desc) < 10:
            return None
        
        # Infer file path based on task content
        target_file = self._infer_file_path(task_name + " " + task_desc)
        
        return {
            "description": task_desc,
            "target_file": target_file,
            "priority": 50,
            "category": self._infer_category(task_desc),
            "rationale": "Extracted from text response (file path inferred)"
        }
    
    def _infer_file_path(self, text: str) -> str:
        """Infer a reasonable file path based on task description"""
        text_lower = text.lower()
        
        # Check for specific keywords to determine file location
        if any(word in text_lower for word in ['alert', 'alerting', 'notification']):
            return "monitors/alerting.py"
        elif any(word in text_lower for word in ['security', 'threat', 'vulnerability']):
            return "monitors/security.py"
        elif any(word in text_lower for word in ['performance', 'metric', 'optimize']):
            return "monitors/performance.py"
        elif any(word in text_lower for word in ['dashboard', 'ui', 'interface', 'web']):
            return "ui/dashboard.py"
        elif any(word in text_lower for word in ['integration', 'external', 'api']):
            return "integrations/external.py"
        elif any(word in text_lower for word in ['log', 'logging']):
            return "utils/logging.py"
        elif any(word in text_lower for word in ['config', 'configuration']):
            return "config/settings.py"
        elif any(word in text_lower for word in ['test', 'testing']):
            # Extract meaningful test name from description
            name = self._extract_meaningful_name(text)
            return f"tests/test_{name}.py"
        elif any(word in text_lower for word in ['monitor', 'monitoring']):
            return "monitors/system.py"
        else:
            # Extract meaningful name from description instead of generic default
            name = self._extract_meaningful_name(text)
            return f"features/{name}.py"
    
    def _extract_meaningful_name(self, text: str) -> str:
        """Extract a meaningful filename from task description"""
        import re
        
        # Remove common words and extract key terms
        text_lower = text.lower()
        
        # Remove common prefixes
        text_lower = re.sub(r'^(implement|create|add|develop|build|design)\s+', '', text_lower)
        text_lower = re.sub(r'^(the|a|an)\s+', '', text_lower)
        
        # Extract first 2-3 meaningful words
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'more', 
                      'than', 'such', 'when', 'where', 'which', 'will', 'would', 'could',
                      'should', 'about', 'after', 'before', 'between', 'through'}
        meaningful_words = [w for w in words if w not in stop_words][:3]
        
        if meaningful_words:
            # Join with underscores
            return '_'.join(meaningful_words)
        else:
            # Last resort: use first word from original text
            first_word = re.search(r'\b[a-zA-Z]{3,}\b', text)
            if first_word:
                return first_word.group(0).lower()
            else:
                return "feature"  # Absolute fallback
    
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