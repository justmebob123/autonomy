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
import logging
import signal
import atexit
from pathlib import Path

# Import the pipeline module
from pipeline import PhaseCoordinator, PipelineConfig
from pipeline.error_signature import ErrorSignature, ProgressTracker
from pipeline.progress_display import print_bug_transition, print_progress_stats, print_refining_fix
from pipeline.command_detector import CommandDetector

# Global reference to runtime tester for signal handling
_global_tester = None

def cleanup_handler(signum=None, frame=None):
    """Handle cleanup on exit or interrupt"""
    global _global_tester
    if _global_tester is not None:
        print("\n🛑 Cleaning up processes...")
        try:
            _global_tester.stop()
            print("✅ All processes stopped")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
    
    if signum is not None:
        sys.exit(130)  # Standard exit code for SIGINT

# Register signal handlers
# CRITICAL: Only handle SIGINT (Ctrl+C), not SIGTERM
# SIGTERM might be sent to process groups we're managing
signal.signal(signal.SIGINT, cleanup_handler)
# DO NOT handle SIGTERM - it might come from our own killpg calls
# signal.signal(signal.SIGTERM, cleanup_handler)
atexit.register(cleanup_handler)


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
    
    # Auto-detect command if not provided
    if not hasattr(args, 'test_command') or not args.test_command:
        print("\n🤖 No --command provided, attempting auto-detection...")
        detector = CommandDetector(project_dir)
        detected_command, reason = detector.detect_command()
        
        if detected_command:
            print(f"✅ Auto-detected command: {detected_command}")
            print(f"   Reason: {reason}")
            args.test_command = detected_command
            
            # Show project info
            project_info = detector.get_project_info()
            if project_info.get('config_files'):
                print(f"   Config files found: {', '.join(project_info['config_files'])}")
            if project_info.get('python_files'):
                print(f"   Python files: {len(project_info['python_files'])} found")
        else:
            print(f"⚠️  Could not auto-detect command: {reason}")
            print("   You can specify a command with --command 'your command here'")
            print("   Continuing with static analysis only (no runtime testing).\n")
    
    print("\nThis mode will:")
    print("  • Scan all Python files for syntax and import errors")
    print("  • Use AI pipeline (QA + Debugging) to fix issues")
    print("  • Examine related files and dependencies")
    print("  • Track runtime errors from log files (if --follow specified)")
    print("  • Continue until all errors are resolved")
    
    if hasattr(args, 'follow_log') and args.follow_log:
        print(f"  • Following log file: {args.follow_log}")
    
    if hasattr(args, 'test_command') and args.test_command:
        print(f"  • Running command: {args.test_command}")
    
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
    from pipeline.phases.investigation import InvestigationPhase
    qa_phase = QAPhase(config, client)
    investigation_phase = InvestigationPhase(config, client)
    debug_phase = DebuggingPhase(config, client)
    
    # Pass investigation phase to debugging phase
    debug_phase.phases = {'investigation': investigation_phase}
    
    # Log file monitoring (only if NOT using --command)
    # When using --command, RuntimeTester handles log monitoring
    log_errors = []
    log_monitor_active = False
    
    if hasattr(args, 'follow_log') and args.follow_log and not hasattr(args, 'test_command'):
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
    elif hasattr(args, 'test_command') and args.test_command:
        print(f"📋 Runtime testing mode: Log monitoring will start with program execution\n")
    
    iteration = 0
    consecutive_no_progress = 0
    max_no_progress = 10  # Allow more attempts before giving up
    
    # Initialize runtime tester outside loop so it can be cleaned up on Ctrl-C
    tester = None
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker()
    
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
                                timeout=None,
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
            
            # Phase 3: Runtime errors (handled by RuntimeTester below)
            runtime_errors = []
            # OLD log_errors code removed - RuntimeTester handles runtime errors now

            # Combine all errors
            all_errors = syntax_errors + import_errors + runtime_errors
            
            # Track errors for progress detection
            progress_tracker.add_iteration(all_errors)
            
            # Check for bug transitions
            if iteration > 1:
                transition = progress_tracker.detect_transition()
                if transition:
                    print_bug_transition(transition)
            
            # Display results
            print("="*70)
            print("📊 SCAN RESULTS")
            print("="*70 + "\n")
            
            if not all_errors:
                print("✅ SUCCESS! No syntax or import errors found.")
                
                # If test command is provided, run runtime tests
                if hasattr(args, 'test_command') and args.test_command:
                    print("\n🧪 Phase 3: Running runtime tests...")
                    print(f"   Command: {args.test_command}")
                    print(f"   Log file: {args.follow_log if hasattr(args, 'follow_log') and args.follow_log else 'Not specified'}")
                    
                    if not hasattr(args, 'follow_log') or not args.follow_log:
                        print("\n⚠️  Warning: No log file specified with --follow")
                        print("   Runtime error detection will be limited.")
                    
                    # Import runtime tester
                    from pipeline.runtime_tester import RuntimeTester
                    
                    # Setup runtime tester
                    log_file = Path(args.follow_log) if hasattr(args, 'follow_log') and args.follow_log else project_dir / 'test.log'

                    # Clear the log file to avoid processing stale errors from previous runs
                    if log_file.exists():
                        print(f"   🧹 Clearing log file to avoid stale errors...")
                        try:
                            log_file.write_text('')
                            print(f"   ✅ Log file cleared: {log_file}")
                        except Exception as e:
                            print(f"   ⚠️  Warning: Could not clear log file: {e}")

                    tester = RuntimeTester(
                        command=args.test_command,
                        working_dir=project_dir,
                        log_file=log_file,
                        logger=logging.getLogger(__name__)
                    )
                    
                    # Set global reference for signal handler
                    global _global_tester
                    _global_tester = tester
                    
                    print("\n▶️  Starting program execution...")
                    tester.start()
                    
                    # Monitor for errors (configurable duration, default 5 minutes)
                    test_duration = getattr(args, 'test_duration', 300)  # Default 5 minutes
                    print(f"   Monitoring for runtime errors ({test_duration} seconds)...")
                    start_time = time.time()
                    runtime_errors_found = []
                    
                    while time.time() - start_time < test_duration:
                        errors = tester.get_errors()
                        if errors:
                            runtime_errors_found.extend(errors)
                            break
                        
                        if not tester.is_running():
                            print(f"\n⚠️  Program exited after {int(time.time() - start_time)} seconds")
                            break
                        
                        time.sleep(1)
                    
                    # Stop the tester
                    tester.stop()
                    
                    # Clear global reference (already declared above)
                    _global_tester = None
                    
                    # CRITICAL: Check if program crashed but no errors in log file
                    # This catches initialization crashes before logging starts
                    if not runtime_errors_found and not tester.is_running():
                        exit_code = tester.get_exit_code()
                        if exit_code and exit_code != 0:
                            print(f"\n⚠️  Program exited with code {exit_code} but no errors in log file")
                            print("   Checking stdout/stderr for crash information...")
                            
                            stderr = tester.get_stderr()
                            stdout = tester.get_stdout()
                            
                            # Check stderr for errors
                            if stderr and any('Traceback' in line or 'Error' in line for line in stderr):
                                print(f"\n❌ Found crash in stderr output!")
                                print("\n📋 Program Output (stderr):")
                                for line in stderr[-30:]:  # Last 30 lines
                                    print(f"   {line.rstrip()}")
                                
                                # Force error detection
                                runtime_errors_found.append({
                                    'type': 'stderr_crash',
                                    'line': 'Program crashed during initialization',
                                    'context': stderr[-30:],
                                    'exit_code': exit_code
                                })
                            
                            # Check stdout for errors
                            elif stdout and any('Traceback' in line or 'Error' in line for line in stdout):
                                print(f"\n❌ Found crash in stdout output!")
                                print("\n📋 Program Output (stdout):")
                                for line in stdout[-30:]:  # Last 30 lines
                                    print(f"   {line.rstrip()}")
                                
                                # Force error detection
                                runtime_errors_found.append({
                                    'type': 'stdout_crash',
                                    'line': 'Program crashed during initialization',
                                    'context': stdout[-30:],
                                    'exit_code': exit_code
                                })
                    
                    if runtime_errors_found:
                        print(f"\n❌ Found {len(runtime_errors_found)} runtime error(s)!")
                        print("\n📋 Runtime Errors:")
                        for i, error in enumerate(runtime_errors_found[:5], 1):  # Show first 5
                            print(f"\n{i}. {error['type'].upper()}")
                            if error.get('context'):
                                # Show full traceback
                                print(f"   Traceback ({len(error['context'])} lines):")
                                for ctx_line in error['context']:
                                    print(f"   {ctx_line}")
                            else:
                                print(f"   {error['line']}")
                        
                        # Convert runtime errors to format expected by error processing
                        # Extract file and line info from traceback
                        import re
                        
                        # CRITICAL: Detect environment issues (curses errors)
                        curses_error_count = 0
                        for error in runtime_errors_found:
                            error_msg = error.get('line', '')
                            if 'curses' in error_msg.lower() and ('returned ERR' in error_msg or 'error:' in error_msg.lower()):
                                curses_error_count += 1
                        
                        # If we have multiple curses errors, this is an environment issue
                        if curses_error_count >= 3:
                            print("\n" + "="*70)
                            print("⚠️  ENVIRONMENT ISSUE DETECTED ⚠️")
                            print("="*70)
                            print("\nThe curses UI cannot initialize. This is NOT a code problem.")
                            print("The terminal environment is not suitable for curses.")
                            print("\n🔧 SOLUTIONS:")
                            print("\n1. Run with --no-ui flag (RECOMMENDED):")
                            print("   ./autonomous ../my_project/ --no-ui")
                            print("\n2. Fix terminal environment:")
                            print("   export TERM=xterm-256color")
                            print("\n3. Use screen/tmux:")
                            print("   screen -S test")
                            print("   ./autonomous ../my_project/")
                            print("\n" + "="*70)
                            print("\n⚠️  Skipping code fixes - environment must be fixed first")
                            print("="*70 + "\n")
                            
                            # Skip processing these errors
                            continue
                        
                        for error in runtime_errors_found:
                            error_type = error.get('type', 'error')
                            context = error.get('context', [])
                            
                            # SIMPLE FIX: Just give the AI the ENTIRE error output
                            # Don't try to be clever - let the AI parse it
                            full_error_output = '\n'.join(context) if context else error.get('line', '')
                            
                            # Extract exception type for categorization only
                            actual_exception_type = None
                            for line in reversed(context):
                                line_stripped = line.strip()
                                if line_stripped and ('Error:' in line_stripped or 'Exception:' in line_stripped):
                                    if not line_stripped.startswith('ERROR:') and not line_stripped.startswith('File'):
                                        match = re.match(r'(\w+(?:Error|Exception)):', line_stripped)
                                        if match:
                                            actual_exception_type = match.group(1)
                                        break
                            
                            # Skip ERROR types - they don't have tracebacks
                            # Only process EXCEPTION types which have full context
                            if 'exception' not in error_type.lower() and 'crash' not in error_type.lower():
                                continue
                            
                            # Try to extract file and line from traceback
                            file_path = None
                            line_num = None
                            error_msg = error.get('message', '')  # Define error_msg here
                            
                            # Strategy 1: Look in context for File line
                            for ctx in context:
                                if 'File "' in ctx:
                                    match = re.search(r'File "([^"]+)", line (\d+)', ctx)
                                    if match:
                                        file_path = match.group(1)
                                        line_num = int(match.group(2))
                                        break
                            
                            # Strategy 2: If no file found, grep through project for the error message
                            if not file_path and error_msg:
                                # Extract the actual error message (last line of context or error_msg)
                                search_text = context[-1] if context else error_msg
                                # Remove common prefixes
                                search_text = search_text.replace('ERROR:', '').replace('CRITICAL:', '').strip()
                                
                                # Only search if we have meaningful text (not just "Traceback")
                                if search_text and 'Traceback' not in search_text and len(search_text) > 20:
                                    try:
                                        # Use grep to find the file
                                        import subprocess
                                        result = subprocess.run(
                                            ['grep', '-r', '-l', '--include=*.py', search_text[:100], str(project_dir)],
                                            capture_output=True,
                                            text=True,
                                            timeout=None
                                        )
                                        if result.returncode == 0 and result.stdout.strip():
                                            # Found file(s), use the first one
                                            found_file = result.stdout.strip().split('\n')[0]
                                            file_path = found_file
                                            # Try to find line number
                                            result2 = subprocess.run(
                                                ['grep', '-n', search_text[:100], found_file],
                                                capture_output=True,
                                                text=True,
                                                timeout=None
                                            )
                                            if result2.returncode == 0 and result2.stdout.strip():
                                                line_match = re.match(r'(\d+):', result2.stdout)
                                                if line_match:
                                                    line_num = int(line_match.group(1))
                                    except Exception as e:
                                        if config.verbose:
                                            print(f"  Could not grep for error: {e}")
                            
                            # Use the actual exception type if we found it, otherwise default to RuntimeError
                            final_error_type = actual_exception_type if actual_exception_type else 'RuntimeError'
                            
                            runtime_errors.append({
                                'file': file_path or 'unknown',
                                'type': final_error_type,  # Use actual Python exception type
                                'message': full_error_output,  # ENTIRE error output - let AI parse it
                                'line': line_num,
                                'context': context,
                                'original_type': error_type
                            })
                        
                        # Don't return here - let it fall through to error processing
                        print("\n🔄 Will attempt to fix runtime errors...")
                        # Recalculate all_errors to include runtime errors
                        all_errors = syntax_errors + import_errors + runtime_errors
                        # Don't break - we want to continue to error processing below
                    else:
                        print(f"\n✅ No runtime errors detected in {int(time.time() - start_time)} seconds")
                        
                        # Check if we should extend monitoring or detach
                        success_timeout = getattr(args, 'success_timeout', 999999)  # UNLIMITED by default
                        detach_mode = getattr(args, 'detach', False)
                        
                        if detach_mode:
                            print("\n🎉 All tests passed!")
                            print(f"✅ Program is running successfully")
                            print(f"🔓 Detaching - program will continue running in background")
                            print(f"\nTo stop the program, use: pkill -f '{args.test_command}'")
                            return 0
                        elif success_timeout > test_duration:
                            # Extend monitoring
                            extended_duration = success_timeout - test_duration
                            print(f"\n⏱️  Extending monitoring for {extended_duration} more seconds...")
                            print(f"   (Use --detach to exit immediately on success)")
                            
                            extended_start = time.time()
                            while time.time() - extended_start < extended_duration:
                                errors = tester.get_errors()
                                if errors:
                                    print(f"\n⚠️  Errors appeared during extended monitoring!")
                                    runtime_errors_found.extend(errors)
                                    break
                                
                                if not tester.is_running():
                                    print(f"\n⚠️  Program exited during extended monitoring")
                                    break
                                
                                time.sleep(1)
                            
                            # Stop the tester after extended monitoring
                            tester.stop()
                            
                            if not runtime_errors_found:
                                print("\n🎉 All tests passed!")
                                print(f"✅ Program ran successfully for {int(time.time() - start_time)} seconds")
                                return 0
                            else:
                                # Errors found during extended monitoring - continue to process them
                                print(f"\n🔄 Processing errors found during extended monitoring...")
                                # The error processing logic below will handle these
                        else:
                            print("\n🎉 All tests passed!")
                            return 0
                else:
                    # No test command, just report success
                    if iteration == 1:
                        print("\n🎉 All checks passed! The application is error-free.")
                    else:
                        print(f"\n🎉 All errors resolved after {iteration} iterations!")
                    
                    print("\nYou can now run the application normally.")
                    print("\n💡 Tip: Use --command to run runtime tests automatically")
                    return 0
            
            # Deduplicate errors before processing
            from pipeline.error_dedup import deduplicate_errors, format_deduplicated_summary
            
            print(f"Found {len(all_errors)} total errors:")
            print(f"  • Syntax errors: {len(syntax_errors)}")
            print(f"  • Import errors: {len(import_errors)}")
            print(f"  • Runtime errors: {len(runtime_errors)}")
            print()
            
            # Deduplicate to avoid fixing the same error multiple times
            print("🔄 Deduplicating errors...")
            deduplicated_errors = deduplicate_errors(all_errors)
            print(f"   Reduced to {len(deduplicated_errors)} unique error(s)\n")
            
            if config.verbose:
                print(format_deduplicated_summary(deduplicated_errors))
            print()
            
            # Display detailed errors
            for i, error in enumerate(all_errors[:10], 1):  # Show first 10
                error_type = error.get('type', 'Error')
                error_file = error.get('file', 'unknown')
                
                if error_type == 'RuntimeError':
                    print(f"{i}. {error_type} at {error.get('timestamp', 'unknown time')}")
                    msg = error.get('message', 'Unknown error')
                    # Truncate long messages
                    if len(msg) > 100:
                        print(f"   {msg[:100]}...")
                    else:
                        print(f"   {msg}")
                else:
                    print(f"{i}. {error_type} in {error_file}")
                    if error.get('line'):
                        print(f"   Line {error['line']}: {error.get('message', '')}")
                        if error.get('text'):
                            print(f"   Code: {error['text']}")
                    else:
                        msg = error.get('message', 'Unknown error')[:100]
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
            
            # Track all modified files across all fixes in this iteration
            all_modified_files = set()
            
            # Group deduplicated errors by file
            from pipeline.error_dedup import group_errors_by_file
            errors_by_file = group_errors_by_file(deduplicated_errors)
            
            # Process each file
            for file_path, error_groups in errors_by_file.items():
                # Skip unknown files (runtime errors without file info)
                if file_path == 'unknown' or file_path == 'runtime':
                    print(f"   ⚠️  Skipping {len(error_groups)} error group(s) without file location")
                    print(f"   These errors need manual investigation:")
                    for err_group in error_groups[:3]:
                        print(f"      - {err_group.get('message', 'Unknown')[:80]} ({len(err_group.get('locations', []))} locations)")
                    continue
                
                print(f"📄 Processing {file_path} ({len(error_groups)} error group(s), {sum(len(g.get('locations', [])) for g in error_groups)} total occurrences)...")
                fixes_attempted += sum(len(g.get('locations', [])) for g in error_groups)
                
                # Verify file exists before processing
                # Handle absolute paths
                if Path(file_path).is_absolute():
                    file_full_path = Path(file_path)
                    # Make it relative to project_dir for display
                    try:
                        file_path = str(file_full_path.relative_to(project_dir))
                    except ValueError:
                        # File is outside project dir
                        print(f"   ⚠️  File is outside project directory: {file_path}")
                        continue
                else:
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
                
                # Run debugging phase for each error group
                for error_group in error_groups:
                    num_locations = len(error_group.get("locations", []))
                    print(f"   🔧 Fixing: {error_group['type']} - {error_group['message'][:60]}...")
                    print(f"      📍 {num_locations} occurrence(s) in {file_path}")
                    
                    # Create error signature for this error
                    error_sig = ErrorSignature.from_error_dict(error_group)
                    if error_sig and hasattr(debug_phase, 'pattern_detector'):
                        debug_phase.pattern_detector.set_current_error(error_sig)
                    
                    # Build comprehensive debug context
                    from pipeline.debug_context import build_comprehensive_context, format_context_for_prompt
                    from pipeline.code_search import detect_refactoring_context, format_refactoring_context
                    
                    print("      📊 Gathering debug context...")
                    debug_context = build_comprehensive_context(error_group, project_dir)
                    
                    # Detect if this is part of a refactoring
                    print("      🔍 Checking for refactoring context...")
                    refactoring_context = detect_refactoring_context(error_group, project_dir)
                    
                    if config.verbose:
                        print(f"      - Call chain: {len(debug_context.get('call_chain', []))} frames")
                        print(f"      - Related files: {len(debug_context.get('related_files', {}))}")
                        if debug_context.get('object_type'):
                            print(f"      - Object type: {debug_context['object_type']}")
                        if debug_context.get('class_definition', {}).get('found'):
                            print(f"      - Class found with {len(debug_context['class_definition'].get('methods', []))} methods")
                        if debug_context.get('similar_methods'):
                            print(f"      - Similar methods: {', '.join(debug_context['similar_methods'][:3])}")
                        if refactoring_context['is_refactoring']:
                            print(f"      - ⚠️  Refactoring detected: {refactoring_context['total_occurrences']} total uses across {len(refactoring_context['files_affected'])} files")
                    
                    # Format context for prompt
                    context_text = format_context_for_prompt(debug_context)
                    
                    # Add refactoring context if detected
                    if refactoring_context['is_refactoring']:
                        context_text += "\n" + format_refactoring_context(refactoring_context)
                    
                    # Get local context around error line
                    from pipeline.line_fixer import get_line_context
                    error_line = error_group.get('locations', [{}])[0].get('line')  # Use first location
                    if error_line:
                        try:
                            file_full_path = project_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
                            context_list = get_line_context(file_full_path, error_line, context_lines=5)
                            local_context = '\n'.join(context_list)
                        except:
                            local_context = "Could not read local context"
                    else:
                        local_context = "No line number available"
                    
                    # Create comprehensive issue dict for the error group
                    issue = {
                        'filepath': file_path,
                        'type': error_group['type'],
                        'message': error_group['message'],
                        'line': error_line,
                        'locations': error_group.get('locations', []),  # All locations
                        'offset': error_group.get('locations', [{}])[0].get('offset'),
                        'text': error_group.get('locations', [{}])[0].get('code'),
                        'traceback': error_group.get('context', []),
                        'call_chain': debug_context.get('call_chain', []),
                        'object_type': debug_context.get('object_type'),
                        'missing_attribute': debug_context.get('missing_attribute'),
                        'class_definition': debug_context.get('class_definition', {}),
                        'similar_methods': debug_context.get('similar_methods', []),
                        'related_files': debug_context.get('related_files', {}),
                        'description': f"{error['type']} at line {error_line}: {error.get('message', 'No message')}\n\n## Local Context\n{local_context}\n\n{context_text}\n\n## Analysis Required\nThis is a runtime error that needs debugging. Analyze the full context above."
                    }
                    
                    try:
                        # Use conversation thread method for better context and specialist consultation
                        debug_result = debug_phase.execute_with_conversation_thread(
                            state, 
                            issue=issue,
                            max_attempts=5
                        )
                        
                        # Track modified files from this debug attempt
                        if debug_result.files_modified:
                            all_modified_files.update(debug_result.files_modified)
                        
                        # Check if user intervention is required
                        # AUTONOMOUS: Use AI UserProxy instead of blocking for human input
                        if debug_result.data and debug_result.data.get('requires_user_input'):
                            print("\n" + "="*70)
                            print("🤖 AUTONOMOUS USER PROXY CONSULTATION")
                            print("="*70)
                            print(f"\nThe AI system is stuck - consulting UserProxy specialist...")
                            print(f"Error: {issue.get('message', 'Unknown error')[:100]}")
                            print(f"File: {issue.get('filepath', 'Unknown file')}")
                            print(f"Line: {issue.get('line', 'Unknown line')}")
                            print(f"\nReason: {debug_result.message}")
                            print(f"Intervention count: {debug_result.data.get('intervention_count', 0)}")
                            
                            # Import and create UserProxyAgent
                            from pipeline.user_proxy import UserProxyAgent
                            user_proxy = UserProxyAgent(
                                role_registry=debug_phase.role_registry,
                                prompt_registry=debug_phase.prompt_registry,
                                tool_registry=debug_phase.tool_registry,
                                client=client,
                                config=config,
                                   logger=logging.getLogger(__name__)
                            )
                            
                            # Get guidance from AI specialist
                            guidance_result = user_proxy.get_guidance(
                                error_info={
                                    'type': issue.get('type', 'Unknown'),
                                    'message': issue.get('message', 'Unknown'),
                                    'file': issue.get('filepath', 'Unknown'),
                                    'line': issue.get('line', 'Unknown')
                                },
                                loop_info={
                                    'type': 'multiple_interventions',
                                    'iterations': debug_result.data.get('intervention_count', 0),
                                    'pattern': 'stuck_in_loop'
                                },
                                debugging_history=debug_result.data.get('history', []),
                                context={'issue': issue, 'debug_result': debug_result}
                            )
                            
                            # Apply AI guidance
                            guidance = guidance_result.get('guidance', '')
                            action = guidance_result.get('action', 'continue')
                            
                            print(f"\n📋 UserProxy Guidance: {guidance}")
                            print(f"📋 Recommended Action: {action}")
                            
                            if action == "escalate":
                                print("\n🔼 Escalating to different specialist per AI guidance...")
                                # TODO: Implement specialist escalation
                                # For now, treat as continue with guidance
                            
                            # ALWAYS continue - UserProxy never skips bugs
                            if action in ["continue", "escalate"]:
                                # Add AI guidance to issue and retry
                                issue['user_guidance'] = guidance
                                print(f"\n🔄 Retrying with AI guidance...")
                                
                                # Retry with AI guidance
                                retry_result = debug_phase.execute_with_conversation_thread(
                                    state,
                                    issue=issue,
                                    max_attempts=3
                                )
                                
                                # Track modified files from retry
                                if retry_result.files_modified:
                                    all_modified_files.update(retry_result.files_modified)
                                
                                if retry_result.success:
                                    print("      ✅ Fixed successfully with AI guidance!")
                                    fixes_applied += 1
                                else:
                                    print(f"      ❌ Still failed: {retry_result.message}")

                        elif debug_result.success:
                            print("      ✅ Fixed successfully")
                            fixes_applied += 1
                            
                            # CRITICAL FIX #2: RUNTIME VERIFICATION
                            # Verify the fix actually worked by re-running the program
                            if tester:
                                print("      🧪 Verifying fix with runtime test...")
                                verification = debug_phase._verify_fix_with_runtime_test(
                                    filepath=issue.get('filepath'),
                                    original_error=error_group,
                                    tester=tester
                                )
                                
                                if verification['error_fixed'] and not verification.get('has_cascading_errors'):
                                    print("      ✅ Runtime verification PASSED: Error is fixed")
                                elif verification.get('has_cascading_errors'):
                                    cascading_count = len(verification['cascading_errors'])
                                    print(f"      ⚠️ Runtime verification PARTIAL: Original error fixed but {cascading_count} new error(s) introduced")
                                    for i, error in enumerate(verification['cascading_errors'], 1):
                                        error_msg = error.get('message', '')[:80]
                                        print(f"         {i}. {error.get('type')}: {error_msg}")
                                    print("      🔄 Will fix cascading errors in next iteration...")
                                    # Count as partial success - original error is fixed
                                else:
                                    print("      ❌ Runtime verification FAILED: Error persists")
                                    print("      🔄 Continuing to next iteration...")
                                    fixes_applied -= 1  # Don't count this as a successful fix
                        
                        else:
                            print(f"      ⚠️  Could not fix: {debug_result.message}")
                            
                            # ENHANCED: Check if we should retry with failure analysis
                            if debug_result.data and debug_result.data.get("should_retry"):
                                ai_feedback = debug_result.data.get("ai_feedback")
                                if ai_feedback:
                                    print("      🔄 Retrying with failure analysis...")
                                    try:
                                        retry_result = debug_phase.retry_with_feedback(
                                            state, 
                                            issue, 
                                            ai_feedback
                                        )
                                        
                                        if retry_result.success:
                                            print("      ✅ Retry successful!")
                                            fixes_applied += 1
                                        else:
                                            print(f"      ⚠️  Retry failed: {retry_result.message}")
                                            
                                            # Fall back to line-based fix if available
                                            if "Original code not found" in debug_result.message and error_line:
                                                print("      🔄 Attempting line-based fix...")
                                                if attempt_line_based_fix(file_full_path, error_line, error):
                                                    print("      ✅ Fixed with line-based approach")
                                                    fixes_applied += 1
                                                else:
                                                    print("      ❌ Line-based fix also failed")
                                    except Exception as retry_error:
                                        print(f"      ❌ Retry error: {retry_error}")
                                        if config.verbose:
                                            import traceback
                                            print(traceback.format_exc())
                            
                            # If the fix failed due to string matching, try a simpler approach
                            elif "Original code not found" in debug_result.message and error_line:
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
            
            # STAGE 2: Post-Fix QA Verification
            # Run QA phase on files that were modified to catch any new issues
            if fixes_applied > 0:
                print("\n" + "="*70)
                print("🔍 STAGE 2: POST-FIX QUALITY VERIFICATION")
                print("="*70)
                
                # Get list of modified files from all debug attempts in this iteration
                modified_files = list(all_modified_files)  # Convert set to list
                
                if modified_files:
                    print(f"Verifying {len(modified_files)} modified file(s)...\n")
                    
                    post_fix_issues = []
                    for modified_file in modified_files:
                        print(f"  📄 Checking: {modified_file}")
                        
                        # Read the modified file
                        file_full_path = project_dir / modified_file
                        if not file_full_path.exists():
                            print(f"     ⚠️  File not found, skipping")
                            continue
                        
                        try:
                            # Run QA phase on this file
                            qa_result = qa_phase.execute(state, filepath=modified_file)
                            
                            if qa_result.success:
                                print(f"     ✅ QA passed - no new issues")
                            else:
                                print(f"     ⚠️  QA found issues: {qa_result.message}")
                                # Note: Issues are already added to state by QA phase
                                post_fix_issues.append({
                                    'file': modified_file,
                                    'message': qa_result.message
                                })
                        except Exception as e:
                            print(f"     ❌ QA error: {e}")
                            if config.verbose:
                                import traceback
                                print(traceback.format_exc())
                    
                    if post_fix_issues:
                        print(f"\n⚠️  Post-fix QA found {len(post_fix_issues)} file(s) with new issues")
                        print("   These will be addressed in the next iteration")
                    else:
                        print(f"\n✅ All modified files passed post-fix QA")
                
                print("="*70 + "\n")
            
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
            
            # Show progress statistics
            if iteration > 1:
                stats = progress_tracker.get_stats()
                print_progress_stats(stats)
            
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
            
            # If we fixed runtime errors and have a test command, verify the fix worked
            if fixes_applied > 0 and runtime_errors and hasattr(args, 'test_command') and args.test_command:
                print("\n🔍 Verifying fixes by re-running tests...\n")
                
                # Stop the current test run
                if tester is not None:
                    print("🛑 Stopping current test run...")
                    tester.stop()
                    time.sleep(2)  # Give it time to stop
                
                # Clear the log file
                if log_file and log_file.exists():
                    print(f"🗑️  Clearing log file: {log_file}")
                    log_file.write_text("")
                
                # Restart the test
                print(f"▶️  Restarting test: {args.test_command}\n")
                tester = RuntimeTester(
                    command=args.test_command,
                    working_dir=project_dir,
                    log_file=log_file,
                    logger=logging.getLogger(__name__)
                )
                tester.start()
                
                # Wait a bit for the program to start and potentially hit errors
                print("⏳ Waiting 10 seconds to check if errors recur...")
                time.sleep(10)
                
                # Check if the same errors appear again
                if log_file and log_file.exists():
                    log_content = log_file.read_text()
                    # Simple check: see if the error message appears in the new log
                    error_recurred = False
                    for error in runtime_errors:
                        if error.get('message', '') in log_content:
                            error_recurred = True
                            print(f"⚠️  Error still present: {error.get('message', '')[:100]}")
                            break
                    
                    if not error_recurred:
                        print("✅ Errors appear to be fixed! Continuing monitoring...")
                    else:
                        print("⚠️  Some errors still present, will continue debugging...")
            
            print("\n🔄 Re-scanning for errors...\n")
            time.sleep(2)  # Brief pause before next iteration
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting debug/QA mode...")
        log_monitor_active = False
        
        # Stop runtime tester if it exists
        if tester is not None:
            print("🛑 Stopping runtime tester...")
            tester.stop()
            print("✅ Runtime tester stopped")
        
        # Clear global reference (already declared above)
        _global_tester = None
        
        return 0
    finally:
        log_monitor_active = False
        
        # Ensure tester is stopped in finally block too
        if tester is not None:
            try:
                tester.stop()
            except:
                pass


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
        action="count",
        default=0,
        help="Verbose mode - show prompts and responses (-v=verbose, -vv=very verbose)"
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
    parser.add_argument(
        "--command",
        dest="test_command",
        metavar="COMMAND",
        required=False,
        help="Command to execute for testing (use with --debug-qa). If not provided, will auto-detect from project structure."
    )
    parser.add_argument(
        "--test-duration",
        type=int,
        default=300,
        metavar="SECONDS",
        help="Duration to monitor for runtime errors in seconds (default: 300)"
    )
    parser.add_argument(
        "--success-timeout",
        type=int,
        default=600,
        metavar="SECONDS",
        help="Extended monitoring duration if no errors found (default: 600)"
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        help="Exit after successful run, leaving program running in background"
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
