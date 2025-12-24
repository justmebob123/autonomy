#!/usr/bin/env python3
"""
AI Development Pipeline - CLI Entry Point

Usage:
    python -m pipeline -d /path/to/project [options]
    
Options:
    -d, --project-dir    Project directory (required)
    -i, --iterations     Max iterations (0 = unlimited)
    --max-retries        Max retries per task before skipping
    --no-git             Disable git integration
    --fresh              Start fresh, ignore saved state
    --discover           Only discover servers and show model assignments
    -v, --verbose        Enable verbose logging
"""

import argparse
import sys
from pathlib import Path

from .config import PipelineConfig
from .coordinator import PhaseCoordinator


def main():
    parser = argparse.ArgumentParser(
        description="AI Development Pipeline - State-Managed Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run pipeline on a project (resumes from saved state)
    python -m pipeline -d ~/projects/myapp
    
    # Start fresh, ignoring saved state
    python -m pipeline -d ~/projects/myapp --fresh
    
    # Run with limited iterations
    python -m pipeline -d ~/projects/myapp -i 10
    
    # Discover available models
    python -m pipeline -d . --discover
    
    # Verbose output
    python -m pipeline -d ~/projects/myapp -v
        """
    )
    
    parser.add_argument(
        "-d", "--project-dir",
        required=True,
        help="Project directory containing MASTER_PLAN.md"
    )
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=0,
        help="Maximum iterations (0 = unlimited)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per task before skipping (default: 3)"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Disable git integration"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh, ignore any saved state"
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Only discover servers and show model assignments"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    
    args = parser.parse_args()
    
    # Resolve project directory
    project_dir = Path(args.project_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create configuration
    config = PipelineConfig(
        project_dir=project_dir,
        git_enabled=not args.no_git,
        max_iterations=args.iterations,
        max_retries_per_task=args.max_retries,
    )
    
    # Create coordinator
    coordinator = PhaseCoordinator(config)
    
    # Discovery mode
    if args.discover:
        print("\n🔍 Discovering Ollama servers...\n")
        coordinator.client.discover_servers()
        
        print("\n📋 Model Assignments:\n")
        print(f"{'Task Type':<15} {'Model':<25} {'Preferred Server':<30} {'Available'}")
        print("-" * 85)
        
        for task_type, (model, server) in config.model_assignments.items():
            available = coordinator.client.get_model_for_task(task_type)
            status = "✓" if available else "✗"
            actual = f"{available[1]} @ {available[0]}" if available else "NOT FOUND"
            print(f"{task_type:<15} {model:<25} {server:<30} {status} {actual}")
        
        print()
        return 0
    
    # Run pipeline
    resume = not args.fresh
    success = coordinator.run(resume=resume)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
