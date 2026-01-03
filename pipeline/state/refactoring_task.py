"""
Refactoring Task Management

This module defines the RefactoringTask class for tracking refactoring work
across multiple iterations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from .manager import TaskStatus


class RefactoringIssueType(Enum):
    """Types of refactoring issues"""
    DUPLICATE = "duplicate"
    COMPLEXITY = "complexity"
    DEAD_CODE = "dead_code"
    ARCHITECTURE = "architecture"
    CONFLICT = "conflict"
    INTEGRATION = "integration"
    NAMING = "naming"
    STRUCTURE = "structure"


class RefactoringPriority(Enum):
    """Priority levels for refactoring tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RefactoringApproach(Enum):
    """How to handle the refactoring"""
    AUTONOMOUS = "autonomous"  # AI fixes automatically
    DEVELOPER_REVIEW = "developer_review"  # Too complex, needs human
    NEEDS_NEW_CODE = "needs_new_code"  # Requires new implementation


@dataclass
class RefactoringTask:
    """
    Represents a single refactoring task.
    
    Refactoring tasks are created during analysis and track specific
    issues that need to be fixed. They support multi-iteration refactoring
    by maintaining state across executions.
    """
    
    # Identity
    task_id: str
    issue_type: RefactoringIssueType
    
    # Description
    title: str
    description: str
    
    # Scope
    target_files: List[str]
    affected_components: List[str] = field(default_factory=list)
    
    # Priority and approach
    priority: RefactoringPriority = RefactoringPriority.MEDIUM
    fix_approach: RefactoringApproach = RefactoringApproach.AUTONOMOUS
    
    # Status
    status: TaskStatus = TaskStatus.NEW
    
    # Execution details
    fix_details: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 999  # Effectively unlimited - continuous until resolved
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Analysis results
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other task IDs
    blocks: List[str] = field(default_factory=list)  # Tasks blocked by this
    
    # Metrics
    estimated_effort: Optional[int] = None  # Minutes
    actual_effort: Optional[int] = None  # Minutes
    complexity_score: Optional[float] = None  # 0.0 - 1.0
    impact_score: Optional[float] = None  # 0.0 - 1.0
    
    def can_execute(self, completed_tasks: List[str]) -> bool:
        """
        Check if this task can be executed.
        
        Args:
            completed_tasks: List of completed task IDs
            
        Returns:
            True if all dependencies are met
        """
        if self.status not in [TaskStatus.NEW, TaskStatus.FAILED]:
            return False
        
        if self.attempts >= self.max_attempts:
            return False
        
        # Check dependencies
        for dep_id in self.depends_on:
            if dep_id not in completed_tasks:
                return False
        
        return True
    
    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.attempts += 1
    
    def complete(self, fix_details: str) -> None:
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.fix_details = fix_details
        
        if self.started_at:
            duration = (datetime.now() - self.started_at).total_seconds() / 60
            self.actual_effort = int(duration)
    
    def fail(self, error_message: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
    
    def needs_review(self, reason: str) -> None:
        """Mark task as needing developer review"""
        self.fix_approach = RefactoringApproach.DEVELOPER_REVIEW
        self.status = TaskStatus.BLOCKED
        self.error_message = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "issue_type": self.issue_type.value,
            "title": self.title,
            "description": self.description,
            "target_files": self.target_files,
            "affected_components": self.affected_components,
            "priority": self.priority.value,
            "fix_approach": self.fix_approach.value,
            "status": self.status.value,
            "fix_details": self.fix_details,
            "error_message": self.error_message,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "analysis_data": self.analysis_data,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "estimated_effort": self.estimated_effort,
            "actual_effort": self.actual_effort,
            "complexity_score": self.complexity_score,
            "impact_score": self.impact_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefactoringTask':
        """Create from dictionary"""
        # Convert enums
        data["issue_type"] = RefactoringIssueType(data["issue_type"])
        data["priority"] = RefactoringPriority(data["priority"])
        data["fix_approach"] = RefactoringApproach(data["fix_approach"])
        data["status"] = TaskStatus(data["status"])
        
        # Convert timestamps
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        
        return cls(**data)


class RefactoringTaskManager:
    """
    Manages refactoring tasks across iterations.
    
    Provides methods for creating, updating, querying, and tracking
    refactoring tasks.
    """
    
    def __init__(self):
        self.tasks: Dict[str, RefactoringTask] = {}
        self._next_id = 1
        
        # CRITICAL: Track resolved issues to prevent re-detection
        self.resolution_history: Dict[str, Dict[str, Any]] = {
            'resolved': {},  # Issues that were successfully fixed
            'escalated': {},  # Issues that were escalated to coding phase
            'false_positives': {}  # Issues marked as false positives
        }
        
        # Track detection counts for false positive detection
        self.detection_counts: Dict[str, int] = {}
    
    def create_task(
        self,
        issue_type: RefactoringIssueType,
        title: str,
        description: str,
        target_files: List[str],
        priority: RefactoringPriority = RefactoringPriority.MEDIUM,
        fix_approach: RefactoringApproach = RefactoringApproach.AUTONOMOUS,
        **kwargs
    ) -> RefactoringTask:
        """
        Create a new refactoring task.
        
        Args:
            issue_type: Type of refactoring issue
            title: Short title
            description: Detailed description
            target_files: Files affected
            priority: Task priority
            fix_approach: How to handle the task
            **kwargs: Additional task attributes
            
        Returns:
            Created RefactoringTask
        """
        from pathlib import Path
        
        # VALIDATION: Filter out invalid file paths
        valid_files = []
        for file_path in target_files:
            if not file_path or file_path == '':
                continue
            
            # Skip backup directories
            if '.autonomy' in file_path or '/backups/' in file_path or '\\backups\\' in file_path:
                continue
            
            # Skip placeholder paths
            if 'some_file' in file_path or 'unknown' in file_path:
                continue
            
            valid_files.append(file_path)
        
        # If no valid files, skip task creation
        if not valid_files:
            if hasattr(self, 'logger'):
                self.logger.warning(f"⚠️ Skipping task creation - no valid files: {target_files}")
            return None
        
        task_id = f"refactor_{self._next_id:04d}"
        self._next_id += 1
        
        task = RefactoringTask(
            task_id=task_id,
            issue_type=issue_type,
            title=title,
            description=description,
            target_files=valid_files,  # Use validated files
            priority=priority,
            fix_approach=fix_approach,
            **kwargs
        )
        
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[RefactoringTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        Update task attributes.
        
        Args:
            task_id: Task ID
            **kwargs: Attributes to update
            
        Returns:
            True if updated, False if task not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        return True
    
    def get_pending_tasks(self) -> List[RefactoringTask]:
        """Get all tasks that can be executed"""
        completed_ids = [
            task.task_id for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED
        ]
        
        return [
            task for task in self.tasks.values()
            if task.can_execute(completed_ids)
        ]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[RefactoringTask]:
        """Get all tasks with given status"""
        return [
            task for task in self.tasks.values()
            if task.status == status
        ]
    
    def get_tasks_by_priority(self, priority: RefactoringPriority) -> List[RefactoringTask]:
        """Get all tasks with given priority"""
        return [
            task for task in self.tasks.values()
            if task.priority == priority
        ]
    
    def get_tasks_by_type(self, issue_type: RefactoringIssueType) -> List[RefactoringTask]:
        """Get all tasks of given type"""
        return [
            task for task in self.tasks.values()
            if task.issue_type == issue_type
        ]
    
    def get_blocked_tasks(self) -> List[RefactoringTask]:
        """Get all tasks needing developer review"""
        return [
            task for task in self.tasks.values()
            if task.fix_approach == RefactoringApproach.DEVELOPER_REVIEW
        ]
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get refactoring progress statistics.
        
        Returns:
            Dictionary with progress metrics
        """
        total = len(self.tasks)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0,
                "blocked": 0,
                "completion_percentage": 0.0
            }
        
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        in_progress = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        pending = len(self.get_pending_tasks())
        failed = len(self.get_tasks_by_status(TaskStatus.FAILED))
        blocked = len(self.get_blocked_tasks())
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "blocked": blocked,
            "completion_percentage": (completed / total) * 100
        }
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a specific task by ID.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def clear_completed(self) -> int:
        """
        Remove completed tasks.
        
        Returns:
            Number of tasks removed
        """
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        return len(completed_ids)
    
    def get_issue_key(self, issue_type: str, target_files: List[str]) -> str:
        """
        Generate a unique key for an issue based on type and files.
        
        This is used to track if the same issue has been seen before.
        """
        # Sort files for consistent key generation
        sorted_files = sorted(target_files)
        files_str = ':'.join(sorted_files)
        return f"{issue_type}:{files_str}"
    
    def is_issue_already_handled(self, issue_type: str, target_files: List[str]) -> tuple[bool, str]:
        """
        Check if an issue has already been handled.
        
        Returns:
            (is_handled, reason) tuple
        """
        issue_key = self.get_issue_key(issue_type, target_files)
        
        # Check if resolved
        if issue_key in self.resolution_history['resolved']:
            return (True, 'already_resolved')
        
        # Check if escalated
        if issue_key in self.resolution_history['escalated']:
            return (True, 'already_escalated')
        
        # Check if false positive
        if issue_key in self.resolution_history['false_positives']:
            return (True, 'false_positive')
        
        return (False, '')
    
    def record_resolution(self, issue_type: str, target_files: List[str], 
                         resolution_type: str, task_id: str = None, 
                         details: Dict[str, Any] = None):
        """
        Record that an issue has been resolved.
        
        Args:
            issue_type: Type of issue
            target_files: Files involved
            resolution_type: 'resolved', 'escalated', or 'false_positive'
            task_id: Associated task ID (if any)
            details: Additional details about the resolution
        """
        issue_key = self.get_issue_key(issue_type, target_files)
        
        record = {
            'issue_type': issue_type,
            'target_files': target_files,
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'details': details or {}
        }
        
        if resolution_type == 'resolved':
            self.resolution_history['resolved'][issue_key] = record
        elif resolution_type == 'escalated':
            self.resolution_history['escalated'][issue_key] = record
        elif resolution_type == 'false_positive':
            self.resolution_history['false_positives'][issue_key] = record
    
    def increment_detection_count(self, issue_type: str, target_files: List[str]) -> int:
        """
        Increment detection count for an issue.
        
        Returns the new count. Used for false positive detection.
        """
        issue_key = self.get_issue_key(issue_type, target_files)
        current_count = self.detection_counts.get(issue_key, 0)
        new_count = current_count + 1
        self.detection_counts[issue_key] = new_count
        return new_count
    
    def should_mark_as_false_positive(self, issue_type: str, target_files: List[str]) -> bool:
        """
        Check if an issue should be marked as a false positive.
        
        Criteria: Detected 3+ times but never successfully resolved.
        """
        issue_key = self.get_issue_key(issue_type, target_files)
        
        # Check detection count
        count = self.detection_counts.get(issue_key, 0)
        if count < 3:
            return False
        
        # Check if ever resolved
        if issue_key in self.resolution_history['resolved']:
            return False
        
        # Detected multiple times but never resolved = likely false positive
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            },
            "next_id": self._next_id,
            "resolution_history": self.resolution_history,
            "detection_counts": self.detection_counts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefactoringTaskManager':
        """Create from dictionary"""
        manager = cls()
        manager._next_id = data.get("next_id", 1)
        
        for task_id, task_data in data.get("tasks", {}).items():
            task = RefactoringTask.from_dict(task_data)
            manager.tasks[task_id] = task
        
        # Load resolution history
        manager.resolution_history = data.get("resolution_history", {
            'resolved': {},
            'escalated': {},
            'false_positives': {}
        })
        manager.detection_counts = data.get("detection_counts", {})
        
        return manager