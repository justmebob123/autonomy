"""
State Manager

Handles persistence and loading of pipeline state across all phases.
Enables crash recovery and phase coordination.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

from ..logging_setup import get_logger


class TaskStatus(str, Enum):
    """Status of a task in the pipeline"""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    QA_PENDING = "QA_PENDING"
    QA_FAILED = "QA_FAILED"
    DEBUG_PENDING = "DEBUG_PENDING"
    NEEDS_FIXES = "NEEDS_FIXES"  # Alias for compatibility


class FileStatus(str, Enum):
    """QA status of a file"""
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class TaskError:
    """Record of an error that occurred during task execution"""
    attempt: int
    error_type: str
    message: str
    timestamp: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    phase: str = "coding"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TaskError":
        return cls(**data)


@dataclass
class TaskState:
    """State of a single task"""
    task_id: str
    description: str
    target_file: str
    priority: int
    status: TaskStatus
    attempts: int = 0
    created: str = ""
    completed: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    errors: List[TaskError] = field(default_factory=list)
    issues: List[Dict] = field(default_factory=list)  # QA issues
    created_at: str = ""  # Alias for compatibility
    updated_at: str = ""  # For tracking updates
    
    # Objective linking (NEW)
    objective_id: Optional[str] = None  # e.g., "primary_001"
    objective_level: Optional[str] = None  # e.g., "primary"
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = self.created
        if not self.updated_at:
            self.updated_at = self.created
        if isinstance(self.status, str):
            # Handle both uppercase and lowercase status values
            status_upper = self.status.upper()
            # Map NEEDS_FIXES to QA_FAILED for compatibility
            if status_upper == "NEEDS_FIXES":
                self.status = TaskStatus.QA_FAILED
            else:
                self.status = TaskStatus(status_upper)
        self.errors = [
            TaskError.from_dict(e) if isinstance(e, dict) else e 
            for e in self.errors
        ]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["errors"] = [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.errors]
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TaskState":
        return cls(**data)
    
    def add_error(self, error_type: str, message: str, 
                  line_number: int = None, code_snippet: str = None,
                  phase: str = "coding"):
        """Add an error to this task's history"""
        self.errors.append(TaskError(
            attempt=self.attempts,
            error_type=error_type,
            message=message,
            timestamp=datetime.now().isoformat(),
            line_number=line_number,
            code_snippet=code_snippet,
            phase=phase
        ))
        self.updated_at = datetime.now().isoformat()
    
    def get_error_context(self, max_errors: int = 5) -> str:
        """Get formatted error context for LLM"""
        if not self.errors:
            return ""
        
        lines = ["Previous errors for this task:"]
        for err in self.errors[-max_errors:]:
            lines.append(f"- Attempt {err.attempt} [{err.error_type}]: {err.message}")
            if err.line_number:
                lines.append(f"  Line: {err.line_number}")
            if err.code_snippet:
                lines.append(f"  Code: {err.code_snippet[:100]}")
        
        return "\n".join(lines)


@dataclass
class FileState:
    """State of a tracked file"""
    filepath: str
    hash: str
    created: str
    last_modified: str
    last_qa: Optional[str] = None
    qa_status: FileStatus = FileStatus.UNKNOWN
    size: int = 0
    issues: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.qa_status, str):
            self.qa_status = FileStatus(self.qa_status)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["qa_status"] = self.qa_status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FileState":
        return cls(**data)


