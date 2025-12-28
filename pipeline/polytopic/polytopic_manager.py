"""
Polytopic Objective Manager

Extends ObjectiveManager with 7D hyperdimensional navigation and
intelligent objective selection capabilities.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
from datetime import datetime

from ..objective_manager import ObjectiveManager, Objective
from ..state.manager import StateManager, PipelineState
from .polytopic_objective import PolytopicObjective
from .dimensional_space import DimensionalSpace
from .visualizations import PolytopicVisualizer


class PolytopicObjectiveManager(ObjectiveManager):
    """
    Enhanced objective manager with 7D polytopic navigation.
    
    Provides:
    - Automatic dimensional profile calculation
    - 7D space navigation
    - Intelligent objective selection
    - Dimensional health analysis
    - Trajectory prediction
    """
    
    def __init__(self, project_dir: str, state_manager: StateManager):
        """
        Initialize polytopic objective manager.
        
        Args:
            project_dir: Project directory path
            state_manager: State manager instance
        """
        super().__init__(project_dir, state_manager)
        self.dimensional_space = DimensionalSpace(dimensions=7)
        self.visualizer = PolytopicVisualizer(self.dimensional_space)
        
    def load_objectives(self, state: PipelineState) -> Dict[str, Dict[str, PolytopicObjective]]:
        """Load objectives from markdown files and populate dimensional space."""
        # Load using parent method
        objectives_by_level = super().load_objectives(state)
        
        # Convert to polytopic objectives and add to dimensional space
        polytopic_objectives_by_level = {
            "primary": {},
            "secondary": {},
            "tertiary": {}
        }
        
        for level, objectives in objectives_by_level.items():
            for obj_id, obj in objectives.items():
                # Convert to PolytopicObjective if not already
                if not isinstance(obj, PolytopicObjective):
                    poly_obj = self._convert_to_polytopic(obj)
                    polytopic_objectives_by_level[level][obj_id] = poly_obj
                else:
                    polytopic_objectives_by_level[level][obj_id] = obj
                
                # Add to dimensional space
                self.dimensional_space.add_objective(polytopic_objectives_by_level[level][obj_id])
        
        return polytopic_objectives_by_level
    
    def _convert_to_polytopic(self, objective: Objective) -> PolytopicObjective:
        """
        Convert regular Objective to PolytopicObjective.
        
        Args:
            objective: Regular objective
            
        Returns:
            Polytopic objective with calculated dimensional profile
        """
        # Create polytopic objective with same base properties
        poly_obj = PolytopicObjective(
            id=objective.id,
            level=objective.level,
            title=objective.title,
            description=objective.description,
            status=objective.status,
            target_date=objective.target_date,
            tasks=objective.tasks.copy(),
            depends_on=objective.depends_on.copy(),
            blocks=objective.blocks.copy(),
            acceptance_criteria=objective.acceptance_criteria.copy(),
            open_issues=objective.open_issues.copy(),
            critical_issues=objective.critical_issues.copy(),
            created_at=objective.created_at,
            completed_tasks=objective.completed_tasks.copy(),
            total_tasks=objective.total_tasks,
            completion_percentage=objective.completion_percentage,
            success_rate=objective.success_rate,
            avg_task_duration=objective.avg_task_duration,
            failure_count=objective.failure_count,
            started_at=objective.started_at,
            completed_at=objective.completed_at
        )
        
        # Calculate dimensional profile
        poly_obj.dimensional_profile = self.calculate_dimensional_profile(poly_obj)
        poly_obj.polytopic_position = poly_obj._calculate_position()
        poly_obj._update_metrics()
        
        return poly_obj
    
    def calculate_dimensional_profile(self, objective: PolytopicObjective) -> Dict[str, float]:
        """
        Calculate 7D dimensional profile based on objective properties.
        
        Args:
            objective: Objective to analyze
            
        Returns:
            Dict with dimensional values (0.0 to 1.0)
        """
        profile = {}
        
        # D1: Temporal - Based on target date and status
        if objective.target_date:
            try:
                target = datetime.fromisoformat(objective.target_date)
                days_until = (target - datetime.now()).days
                
                if days_until < 7:
                    profile["temporal"] = 0.9  # Very urgent
                elif days_until < 30:
                    profile["temporal"] = 0.7  # Urgent
                elif days_until < 90:
                    profile["temporal"] = 0.5  # Moderate
                else:
                    profile["temporal"] = 0.3  # Low urgency
            except:
                profile["temporal"] = 0.5
        else:
            profile["temporal"] = 0.5
        
        # Increase urgency if status is approved
        if objective.status == "approved":
            profile["temporal"] = min(1.0, profile["temporal"] + 0.2)
        
        # D2: Functional - Based on task count and description complexity
        task_count = len(objective.tasks)
        description_length = len(objective.description)
        
        # More tasks = more functional complexity
        task_factor = min(1.0, task_count / 20.0)  # Normalize to 20 tasks
        
        # Longer description = more complex functionality
        desc_factor = min(1.0, description_length / 1000.0)  # Normalize to 1000 chars
        
        profile["functional"] = (task_factor * 0.6 + desc_factor * 0.4)
        
        # D3: Data - Based on dependencies and task file references
        dependency_count = len(objective.depends_on)
        
        # Count file references in tasks (approximate data dependencies)
        file_references = sum(1 for task in objective.tasks if '.py' in task or '.js' in task or '.json' in task)
        
        dependency_factor = min(1.0, dependency_count / 5.0)  # Normalize to 5 dependencies
        file_factor = min(1.0, file_references / 10.0)  # Normalize to 10 files
        
        profile["data"] = (dependency_factor * 0.6 + file_factor * 0.4)
        
        # D4: State - Based on keywords in description and tasks
        state_keywords = ['state', 'session', 'cache', 'store', 'persist', 'memory', 'context']
        
        description_lower = objective.description.lower()
        tasks_lower = ' '.join(objective.tasks).lower()
        
        state_mentions = sum(1 for keyword in state_keywords 
                           if keyword in description_lower or keyword in tasks_lower)
        
        profile["state"] = min(1.0, state_mentions / 5.0)  # Normalize to 5 mentions
        
        # D5: Error - Based on critical issues and risk keywords
        critical_issue_count = len(objective.critical_issues)
        
        risk_keywords = ['error', 'exception', 'fail', 'bug', 'issue', 'risk', 'critical']
        risk_mentions = sum(1 for keyword in risk_keywords 
                          if keyword in description_lower or keyword in tasks_lower)
        
        issue_factor = min(1.0, critical_issue_count / 5.0)  # Normalize to 5 critical issues
        risk_factor = min(1.0, risk_mentions / 5.0)  # Normalize to 5 mentions
        
        profile["error"] = (issue_factor * 0.6 + risk_factor * 0.4)
        
        # D6: Context - Based on acceptance criteria and description detail
        criteria_count = len(objective.acceptance_criteria)
        
        # More criteria = more context needed
        criteria_factor = min(1.0, criteria_count / 10.0)  # Normalize to 10 criteria
        
        # Check for context keywords
        context_keywords = ['context', 'environment', 'configuration', 'setup', 'prerequisite']
        context_mentions = sum(1 for keyword in context_keywords 
                             if keyword in description_lower or keyword in tasks_lower)
        
        context_factor = min(1.0, context_mentions / 5.0)
        
        profile["context"] = (criteria_factor * 0.5 + context_factor * 0.5)
        
        # D7: Integration - Based on dependencies and integration keywords
        integration_keywords = ['integrate', 'connect', 'interface', 'api', 'service', 'component']
        integration_mentions = sum(1 for keyword in integration_keywords 
                                 if keyword in description_lower or keyword in tasks_lower)
        
        integration_factor = min(1.0, integration_mentions / 5.0)
        
        # Dependencies also indicate integration needs
        profile["integration"] = (dependency_factor * 0.5 + integration_factor * 0.5)
        
        return profile
    
    def find_optimal_objective(self, current_state: PipelineState) -> Optional[PolytopicObjective]:
        """
        Use 7D navigation to find best next objective.
        
        Args:
            current_state: Current pipeline state
            
        Returns:
            Best objective to work on, or None
        """
        return self.dimensional_space.find_optimal_next_objective({
            "state": current_state
        })
    
    def calculate_objective_distance(self, obj1: PolytopicObjective, 
                                    obj2: PolytopicObjective) -> float:
        """
        Calculate distance between two objectives in 7D space.
        
        Args:
            obj1: First objective
            obj2: Second objective
            
        Returns:
            Euclidean distance in 7D space
        """
        return obj1.calculate_distance_to(obj2)
    
    def get_adjacent_objectives(self, objective: PolytopicObjective) -> List[PolytopicObjective]:
        """
        Get objectives adjacent to given objective in polytopic space.
        
        Args:
            objective: Reference objective
            
        Returns:
            List of adjacent objectives
        """
        adjacent_ids = objective.adjacent_objectives
        return [self.objectives[obj_id] for obj_id in adjacent_ids 
                if obj_id in self.objectives]
    
    def analyze_dimensional_health(self, objective: PolytopicObjective) -> Dict[str, Any]:
        """
        Analyze health across all 7 dimensions.
        
        Args:
            objective: Objective to analyze
            
        Returns:
            Dict with dimensional health analysis
        """
        health = {
            "objective_id": objective.id,
            "overall_health": "HEALTHY",
            "dimensional_analysis": {},
            "concerns": [],
            "recommendations": []
        }
        
        # Analyze each dimension
        for dim, value in objective.dimensional_profile.items():
            dim_health = {
                "value": value,
                "status": "NORMAL",
                "concern_level": "LOW"
            }
            
            # High values in certain dimensions indicate concerns
            if dim in ["error", "temporal"] and value > 0.7:
                dim_health["status"] = "HIGH"
                dim_health["concern_level"] = "HIGH"
                health["concerns"].append(f"High {dim} dimension ({value:.2f})")
                
                if dim == "error":
                    health["recommendations"].append("Address critical issues immediately")
                elif dim == "temporal":
                    health["recommendations"].append("Prioritize this objective due to time constraints")
            
            elif dim in ["functional", "integration"] and value > 0.8:
                dim_health["status"] = "VERY_HIGH"
                dim_health["concern_level"] = "MEDIUM"
                health["concerns"].append(f"Very high {dim} complexity ({value:.2f})")
                health["recommendations"].append(f"Consider breaking down {dim} requirements")
            
            health["dimensional_analysis"][dim] = dim_health
        
        # Determine overall health
        high_concerns = len([c for c in health["dimensional_analysis"].values() 
                           if c["concern_level"] == "HIGH"])
        medium_concerns = len([c for c in health["dimensional_analysis"].values() 
                             if c["concern_level"] == "MEDIUM"])
        
        if high_concerns >= 2:
            health["overall_health"] = "CRITICAL"
        elif high_concerns >= 1 or medium_concerns >= 3:
            health["overall_health"] = "DEGRADING"
        elif medium_concerns >= 1:
            health["overall_health"] = "ATTENTION_NEEDED"
        
        # Add metrics
        health["complexity_score"] = objective.complexity_score
        health["risk_score"] = objective.risk_score
        health["readiness_score"] = objective.readiness_score
        
        return health
    
    def get_dimensional_statistics(self) -> Dict[str, Any]:
        """
        Get statistics across all objectives in dimensional space.
        
        Returns:
            Dict with dimensional statistics
        """
        return self.dimensional_space.calculate_dimensional_statistics()
    
    def cluster_objectives(self, max_distance: float = 0.4) -> Dict[str, List[str]]:
        """
        Cluster objectives based on dimensional similarity.
        
        Args:
            max_distance: Maximum distance within a cluster
            
        Returns:
            Dict mapping cluster_id to list of objective IDs
        """
        return self.dimensional_space.cluster_objectives(max_distance)
    
    def visualize_dimensional_space(self) -> str:
        """
        Generate visualization of dimensional space.
        
        Returns:
            ASCII art visualization
        """
        return self.dimensional_space.visualize_space_2d()
    
    def get_space_summary(self) -> Dict[str, Any]:
        """
        Get summary of dimensional space.
        
        Returns:
            Dict with space statistics
        """
        return self.dimensional_space.get_space_summary()
    
    def update_objective_dimensions(self, objective_id: str, 
                                   dimension: str, value: float) -> None:
        """
        Update a specific dimension of an objective.
        
        Args:
            objective_id: Objective ID
            dimension: Dimension name
            value: New value (0.0 to 1.0)
        """
        if objective_id not in self.dimensional_space.objectives:
            raise ValueError(f"Objective not found: {objective_id}")
        
        objective = self.dimensional_space.objectives[objective_id]
        objective.update_dimensional_profile(dimension, value)
        
        # Update in dimensional space
        self.dimensional_space._update_adjacency(objective)
    
    def predict_objective_trajectory(self, objective_id: str, 
                                    time_steps: int = 5) -> List[List[float]]:
        """
        Predict future trajectory of an objective.
        
        Args:
            objective_id: Objective ID
            time_steps: Number of time steps to predict
            
        Returns:
            List of predicted positions
        """
        if objective_id not in self.dimensional_space.objectives:
            raise ValueError(f"Objective not found: {objective_id}")
        
        objective = self.dimensional_space.objectives[objective_id]
        return self.dimensional_space.calculate_trajectory(objective, time_steps)
    
    def find_similar_objectives(self, objective_id: str, 
                               similarity_threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find objectives similar to the given one.
        
        Args:
            objective_id: Reference objective ID
            similarity_threshold: Minimum similarity (0.0 to 1.0)
            
        Returns:
            List of (objective_id, similarity) tuples
        """
        if objective_id not in self.dimensional_space.objectives:
            raise ValueError(f"Objective not found: {objective_id}")
        
        objective = self.dimensional_space.objectives[objective_id]
        similar = self.dimensional_space.find_similar_objectives(objective, similarity_threshold)
        
        return [(obj.id, sim) for obj, sim in similar]
    
    def visualize_3d_space(self, dimensions: Tuple[str, str, str] = ("temporal", "functional", "data")) -> str:
        """
        Create 3D visualization of objectives.
        
        Args:
            dimensions: Tuple of 3 dimension names to visualize
            
        Returns:
            ASCII 3D visualization
        """
        return self.visualizer.visualize_3d_space(dimensions)
    
    def visualize_trajectory(self, objective_id: str, time_steps: int = 5) -> str:
        """
        Visualize trajectory of an objective.
        
        Args:
            objective_id: Objective ID
            time_steps: Number of future time steps
            
        Returns:
            ASCII trajectory visualization
        """
        return self.visualizer.visualize_trajectory(objective_id, time_steps)
    
    def visualize_health_heatmap(self) -> str:
        """
        Create health heatmap for all objectives.
        
        Returns:
            ASCII heatmap visualization
        """
        return self.visualizer.visualize_health_heatmap()
    
    def visualize_clusters(self, max_distance: float = 0.4) -> str:
        """
        Visualize objective clusters.
        
        Args:
            max_distance: Maximum distance for clustering
            
        Returns:
            ASCII cluster visualization
        """
        return self.visualizer.visualize_clusters(max_distance)
    
    def visualize_dimensional_distribution(self) -> str:
        """
        Visualize distribution across dimensions.
        
        Returns:
            ASCII distribution visualization
        """
        return self.visualizer.visualize_dimensional_distribution()
    
    def visualize_adjacency_graph(self, max_objectives: int = 10) -> str:
        """
        Visualize adjacency relationships.
        
        Args:
            max_objectives: Maximum objectives to show
            
        Returns:
            ASCII adjacency graph
        """
        return self.visualizer.visualize_adjacency_graph(max_objectives)
    
    def generate_comprehensive_visualization_report(self) -> str:
        """
        Generate comprehensive visualization report.
        
        Returns:
            Complete visualization report
        """
        return self.visualizer.generate_comprehensive_report()
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"PolytopicObjectiveManager(objectives={len(self.dimensional_space.objectives)}, "
                f"dimensional_space={self.dimensional_space})")