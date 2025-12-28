"""
Polytopic Integration Module

This module provides 7D hyperdimensional objective management capabilities,
including dimensional profiles, navigation, health analysis, and visualizations.
"""

from .polytopic_objective import PolytopicObjective
from .dimensional_space import DimensionalSpace
from .polytopic_manager import PolytopicObjectiveManager
from .visualizations import PolytopicVisualizer

__all__ = [
    'PolytopicObjective',
    'DimensionalSpace',
    'PolytopicObjectiveManager',
    'PolytopicVisualizer',
]