@dataclass
class PhaseState:
    """State of a pipeline phase"""
    last_run: Optional[str] = None
    runs: int = 0
    successes: int = 0
    failures: int = 0
    
    # Run history (limited to last N runs for temporal pattern detection)
    run_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 20  # Keep last 20 runs
    
    # Aliases for compatibility
    @property
    def run_count(self) -> int:
        return self.runs
    
    @property
    def success_count(self) -> int:
        return self.successes
    
    @property
    def failure_count(self) -> int:
        return self.failures
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PhaseState":
        return cls(**data)
    
    def record_run(self, success: bool, task_id: str = None, 
                   files_created: List[str] = None, 
                   files_modified: List[str] = None):
        """Record a phase run with full details"""
        self.last_run = datetime.now().isoformat()
        self.runs += 1
        
        if success:
            self.successes += 1
        else:
            self.failures += 1
        
        # Record in history
        run_record = {
            'timestamp': self.last_run,
            'success': success,
            'task_id': task_id,
            'files_created': files_created or [],
            'files_modified': files_modified or []
        }
        
        self.run_history.append(run_record)
        
        # Limit history size
        if len(self.run_history) > self.max_history:
            self.run_history = self.run_history[-self.max_history:]
    
    def get_consecutive_failures(self) -> int:
        """Count consecutive failures from end of history"""
        count = 0
        for run in reversed(self.run_history):
            if not run['success']:
                count += 1
            else:
                break
        return count
    
    def get_consecutive_successes(self) -> int:
        """Count consecutive successes from end of history"""
        count = 0
        for run in reversed(self.run_history):
            if run['success']:
                count += 1
            else:
                break
        return count
    
    def get_recent_success_rate(self, n: int = 5) -> float:
        """Get success rate over last N runs"""
        recent = self.run_history[-n:] if len(self.run_history) >= n else self.run_history
        if not recent:
            return 0.0
        successes = sum(1 for r in recent if r['success'])
        return successes / len(recent)
    
    def is_improving(self, window: int = 5) -> bool:
        """Check if success rate is improving"""
        if len(self.run_history) < window * 2:
            return False
        
        older = self.run_history[-window*2:-window]
        recent = self.run_history[-window:]
        
        older_rate = sum(1 for r in older if r['success']) / len(older)
        recent_rate = sum(1 for r in recent if r['success']) / len(recent)
        
        return recent_rate > older_rate
    
    def is_degrading(self, window: int = 5) -> bool:
        """Check if success rate is degrading"""
        if len(self.run_history) < window * 2:
            return False
        
        older = self.run_history[-window*2:-window]
        recent = self.run_history[-window:]
        
        older_rate = sum(1 for r in older if r['success']) / len(older)
        recent_rate = sum(1 for r in recent if r['success']) / len(recent)
        
        return recent_rate < older_rate
    
    def is_oscillating(self, threshold: int = 3) -> bool:
        """Check if alternating between success and failure"""
        if len(self.run_history) < threshold * 2:
            return False
        
        recent = self.run_history[-threshold*2:]
        changes = 0
        
        for i in range(1, len(recent)):
            if recent[i]['success'] != recent[i-1]['success']:
                changes += 1
        
        # If changes >= threshold, it's oscillating
        return changes >= threshold


