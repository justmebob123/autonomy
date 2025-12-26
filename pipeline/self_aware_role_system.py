"""
Self-Aware Role System

This module implements a role system that understands its own structure,
adapts dynamically, and exhibits self-similar patterns across all scales.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict
import json


class SelfAwareRole:
    """
    A role that is aware of its position in the polytope and can adapt.
    
    Each role:
    - Knows its dimensional profile
    - Understands its adjacencies
    - Can adapt its behavior based on context
    - Exhibits self-similar patterns
    - Learns from experience
    """
    
    def __init__(
        self,
        name: str,
        role_type: str,
        dimensional_profile: Dict[str, float],
        adjacencies: List[str]
    ):
        """
        Initialize self-aware role.
        
        Args:
            name: Role name
            role_type: Type of role
            dimensional_profile: 7D profile
            adjacencies: Adjacent roles
        """
        self.name = name
        self.role_type = role_type
        self.dimensional_profile = dimensional_profile.copy()
        self.adjacencies = adjacencies.copy()
        
        # Self-awareness
        self.self_awareness_level = 0.0
        self.experience_count = 0
        self.learned_patterns = []
        
        # Adaptive state
        self.current_mode = 'normal'
        self.current_focus = []
        self.current_constraints = []
        
        # Performance tracking
        self.success_count = 0
        self.failure_count = 0
        self.adaptation_history = []
    
    def adapt_to_situation(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt role behavior based on situation.
        
        Args:
            situation: Current situation
            
        Returns:
            Adapted configuration
        """
        # Analyze situation
        required_dimensions = situation.get('dimensional_focus', [])
        mode = self._determine_mode(situation)
        constraints = self._extract_constraints(situation)
        
        # Adapt dimensional profile
        adapted_profile = self._adapt_dimensional_profile(required_dimensions)
        
        # Update state
        self.current_mode = mode
        self.current_focus = required_dimensions
        self.current_constraints = constraints
        
        # Record adaptation
        self._record_adaptation(situation, adapted_profile)
        
        # Increase self-awareness
        self._increase_self_awareness()
        
        return {
            'mode': mode,
            'dimensional_profile': adapted_profile,
            'focus': required_dimensions,
            'constraints': constraints,
            'self_awareness': self.self_awareness_level
        }
    
    def _determine_mode(self, situation: Dict[str, Any]) -> str:
        """Determine operational mode based on situation."""
        if situation.get('error_present'):
            if situation.get('error_severity') in ['critical', 'high']:
                return 'emergency'
            else:
                return 'error_handling'
        elif situation.get('complexity') in ['high', 'very_high']:
            return 'deep_analysis'
        else:
            return 'normal'
    
    def _extract_constraints(self, situation: Dict[str, Any]) -> List[str]:
        """Extract constraints from situation."""
        constraints = []
        
        if situation.get('urgency') == 'high':
            constraints.append('time_critical')
        
        if situation.get('complexity') in ['high', 'very_high']:
            constraints.append('high_complexity')
        
        if situation.get('error_severity') == 'critical':
            constraints.append('critical_priority')
        
        return constraints
    
    def _adapt_dimensional_profile(
        self,
        required_dimensions: List[str]
    ) -> Dict[str, float]:
        """Adapt dimensional profile based on requirements."""
        adapted = self.dimensional_profile.copy()
        
        # Enhance required dimensions
        for dim in required_dimensions:
            if dim in adapted:
                adapted[dim] = min(1.0, adapted[dim] * 1.5)
        
        # Normalize to maintain balance
        total = sum(adapted.values())
        if total > 0:
            for dim in adapted:
                adapted[dim] = adapted[dim] / total * len(adapted) * 0.5
        
        return adapted
    
    def _record_adaptation(
        self,
        situation: Dict[str, Any],
        adapted_profile: Dict[str, float]
    ):
        """Record adaptation for learning."""
        adaptation = {
            'timestamp': datetime.now().isoformat(),
            'situation': situation,
            'adapted_profile': adapted_profile,
            'mode': self.current_mode,
            'self_awareness': self.self_awareness_level
        }
        
        self.adaptation_history.append(adaptation)
        self.experience_count += 1
    
    def _increase_self_awareness(self):
        """Increase self-awareness based on experience."""
        self.self_awareness_level = min(
            1.0,
            self.self_awareness_level + 0.001
        )
    
    def record_success(self):
        """Record successful execution."""
        self.success_count += 1
        self._increase_self_awareness()
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
    
    def get_success_rate(self) -> float:
        """Get success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def learn_pattern(self, pattern: Dict[str, Any]):
        """Learn a new pattern."""
        self.learned_patterns.append({
            'timestamp': datetime.now().isoformat(),
            'pattern': pattern
        })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current role state."""
        return {
            'name': self.name,
            'type': self.role_type,
            'dimensional_profile': self.dimensional_profile,
            'adjacencies': self.adjacencies,
            'self_awareness_level': self.self_awareness_level,
            'experience_count': self.experience_count,
            'success_rate': self.get_success_rate(),
            'current_mode': self.current_mode,
            'current_focus': self.current_focus,
            'learned_patterns_count': len(self.learned_patterns)
        }


