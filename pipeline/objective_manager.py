"""
Objective Manager

Manages the lifecycle of objectives and provides strategic decision-making
capabilities for the pipeline coordinator.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .state.manager import StateManager, PipelineState, TaskState, TaskStatus
from .logging_setup import get_logger


class ObjectiveLevel(str, Enum):
    """Objective priority levels"""
    PRIMARY = "primary"      # Must-have features
    SECONDARY = "secondary"  # Important features
    TERTIARY = "tertiary"    # Nice-to-have features


class ObjectiveStatus(str, Enum):
    """Objective lifecycle status"""
    PROPOSED = "proposed"        # Created but not approved
    APPROVED = "approved"        # Approved for work
    ACTIVE = "active"           # Currently being worked on
    IN_PROGRESS = "in_progress" # Has tasks being executed
    BLOCKED = "blocked"         # Dependencies not met
    DEGRADING = "degrading"     # Success rate dropping
    COMPLETING = "completing"   # All tasks done, needs QA
    COMPLETED = "completed"     # All tasks done and QA'd
    DOCUMENTED = "documented"   # Documented and archived


class ObjectiveHealthStatus(str, Enum):
    """Objective health status"""
    HEALTHY = "healthy"         # Everything good
    DEGRADING = "degrading"     # Success rate dropping
    CRITICAL = "critical"       # Multiple failures
    BLOCKED = "blocked"         # Can't proceed


@dataclass
class ObjectiveHealth:
    """Health analysis of an objective"""
    status: ObjectiveHealthStatus
    success_rate: float
    consecutive_failures: int
    blocking_issues: List[str]  # Issue IDs
    blocking_dependencies: List[str]  # Objective IDs
    recommendation: str


@dataclass
class PhaseAction:
    """Recommended action for an objective"""
    phase: str
    task: Optional[TaskState]
    reason: str
    priority: int


@dataclass
class Objective:
    """Strategic goal with active decision-making capabilities"""
    
    # Identity
    id: str
    level: ObjectiveLevel
    title: str
    description: str
    
    # Status
    status: ObjectiveStatus
    
    # Tasks and Progress
    tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    total_tasks: int = 0
    completion_percentage: float = 0.0
    
    # Issues
    open_issues: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    # Metrics
    success_rate: float = 1.0
    avg_task_duration: float = 0.0
    failure_count: int = 0
    
    # Timestamps
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    target_date: Optional[str] = None
    
    # Acceptance Criteria
    acceptance_criteria: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def update_progress(self, state: PipelineState):
        """Update completion percentage based on task status"""
        if not self.tasks:
            self.completion_percentage = 0.0
            return
        
        completed = [
            tid for tid in self.tasks
            if tid in state.tasks and state.tasks[tid].status == TaskStatus.COMPLETED
        ]
        self.completed_tasks = completed
        self.completion_percentage = (len(completed) / len(self.tasks)) * 100
        
        # Update status based on progress
        if self.completion_percentage == 0:
            if self.status not in [ObjectiveStatus.PROPOSED, ObjectiveStatus.APPROVED]:
                self.status = ObjectiveStatus.APPROVED
        elif self.completion_percentage == 100:
            if self.status != ObjectiveStatus.COMPLETED:
                self.status = ObjectiveStatus.COMPLETING
                if not self.completed_at:
                    self.completed_at = datetime.now().isoformat()
        else:
            if self.status in [ObjectiveStatus.APPROVED, ObjectiveStatus.PROPOSED]:
                self.status = ObjectiveStatus.IN_PROGRESS
                if not self.started_at:
                    self.started_at = datetime.now().isoformat()
    
    def calculate_success_rate(self, state: PipelineState) -> float:
        """Calculate success rate based on task outcomes"""
        if not self.tasks:
            return 1.0
        
        total = 0
        successful = 0
        
        for tid in self.tasks:
            if tid not in state.tasks:
                continue
            task = state.tasks[tid]
            if task.attempts > 0:
                total += task.attempts
                # Count successful attempts (completed without errors)
                if task.status == TaskStatus.COMPLETED and not task.errors:
                    successful += 1
        
        if total == 0:
            return 1.0
        
        self.success_rate = successful / total
        return self.success_rate
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "level": self.level.value if isinstance(self.level, ObjectiveLevel) else self.level,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, ObjectiveStatus) else self.status,
            "tasks": self.tasks,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "completion_percentage": self.completion_percentage,
            "open_issues": self.open_issues,
            "critical_issues": self.critical_issues,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "success_rate": self.success_rate,
            "avg_task_duration": self.avg_task_duration,
            "failure_count": self.failure_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "target_date": self.target_date,
            "acceptance_criteria": self.acceptance_criteria
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Objective":
        """Deserialize from dictionary"""
        return cls(
            id=data["id"],
            level=ObjectiveLevel(data["level"]),
            title=data["title"],
            description=data["description"],
            status=ObjectiveStatus(data["status"]),
            tasks=data.get("tasks", []),
            completed_tasks=data.get("completed_tasks", []),
            total_tasks=data.get("total_tasks", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            open_issues=data.get("open_issues", []),
            critical_issues=data.get("critical_issues", []),
            depends_on=data.get("depends_on", []),
            blocks=data.get("blocks", []),
            success_rate=data.get("success_rate", 1.0),
            avg_task_duration=data.get("avg_task_duration", 0.0),
            failure_count=data.get("failure_count", 0),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            target_date=data.get("target_date"),
            acceptance_criteria=data.get("acceptance_criteria", [])
        )


class ObjectiveManager:
    """Manages objective lifecycle and strategic decision-making"""
    
    def __init__(self, project_dir: Path, state_manager: StateManager):
        self.project_dir = Path(project_dir)
        self.state_manager = state_manager
        self.logger = get_logger()
        
        # Objective files
        self.objective_files = {
            ObjectiveLevel.PRIMARY: self.project_dir / "PRIMARY_OBJECTIVES.md",
            ObjectiveLevel.SECONDARY: self.project_dir / "SECONDARY_OBJECTIVES.md",
            ObjectiveLevel.TERTIARY: self.project_dir / "TERTIARY_OBJECTIVES.md"
        }
    
    def load_objectives(self, state: PipelineState) -> Dict[str, Dict[str, Objective]]:
        """
        Load objectives from markdown files.
        
        Returns dict: {level: {objective_id: Objective}}
        """
        objectives = {
            "primary": {},
            "secondary": {},
            "tertiary": {}
        }
        
        for level, filepath in self.objective_files.items():
            if not filepath.exists():
                self.logger.debug(f"No {level.value} objectives file found")
                continue
            
            level_objectives = self._parse_objective_file(filepath, level)
            objectives[level.value] = level_objectives
        
        return objectives
    
    def _parse_objective_file(self, filepath: Path, level: ObjectiveLevel) -> Dict[str, Objective]:
        """Parse objective markdown file"""
        content = filepath.read_text()
        objectives = {}
        current_obj = None
        in_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # New objective (## heading)
            if line.startswith('## '):
                if current_obj:
                    objectives[current_obj.id] = current_obj
                
                # Extract title
                title = line[3:].strip()
                if '. ' in title:
                    title = title.split('. ', 1)[1]
                
                # Generate ID
                obj_id = f"{level.value}_{len(objectives) + 1:03d}"
                
                current_obj = Objective(
                    id=obj_id,
                    level=level,
                    title=title,
                    description="",
                    status=ObjectiveStatus.PROPOSED
                )
                in_section = None
            
            # Metadata fields
            elif line.startswith('**ID**:') and current_obj:
                current_obj.id = line.split(':', 1)[1].strip()
            
            elif line.startswith('**Status**:') and current_obj:
                status_str = line.split(':', 1)[1].strip().lower()
                try:
                    current_obj.status = ObjectiveStatus(status_str)
                except ValueError:
                    pass
            
            elif line.startswith('**Target Date**:') and current_obj:
                current_obj.target_date = line.split(':', 1)[1].strip()
            
            # Sections
            elif line.startswith('### Tasks') and current_obj:
                in_section = 'tasks'
            
            elif line.startswith('### Dependencies') and current_obj:
                in_section = 'dependencies'
            
            elif line.startswith('### Acceptance Criteria') and current_obj:
                in_section = 'acceptance_criteria'
            
            # Section content
            elif in_section == 'tasks' and (line.startswith('- [x]') or line.startswith('- [ ]')):
                # Task items - will be linked when tasks are created
                pass
            
            elif in_section == 'dependencies' and line.startswith('- '):
                dep = line[2:].strip()
                if dep:
                    current_obj.depends_on.append(dep)
            
            elif in_section == 'acceptance_criteria' and line.startswith('- '):
                criteria = line[2:].strip()
                if criteria:
                    current_obj.acceptance_criteria.append(criteria)
        
        # Add last objective
        if current_obj:
            objectives[current_obj.id] = current_obj
        
        return objectives
    
    def sync_objectives_to_state(self, state: PipelineState):
        """Load objectives from files and sync to state"""
        loaded_objectives = self.load_objectives(state)
        
        # Merge with existing objectives in state
        for level, level_objs in loaded_objectives.items():
            if level not in state.objectives:
                state.objectives[level] = {}
            
            for obj_id, obj in level_objs.items():
                # Convert to dict for storage
                state.objectives[level][obj_id] = obj.to_dict()
        
        self.state_manager.save(state)
        self.logger.info(f"Synced objectives to state: {sum(len(v) for v in state.objectives.values())} total")
    
    def get_active_objective(self, state: PipelineState) -> Optional[Objective]:
        """
        Get the objective that should be worked on now.
        
        Priority:
        1. ACTIVE objective (explicitly set)
        2. IN_PROGRESS objective with highest priority
        3. APPROVED objective with highest priority and met dependencies
        4. None (need project planning)
        """
        # Check for explicitly active objective
        for level in ["primary", "secondary", "tertiary"]:
            for obj_data in state.objectives.get(level, {}).values():
                obj = Objective.from_dict(obj_data) if isinstance(obj_data, dict) else obj_data
                if obj.status == ObjectiveStatus.ACTIVE:
                    return obj
        
        # Check for in-progress objectives (highest priority first)
        for level in ["primary", "secondary", "tertiary"]:
            for obj_data in state.objectives.get(level, {}).values():
                obj = Objective.from_dict(obj_data) if isinstance(obj_data, dict) else obj_data
                if obj.status == ObjectiveStatus.IN_PROGRESS:
                    return obj
        
        # Check for approved objectives with met dependencies
        for level in ["primary", "secondary", "tertiary"]:
            for obj_data in state.objectives.get(level, {}).values():
                obj = Objective.from_dict(obj_data) if isinstance(obj_data, dict) else obj_data
                if obj.status == ObjectiveStatus.APPROVED:
                    if self.check_dependencies_met(obj, state):
                        return obj
        
        return None
    
    def check_dependencies_met(self, objective: Objective, state: PipelineState) -> bool:
        """Check if objective's dependencies are met"""
        for dep_id in objective.depends_on:
            # Find dependency objective
            dep_obj = None
            for level in ["primary", "secondary", "tertiary"]:
                if dep_id in state.objectives.get(level, {}):
                    dep_data = state.objectives[level][dep_id]
                    dep_obj = Objective.from_dict(dep_data) if isinstance(dep_data, dict) else dep_data
                    break
            
            if not dep_obj:
                self.logger.warning(f"Dependency not found: {dep_id}")
                return False
            
            if dep_obj.status != ObjectiveStatus.COMPLETED:
                return False
        
        return True
    
    def analyze_objective_health(self, objective: Objective, state: PipelineState, 
                                 issue_tracker: Any) -> ObjectiveHealth:
        """Analyze objective health"""
        # Update metrics
        objective.update_progress(state)
        success_rate = objective.calculate_success_rate(state)
        
        # Get blocking issues
        blocking_issues = []
        for issue_id in objective.critical_issues:
            if issue_id in issue_tracker.issues:
                issue = issue_tracker.issues[issue_id]
                if issue.status in ["open", "in_progress"]:
                    blocking_issues.append(issue_id)
        
        # Check dependencies
        blocking_deps = []
        for dep_id in objective.depends_on:
            for level in ["primary", "secondary", "tertiary"]:
                if dep_id in state.objectives.get(level, {}):
                    dep_data = state.objectives[level][dep_id]
                    dep_obj = Objective.from_dict(dep_data) if isinstance(dep_data, dict) else dep_data
                    if dep_obj.status != ObjectiveStatus.COMPLETED:
                        blocking_deps.append(dep_id)
        
        # Count consecutive failures
        consecutive_failures = 0
        for tid in reversed(objective.tasks):
            if tid not in state.tasks:
                continue
            task = state.tasks[tid]
            if task.status in [TaskStatus.FAILED, TaskStatus.NEEDS_FIXES]:
                consecutive_failures += 1
            else:
                break
        
        # Determine health status
        if blocking_deps:
            status = ObjectiveHealthStatus.BLOCKED
            recommendation = f"Blocked by dependencies: {', '.join(blocking_deps)}"
        elif len(blocking_issues) > 0:
            status = ObjectiveHealthStatus.CRITICAL
            recommendation = f"Critical issues blocking progress: {len(blocking_issues)} issues"
        elif consecutive_failures >= 3:
            status = ObjectiveHealthStatus.CRITICAL
            recommendation = f"Multiple consecutive failures: {consecutive_failures}"
        elif success_rate < 0.5:
            status = ObjectiveHealthStatus.DEGRADING
            recommendation = f"Success rate degrading: {success_rate:.1%}"
        else:
            status = ObjectiveHealthStatus.HEALTHY
            recommendation = "Objective progressing normally"
        
        return ObjectiveHealth(
            status=status,
            success_rate=success_rate,
            consecutive_failures=consecutive_failures,
            blocking_issues=blocking_issues,
            blocking_dependencies=blocking_deps,
            recommendation=recommendation
        )
    
    def get_objective_action(self, objective: Objective, state: PipelineState,
                            health: ObjectiveHealth) -> PhaseAction:
        """Determine what action this objective needs"""
        
        # Critical health - investigate
        if health.status == ObjectiveHealthStatus.CRITICAL:
            return PhaseAction(
                phase="investigation",
                task=None,
                reason=health.recommendation,
                priority=1
            )
        
        # Blocked - can't proceed
        if health.status == ObjectiveHealthStatus.BLOCKED:
            return PhaseAction(
                phase="project_planning",
                task=None,
                reason=f"Objective blocked: {health.recommendation}",
                priority=2
            )
        
        # Has critical issues - debug
        if health.blocking_issues:
            return PhaseAction(
                phase="debugging",
                task=None,
                reason=f"{len(health.blocking_issues)} critical issues need fixing",
                priority=3
            )
        
        # Get tasks needing work
        pending_tasks = [
            state.tasks[tid] for tid in objective.tasks
            if tid in state.tasks and state.tasks[tid].status in [
                TaskStatus.NEW, TaskStatus.IN_PROGRESS
            ]
        ]
        
        qa_pending_tasks = [
            state.tasks[tid] for tid in objective.tasks
            if tid in state.tasks and state.tasks[tid].status == TaskStatus.QA_PENDING
        ]
        
        needs_fixes_tasks = [
            state.tasks[tid] for tid in objective.tasks
            if tid in state.tasks and state.tasks[tid].status == TaskStatus.NEEDS_FIXES
        ]
        
        # Priority: fixes > QA > coding
        if needs_fixes_tasks:
            return PhaseAction(
                phase="debugging",
                task=needs_fixes_tasks[0],
                reason=f"{len(needs_fixes_tasks)} tasks need fixes",
                priority=4
            )
        
        if qa_pending_tasks:
            return PhaseAction(
                phase="qa",
                task=qa_pending_tasks[0],
                reason=f"{len(qa_pending_tasks)} tasks awaiting QA",
                priority=5
            )
        
        if pending_tasks:
            return PhaseAction(
                phase="coding",
                task=pending_tasks[0],
                reason=f"{len(pending_tasks)} tasks in progress",
                priority=6
            )
        
        # All tasks complete - document
        if objective.completion_percentage == 100:
            return PhaseAction(
                phase="documentation",
                task=None,
                reason="Objective complete, needs documentation",
                priority=7
            )
        
        # Need more tasks
        return PhaseAction(
            phase="planning",
            task=None,
            reason="Objective needs more tasks",
            priority=8
        )
    
    def save_objective(self, objective: Objective, state: PipelineState):
        """Save objective to state"""
        level = objective.level.value if isinstance(objective.level, ObjectiveLevel) else objective.level
        if level not in state.objectives:
            state.objectives[level] = {}
        state.objectives[level][objective.id] = objective.to_dict()
        self.state_manager.save(state)