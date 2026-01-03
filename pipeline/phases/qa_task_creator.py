"""
QA Task Creator.

Handles creation of fix tasks for issues found during QA,
extracted from the QAPhase class to reduce complexity.
"""

from typing import List, Dict
import logging
from datetime import datetime


class QATaskCreator:
    """
    Creates fix tasks for issues found during QA review.
    
    This is CRITICAL for the coordinator to route issues to debugging phase.
    Without this, issues are reported but never fixed.
    """
    
    def __init__(self, project_dir: str, logger: logging.Logger = None):
        """
        Initialize QA task creator.
        
        Args:
            project_dir: Project directory path
            logger: Optional logger instance
        """
        self.project_dir = project_dir
        self.logger = logger or logging.getLogger('QATaskCreator')
    
    def create_fix_tasks_for_issues(
        self,
        state,  # PipelineState
        filepath: str,
        issues: List[Dict]
    ):
        """
        Create NEEDS_FIXES tasks for each issue found.
        
        This is CRITICAL for the coordinator to route to debugging phase.
        Without this, issues are reported but never fixed.
        
        Args:
            state: PipelineState object
            filepath: Path to the file with issues
            issues: List of issues found during QA
        """
        from ..state.manager import TaskStatus, TaskState, StateManager
        
        if not issues:
            return
        
        self.logger.info(f"  🔧 Creating {len(issues)} NEEDS_FIXES tasks for {filepath}")
        
        for idx, issue in enumerate(issues):
            # Create unique task ID
            task_id = f"qa_fix_{filepath.replace('/', '_')}_{issue.get('line_number', idx)}"
            
            # Check if task already exists
            if task_id in state.tasks:
                self.logger.debug(f"    ⏭️  Task {task_id} already exists, skipping")
                continue
            
            # Determine priority based on severity
            severity = issue.get('severity', 'medium')
            priority_map = {
                'critical': 1,
                'high': 5,
                'medium': 10,
                'low': 20
            }
            priority = priority_map.get(severity, 10)
            
            # Create task
            task = TaskState(
                task_id=task_id,
                description=f"Fix {issue.get('issue_type', 'issue')} in {filepath}: {issue.get('description', 'No description')}",
                target_file=filepath,
                status=TaskStatus.NEEDS_FIXES,
                priority=priority,
                created_at=datetime.now().isoformat()
            )
            
            # Store issue data in task for debugging phase
            task.metadata = {
                'issue_type': issue.get('issue_type'),
                'line_number': issue.get('line_number'),
                'severity': severity,
                'description': issue.get('description'),
                'source': 'qa_phase'
            }
            
            # Add to state
            state.tasks[task_id] = task
            self.logger.info(f"    ✅ Created task {task_id} (priority {priority})")
        
        # Save state immediately so coordinator sees the tasks
        state_manager = StateManager(self.project_dir)
        state_manager.save(state)
        self.logger.info(f"  💾 Saved state with {len(issues)} new NEEDS_FIXES tasks")