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
    
    def predict_dimensional_state(self, time_steps: int = 5) -> List[Dict[str, float]]:
        """
        Predict future dimensional states using velocity with damping.
        
        ============================================================================
        DIMENSIONAL VELOCITY PREDICTION (Week 1 Enhancement #2)
        ============================================================================
        WHAT: Predicts how objective's dimensions will change over time
        WHY: Enables proactive management - anticipate urgent/risky objectives
        HOW: Uses velocity with damping factor (0.9^t) for realistic predictions
        
        PREDICTION ALGORITHM:
        1. Start with current dimensional profile
        2. For each time step t:
           - Apply damped velocity: velocity * (0.9^t)
           - Update dimension: value + damped_velocity
           - Clamp to [0.0, 1.0] range
        3. Return list of predicted profiles
        
        DAMPING FACTOR (0.9):
        - Prevents unrealistic predictions (velocity doesn't continue forever)
        - Models natural deceleration over time
        - At t=5: velocity is 0.9^5 = 0.59 of original (41% reduction)
        
        EXAMPLE:
        Current: {temporal: 0.6, functional: 0.5, ...}
        Velocity: {temporal: +0.1, functional: -0.02, ...}
        
        Predictions:
        t=1: {temporal: 0.69, functional: 0.48, ...}  # velocity * 0.9
        t=2: {temporal: 0.77, functional: 0.46, ...}  # velocity * 0.81
        t=3: {temporal: 0.84, functional: 0.45, ...}  # velocity * 0.73
        
        INTEGRATION: Used by will_become_urgent() and will_become_risky()
        ============================================================================
        
        Args:
            time_steps: Number of future time steps to predict
            
        Returns:
            List of predicted dimensional profiles at each time step
        """
        if not self.dimensional_velocity:
            return [self.dimensional_profile.copy()] * time_steps
        
        predictions = []
        current = self.dimensional_profile.copy()
        damping_factor = 0.9  # Reduce velocity over time
        
        for t in range(time_steps):
            predicted = {}
            for dim, value in current.items():
                velocity = self.dimensional_velocity.get(dim, 0.0)
                # Apply damped velocity
                damped_velocity = velocity * (damping_factor ** t)
                predicted[dim] = max(0.0, min(1.0, value + damped_velocity))
            
            predictions.append(predicted)
            current = predicted
        
        return predictions
    
    def will_become_urgent(self, threshold: float = 0.8, time_steps: int = 3) -> bool:
        """
        Check if objective will become urgent soon.
        
        Args:
            threshold: Temporal dimension threshold for urgency
            time_steps: Number of time steps to look ahead
            
        Returns:
            True if temporal dimension will exceed threshold
        """
        predictions = self.predict_dimensional_state(time_steps)
        
        for predicted in predictions:
            if predicted.get('temporal', 0.0) > threshold:
                return True
        
        return False
    
    def will_become_risky(self, threshold: float = 0.7, time_steps: int = 3) -> bool:
        """
        Check if objective will become risky soon.
        
        Args:
            threshold: Error dimension threshold for risk
            time_steps: Number of time steps to look ahead
            
        Returns:
            True if error dimension will exceed threshold
        """
        predictions = self.predict_dimensional_state(time_steps)
        
        for predicted in predictions:
            if predicted.get('error', 0.0) > threshold:
                return True
        
        return False
    
    def get_trajectory_warnings(self) -> List[str]:
        """
        Get warnings about trajectory based on predictions.
        
        ============================================================================
        PROACTIVE TRAJECTORY WARNINGS (Week 1 Enhancement #2)
        ============================================================================
        WHAT: Generates human-readable warnings about objective's trajectory
        WHY: Alerts users to objectives that will become urgent/risky soon
        HOW: Uses prediction methods to check future states
        
        WARNINGS GENERATED:
        1. "Will become URGENT in next 3 iterations"
           - Temporal dimension will exceed 0.8 within 3 time steps
           - Enables proactive prioritization
        
        2. "Will become RISKY in next 3 iterations"
           - Error dimension will exceed 0.7 within 3 time steps
           - Enables early risk mitigation
        
        3. "{Dimension} dimension {increasing/decreasing} rapidly"
           - Velocity magnitude > 0.2 (rapid change)
           - Indicates unstable or volatile objective
        
        EXAMPLE OUTPUT:
        [
            "Will become URGENT in next 3 iterations",
            "Temporal dimension increasing rapidly",
            "Error dimension increasing rapidly"
        ]
        
        INTEGRATION: Logged in _determine_next_action_strategic() (line 1725)
        Appears in logs as:
        ⚠️ Trajectory: Will become URGENT in next 3 iterations
        ⚠️ Trajectory: Temporal dimension increasing rapidly
        ============================================================================
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        if self.will_become_urgent(threshold=0.8, time_steps=3):
            warnings.append("Will become URGENT in next 3 iterations")
        
        if self.will_become_risky(threshold=0.7, time_steps=3):
            warnings.append("Will become RISKY in next 3 iterations")
        
        # Check for rapid dimensional changes
        for dim, velocity in self.dimensional_velocity.items():
            if abs(velocity) > 0.2:  # Rapid change
                direction = "increasing" if velocity > 0 else "decreasing"
                warnings.append(f"{dim.title()} dimension {direction} rapidly")
        
        return warnings
    
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
    # ============================================================================
    # WEEK 2 PHASE 3: ADVANCED TRAJECTORY PREDICTION ENHANCEMENTS
    # ============================================================================
    
    def predict_with_model(self, model: str = "linear", time_steps: int = 5) -> List[Dict[str, float]]:
        """
        Predict future dimensional states using specified model.
        
        PREDICTION MODELS:
        1. LINEAR: velocity * damping^t (default, good for stable trends)
        2. EXPONENTIAL: value * (1 + velocity)^t (good for accelerating changes)
        3. SIGMOID: asymptotic approach to limit (good for bounded growth)
        
        Args:
            model: Prediction model ('linear', 'exponential', 'sigmoid')
            time_steps: Number of future time steps to predict
            
        Returns:
            List of predicted dimensional profiles at each time step
        """
        if not self.dimensional_velocity:
            return [self.dimensional_profile.copy()] * time_steps
        
        predictions = []
        current = self.dimensional_profile.copy()
        
        if model == "linear":
            # Linear model with damping (existing implementation)
            damping_factor = 0.9
            for t in range(time_steps):
                predicted = {}
                for dim, value in current.items():
                    velocity = self.dimensional_velocity.get(dim, 0.0)
                    damped_velocity = velocity * (damping_factor ** t)
                    predicted[dim] = max(0.0, min(1.0, value + damped_velocity))
                predictions.append(predicted)
                current = predicted
                
        elif model == "exponential":
            # Exponential growth/decay model
            for t in range(1, time_steps + 1):
                predicted = {}
                for dim, value in self.dimensional_profile.items():
                    velocity = self.dimensional_velocity.get(dim, 0.0)
                    # Exponential: value * (1 + velocity)^t
                    growth_factor = 1.0 + velocity
                    predicted[dim] = max(0.0, min(1.0, value * (growth_factor ** t)))
                predictions.append(predicted)
                
        elif model == "sigmoid":
            # Sigmoid model (asymptotic approach to limit)
            for t in range(1, time_steps + 1):
                predicted = {}
                for dim, value in self.dimensional_profile.items():
                    velocity = self.dimensional_velocity.get(dim, 0.0)
                    # Sigmoid: approach 1.0 if velocity > 0, approach 0.0 if velocity < 0
                    if velocity > 0:
                        limit = 1.0
                        k = 5.0  # Steepness factor
                        predicted[dim] = limit - (limit - value) * math.exp(-k * velocity * t)
                    elif velocity < 0:
                        limit = 0.0
                        k = 5.0
                        predicted[dim] = limit + (value - limit) * math.exp(k * velocity * t)
                    else:
                        predicted[dim] = value
                    predicted[dim] = max(0.0, min(1.0, predicted[dim]))
                predictions.append(predicted)
        else:
            # Default to linear
            return self.predict_dimensional_state(time_steps)
        
        return predictions
    
    def select_best_model(self) -> str:
        """
        Select best prediction model based on historical patterns.
        
        MODEL SELECTION CRITERIA:
        1. LINEAR: Default, good for most cases
        2. EXPONENTIAL: Use if velocity is accelerating (variance > 0.1)
        3. SIGMOID: Use if approaching limits (value near 0.0 or 1.0)
        
        Returns:
            Best model name ('linear', 'exponential', 'sigmoid')
        """
        if not self.dimensional_history or len(self.dimensional_history) < 3:
            return "linear"  # Default for insufficient history
        
        # Analyze velocity patterns
        velocity_variance = 0.0
        near_limits = 0
        total_dims = len(self.dimensional_profile)
        
        for dim in self.dimensional_profile.keys():
            velocity = self.dimensional_velocity.get(dim, 0.0)
            value = self.dimensional_profile[dim]
            
            # Check if near limits (0.0 or 1.0)
            if value < 0.2 or value > 0.8:
                near_limits += 1
            
            # Calculate velocity variance from history
            if len(self.dimensional_history) >= 3:
                recent_velocities = []
                for i in range(len(self.dimensional_history) - 2):
                    v1 = self.dimensional_history[i].get("profile", {}).get(dim, 0.0)
                    v2 = self.dimensional_history[i + 1].get("profile", {}).get(dim, 0.0)
                    recent_velocities.append(v2 - v1)
                
                if recent_velocities:
                    mean_v = sum(recent_velocities) / len(recent_velocities)
                    variance = sum((v - mean_v) ** 2 for v in recent_velocities) / len(recent_velocities)
                    velocity_variance += variance
        
        velocity_variance /= total_dims
        near_limit_ratio = near_limits / total_dims
        
        # Model selection logic
        if near_limit_ratio > 0.5:
            return "sigmoid"  # Many dimensions near limits
        elif velocity_variance > 0.1:
            return "exponential"  # High velocity variance (acceleration)
        else:
            return "linear"  # Stable, predictable changes
    
    def get_prediction_confidence(self, predictions: List[Dict[str, float]]) -> float:
        """
        Calculate confidence score for predictions (0.0 to 1.0).
        
        CONFIDENCE FACTORS:
        1. Velocity stability (low variance = high confidence)
        2. Historical accuracy (if available)
        3. Time horizon (confidence decays with distance)
        4. Data sufficiency (more history = higher confidence)
        
        Args:
            predictions: List of predicted dimensional profiles
            
        Returns:
            Confidence score (0.0 = no confidence, 1.0 = high confidence)
        """
        if not predictions:
            return 0.0
        
        # Factor 1: Velocity stability
        velocity_stability = 1.0
        if self.dimensional_velocity:
            velocities = list(self.dimensional_velocity.values())
            if velocities:
                mean_v = sum(abs(v) for v in velocities) / len(velocities)
                variance = sum((abs(v) - mean_v) ** 2 for v in velocities) / len(velocities)
                velocity_stability = max(0.0, 1.0 - variance * 10)  # Scale variance
        
        # Factor 2: Historical accuracy (placeholder - would need actual vs predicted comparison)
        historical_accuracy = 0.8  # Default assumption
        
        # Factor 3: Time horizon decay
        time_steps = len(predictions)
        time_decay = 0.95 ** time_steps  # Confidence decays with distance
        
        # Factor 4: Data sufficiency
        history_length = len(self.dimensional_history)
        data_sufficiency = min(1.0, history_length / 10.0)  # Full confidence at 10+ history points
        
        # Weighted average
        confidence = (
            velocity_stability * 0.3 +
            historical_accuracy * 0.2 +
            time_decay * 0.3 +
            data_sufficiency * 0.2
        )
        
        return max(0.0, min(1.0, confidence))
    
    def calculate_trajectory_confidence(self) -> Dict[str, float]:
        """
        Calculate confidence for each dimension's trajectory.
        
        CONFIDENCE CALCULATION:
        - Per-dimension confidence based on velocity stability
        - Higher confidence for stable velocities
        - Lower confidence for volatile dimensions
        
        Returns:
            Dictionary mapping dimension name to confidence score
        """
        confidence = {}
        
        for dim in self.dimensional_profile.keys():
            velocity = abs(self.dimensional_velocity.get(dim, 0.0))
            
            # Calculate stability from history
            stability = 1.0
            if len(self.dimensional_history) >= 3:
                recent_values = []
                for entry in self.dimensional_history[-5:]:
                    recent_values.append(entry.get("profile", {}).get(dim, 0.0))
                
                if len(recent_values) >= 2:
                    diffs = [abs(recent_values[i+1] - recent_values[i]) 
                            for i in range(len(recent_values)-1)]
                    mean_diff = sum(diffs) / len(diffs)
                    variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
                    stability = max(0.0, 1.0 - variance * 10)
            
            # Combine velocity magnitude and stability
            # Low velocity + high stability = high confidence
            # High velocity + low stability = low confidence
            dim_confidence = stability * (1.0 - min(1.0, velocity * 2))
            confidence[dim] = max(0.0, min(1.0, dim_confidence))
        
        return confidence
    
    def get_confidence_decay_factor(self, time_steps: int) -> float:
        """
        Calculate confidence decay over time.
        
        DECAY MODEL:
        - Confidence = base_confidence * (0.9^time_steps)
        - At t=1: 90% confidence
        - At t=3: 73% confidence
        - At t=5: 59% confidence
        
        Args:
            time_steps: Number of time steps into future
            
        Returns:
            Decay factor (0.0 to 1.0)
        """
        decay_rate = 0.9
        return decay_rate ** time_steps
    
    def get_intervention_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate specific intervention recommendations based on trajectory.
        
        RECOMMENDATION TYPES:
        1. INCREASE_PRIORITY: Objective will become urgent
        2. RISK_MITIGATION: Objective will become risky
        3. RESOURCE_ALLOCATION: Complex objective needs resources
        4. DEPENDENCY_RESOLUTION: High data/context dependencies
        5. ARCHITECTURE_REVIEW: High architecture impact
        
        Returns:
            List of intervention dictionaries with action, reason, priority, phase
        """
        recommendations = []
        predictions = self.predict_dimensional_state(3)
        
        if not predictions:
            return recommendations
        
        # Check for urgency
        if self.will_become_urgent(threshold=0.8, time_steps=3):
            recommendations.append({
                "action": "increase_priority",
                "reason": "Will become urgent in next 3 iterations",
                "priority": 0.9,
                "phase": "planning",
                "dimension": "temporal"
            })
        
        # Check for risk
        if self.will_become_risky(threshold=0.7, time_steps=3):
            recommendations.append({
                "action": "risk_mitigation",
                "reason": "Will become risky in next 3 iterations",
                "priority": 0.85,
                "phase": "qa",
                "dimension": "error"
            })
        
        # Check for high complexity
        future_complexity = (
            predictions[0].get("functional", 0.0) * 0.25 +
            predictions[0].get("data", 0.0) * 0.15 +
            predictions[0].get("state", 0.0) * 0.15 +
            predictions[0].get("integration", 0.0) * 0.25 +
            predictions[0].get("architecture", 0.0) * 0.20
        )
        
        if future_complexity > 0.7:
            recommendations.append({
                "action": "resource_allocation",
                "reason": f"High complexity predicted ({future_complexity:.2f})",
                "priority": 0.75,
                "phase": "investigation",
                "dimension": "functional"
            })
        
        # Check for dependency issues
        future_deps = max(
            predictions[0].get("data", 0.0),
            predictions[0].get("context", 0.0)
        )
        
        if future_deps > 0.7:
            recommendations.append({
                "action": "dependency_resolution",
                "reason": f"High dependencies predicted ({future_deps:.2f})",
                "priority": 0.7,
                "phase": "planning",
                "dimension": "data"
            })
        
        # Check for architecture impact
        future_arch = predictions[0].get("architecture", 0.0)
        if future_arch > 0.7:
            recommendations.append({
                "action": "architecture_review",
                "reason": f"High architecture impact predicted ({future_arch:.2f})",
                "priority": 0.8,
                "phase": "refactoring",
                "dimension": "architecture"
            })
        
        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommendations
    
    def get_mitigation_strategies(self) -> List[str]:
        """
        Get strategies to mitigate predicted risks.
        
        MITIGATION STRATEGIES:
        1. Temporal: Break into smaller tasks, increase resources
        2. Error: Add validation, increase testing, code review
        3. Complexity: Simplify design, add documentation
        4. Dependencies: Decouple, add interfaces, mock dependencies
        5. Architecture: Review design, consult team, prototype
        
        Returns:
            List of mitigation strategy descriptions
        """
        strategies = []
        predictions = self.predict_dimensional_state(3)
        
        if not predictions:
            return strategies
        
        future_state = predictions[0]
        
        # Temporal mitigation
        if future_state.get("temporal", 0.0) > 0.7:
            strategies.append("Break objective into smaller, time-boxed tasks")
            strategies.append("Allocate additional resources to meet deadline")
            strategies.append("Identify and remove blockers early")
        
        # Error mitigation
        if future_state.get("error", 0.0) > 0.7:
            strategies.append("Add comprehensive input validation")
            strategies.append("Increase test coverage (unit + integration)")
            strategies.append("Implement error handling and recovery")
            strategies.append("Schedule code review with senior developer")
        
        # Complexity mitigation
        if future_state.get("functional", 0.0) > 0.7:
            strategies.append("Simplify design - apply SOLID principles")
            strategies.append("Add detailed documentation and examples")
            strategies.append("Create architectural diagrams")
            strategies.append("Consider design patterns for complexity management")
        
        # Dependency mitigation
        if future_state.get("data", 0.0) > 0.7 or future_state.get("context", 0.0) > 0.7:
            strategies.append("Decouple components - reduce tight coupling")
            strategies.append("Add abstraction layers (interfaces)")
            strategies.append("Use dependency injection")
            strategies.append("Create mock implementations for testing")
        
        # Architecture mitigation
        if future_state.get("architecture", 0.0) > 0.7:
            strategies.append("Review architectural design with team")
            strategies.append("Create proof-of-concept prototype")
            strategies.append("Document architectural decisions (ADRs)")
            strategies.append("Validate against ARCHITECTURE.md")
        
        return strategies

