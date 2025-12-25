import sys
import argparse
import time
from pathlib import Path
import logging
import signal
import atexit

from pipeline.coordinator import Coordinator
from pipeline.state import PipelineState
from pipeline.config import Config
from pipeline.logging_setup import setup_logging, get_logger
from pipeline.runtime_tester import RuntimeTester
from pipeline.phases.debugging import DebuggingPhase
from pipeline.phases.qa import QAPhase
from pipeline.phases.investigation import InvestigationPhase
from pipeline.handlers import ToolCallHandler
from pipeline.error_signature import ErrorSignature, ProgressTracker
from pipeline.progress_display import (
    print_iteration_header,
    print_scan_results,
    print_error_summary,
    print_iteration_summary,
    print_progress_update
)

# Global reference for signal handling
_global_tester = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global _global_tester
    logger = get_logger()
    logger.info("\n\n🛑 Received interrupt signal, cleaning up...")
    
    if _global_tester:
        logger.info("Stopping runtime tester...")
        _global_tester.stop()
    
    logger.info("Exiting...")
    sys.exit(0)

def cleanup():
    """Cleanup function called on exit"""
    global _global_tester
    if _global_tester:
        try:
            _global_tester.stop()
        except:
            pass

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup)


def deduplicate_errors(errors):
    """
    Deduplicate errors by creating unique signatures.
    Groups errors by (type, message, file, line).
    """
    unique_errors = {}
    
    for error in errors:
        sig = ErrorSignature.from_error(error)
        key = sig.get_key()
        
        if key not in unique_errors:
            unique_errors[key] = {
                'signature': sig,
                'error': error,
                'locations': []
            }
        
        # Add location
        unique_errors[key]['locations'].append({
            'file': error.get('filepath'),
            'line': error.get('line'),
            'function': error.get('function'),
            'code': error.get('code')
        })
    
    return list(unique_errors.values())


def group_errors_by_file(errors):
    """Group errors by file for processing"""
    by_file = {}
    for error in errors:
        filepath = error.get('filepath', 'unknown')
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append(error)
    return by_file


