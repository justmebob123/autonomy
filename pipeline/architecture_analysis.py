"""
Architecture Analysis Module

Provides data structures and analysis capabilities for architecture validation.
Integrates with validation tools to provide comprehensive architecture insights.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from pathlib import Path
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ComponentInfo:
    """Information about a component"""
    name: str
    path: str
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    line_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'path': self.path,
            'classes': self.classes,
            'functions': self.functions,
            'dependencies': self.dependencies,
            'dependents': self.dependents,
            'line_count': self.line_count
        }


@dataclass
class IntegrationStatus:
    """Integration status for a component"""
    component: str
    is_integrated: bool
    missing_integrations: List[str] = field(default_factory=list)
    unused_classes: List[str] = field(default_factory=list)
    integration_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'is_integrated': self.is_integrated,
            'missing_integrations': self.missing_integrations,
            'unused_classes': self.unused_classes,
            'integration_score': self.integration_score
        }


@dataclass
class QualityMetrics:
    """Code quality metrics for a component"""
    component: str
    complexity_avg: float = 0.0
    complexity_max: int = 0
    high_complexity_count: int = 0
    dead_code_count: int = 0
    validation_errors: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'complexity_avg': self.complexity_avg,
            'complexity_max': self.complexity_max,
            'high_complexity_count': self.high_complexity_count,
            'dead_code_count': self.dead_code_count,
            'validation_errors': self.validation_errors
        }


@dataclass
class CallGraphSubset:
    """Subset of call graph for a component"""
    component: str
    functions: List[str] = field(default_factory=list)
    internal_calls: Dict[str, Set[str]] = field(default_factory=dict)
    external_calls: Dict[str, Set[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'functions': self.functions,
            'internal_calls': {k: list(v) for k, v in self.internal_calls.items()},
            'external_calls': {k: list(v) for k, v in self.external_calls.items()}
        }


@dataclass
class ArchitectureAnalysis:
    """Result of analyzing current architecture"""
    timestamp: datetime
    components: Dict[str, ComponentInfo] = field(default_factory=dict)
    call_graph: Optional[Any] = None  # CallGraphResult from call_graph.py
    integration_status: Dict[str, IntegrationStatus] = field(default_factory=dict)
    quality_metrics: Dict[str, QualityMetrics] = field(default_factory=dict)
    validation_errors: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'components': {k: v.to_dict() for k, v in self.components.items()},
            'integration_status': {k: v.to_dict() for k, v in self.integration_status.items()},
            'quality_metrics': {k: v.to_dict() for k, v in self.quality_metrics.items()},
            'validation_errors': self.validation_errors,
            'call_graph_stats': {
                'total_functions': self.call_graph.total_functions if self.call_graph else 0,
                'total_calls': self.call_graph.total_calls if self.call_graph else 0
            } if self.call_graph else {}
        }


@dataclass
class PlacementIssue:
    """Issue with component placement"""
    component: str
    current_location: str
    expected_location: str
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'current_location': self.current_location,
            'expected_location': self.expected_location,
            'reason': self.reason
        }


@dataclass
class IntegrationGap:
    """Gap in component integration"""
    component: str
    missing_integration: str
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'missing_integration': self.missing_integration,
            'reason': self.reason
        }


@dataclass
class NamingViolation:
    """Naming convention violation"""
    file_path: str
    violation_type: str
    expected: str
    actual: str
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'violation_type': self.violation_type,
            'expected': self.expected,
            'actual': self.actual
        }


@dataclass
class ValidationReport:
    """Result of architecture validation"""
    is_consistent: bool
    missing_components: List[str] = field(default_factory=list)
    extra_components: List[str] = field(default_factory=list)
    misplaced_components: List[PlacementIssue] = field(default_factory=list)
    integration_gaps: List[IntegrationGap] = field(default_factory=list)
    naming_violations: List[NamingViolation] = field(default_factory=list)
    severity: ValidationSeverity = ValidationSeverity.INFO
    
    def to_dict(self) -> Dict:
        return {
            'is_consistent': self.is_consistent,
            'missing_components': self.missing_components,
            'extra_components': self.extra_components,
            'misplaced_components': [i.to_dict() for i in self.misplaced_components],
            'integration_gaps': [g.to_dict() for g in self.integration_gaps],
            'naming_violations': [v.to_dict() for v in self.naming_violations],
            'severity': self.severity.value
        }


@dataclass
class ComponentChange:
    """Change to a component"""
    component: str
    change_type: str  # 'modified', 'added', 'removed'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'change_type': self.change_type,
            'details': self.details
        }


@dataclass
class ComponentMove:
    """Component moved to new location"""
    component: str
    old_location: str
    new_location: str
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            'component': self.component,
            'old_location': self.old_location,
            'new_location': self.new_location,
            'reason': self.reason
        }


@dataclass
class ArchitectureDiff:
    """Differences between architectures"""
    added: List[ComponentInfo] = field(default_factory=list)
    removed: List[ComponentInfo] = field(default_factory=list)
    modified: List[ComponentChange] = field(default_factory=list)
    moved: List[ComponentMove] = field(default_factory=list)
    
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified or self.moved)
    
    def to_dict(self) -> Dict:
        return {
            'added': [c.to_dict() for c in self.added],
            'removed': [c.to_dict() for c in self.removed],
            'modified': [c.to_dict() for c in self.modified],
            'moved': [m.to_dict() for m in self.moved]
        }


@dataclass
class PlacementValidation:
    """Result of validating component placement"""
    is_valid: bool
    expected_location: str
    current_location: str
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            'is_valid': self.is_valid,
            'expected_location': self.expected_location,
            'current_location': self.current_location,
            'reason': self.reason
        }