@dataclass
class PipelineState:
    """Complete pipeline state"""
    version: int = 2
    updated: str = ""
    pipeline_run_id: str = ""
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    files: Dict[str, FileState] = field(default_factory=dict)
    phases: Dict[str, PhaseState] = field(default_factory=dict)
    queue: List[Dict] = field(default_factory=list)
    
    # Expansion tracking fields (for continuous operation)
    expansion_count: int = 0
    last_doc_update_count: int = 0
    project_maturity: str = "initial"  # initial, developing, mature
    last_planning_iteration: int = 0
    
    # Learning and intelligence fields (from unified_state integration)
    performance_metrics: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
    learned_patterns: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
    fix_history: List[Dict] = field(default_factory=list)
    troubleshooting_results: List[Dict] = field(default_factory=list)
    correlations: List[Dict] = field(default_factory=list)
    
    # Loop prevention fields
    no_update_counts: Dict[str, int] = field(default_factory=dict)
    phase_history: List[str] = field(default_factory=list)
    
    # Strategic management fields (NEW)
    objectives: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Structure: objectives[level][objective_id] = Objective dict
    # Example: objectives["primary"]["primary_001"] = {...}
    
    issues: Dict[str, Any] = field(default_factory=dict)
    # Structure: issues[issue_id] = Issue dict
    # Example: issues["issue_001"] = {...}
    
    def __post_init__(self):
        if not self.updated:
            self.updated = datetime.now().isoformat()
        if not self.pipeline_run_id:
            self.pipeline_run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize phase states (including new phases)
        for phase in ["planning", "coding", "qa", "debug", "project_planning", "documentation"]:
            if phase not in self.phases:
                self.phases[phase] = PhaseState()
        
        # Convert dicts to proper objects
        self.tasks = {
            k: TaskState.from_dict(v) if isinstance(v, dict) else v
            for k, v in self.tasks.items()
        }
        self.files = {
            k: FileState.from_dict(v) if isinstance(v, dict) else v
            for k, v in self.files.items()
        }
        self.phases = {
            k: PhaseState.from_dict(v) if isinstance(v, dict) else v
            for k, v in self.phases.items()
        }
    
    # Compatibility property aliases
    @property
    def run_id(self) -> str:
        return self.pipeline_run_id
    
    @property
    def needs_planning(self) -> bool:
        """Check if initial planning is needed"""
        return len(self.tasks) == 0
    
    @property
    def needs_project_planning(self) -> bool:
        """Check if all tasks are complete and ready for expansion planning"""
        if not self.tasks:
            return False
        return all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for t in self.tasks.values()
        )
    
    @property
    def needs_documentation_update(self) -> bool:
        """Check if documentation needs updating after task completion"""
        completed_count = sum(
            1 for t in self.tasks.values()
            if t.status == TaskStatus.COMPLETED
        )
        return completed_count > self.last_doc_update_count
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "updated": self.updated,
            "pipeline_run_id": self.pipeline_run_id,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "phases": {k: v.to_dict() for k, v in self.phases.items()},
            "queue": self.queue,
            # Expansion tracking
            "expansion_count": self.expansion_count,
            "last_doc_update_count": self.last_doc_update_count,
            "project_maturity": self.project_maturity,
            "last_planning_iteration": self.last_planning_iteration,
            # Learning and intelligence
            "performance_metrics": dict(self.performance_metrics),
            "learned_patterns": dict(self.learned_patterns),
            "fix_history": self.fix_history,
            "troubleshooting_results": self.troubleshooting_results,
            "correlations": self.correlations,
            # Loop prevention
            "no_update_counts": self.no_update_counts,
            "phase_history": self.phase_history,
            # Strategic management (NEW)
            "objectives": self.objectives,
            "issues": self.issues,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineState":
        # Backward compatibility: add defaults for new fields
        data.setdefault("objectives", {})
        data.setdefault("issues", {})
        return cls(**data)
    
    def get_task(self, task_id: str) -> Optional[TaskState]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def add_task(self, description: str, target_file: str, 
                 priority: int = 5, dependencies: List[str] = None,
                 objective_id: Optional[str] = None,
                 objective_level: Optional[str] = None) -> TaskState:
        """Add a new task"""
        task_id = hashlib.sha256(
            f"{description}:{target_file}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        task = TaskState(
            task_id=task_id,
            description=description,
            target_file=target_file,
            priority=priority,
            status=TaskStatus.NEW,
            dependencies=dependencies or [],
            objective_id=objective_id,
            objective_level=objective_level
        )
        
        self.tasks[task_id] = task
        self.queue.append({"task_id": task_id, "priority": priority})
        self._sort_queue()
        self.updated = datetime.now().isoformat()
        
        return task
    
    def update_task(self, task_id: str, **kwargs):
        """Update task properties"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now().isoformat()
            self.updated = datetime.now().isoformat()
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update a task's status (compatibility method)"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.now().isoformat()
            self.updated = datetime.now().isoformat()
    
    def get_next_task(self) -> Optional[TaskState]:
        """Get the highest priority incomplete task"""
        for item in self.queue:
            task = self.tasks.get(item["task_id"])
            if task and task.status in [TaskStatus.NEW, TaskStatus.QA_FAILED, 
                                         TaskStatus.DEBUG_PENDING, TaskStatus.IN_PROGRESS]:
                return task
        return None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskState]:
        """Get all tasks with a specific status"""
        return [t for t in self.tasks.values() if t.status == status]
    
    def get_tasks_by_priority(self, priority: int) -> List[TaskState]:
        """Get all tasks with a specific priority"""
        return [t for t in self.tasks.values() if t.priority == priority]
    
    def get_next_priority_task(self, status: TaskStatus) -> Optional[TaskState]:
        """Get the highest priority task with given status"""
        tasks = self.get_tasks_by_status(status)
        if not tasks:
            return None
        return min(tasks, key=lambda t: t.priority)
    
    def _sort_queue(self):
        """Sort queue by priority (lower number = higher priority)"""
        self.queue.sort(key=lambda x: x["priority"])
    
    def rebuild_queue(self):
        """Rebuild the task queue from current task states"""
        self.queue = []
        for task_id, task in self.tasks.items():
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]:
                # Adjust priority based on status
                priority = task.priority
                if task.status == TaskStatus.QA_FAILED:
                    priority = 2  # QA failures are high priority
                elif task.status == TaskStatus.DEBUG_PENDING:
                    priority = 3
                elif task.status == TaskStatus.IN_PROGRESS:
                    priority = 4
                
                self.queue.append({"task_id": task_id, "priority": priority})
        
        self._sort_queue()
    
    def update_file(self, filepath: str, hash: str, size: int):
        """Update or create file state"""
        now = datetime.now().isoformat()
        
        if filepath in self.files:
            old_hash = self.files[filepath].hash
            self.files[filepath].hash = hash
            self.files[filepath].last_modified = now
            self.files[filepath].size = size
            # Reset QA status if file changed
            if old_hash != hash:
                self.files[filepath].qa_status = FileStatus.PENDING
        else:
            self.files[filepath] = FileState(
                filepath=filepath,
                hash=hash,
                created=now,
                last_modified=now,
                size=size,
                qa_status=FileStatus.PENDING
            )
        
        self.updated = now
    
    def get_files_needing_qa(self) -> List[str]:
        """Get files that need QA review"""
        return [
            f.filepath for f in self.files.values()
            if f.qa_status in [FileStatus.UNKNOWN, FileStatus.PENDING]
        ]
    
    def mark_file_reviewed(self, filepath: str, approved: bool, 
                           issues: List[Dict] = None):
        """Mark a file as reviewed by QA"""
        if filepath in self.files:
            self.files[filepath].last_qa = datetime.now().isoformat()
            self.files[filepath].qa_status = (
                FileStatus.APPROVED if approved else FileStatus.REJECTED
            )
            if issues:
                self.files[filepath].issues = issues


class StateManager:
    """Manages pipeline state persistence"""
    
    STATE_FILE = ".pipeline/state.json"
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.state_dir = self.project_dir / ".pipeline"
        self.state_file = self.project_dir / self.STATE_FILE
        self.logger = get_logger()
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> PipelineState:
        """Load state from disk, or create new state"""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.logger.debug(f"Loaded state from {self.state_file}")
                return PipelineState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Failed to load state: {e}")
                self.logger.warning("Creating new state")
        
        return PipelineState()
    
    def save(self, state: PipelineState):
        """
        Save state to disk atomically.
        
        Uses temp file + atomic rename to ensure state file is never corrupted,
        even if process crashes during write.
        """
        from ..atomic_file import atomic_write_json
        
        state.updated = datetime.now().isoformat()
        
        try:
            atomic_write_json(self.state_file, state.to_dict(), indent=2)
            self.logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            raise
    
    def write_phase_state(self, phase: str, content: str):
        """Write a phase-specific state file (markdown) atomically"""
        from ..atomic_file import atomic_write
        
        filename = f"{phase.upper()}_STATE.md"
        filepath = self.state_dir / filename
        
        try:
            atomic_write(filepath, content)
            self.logger.debug(f"Wrote {filename}")
        except Exception as e:
            self.logger.error(f"Failed to write {filename}: {e}")
    
    def read_phase_state(self, phase: str) -> Optional[str]:
        """Read a phase-specific state file"""
        filename = f"{phase.upper()}_STATE.md"
        filepath = self.state_dir / filename
        
        if filepath.exists():
            return filepath.read_text()
        return None
    
    def get_all_phase_states(self) -> Dict[str, str]:
        """Get all phase state files"""
        states = {}
        for phase in ["planning", "coding", "qa", "debug", "project_planning", "documentation"]:
            content = self.read_phase_state(phase)
            if content:
                states[phase] = content
        return states
    
    def backup_state(self) -> Optional[Path]:
        """Create a backup of current state"""
        if not self.state_file.exists():
            return None
        
        backup_dir = self.state_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"state_{timestamp}.json"
        
        import shutil
        shutil.copy(self.state_file, backup_file)
        
        return backup_file
    
    def get_state_summary(self) -> Dict:
        """Get a summary of current state"""
        state = self.load()
        
        status_counts = {}
        for task in state.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "run_id": state.pipeline_run_id,
            "total_tasks": len(state.tasks),
            "status_counts": status_counts,
            "expansion_count": state.expansion_count,
            "project_maturity": state.project_maturity,
            "phases": {
                name: {
                    "runs": p.runs,
                    "successes": p.successes,
                    "failures": p.failures,
                }
                for name, p in state.phases.items()
            }
        }
    
    def add_performance_metric(self, state: PipelineState, metric_name: str, value: float):
        """Add a performance metric to state."""
        from collections import defaultdict
        if not isinstance(state.performance_metrics, defaultdict):
            state.performance_metrics = defaultdict(list, state.performance_metrics)
        
        state.performance_metrics[metric_name].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        self.save(state)
    
    def learn_pattern(self, state: PipelineState, pattern_name: str, pattern_data: Dict[str, Any]):
        """Learn a new pattern."""
        from collections import defaultdict
        if not isinstance(state.learned_patterns, defaultdict):
            state.learned_patterns = defaultdict(list, state.learned_patterns)
        
        pattern_data['timestamp'] = datetime.now().isoformat()
        pattern_data['id'] = len(state.learned_patterns[pattern_name])
        state.learned_patterns[pattern_name].append(pattern_data)
        self.save(state)
    
    def add_fix(self, state: PipelineState, fix: Dict[str, Any]):
        """Add a fix to history."""
        fix['timestamp'] = datetime.now().isoformat()
        fix['id'] = len(state.fix_history)
        state.fix_history.append(fix)
        self.save(state)
    
    def get_fix_effectiveness(self, state: PipelineState) -> Dict[str, float]:
        """Calculate fix effectiveness."""
        if not state.fix_history:
            return {}
        
        effectiveness = {}
        for fix in state.fix_history:
            fix_type = fix.get('type', 'unknown')
            success = fix.get('success', False)
            
            if fix_type not in effectiveness:
                effectiveness[fix_type] = {'total': 0, 'successful': 0}
            
            effectiveness[fix_type]['total'] += 1
            if success:
                effectiveness[fix_type]['successful'] += 1
        
        return {
            fix_type: data['successful'] / data['total'] if data['total'] > 0 else 0.0
            for fix_type, data in effectiveness.items()
        }
    
    def update_from_troubleshooting(self, state: PipelineState, results: Dict[str, Any]):
        """Update state from troubleshooting results."""
        results['timestamp'] = datetime.now().isoformat()
        results['id'] = len(state.troubleshooting_results)
        state.troubleshooting_results.append(results)
        self.save(state)
    
    def add_correlation(self, state: PipelineState, correlation: Dict[str, Any]):
        """Add a correlation between components."""
        correlation['timestamp'] = datetime.now().isoformat()
        correlation['id'] = len(state.correlations)
        state.correlations.append(correlation)
        self.save(state)
    
    def get_full_context(self, state: PipelineState) -> Dict[str, Any]:
        """Get full context including all learning and metrics."""
        return {
            'pipeline_state': {
                'run_id': state.pipeline_run_id,
                'tasks': len(state.tasks),
                'maturity': state.project_maturity
            },
            'performance_metrics': dict(state.performance_metrics),
            'learned_patterns': dict(state.learned_patterns),
            'fix_history': state.fix_history,
            'troubleshooting_results': state.troubleshooting_results,
            'correlations': state.correlations,
            'phases': {
                name: {
                    'runs': p.runs,
                    'successes': p.successes,
                    'failures': p.failures
                }
                for name, p in state.phases.items()
            }
        }
    
    def increment_no_update_count(self, state: PipelineState, phase: str) -> int:
        """
        Increment and return no-update count for a phase.
        
        Args:
            state: Pipeline state
            phase: Phase name
            
        Returns:
            Current count after increment
        """
        if phase not in state.no_update_counts:
            state.no_update_counts[phase] = 0
        state.no_update_counts[phase] += 1
        self.save(state)
        return state.no_update_counts[phase]
    
    def reset_no_update_count(self, state: PipelineState, phase: str):
        """
        Reset no-update count when phase makes progress.
        
        Args:
            state: Pipeline state
            phase: Phase name
        """
        state.no_update_counts[phase] = 0
        self.save(state)
    
    def get_no_update_count(self, state: PipelineState, phase: str) -> int:
        """
        Get current no-update count for a phase.
        
        Args:
            state: Pipeline state
            phase: Phase name
            
        Returns:
            Current count
        """
        return state.no_update_counts.get(phase, 0)
