"""
Priority Queue

Manages task prioritization across pipeline phases.
"""

from enum import IntEnum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import heapq

from pipeline.logging_setup import get_logger


class TaskPriority(IntEnum):
    """Task priority levels (lower = more urgent)"""
    CRITICAL_BUG = 1      # Syntax errors blocking execution
    QA_FAILURE = 2        # QA rejected, needs fix
    DEBUG_PENDING = 3     # Fix attempted, needs re-QA
    IN_PROGRESS = 4       # Currently being worked on
    INCOMPLETE = 5        # Started but not finished
    NEW_TASK = 6          # Not yet started
    LOW = 7               # Optional/nice-to-have
    DEFERRED = 10         # Explicitly deferred
    
    # Production code priorities (10-80)
    CORE_INFRASTRUCTURE = 10    # Config, logging, base classes
    ESSENTIAL_FEATURES = 30     # Core business logic
    SECONDARY_FEATURES = 50     # Additional features
    OPTIONAL_FEATURES = 70      # Nice-to-have features
    
    # Tests and docs (much lower priority)
    TESTS = 200                 # Only if explicitly requested
    DOCUMENTATION = 300         # Only if explicitly requested


@dataclass(order=True)
class PriorityItem:
    """Item in the priority queue"""
    priority: int
    task_id: str = field(compare=False)
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)
    
    def to_dict(self) -> Dict:
        return {
            "priority": self.priority,
            "task_id": self.task_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PriorityItem":
        return cls(**data)


class PriorityQueue:
    """
    Priority queue for task management.
    
    Uses a min-heap so lower priority numbers are processed first.
    Supports dynamic priority updates and filtering.
    """
    
    def __init__(self):
        self._heap: List[PriorityItem] = []
        self._task_map: Dict[str, PriorityItem] = {}
        self._removed: set = set()
        self.logger = get_logger()
    
    def push(self, task_id: str, priority: int = TaskPriority.NEW_TASK,
             metadata: Dict = None):
        """Add a task to the queue"""
        if task_id in self._task_map and task_id not in self._removed:
            # Update existing task
            self.update_priority(task_id, priority, metadata)
            return
        
        item = PriorityItem(
            priority=priority,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        self._task_map[task_id] = item
        self._removed.discard(task_id)
        heapq.heappush(self._heap, item)
    
    def pop(self) -> Optional[PriorityItem]:
        """Remove and return the highest priority task"""
        while self._heap:
            item = heapq.heappop(self._heap)
            if item.task_id not in self._removed:
                del self._task_map[item.task_id]
                return item
        return None
    
    def peek(self) -> Optional[PriorityItem]:
        """Return the highest priority task without removing it"""
        while self._heap:
            if self._heap[0].task_id in self._removed:
                heapq.heappop(self._heap)
            else:
                return self._heap[0]
        return None
    
    def remove(self, task_id: str):
        """Mark a task as removed (lazy deletion)"""
        if task_id in self._task_map:
            self._removed.add(task_id)
            del self._task_map[task_id]
    
    def update_priority(self, task_id: str, new_priority: int,
                        metadata: Dict = None):
        """Update the priority of an existing task"""
        if task_id in self._task_map:
            # Mark old entry as removed
            self._removed.add(task_id)
        
        # Add new entry with updated priority
        item = PriorityItem(
            priority=new_priority,
            task_id=task_id,
            metadata=metadata or self._task_map.get(task_id, PriorityItem(0, "")).metadata
        )
        
        self._task_map[task_id] = item
        self._removed.discard(task_id)
        heapq.heappush(self._heap, item)
    
    def get_priority(self, task_id: str) -> Optional[int]:
        """Get the current priority of a task"""
        if task_id in self._task_map and task_id not in self._removed:
            return self._task_map[task_id].priority
        return None
    
    def contains(self, task_id: str) -> bool:
        """Check if a task is in the queue"""
        return task_id in self._task_map and task_id not in self._removed
    
    def __len__(self) -> int:
        """Return number of active tasks"""
        return len(self._task_map) - len(self._removed & set(self._task_map.keys()))
    
    def __bool__(self) -> bool:
        """Return True if queue has tasks"""
        return len(self) > 0
    
    def clear(self):
        """Clear the queue"""
        self._heap = []
        self._task_map = {}
        self._removed = set()
    
    def get_all(self, sorted: bool = True) -> List[PriorityItem]:
        """Get all active tasks"""
        items = [
            item for item in self._task_map.values()
            if item.task_id not in self._removed
        ]
        if sorted:
            items.sort(key=lambda x: x.priority)
        return items
    
    def get_by_priority(self, priority: int) -> List[PriorityItem]:
        """Get all tasks with a specific priority"""
        return [
            item for item in self._task_map.values()
            if item.priority == priority and item.task_id not in self._removed
        ]
    
    def get_by_priority_range(self, min_priority: int, 
                               max_priority: int) -> List[PriorityItem]:
        """Get all tasks within a priority range"""
        return [
            item for item in self._task_map.values()
            if min_priority <= item.priority <= max_priority
            and item.task_id not in self._removed
        ]
    
    def to_list(self) -> List[Dict]:
        """Export queue as list of dicts"""
        return [item.to_dict() for item in self.get_all()]
    
    def from_list(self, items: List[Dict]):
        """Import queue from list of dicts"""
        self.clear()
        for item_data in items:
            item = PriorityItem.from_dict(item_data)
            self.push(item.task_id, item.priority, item.metadata)
    
    def compact(self):
        """Remove all lazy-deleted items from the heap"""
        self._heap = [
            item for item in self._heap
            if item.task_id not in self._removed
        ]
        heapq.heapify(self._heap)
        self._removed.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        items = self.get_all(sorted=False)
        
        by_priority = {}
        for item in items:
            p = item.priority
            by_priority[p] = by_priority.get(p, 0) + 1
        
        return {
            "total": len(items),
            "by_priority": by_priority,
            "critical": len(self.get_by_priority(TaskPriority.CRITICAL_BUG)),
            "qa_failures": len(self.get_by_priority(TaskPriority.QA_FAILURE)),
            "pending": len(self.get_by_priority_range(
                TaskPriority.DEBUG_PENDING, TaskPriority.NEW_TASK
            )),
        }
