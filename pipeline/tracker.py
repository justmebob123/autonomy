"""
Task Progress Tracker
"""

import hashlib
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set

from .project import ProjectFiles
from .logging_setup import get_logger


class TaskTracker:
    """Tracks task progress and manages retries"""
    
    def __init__(self, project: ProjectFiles):
        self.project = project
        self.logger = get_logger()
        self.attempts: Dict[str, int] = defaultdict(int)
        self.errors: Dict[str, List[str]] = defaultdict(list)
        self.completed: Set[str] = set()
        self.skipped: Set[str] = set()
    
    def get_task_key(self, task: Dict) -> str:
        desc = task.get("description", "")[:50]
        return hashlib.md5(desc.encode()).hexdigest()[:8]
    
    def record_attempt(self, task: Dict, error: str = None):
        key = self.get_task_key(task)
        self.attempts[key] += 1
        if error:
            self.errors[key].append(error[:200])
    
    def get_errors(self, task: Dict) -> List[str]:
        return self.errors.get(self.get_task_key(task), [])
    
    def should_skip(self, task: Dict, max_retries: int) -> bool:
        return self.attempts[self.get_task_key(task)] >= max_retries
    
    def mark_complete(self, task: Dict):
        self.completed.add(self.get_task_key(task))
    
    def mark_skipped(self, task: Dict):
        self.skipped.add(self.get_task_key(task))
    
    def is_complete(self, task: Dict) -> bool:
        return self.get_task_key(task) in self.completed
    
    def is_skipped(self, task: Dict) -> bool:
        return self.get_task_key(task) in self.skipped
    
    def write_next_steps(self, tasks: List[Dict]):
        content = f"""# NEXT_STEPS.md

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Task Status

| Completed | Skipped | Pending |
|-----------|---------|---------|
| {len(self.completed)} | {len(self.skipped)} | {len(tasks) - len(self.completed) - len(self.skipped)} |

## Tasks

"""
        for i, task in enumerate(tasks, 1):
            key = self.get_task_key(task)
            if key in self.completed:
                status = "[x]"
            elif key in self.skipped:
                status = "[~]"
            else:
                status = "[ ]"
            
            content += f"{i}. {status} {task.get('description', '')}\n"
            if task.get("target_file"):
                content += f"   - File: `{task['target_file']}`\n"
        
        self.project.write("NEXT_STEPS.md", content, validate=False)
    
    def get_summary(self) -> Dict:
        return {
            "completed": len(self.completed),
            "skipped": len(self.skipped),
            "total_attempts": sum(self.attempts.values()),
        }
