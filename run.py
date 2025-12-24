#!/usr/bin/env python3
"""
AI Development Pipeline Application

This application uses the pipeline module to run autonomous code generation
on a project directory containing a MASTER_PLAN.md specification.

Usage:
    ./run.py ~/projects/myapp
    ./run.py ~/projects/myapp --iterations 10
    ./run.py ~/projects/myapp --fresh
    ./run.py --discover
"""

import argparse
import sys
from pathlib import Path

# Import the pipeline module
from pipeline import PhaseCoordinator, PipelineConfig


def discover_models(config: PipelineConfig) -> None:
    """Discover and display available models on Ollama servers."""
    print("\n🔍 Discovering Ollama servers...\n")
    
    coordinator = PhaseCoordinator(config)
    coordinator.client.discover_servers()
    
    print("\n📋 Model Assignments:\n")
    print(f"{'Task Type':<15} {'Model':<25} {'Server':<30} {'Status'}")
    print("=" * 85)
    
    for task_type, (model, server) in config.model_assignments.items():
        available = coordinator.client.get_model_for_task(task_type)
        if available:
            status = f"✓ {available[1]} @ {available[0]}"
        else:
            status = "✗ NOT FOUND"
        print(f"{task_type:<15} {model:<25} {server:<30} {status}")
    
    print()


def show_status(config: PipelineConfig) -> None:
    """Show current pipeline status."""
    # Import from the correct location
    from pipeline.state import StateManager
    from pipeline.state.manager import TaskStatus
    
    state_manager = StateManager(config.project_dir)
    state = state_manager.load()
    
    print(f"\n📊 Pipeline Status: {state.pipeline_run_id}")
    print("=" * 60)
    
    # Task counts
    status_counts = {}
    for task in state.tasks.values():
        status = task.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nTasks:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Phase stats
    print("\nPhase Statistics:")
    for phase_name, phase_state in state.phases.items():
        if phase_state.runs > 0:
            print(f"  {phase_name}: {phase_state.runs} runs, "
                  f"{phase_state.successes} success, {phase_state.failures} failed")
    
    # Recent files
    print("\nRecent Files:")
    files = sorted(state.files.values(), key=lambda f: f.last_modified, reverse=True)[:5]
    for f in files:
        print(f"  {f.qa_status.value:8} {f.filepath}")
    
    print()


def run_pipeline(config: PipelineConfig, resume: bool = True) -> bool:
    """Run the development pipeline."""
    coordinator = PhaseCoordinator(config)
    return coordinator.run(resume=resume)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI Development Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s ~/projects/myapp                    Run on project (resumes)
    %(prog)s ~/projects/myapp --fresh            Start fresh
    %(prog)s ~/projects/myapp -i 5               Limit to 5 iterations
    %(prog)s ~/projects/myapp -v                 Verbose mode (show prompts/responses)
    %(prog)s --discover                          Show available models
    %(prog)s ~/projects/myapp --status           Show pipeline status
        """
    )
    
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory containing MASTER_PLAN.md (default: current directory)"
    )
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=0,
        help="Maximum iterations (0 = unlimited, default: 0)"
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
        "--status",
        action="store_true",
        help="Show current pipeline status"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose mode - show prompts and responses"
    )
    
    # Server configuration
    parser.add_argument(
        "--server",
        action="append",
        dest="servers",
        metavar="HOST",
        help="Add Ollama server (can be specified multiple times)"
    )
    
    args = parser.parse_args()
    
    # Resolve project directory
    project_dir = Path(args.project_dir).resolve()
    
    # Build configuration - CRITICAL: pass verbose flag!
    config = PipelineConfig(
        project_dir=project_dir,
        git_enabled=not args.no_git,
        max_iterations=args.iterations,
        max_retries_per_task=args.max_retries,
        verbose=args.verbose,  # THIS LINE WAS MISSING!
    )
    
    # Add custom servers if specified
    if args.servers:
        from pipeline.config import ServerConfig
        config.servers = [
            ServerConfig(name=f"server{i}", host=host)
            for i, host in enumerate(args.servers)
        ]
    
    # Discovery mode
    if args.discover:
        discover_models(config)
        return 0
    
    # Status mode
    if args.status:
        if not project_dir.exists():
            print(f"Error: Project directory does not exist: {project_dir}", file=sys.stderr)
            return 1
        show_status(config)
        return 0
    
    # Validate project directory
    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1
    
    master_plan = project_dir / "MASTER_PLAN.md"
    if not master_plan.exists():
        print(f"Error: MASTER_PLAN.md not found in {project_dir}", file=sys.stderr)
        print("\nCreate a MASTER_PLAN.md file with your project specification.", file=sys.stderr)
        return 1
    
    # Run the pipeline
    try:
        resume = not args.fresh
        success = run_pipeline(config, resume=resume)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
