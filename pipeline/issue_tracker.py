"""
Issue Tracker

Centralized issue tracking system with full lifecycle management,
priority-based querying, and issue correlation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from .state.manager import StateManager, PipelineState, TaskState
from .logging_setup import get_logger


class IssueType(str, Enum):
    """Types of issues"""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    TYPE_ERROR = "type_error"
    LOGIC_ERROR = "logic_error"
    INCOMPLETE = "incomplete"
    MISSING_FUNCTIONALITY = "missing_functionality"
    STYLE_VIOLATION = "style_violation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    OTHER = "other"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"  # System broken, blocks progress
    HIGH = "high"          # Major problems, significant impact
    MEDIUM = "medium"      # Minor issues, moderate impact
    LOW = "low"            # Cosmetic issues, minimal impact


class IssueStatus(str, Enum):
    """Issue lifecycle status"""
    OPEN = "open"                  # Newly created
    ASSIGNED = "assigned"          # Assigned to fix task
    IN_PROGRESS = "in_progress"    # Being fixed
    RESOLVED = "resolved"          # Fix implemented
    VERIFIED = "verified"          # Fix verified by QA
    CLOSED = "closed"              # Completed
    REOPENED = "reopened"          # Fix didn't work
    WONT_FIX = "wont_fix"         # Decided not to fix


@dataclass
class Issue:
    """Quality issue with full lifecycle tracking"""
    
    # Identity
    id: str
    issue_type: IssueType
    severity: IssueSeverity
    
    # Location
    file: str
    line_number: Optional[int] = None
    function: Optional[str] = None
    
    # Description
    title: str = ""
    description: str = ""
    code_snippet: Optional[str] = None
    
    # Status
    status: IssueStatus = IssueStatus.OPEN
    resolution: Optional[str] = None
    
    # Relationships
    related_task: Optional[str] = None
    related_objective: Optional[str] = None
    related_issues: List[str] = field(default_factory=list)
    
    # Assignment
    assigned_to_task: Optional[str] = None
    
    # Lifecycle timestamps
    reported_by: str = ""
    reported_at: str = ""
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    resolved_at: Optional[str] = None
    verified_at: Optional[str] = None
    closed_at: Optional[str] = None
    
    # Metrics
    fix_attempts: int = 0
    time_to_fix: Optional[float] = None
    
    # Suggested fix
    suggested_fix: Optional[str] = None
    fix_complexity: Optional[str] = None  # SIMPLE, MODERATE, COMPLEX
    
    def __post_init__(self):
        if not self.reported_at:
            self.reported_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "issue_type": self.issue_type.value if isinstance(self.issue_type, IssueType) else self.issue_type,
            "severity": self.severity.value if isinstance(self.severity, IssueSeverity) else self.severity,
            "file": self.file,
            "line_number": self.line_number,
            "function": self.function,
            "title": self.title,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "status": self.status.value if isinstance(self.status, IssueStatus) else self.status,
            "resolution": self.resolution,
            "related_task": self.related_task,
            "related_objective": self.related_objective,
            "related_issues": self.related_issues,
            "assigned_to_task": self.assigned_to_task,
            "reported_by": self.reported_by,
            "reported_at": self.reported_at,
            "assigned_at": self.assigned_at,
            "started_at": self.started_at,
            "resolved_at": self.resolved_at,
            "verified_at": self.verified_at,
            "closed_at": self.closed_at,
            "fix_attempts": self.fix_attempts,
            "time_to_fix": self.time_to_fix,
            "suggested_fix": self.suggested_fix,
            "fix_complexity": self.fix_complexity
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Issue":
        """Deserialize from dictionary"""
        return cls(
            id=data["id"],
            issue_type=IssueType(data["issue_type"]),
            severity=IssueSeverity(data["severity"]),
            file=data["file"],
            line_number=data.get("line_number"),
            function=data.get("function"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            code_snippet=data.get("code_snippet"),
            status=IssueStatus(data.get("status", "open")),
            resolution=data.get("resolution"),
            related_task=data.get("related_task"),
            related_objective=data.get("related_objective"),
            related_issues=data.get("related_issues", []),
            assigned_to_task=data.get("assigned_to_task"),
            reported_by=data.get("reported_by", ""),
            reported_at=data.get("reported_at", ""),
            assigned_at=data.get("assigned_at"),
            started_at=data.get("started_at"),
            resolved_at=data.get("resolved_at"),
            verified_at=data.get("verified_at"),
            closed_at=data.get("closed_at"),
            fix_attempts=data.get("fix_attempts", 0),
            time_to_fix=data.get("time_to_fix"),
            suggested_fix=data.get("suggested_fix"),
            fix_complexity=data.get("fix_complexity")
        )


@dataclass
class IssueCorrelation:
    """Correlation between related issues"""
    issue_ids: List[str]
    correlation_type: str  # SAME_FILE, SAME_TYPE, SAME_FUNCTION, DEPENDENCY
    confidence: float
    description: str


class IssueTracker:
    """Centralized issue tracking and lifecycle management"""
    
    def __init__(self, project_dir: Path, state_manager: StateManager):
        self.project_dir = Path(project_dir)
        self.state_manager = state_manager
        self.logger = get_logger()
        self.issues: Dict[str, Issue] = {}
    
    def load_issues(self, state: PipelineState):
        """Load issues from state"""
        self.issues = {}
        for issue_id, issue_data in state.issues.items():
            if isinstance(issue_data, dict):
                issue = Issue.from_dict(issue_data)
            else:
                issue = issue_data
            self.issues[issue.id] = issue
    
    def create_issue(self, issue: Issue, state: PipelineState) -> str:
        """Create new issue and return ID"""
        # Generate ID if not set
        if not issue.id:
            issue.id = f"issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.issues)}"
        
        # Add to tracker
        self.issues[issue.id] = issue
        
        # Add to state
        state.issues[issue.id] = issue.to_dict()
        
        # Save state
        self.state_manager.save(state)
        
        self.logger.info(f"Created issue: {issue.id} ({issue.severity.value}) in {issue.file}")
        
        return issue.id
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """Get issue by ID"""
        return self.issues.get(issue_id)
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        """Get all issues with specific severity"""
        return [
            issue for issue in self.issues.values()
            if issue.severity == severity and issue.status in [
                IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS
            ]
        ]
    
    def get_issues_by_status(self, status: IssueStatus) -> List[Issue]:
        """Get all issues with specific status"""
        return [
            issue for issue in self.issues.values()
            if issue.status == status
        ]
    
    def get_issues_for_objective(self, objective_id: str) -> List[Issue]:
        """Get all issues affecting an objective"""
        return [
            issue for issue in self.issues.values()
            if issue.related_objective == objective_id and issue.status in [
                IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS
            ]
        ]
    
    def get_issues_for_file(self, filepath: str) -> List[Issue]:
        """Get all issues in a specific file"""
        return [
            issue for issue in self.issues.values()
            if issue.file == filepath and issue.status in [
                IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS
            ]
        ]
    
    def get_issues_by_priority(self) -> List[Issue]:
        """Get issues sorted by priority (severity + age)"""
        # Severity weights
        severity_weights = {
            IssueSeverity.CRITICAL: 1,
            IssueSeverity.HIGH: 5,
            IssueSeverity.MEDIUM: 10,
            IssueSeverity.LOW: 20
        }
        
        # Calculate priority score for each issue
        scored_issues = []
        for issue in self.issues.values():
            if issue.status not in [IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS]:
                continue
            
            # Base priority from severity
            priority = severity_weights.get(issue.severity, 10)
            
            # Adjust for age (older issues get higher priority)
            age_hours = (datetime.now() - datetime.fromisoformat(issue.reported_at)).total_seconds() / 3600
            priority -= age_hours * 0.1  # Decrease priority by 0.1 per hour
            
            # Adjust for fix attempts (more attempts = higher priority)
            priority -= issue.fix_attempts * 0.5
            
            scored_issues.append((priority, issue))
        
        # Sort by priority (lower score = higher priority)
        scored_issues.sort(key=lambda x: x[0])
        
        return [issue for _, issue in scored_issues]
    
    def correlate_issues(self) -> List[IssueCorrelation]:
        """Find related issues across files"""
        correlations = []
        
        # Group by file
        by_file = defaultdict(list)
        for issue in self.issues.values():
            if issue.status in [IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS]:
                by_file[issue.file].append(issue)
        
        # Find same-file correlations
        for filepath, file_issues in by_file.items():
            if len(file_issues) > 1:
                correlations.append(IssueCorrelation(
                    issue_ids=[i.id for i in file_issues],
                    correlation_type="SAME_FILE",
                    confidence=0.8,
                    description=f"{len(file_issues)} issues in {filepath}"
                ))
        
        # Group by type
        by_type = defaultdict(list)
        for issue in self.issues.values():
            if issue.status in [IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS]:
                by_type[issue.issue_type].append(issue)
        
        # Find same-type correlations
        for issue_type, type_issues in by_type.items():
            if len(type_issues) > 2:
                correlations.append(IssueCorrelation(
                    issue_ids=[i.id for i in type_issues],
                    correlation_type="SAME_TYPE",
                    confidence=0.6,
                    description=f"{len(type_issues)} {issue_type.value} issues"
                ))
        
        return correlations
    
    def assign_issue(self, issue_id: str, task_id: str, state: PipelineState):
        """Assign issue to a fix task"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.assigned_to_task = task_id
        issue.status = IssueStatus.ASSIGNED
        issue.assigned_at = datetime.now().isoformat()
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.info(f"Assigned issue {issue_id} to task {task_id}")
    
    def start_fixing(self, issue_id: str, state: PipelineState):
        """Mark issue as being fixed"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.status = IssueStatus.IN_PROGRESS
        issue.started_at = datetime.now().isoformat()
        issue.fix_attempts += 1
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.info(f"Started fixing issue {issue_id} (attempt {issue.fix_attempts})")
    
    def resolve_issue(self, issue_id: str, resolution: str, state: PipelineState):
        """Mark issue as resolved"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.status = IssueStatus.RESOLVED
        issue.resolution = resolution
        issue.resolved_at = datetime.now().isoformat()
        
        # Calculate time to fix
        if issue.started_at:
            start = datetime.fromisoformat(issue.started_at)
            end = datetime.fromisoformat(issue.resolved_at)
            issue.time_to_fix = (end - start).total_seconds() / 3600  # hours
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.info(f"Resolved issue {issue_id}: {resolution}")
    
    def verify_issue(self, issue_id: str, state: PipelineState):
        """Mark issue as verified by QA"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.status = IssueStatus.VERIFIED
        issue.verified_at = datetime.now().isoformat()
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.info(f"Verified issue {issue_id}")
    
    def close_issue(self, issue_id: str, state: PipelineState):
        """Close verified issue"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.status = IssueStatus.CLOSED
        issue.closed_at = datetime.now().isoformat()
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.info(f"Closed issue {issue_id}")
    
    def reopen_issue(self, issue_id: str, reason: str, state: PipelineState):
        """Reopen issue if fix didn't work"""
        if issue_id not in self.issues:
            return
        
        issue = self.issues[issue_id]
        issue.status = IssueStatus.REOPENED
        issue.resolution = f"Reopened: {reason}"
        
        # Update state
        state.issues[issue_id] = issue.to_dict()
        self.state_manager.save(state)
        
        self.logger.warning(f"Reopened issue {issue_id}: {reason}")
    
    def create_fix_task(self, issue: Issue, state: PipelineState) -> TaskState:
        """Create task to fix issue"""
        from .state.priority import TaskPriority
        
        # Determine priority based on severity
        priority_map = {
            IssueSeverity.CRITICAL: TaskPriority.CRITICAL_BUG,
            IssueSeverity.HIGH: TaskPriority.QA_FAILURE,
            IssueSeverity.MEDIUM: TaskPriority.NEW_TASK,
            IssueSeverity.LOW: TaskPriority.LOW
        }
        
        priority = priority_map.get(issue.severity, TaskPriority.NEW_TASK)
        
        # Create task
        task = state.add_task(
            description=f"Fix {issue.severity.value} issue: {issue.title}",
            target_file=issue.file,
            priority=priority,
            dependencies=[],
            objective_id=issue.related_objective,
            objective_level=None  # Will be determined from objective
        )
        
        # Link issue to task
        self.assign_issue(issue.id, task.task_id, state)
        
        return task