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


def run_debug_qa_mode(args) -> int:
    """Run continuous debug/QA mode to check for errors and warnings."""
    import ast
    import py_compile
    import subprocess
    import time
    from pathlib import Path
    
    project_dir = Path(args.project_dir).resolve()
    
    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1
    
    print("\n" + "="*70)
    print("🔍 DEBUG/QA MODE - Continuous Error Detection")
    print("="*70)
    print(f"\nProject: {project_dir}")
    print("\nThis mode will continuously check for:")
    print("  • Syntax errors in Python files")
    print("  • Import errors")
    print("  • Runtime errors (when possible)")
    print("\nPress Ctrl+C to exit at any time.\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'─'*70}")
            print(f"🔄 Iteration {iteration} - {time.strftime('%H:%M:%S')}")
            print(f"{'─'*70}\n")
            
            # Find all Python files
            py_files = list(project_dir.rglob("*.py"))
            if not py_files:
                print("⚠️  No Python files found in project directory")
                break
            
            print(f"📁 Found {len(py_files)} Python files to check\n")
            
            errors_found = []
            warnings_found = []
            
            # Check each Python file
            for py_file in sorted(py_files):
                rel_path = py_file.relative_to(project_dir)
                
                # Skip __pycache__ and virtual environments
                if '__pycache__' in str(rel_path) or 'venv' in str(rel_path) or '.venv' in str(rel_path):
                    continue
                
                # 1. Syntax check using py_compile
                try:
                    py_compile.compile(str(py_file), doraise=True)
                except py_compile.PyCompileError as e:
                    errors_found.append({
                        'file': rel_path,
                        'type': 'SyntaxError',
                        'message': str(e.msg),
                        'line': e.exc_value.lineno if hasattr(e.exc_value, 'lineno') else None
                    })
                    continue
                
                # 2. AST parsing for deeper syntax validation
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content, filename=str(py_file))
                except SyntaxError as e:
                    errors_found.append({
                        'file': rel_path,
                        'type': 'SyntaxError',
                        'message': e.msg,
                        'line': e.lineno,
                        'offset': e.offset,
                        'text': e.text
                    })
                except Exception as e:
                    errors_found.append({
                        'file': rel_path,
                        'type': type(e).__name__,
                        'message': str(e)
                    })
            
            # 3. Try importing the main module to catch import errors
            if (project_dir / "pipeline" / "__init__.py").exists():
                print("🔍 Checking imports...")
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", "import pipeline"],
                        cwd=str(project_dir),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        if "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr:
                            errors_found.append({
                                'file': 'pipeline',
                                'type': 'ImportError',
                                'message': result.stderr.strip()
                            })
                except subprocess.TimeoutExpired:
                    warnings_found.append({
                        'type': 'Warning',
                        'message': 'Import check timed out after 10 seconds'
                    })
                except Exception as e:
                    warnings_found.append({
                        'type': 'Warning',
                        'message': f'Could not check imports: {e}'
                    })
            
            # Display results
            print("\n" + "="*70)
            print("📊 RESULTS")
            print("="*70 + "\n")
            
            if not errors_found and not warnings_found:
                print("✅ SUCCESS! No errors or warnings found.")
                print("\n🎉 All checks passed! The application appears to be error-free.")
                print("\nYou can now run the application normally.")
                return 0
            
            # Display errors
            if errors_found:
                print(f"❌ ERRORS FOUND: {len(errors_found)}\n")
                for i, error in enumerate(errors_found, 1):
                    print(f"{i}. {error['type']} in {error['file']}")
                    if error.get('line'):
                        print(f"   Line {error['line']}: {error['message']}")
                        if error.get('text'):
                            print(f"   Code: {error['text'].strip()}")
                        if error.get('offset'):
                            print(f"   Position: column {error['offset']}")
                    else:
                        print(f"   {error['message']}")
                    print()
            
            # Display warnings
            if warnings_found:
                print(f"⚠️  WARNINGS: {len(warnings_found)}\n")
                for i, warning in enumerate(warnings_found, 1):
                    print(f"{i}. {warning['type']}: {warning['message']}\n")
            
            # Wait for user action
            print("\n" + "─"*70)
            print("🔧 Please fix the errors above, then press Enter to re-check...")
            print("   Or press Ctrl+C to exit")
            print("─"*70)
            
            try:
                input()
            except KeyboardInterrupt:
                print("\n\n👋 Exiting debug/QA mode...")
                return 0
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting debug/QA mode...")
        return 0


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
    parser.add_argument(
        "--debug-qa",
        action="store_true",
        help="Debug/QA mode - continuously check for errors and warnings until resolved"
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
    
    # Debug/QA mode
    if args.debug_qa:
        return run_debug_qa_mode(args)
    
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
