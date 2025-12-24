"""
Pipeline Orchestration Module (Legacy)

This module provides backward compatibility with the original Pipeline class.
For new projects, use PhaseCoordinator instead.

The Pipeline class now wraps PhaseCoordinator internally.
"""

from pathlib import Path
from typing import Optional

from .config import PipelineConfig
from .logging_setup import setup_logging, get_logger
from .client import OllamaClient
from .coordinator import PhaseCoordinator


class Pipeline:
    """
    AI Development Pipeline (Legacy Interface)
    
    This class maintains backward compatibility with the original API.
    Internally, it delegates to PhaseCoordinator for state-managed execution.
    
    For new code, prefer using PhaseCoordinator directly:
    
        from pipeline import PhaseCoordinator, PipelineConfig
        
        config = PipelineConfig(project_dir=Path("/path/to/project"))
        coordinator = PhaseCoordinator(config)
        coordinator.run()
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.project_dir = Path(config.project_dir)
        
        # Set up logging
        log_file = self.project_dir / "pipeline.log"
        setup_logging(log_file)
        self.logger = get_logger()
        
        # Initialize client (for compatibility - used by discovery)
        self.client = OllamaClient(config)
        
        # Internal coordinator
        self._coordinator = PhaseCoordinator(config)
    
    def run(self) -> bool:
        """
        Run the development pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        return self._coordinator.run(resume=True)
    
    def run_fresh(self) -> bool:
        """
        Run the pipeline from scratch, ignoring any saved state.
        
        Returns:
            True if successful, False otherwise
        """
        return self._coordinator.run(resume=False)
    
    def discover_models(self) -> dict:
        """
        Discover available models on configured servers.
        
        Returns:
            Dict mapping server hosts to lists of model names
        """
        return self.client.discover_servers()


# Alias for clarity
LegacyPipeline = Pipeline
