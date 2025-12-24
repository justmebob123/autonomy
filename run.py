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


def attempt_line_based_fix(file_path: Path, error_line: int, error: dict) -> bool:
    """
    Attempt a simple line-based fix for common syntax errors.
    
    This is a fallback when AI-based fixing fails.
    Uses direct line manipulation to avoid string escape issues.
    """
    from pipeline.line_fixer import fix_line_directly
    
    try:
        error_type = error.get('type', '')
        error_msg = error.get('message', '')
        
        return fix_line_directly(file_path, error_line, error_type, error_msg)
        
    except Exception as e:
        print(f"      ⚠️  Line-based fix exception: {e}")
        return False


def run_debug_qa_mode(args) -> int:
    """
    Run continuous debug/QA mode using the full AI pipeline.
    
    This mode:
    1. Scans all Python files for syntax/import errors
    2. Optionally follows a log file for runtime errors
    3. Uses the full pipeline (QA + Debugging phases) to fix issues
    4. Examines related files and dependencies
    5. Continues until all errors are resolved
    """
    import ast
    import subprocess
    import time
    import threading
    from pathlib import Path
    from collections import defaultdict
    
    project_dir = Path(args.project_dir).resolve()
    
    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1
    
    print("\n" + "="*70)
    print("🔍 DEBUG/QA MODE - Continuous AI-Powered Debugging & QA")
    print("="*70)
    print(f"\nProject: {project_dir}")
    print("\nThis mode will:")
    print("  • Scan all Python files for syntax and import errors")
    print("  • Use AI pipeline (QA + Debugging) to fix issues")
    print("  • Examine related files and dependencies")
    print("  • Track runtime errors from log files (if --follow specified)")
    print("  • Continue until all errors are resolved")
    
    if hasattr(args, 'follow_log') and args.follow_log:
        print(f"  • Following log file: {args.follow_log}")
    
    print("\nPress Ctrl+C to exit at any time.\n")
    
    # Build configuration for the pipeline
    config = PipelineConfig(
        project_dir=project_dir,
        git_enabled=not args.no_git,
        max_iterations=0,  # Unlimited iterations for debugging
        max_retries_per_task=args.max_retries,
        verbose=args.verbose,
    )
    
    # Add custom servers if specified
    if args.servers:
        from pipeline.config import ServerConfig
        config.servers = [
            ServerConfig(name=f"server{i}", host=host)
            for i, host in enumerate(args.servers)
        ]
    
    # Initialize pipeline components
    from pipeline.phases.qa import QAPhase
    from pipeline.phases.debugging import DebuggingPhase
    from pipeline.state.manager import StateManager, TaskState, TaskStatus
    from pipeline.state.priority import TaskPriority
    from pipeline.client import OllamaClient
    
    # Discover Ollama servers
    print("🔍 Discovering Ollama servers...")
    client = OllamaClient(config)
    client.discover_servers()
    print()
    
    # Initialize state manager
    state_manager = StateManager(project_dir)
    state = state_manager.load()
    
    # Initialize phases
    qa_phase = QAPhase(config, client)
    debug_phase = DebuggingPhase(config, client)
    
    # Log file monitoring
    log_errors = []
    log_monitor_active = False
    
    if hasattr(args, 'follow_log') and args.follow_log:
        log_file = Path(args.follow_log)
        if log_file.exists():
            log_monitor_active = True
            print(f"📋 Monitoring log file: {log_file}\n")
            
            def monitor_log():
                """Monitor log file for errors in background thread"""
                try:
                    with open(log_file, 'r') as f:
                        # Seek to end
                        f.seek(0, 2)
                        while log_monitor_active:
                            line = f.readline()
                            if line:
                                # Check for error patterns
                                if any(pattern in line.lower() for pattern in 
                                      ['error', 'exception', 'traceback', 'failed', 'critical']):
                                    log_errors.append({
                                        'timestamp': time.strftime('%H:%M:%S'),
                                        'line': line.strip()
                                    })
                            else:
                                time.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  Log monitoring error: {e}")
            
            # Start log monitoring thread
            log_thread = threading.Thread(target=monitor_log, daemon=True)
            log_thread.start()
        else:
            print(f"⚠️  Log file not found: {log_file}\n")
    
    iteration = 0
    consecutive_no_progress = 0
    max_no_progress = 3
    
    try:
        while True:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"🔄 ITERATION {iteration} - {time.strftime('%H:%M:%S')}")
            print(f"{'='*70}\n")
            
            # Phase 1: Scan for syntax errors
            print("📁 Phase 1: Scanning Python files for syntax errors...")
            py_files = list(project_dir.rglob("*.py"))
            
            # Filter out excluded directories
            py_files = [f for f in py_files if not any(
                excluded in str(f) for excluded in 
                ['__pycache__', 'venv', '.venv', '.git', 'node_modules']
            )]
            
            print(f"   Found {len(py_files)} Python files to check\n")
            
            syntax_errors = []
            import_errors = []
            
            # Check syntax
            for py_file in sorted(py_files):
                rel_path = py_file.relative_to(project_dir)
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content, filename=str(py_file))
                except SyntaxError as e:
                    syntax_errors.append({
                        'file': str(rel_path),
                        'type': 'SyntaxError',
                        'message': e.msg,
                        'line': e.lineno,
                        'offset': e.offset,
                        'text': e.text.strip() if e.text else None,
                        'full_path': str(py_file)
                    })
                except Exception as e:
                    syntax_errors.append({
                        'file': str(rel_path),
                        'type': type(e).__name__,
                        'message': str(e),
                        'line': None,
                        'full_path': str(py_file)
                    })
            
            # Phase 2: Check imports (only if no syntax errors)
            if not syntax_errors:
                print("📦 Phase 2: Checking imports...")
                
                # Try importing main module if it exists
                main_modules = ['__init__.py', '__main__.py', 'main.py']
                for main_mod in main_modules:
                    if (project_dir / main_mod).exists():
                        try:
                            result = subprocess.run(
                                [sys.executable, "-c", f"import sys; sys.path.insert(0, '{project_dir}'); import {project_dir.name}"],
                                capture_output=True,
                                text=True,
                                timeout=10,
                                cwd=str(project_dir.parent)
                            )
                            if result.returncode != 0 and result.stderr:
                                # Parse import error
                                if "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr:
                                    import_errors.append({
                                        'file': main_mod,
                                        'type': 'ImportError',
                                        'message': result.stderr.strip(),
                                        'line': None
                                    })
                        except subprocess.TimeoutExpired:
                            print("   ⚠️  Import check timed out")
                        except Exception as e:
                            print(f"   ⚠️  Import check error: {e}")
                        break
                print()
            
            # Phase 3: Check log errors
            runtime_errors = []
            if log_errors:
                print(f"📋 Phase 3: Processing {len(log_errors)} log errors...")
                runtime_errors = log_errors.copy()
                log_errors.clear()
                print()
            
            # Combine all errors
            all_errors = syntax_errors + import_errors + runtime_errors
            
            # Display results
            print("="*70)
            print("📊 SCAN RESULTS")
            print("="*70 + "\n")
            
            if not all_errors:
                print("✅ SUCCESS! No errors found.")
                
                if iteration == 1:
                    print("\n🎉 All checks passed! The application is error-free.")
                else:
                    print(f"\n🎉 All errors resolved after {iteration} iterations!")
                
                print("\nYou can now run the application normally.")
                return 0
            
            # Display error summary
            print(f"Found {len(all_errors)} total errors:")
            print(f"  • Syntax errors: {len(syntax_errors)}")
            print(f"  • Import errors: {len(import_errors)}")
            print(f"  • Runtime errors: {len(runtime_errors)}")
            print()
            
            # Display detailed errors
            for i, error in enumerate(all_errors[:10], 1):  # Show first 10
                print(f"{i}. {error['type']} in {error.get('file', 'unknown')}")
                if error.get('line'):
                    print(f"   Line {error['line']}: {error['message']}")
                    if error.get('text'):
                        print(f"   Code: {error['text']}")
                else:
                    msg = error['message'][:100]
                    print(f"   {msg}...")
                print()
            
            if len(all_errors) > 10:
                print(f"... and {len(all_errors) - 10} more errors\n")
            
            # Phase 4: Use AI Pipeline to fix errors
            print("="*70)
            print("🤖 AI PIPELINE - Fixing Errors")
            print("="*70 + "\n")
            
            fixes_applied = 0
            fixes_attempted = 0
            
            # Group errors by file for efficient processing
            errors_by_file = defaultdict(list)
            for error in all_errors:
                file_path = error.get('file', 'unknown')
                errors_by_file[file_path].append(error)
            
            # Process each file
            for file_path, file_errors in errors_by_file.items():
                print(f"📄 Processing {file_path} ({len(file_errors)} errors)...")
                fixes_attempted += len(file_errors)
                
                # Verify file exists before processing
                file_full_path = project_dir / file_path
                if not file_full_path.exists():
                    print(f"   ⚠️  File not found: {file_path}")
                    print(f"   Full path checked: {file_full_path}")
                    continue
                
                # Run QA phase first to identify all issues
                print("   🔍 Running QA analysis...")
                try:
                    qa_result = qa_phase.execute(state, filepath=file_path)
                    
                    if qa_result.success:
                        print("   ✅ QA passed")
                    else:
                        print(f"   ⚠️  QA found issues: {qa_result.message}")
                except Exception as e:
                    print(f"   ❌ QA error: {e}")
                    if config.verbose:
                        import traceback
                        print(traceback.format_exc())
                
                # Run debugging phase for each error  
                for error in file_errors:
                    print(f"   🔧 Fixing: {error['type']} at line {error.get('line', '?')}")
                    
                    # Read the file to get context
                    try:
                        file_full_path = project_dir / file_path
                        with open(file_full_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            file_lines = file_content.splitlines()
                    except Exception as e:
                        print(f"      ❌ Could not read file: {e}")
                        continue
                    
                    # Get context around the error line
                    from pipeline.line_fixer import get_line_context
                    
                    error_line = error.get('line')
                    if error_line:
                        context_list = get_line_context(file_full_path, error_line, context_lines=3)
                        context = '\n'.join(context_list)
                    else:
                        context = "No line number available"
                    
                    # Create detailed issue dict with context
                    issue = {
                        'filepath': file_path,
                        'type': error['type'],
                        'message': error['message'],
                        'line': error_line,
                        'offset': error.get('offset'),
                        'text': error.get('text'),
                        'description': f"{error['type']} at line {error_line}: {error['message']}\n\nContext:\n{context}"
                    }
                    
                    try:
                        debug_result = debug_phase.execute(state, issue=issue)
                        
                        if debug_result.success:
                            print("      ✅ Fixed successfully")
                            fixes_applied += 1
                        else:
                            print(f"      ⚠️  Could not fix: {debug_result.message}")
                            
                            # If the fix failed due to string matching, try a simpler approach
                            if "Original code not found" in debug_result.message and error_line:
                                print("      🔄 Attempting line-based fix...")
                                if attempt_line_based_fix(file_full_path, error_line, error):
                                    print("      ✅ Fixed with line-based approach")
                                    fixes_applied += 1
                                else:
                                    print("      ❌ Line-based fix also failed")
                    except Exception as e:
                        print(f"      ❌ Debug error: {e}")
                        if config.verbose:
                            import traceback
                            print(traceback.format_exc())
                
                print()
            
            # Save state
            state_manager.save(state)
            
            # Summary
            print("="*70)
            print("📊 ITERATION SUMMARY")
            print("="*70)
            print(f"  Errors found: {len(all_errors)}")
            print(f"  Fixes attempted: {fixes_attempted}")
            print(f"  Fixes applied: {fixes_applied}")
            print(f"  Success rate: {fixes_applied}/{fixes_attempted} ({100*fixes_applied//max(fixes_attempted,1)}%)")
            print("="*70 + "\n")
            
            # Check for progress
            if fixes_applied == 0:
                consecutive_no_progress += 1
                print(f"⚠️  No progress made ({consecutive_no_progress}/{max_no_progress})")
                
                if consecutive_no_progress >= max_no_progress:
                    print("\n❌ Unable to make progress after multiple attempts.")
                    print("Some errors may require manual intervention.")
                    return 1
            else:
                consecutive_no_progress = 0
            
            print("🔄 Re-scanning for errors...\n")
            time.sleep(2)  # Brief pause before next iteration
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting debug/QA mode...")
        log_monitor_active = False
        return 0
    finally:
        log_monitor_active = False


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
    parser.add_argument(
        "--follow",
        dest="follow_log",
        metavar="LOGFILE",
        help="Follow a log file for runtime errors (use with --debug-qa)"
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
