"""
Team Coordination System

Consolidated module for specialist team coordination.
Combines SpecialistTeam and TeamOrchestrator functionality.
"""

from typing import Any, Dict, Optional
import logging

from .specialist_agents import SpecialistTeam
from .team_orchestrator import TeamOrchestrator


class TeamCoordinationFacade:
    """
    Facade for team coordination system.
    Simplifies specialist team and orchestration usage.
    """
    
    def __init__(self, client: Any, logger: logging.Logger, max_workers: int = 4):
        """
        Initialize the team coordination system.
        
        Args:
            client: LLM client
            logger: Logger instance
            max_workers: Maximum parallel workers for orchestration
        """
        self.specialist_team = SpecialistTeam(client, logger)
        self.team_orchestrator = TeamOrchestrator(
            client,
            self.specialist_team,
            logger,
            max_workers=max_workers
        )
        self.logger = logger
    
    def create_orchestration_plan(self, issue: Dict, context: Dict) -> Dict:
        """Create an orchestration plan for complex issues."""
        return self.team_orchestrator.create_orchestration_plan(issue, context)
    
    def execute_plan(self, plan: Dict, thread: Any) -> Dict:
        """Execute an orchestration plan."""
        return self.team_orchestrator.execute_plan(plan, thread)
    
    def consult_specialist(self, specialist_type: str, issue: Dict, 
                          context: Dict) -> Optional[Dict]:
        """
        Consult a specific specialist.
        
        Args:
            specialist_type: Type of specialist to consult
            issue: Issue to analyze
            context: Additional context
            
        Returns:
            Specialist response or None
        """
        try:
            # Note: This needs to be updated to match SpecialistTeam API
            # which requires thread and tools parameters
            # For now, return None as this interface mismatch needs design review
            self.logger.warning(f"consult_specialist interface mismatch - needs design review")
            return None
        except Exception as e:
            self.logger.error(f"Specialist consultation failed: {e}")
            return None