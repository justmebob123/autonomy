"""
Tool Call Handlers

Executes tool calls and manages side effects (file creation, etc.)
"""

import json
from typing import Dict, List, Callable
from pathlib import Path
from datetime import datetime

from .logging_setup import get_logger
from .utils import validate_python_syntax
from .process_manager import ProcessBaseline, SafeProcessManager, ResourceMonitor
from .failure_analyzer import FailureAnalyzer, ModificationFailure, create_failure_report
from .signature_extractor import SignatureExtractor
from .context_investigator import ContextInvestigator
from .import_analyzer import ImportAnalyzer
from .syntax_validator import SyntaxValidator
from .system_analyzer import SystemAnalyzer


class ToolCallHandler:
    """Handles execution of tool calls from LLM responses"""
    
    def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None, 
                 tool_registry=None, tool_creator=None, tool_validator=None, refactoring_manager=None):
        self.project_dir = Path(project_dir)
        self.logger = get_logger()
        self.verbose = verbose  # 0=normal, 1=verbose, 2=very verbose
        
        # Refactoring manager (shared with refactoring phase)
        self._refactoring_manager = refactoring_manager
        
        # Track results
        self.files_created: List[str] = []
        self.files_modified: List[str] = []
        self.issues: List[Dict] = []
        self.approved: List[str] = []
        self.tasks: List[Dict] = []
        
        # Detailed error info for debugging
        self.errors: List[Dict] = []
        
        # Activity logging
        self.activity_log: List[Dict] = []
        
        # Setup activity log file if specified
        self.activity_log_file = None
        if activity_log_file:
            self.activity_log_file = Path(activity_log_file)
            # Create/clear the log file
            self.activity_log_file.write_text("")
        
        # Process and resource monitoring
        self.process_baseline = ProcessBaseline()
        self.process_manager = SafeProcessManager(self.process_baseline)
        self.resource_monitor = ResourceMonitor()
        
        # Signature extraction for parameter validation
        self.signature_extractor = SignatureExtractor(str(self.project_dir))
        
        # Context investigation for understanding intent
        self.context_investigator = ContextInvestigator(str(self.project_dir))
        
        # Import analysis for proper import placement
        self.import_analyzer = ImportAnalyzer(str(self.project_dir))
        
        # Failure analysis
        self.failure_analyzer = FailureAnalyzer(logger=self.logger)
        self.failures_dir = self.project_dir / "failures"
        self.failures_dir.mkdir(exist_ok=True)
        
        # INTEGRATION: Tool Validator for tracking effectiveness
        # Use shared instance if provided, otherwise create new one
        if tool_validator is None:
            from .tool_validator import ToolValidator
            self.tool_validator = ToolValidator(self.project_dir)
        else:
            self.tool_validator = tool_validator
        
        # INTEGRATION: Tool Creator for dynamic tool creation
        # Use shared instance if provided, otherwise create new one
        if tool_creator is None:
            from .tool_creator import ToolCreator
            self.tool_creator = ToolCreator(self.project_dir)
        else:
            self.tool_creator = tool_creator
        
        # INTEGRATION: Custom Tool Handler for scripts/
        # This feature allows dynamic loading of user-defined custom tools
        # Tools are loaded from scripts/ directory (part of pipeline infrastructure)
        self.custom_tool_handler = None
        try:
            from .custom_tools import CustomToolRegistry, CustomToolHandler
            custom_registry = CustomToolRegistry(str(self.project_dir))
            custom_registry.discover_tools()
            self.custom_tool_handler = CustomToolHandler(
                str(self.project_dir),
                custom_registry,
                self.logger
            )
            tool_count = len(custom_registry.list_tools())
            if tool_count > 0:
                self.logger.info(f"Initialized custom tool handler with {tool_count} tools")
        except Exception as e:
            pass
            # Fail silently - custom tools are optional
            pass
        
        # Tool handlers
        self._handlers: Dict[str, Callable] = {
            "create_python_file": self._handle_create_file,
            "create_file": self._handle_create_file,  # Alias
            "full_file_rewrite": self._handle_create_file,  # Alias for complete file rewrites
            "modify_python_file": self._handle_modify_file,
            "modify_file": self._handle_modify_file,  # Alias
            "report_issue": self._handle_report_issue,
            "approve_code": self._handle_approve_code,
            "mark_task_complete": self._handle_mark_task_complete,
            "create_task_plan": self._handle_create_plan,
            "read_file": self._handle_read_file,
            "search_code": self._handle_search_code,
            "list_directory": self._handle_list_directory,
            "execute_command": self._handle_execute_command,
            # Signature validation tools
            "get_function_signature": self._handle_get_function_signature,
            "validate_function_call": self._handle_validate_function_call,
            # Context investigation tools
            "investigate_parameter_removal": self._handle_investigate_parameter_removal,
            "investigate_data_flow": self._handle_investigate_data_flow,
            "check_config_structure": self._handle_check_config_structure,
            # Import analysis tools
            "analyze_missing_import": self._handle_analyze_missing_import,
            "check_import_scope": self._handle_check_import_scope,
            # Monitoring tools
            "get_memory_profile": self._handle_get_memory_profile,
            "get_cpu_profile": self._handle_get_cpu_profile,
            "inspect_process": self._handle_inspect_process,
            "get_system_resources": self._handle_get_system_resources,
            "show_process_tree": self._handle_show_process_tree,
            # Project planning tools
            "analyze_project_status": self._handle_analyze_project_status,
            "propose_expansion_tasks": self._handle_propose_expansion_tasks,
            "update_architecture": self._handle_update_architecture,
            # System analysis tools
            "analyze_connectivity": self._handle_analyze_connectivity,
            "analyze_integration_depth": self._handle_analyze_integration_depth,
            "trace_variable_flow": self._handle_trace_variable_flow,
            "find_recursive_patterns": self._handle_find_recursive_patterns,
            "assess_code_quality": self._handle_assess_code_quality,
            "get_refactoring_suggestions": self._handle_get_refactoring_suggestions,
            # Analysis tools (native implementations in pipeline/analysis/)
            "analyze_complexity": self._handle_analyze_complexity,
            "detect_dead_code": self._handle_detect_dead_code,
            "find_integration_gaps": self._handle_find_integration_gaps,
            "detect_integration_conflicts": self._handle_detect_integration_conflicts,
            "generate_call_graph": self._handle_generate_call_graph,
            "find_bugs": self._handle_find_bugs,
            "detect_antipatterns": self._handle_detect_antipatterns,
            "analyze_dataflow": self._handle_analyze_dataflow,
            # External analysis scripts (scripts/analysis/ - for comprehensive analysis)
            "deep_analysis": self._handle_deep_analysis,
            "advanced_analysis": self._handle_advanced_analysis,
            "unified_analysis": self._handle_unified_analysis,
            # File update tools
            "append_to_file": self._handle_append_to_file,
            "update_section": self._handle_update_section,
            "insert_after": self._handle_insert_after,
            "insert_before": self._handle_insert_before,
            "replace_between": self._handle_replace_between,
            # Documentation tools
            # Refactoring tools
            "validate_architecture": self._handle_validate_architecture,
            "create_refactoring_task": self._handle_create_refactoring_task,
            "update_refactoring_task": self._handle_update_refactoring_task,
            "list_refactoring_tasks": self._handle_list_refactoring_tasks,
            "get_refactoring_progress": self._handle_get_refactoring_progress,
            "create_issue_report": self._handle_create_issue_report,
            "request_developer_review": self._handle_request_developer_review,
            "detect_duplicate_implementations": self._handle_detect_duplicate_implementations,
            "compare_file_implementations": self._handle_compare_file_implementations,
            "extract_file_features": self._handle_extract_file_features,
            "analyze_architecture_consistency": self._handle_analyze_architecture_consistency,
            "suggest_refactoring_plan": self._handle_suggest_refactoring_plan,
            "merge_file_implementations": self._handle_merge_file_implementations,
            "validate_refactoring": self._handle_validate_refactoring,
            "cleanup_redundant_files": self._handle_cleanup_redundant_files,
            "analyze_documentation_needs": self._handle_analyze_documentation_needs,
            "update_readme_section": self._handle_update_readme_section,
            "add_readme_section": self._handle_add_readme_section,
            "confirm_documentation_current": self._handle_confirm_documentation_current,
            # Validation tools (Phase 1 - Critical)
            "validate_function_calls": self._handle_validate_function_calls,
            "validate_method_existence": self._handle_validate_method_existence,
            # Validation tools (Phase 2 - High Priority)
            "validate_dict_structure": self._handle_validate_dict_structure,
            "validate_type_usage": self._handle_validate_type_usage,
            # Validation tools (Other)
            "validate_attribute_access": self._handle_validate_attribute_access,
            "verify_import_class_match": self._handle_verify_import_class_match,
            "check_abstract_methods": self._handle_check_abstract_methods,
            "verify_tool_handlers": self._handle_verify_tool_handlers,
            "validate_syntax": self._handle_validate_syntax,
            "detect_circular_imports": self._handle_detect_circular_imports,
            "validate_all_imports": self._handle_validate_all_imports,
            "validate_dict_access": self._handle_validate_dict_access,
            "validate_imports_comprehensive": self._handle_validate_imports_comprehensive,
            "fix_html_entities": self._handle_fix_html_entities,
            # File discovery and naming convention tools
            "find_similar_files": self._handle_find_similar_files,
            "validate_filename": self._handle_validate_filename,
            "compare_files": self._handle_compare_files,
            "find_all_conflicts": self._handle_find_all_conflicts,
            "archive_file": self._handle_archive_file,
            "detect_naming_violations": self._handle_detect_naming_violations,
            # File operation tools (CRITICAL - Phase 2)
            "move_file": self._handle_move_file,
            "rename_file": self._handle_rename_file,
            "restructure_directory": self._handle_restructure_directory,
            "analyze_file_placement": self._handle_analyze_file_placement,
            # Import operation tools (CRITICAL - Phase 2)
            "build_import_graph": self._handle_build_import_graph,
            "analyze_import_impact": self._handle_analyze_import_impact,
            # Codebase analysis tools (CRITICAL - Deep Analysis)
            "list_all_source_files": self._handle_list_all_source_files,
            "cross_reference_file": self._handle_cross_reference_file,
            "map_file_relationships": self._handle_map_file_relationships,
            "find_all_related_files": self._handle_find_all_related_files,
            "analyze_file_purpose": self._handle_analyze_file_purpose,
            "compare_multiple_files": self._handle_compare_multiple_files,
            # On-demand analysis tools (NEW - flexible scope)
            "analyze_complexity": self._handle_analyze_complexity_on_demand,
            "analyze_call_graph": self._handle_analyze_call_graph_on_demand,
            "detect_dead_code": self._handle_detect_dead_code_on_demand,
            "find_integration_gaps": self._handle_find_integration_gaps_on_demand,
            "find_integration_conflicts": self._handle_find_integration_conflicts_on_demand,
        }
        
        # Register custom tools from registry (Integration Fix #1)
        if tool_registry:
            tool_registry.set_handler(self)
            self.logger.info(f"Registered {len(tool_registry.tools)} custom tools from ToolRegistry")
        self.syntax_validator = SyntaxValidator(project_root=str(self.project_dir))
        self.system_analyzer = SystemAnalyzer(self.project_dir)

    def reset(self):
        """Reset tracking state"""
        self.files_created = []
        self.files_modified = []
        self.issues = []
        self.approved = []
        self.tasks = []
        self.errors = []
        self.activity_log = []
    
    def _log_tool_activity(self, tool_name: str, args: Dict):
        """Log AI tool activity with formatted output based on verbosity level"""
        import datetime
        
        # Create activity entry
        activity = {
            'timestamp': datetime.datetime.now().isoformat(),
            'tool': tool_name,
            'args': args
        }
        self.activity_log.append(activity)
        
        # Prepare log messages
        console_lines = []
        file_lines = []
        
        # Format output based on tool type and verbosity
        if tool_name in ['modify_python_file', 'modify_file']:
            file_path = args.get('filepath', args.get('file_path', args.get('path', 'unknown')))
            operation = args.get('operation', 'str_replace')
            
            # Normal mode: Just file and operation
            console_lines.append(f"🔧 [AI Activity] Modifying file: {file_path}")
            file_lines.append(f"[{activity['timestamp']}] MODIFY: {file_path} ({operation})")
            
            # Verbose mode: Add operation details
            if self.verbose >= 1:
                console_lines.append(f"   └─ Operation: {operation}")
                
                if operation == 'str_replace':
                    old_str = args.get('old_str', '')
                    new_str = args.get('new_str', '')
                    console_lines.append(f"   └─ Replacing: {old_str[:60]}...")
                    console_lines.append(f"   └─ With: {new_str[:60]}...")
                    file_lines.append(f"     OLD: {old_str[:100]}")
                    file_lines.append(f"     NEW: {new_str[:100]}")
                elif operation == 'insert_after':
                    marker = args.get('marker', '')
                    console_lines.append(f"   └─ Inserting after: {marker[:60]}...")
                    file_lines.append(f"     MARKER: {marker[:100]}")
                elif operation == 'append':
                    console_lines.append(f"   └─ Appending content to end of file")
            
            # Very verbose mode: Full arguments in tree format
            if self.verbose >= 2:
                console_lines.append(f"   └─ Full arguments:")
                for key, value in args.items():
                    if isinstance(value, str):
                        if len(value) > 200:
                            console_lines.append(f"      ├─ {key}: {value[:200]}... ({len(value)} chars)")
                        else:
                            console_lines.append(f"      ├─ {key}: {value}")
                    else:
                        console_lines.append(f"      ├─ {key}: {value}")
                
        elif tool_name == 'read_file':
            file_path = args.get('filepath', args.get('file_path', args.get('path', 'unknown')))
            console_lines.append(f"📖 [AI Activity] Reading file: {file_path}")
            file_lines.append(f"[{activity['timestamp']}] READ: {file_path}")
            
        elif tool_name == 'search_code':
            pattern = args.get('pattern', 'unknown')
            file_pattern = args.get('file_pattern', '*')
            console_lines.append(f"🔍 [AI Activity] Searching code: {pattern}")
            file_lines.append(f"[{activity['timestamp']}] SEARCH: {pattern} in {file_pattern}")
            
            if self.verbose >= 1:
                console_lines.append(f"   └─ Pattern: {pattern}")
                console_lines.append(f"   └─ Files: {file_pattern}")
            
        elif tool_name == 'list_directory':
            directory = args.get('directory', '.')
            console_lines.append(f"📁 [AI Activity] Listing directory: {directory}")
            file_lines.append(f"[{activity['timestamp']}] LIST: {directory}")
            
        elif tool_name == 'create_python_file' or tool_name == 'create_file':
            pass
            # Try multiple parameter names (filepath, file_path, path)
            file_path = args.get('filepath') or args.get('file_path') or args.get('path') or 'unknown'
            console_lines.append(f"✨ [AI Activity] Creating file: {file_path}")
            file_lines.append(f"[{activity['timestamp']}] CREATE: {file_path}")
            
            if self.verbose >= 1:
                content = args.get('content', '')
                if content:
                    console_lines.append(f"   └─ Content length: {len(content)} chars")
            
        else:
            pass
            # Generic logging for other tools
            console_lines.append(f"🤖 [AI Activity] Calling tool: {tool_name}")
            file_lines.append(f"[{activity['timestamp']}] TOOL: {tool_name}")
            
            # Verbose mode: Show key arguments
            if self.verbose >= 1:
                for key, value in args.items():
                    if isinstance(value, str) and len(value) > 100:
                        console_lines.append(f"   └─ {key}: {value[:100]}...")
                    else:
                        console_lines.append(f"   └─ {key}: {value}")
        
        # Output to console
        for line in console_lines:
            self.logger.info(line)
        
        # Output to file if configured
        if self.activity_log_file:
            with open(self.activity_log_file, 'a') as f:
                for line in file_lines:
                    f.write(line + '\n')
                f.write('\n')  # Blank line between entries
    
    def process_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Process a list of tool calls and return results"""
        results = []
        
        for call in tool_calls:
            result = self._execute_tool_call(call)
            results.append(result)
            
            # Track errors
            if not result.get("success"):
                self.errors.append({
                    "tool": result.get("tool"),
                    "error": result.get("error"),
                    "filepath": result.get("filepath"),
                })
        
        return results
    
    def _infer_tool_name_from_args(self, args: Dict) -> str:
        """Infer tool name from arguments when name is empty"""
        
        # Check for create_task_plan (planning phase)
        if 'tasks' in args and isinstance(args.get('tasks'), list):
            return 'create_task_plan'
        
        # Check for report_issue indicators
        if any(key in args for key in ['issue_type', 'description', 'line_number', 'suggested_fix']):
            return 'report_issue'
        
        # Check for approve_code indicators  
        if 'filepath' in args and ('notes' in args or len(args) <= 2):
            return 'approve_code'
        
        # Check for read_file
        if 'filepath' in args and len(args) == 1:
            return 'read_file'
        
        # Default to approve_code to break QA loops
        if 'filepath' in args:
            return 'approve_code'
        
        return 'unknown'
    
    def _execute_tool_call(self, call: Dict) -> Dict:
        """Execute a single tool call"""
        func = call.get("function", {})
        name = func.get("name", "unknown")
        args = func.get("arguments", {})
        
        # Handle empty string names (common AI model error)
        if not name or name.strip() == "":
            pass
            # Try to infer tool name from arguments
            inferred_name = self._infer_tool_name_from_args(args)
            
            self.logger.warning(f"=" * 70)
            self.logger.warning(f"TOOL CALL: Empty tool name - inferring from arguments")
            self.logger.warning(f"=" * 70)
            self.logger.warning(f"Arguments: {json.dumps(args, indent=2)}")
            self.logger.warning(f"Inferred tool name: {inferred_name}")
            self.logger.warning(f"=" * 70)
            
            if inferred_name != "unknown":
                pass
                # Use inferred name and continue execution
                name = inferred_name
                func["name"] = name  # Update the function object
            else:
                pass
                # Could not infer - return error
                self.logger.error(f"Could not infer tool name from arguments")
                return {
                    "tool": "unknown",
                    "success": False,
                    "error": "empty_tool_name",
                    "error_type": "empty_tool_name",
                    "message": "Tool call has empty name field and could not be inferred",
                    "call_structure": call
                }
        
        args = func.get("arguments", {})
        
        # Handle arguments that might be a string (JSON)
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse arguments: {args[:100]}")
                return {
                    "tool": name, 
                    "success": False, 
                    "error": f"Invalid arguments JSON: {e}"
                }
        
        # Log AI activity with details
        self._log_tool_activity(name, args)
        
        # ENHANCED: Detailed tool execution logging
        self.logger.info(f"")
        self.logger.info(f"{'─'*70}")
        self.logger.info(f"🔧 EXECUTING TOOL: {name}")
        self.logger.info(f"{'─'*70}")
        if args:
            pass
            # Show arguments in a readable format
            arg_preview = {}
            for k, v in list(args.items())[:10]:  # Limit to first 10 args
                if isinstance(v, str) and len(v) > 100:
                    arg_preview[k] = f"{v[:100]}... ({len(v)} chars)"
                else:
                    arg_preview[k] = v
            self.logger.info(f"  📋 Arguments:")
            for k, v in arg_preview.items():
                self.logger.info(f"     • {k}: {v}")
            if len(args) > 10:
                self.logger.info(f"     ... and {len(args) - 10} more arguments")
        else:
            self.logger.info(f"  📋 Arguments: None")
        self.logger.debug(f"Executing tool: {name}")
        
        handler = self._handlers.get(name)
        if not handler:
            pass
            # Check if this is a custom tool
            if hasattr(self, 'custom_tool_handler') and self.custom_tool_handler:
                if self.custom_tool_handler.is_custom_tool(name):
                    self.logger.info(f"Executing custom tool: {name}")
                    try:
                        result = self.custom_tool_handler.execute_tool(name, args)
                        return result
                    except Exception as e:
                        self.logger.error(f"Custom tool execution failed: {e}")
                        return {
                            "tool": name,
                            "success": False,
                            "error": str(e),
                            "error_type": "custom_tool_error"
                        }
            
            self.logger.error(f"=" * 70)
            self.logger.error(f"TOOL CALL FAILURE: Unknown tool '{name}'")
            self.logger.error(f"=" * 70)
            self.logger.error(f"Full call structure:")
            self.logger.error(json.dumps(call, indent=2))
            self.logger.error(f"Available tools: {', '.join(sorted(self._handlers.keys()))}")
            self.logger.error(f"Args provided: {list(args.keys())}")
            self.logger.error(f"=" * 70)
            
            # INTEGRATION: Record unknown tool attempt for potential creation
            self.tool_creator.record_unknown_tool(
                tool_name=name,
                context={
                    'phase': 'unknown',
                    'description': f"Attempted to use {name} with args: {list(args.keys())}"
                }
            )
            
            return {
                "tool": name,
                "success": False,
                "error": "unknown_tool",
                "error_type": "unknown_tool",
                "tool_name": name,
                "message": f"Unknown tool: {name}. Available tools: {', '.join(sorted(self._handlers.keys())[:5])}...",
                "args": args,  # Include for context
                "available_tools": list(self._handlers.keys())
            }
        
        try:
            pass
            # INTEGRATION: Record tool usage start time
            import time
            start_time = time.time()
            
            # Execute the tool
            result = handler(args)
            
            # INTEGRATION: Record tool usage metrics
            execution_time = time.time() - start_time
            success = result.get("success", False)
            error_type = result.get("error_type") if not success else None
            
            self.tool_validator.record_tool_usage(
                tool_name=name,
                success=success,
                execution_time=execution_time,
                phase=None,  # Phase context not available here
                error_type=error_type
            )
            
            # ENHANCED: Post-execution logging
            status_icon = "✅" if success else "❌"
            self.logger.info(f"  {status_icon} Result: {'SUCCESS' if success else 'FAILED'}")
            self.logger.info(f"  ⏱️  Execution time: {execution_time:.2f}s")
            if not success:
                error_msg = result.get("error", "Unknown error")
            elif "message" in result:
                msg = result.get("message", "")
                if msg and len(msg) < 200:
                    self.logger.info(f"  💬 Message: {msg}")
            self.logger.info(f"{'─'*70}")
            self.logger.info(f"")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            
            # INTEGRATION: Record tool failure
            self.tool_validator.record_tool_usage(
                tool_name=name,
                success=False,
                execution_time=0.0,
                error_type=type(e).__name__
            )
            
            return {"tool": name, "success": False, "error": str(e)}
    
    def _normalize_filepath(self, filepath: str) -> str:
        """
        Normalize a filepath to be relative to project directory.
        
        Handles:
        - Absolute paths (/foo/bar.py -> foo/bar.py)
        - Windows paths (foo\\bar.py -> foo/bar.py)
        - Relative prefixes (./foo/bar.py -> foo/bar.py)
        - Whitespace
        """
        if not filepath:
            return filepath
        
        # Strip whitespace
        filepath = filepath.strip()
        
        # Convert Windows backslashes to forward slashes
        filepath = filepath.replace('\\', '/')
        
        # Remove leading slashes (absolute path -> relative)
        # This is critical: Path("/project") / "/absolute" = "/absolute"
        # But we want: Path("/project") / "absolute" = "/project/absolute"
        filepath = filepath.lstrip('/')
        
        # Remove ./ prefix
        if filepath.startswith('./'):
            filepath = filepath[2:]
        
        # Remove any double slashes
        while '//' in filepath:
            filepath = filepath.replace('//', '/')
        
        return filepath
    
    def _handle_create_file(self, args: Dict) -> Dict:
        """Handle create_python_file / create_file tool"""
        filepath = args.get("filepath", args.get("path", args.get("file_path", "")))
        code = args.get("code", args.get("content", ""))
        
        if not filepath:
            self.logger.error(f"create_file called with missing filepath. Args: {args.keys()}")
            return {"tool": "create_file", "success": False, "error": "Missing filepath", "args_received": list(args.keys())}
        if not code:
            self.logger.error(f"create_file called with missing code for {filepath}")
            return {"tool": "create_file", "success": False, "error": "Missing code/content", "filepath": filepath}
        
        # CRITICAL: Normalize path to prevent absolute path issues
        original_filepath = filepath
        filepath = self._normalize_filepath(filepath)
        
        if not filepath:
            self.logger.error(f"Path normalization failed: '{original_filepath}' -> empty string")
            return {"tool": "create_file", "success": False, "error": "Invalid filepath after normalization", "original_path": original_filepath}
        
        # OPTIMIZATION: Coding phase should NOT create documentation files
        # Documentation files should only be created by documentation phase
        if filepath.endswith('.md'):
            self.logger.warning(f"    Documentation files should be created by documentation phase")
            return {
                "tool": "create_file",
                "success": False,
                "error": "Coding phase cannot create .md files - use documentation phase instead",
                "filepath": filepath,
                "suggestion": "This file should be created by the documentation phase, not coding phase"
            }
        
        # Validate Python syntax
        # Validate and fix syntax
        is_valid, fixed_code, error_msg = self.syntax_validator.validate_and_fix(code, filepath)
        
        # Use fixed code if it was modified
        if fixed_code != code:
            self.logger.info(f"Applied automatic syntax fixes")
            code = fixed_code
        
        # CRITICAL: Save file even if syntax validation fails
        # This allows the debugging phase to see and fix the file
        syntax_error = None
        if not is_valid:
            self.logger.error(f"Syntax validation failed for {filepath}")
            self.logger.error(error_msg)
            syntax_error = error_msg
        
        # CRITICAL FIX: Auto-create __init__.py files for Python packages
        if filepath.endswith('.py') and '/' in filepath:
            parts = filepath.split('/')
            for i in range(len(parts) - 1):
                init_path = '/'.join(parts[:i+1]) + '/__init__.py'
                init_full_path = self.project_dir / init_path
                
                # Create __init__.py if it doesn't exist
                if not init_full_path.exists():
                    try:
                        init_full_path.parent.mkdir(parents=True, exist_ok=True)
                        init_full_path.write_text("# Auto-generated __init__.py\n")
                        self.logger.info(f"  📦 Auto-created: {init_path}")
                    except Exception as e:
                        pass
        
        # Create directory and file
        full_path = self.project_dir / filepath
        
        try:
            self.logger.debug(f"Creating directory: {full_path.parent}")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug(f"Writing file: {full_path} ({len(code)} bytes)")
            full_path.write_text(code)
            
            self.files_created.append(filepath)
            self.logger.info(f"  📝 Created: {filepath} ({len(code)} bytes)")
            
            # Return success=False if there was a syntax error, but file is saved
            if syntax_error:
                return {
                    "tool": "create_file", 
                    "success": False,
                    "error": f"Syntax error: {syntax_error}",
                    "filepath": filepath, 
                    "size": len(code),
                    "full_path": str(full_path),
                    "file_saved": True,
                    "needs_debugging": True
                }
            
            return {
                "tool": "create_file", 
                "success": True,
                "filepath": filepath, 
                "size": len(code),
                "full_path": str(full_path)
            }
        except PermissionError as e:
            self.logger.error(f"  ✗ Permission denied for {filepath}: {e}")
            self.logger.error(f"     Full path: {full_path}")
            self.logger.error(f"     Project dir: {self.project_dir}")
            return {
                "tool": "create_file", 
                "success": False,
                "error": f"Permission denied: {filepath}", 
                "filepath": filepath,
                "full_path": str(full_path),
                "error_details": str(e)
            }
        except Exception as e:
            self.logger.error(f"  ✗ Failed to write {filepath}: {e}")
            self.logger.error(f"     Full path: {full_path}")
            self.logger.error(f"     Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"     Traceback: {traceback.format_exc()}")
            return {
                "tool": "create_file", 
                "success": False,
                "error": str(e), 
                "filepath": filepath,
                "full_path": str(full_path),
                "error_type": type(e).__name__
            }
    
    def _handle_modify_file(self, args: Dict) -> Dict:
        """Handle modify_python_file / modify_file tool"""
        filepath = args.get("filepath", args.get("path", args.get("file_path", "")))
        original = args.get("original_code", args.get("original", ""))
        new_code = args.get("new_code", args.get("replacement", ""))
        
        if not filepath:
            return {
                "tool": "modify_file", 
                "success": False, 
                "error": "Missing filepath parameter. You must provide the file path to modify.",
                "filepath": None
            }
        if not original:
            return {
                "tool": "modify_file", 
                "success": False, 
                "error": "Missing original_code parameter. You must provide the exact code to find and replace. "
                        "If you cannot provide exact matching code, use full_file_rewrite instead.",
                "filepath": filepath
            }
        if new_code is None:  # Allow empty string for deletions
            return {
                "tool": "modify_file", 
                "success": False, 
                "error": "Missing new_code parameter. You must provide the replacement code.",
                "filepath": filepath
            }
        
        # CRITICAL: Normalize path to prevent absolute path issues
        filepath = self._normalize_filepath(filepath)
        
        if not filepath:
            return {"tool": "modify_file", "success": False, "error": "Invalid filepath after normalization"}
        
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return {
                "tool": "modify_file", 
                "success": False,
                "error": f"File not found: {filepath}",
                "filepath": filepath
            }
        
        content = full_path.read_text()
        
        # Try exact match first
        if original in content:
            new_content = content.replace(original, new_code, 1)
        else:
            pass
            # Try with normalized whitespace (strip leading/trailing, normalize internal)
            original_stripped = original.strip()
            
            # Try to find the code with any indentation
            found = False
            for line_num, line in enumerate(content.split('\n'), 1):
                if line.strip() == original_stripped:
                    pass
                    # Found it! Get the indentation
                    indent = line[:len(line) - len(line.lstrip())]
                    
                    # CRITICAL FIX: Strip existing indentation from new_code before applying detected indentation
                    new_code_lines_raw = new_code.split('\n')
                    
                    # Detect minimum indentation in new_code
                    min_indent = float('inf')
                    for l in new_code_lines_raw:
                        if l.strip():
                            line_indent = len(l) - len(l.lstrip())
                            min_indent = min(min_indent, line_indent)
                    
                    if min_indent == float('inf'):
                        min_indent = 0
                    
                    # Strip minimum indentation, then apply target indentation
                    new_code_lines = []
                    for l in new_code_lines_raw:
                        if l.strip():
                            stripped = l[min_indent:] if len(l) >= min_indent else l.lstrip()
                            new_code_lines.append(indent + stripped)
                        else:
                            new_code_lines.append(l)
                    
                    new_code_indented = '\n'.join(new_code_lines)
                    
                    # Replace the line
                    lines = content.split('\n')
                    lines[line_num - 1] = new_code_indented
                    new_content = '\n'.join(lines)
                    found = True
                    break
            
            if not found:
                pass
                # Try multi-line match with flexible whitespace
                original_lines = [l.strip() for l in original.strip().split('\n') if l.strip()]
                content_lines = content.split('\n')
                
                for i in range(len(content_lines) - len(original_lines) + 1):
                    pass
                    # Check if this is a match
                    match = True
                    for j, orig_line in enumerate(original_lines):
                        if content_lines[i + j].strip() != orig_line:
                            match = False
                            break
                    
                    if match:
                        pass
                        # Found it! Get indentation from first line
                        first_line = content_lines[i]
                        indent = first_line[:len(first_line) - len(first_line.lstrip())]
                        
                        # CRITICAL FIX: Strip existing indentation from new_code before applying detected indentation
                        # The AI often provides code with indentation already, and we were adding MORE on top!
                        new_code_lines_raw = new_code.split('\n')
                        
                        # Detect minimum indentation in new_code (excluding empty lines)
                        min_indent = float('inf')
                        for line in new_code_lines_raw:
                            if line.strip():  # Skip empty lines
                                line_indent = len(line) - len(line.lstrip())
                                min_indent = min(min_indent, line_indent)
                        
                        # If new_code has no indentation, min_indent will be inf
                        if min_indent == float('inf'):
                            min_indent = 0
                        
                        # Strip the minimum indentation from all lines, then apply target indentation
                        new_code_lines = []
                        for line in new_code_lines_raw:
                            if line.strip():  # Non-empty line
                                # Remove min_indent spaces, then add target indent
                                stripped = line[min_indent:] if len(line) >= min_indent else line.lstrip()
                                new_code_lines.append(indent + stripped)
                            else:  # Empty line
                                new_code_lines.append(line)
                        
                        # Replace the lines
                        content_lines[i:i+len(original_lines)] = new_code_lines
                        new_content = '\n'.join(content_lines)
                        found = True
                        break
                
                if not found:
                    pass
                    
                    # ENHANCED: Create failure analysis
                    failure = ModificationFailure(
                        filepath=filepath,
                        original_content=content,
                        modified_content=None,
                        intended_original=original,
                        intended_replacement=new_code,
                        error_message="Original code not found in file"
                    )
                    
                    analysis = self.failure_analyzer.analyze_modification_failure(failure)
                    
                    # Save detailed failure report
                    report_path = create_failure_report(failure, analysis, self.failures_dir)
                    
                    # Try to find similar code
                    similar = self._find_similar_code(content, original)
                    error_msg = "Original code not found in file"
                    if similar:
                        error_msg += f". Did you mean:\n{similar[:200]}"
                    
                    return {
                        "tool": "modify_file", 
                        "success": False,
                        "error": error_msg,
                        "filepath": filepath,
                        "original_code": original,
                        "new_code": new_code,
                        "failure_analysis": analysis,
                        "failure_report": str(report_path),
                        "ai_feedback": analysis["ai_feedback"]
                    }
        
        # Validate Python syntax
        if filepath.endswith('.py'):
            valid, error = validate_python_syntax(new_content)
            if not valid:
                pass
                # ENHANCED: Create failure analysis for syntax errors
                failure = ModificationFailure(
                    filepath=filepath,
                    original_content=content,
                    modified_content=new_content,
                    intended_original=original,
                    intended_replacement=new_code,
                    error_message=f"Modified code has syntax error: {error}"
                )
                
                analysis = self.failure_analyzer.analyze_modification_failure(failure)
                report_path = create_failure_report(failure, analysis, self.failures_dir)
                
                return {
                    "tool": "modify_file", 
                    "success": False,
                    "error": f"Modified code has syntax error: {error}",
                    "filepath": filepath,
                    "error_type": "syntax_error",
                    "failure_analysis": analysis,
                    "failure_report": str(report_path),
                    "ai_feedback": analysis["ai_feedback"]
                }
        
        # Generate and save patch before applying changes
        try:
            from .patch_manager import PatchManager
            patch_manager = PatchManager()
            
            # Create a unified diff patch
            import difflib
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(filepath),
                tofile=str(filepath)
            )
            patch_content = ''.join(diff)
            
            if patch_content:
                pass
                # Save the patch
                from datetime import datetime
                change_num = patch_manager._get_next_change_number()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = full_path.name.replace('.py', '').replace('.', '_')
                patch_filename = f"change_{change_num:04d}_{timestamp}_{filename}.patch"
                patch_path = patch_manager.patches_dir / patch_filename
                patch_path.write_text(patch_content)
                self.logger.info(f"  💾 Saved patch: {patch_filename}")
        except Exception as e:
            pass
        
        # Validate syntax before writing
        is_valid, fixed_content, error_msg = self.syntax_validator.validate_and_fix(new_content, filepath)
        
        # Use fixed content if it was modified
        if fixed_content != new_content:
            self.logger.info(f"Applied automatic syntax fixes")
            new_content = fixed_content
        
        # CRITICAL: Save file even if syntax validation fails
        # This allows the debugging phase to see and fix the file
        syntax_error = None
        if not is_valid:
            self.logger.error(f"Syntax validation failed for modified {filepath}")
            self.logger.error(error_msg)
            syntax_error = error_msg
        
        full_path.write_text(new_content)
        
        # STAGE 1: Immediate Post-Fix Verification
        verification_passed = True
        verification_errors = []
        
        try:
            pass
            # 1. Re-read file to ensure write succeeded
            written_content = full_path.read_text()
            if written_content != new_content:
                verification_errors.append("File content doesn't match what was written")
                verification_passed = False
            
            # 2. Verify syntax is still valid (post-write check)
            if filepath.endswith('.py'):
                valid, error = validate_python_syntax(written_content)
                if not valid:
                    verification_errors.append(f"Syntax error after write: {error}")
                    verification_passed = False
            
            # 3. Verify the change actually occurred - FIXED LOGIC
            # Normalize whitespace for comparison
            original_normalized = ' '.join(original.split())
            new_code_normalized = ' '.join(new_code.split())
            written_normalized = ' '.join(written_content.split())
            
            # Detect if this is a wrapping operation (code is being wrapped, not replaced)
            is_wrapping = (
                original_normalized in new_code_normalized and  # Original is inside new code
                len(new_code_normalized) > len(original_normalized) * 1.3  # New code is significantly larger (30%+)
            )
            
            if is_wrapping:
                pass
                # For wrapping operations (try/except, if/else, etc.)
                # Just verify the new wrapped code was added
                if new_code_normalized not in written_normalized:
                    verification_errors.append("Wrapped code not found in file - wrapping operation may have failed")
                    verification_passed = False
            else:
                pass
                # For replacement operations
                # Verify original was removed AND new was added
                if new_code_normalized not in written_normalized:
                    verification_errors.append("New code not found in file - replacement may have failed")
                    verification_passed = False
                
                # Only check if original was completely replaced (not just wrapped)
                if original_normalized not in new_code_normalized:
                    if original_normalized in written_normalized:
                        verification_errors.append("Original code still present - replacement incomplete")
                        verification_passed = False
            
            # Check if new code is present (with some flexibility for whitespace)
            new_code_stripped = new_code.strip()
            if new_code_stripped and new_code_stripped not in written_content:
                verification_errors.append("New code not found in file - change may have failed")
                verification_passed = False
            
            # 4. Check imports are valid (basic check)
            if filepath.endswith('.py'):
                import ast
                try:
                    tree = ast.parse(written_content)
                    # Extract imports
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                    # Basic validation - just ensure imports parse
                    self.logger.debug(f"    Found {len(imports)} import statements")
                except SyntaxError as e:
                    verification_errors.append(f"Import syntax error: {e}")
                    verification_passed = False
        
        except Exception as e:
            verification_errors.append(f"Verification exception: {e}")
            verification_passed = False
        
        if not verification_passed:
            for err in verification_errors:
                self.logger.warning(f"     - {err}")
            
            # ENHANCED: Create failure analysis for verification failures
            failure = ModificationFailure(
                filepath=filepath,
                original_content=content,
                modified_content=written_content,
                intended_original=original,
                intended_replacement=new_code,
                error_message="Post-fix verification found issues: " + "; ".join(verification_errors),
                patch=patch_content if 'patch_content' in locals() else None
            )
            
            analysis = self.failure_analyzer.analyze_modification_failure(failure)
            report_path = create_failure_report(failure, analysis, self.failures_dir)
            
            # ARCHITECTURAL CHANGE: DO NOT automatically rollback!
            # Instead, return the state and let the AI decide what to do
            self.logger.info(f"  💭 Change has been applied - AI will decide next action")
            
            return {
                "tool": "modify_file",
                "success": True,  # Change WAS applied successfully
                "applied": True,
                "verification_issues": verification_errors,
                "verification_passed": False,
                "modified_content": written_content,
                "original_content": content,
                "patch": patch_content if 'patch_content' in locals() else None,
                "filepath": filepath,
                "needs_ai_decision": True,  # Signal that AI should decide next action
                "failure_analysis": analysis,
                "failure_report": str(report_path),
                "ai_feedback": analysis["ai_feedback"],
                "rollback_available": bool(patch_content and 'patch_path' in locals())
            }
        
        self.files_modified.append(filepath)
        self.logger.info(f"  ✏️ Modified: {filepath}")
        
        # Return success=False if there was a syntax error, but file is saved
        if syntax_error:
            return {
                "tool": "modify_file", 
                "success": False,
                "error": f"Syntax error: {syntax_error}",
                "filepath": filepath, 
                "verified": True,
                "file_saved": True,
                "needs_debugging": True
            }
        
        return {"tool": "modify_file", "success": True, "filepath": filepath, "verified": True}
    
    def _find_similar_code(self, content: str, target: str, threshold: float = 0.6) -> str:
        """Try to find similar code in content"""
        import difflib
        
        target_lines = target.strip().split('\n')
        content_lines = content.split('\n')
        
        # Sliding window search
        best_match = ""
        best_ratio = 0
        
        window_size = len(target_lines)
        for i in range(len(content_lines) - window_size + 1):
            window = '\n'.join(content_lines[i:i + window_size])
            ratio = difflib.SequenceMatcher(None, target, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = window
        
        if best_ratio >= threshold:
            return best_match
        return ""
    
    def _handle_report_issue(self, args: Dict) -> Dict:
        """Handle report_issue tool"""
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path", "")
        
        # Normalize filepath if provided
        if filepath:
            filepath = self._normalize_filepath(filepath)
        
        issue = {
            "filepath": filepath,
            "type": args.get("issue_type", args.get("type")),
            "description": args.get("description"),
            "line": args.get("line_number", args.get("line")),
            "fix": args.get("suggested_fix", args.get("fix"))
        }
        self.issues.append(issue)
        
        
        return {"tool": "report_issue", "success": True, "issue": issue}
    
    def _handle_approve_code(self, args: Dict) -> Dict:
        """Handle approve_code tool"""
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path", "")
        if not filepath:
            return {"tool": "approve_code", "success": False, "error": "Missing filepath"}
        
        # Normalize filepath
        filepath = self._normalize_filepath(filepath)
        
        self.approved.append(filepath)
        return {"tool": "approve_code", "success": True, "filepath": filepath}
    
    def _handle_mark_task_complete(self, args: Dict) -> Dict:
        """Handle mark_task_complete tool - explicitly marks task as complete without changes"""
        reason = args.get("reason", "File is already complete and correct")
        return {
            "tool": "mark_task_complete",
            "success": True,
            "message": reason,
            "no_changes_needed": True
        }
    
    def _handle_create_plan(self, args: Dict) -> Dict:
        """Handle create_task_plan tool"""
        tasks = args.get("tasks", [])
        
        if not tasks:
            return {"tool": "create_task_plan", "success": False, "error": "No tasks provided"}
        
        # Normalize and validate tasks
        normalized_tasks = []
        for task in tasks:
            target_file = task.get("target_file", task.get("file", ""))
            
            # Normalize the target file path
            if target_file:
                target_file = self._normalize_filepath(target_file)
            
            normalized = {
                "description": task.get("description", ""),
                "target_file": target_file,
                "priority": task.get("priority", 5),
                "dependencies": task.get("dependencies", []),
            }
            
            # Skip tasks without description
            if not normalized["description"]:
                continue
            
            # Ensure priority is in valid range
            normalized["priority"] = max(1, min(10, normalized["priority"]))
            
            normalized_tasks.append(normalized)
        
        # Sort by priority
        self.tasks = sorted(normalized_tasks, key=lambda t: t.get("priority", 10))
        
        self.logger.info(f"  📋 Created plan with {len(self.tasks)} tasks:")
        for i, task in enumerate(self.tasks[:5], 1):
            self.logger.info(f"     {i}. [{task['priority']}] {task.get('description', '')[:50]}")
        if len(self.tasks) > 5:
            self.logger.info(f"     ... and {len(self.tasks) - 5} more")
        
        return {"tool": "create_task_plan", "success": True, "task_count": len(self.tasks)}
    
    def _handle_read_file(self, args: Dict) -> Dict:
        """Handle read_file tool - read a file from the project."""
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path", "")
        
        if not filepath:
            return {"tool": "read_file", "success": False, "error": "No filepath provided"}
        
        # Normalize path
        filepath = self._normalize_filepath(filepath)
        full_path = self.project_dir / filepath
        
        try:
            if not full_path.exists():
                return {
                    "tool": "read_file",
                    "success": False,
                    "error": f"File not found: {filepath}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "tool": "read_file",
                "success": True,
                "filepath": filepath,
                "content": content,
                "lines": len(content.split('\n'))
            }
        
        except Exception as e:
            return {
                "tool": "read_file",
                "success": False,
                "error": f"Failed to read file: {e}"
            }
    
    def _handle_search_code(self, args: Dict) -> Dict:
        """Handle search_code tool - search for patterns in the project."""
        pattern = args.get("pattern", "")
        file_pattern = args.get("file_pattern", "*.py")
        
        if not pattern:
            return {"tool": "search_code", "success": False, "error": "No pattern provided"}
        
        try:
            import subprocess
            result = subprocess.run(
                ['grep', '-r', '-n', '-E', pattern, str(self.project_dir), f'--include={file_pattern}'],
                capture_output=True,
                text=True,
                timeout=None  # UNLIMITED
            )
            
            if result.returncode == 0:
                matches = result.stdout.strip()
                match_count = len(matches.split('\n')) if matches else 0
                
                return {
                    "tool": "search_code",
                    "success": True,
                    "pattern": pattern,
                    "matches": matches,
                    "match_count": match_count
                }
            else:
                return {
                    "tool": "search_code",
                    "success": True,
                    "pattern": pattern,
                    "matches": "",
                    "match_count": 0
                }
        
        except Exception as e:
            return {
                "tool": "search_code",
                "success": False,
                "error": f"Search failed: {e}"
            }
    
    def _handle_list_directory(self, args: Dict) -> Dict:
        """Handle list_directory tool - list files in a directory."""
        directory = args.get("directory", "")
        
        if not directory:
            directory = "."
        
        # Normalize path
        directory = self._normalize_filepath(directory)
        full_path = self.project_dir / directory
        
        try:
            if not full_path.exists():
                return {
                    "tool": "list_directory",
                    "success": False,
                    "error": f"Directory not found: {directory}"
                }
            
            if not full_path.is_dir():
                return {
                    "tool": "list_directory",
                    "success": False,
                    "error": f"Not a directory: {directory}"
                }
            
            # List files and directories
            items = []
            for item in sorted(full_path.iterdir()):
                item_type = "dir" if item.is_dir() else "file"
                items.append({
                    "name": item.name,
                    "type": item_type,
                    "path": str(item.relative_to(self.project_dir))
                })
            
            return {
                "tool": "list_directory",
                "success": True,
                "directory": directory,
                "items": items,
                "count": len(items)
            }
        
        except Exception as e:
            return {
                "tool": "list_directory",
                "success": False,
                "error": f"Failed to list directory: {e}"
            }
    
    def _handle_execute_command(self, args: Dict) -> Dict:
        """Handle execute_command tool - execute shell commands for analysis."""
        import subprocess
        
        command = args.get("command", "")
        timeout = args.get("timeout", None)  # UNLIMITED by default
        capture_output = args.get("capture_output", True)
        
        if not command:
            return {
                "tool": "execute_command",
                "success": False,
                "error": "No command provided"
            }
        
        try:
            pass
            # Execute command in project directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return {
                "tool": "execute_command",
                "success": result.returncode == 0,
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "output": result.stdout if capture_output else ""
            }
        
        except subprocess.TimeoutExpired:
            return {
                "tool": "execute_command",
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "command": command
            }
        except Exception as e:
            return {
                "tool": "execute_command",
                "success": False,
                "error": f"Failed to execute command: {e}",
                "command": command
            }


    def get_error_summary(self) -> str:
        """Get a summary of all errors for debugging"""
        if not self.errors:
            return ""
        
        lines = ["Errors encountered:"]
        for err in self.errors:
            lines.append(f"  - [{err.get('tool')}] {err.get('filepath', '')}: {err.get('error', '')}")
        return "\n".join(lines)
    
    def get_activity_summary(self) -> str:
        """Get a summary of all AI activities"""
        if not self.activity_log:
            return "No AI activities recorded"
        
        lines = [f"\n📊 AI Activity Summary ({len(self.activity_log)} actions):"]
        lines.append("=" * 60)
        
        # Count by tool type
        tool_counts = {}
        for activity in self.activity_log:
            tool = activity['tool']
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        for tool, count in sorted(tool_counts.items()):
            lines.append(f"  {tool}: {count} call(s)")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    # =========================================================================
    # Resource Monitoring Tool Handlers
    # =========================================================================
    
    def _handle_get_memory_profile(self, args: Dict) -> Dict:
        """Handle get_memory_profile tool"""
        pid = args.get("pid")
        include_children = args.get("include_children", False)
        
        try:
            profile = self.resource_monitor.get_memory_profile(pid, include_children)
            return {
                "tool": "get_memory_profile",
                "success": True,
                "profile": profile
            }
        except Exception as e:
            return {
                "tool": "get_memory_profile",
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_cpu_profile(self, args: Dict) -> Dict:
        """Handle get_cpu_profile tool"""
        pid = args.get("pid")
        duration = args.get("duration", 1.0)
        
        try:
            profile = self.resource_monitor.get_cpu_profile(pid, duration)
            return {
                "tool": "get_cpu_profile",
                "success": True,
                "profile": profile
            }
        except Exception as e:
            return {
                "tool": "get_cpu_profile",
                "success": False,
                "error": str(e)
            }
    
    def _handle_inspect_process(self, args: Dict) -> Dict:
        """Handle inspect_process tool"""
        pid = args.get("pid")
        
        if not pid:
            return {
                "tool": "inspect_process",
                "success": False,
                "error": "Missing required parameter: pid"
            }
        
        try:
            info = self.process_baseline.get_process_info(pid)
            if info:
                return {
                    "tool": "inspect_process",
                    "success": True,
                    "process": {
                        "pid": info.pid,
                        "ppid": info.ppid,
                        "pgid": info.pgid,
                        "name": info.name,
                        "cmdline": " ".join(info.cmdline),
                        "memory_mb": round(info.memory_mb, 2),
                        "cpu_percent": round(info.cpu_percent, 2),
                        "is_spawned": self.process_baseline.is_spawned(pid),
                        "is_protected": self.process_baseline.is_protected(pid)
                    }
                }
            else:
                return {
                    "tool": "inspect_process",
                    "success": False,
                    "error": f"Process {pid} not found or not accessible"
                }
        except Exception as e:
            return {
                "tool": "inspect_process",
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_system_resources(self, args: Dict) -> Dict:
        """Handle get_system_resources tool"""
        metrics = args.get("metrics", ["cpu", "memory", "disk"])
        
        try:
            resources = self.resource_monitor.get_system_resources(metrics)
            return {
                "tool": "get_system_resources",
                "success": True,
                "resources": resources
            }
        except Exception as e:
            return {
                "tool": "get_system_resources",
                "success": False,
                "error": str(e)
            }
    
    def _handle_show_process_tree(self, args: Dict) -> Dict:
        """Handle show_process_tree tool"""
        root_pid = args.get("root_pid")
        depth = args.get("depth", 3)
        
        try:
            tree = self.process_manager.show_process_tree(root_pid, depth)
            return {
                "tool": "show_process_tree",
                "success": True,
                "tree": tree,
                "own_pid": self.process_baseline.own_pid,
                "own_pgid": self.process_baseline.own_pgid
            }
        except Exception as e:
            return {
                "tool": "show_process_tree",
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_function_signature(self, args: Dict) -> Dict:
        """
        Handle get_function_signature tool.
        
        Extracts function signature to verify what parameters it accepts.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        function_name = args.get("function_name")
        class_name = args.get("class_name")
        
        if not filepath or not function_name:
            return {
                "tool": "get_function_signature",
                "success": False,
                "error": "Missing required arguments: filepath and function_name"
            }
        
        try:
            signature = self.signature_extractor.extract_function_signature(
                filepath, function_name, class_name
            )
            
            if not signature:
                return {
                    "tool": "get_function_signature",
                    "success": False,
                    "error": f"Function {function_name} not found in {filepath}"
                }
            
            if "error" in signature:
                return {
                    "tool": "get_function_signature",
                    "success": False,
                    "error": signature["error"]
                }
            
            # Format signature for readability
            formatted = self.signature_extractor.format_signature(signature)
            
            return {
                "tool": "get_function_signature",
                "success": True,
                "signature": signature,
                "formatted": formatted,
                "filepath": filepath,
                "function_name": function_name,
                "class_name": class_name
            }
            
        except Exception as e:
            return {
                "tool": "get_function_signature",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_function_call(self, args: Dict) -> Dict:
        """
        Handle validate_function_call tool.
        
        Validates that a function call uses valid parameters before making the call.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        function_name = args.get("function_name")
        call_kwargs = args.get("call_kwargs", {})
        class_name = args.get("class_name")
        
        if not filepath or not function_name:
            return {
                "tool": "validate_function_call",
                "success": False,
                "error": "Missing required arguments: filepath and function_name"
            }
        
        try:
            validation = self.signature_extractor.validate_function_call(
                filepath, function_name, call_kwargs, class_name
            )
            
            if validation["valid"]:
                return {
                    "tool": "validate_function_call",
                    "success": True,
                    "valid": True,
                    "message": "All parameters are valid",
                    "signature": validation["signature"]
                }
            else:
                pass
                # Invalid parameters found
                invalid = validation.get("invalid_parameters", [])
                valid = validation.get("valid_parameters", [])
                
                return {
                    "tool": "validate_function_call",
                    "success": True,  # Tool executed successfully
                    "valid": False,   # But validation failed
                    "invalid_parameters": invalid,
                    "valid_parameters": valid,
                    "has_kwargs": validation.get("has_kwargs", False),
                    "error": f"Invalid parameters: {', '.join(invalid)}",
                    "suggestion": f"Valid parameters are: {', '.join(valid)}",
                    "signature": validation.get("signature")
                }
                
        except Exception as e:
            return {
                "tool": "validate_function_call",
                "success": False,
                "error": str(e)
            }
    
    def _handle_investigate_parameter_removal(self, args: Dict) -> Dict:
        """
        Handle investigate_parameter_removal tool.
        
        CRITICAL: Use this BEFORE removing parameters from function calls.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        function_name = args.get("function_name")
        parameter_name = args.get("parameter_name")
        class_name = args.get("class_name")
        
        if not filepath or not function_name or not parameter_name:
            return {
                "tool": "investigate_parameter_removal",
                "success": False,
                "error": "Missing required arguments: filepath, function_name, parameter_name"
            }
        
        try:
            investigation = self.context_investigator.investigate_parameter_removal(
                filepath, function_name, parameter_name, class_name
            )
            
            if "error" in investigation:
                return {
                    "tool": "investigate_parameter_removal",
                    "success": False,
                    "error": investigation["error"]
                }
            
            return {
                "tool": "investigate_parameter_removal",
                "success": True,
                **investigation
            }
            
        except Exception as e:
            return {
                "tool": "investigate_parameter_removal",
                "success": False,
                "error": str(e)
            }
    
    def _handle_investigate_data_flow(self, args: Dict) -> Dict:
        """
        Handle investigate_data_flow tool.
        
        Traces where data comes from and where it goes.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        variable_name = args.get("variable_name")
        line_number = args.get("line_number")
        
        if not filepath or not variable_name:
            return {
                "tool": "investigate_data_flow",
                "success": False,
                "error": "Missing required arguments: filepath, variable_name"
            }
        
        try:
            investigation = self.context_investigator.investigate_data_flow(
                filepath, variable_name, line_number or 0
            )
            
            if "error" in investigation:
                return {
                    "tool": "investigate_data_flow",
                    "success": False,
                    "error": investigation["error"]
                }
            
            return {
                "tool": "investigate_data_flow",
                "success": True,
                **investigation
            }
            
        except Exception as e:
            return {
                "tool": "investigate_data_flow",
                "success": False,
                "error": str(e)
            }
    
    def _handle_check_config_structure(self, args: Dict) -> Dict:
        """
        Handle check_config_structure tool.
        
        Checks if configuration file has expected structure.
        """
        config_file = args.get("config_file")
        expected_keys = args.get("expected_keys", [])
        
        if not config_file:
            return {
                "tool": "check_config_structure",
                "success": False,
                "error": "Missing required argument: config_file"
            }
        
        try:
            investigation = self.context_investigator.check_configuration_structure(
                config_file, expected_keys
            )
            
            if "error" in investigation:
                return {
                    "tool": "check_config_structure",
                    "success": False,
                    "error": investigation["error"]
                }
            
            return {
                "tool": "check_config_structure",
                "success": True,
                **investigation
            }
            
        except Exception as e:
            return {
                "tool": "check_config_structure",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_missing_import(self, args: Dict) -> Dict:
        """
        Handle analyze_missing_import tool.
        
        Analyzes where an import should be added.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        module_name = args.get("module_name")
        usage_line = args.get("usage_line", 0)
        
        if not filepath or not module_name:
            return {
                "tool": "analyze_missing_import",
                "success": False,
                "error": "Missing required arguments: filepath, module_name"
            }
        
        try:
            analysis = self.import_analyzer.analyze_missing_import(
                filepath, module_name, usage_line
            )
            
            if "error" in analysis:
                return {
                    "tool": "analyze_missing_import",
                    "success": False,
                    "error": analysis["error"]
                }
            
            return {
                "tool": "analyze_missing_import",
                "success": True,
                **analysis
            }
            
        except Exception as e:
            return {
                "tool": "analyze_missing_import",
                "success": False,
                "error": str(e)
            }
    
    def _handle_check_import_scope(self, args: Dict) -> Dict:
        """
        Handle check_import_scope tool.
        
        Checks if an import is in the correct scope.
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get("filepath") or args.get("file_path")
        import_statement = args.get("import_statement")
        line_number = args.get("line_number", 0)
        
        if not filepath or not import_statement:
            return {
                "tool": "check_import_scope",
                "success": False,
                "error": "Missing required arguments: filepath, import_statement"
            }
        
        try:
            analysis = self.import_analyzer.check_import_scope(
                filepath, import_statement, line_number
            )
            
            if "error" in analysis:
                return {
                    "tool": "check_import_scope",
                    "success": False,
                    "error": analysis["error"]
                }
            
            return {
                "tool": "check_import_scope",
                "success": True,
                **analysis
            }
            
        except Exception as e:
            return {
                "tool": "check_import_scope",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_project_status(self, args: Dict) -> Dict:
        """
        Handle analyze_project_status tool.
        
        Reports on current project status relative to MASTER_PLAN objectives.
        This is informational only - doesn't create tasks.
        """
        objectives_completed = args.get("objectives_completed", [])
        objectives_in_progress = args.get("objectives_in_progress", [])
        objectives_pending = args.get("objectives_pending", [])
        code_quality_notes = args.get("code_quality_notes", "")
        recommended_focus = args.get("recommended_focus", "")
        
        self.logger.info(f"    Completed: {len(objectives_completed)} objectives")
        self.logger.info(f"    In Progress: {len(objectives_in_progress)} objectives")
        self.logger.info(f"    Pending: {len(objectives_pending)} objectives")
        if recommended_focus:
            self.logger.info(f"    Recommended Focus: {recommended_focus}")
        
        return {
            "tool": "analyze_project_status",
            "success": True,
            "objectives_completed": objectives_completed,
            "objectives_in_progress": objectives_in_progress,
            "objectives_pending": objectives_pending,
            "code_quality_notes": code_quality_notes,
            "recommended_focus": recommended_focus
        }
    
    def _handle_propose_expansion_tasks(self, args: Dict) -> Dict:
        """
        Handle propose_expansion_tasks tool.
        
        Proposes new tasks for project expansion.
        Stores tasks in self.tasks for the phase to process.
        """
        tasks = args.get("tasks", [])
        expansion_focus = args.get("expansion_focus", "")
        
        if not tasks:
            return {
                "tool": "propose_expansion_tasks",
                "success": False,
                "error": "No tasks provided"
            }
        
        # Validate task structure
        required_fields = ["description", "target_file", "priority", "category", "rationale"]
        for i, task in enumerate(tasks):
            missing = [f for f in required_fields if f not in task]
            if missing:
                return {
                    "tool": "propose_expansion_tasks",
                    "success": False,
                    "error": f"Task {i+1} missing required fields: {missing}"
                }
        
        # Store tasks for phase to process
        self.tasks = tasks
        
        self.logger.info(f"  📝 Proposed {len(tasks)} expansion tasks")
        self.logger.info(f"    Focus: {expansion_focus}")
        for i, task in enumerate(tasks, 1):
            self.logger.info(f"    {i}. {task['description'][:60]}... ({task['target_file']})")
        
        return {
            "tool": "propose_expansion_tasks",
            "success": True,
            "task_count": len(tasks),
            "expansion_focus": expansion_focus,
            "tasks": tasks
        }
    
    def _handle_update_architecture(self, args: Dict) -> Dict:
        """
        Handle update_architecture tool.
        
        Proposes updates to ARCHITECTURE.md based on implementation patterns.
        """
        sections_to_add = args.get("sections_to_add", [])
        sections_to_update = args.get("sections_to_update", [])
        rationale = args.get("rationale", "")
        
        self.logger.info("  📐 Architecture Update Proposed:")
        if sections_to_add:
            self.logger.info(f"    Sections to add: {len(sections_to_add)}")
            for section in sections_to_add:
                self.logger.info(f"      + {section.get('heading', 'Unknown')}")
        if sections_to_update:
            self.logger.info(f"    Sections to update: {len(sections_to_update)}")
            for section in sections_to_update:
                self.logger.info(f"      ~ {section.get('heading', 'Unknown')}")
        
        # For now, just log the proposal
        # In the future, could actually update ARCHITECTURE.md
        
        return {
            "tool": "update_architecture",
            "success": True,
            "sections_to_add": len(sections_to_add),
            "sections_to_update": len(sections_to_update),
            "rationale": rationale
        }

    def _handle_analyze_documentation_needs(self, args: Dict) -> Dict:
        """
        Handle analyze_documentation_needs tool.
        
        Analyzes what documentation needs to be updated based on recent changes.
        """
        readme_needs_update = args.get("readme_needs_update", False)
        architecture_needs_update = args.get("architecture_needs_update", False)
        documentation_quality_notes = args.get("documentation_quality_notes", "")
        new_features_to_document = args.get("new_features_to_document", [])
        readme_sections_outdated = args.get("readme_sections_outdated", [])
        
        self.logger.info("  📝 Documentation Analysis:")
        self.logger.info(f"    README needs update: {readme_needs_update}")
        self.logger.info(f"    ARCHITECTURE needs update: {architecture_needs_update}")
        
        if new_features_to_document:
            self.logger.info(f"    New features to document: {len(new_features_to_document)}")
            for feature in new_features_to_document:
                self.logger.info(f"      • {feature}")
        
        if readme_sections_outdated:
            self.logger.info(f"    Outdated README sections: {', '.join(readme_sections_outdated)}")
        
        if documentation_quality_notes:
            self.logger.info(f"    Quality notes: {documentation_quality_notes}")
        
        return {
            "tool": "analyze_documentation_needs",
            "success": True,
            "readme_needs_update": readme_needs_update,
            "architecture_needs_update": architecture_needs_update,
            "new_features_count": len(new_features_to_document),
            "outdated_sections_count": len(readme_sections_outdated)
        }

    def _handle_update_readme_section(self, args: Dict) -> Dict:
        """
        Handle update_readme_section tool.
        
        Updates a specific section in README.md.
        """
        section_heading = args.get("section_heading", "")
        new_content = args.get("new_content", "")
        action = args.get("action", "replace")  # replace, append, prepend
        
        readme_path = self.project_dir / "README.md"
        
        if not readme_path.exists():
            return {
                "tool": "update_readme_section",
                "success": False,
                "error": "README.md not found"
            }
        
        try:
            pass
            # Read current README
            with open(readme_path, 'r') as f:
                content = f.read()
            
            # Find the section
            import re
            # Match section heading (## or ###)
            pattern = rf'(^#{1,3}\s+{re.escape(section_heading)}.*?)(?=^#{1,3}\s+|\Z)'
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            
            if match:
                old_section = match.group(1)
                # Keep the heading, update the content
                heading_line = old_section.split('\n')[0]
                
                if action == "replace":
                    new_section = f"{heading_line}\n{new_content}\n"
                elif action == "append":
                    new_section = old_section.rstrip() + f"\n{new_content}\n"
                elif action == "prepend":
                    new_section = f"{heading_line}\n{new_content}\n" + '\n'.join(old_section.split('\n')[1:])
                else:
                    new_section = f"{heading_line}\n{new_content}\n"
                
                # Replace the section
                updated_content = content.replace(old_section, new_section)
                
                # Write back
                with open(readme_path, 'w') as f:
                    f.write(updated_content)
                
                self.logger.info(f"  ✏️  Updated README section: {section_heading}")
                self.files_modified.append(str(readme_path))
                
                return {
                    "tool": "update_readme_section",
                    "success": True,
                    "section": section_heading,
                    "action": action
                }
            else:
                return {
                    "tool": "update_readme_section",
                    "success": False,
                    "error": f"Section '{section_heading}' not found in README.md"
                }
        
        except Exception as e:
            self.logger.error(f"Failed to update README section: {e}")
            return {
                "tool": "update_readme_section",
                "success": False,
                "error": str(e)
            }

    def _handle_add_readme_section(self, args: Dict) -> Dict:
        """
        Handle add_readme_section tool.
        
        Adds a new section to README.md.
        """
        section_heading = args.get("section_heading", "")
        content = args.get("content", "")
        position = args.get("position", "end")  # end, after_section, before_section
        reference_section = args.get("reference_section", "")
        
        readme_path = self.project_dir / "README.md"
        
        if not readme_path.exists():
            return {
                "tool": "add_readme_section",
                "success": False,
                "error": "README.md not found"
            }
        
        try:
            pass
            # Read current README
            with open(readme_path, 'r') as f:
                readme_content = f.read()
            
            # Create new section
            new_section = f"\n## {section_heading}\n{content}\n"
            
            if position == "end":
                updated_content = readme_content.rstrip() + new_section
            elif position in ["after_section", "before_section"] and reference_section:
                import re
                pattern = rf'(^#{1,3}\s+{re.escape(reference_section)}.*?)(?=^#{1,3}\s+|\Z)'
                match = re.search(pattern, readme_content, re.MULTILINE | re.DOTALL)
                
                if match:
                    ref_section = match.group(1)
                    if position == "after_section":
                        updated_content = readme_content.replace(ref_section, ref_section + new_section)
                    else:  # before_section
                        updated_content = readme_content.replace(ref_section, new_section + ref_section)
                else:
                    pass
                    # Reference section not found, add at end
                    updated_content = readme_content.rstrip() + new_section
            else:
                updated_content = readme_content.rstrip() + new_section
            
            # Write back
            with open(readme_path, 'w') as f:
                f.write(updated_content)
            
            self.logger.info(f"  ➕ Added README section: {section_heading}")
            self.files_modified.append(str(readme_path))
            
            return {
                "tool": "add_readme_section",
                "success": True,
                "section": section_heading
            }
        
        except Exception as e:
            self.logger.error(f"Failed to add README section: {e}")
            return {
                "tool": "add_readme_section",
                "success": False,
                "error": str(e)
            }

    def _handle_confirm_documentation_current(self, args: Dict) -> Dict:
        """
        Handle confirm_documentation_current tool.
        
        Confirms that documentation is up to date.
        """
        confirmation_notes = args.get("confirmation_notes", "")
        
        if confirmation_notes:
            self.logger.info(f"    Notes: {confirmation_notes}")
        
        return {
            "tool": "confirm_documentation_current",
            "success": True,
            "notes": confirmation_notes
        }

    # ========================================================================
    # SYSTEM ANALYZER HANDLERS
    # ========================================================================
    
    def _handle_analyze_connectivity(self, args: Dict) -> Dict:
        """
        Analyze polytopic connectivity.
        
        Returns connectivity metrics and recommendations.
        """
        try:
            result = self.system_analyzer.analyze_connectivity()
            
            self.logger.info(f"   Connected: {result.get('connected_vertices', 0)}/{result.get('total_vertices', 0)} phases")
            self.logger.info(f"   Edges: {result.get('total_edges', 0)}")
            self.logger.info(f"   Avg Reachability: {result.get('avg_reachability', 0.0):.1f} phases")
            
            if result.get('isolated_phases', []):
                self.logger.warning(f"   Isolated: {', '.join(result.get('isolated_phases', []))}")
            
            return {
                "tool": "analyze_connectivity",
                "success": True,
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Connectivity analysis failed: {e}")
            return {
                "tool": "analyze_connectivity",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_integration_depth(self, args: Dict) -> Dict:
        """
        Analyze integration depth for a phase.
        
        Args:
            phase_name: Name of the phase to analyze
        """
        phase_name = args.get('phase_name', '')
        
        if not phase_name:
            return {
                "tool": "analyze_integration_depth",
                "success": False,
                "error": "Missing phase_name parameter"
            }
        
        try:
            result = self.system_analyzer.analyze_integration_depth(phase_name)
            
            if 'error' not in result:
                self.logger.info(f"🔗 Integration Analysis for {phase_name}:")
                self.logger.info(f"   Total Points: {result.get('total_integration_points', 0)}")
                self.logger.info(f"   Complexity: {result['complexity_level']}")
            
            return {
                "tool": "analyze_integration_depth",
                "success": 'error' not in result,
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Integration analysis failed: {e}")
            return {
                "tool": "analyze_integration_depth",
                "success": False,
                "error": str(e)
            }
    
    def _handle_trace_variable_flow(self, args: Dict) -> Dict:
        """
        Trace variable flow through the system.
        
        Args:
            variable_name: Name of the variable to trace
        """
        variable_name = args.get('variable_name', '')
        
        if not variable_name:
            return {
                "tool": "trace_variable_flow",
                "success": False,
                "error": "Missing variable_name parameter"
            }
        
        try:
            result = self.system_analyzer.trace_variable_flow(variable_name)
            
            if result.get('found', False):
                self.logger.info(f"🌊 Variable Flow for '{variable_name}':")
                self.logger.info(f"   Flows through: {result.get('flows_through', [])} functions")
                self.logger.info(f"   Criticality: {result.get('criticality', 'unknown')}")
            
            return {
                "tool": "trace_variable_flow",
                "success": result.get('found', False),
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Variable flow analysis failed: {e}")
            return {
                "tool": "trace_variable_flow",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_recursive_patterns(self, args: Dict) -> Dict:
        """
        Find recursive and circular call patterns.
        """
        try:
            result = self.system_analyzer.find_recursive_patterns()
            
            self.logger.info(f"🔄 Recursive Pattern Analysis:")
            self.logger.info(f"   Direct recursion: {result.get('total_recursive', 0)} functions")
            self.logger.info(f"   Circular calls: {result.get('total_circular', 0)} functions")
            
            if result.get('warning', None):
                pass
            
            return {
                "tool": "find_recursive_patterns",
                "success": True,
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Recursive pattern analysis failed: {e}")
            return {
                "tool": "find_recursive_patterns",
                "success": False,
                "error": str(e)
            }
    
    def _handle_assess_code_quality(self, args: Dict) -> Dict:
        """
        Assess code quality for a file.
        
        Args:
            filepath: Path to the file to analyze
        """
        # Accept both 'filepath' and 'file_path' for backward compatibility
        filepath = args.get('filepath') or args.get('file_path', '')
        
        if not filepath:
            return {
                "tool": "assess_code_quality",
                "success": False,
                "error": "Missing filepath parameter"
            }
        
        try:
            result = self.system_analyzer.assess_code_quality(filepath)
            
            if 'error' not in result:
                self.logger.info(f"✨ Code Quality for {filepath}:")
                self.logger.info(f"   Quality Score: {result.get('quality_score', 0.0):.1f}/100")
                self.logger.info(f"   Lines: {result.get('lines', 0)}, Functions: {result['functions']}")
                self.logger.info(f"   Comment Ratio: {result.get('comment_ratio', 0.0):.1f}%")
            
            return {
                "tool": "assess_code_quality",
                "success": 'error' not in result,
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Code quality assessment failed: {e}")
            return {
                "tool": "assess_code_quality",
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_refactoring_suggestions(self, args: Dict) -> Dict:
        """
        Get refactoring suggestions for a phase.
        
        Args:
            phase_name: Name of the phase
        """
        phase_name = args.get('phase_name', '')
        
        if not phase_name:
            return {
                "tool": "get_refactoring_suggestions",
                "success": False,
                "error": "Missing phase_name parameter"
            }
        
        try:
            suggestions = self.system_analyzer.get_refactoring_suggestions(phase_name)
            
            self.logger.info(f"💡 Refactoring Suggestions for {phase_name}:")
            for i, suggestion in enumerate(suggestions, 1):
                self.logger.info(f"   {i}. {suggestion}")
            
            return {
                "tool": "get_refactoring_suggestions",
                "success": True,
                "suggestions": suggestions
            }
        
        except Exception as e:
            self.logger.error(f"Refactoring suggestions failed: {e}")
            return {
                "tool": "get_refactoring_suggestions",
                "success": False,
                "error": str(e)
            }

    # =============================================================================
    # Analysis Tools Handlers (scripts/analysis/)
    # =============================================================================
    
    def _handle_analyze_complexity(self, args: Dict) -> Dict:
        """Handle analyze_complexity tool."""
        try:
            from .analysis.complexity import ComplexityAnalyzer
            
            analyzer = ComplexityAnalyzer(str(self.project_dir), self.logger)
            target = args.get('target')
            
            result = analyzer.analyze(target)
            
            # Generate report
            report = analyzer.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "COMPLEXITY_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Total functions: {result.total_functions}")
            self.logger.info(f"   Average complexity: {result.average_complexity:.2f}")
            self.logger.info(f"   Critical functions: {result.critical_count}")
            self.logger.info(f"   Report: COMPLEXITY_REPORT.txt")
            
            return {
                "tool": "analyze_complexity",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "COMPLEXITY_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            return {
                "tool": "analyze_complexity",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_dead_code(self, args: Dict) -> Dict:
        """Handle detect_dead_code tool."""
        try:
            from .analysis.dead_code import DeadCodeDetector
            
            detector = DeadCodeDetector(str(self.project_dir), self.logger)
            target = args.get('target')
            
            result = detector.analyze(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "DEAD_CODE_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Unused functions: {result.total_unused_functions}")
            self.logger.info(f"   Unused methods: {result.total_unused_methods}")
            self.logger.info(f"   Unused imports: {result.total_unused_imports}")
            self.logger.info(f"   Report: DEAD_CODE_REPORT.txt")
            
            return {
                "tool": "detect_dead_code",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "DEAD_CODE_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Dead code detection failed: {e}")
            return {
                "tool": "detect_dead_code",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_integration_gaps(self, args: Dict) -> Dict:
        """Handle find_integration_gaps tool."""
        try:
            from .analysis.integration_gaps import IntegrationGapFinder
            
            finder = IntegrationGapFinder(str(self.project_dir), self.logger)
            target = args.get('target')
            
            result = finder.analyze(target)
            
            # Generate report
            report = finder.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "INTEGRATION_GAP_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Unused classes: {result.total_unused_classes}")
            self.logger.info(f"   Classes with gaps: {result.total_classes_with_gaps}")
            self.logger.info(f"   Report: INTEGRATION_GAP_REPORT.txt")
            
            return {
                "tool": "find_integration_gaps",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "INTEGRATION_GAP_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Integration gap analysis failed: {e}")
            return {
                "tool": "find_integration_gaps",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_integration_conflicts(self, args: Dict) -> Dict:
        """Handle detect_integration_conflicts tool."""
        try:
            from .analysis.integration_conflicts import IntegrationConflictDetector
            
            detector = IntegrationConflictDetector(str(self.project_dir), self.logger)
            target = args.get('target')
            
            result = detector.analyze(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "INTEGRATION_CONFLICT_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Total conflicts: {result.total_conflicts}")
            if result.duplicate_definitions:
                self.logger.info(f"   Duplicate definitions: {len(result.duplicate_definitions)}")
            if result.circular_dependencies:
                self.logger.info(f"   Circular dependencies: {len(result.circular_dependencies)}")
            self.logger.info(f"   Report: INTEGRATION_CONFLICT_REPORT.txt")
            
            return {
                "tool": "detect_integration_conflicts",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "INTEGRATION_CONFLICT_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Integration conflict detection failed: {e}")
            return {
                "tool": "detect_integration_conflicts",
                "success": False,
                "error": str(e)
            }
    
    def _handle_generate_call_graph(self, args: Dict) -> Dict:
        """Handle generate_call_graph tool."""
        try:
            from .analysis.call_graph import CallGraphGenerator
            
            generator = CallGraphGenerator(str(self.project_dir), self.logger)
            target = args.get('target')
            
            result = generator.analyze(target)
            
            # Generate report
            report = generator.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "CALL_GRAPH_REPORT.txt"
            report_file.write_text(report)
            
            # Generate DOT graph
            dot_graph = generator.generate_dot(result)
            dot_file = self.project_dir / "call_graph.dot"
            dot_file.write_text(dot_graph)
            
            self.logger.info(f"   Total functions: {result.total_functions}")
            self.logger.info(f"   Total calls: {result.total_calls}")
            self.logger.info(f"   Report: CALL_GRAPH_REPORT.txt")
            self.logger.info(f"   Graph: call_graph.dot")
            
            return {
                "tool": "generate_call_graph",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "CALL_GRAPH_REPORT.txt",
                "graph_file": "call_graph.dot"
            }
        except Exception as e:
            self.logger.error(f"Call graph generation failed: {e}")
            return {
                "tool": "generate_call_graph",
                "success": False,
                "error": str(e)
            }
    
    def _handle_deep_analysis(self, args: Dict) -> Dict:
        """Handle deep_analysis tool - comprehensive recursive analysis."""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # Get pipeline root
            pipeline_root = Path(__file__).parent.parent
            script_path = pipeline_root / 'scripts' / 'analysis' / 'deep_analysis.py'
            
            target = args.get('target', str(self.project_dir))
            
            
            # Run external script
            result = subprocess.run(
                [sys.executable, str(script_path), target],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                self.logger.info(f"   Report: deep_analysis.txt")
                
                return {
                    "tool": "deep_analysis",
                    "success": True,
                    "output": result.stdout,
                    "report_file": "deep_analysis.txt"
                }
            else:
                return {
                    "tool": "deep_analysis",
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            self.logger.error(f"Deep analysis failed: {e}")
            return {
                "tool": "deep_analysis",
                "success": False,
                "error": str(e)
            }
    
    def _handle_advanced_analysis(self, args: Dict) -> Dict:
        """Handle advanced_analysis tool - advanced pattern detection and analysis."""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # Get pipeline root
            pipeline_root = Path(__file__).parent.parent
            script_path = pipeline_root / 'scripts' / 'analysis' / 'advanced_analysis.py'
            
            target = args.get('target', str(self.project_dir))
            
            
            # Run external script
            result = subprocess.run(
                [sys.executable, str(script_path), target],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                self.logger.info(f"   Report: advanced_analysis.txt")
                
                return {
                    "tool": "advanced_analysis",
                    "success": True,
                    "output": result.stdout,
                    "report_file": "advanced_analysis.txt"
                }
            else:
                return {
                    "tool": "advanced_analysis",
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            self.logger.error(f"Advanced analysis failed: {e}")
            return {
                "tool": "advanced_analysis",
                "success": False,
                "error": str(e)
            }
    
    def _handle_unified_analysis(self, args: Dict) -> Dict:
        """Handle unified_analysis tool - unified analysis with multiple output formats."""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # Get pipeline root
            pipeline_root = Path(__file__).parent.parent
            script_path = pipeline_root / 'scripts' / 'deep_analyze.py'
            
            target = args.get('target', str(self.project_dir))
            checks = args.get('checks', [])
            output_format = args.get('output_format', 'text')
            recursive = args.get('recursive', True)
            
            
            # Build command
            cmd = [sys.executable, str(script_path), target]
            if output_format:
                cmd.extend(['--format', output_format])
            if recursive:
                cmd.append('--recursive')
            for check in checks:
                cmd.extend(['--check', check])
            
            # Run external script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                pass
                
                return {
                    "tool": "unified_analysis",
                    "success": True,
                    "output": result.stdout,
                    "format": output_format
                }
            else:
                return {
                    "tool": "unified_analysis",
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            self.logger.error(f"Unified analysis failed: {e}")
            return {
                "tool": "unified_analysis",
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # File Update Tools Handlers
    # =============================================================================
    
    def _handle_append_to_file(self, args: Dict) -> Dict:
        """Handle append_to_file tool."""
        try:
            from .tool_modules.file_updates import FileUpdateTools
            
            file_tools = FileUpdateTools(str(self.project_dir), self.logger)
            # Accept both 'filepath' and 'file_path' for backward compatibility
            filepath = args.get('filepath') or args.get('file_path')
            content = args.get('content')
            ensure_newline = args.get('ensure_newline', True)
            
            self.logger.info(f"📝 Appending to file: {filepath}")
            result = file_tools.append_to_file(filepath, content, ensure_newline)
            
            if result['success']:
                pass
                # Track as file modification
                if filepath not in self.files_modified:
                    self.files_modified.append(filepath)
            
            return {
                "tool": "append_to_file",
                **result
            }
        except Exception as e:
            self.logger.error(f"Append to file failed: {e}")
            return {
                "tool": "append_to_file",
                "success": False,
                "error": str(e)
            }
    
    def _handle_update_section(self, args: Dict) -> Dict:
        """Handle update_section tool."""
        try:
            from .tool_modules.file_updates import FileUpdateTools
            
            file_tools = FileUpdateTools(str(self.project_dir), self.logger)
            # Accept both 'filepath' and 'file_path' for backward compatibility
            filepath = args.get('filepath') or args.get('file_path')
            section_title = args.get('section_title')
            new_content = args.get('new_content')
            create_if_missing = args.get('create_if_missing', True)
            
            self.logger.info(f"📝 Updating section '{section_title}' in {filepath}")
            result = file_tools.update_section(filepath, section_title, new_content, create_if_missing)
            
            if result['success']:
                pass
                # Track as file modification or creation
                if result.get('created'):
                    if filepath not in self.files_created:
                        self.files_created.append(filepath)
                else:
                    if filepath not in self.files_modified:
                        self.files_modified.append(filepath)
            
            return {
                "tool": "update_section",
                **result
            }
        except Exception as e:
            self.logger.error(f"Update section failed: {e}")
            return {
                "tool": "update_section",
                "success": False,
                "error": str(e)
            }
    
    def _handle_insert_after(self, args: Dict) -> Dict:
        """Handle insert_after tool."""
        try:
            from .tool_modules.file_updates import FileUpdateTools
            
            file_tools = FileUpdateTools(str(self.project_dir), self.logger)
            # Accept both 'filepath' and 'file_path' for backward compatibility
            filepath = args.get('filepath') or args.get('file_path')
            marker = args.get('marker')
            content = args.get('content')
            first_occurrence = args.get('first_occurrence', True)
            
            self.logger.info(f"📝 Inserting content after marker in {filepath}")
            result = file_tools.insert_after(filepath, marker, content, first_occurrence)
            
            if result['success']:
                pass
                # Track as file modification
                if filepath not in self.files_modified:
                    self.files_modified.append(filepath)
            
            return {
                "tool": "insert_after",
                **result
            }
        except Exception as e:
            self.logger.error(f"Insert after failed: {e}")
            return {
                "tool": "insert_after",
                "success": False,
                "error": str(e)
            }
    
    def _handle_insert_before(self, args: Dict) -> Dict:
        """Handle insert_before tool."""
        try:
            from .tool_modules.file_updates import FileUpdateTools
            
            file_tools = FileUpdateTools(str(self.project_dir), self.logger)
            # Accept both 'filepath' and 'file_path' for backward compatibility
            filepath = args.get('filepath') or args.get('file_path')
            marker = args.get('marker')
            content = args.get('content')
            first_occurrence = args.get('first_occurrence', True)
            
            self.logger.info(f"📝 Inserting content before marker in {filepath}")
            result = file_tools.insert_before(filepath, marker, content, first_occurrence)
            
            if result['success']:
                pass
                # Track as file modification
                if filepath not in self.files_modified:
                    self.files_modified.append(filepath)
            
            return {
                "tool": "insert_before",
                **result
            }
        except Exception as e:
            self.logger.error(f"Insert before failed: {e}")
            return {
                "tool": "insert_before",
                "success": False,
                "error": str(e)
            }
    
    def _handle_replace_between(self, args: Dict) -> Dict:
        """Handle replace_between tool."""
        try:
            from .tool_modules.file_updates import FileUpdateTools
            
            file_tools = FileUpdateTools(str(self.project_dir), self.logger)
            # Accept both 'filepath' and 'file_path' for backward compatibility
            filepath = args.get('filepath') or args.get('file_path')
            start_marker = args.get('start_marker')
            end_marker = args.get('end_marker')
            new_content = args.get('new_content')
            include_markers = args.get('include_markers', False)
            
            self.logger.info(f"📝 Replacing content between markers in {filepath}")
            result = file_tools.replace_between(filepath, start_marker, end_marker, new_content, include_markers)
            
            if result['success']:
                pass
                # Track as file modification
                if filepath not in self.files_modified:
                    self.files_modified.append(filepath)
            
            return {
                "tool": "replace_between",
                **result
            }
        except Exception as e:
            self.logger.error(f"Replace between failed: {e}")
            return {
                "tool": "replace_between",
                "success": False,
                "error": str(e)
            }

    def _handle_find_bugs(self, args: Dict) -> Dict:
        """Handle find_bugs tool - native implementation."""
        try:
            from .analysis.bug_detection import BugDetector
            
            detector = BugDetector(str(self.project_dir), self.logger)
            target = args.get('filepath', args.get('target'))
            
            # If target is None or not specified, analyze all files
            if target is None:
                result = detector.analyze_all()
            else:
                result = detector.detect(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "BUG_DETECTION_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Total bugs: {len(result.bugs)}")
            if result.severity_counts:
                for severity, count in result.severity_counts.items():
                    self.logger.info(f"   {severity}: {count}")
            self.logger.info(f"   Report: BUG_DETECTION_REPORT.txt")
            
            return {
                "tool": "find_bugs",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "BUG_DETECTION_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Bug detection failed: {e}")
            return {
                "tool": "find_bugs",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_antipatterns(self, args: Dict) -> Dict:
        """Handle detect_antipatterns tool - native implementation."""
        try:
            from .analysis.antipatterns import AntiPatternDetector
            
            detector = AntiPatternDetector(str(self.project_dir), self.logger)
            target = args.get('filepath', args.get('target'))
            
            # If target is None or not specified, analyze all files
            if target is None:
                result = detector.analyze_all()
            else:
                result = detector.detect(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "ANTIPATTERN_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Total anti-patterns: {len(result.antipatterns)}")
            if result.pattern_counts:
                for pattern, count in result.pattern_counts.items():
                    self.logger.info(f"   {pattern}: {count}")
            self.logger.info(f"   Report: ANTIPATTERN_REPORT.txt")
            
            return {
                "tool": "detect_antipatterns",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "ANTIPATTERN_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Anti-pattern detection failed: {e}")
            return {
                "tool": "detect_antipatterns",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_dataflow(self, args: Dict) -> Dict:
        """Handle analyze_dataflow tool - native implementation."""
        try:
            from .analysis.dataflow import DataFlowAnalyzer
            
            analyzer = DataFlowAnalyzer(str(self.project_dir), self.logger)
            target = args.get('filepath', args.get('target'))
            
            result = analyzer.analyze(target)
            
            # Generate report
            report = analyzer.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "DATAFLOW_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"   Total variables: {len(result.variables)}")
            self.logger.info(f"   Uninitialized: {len(result.uninitialized_vars)}")
            self.logger.info(f"   Unused assignments: {len(result.unused_assignments)}")
            self.logger.info(f"   Report: DATAFLOW_REPORT.txt")
            
            return {
                "tool": "analyze_dataflow",
                "success": True,
                "result": result.to_dict(),
                "report": report,
                "report_file": "DATAFLOW_REPORT.txt"
            }
        except Exception as e:
            self.logger.error(f"Data flow analysis failed: {e}")
            return {
                "tool": "analyze_dataflow",
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # Refactoring Tool Handlers
    # =============================================================================
    
    def _handle_create_refactoring_task(self, args: Dict) -> Dict:
        """Handle create_refactoring_task tool."""
        try:
            from pipeline.state.refactoring_task import (
                RefactoringIssueType,
                RefactoringPriority,
                RefactoringApproach
            )
            
            # Get or create refactoring task manager
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                from pipeline.state.refactoring_task import RefactoringTaskManager
                self._refactoring_manager = RefactoringTaskManager()
            
            # Parse enums
            issue_type = RefactoringIssueType(args['issue_type'])
            priority = RefactoringPriority(args.get('priority', 'medium'))
            fix_approach = RefactoringApproach(args.get('fix_approach', 'autonomous'))
            
            # Create task
            task = self._refactoring_manager.create_task(
                issue_type=issue_type,
                title=args['title'],
                description=args['description'],
                target_files=args['target_files'],
                priority=priority,
                fix_approach=fix_approach
            )
            
            
            return {
                "tool": "create_refactoring_task",
                "success": True,
                "task_id": task.task_id,
                "task": task.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create refactoring task: {e}")
            return {
                "tool": "create_refactoring_task",
                "success": False,
                "error": str(e)
            }
    
    def _handle_update_refactoring_task(self, args: Dict) -> Dict:
        """Handle update_refactoring_task tool."""
        try:
            from pipeline.state.manager import TaskStatus
            
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                return {
                    "tool": "update_refactoring_task",
                    "success": False,
                    "error": "No refactoring tasks exist"
                }
            
            task_id = args['task_id']
            task = self._refactoring_manager.get_task(task_id)
            
            if not task:
                return {
                    "tool": "update_refactoring_task",
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # Update status if provided
            if 'status' in args:
                status = TaskStatus(args['status'])
                task.status = status
                
                if status == TaskStatus.COMPLETED and 'fix_details' in args:
                    task.complete(args['fix_details'])
                elif status == TaskStatus.FAILED and 'error_message' in args:
                    task.fail(args['error_message'])
            
            # Update other fields
            if 'priority' in args:
                from pipeline.state.refactoring_task import RefactoringPriority
                task.priority = RefactoringPriority(args['priority'])
            
            if 'fix_details' in args:
                task.fix_details = args['fix_details']
            
            if 'error_message' in args:
                task.error_message = args['error_message']
            
            
            return {
                "tool": "update_refactoring_task",
                "success": True,
                "task_id": task_id,
                "task": task.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update refactoring task: {e}")
            return {
                "tool": "update_refactoring_task",
                "success": False,
                "error": str(e)
            }
    
    def _handle_list_refactoring_tasks(self, args: Dict) -> Dict:
        """Handle list_refactoring_tasks tool."""
        try:
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                return {
                    "tool": "list_refactoring_tasks",
                    "success": True,
                    "tasks": [],
                    "count": 0
                }
            
            # Get tasks based on filters
            if 'status' in args:
                if args['status'] == 'pending':
                    tasks = self._refactoring_manager.get_pending_tasks()
                else:
                    from pipeline.state.manager import TaskStatus
                    status = TaskStatus(args['status'])
                    tasks = self._refactoring_manager.get_tasks_by_status(status)
            elif 'priority' in args:
                from pipeline.state.refactoring_task import RefactoringPriority
                priority = RefactoringPriority(args['priority'])
                tasks = self._refactoring_manager.get_tasks_by_priority(priority)
            elif 'issue_type' in args:
                from pipeline.state.refactoring_task import RefactoringIssueType
                issue_type = RefactoringIssueType(args['issue_type'])
                tasks = self._refactoring_manager.get_tasks_by_type(issue_type)
            else:
                tasks = list(self._refactoring_manager.tasks.values())
            
            self.logger.info(f"  📋 Found {len(tasks)} refactoring tasks")
            
            return {
                "tool": "list_refactoring_tasks",
                "success": True,
                "tasks": [task.to_dict() for task in tasks],
                "count": len(tasks)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to list refactoring tasks: {e}")
            return {
                "tool": "list_refactoring_tasks",
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_refactoring_progress(self, args: Dict) -> Dict:
        """Handle get_refactoring_progress tool."""
        try:
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                return {
                    "tool": "get_refactoring_progress",
                    "success": True,
                    "progress": {
                        "total": 0,
                        "completed": 0,
                        "in_progress": 0,
                        "pending": 0,
                        "failed": 0,
                        "blocked": 0,
                        "completion_percentage": 0.0
                    }
                }
            
            progress = self._refactoring_manager.get_progress()
            
            self.logger.info(f"     Total: {progress['total']}, Completed: {progress['completed']}, Pending: {progress['pending']}")
            
            return {
                "tool": "get_refactoring_progress",
                "success": True,
                "progress": progress
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get refactoring progress: {e}")
            return {
                "tool": "get_refactoring_progress",
                "success": False,
                "error": str(e)
            }
    
    def _handle_create_issue_report(self, args: Dict) -> Dict:
        """Handle create_issue_report tool."""
        try:
            pass
            # Get or create refactoring task manager
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                from pipeline.state.refactoring_task import RefactoringTaskManager
                self._refactoring_manager = RefactoringTaskManager()
            
            task_id = args['task_id']
            task = self._refactoring_manager.get_task(task_id)
            
            if not task:
                return {
                    "tool": "create_issue_report",
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # Handle both old parameter names (title, description, files_affected) 
            # and new parameter names (impact_analysis, code_examples, etc.)
            # This provides backward compatibility while the AI learns the correct schema
            
            # Map old parameters to new ones if present
            impact_analysis = args.get('impact_analysis')
            if not impact_analysis:
                pass
                # Try old parameter names
                impact_analysis = args.get('description', '')
                if not impact_analysis:
                    impact_analysis = f"Issue in files: {', '.join(args.get('files_affected', task.target_files))}"
            
            # Create issue report
            report = {
                "task_id": task_id,
                "task_title": args.get('title', task.title),  # Support both 'title' and task.title
                "issue_type": task.issue_type.value,
                "severity": args.get('severity', 'medium'),
                "impact_analysis": impact_analysis,
                "recommended_approach": args.get('recommended_approach', 'Manual review required'),
                "code_examples": args.get('code_examples', ''),
                "estimated_effort": args.get('estimated_effort', 'Unknown'),
                "alternatives": args.get('alternatives', ''),
                "target_files": args.get('files_affected', task.target_files),  # Support both parameter names
                "created_at": datetime.now().isoformat()
            }
            
            # Store report in task
            if not hasattr(self, '_issue_reports'):
                self._issue_reports = []
            self._issue_reports.append(report)
            
            # Mark task as needing developer review
            from pipeline.state.refactoring_task import RefactoringApproach
            task.fix_approach = RefactoringApproach.DEVELOPER_REVIEW
            task.needs_review(f"Issue report created: {args['severity']} severity")
            
            self.logger.info(f"  📝 Created issue report for task {task_id}")
            self.logger.info(f"     Severity: {args['severity']}, Effort: {args.get('estimated_effort', 'Unknown')}")
            
            return {
                "tool": "create_issue_report",
                "success": True,
                "report": report
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create issue report: {e}")
            return {
                "tool": "create_issue_report",
                "success": False,
                "error": str(e)
            }
    
    def _handle_request_developer_review(self, args: Dict) -> Dict:
        """Handle request_developer_review tool."""
        try:
            pass
            # Get or create refactoring task manager
            if not hasattr(self, '_refactoring_manager') or self._refactoring_manager is None:
                from pipeline.state.refactoring_task import RefactoringTaskManager
                self._refactoring_manager = RefactoringTaskManager()
            
            task_id = args['task_id']
            task = self._refactoring_manager.get_task(task_id)
            
            if not task:
                return {
                    "tool": "request_developer_review",
                    "success": False,
                    "error": f"Task {task_id} not found"
                }
            
            # Create review request
            review_request = {
                "task_id": task_id,
                "task_title": task.title,
                "question": args['question'],
                "options": args['options'],
                "context": args.get('context', ''),
                "urgency": args.get('urgency', 'medium'),
                "created_at": datetime.now().isoformat()
            }
            
            # Store review request
            if not hasattr(self, '_review_requests'):
                self._review_requests = []
            self._review_requests.append(review_request)
            
            # Mark task as blocked
            from pipeline.state.refactoring_task import RefactoringApproach
            task.fix_approach = RefactoringApproach.DEVELOPER_REVIEW
            task.needs_review(f"Developer review requested: {args['question']}")
            
            self.logger.info(f"  🙋 Requested developer review for task {task_id}")
            self.logger.info(f"     Question: {args['question'][:80]}...")
            self.logger.info(f"     Options: {len(args['options'])} provided")
            
            return {
                "tool": "request_developer_review",
                "success": True,
                "review_request": review_request
            }
            
        except Exception as e:
            self.logger.error(f"Failed to request developer review: {e}")
            return {
                "tool": "request_developer_review",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_architecture(self, args: Dict) -> Dict:
        """Handle validate_architecture tool."""
        try:
            from pipeline.analysis.architecture_validator import ArchitectureValidator
            
            check_locations = args.get('check_locations', True)
            check_naming = args.get('check_naming', True)
            check_missing = args.get('check_missing', True)
            
            
            validator = ArchitectureValidator(self.project_dir, self.logger)
            results = validator.validate_all()
            
            # Generate report
            report = validator.generate_report(results)
            
            # Save report to file
            report_file = self.project_dir / "ARCHITECTURE_VALIDATION_REPORT.md"
            report_file.write_text(report)
            
            # Count violations by severity
            all_violations = []
            for violations in results.values():
                all_violations.extend(violations)
            
            by_severity = {}
            for v in all_violations:
                by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
            
            self.logger.info(f"   Total violations: {len(all_violations)}")
            if by_severity:
                for severity in ['critical', 'high', 'medium', 'low']:
                    if severity in by_severity:
                        self.logger.info(f"   {severity.upper()}: {by_severity[severity]}")
            self.logger.info(f"   Report: ARCHITECTURE_VALIDATION_REPORT.md")
            
            return {
                "tool": "validate_architecture",
                "success": True,
                "result": {
                    "violations": [
                        {
                            'type': v.violation_type,
                            'severity': v.severity,
                            'file': v.file_path,
                            'description': v.description,
                            'expected': v.expected,
                            'actual': v.actual,
                            'recommendation': v.recommendation
                        }
                        for violations in results.values()
                        for v in violations
                    ],
                    "total_violations": len(all_violations),
                    "by_severity": by_severity
                },
                "report": report,
                "report_file": "ARCHITECTURE_VALIDATION_REPORT.md"
            }
        except Exception as e:
            self.logger.error(f"Architecture validation failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "tool": "validate_architecture",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_duplicate_implementations(self, args: Dict) -> Dict:
        """Handle detect_duplicate_implementations tool."""
        try:
            from pipeline.analysis.file_refactoring import DuplicateDetector
            
            similarity_threshold = args.get('similarity_threshold', 0.75)
            scope = args.get('scope', 'project')
            include_tests = args.get('include_tests', False)
            
            
            detector = DuplicateDetector(self.project_dir, self.logger)
            duplicate_sets = detector.find_duplicates(
                similarity_threshold=similarity_threshold,
                scope=scope,
                include_tests=include_tests
            )
            
            # Convert to dict
            result = {
                'duplicate_sets': [ds.to_dict() for ds in duplicate_sets],
                'total_duplicates': len(duplicate_sets),
                'estimated_reduction': sum(ds.estimated_reduction for ds in duplicate_sets)
            }
            
            if duplicate_sets:
                self.logger.info(f"   Estimated reduction: ~{result.get('estimated_reduction', 0)} lines")
            
            return {
                "tool": "detect_duplicate_implementations",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Duplicate detection failed: {e}")
            return {
                "tool": "detect_duplicate_implementations",
                "success": False,
                "error": str(e)
            }
    
    def _handle_compare_file_implementations(self, args: Dict) -> Dict:
        """Handle compare_file_implementations tool."""
        try:
            from pipeline.analysis.file_refactoring import FileComparator
            
            file1 = args['file1']
            file2 = args['file2']
            comparison_type = args.get('comparison_type', 'full')
            
            
            comparator = FileComparator(self.project_dir, self.logger)
            comparison = comparator.compare(file1, file2, comparison_type)
            
            self.logger.info(f"   Similarity: {comparison.similarity_score:.2%}")
            self.logger.info(f"   Common features: {len(comparison.common_features)}")
            self.logger.info(f"   Conflicts: {len(comparison.conflicts)}")
            self.logger.info(f"   Merge strategy: {comparison.merge_strategy}")
            
            return {
                "tool": "compare_file_implementations",
                "success": True,
                "comparison": comparison.to_dict()
            }
        except Exception as e:
            self.logger.error(f"File comparison failed: {e}")
            return {
                "tool": "compare_file_implementations",
                "success": False,
                "error": str(e)
            }
    
    def _handle_extract_file_features(self, args: Dict) -> Dict:
        """Handle extract_file_features tool."""
        try:
            from pipeline.analysis.file_refactoring import FeatureExtractor
            
            source_file = args['source_file']
            features = args['features']
            include_dependencies = args.get('include_dependencies', True)
            
            self.logger.info(f"📦 Extracting {len(features)} features from {source_file}")
            
            extractor = FeatureExtractor(self.project_dir, self.logger)
            extracted = extractor.extract(
                source_file=source_file,
                features=features,
                include_dependencies=include_dependencies
            )
            
            # Convert to dict
            result = {
                'extracted_features': {
                    name: feature.to_dict()
                    for name, feature in extracted.items()
                },
                'total_lines': sum(
                    feature.line_range[1] - feature.line_range[0] + 1
                    for feature in extracted.values()
                ),
                'dependencies_resolved': include_dependencies
            }
            
            self.logger.info(f"   Total lines: {result.get('total_lines', 0)}")
            
            return {
                "tool": "extract_file_features",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return {
                "tool": "extract_file_features",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_architecture_consistency(self, args: Dict) -> Dict:
        """Handle analyze_architecture_consistency tool."""
        try:
            from pipeline.analysis.file_refactoring import RefactoringArchitectureAnalyzer
            
            check_master_plan = args.get('check_master_plan', True)
            check_architecture = args.get('check_architecture', True)
            check_objectives = args.get('check_objectives', True)
            
            self.logger.info("🏗️  Analyzing architecture consistency")
            
            analyzer = RefactoringArchitectureAnalyzer(self.project_dir, self.logger)
            consistency = analyzer.analyze_consistency(
                check_master_plan=check_master_plan,
                check_architecture=check_architecture,
                check_objectives=check_objectives
            )
            
            self.logger.info(f"   Consistency score: {consistency.consistency_score:.2%}")
            self.logger.info(f"   Issues found: {len(consistency.issues)}")
            self.logger.info(f"   Refactoring needed: {consistency.refactoring_needed}")
            self.logger.info(f"   Priority: {consistency.priority}")
            
            return {
                "tool": "analyze_architecture_consistency",
                "success": True,
                "consistency": consistency.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Architecture analysis failed: {e}")
            return {
                "tool": "analyze_architecture_consistency",
                "success": False,
                "error": str(e)
            }
    
    def _handle_suggest_refactoring_plan(self, args: Dict) -> Dict:
        """Handle suggest_refactoring_plan tool."""
        try:
            analysis_results = args['analysis_results']
            priority = args.get('priority', 'high')
            max_steps = args.get('max_steps', 10)
            
            self.logger.info(f"📋 Generating refactoring plan (priority: {priority})")
            
            # Generate plan based on analysis results
            plan = []
            step_num = 1
            
            # If duplicate sets exist, create merge steps
            if 'duplicate_sets' in analysis_results:
                for dup_set in analysis_results['duplicate_sets']:
                    if step_num > max_steps:
                        break
                    
                    if dup_set.get('merge_recommended'):
                        plan.append({
                            'step': step_num,
                            'action': 'merge_files',
                            'source_files': dup_set['files'],
                            'target_file': f"{dup_set['files'][0].replace('.py', '_merged.py')}",
                            'reason': f"Duplicate implementations",
                            'estimated_effort': 'medium',
                            'dependencies': []
                        })
                        step_num += 1
            
            result = {
                'refactoring_plan': plan,
                'total_steps': len(plan),
                'estimated_time': f"{len(plan) * 15} minutes"
            }
            
            
            return {
                "tool": "suggest_refactoring_plan",
                "success": True,
                "plan": result
            }
        except Exception as e:
            self.logger.error(f"Plan generation failed: {e}")
            return {
                "tool": "suggest_refactoring_plan",
                "success": False,
                "error": str(e)
            }
    
    def _handle_merge_file_implementations(self, args: Dict) -> Dict:
        """Handle merge_file_implementations tool."""
        try:
            source_files = args['source_files']
            target_file = args['target_file']
            merge_strategy = args.get('merge_strategy', 'ai_merge')
            
            
            # Create backup
            import shutil
            from datetime import datetime
            import ast
            backup_dir = self.project_dir / '.autonomy' / 'backups' / f"merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup target file if it exists
            target_path = self.project_dir / target_file
            if target_path.exists():
                shutil.copy2(target_path, backup_dir / target_path.name)
            
            # Backup source files
            for src_file in source_files:
                src_path = self.project_dir / src_file
                if src_path.exists():
                    shutil.copy2(src_path, backup_dir / src_path.name)
            
            # Read and merge content
            all_imports = set()
            all_classes = {}
            all_functions = {}
            all_other_code = []
            module_docstring = None
            
            for src_file in source_files:
                src_path = self.project_dir / src_file
                if not src_path.exists():
                    self.logger.warning(f"Source file not found: {src_file}")
                    continue
                
                try:
                    content = src_path.read_text()
                    tree = ast.parse(content)
                    
                    # Extract module docstring
                    if ast.get_docstring(tree) and not module_docstring:
                        module_docstring = ast.get_docstring(tree)
                    
                    for i, node in enumerate(tree.body):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            pass
                            # Collect imports
                            all_imports.add(ast.unparse(node))
                        elif isinstance(node, ast.ClassDef):
                            pass
                            # Collect classes (keep first occurrence)
                            if node.name not in all_classes:
                                all_classes[node.name] = ast.unparse(node)
                        elif isinstance(node, ast.FunctionDef):
                            pass
                            # Collect functions (keep first occurrence)
                            if node.name not in all_functions:
                                all_functions[node.name] = ast.unparse(node)
                        elif i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            pass
                            # Skip module docstring (first node that's a string expression)
                            # It's already captured by ast.get_docstring()
                            continue
                        else:
                            pass
                            # Collect other code (constants, etc.)
                            all_other_code.append(ast.unparse(node))
                
                except SyntaxError as e:
                    self.logger.warning(f"Syntax error in {src_file}, copying raw content: {e}")
                    # If parsing fails, just append the raw content
                    all_other_code.append(f"\n# Content from {src_file} (could not parse):\n{content}\n")
            
            # Build merged content
            merged_lines = []
            
            # Add header comment
            merged_lines.append(f"# Merged from: {', '.join(source_files)}")
            merged_lines.append(f"# Backup location: {backup_dir.relative_to(self.project_dir)}")
            merged_lines.append("")
            
            # Add module docstring
            if module_docstring:
                merged_lines.append(f'"""{module_docstring}"""')
                merged_lines.append("")
            
            # Add imports (sorted)
            if all_imports:
                merged_lines.extend(sorted(all_imports))
                merged_lines.append("")
            
            # Add other code (constants, etc.)
            if all_other_code:
                merged_lines.extend(all_other_code)
                merged_lines.append("")
            
            # Add classes
            if all_classes:
                for class_code in all_classes.values():
                    merged_lines.append(class_code)
                    merged_lines.append("")
            
            # Add functions
            if all_functions:
                for func_code in all_functions.values():
                    merged_lines.append(func_code)
                    merged_lines.append("")
            
            merged_content = "\n".join(merged_lines)
            
            # Write merged content
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(merged_content)
            
            result = {
                'success': True,
                'merged_file': target_file,
                'backup_path': str(backup_dir.relative_to(self.project_dir)),
                'imports_merged': len(all_imports),
                'classes_merged': len(all_classes),
                'functions_merged': len(all_functions)
            }
            
            
            return {
                "tool": "merge_file_implementations",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"File merge failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "tool": "merge_file_implementations",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_refactoring(self, args: Dict) -> Dict:
        """Handle validate_refactoring tool."""
        try:
            refactored_files = args['refactored_files']
            check_syntax = args.get('check_syntax', True)
            
            
            syntax_errors = []
            
            if check_syntax:
                import ast
                for filepath in refactored_files:
                    full_path = self.project_dir / filepath
                    if full_path.exists():
                        try:
                            content = full_path.read_text()
                            ast.parse(content)
                        except SyntaxError as e:
                            syntax_errors.append({'file': filepath, 'error': str(e)})
            
            result = {
                'valid': len(syntax_errors) == 0,
                'syntax_errors': syntax_errors
            }
            
            
            return {
                "tool": "validate_refactoring",
                "success": True,
                "validation": result
            }
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                "tool": "validate_refactoring",
                "success": False,
                "error": str(e)
            }
    
    def _handle_cleanup_redundant_files(self, args: Dict) -> Dict:
        """Handle cleanup_redundant_files tool."""
        try:
            files_to_remove = args['files_to_remove']
            reason = args['reason']
            create_backup = args.get('create_backup', True)
            
            self.logger.info(f"🗑️  Cleaning up {len(files_to_remove)} redundant files")
            
            backup_location = None
            if create_backup:
                import shutil
                from datetime import datetime
                backup_dir = self.project_dir / '.autonomy' / 'backups' / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                for filepath in files_to_remove:
                    src_path = self.project_dir / filepath
                    if src_path.exists():
                        shutil.copy2(src_path, backup_dir / src_path.name)
                
                backup_location = str(backup_dir.relative_to(self.project_dir))
            
            files_removed = []
            for filepath in files_to_remove:
                full_path = self.project_dir / filepath
                if full_path.exists():
                    full_path.unlink()
                    files_removed.append(filepath)
            
            result = {
                'success': True,
                'files_removed': files_removed,
                'backup_location': backup_location
            }
            
            
            return {
                "tool": "cleanup_redundant_files",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {
                "tool": "cleanup_redundant_files",
                "success": False,
                "error": str(e)
            }
    
    # =========================================================================
    # Validation Tools (Phase 1 - Critical)
    # =========================================================================
    
    def _handle_validate_attribute_access(self, args: Dict) -> Dict:
        """Validate attribute access patterns."""
        try:
            from ..analysis.code_validation import AttributeAccessValidator
            
            filepath = args.get('filepath')
            check_all = args.get('check_all_files', False)
            
            
            if check_all:
                pass
                # Check all Python files
                from pathlib import Path
                files = [f for f in Path(self.project_dir).rglob("*.py") 
                        if '.venv' not in str(f) and '__pycache__' not in str(f)]
            else:
                files = [self.project_dir / filepath]
            
            all_issues = []
            for file in files:
                validator = AttributeAccessValidator(str(file), self.logger)
                issues = validator.validate()
                if issues:
                    all_issues.extend(issues)
            
            if all_issues:
                for issue in all_issues[:5]:  # Show first 5
                    self.logger.warning(f"  • {issue['file']}:{issue.get('line', '?')}: {issue['message']}")
            else:
                pass
            
            return {
                "tool": "validate_attribute_access",
                "success": True,
                "issues_found": len(all_issues),
                "issues": all_issues,
                "message": f"Found {len(all_issues)} attribute access issues"
            }
        except Exception as e:
            self.logger.error(f"Attribute validation failed: {e}")
            return {
                "tool": "validate_attribute_access",
                "success": False,
                "error": str(e)
            }
    
    def _handle_verify_import_class_match(self, args: Dict) -> Dict:
        """Verify import names match class names."""
        try:
            from ..analysis.code_validation import ImportClassMatcher
            
            filepath = args.get('filepath')
            
            
            full_path = self.project_dir / filepath
            matcher = ImportClassMatcher(str(full_path), self.logger)
            issues = matcher.validate()
            
            if issues:
                for issue in issues[:5]:  # Show first 5
                    self.logger.warning(f"  • Line {issue.get('line', '?')}: {issue['message']}")
            else:
                pass
            
            return {
                "tool": "verify_import_class_match",
                "success": True,
                "issues_found": len(issues),
                "issues": issues,
                "message": f"Found {len(issues)} import-class mismatch issues"
            }
        except Exception as e:
            self.logger.error(f"Import verification failed: {e}")
            return {
                "tool": "verify_import_class_match",
                "success": False,
                "error": str(e)
            }
    
    def _handle_check_abstract_methods(self, args: Dict) -> Dict:
        """Check abstract methods are implemented."""
        try:
            from ..analysis.code_validation import AbstractMethodChecker
            
            filepath = args.get('filepath')
            class_name = args.get('class_name')
            
            
            full_path = self.project_dir / filepath
            checker = AbstractMethodChecker(str(full_path), class_name, self.logger)
            issues = checker.validate()
            
            if issues:
                for issue in issues:
                    self.logger.warning(f"  • {issue['message']}")
            else:
                pass
            
            return {
                "tool": "check_abstract_methods",
                "success": True,
                "issues_found": len(issues),
                "issues": issues,
                "message": f"Found {len(issues)} abstract method issues"
            }
        except Exception as e:
            self.logger.error(f"Abstract method check failed: {e}")
            return {
                "tool": "check_abstract_methods",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_syntax(self, args: Dict) -> Dict:
        """Handle validate_syntax tool."""
        try:
            code = args.get('code', '')
            filename = args.get('filename', '<string>')
            
            # Use existing syntax validator
            from pipeline.syntax_validator import SyntaxValidator
            validator = SyntaxValidator(project_root=str(self.project_dir))
            
            is_valid, errors = validator.validate_python_code(code, filename)
            
            if errors:
                self.logger.info(f"     Errors: {len(errors)}")
            
            return {
                "tool": "validate_syntax",
                "success": is_valid,
                "errors": errors if not is_valid else [],
                "message": "Syntax is valid" if is_valid else f"Found {len(errors)} syntax errors"
            }
        except Exception as e:
            self.logger.error(f"Syntax validation failed: {e}")
            return {
                "tool": "validate_syntax",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_circular_imports(self, args: Dict) -> Dict:
        """Handle detect_circular_imports tool."""
        try:
            project_dir = args.get('project_dir', str(self.project_dir))
            
            # Use existing import analyzer
            from pipeline.import_analyzer import ImportAnalyzer
            analyzer = ImportAnalyzer(project_dir)
            
            circular = analyzer.detect_circular_imports()
            
            self.logger.info(f"  🔄 Circular imports: {len(circular)} found")
            for cycle in circular[:3]:  # Show first 3
                self.logger.info(f"     {' → '.join(cycle)}")
            
            return {
                "tool": "detect_circular_imports",
                "success": True,
                "circular_imports": circular,
                "count": len(circular),
                "message": f"Found {len(circular)} circular import cycles"
            }
        except Exception as e:
            self.logger.error(f"Circular import detection failed: {e}")
            return {
                "tool": "detect_circular_imports",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_all_imports(self, args: Dict) -> Dict:
        """Handle validate_all_imports tool."""
        try:
            project_dir = args.get('project_dir', str(self.project_dir))
            
            # Use existing import analyzer
            from pipeline.import_analyzer import ImportAnalyzer
            analyzer = ImportAnalyzer(project_dir)
            
            invalid = analyzer.validate_all_imports()
            
            self.logger.info(f"  📦 Import validation: {len(invalid)} invalid imports")
            for imp in invalid[:3]:  # Show first 3
                self.logger.info(f"     {imp}")
            
            return {
                "tool": "validate_all_imports",
                "success": True,
                "invalid_imports": invalid,
                "count": len(invalid),
                "message": f"Found {len(invalid)} invalid imports"
            }
        except Exception as e:
            self.logger.error(f"Import validation failed: {e}")
            return {
                "tool": "validate_all_imports",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_function_calls(self, args: Dict) -> Dict:
        """Validate function and method calls use correct parameters."""
        try:
            from pipeline.analysis.function_call_validator import FunctionCallValidator
            
            
            validator = FunctionCallValidator(str(self.project_dir))
            result = validator.validate_all()
            
            errors = result.get('errors', [])
            if errors:
                for err in errors[:5]:  # Show first 5
                    self.logger.warning(f"  • {err['file']}:{err['line']}: {err['message']}")
            else:
                pass
            
            return {
                "tool": "validate_function_calls",
                "success": True,
                "result": result,
                "errors": errors,
                "total_errors": len(errors),
                "message": f"Found {len(errors)} function call errors"
            }
        except Exception as e:
            self.logger.error(f"Function call validation failed: {e}")
            return {
                "tool": "validate_function_calls",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_method_existence(self, args: Dict) -> Dict:
        """Validate that methods called on objects exist."""
        try:
            from pipeline.analysis.method_existence_validator import MethodExistenceValidator
            
            
            validator = MethodExistenceValidator(str(self.project_dir))
            result = validator.validate_all()
            
            errors = result.get('errors', [])
            if errors:
                for err in errors[:5]:  # Show first 5
                    self.logger.warning(f"  • {err['file']}:{err['line']}: {err['class_name']}.{err['method_name']} does not exist")
            else:
                pass
            
            return {
                "tool": "validate_method_existence",
                "success": True,
                "result": result,
                "errors": errors,
                "total_errors": len(errors),
                "message": f"Found {len(errors)} method existence errors"
            }
        except Exception as e:
            self.logger.error(f"Method existence validation failed: {e}")
            return {
                "tool": "validate_method_existence",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_dict_structure(self, args: Dict) -> Dict:
        """Validate dictionary access patterns match actual structures."""
        try:
            from pipeline.analysis.dict_structure_validator import DictStructureValidator
            
            
            validator = DictStructureValidator(str(self.project_dir))
            result = validator.validate_all()
            
            errors = result.get('errors', [])
            if errors:
                for err in errors[:5]:  # Show first 5
                    self.logger.warning(f"  • {err['file']}:{err['line']}: {err['message']}")
            else:
                pass
            
            return {
                "tool": "validate_dict_structure",
                "success": True,
                "result": result,
                "errors": errors,
                "total_errors": len(errors),
                "message": f"Found {len(errors)} dictionary structure errors"
            }
        except Exception as e:
            self.logger.error(f"Dictionary structure validation failed: {e}")
            return {
                "tool": "validate_dict_structure",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_type_usage(self, args: Dict) -> Dict:
        """Validate that objects are used according to their types."""
        try:
            from pipeline.analysis.type_usage_validator import TypeUsageValidator
            
            
            validator = TypeUsageValidator(str(self.project_dir))
            result = validator.validate_all()
            
            errors = result.get('errors', [])
            if errors:
                for err in errors[:5]:  # Show first 5
                    self.logger.warning(f"  • {err['file']}:{err['line']}: {err['message']}")
            else:
                pass
            
            return {
                "tool": "validate_type_usage",
                "success": True,
                "result": result,
                "errors": errors,
                "total_errors": len(errors),
                "message": f"Found {len(errors)} type usage errors"
            }
        except Exception as e:
            self.logger.error(f"Type usage validation failed: {e}")
            return {
                "tool": "validate_type_usage",
                "success": False,
                "error": str(e)
            }
    
    def _handle_verify_tool_handlers(self, args: Dict) -> Dict:
        """Verify tool-handler-registration chain."""
        try:
            from ..analysis.code_validation import ToolHandlerVerifier
            
            
            verifier = ToolHandlerVerifier(str(self.project_dir), self.logger)
            issues = verifier.validate()
            
            if issues:
                for issue in issues[:10]:  # Show first 10
                    self.logger.warning(f"  • {issue['type']}: {issue['message']}")
            else:
                pass
            
            return {
                "tool": "verify_tool_handlers",
                "success": True,
                "issues_found": len(issues),
                "issues": issues,
                "message": f"Found {len(issues)} tool-handler issues"
            }
        except Exception as e:
            self.logger.error(f"Tool-handler verification failed: {e}")
            return {
                "tool": "verify_tool_handlers",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_dict_access(self, args: Dict) -> Dict:
        """Validate dictionary access patterns."""
        try:
            from ..analysis.code_validation import DictAccessValidator
            
            filepath = args.get('filepath')
            
            
            full_path = self.project_dir / filepath
            validator = DictAccessValidator(str(full_path), self.logger)
            issues = validator.validate()
            
            if issues:
                for issue in issues[:5]:  # Show first 5
                    self.logger.warning(f"  • Line {issue.get('line', '?')}: {issue['message']}")
            else:
                pass
            
            return {
                "tool": "validate_dict_access",
                "success": True,
                "issues_found": len(issues),
                "issues": issues,
                "message": f"Found {len(issues)} unsafe dictionary access patterns"
            }
        except Exception as e:
            self.logger.error(f"Dictionary access validation failed: {e}")
            return {
                "tool": "validate_dict_access",
                "success": False,
                "error": str(e)
            }
    
    def _handle_validate_imports_comprehensive(self, args: Dict) -> Dict:
        """Handle validate_imports_comprehensive tool."""
        try:
            import ast
            import re
            from pathlib import Path
            from collections import defaultdict
            
            target_dir = args.get('target_dir', 'pipeline')
            check_syntax = args.get('check_syntax', True)
            check_imports = args.get('check_imports', True)
            check_modules = args.get('check_modules', True)
            check_typing = args.get('check_typing', True)
            
            
            full_path = self.project_dir / target_dir
            errors = []
            warnings = []
            stats = {
                'total_files': 0,
                'total_modules': 0,
                'syntax_errors': 0,
                'import_errors': 0,
                'module_errors': 0,
                'typing_warnings': 0
            }
            
            # Scan for modules
            actual_modules = set()
            for root, dirs, files in full_path.walk():
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        rel_path = Path(root).relative_to(self.project_dir)
                        module_path = str(rel_path / file[:-3]).replace('/', '.')
                        actual_modules.add(module_path)
            
            stats['total_modules'] = len(actual_modules)
            
            # Check syntax
            if check_syntax:
                for root, dirs, files in full_path.walk():
                    for file in files:
                        if file.endswith('.py'):
                            filepath = Path(root) / file
                            stats['total_files'] += 1
                            try:
                                with open(filepath, 'r') as f:
                                    ast.parse(f.read())
                            except SyntaxError as e:
                                rel_path = filepath.relative_to(self.project_dir)
                                errors.append(f"{rel_path}:{e.lineno} - Syntax error: {e.msg}")
                                stats['syntax_errors'] += 1
            
            # Check imports
            imports_found = defaultdict(list)
            if check_imports:
                for root, dirs, files in full_path.walk():
                    for file in files:
                        if file.endswith('.py'):
                            filepath = Path(root) / file
                            rel_path = filepath.relative_to(self.project_dir)
                            with open(filepath, 'r') as f:
                                for i, line in enumerate(f, 1):
                                    if 'from pipeline.state.task import' in line:
                                        errors.append(f"{rel_path}:{i} - Non-existent module 'pipeline.state.task'")
                                        stats['import_errors'] += 1
                                    
                                    match = re.match(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', line)
                                    if match:
                                        module = match.group(1) or match.group(2)
                                        if module.startswith('pipeline.'):
                                            imports_found[module].append(f"{rel_path}:{i}")
            
            # Check module existence
            if check_modules:
                for module, locations in imports_found.items():
                    if module not in actual_modules:
                        package_path = module.replace('.', '/')
                        if not (self.project_dir / package_path).exists() and \
                           not (self.project_dir / f"{package_path}.py").exists():
                            parent_exists = any(m.startswith(module + '.') for m in actual_modules)
                            if not parent_exists and module.startswith('pipeline.'):
                                errors.append(f"Module '{module}' does not exist (imported in {len(locations)} places)")
                                stats['module_errors'] += 1
            
            # Check typing imports
            if check_typing:
                typing_types = ['Any', 'Union', 'Optional', 'List', 'Dict', 'Tuple', 'Set', 'Callable']
                for root, dirs, files in full_path.walk():
                    for file in files:
                        if file.endswith('.py'):
                            filepath = Path(root) / file
                            rel_path = filepath.relative_to(self.project_dir)
                            with open(filepath, 'r') as f:
                                content = f.read()
                                lines = content.split('\n')
                                
                                typing_imports = set()
                                for line in lines:
                                    match = re.match(r'from typing import (.+)', line)
                                    if match:
                                        imports = match.group(1).split(',')
                                        typing_imports.update(i.strip() for i in imports)
                                
                                for type_name in typing_types:
                                    pattern = rf'(?:->|:)\s*{type_name}[\[\s,\)]'
                                    if re.search(pattern, content) and type_name not in typing_imports:
                                        for i, line in enumerate(lines, 1):
                                            if re.search(pattern, line):
                                                warnings.append(f"{rel_path}:{i} - Uses '{type_name}' but doesn't import it")
                                                stats['typing_warnings'] += 1
                                                break
            
            # Log results
            if errors:
                self.logger.warning(f"❌ Found {len(errors)} errors")
                for error in errors[:5]:
                    self.logger.warning(f"  • {error}")
            else:
                pass
            
            if warnings:
                pass
            
            return {
                "tool": "validate_imports_comprehensive",
                "success": True,
                "stats": stats,
                "errors": errors,
                "warnings": warnings,
                "passed": len(errors) == 0,
                "message": f"Validated {stats['total_files']} files, found {len(errors)} errors, {len(warnings)} warnings"
            }
        except Exception as e:
            self.logger.error(f"Comprehensive import validation failed: {e}")
            return {
                "tool": "validate_imports_comprehensive",
                "success": False,
                "error": str(e)
            }
    
    def _handle_fix_html_entities(self, args: Dict) -> Dict:
        """Handle fix_html_entities tool."""
        try:
            import re
            from pathlib import Path
            
            target = args.get('target')
            dry_run = args.get('dry_run', False)
            backup = args.get('backup', True)
            recursive = args.get('recursive', True)
            
            self.logger.info(f"🔧 Fixing HTML entities: {target} (dry_run={dry_run})")
            
            full_path = self.project_dir / target
            
            # Collect files
            files_to_process = []
            if full_path.is_file():
                if full_path.suffix == '.py':
                    files_to_process.append(full_path)
            elif full_path.is_dir():
                if recursive:
                    files_to_process = list(full_path.rglob('*.py'))
                else:
                    files_to_process = list(full_path.glob('*.py'))
            
            results = []
            total_fixes = 0
            
            for filepath in files_to_process:
                rel_path = filepath.relative_to(self.project_dir)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Detect issues
                issues = []
                lines = original_content.split('\n')
                
                pattern1 = r'\\&amp;quot;\\&amp;quot;\\&amp;quot;'
                pattern2 = r'&amp;[a-z]+;'
                
                for i, line in enumerate(lines, 1):
                    if re.search(pattern1, line):
                        issues.append({'line': i, 'type': 'malformed_docstring'})
                    elif re.search(pattern2, line) and not ('"' in line or "'" in line):
                        issues.append({'line': i, 'type': 'html_entity'})
                
                if len(issues) == 0:
                    continue
                
                # Fix issues
                fixed_content = original_content
                fixes_applied = 0
                
                if not dry_run:
                    pass
                    # Fix malformed docstring quotes
                    fixed_content = re.sub(r'\\&amp;quot;\\&amp;quot;\\&amp;quot;', '"""', fixed_content)
                    fixes_applied += len(re.findall(pattern1, original_content))
                    
                    # Fix HTML entities
                    entity_map = {
                        '&amp;quot;': '"',
                        '&amp;apos;': "'",
                        '&amp;lt;': '<',
                        '&amp;gt;': '>',
                        '&amp;amp;': '&amp;'
                    }
                    
                    for entity, char in entity_map.items():
                        if entity in fixed_content:
                            lines = fixed_content.split('\n')
                            new_lines = []
                            for line in lines:
                                if '"""' in line or "'''" in line or line.strip().startswith('#'):
                                    line = line.replace(entity, char)
                                new_lines.append(line)
                            fixed_content = '\n'.join(new_lines)
                    
                    # Create backup
                    if backup and fixes_applied > 0:
                        backup_path = filepath.with_suffix('.py.bak')
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                    
                    # Write fixed content
                    if fixes_applied > 0:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                
                results.append({
                    'filepath': str(rel_path),
                    'issues_found': len(issues),
                    'fixes_applied': fixes_applied
                })
                total_fixes += fixes_applied
            
            if results:
                pass
            else:
                pass
            
            return {
                "tool": "fix_html_entities",
                "success": True,
                "files_processed": len(files_to_process),
                "files_with_issues": len(results),
                "total_fixes": total_fixes,
                "files": results,
                "message": f"Processed {len(files_to_process)} files, fixed {total_fixes} issues"
            }
        except Exception as e:
            self.logger.error(f"HTML entity fix failed: {e}")
            return {
                "tool": "fix_html_entities",
                "success": False,
                "error": str(e)
            }
# =============================================================================
    # File Operation Handlers (CRITICAL - Phase 2)
    # =============================================================================
    
    def _handle_move_file(self, args: Dict) -> Dict:
        """Handle move_file tool - move file with automatic import updates."""
        try:
            source_path = args['source_path']
            destination_path = args['destination_path']
            update_imports = args.get('update_imports', True)
            create_directories = args.get('create_directories', True)
            reason = args.get('reason', 'No reason provided')
            
            self.logger.info(f"📦 Moving file: {source_path} → {destination_path}")
            if reason != 'No reason provided':
                self.logger.info(f"   Reason: {reason}")
            
            # Import analysis components
            from .analysis.import_impact import ImportImpactAnalyzer
            from .analysis.import_updater import ImportUpdater
            
            # Analyze impact first
            impact_analyzer = ImportImpactAnalyzer(str(self.project_dir), self.logger)
            impact = impact_analyzer.analyze_move_impact(source_path, destination_path)
            
            self.logger.info(f"   Impact: {len(impact.affected_files)} files affected, "
                           f"risk level: {impact.risk_level.value}")
            
            # Check if source exists
            source_full = self.project_dir / source_path
            if not source_full.exists():
                return {
                    "tool": "move_file",
                    "success": False,
                    "error": f"Source file does not exist: {source_path}"
                }
            
            # Create destination directory if needed
            dest_full = self.project_dir / destination_path
            if create_directories:
                dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            # Use git mv to preserve history
            import subprocess
            try:
                result = subprocess.run(
                    ['git', 'mv', source_path, destination_path],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                pass
                # Fallback to regular move if git mv fails
                self.logger.warning(f"   git mv failed, using regular move: {e.stderr}")
                import shutil
                shutil.move(str(source_full), str(dest_full))
            
            # Update imports if requested
            updated_files = []
            if update_imports and impact.affected_files:
                self.logger.info(f"   🔄 Updating imports in {len(impact.affected_files)} files...")
                
                updater = ImportUpdater(str(self.project_dir), self.logger)
                update_results = updater.update_imports_for_move(
                    source_path,
                    destination_path,
                    dry_run=False
                )
                
                for result in update_results:
                    if result.success and result.changes_made > 0:
                        updated_files.append(result.file)
                    elif not result.success:
                        pass
            
            # Track in handler
            self.files_modified.append(destination_path)
            self.files_modified.extend(updated_files)
            
            return {
                "tool": "move_file",
                "success": True,
                "source": source_path,
                "destination": destination_path,
                "files_updated": updated_files,
                "import_changes": len(updated_files),
                "risk_level": impact.risk_level.value,
                "message": f"Moved {source_path} to {destination_path}, updated {len(updated_files)} files"
            }
            
        except Exception as e:
            self.logger.error(f"Move file failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "tool": "move_file",
                "success": False,
                "error": str(e)
            }
    
    def _handle_rename_file(self, args: Dict) -> Dict:
        """Handle rename_file tool - rename file with automatic import updates."""
        try:
            file_path = args['file_path']
            new_name = args['new_name']
            update_imports = args.get('update_imports', True)
            reason = args['reason']
            
            # Renaming is just moving within same directory
            from pathlib import Path
            old_path = Path(file_path)
            new_path = old_path.parent / new_name
            
            return self._handle_move_file({
                'source_path': file_path,
                'destination_path': str(new_path),
                'update_imports': update_imports,
                'create_directories': False,
                'reason': reason
            })
            
        except Exception as e:
            self.logger.error(f"Rename file failed: {e}")
            return {
                "tool": "rename_file",
                "success": False,
                "error": str(e)
            }
    
    def _handle_restructure_directory(self, args: Dict) -> Dict:
        """Handle restructure_directory tool - move multiple files with import updates."""
        try:
            restructuring_plan = args['restructuring_plan']
            update_imports = args.get('update_imports', True)
            reason = args['reason']
            
            self.logger.info(f"🏗️  Restructuring directory: {len(restructuring_plan)} files")
            self.logger.info(f"   Reason: {reason}")
            
            results = []
            total_updated = 0
            
            # Process each move
            for old_path, new_path in restructuring_plan.items():
                result = self._handle_move_file({
                    'source_path': old_path,
                    'destination_path': new_path,
                    'update_imports': update_imports,
                    'create_directories': True,
                    'reason': f"Part of restructuring: {reason}"
                })
                
                results.append({
                    'old_path': old_path,
                    'new_path': new_path,
                    'success': result['success'],
                    'files_updated': result.get('files_updated', [])
                })
                
                if result['success']:
                    total_updated += len(result.get('files_updated', []))
            
            success_count = sum(1 for r in results if r['success'])
            
            return {
                "tool": "restructure_directory",
                "success": success_count == len(restructuring_plan),
                "files_moved": success_count,
                "total_files": len(restructuring_plan),
                "total_imports_updated": total_updated,
                "results": results,
                "message": f"Restructured {success_count}/{len(restructuring_plan)} files, "
                          f"updated {total_updated} import statements"
            }
            
        except Exception as e:
            self.logger.error(f"Restructure directory failed: {e}")
            return {
                "tool": "restructure_directory",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_file_placement(self, args: Dict) -> Dict:
        """Handle analyze_file_placement tool - analyze if file is in correct location."""
        try:
            file_path = args['file_path']
            
            self.logger.info(f"📍 Analyzing file placement: {file_path}")
            
            from .context.architectural import ArchitecturalContextProvider
            
            arch_context = ArchitecturalContextProvider(str(self.project_dir), self.logger)
            validation = arch_context.validate_file_location(file_path)
            
            return {
                "tool": "analyze_file_placement",
                "success": True,
                "file": file_path,
                "valid": validation.valid,
                "violations": validation.violations,
                "suggested_location": validation.suggested_location,
                "reason": validation.reason,
                "confidence": validation.confidence,
                "message": validation.reason
            }
            
        except Exception as e:
            self.logger.error(f"Analyze file placement failed: {e}")
            return {
                "tool": "analyze_file_placement",
                "success": False,
                "error": str(e)
            }
    
    def _handle_build_import_graph(self, args: Dict) -> Dict:
        """Handle build_import_graph tool - build complete import graph."""
        try:
            scope = args.get('scope', 'project')
            
            self.logger.info(f"🕸️  Building import graph (scope: {scope})")
            
            from .analysis.import_graph import ImportGraphBuilder
            
            graph_builder = ImportGraphBuilder(str(self.project_dir), self.logger)
            graph_builder.build_graph()
            
            graph_dict = graph_builder.to_dict()
            
            return {
                "tool": "build_import_graph",
                "success": True,
                "graph": graph_dict,
                "stats": graph_dict['stats'],
                "message": f"Built import graph: {graph_dict['stats']['total_files']} files, "
                          f"{graph_dict['stats']['circular_dependencies']} circular dependencies"
            }
            
        except Exception as e:
            self.logger.error(f"Build import graph failed: {e}")
            return {
                "tool": "build_import_graph",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_import_impact(self, args: Dict) -> Dict:
        """Handle analyze_import_impact tool - analyze impact of file operation."""
        try:
            file_path = args['file_path']
            new_path = args.get('new_path')
            operation = args.get('operation', 'move')
            
            
            from .analysis.import_impact import ImportImpactAnalyzer
            
            impact_analyzer = ImportImpactAnalyzer(str(self.project_dir), self.logger)
            
            if operation == 'delete':
                impact = impact_analyzer.analyze_delete_impact(file_path)
            elif operation == 'rename' and new_path:
                impact = impact_analyzer.analyze_rename_impact(file_path, new_path)
            else:  # move
                if not new_path:
                    return {
                        "tool": "analyze_import_impact",
                        "success": False,
                        "error": "new_path required for move operation"
                    }
                impact = impact_analyzer.analyze_move_impact(file_path, new_path)
            
            return {
                "tool": "analyze_import_impact",
                "success": True,
                "operation": impact.operation,
                "source_file": impact.source_file,
                "target_file": impact.target_file,
                "risk_level": impact.risk_level.value,
                "affected_files": impact.affected_files,
                "estimated_changes": impact.estimated_changes,
                "test_files_affected": impact.test_files_affected,
                "circular_dependency_risk": impact.circular_dependency_risk,
                "warnings": impact.warnings,
                "recommendations": impact.recommendations,
                "message": f"Impact: {len(impact.affected_files)} files affected, "
                          f"risk level: {impact.risk_level.value}"
            }
            
        except Exception as e:
            self.logger.error(f"Analyze import impact failed: {e}")
            return {
                "tool": "analyze_import_impact",
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # Codebase Analysis Tools
    # =============================================================================
    
    def _handle_list_all_source_files(self, args: Dict) -> Dict:
        """Handle list_all_source_files tool - get complete codebase inventory."""
        try:
            file_types = args.get('file_types', ['py'])
            include_tests = args.get('include_tests', False)
            include_metadata = args.get('include_metadata', True)
            directory_filter = args.get('directory_filter')
            
            self.logger.info(f"📋 Listing all source files (types: {file_types})")
            
            import ast
            from pathlib import Path
            
            files = []
            total_files = 0
            
            # Walk through project directory
            for file_type in file_types:
                pattern = f"**/*.{file_type}"
                for file_path in self.project_dir.glob(pattern):
                    pass
                    # Skip hidden directories and common excludes
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                    if '__pycache__' in str(file_path):
                        continue
                    if 'node_modules' in str(file_path):
                        continue
                    
                    # Apply directory filter
                    rel_path = file_path.relative_to(self.project_dir)
                    if directory_filter and not str(rel_path).startswith(directory_filter):
                        continue
                    
                    # Skip tests if requested
                    if not include_tests and ('test' in str(rel_path).lower() or 'tests' in str(rel_path).lower()):
                        continue
                    
                    total_files += 1
                    
                    file_info = {
                        "path": str(rel_path),
                        "size": file_path.stat().st_size,
                        "type": file_type
                    }
                    
                    # Add metadata if requested
                    if include_metadata and file_type == 'py':
                        try:
                            content = file_path.read_text()
                            file_info["lines"] = len(content.split('\n'))
                            
                            # Parse Python file
                            try:
                                tree = ast.parse(content)
                                
                                # Extract imports
                                imports = []
                                for node in ast.walk(tree):
                                    if isinstance(node, ast.Import):
                                        imports.extend(n.name for n in node.names)
                                    elif isinstance(node, ast.ImportFrom):
                                        if node.module:
                                            imports.append(node.module)
                                
                                # Extract classes
                                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                                
                                # Extract functions
                                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                                
                                file_info["imports"] = list(set(imports))[:10]  # Limit to 10
                                file_info["classes"] = classes
                                file_info["functions"] = functions[:10]  # Limit to 10
                                
                            except SyntaxError:
                                file_info["parse_error"] = "Syntax error in file"
                        except Exception as e:
                            file_info["read_error"] = str(e)
                    
                    files.append(file_info)
            
            
            return {
                "tool": "list_all_source_files",
                "success": True,
                "total_files": total_files,
                "files": files,
                "file_types": file_types,
                "directory_filter": directory_filter
            }
            
        except Exception as e:
            self.logger.error(f"List all source files failed: {e}")
            return {
                "tool": "list_all_source_files",
                "success": False,
                "error": str(e)
            }
    
    def _handle_cross_reference_file(self, args: Dict) -> Dict:
        """Handle cross_reference_file tool - validate file against architecture."""
        try:
            file_path = args['file_path']
            check_placement = args.get('check_placement', True)
            check_purpose = args.get('check_purpose', True)
            check_naming = args.get('check_naming', True)
            check_dependencies = args.get('check_dependencies', True)
            
            
            result = {
                "tool": "cross_reference_file",
                "success": True,
                "file_path": file_path
            }
            
            # Read ARCHITECTURE.md
            arch_path = self.project_dir / "ARCHITECTURE.md"
            architecture_content = ""
            if arch_path.exists():
                architecture_content = arch_path.read_text()
            
            # Read MASTER_PLAN.md
            plan_path = self.project_dir / "MASTER_PLAN.md"
            master_plan_content = ""
            if plan_path.exists():
                master_plan_content = plan_path.read_text()
            
            # Check placement
            if check_placement:
                pass
                # Extract directory from file path
                from pathlib import Path
                file_dir = str(Path(file_path).parent)
                file_name = Path(file_path).name
                
                # Check if directory is mentioned in ARCHITECTURE.md
                placement_valid = file_dir in architecture_content.lower()
                
                # Try to find recommended location
                placement_recommendation = None
                if not placement_valid:
                    pass
                    # Look for patterns in architecture
                    if 'service' in file_name.lower() and 'services/' in architecture_content.lower():
                        placement_recommendation = f"Should be in services/ directory per ARCHITECTURE.md"
                    elif 'model' in file_name.lower() and 'models/' in architecture_content.lower():
                        placement_recommendation = f"Should be in models/ directory per ARCHITECTURE.md"
                    elif 'api' in file_name.lower() and 'api/' in architecture_content.lower():
                        placement_recommendation = f"Should be in api/ directory per ARCHITECTURE.md"
                    elif 'core' in file_dir and 'core/' not in architecture_content.lower():
                        placement_recommendation = f"core/ directory not defined in ARCHITECTURE.md"
                
                result["placement_valid"] = placement_valid
                result["placement_recommendation"] = placement_recommendation
            
            # Check purpose
            if check_purpose:
                pass
                # Check if file or its functionality is mentioned in MASTER_PLAN
                file_base = Path(file_path).stem
                purpose_match = file_base.lower() in master_plan_content.lower()
                
                # Extract relevant section from MASTER_PLAN
                purpose_description = None
                if purpose_match:
                    pass
                    # Find context around the mention
                    lines = master_plan_content.split('\n')
                    for i, line in enumerate(lines):
                        if file_base.lower() in line.lower():
                            pass
                            # Get surrounding lines
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            purpose_description = '\n'.join(lines[start:end])
                            break
                
                result["purpose_match"] = purpose_match
                result["purpose_description"] = purpose_description
            
            # Check naming
            if check_naming:
                pass
                # Check if follows Python naming conventions
                file_name = Path(file_path).name
                naming_valid = file_name.islower() or '_' in file_name
                naming_issues = []
                
                if not naming_valid:
                    naming_issues.append("File name should be lowercase with underscores")
                if ' ' in file_name:
                    naming_issues.append("File name should not contain spaces")
                if file_name.startswith('_') and not file_name.startswith('__'):
                    naming_issues.append("Single underscore prefix indicates private module")
                
                result["naming_valid"] = naming_valid
                result["naming_issues"] = naming_issues
            
            # Check dependencies
            if check_dependencies:
                pass
                # Read file and check imports
                full_path = self.project_dir / file_path
                if full_path.exists():
                    try:
                        import ast
                        content = full_path.read_text()
                        tree = ast.parse(content)
                        
                        imports = []
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                imports.extend(n.name for n in node.names)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.append(node.module)
                        
                        # Check for problematic imports
                        dependency_issues = []
                        for imp in imports:
                            pass
                            # Check for circular dependencies (importing from parent)
                            if '..' in imp:
                                dependency_issues.append(f"Relative import may cause circular dependency: {imp}")
                            # Check for cross-layer imports
                            if 'core' in file_path and 'services' in imp:
                                dependency_issues.append(f"Core layer importing from services layer: {imp}")
                            if 'models' in file_path and ('services' in imp or 'api' in imp):
                                dependency_issues.append(f"Models importing from higher layers: {imp}")
                        
                        result["imports"] = imports[:20]  # Limit to 20
                        result["dependency_issues"] = dependency_issues
                        
                    except Exception as e:
                        result["dependency_check_error"] = str(e)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Cross reference file failed: {e}")
            return {
                "tool": "cross_reference_file",
                "success": False,
                "error": str(e)
            }
    
    def _handle_map_file_relationships(self, args: Dict) -> Dict:
        """Handle map_file_relationships tool - map all file relationships."""
        try:
            file_path = args['file_path']
            depth = args.get('depth', 2)
            find_similar = args.get('find_similar', True)
            analyze_usage = args.get('analyze_usage', True)
            
            self.logger.info(f"🗺️  Mapping relationships for {file_path}")
            
            import ast
            from pathlib import Path
            
            result = {
                "tool": "map_file_relationships",
                "success": True,
                "file_path": file_path
            }
            
            # Read the file
            full_path = self.project_dir / file_path
            if not full_path.exists():
                return {
                    "tool": "map_file_relationships",
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            content = full_path.read_text()
            
            # Parse and extract imports
            try:
                tree = ast.parse(content)
                
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(n.name for n in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                result["imports"] = list(set(imports))
                
                # Extract classes and functions
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                
                result["classes"] = classes
                result["functions"] = functions
                
            except SyntaxError as e:
                result["parse_error"] = str(e)
            
            # Find files that import this file
            if analyze_usage:
                imported_by = []
                file_stem = Path(file_path).stem
                
                # Search all Python files
                for py_file in self.project_dir.glob("**/*.py"):
                    if py_file == full_path:
                        continue
                    if '__pycache__' in str(py_file):
                        continue
                    
                    try:
                        other_content = py_file.read_text()
                        # Check if this file is imported
                        if file_stem in other_content or file_path.replace('/', '.').replace('.py', '') in other_content:
                            rel_path = py_file.relative_to(self.project_dir)
                            imported_by.append(str(rel_path))
                    except:
                        pass
                
                result["imported_by"] = imported_by[:20]  # Limit to 20
            
            # Find similar files
            if find_similar:
                similar_files = []
                file_name = Path(file_path).name
                file_stem = Path(file_path).stem
                
                # Search for files with similar names
                for py_file in self.project_dir.glob("**/*.py"):
                    if py_file == full_path:
                        continue
                    if '__pycache__' in str(py_file):
                        continue
                    
                    other_name = py_file.name
                    other_stem = py_file.stem
                    
                    # Check for similar names
                    if file_stem in other_stem or other_stem in file_stem:
                        rel_path = py_file.relative_to(self.project_dir)
                        
                        # Quick similarity check
                        try:
                            other_content = py_file.read_text()
                            other_tree = ast.parse(other_content)
                            
                            other_classes = [node.name for node in ast.walk(other_tree) if isinstance(node, ast.ClassDef)]
                            other_functions = [node.name for node in ast.walk(other_tree) if isinstance(node, ast.FunctionDef)]
                            
                            # Check for common classes
                            common_classes = set(classes) & set(other_classes)
                            
                            similar_files.append({
                                "path": str(rel_path),
                                "common_classes": list(common_classes),
                                "reason": "Similar name and common classes" if common_classes else "Similar name"
                            })
                        except:
                            similar_files.append({
                                "path": str(rel_path),
                                "reason": "Similar name"
                            })
                
                result["similar_files"] = similar_files[:10]  # Limit to 10
            
            return result
            
        except Exception as e:
            self.logger.error(f"Map file relationships failed: {e}")
            return {
                "tool": "map_file_relationships",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_all_related_files(self, args: Dict) -> Dict:
        """Handle find_all_related_files tool - find all files related to a file or pattern."""
        try:
            file_path = args.get('file_path')
            pattern = args.get('pattern')
            include_similar_names = args.get('include_similar_names', True)
            include_same_class = args.get('include_same_class', True)
            include_importers = args.get('include_importers', True)
            include_imported = args.get('include_imported', True)
            
            if not file_path and not pattern:
                return {
                    "tool": "find_all_related_files",
                    "success": False,
                    "error": "Either file_path or pattern must be provided"
                }
            
            
            import ast
            from pathlib import Path
            
            related_files = []
            
            # Determine search term
            if file_path:
                search_term = Path(file_path).stem
                base_file = self.project_dir / file_path
            else:
                search_term = pattern.replace('*', '').replace('_', '')
                base_file = None
            
            # Search all Python files
            for py_file in self.project_dir.glob("**/*.py"):
                if '__pycache__' in str(py_file):
                    continue
                if base_file and py_file == base_file:
                    continue
                
                rel_path = py_file.relative_to(self.project_dir)
                reasons = []
                
                # Check similar names
                if include_similar_names:
                    if search_term.lower() in py_file.stem.lower():
                        reasons.append("Similar name")
                
                # Check for same class names
                if include_same_class and base_file and base_file.exists():
                    try:
                        base_content = base_file.read_text()
                        base_tree = ast.parse(base_content)
                        base_classes = {node.name for node in ast.walk(base_tree) if isinstance(node, ast.ClassDef)}
                        
                        other_content = py_file.read_text()
                        other_tree = ast.parse(other_content)
                        other_classes = {node.name for node in ast.walk(other_tree) if isinstance(node, ast.ClassDef)}
                        
                        common = base_classes & other_classes
                        if common:
                            reasons.append(f"Defines same classes: {', '.join(common)}")
                    except:
                        pass
                
                # Check if imports base file
                if include_importers and file_path:
                    try:
                        other_content = py_file.read_text()
                        if search_term in other_content or file_path.replace('/', '.').replace('.py', '') in other_content:
                            reasons.append("Imports this file")
                    except:
                        pass
                
                # Check if imported by base file
                if include_imported and base_file and base_file.exists():
                    try:
                        base_content = base_file.read_text()
                        other_stem = py_file.stem
                        if other_stem in base_content or str(rel_path).replace('/', '.').replace('.py', '') in base_content:
                            reasons.append("Imported by this file")
                    except:
                        pass
                
                if reasons:
                    related_files.append({
                        "path": str(rel_path),
                        "reasons": reasons
                    })
            
            
            return {
                "tool": "find_all_related_files",
                "success": True,
                "search_term": file_path or pattern,
                "total_related": len(related_files),
                "related_files": related_files
            }
            
        except Exception as e:
            self.logger.error(f"Find all related files failed: {e}")
            return {
                "tool": "find_all_related_files",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_file_purpose(self, args: Dict) -> Dict:
        """Handle analyze_file_purpose tool - deeply analyze file purpose."""
        try:
            file_path = args['file_path']
            extract_classes = args.get('extract_classes', True)
            extract_functions = args.get('extract_functions', True)
            extract_imports = args.get('extract_imports', True)
            analyze_complexity = args.get('analyze_complexity', True)
            extract_docstrings = args.get('extract_docstrings', True)
            
            self.logger.info(f"🔬 Analyzing purpose of {file_path}")
            
            import ast
            
            full_path = self.project_dir / file_path
            if not full_path.exists():
                return {
                    "tool": "analyze_file_purpose",
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            content = full_path.read_text()
            
            result = {
                "tool": "analyze_file_purpose",
                "success": True,
                "file_path": file_path,
                "size": len(content),
                "lines": len(content.split('\n'))
            }
            
            try:
                tree = ast.parse(content)
                
                # Extract module docstring
                if extract_docstrings:
                    module_doc = ast.get_docstring(tree)
                    result["module_docstring"] = module_doc
                
                # Extract classes
                if extract_classes:
                    classes = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_info = {
                                "name": node.name,
                                "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                                "docstring": ast.get_docstring(node) if extract_docstrings else None
                            }
                            classes.append(class_info)
                    result["classes"] = classes
                
                # Extract functions
                if extract_functions:
                    functions = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree) if node in getattr(p, 'body', [])):
                            func_info = {
                                "name": node.name,
                                "args": [arg.arg for arg in node.args.args],
                                "docstring": ast.get_docstring(node) if extract_docstrings else None
                            }
                            functions.append(func_info)
                    result["functions"] = functions[:20]  # Limit to 20
                
                # Extract imports
                if extract_imports:
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            imports.extend(n.name for n in node.names)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                    result["imports"] = list(set(imports))
                
                # Analyze complexity
                if analyze_complexity:
                    pass
                    # Count total nodes as rough complexity measure
                    total_nodes = sum(1 for _ in ast.walk(tree))
                    result["complexity_score"] = total_nodes
                    result["complexity_level"] = "high" if total_nodes > 500 else "medium" if total_nodes > 200 else "low"
                
            except SyntaxError as e:
                result["parse_error"] = str(e)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Analyze file purpose failed: {e}")
            return {
                "tool": "analyze_file_purpose",
                "success": False,
                "error": str(e)
            }
    
    def _handle_compare_multiple_files(self, args: Dict) -> Dict:
        """Handle compare_multiple_files tool - compare 3+ files."""
        try:
            file_paths = args['file_paths']
            compare_structure = args.get('compare_structure', True)
            compare_functionality = args.get('compare_functionality', True)
            compare_quality = args.get('compare_quality', True)
            recommend_action = args.get('recommend_action', True)
            
            if len(file_paths) < 2:
                return {
                    "tool": "compare_multiple_files",
                    "success": False,
                    "error": "At least 2 files required for comparison"
                }
            
            self.logger.info(f"⚖️  Comparing {len(file_paths)} files")
            
            import ast
            
            files_data = []
            
            # Analyze each file
            for file_path in file_paths:
                full_path = self.project_dir / file_path
                if not full_path.exists():
                    continue
                
                try:
                    content = full_path.read_text()
                    tree = ast.parse(content)
                    
                    file_data = {
                        "path": file_path,
                        "size": len(content),
                        "lines": len(content.split('\n')),
                        "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)],
                        "functions": [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)],
                        "imports": [],
                        "has_docstrings": bool(ast.get_docstring(tree)),
                        "has_type_hints": any('->') in content  # Rough check
                    }
                    
                    # Extract imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            file_data["imports"].extend(n.name for n in node.names)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                file_data["imports"].append(node.module)
                    
                    files_data.append(file_data)
                    
                except Exception as e:
                    files_data.append({
                        "path": file_path,
                        "error": str(e)
                    })
            
            result = {
                "tool": "compare_multiple_files",
                "success": True,
                "files_compared": len(files_data),
                "files": files_data
            }
            
            # Compare structure
            if compare_structure:
                all_classes = set()
                all_functions = set()
                
                for fd in files_data:
                    if "classes" in fd:
                        all_classes.update(fd["classes"])
                    if "functions" in fd:
                        all_functions.update(fd["functions"])
                
                # Find common elements
                common_classes = set.intersection(*[set(fd.get("classes", [])) for fd in files_data if "classes" in fd])
                common_functions = set.intersection(*[set(fd.get("functions", [])) for fd in files_data if "functions" in fd])
                
                result["common_classes"] = list(common_classes)
                result["common_functions"] = list(common_functions)
                result["total_unique_classes"] = len(all_classes)
                result["total_unique_functions"] = len(all_functions)
            
            # Compare quality
            if compare_quality:
                quality_scores = []
                for fd in files_data:
                    if "error" in fd:
                        continue
                    
                    score = 0
                    if fd.get("has_docstrings"):
                        score += 1
                    if fd.get("has_type_hints"):
                        score += 1
                    if len(fd.get("classes", [])) > 0:
                        score += 1
                    
                    quality_scores.append({
                        "file": fd["path"],
                        "score": score,
                        "has_docstrings": fd.get("has_docstrings", False),
                        "has_type_hints": fd.get("has_type_hints", False)
                    })
                
                result["quality_scores"] = quality_scores
                
                # Find best quality file
                if quality_scores:
                    best = max(quality_scores, key=lambda x: x["score"])
                    result["best_quality_file"] = best["file"]
            
            # Recommend action
            if recommend_action:
                recommendations = []
                
                # Check if files are very similar
                if common_classes and len(common_classes) > 2:
                    recommendations.append("Files have many common classes - consider merging")
                
                # Check if one file is clearly better
                if compare_quality and quality_scores:
                    scores = [qs["score"] for qs in quality_scores]
                    if max(scores) > min(scores) + 1:
                        recommendations.append(f"File {result['best_quality_file']} has better quality - consider using as base for merge")
                
                # Check if files are completely different
                if not common_classes and not common_functions:
                    recommendations.append("Files have no common elements - likely serve different purposes, keep both")
                
                result["recommendations"] = recommendations
            
            return result
            
        except Exception as e:
            self.logger.error(f"Compare multiple files failed: {e}")
            return {
                "tool": "compare_multiple_files",
                "success": False,
                "error": str(e)
            }
    # =========================================================================
    # ON-DEMAND ANALYSIS TOOL HANDLERS
    # =========================================================================
    
    def _handle_analyze_complexity_on_demand(self, args: Dict) -> Dict:
        """Handle on-demand complexity analysis with flexible scope"""
        try:
            from .tool_modules.analysis_tools import analyze_complexity
            
            project_dir = str(self.project_dir)
            filepath = args.get('filepath')
            directory = args.get('directory')
            
            result = analyze_complexity(project_dir, filepath, directory)
            
            return {
                "tool": "analyze_complexity",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            return {
                "tool": "analyze_complexity",
                "success": False,
                "error": str(e)
            }
    
    def _handle_analyze_call_graph_on_demand(self, args: Dict) -> Dict:
        """Handle on-demand call graph analysis with flexible scope"""
        try:
            from .tool_modules.analysis_tools import analyze_call_graph
            
            project_dir = str(self.project_dir)
            filepath = args.get('filepath')
            directory = args.get('directory')
            
            result = analyze_call_graph(project_dir, filepath, directory)
            
            return {
                "tool": "analyze_call_graph",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Call graph analysis failed: {e}")
            return {
                "tool": "analyze_call_graph",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_dead_code_on_demand(self, args: Dict) -> Dict:
        """Handle on-demand dead code detection with flexible scope"""
        try:
            from .tool_modules.analysis_tools import detect_dead_code
            
            project_dir = str(self.project_dir)
            filepath = args.get('filepath')
            directory = args.get('directory')
            
            result = detect_dead_code(project_dir, filepath, directory)
            
            return {
                "tool": "detect_dead_code",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Dead code detection failed: {e}")
            return {
                "tool": "detect_dead_code",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_integration_gaps_on_demand(self, args: Dict) -> Dict:
        """Handle on-demand integration gap finding with flexible scope"""
        try:
            from .tool_modules.analysis_tools import find_integration_gaps
            
            project_dir = str(self.project_dir)
            directory = args.get('directory')
            
            result = find_integration_gaps(project_dir, directory)
            
            return {
                "tool": "find_integration_gaps",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Integration gap finding failed: {e}")
            return {
                "tool": "find_integration_gaps",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_integration_conflicts_on_demand(self, args: Dict) -> Dict:
        """Handle on-demand integration conflict detection"""
        try:
            from .tool_modules.analysis_tools import find_integration_conflicts
            
            project_dir = str(self.project_dir)
            
            result = find_integration_conflicts(project_dir)
            
            return {
                "tool": "find_integration_conflicts",
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Integration conflict detection failed: {e}")
            return {
                "tool": "find_integration_conflicts",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_similar_files(self, args: Dict) -> Dict:
        """Handle find_similar_files tool call with comprehensive analysis"""
        try:
            from .comprehensive_similarity import ComprehensiveSimilarityAnalyzer
            
            analyzer = ComprehensiveSimilarityAnalyzer(self.project_dir, self.logger)
            
            target_file = args.get('target_file')
            threshold = args.get('similarity_threshold', 0.3)  # Lower threshold for comprehensive analysis
            
            similar = analyzer.find_similar_files(target_file, threshold)
            
            result = {
                "tool": "find_similar_files",
                "success": True,
                "similar_files": similar,
                "count": len(similar),
                "analysis_type": "comprehensive"
            }
            
            # Add clear guidance message with detailed analysis
            if len(similar) == 0:
                result["message"] = f"✅ No similar files found for '{target_file}'. Safe to proceed with file creation."
                result["next_action"] = "You should now create the file using create_python_file tool."
                result["analysis_summary"] = "Analyzed naming, structure, imports, patterns, and behavior. No conflicts detected."
            else:
                # Categorize similarities
                high_similarity = [f for f in similar if f['similarity'] > 0.7]
                medium_similarity = [f for f in similar if 0.4 <= f['similarity'] <= 0.7]
                low_similarity = [f for f in similar if f['similarity'] < 0.4]
                
                result["message"] = f"⚠️ Found {len(similar)} similar file(s): {len(high_similarity)} high, {len(medium_similarity)} medium, {len(low_similarity)} low similarity."
                result["next_action"] = "Review the similar files and their similarity breakdown before deciding."
                result["analysis_summary"] = {
                    "high_similarity_files": [f['path'] for f in high_similarity],
                    "medium_similarity_files": [f['path'] for f in medium_similarity],
                    "low_similarity_files": [f['path'] for f in low_similarity],
                    "recommendation": self._generate_similarity_recommendation(high_similarity, medium_similarity, target_file)
                }
            
            return result
        except Exception as e:
            self.logger.error(f"Find similar files failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "tool": "find_similar_files",
                "success": False,
                "error": str(e)
            }
    
    def _generate_similarity_recommendation(self, high_sim: List, medium_sim: List, target_file: str) -> str:
        """Generate recommendation based on similarity analysis."""
        if len(high_sim) > 0:
            return f"HIGH SIMILARITY DETECTED: Consider modifying '{high_sim[0]['path']}' instead of creating '{target_file}'. The files share similar classes, functions, and patterns."
        elif len(medium_sim) > 0:
            return f"MEDIUM SIMILARITY: '{medium_sim[0]['path']}' has some overlap with '{target_file}'. Review to avoid duplication."
        else:
            return f"LOW SIMILARITY: Safe to create '{target_file}' as a new file."
    
    def _handle_validate_filename(self, args: Dict) -> Dict:
        """Handle validate_filename tool call"""
        try:
            from .naming_conventions import NamingConventionManager
            
            conventions = NamingConventionManager(self.project_dir, self.logger)
            
            filename = args.get('filename')
            validation = conventions.validate_filename(filename)
            
            return {
                "tool": "validate_filename",
                "success": True,
                "validation": validation
            }
        except Exception as e:
            self.logger.error(f"Validate filename failed: {e}")
            return {
                "tool": "validate_filename",
                "success": False,
                "error": str(e)
            }
    
    def _handle_compare_files(self, args: Dict) -> Dict:
        """Handle compare_files tool call"""
        try:
            from .file_conflict_resolver import FileConflictResolver
            from .file_discovery import FileDiscovery
            
            discovery = FileDiscovery(self.project_dir, self.logger)
            resolver = FileConflictResolver(self.project_dir, self.logger, discovery)
            
            files = args.get('files', [])
            comparison = resolver.compare_files(files)
            
            return {
                "tool": "compare_files",
                "success": True,
                "comparison": comparison
            }
        except Exception as e:
            self.logger.error(f"Compare files failed: {e}")
            return {
                "tool": "compare_files",
                "success": False,
                "error": str(e)
            }
    
    def _handle_find_all_conflicts(self, args: Dict) -> Dict:
        """Handle find_all_conflicts tool call"""
        try:
            from .file_discovery import FileDiscovery
            
            discovery = FileDiscovery(self.project_dir, self.logger)
            conflicts = discovery.find_conflicting_files()
            
            # Filter by severity
            min_severity = args.get('min_severity', 'medium')
            severity_order = {'low': 0, 'medium': 1, 'high': 2}
            min_level = severity_order.get(min_severity, 1)
            
            filtered_conflicts = [
                c for c in conflicts 
                if severity_order.get(c['severity'], 0) >= min_level
            ]
            
            return {
                "tool": "find_all_conflicts",
                "success": True,
                "conflicts": filtered_conflicts,
                "total_count": len(conflicts),
                "filtered_count": len(filtered_conflicts)
            }
        except Exception as e:
            self.logger.error(f"Find all conflicts failed: {e}")
            return {
                "tool": "find_all_conflicts",
                "success": False,
                "error": str(e)
            }
    
    def _handle_archive_file(self, args: Dict) -> Dict:
        """Handle archive_file tool call"""
        try:
            from pathlib import Path
            import shutil
            from datetime import datetime
            
            filepath = args.get('filepath')
            reason = args.get('reason', 'No reason provided')
            
            source = self.project_dir / filepath
            if not source.exists():
                return {
                    "tool": "archive_file",
                    "success": False,
                    "error": f"File not found: {filepath}"
                }
            
            # Create archive directory
            archive_dir = self.project_dir / "archive" / "deprecated"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Preserve directory structure
            rel_path = Path(filepath)
            dest = archive_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_with_timestamp = dest.parent / f"{dest.stem}_{timestamp}{dest.suffix}"
            
            # Move file
            shutil.move(str(source), str(dest_with_timestamp))
            
            # Create README in archive
            readme = archive_dir / "README.md"
            with open(readme, 'a') as f:
                f.write(f"\n## {filepath}\n")
                f.write(f"- **Archived:** {datetime.now().isoformat()}\n")
                f.write(f"- **Reason:** {reason}\n")
                f.write(f"- **Location:** {dest_with_timestamp.relative_to(archive_dir)}\n")
            
            return {
                "tool": "archive_file",
                "success": True,
                "archived_to": str(dest_with_timestamp.relative_to(self.project_dir)),
                "reason": reason
            }
        except Exception as e:
            self.logger.error(f"Archive file failed: {e}")
            return {
                "tool": "archive_file",
                "success": False,
                "error": str(e)
            }
    
    def _handle_detect_naming_violations(self, args: Dict) -> Dict:
        """Handle detect_naming_violations tool call"""
        try:
            from .naming_conventions import NamingConventionManager
            
            conventions = NamingConventionManager(self.project_dir, self.logger)
            
            directory = args.get('directory', '.')
            search_dir = self.project_dir / directory
            
            violations = []
            
            # Find all Python files
            for py_file in search_dir.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                rel_path = str(py_file.relative_to(self.project_dir))
                validation = conventions.validate_filename(rel_path)
                
                if not validation['valid']:
                    violations.append({
                        'file': rel_path,
                        'issues': validation['issues'],
                        'suggestions': validation['suggestions']
                    })
            
            return {
                "tool": "detect_naming_violations",
                "success": True,
                "violations": violations,
                "count": len(violations)
            }
        except Exception as e:
            self.logger.error(f"Detect naming violations failed: {e}")
            return {
                "tool": "detect_naming_violations",
                "success": False,
                "error": str(e)
            }