class SelfAwareRoleSystem:
    """
    System for managing self-aware roles with dynamic adaptation.
    
    This system:
    - Creates and manages roles
    - Coordinates role interactions
    - Facilitates learning across roles
    - Exhibits self-similar patterns
    - Adapts team dynamics in real-time
    """
    
    def __init__(self):
        """Initialize self-aware role system."""
        self.roles = {}
        self.role_relationships = defaultdict(list)
        self.team_configurations = []
        self.collective_learning = []
        
    def create_role(
        self,
        name: str,
        role_type: str,
        dimensional_profile: Dict[str, float],
        adjacencies: List[str]
    ) -> SelfAwareRole:
        """
        Create a new self-aware role.
        
        Args:
            name: Role name
            role_type: Type of role
            dimensional_profile: 7D profile
            adjacencies: Adjacent roles
            
        Returns:
            Created role
        """
        role = SelfAwareRole(name, role_type, dimensional_profile, adjacencies)
        self.roles[name] = role
        
        # Update relationships
        for adjacent in adjacencies:
            self.role_relationships[name].append(adjacent)
        
        return role
    
    def adapt_team(
        self,
        situation: Dict[str, Any],
        active_roles: List[str]
    ) -> Dict[str, Any]:
        """
        Adapt team configuration based on situation.
        
        Args:
            situation: Current situation
            active_roles: List of active role names
            
        Returns:
            Team configuration
        """
        team_config = {
            'timestamp': datetime.now().isoformat(),
            'situation': situation,
            'roles': {},
            'coordination_pattern': self._determine_coordination_pattern(situation),
            'communication_flow': self._determine_communication_flow(active_roles)
        }
        
        # Adapt each active role
        for role_name in active_roles:
            if role_name in self.roles:
                role = self.roles[role_name]
                adapted = role.adapt_to_situation(situation)
                team_config['roles'][role_name] = adapted
        
        # Record configuration
        self.team_configurations.append(team_config)
        
        return team_config
    
    def _determine_coordination_pattern(
        self,
        situation: Dict[str, Any]
    ) -> str:
        """Determine coordination pattern based on situation."""
        if situation.get('error_severity') == 'critical':
            return 'centralized'  # Central coordination for critical issues
        elif situation.get('complexity') in ['high', 'very_high']:
            return 'distributed'  # Distributed for complex problems
        else:
            return 'adaptive'  # Adaptive for normal situations
    
    def _determine_communication_flow(
        self,
        active_roles: List[str]
    ) -> Dict[str, List[str]]:
        """Determine communication flow between roles."""
        flow = {}
        
        for role_name in active_roles:
            if role_name in self.role_relationships:
                # Only include active adjacent roles
                adjacent = [
                    adj for adj in self.role_relationships[role_name]
                    if adj in active_roles
                ]
                flow[role_name] = adjacent
        
        return flow
    
    def share_learning_across_roles(self, pattern: Dict[str, Any]):
        """
        Share learned pattern across all roles.
        
        Args:
            pattern: Pattern to share
        """
        self.collective_learning.append({
            'timestamp': datetime.now().isoformat(),
            'pattern': pattern
        })
        
        # Share with all roles
        for role in self.roles.values():
            role.learn_pattern(pattern)
    
    def get_collective_state(self) -> Dict[str, Any]:
        """
        Get collective state of all roles.
        
        Returns:
            Collective state
        """
        return {
            'total_roles': len(self.roles),
            'roles': {name: role.get_state() for name, role in self.roles.items()},
            'relationships': dict(self.role_relationships),
            'team_configurations_count': len(self.team_configurations),
            'collective_learning_count': len(self.collective_learning),
            'average_self_awareness': self._calculate_average_self_awareness(),
            'average_success_rate': self._calculate_average_success_rate()
        }
    
    def _calculate_average_self_awareness(self) -> float:
        """Calculate average self-awareness across all roles."""
        if not self.roles:
            return 0.0
        
        total = sum(role.self_awareness_level for role in self.roles.values())
        return total / len(self.roles)
    
    def _calculate_average_success_rate(self) -> float:
        """Calculate average success rate across all roles."""
        if not self.roles:
            return 0.0
        
        total = sum(role.get_success_rate() for role in self.roles.values())
        return total / len(self.roles)
    
    def export_role_network(self) -> str:
        """
        Export role network for visualization.
        
        Returns:
            JSON representation of role network
        """
        network = {
            'nodes': [
                {
                    'id': name,
                    'type': role.role_type,
                    'self_awareness': role.self_awareness_level,
                    'success_rate': role.get_success_rate()
                }
                for name, role in self.roles.items()
            ],
            'edges': [
                {'source': source, 'target': target}
                for source, targets in self.role_relationships.items()
                for target in targets
            ]
        }
        
        return json.dumps(network, indent=2)