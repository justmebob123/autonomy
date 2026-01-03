"""
Polytopic Objective Implementation

Extends the base Objective class with 7D dimensional profiles for
hyperdimensional navigation and intelligent objective selection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import math

from ..objective_manager import Objective, ObjectiveLevel, ObjectiveStatus


@dataclass
class PolytopicObjective(Objective):
    """
    Enhanced objective with 7D dimensional profile.
    
    The 8 dimensions represent different aspects of objective complexity:
    1. D1: Temporal - Time constraints, deadlines, urgency (0.0 = no urgency, 1.0 = critical deadline)
    2. D2: Functional - Capabilities required, feature complexity (0.0 = simple, 1.0 = highly complex)
    3. D3: Data - Data dependencies, information flow (0.0 = self-contained, 1.0 = many dependencies)
    4. D4: State - State management requirements (0.0 = stateless, 1.0 = complex state)
    5. D5: Error - Error handling needs, risk level (0.0 = low risk, 1.0 = high risk)
    6. D6: Context - Contextual dependencies, environment (0.0 = context-free, 1.0 = context-heavy)
    7. D7: Integration - Cross-component dependencies (0.0 = isolated, 1.0 = highly integrated)
    8. D8: Architecture - Architecture awareness/consistency (0.0 = no arch impact, 1.0 = critical arch change)
    """
    
    # 8D Dimensional Profile (added architecture dimension)
    dimensional_profile: Dict[str, float] = field(default_factory=lambda: {
        "temporal": 0.5,      # Time urgency
        "functional": 0.5,    # Feature complexity
        "data": 0.5,          # Data dependencies
        "state": 0.5,         # State complexity
        "error": 0.5,         # Risk level
        "context": 0.5,       # Context dependencies
        "integration": 0.5,   # Integration complexity
        "architecture": 0.5   # Architecture awareness/consistency
    })
    
    # Polytopic Properties
    polytopic_position: Optional[List[float]] = None  # Position in 8D space
    adjacent_objectives: List[str] = field(default_factory=list)  # Connected objectives
    dimensional_velocity: Dict[str, float] = field(default_factory=dict)  # Rate of change per dimension
    
    # Intelligence Metrics
    complexity_score: float = 0.0  # Overall complexity (0.0 to 1.0)
    risk_score: float = 0.0        # Overall risk (0.0 to 1.0)
    readiness_score: float = 0.0   # Readiness to execute (0.0 to 1.0)
    
    # Dimensional History
    dimensional_history: List[Dict[str, Any]] = field(default_factory=list)  # Track dimensional changes over time
    
    def __post_init__(self):
        """Initialize polytopic properties after creation."""
        super().__post_init__()
        
        # Calculate initial position if not set
        if self.polytopic_position is None:
            self.polytopic_position = self._calculate_position()
        
        # Calculate initial metrics
        self._update_metrics()
        
        # Initialize dimensional velocity if empty
        if not self.dimensional_velocity:
            self.dimensional_velocity = {dim: 0.0 for dim in self.dimensional_profile.keys()}
    
    def _calculate_position(self) -> List[float]:
        """Calculate position in 8D space from dimensional profile."""
        return [self.dimensional_profile[dim] for dim in sorted(self.dimensional_profile.keys())]
    
    def _update_metrics(self) -> None:
        """Update intelligence metrics based on dimensional profile."""
        # Complexity score: weighted average of functional, data, state, integration, and architecture
        self.complexity_score = (
            self.dimensional_profile["functional"] * 0.25 +
            self.dimensional_profile["data"] * 0.15 +
            self.dimensional_profile["state"] * 0.15 +
            self.dimensional_profile["integration"] * 0.25 +
            self.dimensional_profile["architecture"] * 0.20  # Architecture adds to complexity
        )
        
        # Risk score: weighted average of error, temporal, architecture, and complexity
        self.risk_score = (
            self.dimensional_profile["error"] * 0.4 +
            self.dimensional_profile["temporal"] * 0.2 +
            self.dimensional_profile["architecture"] * 0.2 +  # Architecture changes are risky
            self.complexity_score * 0.2
        )
        
        # Readiness score: inverse of dependencies, context, and architecture requirements
        dependency_factor = 1.0 - (
            self.dimensional_profile["data"] * 0.4 + 
            self.dimensional_profile["context"] * 0.4 +
            self.dimensional_profile["architecture"] * 0.2  # Architecture validation needed
        )
        
        # Adjust for task completion
        completion_factor = len([t for t in self.tasks if t.endswith(" ✓")]) / max(len(self.tasks), 1)
        
        self.readiness_score = (dependency_factor * 0.6 + completion_factor * 0.4)
    
    def update_dimensional_profile(self, dimension: str, value: float) -> None:
        """
        Update a specific dimension and recalculate metrics.
        
        Args:
            dimension: Name of dimension to update
            value: New value (0.0 to 1.0)
        """
        if dimension not in self.dimensional_profile:
            raise ValueError(f"Invalid dimension: {dimension}")
        
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Dimension value must be between 0.0 and 1.0, got {value}")
        
        # Calculate velocity (rate of change)
        old_value = self.dimensional_profile[dimension]
        self.dimensional_velocity[dimension] = value - old_value
        
        # Record history
        self.dimensional_history.append({
            "timestamp": datetime.now().isoformat(),
            "dimension": dimension,
            "old_value": old_value,
            "new_value": value,
            "velocity": self.dimensional_velocity[dimension]
        })
        
        # Update profile
        self.dimensional_profile[dimension] = value
        self.polytopic_position = self._calculate_position()
        self._update_metrics()
    
    def get_dimensional_vector(self) -> List[float]:
        """Get the 8D dimensional vector in canonical order."""
        return self.polytopic_position or self._calculate_position()
    
    def calculate_distance_to(self, other: 'PolytopicObjective') -> float:
        """
        Calculate Euclidean distance to another objective in 8D space.
        
        Args:
            other: Another polytopic objective
            
        Returns:
            Distance in 8D space (0.0 to sqrt(8))
        """
        v1 = self.get_dimensional_vector()
        v2 = other.get_dimensional_vector()
        
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    def calculate_similarity(self, other: 'PolytopicObjective') -> float:
        """
        Calculate similarity to another objective (inverse of distance).
        
        Args:
            other: Another polytopic objective
            
        Returns:
            Similarity score (0.0 to 1.0, where 1.0 is identical)
        """
        distance = self.calculate_distance_to(other)
        max_distance = math.sqrt(7)  # Maximum possible distance in 7D unit hypercube
        return 1.0 - (distance / max_distance)
    
    def get_dominant_dimensions(self, threshold: float = 0.6) -> List[str]:
        """
        Get dimensions that are above threshold (indicating high complexity/urgency).
        
        Args:
            threshold: Minimum value to consider dominant (default 0.6)
            
        Returns:
            List of dimension names above threshold
        """
        return [dim for dim, value in self.dimensional_profile.items() if value >= threshold]
    
    def get_weak_dimensions(self, threshold: float = 0.4) -> List[str]:
        """
        Get dimensions that are below threshold (indicating low complexity/urgency).
        
        Args:
            threshold: Maximum value to consider weak (default 0.4)
            
        Returns:
            List of dimension names below threshold
        """
        return [dim for dim, value in self.dimensional_profile.items() if value <= threshold]
    
    def is_adjacent_to(self, other: 'PolytopicObjective', threshold: float = 0.3) -> bool:
        """
        Check if another objective is adjacent in 7D space.
        
        Args:
            other: Another polytopic objective
            threshold: Maximum distance to consider adjacent (default 0.3)
            
        Returns:
            True if objectives are adjacent
        """
        return self.calculate_distance_to(other) <= threshold
    
    def get_trajectory_direction(self) -> Dict[str, str]:
        """
        Get the direction of movement in each dimension.
        
        Returns:
            Dict mapping dimension to direction ("increasing", "decreasing", "stable")
        """
        directions = {}
        for dim, velocity in self.dimensional_velocity.items():
            if velocity > 0.05:
                directions[dim] = "increasing"
            elif velocity < -0.05:
                directions[dim] = "decreasing"
            else:
                directions[dim] = "stable"
        return directions
    
    def predict_future_position(self, time_steps: int = 1) -> List[float]:
        """
        Predict future position based on current velocity.
        
        Args:
            time_steps: Number of time steps to predict forward
            
        Returns:
            Predicted 7D position vector
        """
        current = self.get_dimensional_vector()
        velocities = [self.dimensional_velocity.get(dim, 0.0) 
                     for dim in sorted(self.dimensional_profile.keys())]
        
        # Predict position with velocity, clamped to [0, 1]
        predicted = [max(0.0, min(1.0, pos + vel * time_steps)) 
                    for pos, vel in zip(current, velocities)]
        
        return predicted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "dimensional_profile": self.dimensional_profile,
            "polytopic_position": self.polytopic_position,
            "adjacent_objectives": self.adjacent_objectives,
            "dimensional_velocity": self.dimensional_velocity,
            "complexity_score": self.complexity_score,
            "risk_score": self.risk_score,
            "readiness_score": self.readiness_score,
            "dimensional_history": self.dimensional_history
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolytopicObjective':
        """Create from dictionary."""
        # Extract polytopic-specific fields
        dimensional_profile = data.pop("dimensional_profile", None)
        polytopic_position = data.pop("polytopic_position", None)
        adjacent_objectives = data.pop("adjacent_objectives", [])
        dimensional_velocity = data.pop("dimensional_velocity", {})
        complexity_score = data.pop("complexity_score", 0.0)
        risk_score = data.pop("risk_score", 0.0)
        readiness_score = data.pop("readiness_score", 0.0)
        dimensional_history = data.pop("dimensional_history", [])
        
        # Create base objective
        obj = cls(**data)
        
        # Set polytopic fields
        if dimensional_profile:
            obj.dimensional_profile = dimensional_profile
        if polytopic_position:
            obj.polytopic_position = polytopic_position
        obj.adjacent_objectives = adjacent_objectives
        obj.dimensional_velocity = dimensional_velocity
        obj.complexity_score = complexity_score
        obj.risk_score = risk_score
        obj.readiness_score = readiness_score
        obj.dimensional_history = dimensional_history
        
        return obj
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"PolytopicObjective(id={self.id}, level={self.level}, "
                f"complexity={self.complexity_score:.2f}, risk={self.risk_score:.2f}, "
                f"readiness={self.readiness_score:.2f})")