def run_debug_qa_mode(args):
    """
    Debug/QA mode: Continuously scan for errors and fix them using AI pipeline.
    
    This mode:
    1. Scans all Python files for syntax and import errors
    2. Optionally monitors runtime errors from log files
    3. Uses AI pipeline (QA + Debugging) to fix issues
    4. Continues until all errors are resolved
    """
    global _global_tester
    
    logger = get_logger()
    project_dir = Path(args.project_dir).resolve()
    
    print("\n" + "="*70)
    print("🔍 DEBUG/QA MODE - Continuous AI-Powered Debugging & QA")
    print("="*70)
    print(f"\nProject: {project_dir}")
    print("\nThis mode will:")
    print("  • Scan all Python files for syntax and import errors")
    print("  • Use AI pipeline (QA + Debugging) to fix issues")
    print("  • Examine related files and dependencies")
    
    if args.follow:
        print(f"  • Track runtime errors from log files (if --follow specified)")
        print(f"  • Following log file: {args.follow}")
    
    print("  • Continue until all errors are resolved")
    print(f"  • {'Following log file: ' + args.follow if args.follow else 'No log file monitoring'}")
    print("\nPress Ctrl+C to exit at any time.\n")
    
    # Initialize config and coordinator
    config = Config()
    config.verbose = args.verbose
    
    # Discover Ollama servers
    print("🔍 Discovering Ollama servers...")
    config.discover_ollama_servers()
    
    # Initialize coordinator
    coordinator = Coordinator(project_dir, config)
    state = PipelineState(project_dir)
    
    # Initialize phases
    qa_phase = QAPhase(project_dir, config)
    debug_phase = DebuggingPhase(project_dir, config)
    investigation_phase = InvestigationPhase(project_dir, config)
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker()
    
    # Runtime testing setup
    tester = None
    if args.command:
        print("📋 Runtime testing mode: Log monitoring will start with program execution\n")
        log_file = Path(args.follow) if args.follow else None
        tester = RuntimeTester(
            command=args.command,
            log_file=log_file,
            project_dir=project_dir
        )
        _global_tester = tester
    
    iteration = 0
    max_iterations = args.max_iterations if hasattr(args, 'max_iterations') else 100
    
    while iteration < max_iterations:
        iteration += 1
        print_iteration_header(iteration)
        
        # Phase 1: Scan for syntax errors
        print("📁 Phase 1: Scanning Python files for syntax errors...")
        syntax_errors = coordinator.scan_syntax_errors()
        print(f"   Found {len(coordinator.python_files)} Python files to check")
        
        # Phase 2: Check imports
        print("\n📦 Phase 2: Checking imports...")
        import_errors = coordinator.check_imports()
        
        # Phase 3: Runtime errors (if monitoring)
        runtime_errors = []
        if tester:
            print("\n🧪 Phase 3: Running runtime tests...")
            print(f"   Command: {args.command}")
            if args.follow:
                print(f"   Log file: {args.follow}")
            
            # Clear log file before starting
            if tester.log_file and tester.log_file.exists():
                print("   🧹 Clearing log file to avoid stale errors...")
                tester.log_file.write_text('')
                print(f"   ✅ Log file cleared: {tester.log_file}")
            
            # Start the program
            print("\n▶️  Starting program execution...")
            tester.start()
            
            # Monitor for errors
            timeout = args.timeout if hasattr(args, 'timeout') else 300
            print(f"   Monitoring for runtime errors ({timeout} seconds)...")
            time.sleep(timeout)
            
            # Get errors
            runtime_errors = tester.get_errors()
            
            if runtime_errors:
                print(f"\n❌ Found {len(runtime_errors)} runtime error(s)!")
                print("\n📋 Runtime Errors:\n")
                for i, error in enumerate(runtime_errors, 1):
                    print(f"{i}. {error.get('type', 'UNKNOWN')}")
                    
                    # Show traceback if available
                    if error.get('traceback'):
                        lines = error['traceback'].split('\n')
                        print(f"   Traceback ({len(lines)} lines):")
                        for line in lines[:10]:  # Show first 10 lines
                            print(f"   {line}")
                        if len(lines) > 10:
                            print(f"   ... ({len(lines) - 10} more lines)")
                    
                    # Show message
                    if error.get('message'):
                        print(f"   {error['message']}")
                    
                    # Show log file
                    if error.get('log_file'):
                        print(f"   Log file: {error['log_file']}")
                    
                    print()
                
                print("🔄 Will attempt to fix runtime errors...")
        
        # Print scan results
        print_scan_results(syntax_errors, import_errors, runtime_errors)
        
        # Combine all errors
        all_errors = syntax_errors + import_errors + runtime_errors
        
        if not all_errors:
            print("\n✅ SUCCESS! No errors found.")
            if tester and tester.is_running():
                print(f"\n✅ Program is running successfully!")
                print(f"   Monitoring will continue...")
                time.sleep(10)  # Wait a bit before next check
                continue
            else:
                print("\n🎉 All errors resolved! Exiting debug mode.")
                break
        
        print(f"Found {len(all_errors)} total errors:")
        print(f"  • Syntax errors: {len(syntax_errors)}")
        print(f"  • Import errors: {len(import_errors)}")
        print(f"  • Runtime errors: {len(runtime_errors)}")
        
        # Deduplicate errors
        print("\n🔄 Deduplicating errors...")
        unique_errors = deduplicate_errors(all_errors)
        print(f"   Reduced to {len(unique_errors)} unique error(s)")
        
        # Print error summary
        print_error_summary(unique_errors)
        
        # Group errors by file
        errors_by_file = {}
        for error_group in unique_errors:
            error = error_group['error']
            filepath = error.get('filepath', 'unknown')
            if filepath not in errors_by_file:
                errors_by_file[filepath] = []
            errors_by_file[filepath].append(error_group)
        
        # Process each file
        print("\n" + "="*70)
        print("🤖 AI PIPELINE - Fixing Errors")
        print("="*70 + "\n")
        
        fixes_attempted = 0
        fixes_applied = 0
        
        # Track all modified files across all fixes
        all_modified_files = set()
        
        for filepath, error_groups in errors_by_file.items():
            total_occurrences = sum(len(g['locations']) for g in error_groups)
            print(f"📄 Processing {filepath} ({len(error_groups)} error group(s), {total_occurrences} total occurrences)...")
            
            # Run QA first
            print("   🔍 Running QA analysis...")
            qa_result = qa_phase.execute(state, filepath=filepath)
            
            if qa_result.success:
                print("   ✅ QA passed")
            else:
                print(f"   ⚠️  QA found issues: {qa_result.message}")
            
            # Fix each error group
            for error_group in error_groups:
                error = error_group['error']
                signature = error_group['signature']
                locations = error_group['locations']
                
                error_msg = error.get('message', '')
                if len(error_msg) > 60:
                    error_msg = error_msg[:60] + "..."
                
                print(f"   🔧 Fixing: {signature.error_type} - {error_msg}")
                print(f"      📍 {len(locations)} occurrence(s) in {filepath}")
                
                fixes_attempted += 1
                
                # Run investigation phase FIRST
                print("      📊 Gathering debug context...")
                
                # Check for refactoring context
                print("      🔍 Checking for refactoring context...")
                refactoring_context = coordinator.get_refactoring_context(filepath)
                if refactoring_context:
                    print(f"      - Call chain: {len(refactoring_context.get('call_chain', []))} frames")
                    print(f"      - Related files: {len(refactoring_context.get('related_files', {}))}")
                
                # Run investigation
                investigation_result = investigation_phase.execute(
                    state,
                    issue=error
                )
                
                # Debug with investigation findings
                debug_result = debug_phase.execute(
                    state,
                    issue=error,
                    investigation_findings=investigation_result.data if investigation_result.success else None,
                    refactoring_context=refactoring_context
                )
                
                # Track modified files from this fix
                if debug_result.files_modified:
                    all_modified_files.update(debug_result.files_modified)
                
                # Check for loop detection requiring user input
                if debug_result.data and debug_result.data.get('requires_user_input'):
                    print("      ⚠️  Loop detected - AI needs guidance")
                    
                    # In autonomous mode, use UserProxy instead of blocking
                    from pipeline.user_proxy import UserProxy
                    
                    print("      🤖 Consulting AI UserProxy for guidance...")
                    user_proxy = UserProxy(
                        role_registry=debug_phase.role_registry,
                        client=debug_phase.client,
                        config=config,
                        logger=logging.getLogger(__name__)
                    )
                    
                    guidance = user_proxy.provide_guidance(
                        error=error,
                        attempts=debug_result.data.get('attempts', []),
                        loop_info=debug_result.data.get('loop_info', {})
                    )
                    
                    if guidance['action'] == 'continue':
                        print(f"      💡 UserProxy guidance: {guidance['guidance']}")
                        print("      🔄 Retrying with AI guidance...")
                        
                        # Retry with guidance
                        retry_result = debug_phase.retry_with_user_guidance(
                            state,
                            error,
                            guidance['guidance'],
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
                    
                    elif guidance['action'] == 'escalate':
                        print("      ⬆️  Escalating to more advanced analysis...")
                        # The guidance will be used in next iteration
                
                elif debug_result.success:
                    print("      ✅ Fixed successfully")
                    fixes_applied += 1
                    
                    # CRITICAL FIX #2: RUNTIME VERIFICATION
                    # Verify the fix actually worked by re-running the program
                    if tester:
                        print("      🧪 Verifying fix with runtime test...")
                        verification = debug_phase._verify_fix_with_runtime_test(
                            filepath=error.get('filepath'),
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
                                    error, 
                                    ai_feedback
                                )
                                
                                if retry_result.success:
                                    print("      ✅ Retry successful!")
                                    fixes_applied += 1
                                else:
                                    print(f"      ❌ Retry failed: {retry_result.message}")
                            except Exception as e:
                                print(f"      ❌ Retry error: {e}")
        
        # Stage 2: Post-fix QA verification
        if all_modified_files:
            print("\n" + "="*70)
            print("🔍 STAGE 2: POST-FIX QUALITY VERIFICATION")
            print("="*70)
            print(f"Verifying {len(all_modified_files)} modified file(s)...\n")
            
            post_fix_issues = []
            
            # Create handler with all modified files tracked
            verbose = getattr(config, 'verbose', 0)
            activity_log = project_dir / 'ai_activity.log'
            handler = ToolCallHandler(
                project_dir, 
                verbose=verbose, 
                activity_log_file=str(activity_log),
                tool_registry=coordinator.tool_registry
            )
            
            # Track files in handler
            handler.files_modified = list(all_modified_files)
            
            for filepath in all_modified_files:
                print(f"  📄 Checking: {filepath}")
                qa_result = qa_phase.execute(state, filepath=filepath)
                
                if not qa_result.success:
                    print(f"     ❌ QA found new issues: {qa_result.message}")
                    post_fix_issues.append({
                        'file': filepath,
                        'issues': qa_result.message
                    })
                else:
                    print("     ✅ QA passed - no new issues")
            
            if post_fix_issues:
                print(f"\n⚠️  Post-fix QA found {len(post_fix_issues)} file(s) with new issues")
                print("   These will be addressed in the next iteration")
            else:
                print("\n✅ All modified files passed post-fix QA")
            print("="*70 + "\n")
        
        # Print iteration summary
        print_iteration_summary(fixes_attempted, fixes_applied)
        
        # Update progress tracker
        current_errors = [eg['signature'] for eg in unique_errors]
        progress = progress_tracker.update(current_errors)
        print_progress_update(progress)
        
        # Check if we should continue
        if fixes_applied == 0 and fixes_attempted > 0:
            print("\n⚠️  No fixes were successfully applied this iteration")
            print("   This might indicate:")
            print("   1. The errors are too complex for the current approach")
            print("   2. The AI needs more context or different strategies")
            print("   3. Manual intervention might be needed")
            print("\n   Continuing to next iteration to try different approaches...")
        
        # Re-run tests to verify fixes
        if tester and fixes_applied > 0:
            print("\n🔍 Verifying fixes by re-running tests...")
            print("\n🛑 Stopping current test run...")
            tester.stop()
            
            # Clear log file
            if tester.log_file and tester.log_file.exists():
                print(f"🗑️  Clearing log file: {tester.log_file}")
                tester.log_file.write_text('')
            
            # Restart
            print(f"▶️  Restarting test: {args.command}\n")
            tester.start()
            
            # Wait to see if errors recur
            wait_time = 10
            print(f"⏳ Waiting {wait_time} seconds to check if errors recur...")
            time.sleep(wait_time)
            
            new_errors = tester.get_errors()
            if not new_errors:
                print("✅ Errors appear to be fixed! Continuing monitoring...")
            else:
                print(f"⚠️  {len(new_errors)} error(s) still present, will address in next iteration")
        
        print("\n🔄 Re-scanning for errors...\n")
        time.sleep(2)
    
    if iteration >= max_iterations:
        print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
        print("   Some errors may still remain")
    
    # Cleanup
    if tester:
        print("\n🛑 Stopping runtime tester...")
        tester.stop()
    
    print("\n✅ Debug/QA mode complete")


def main():
    parser = argparse.ArgumentParser(description="AI-Powered Development Pipeline")
    parser.add_argument("project_dir", help="Project directory to process")
    parser.add_argument("--debug-qa", action="store_true", 
                       help="Run in debug/QA mode (continuous error scanning and fixing)")
    parser.add_argument("--follow", help="Log file to monitor for runtime errors")
    parser.add_argument("--command", help="Command to run for runtime testing")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout for runtime monitoring (seconds)")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                       help="Increase verbosity (-v, -vv)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    if args.debug_qa:
        run_debug_qa_mode(args)
    else:
        # Normal mode
        config = Config()
        config.verbose = args.verbose
        config.discover_ollama_servers()
        
        coordinator = Coordinator(Path(args.project_dir), config)
        state = PipelineState(Path(args.project_dir))
        
        result = coordinator.run(state)
        
        if result.success:
            print("\n✅ Pipeline completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline failed: {result.message}")
            sys.exit(1)


if __name__ == "__main__":
    main()