"""
Tool Call Handlers

Executes tool calls and manages side effects (file creation, etc.)
"""

import json
from typing import Dict, List, Callable
from pathlib import Path

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
                 tool_registry=None, tool_creator=None, tool_validator=None):
        self.project_dir = Path(project_dir)
        self.logger = get_logger()
        self.verbose = verbose  # 0=normal, 1=verbose, 2=very verbose
        
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
        
        # INTEGRATION: Custom Tool Handler for scripts/custom_tools/
        # Initialize custom tool support
        self.custom_tool_handler = None
        try:
            from .custom_tools import ToolRegistry, CustomToolHandler
            custom_registry = ToolRegistry(str(self.project_dir))
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
            self.logger.warning(f"Custom tool handler initialization failed: {e}")
        
        # Tool handlers
        self._handlers: Dict[str, Callable] = {
            "create_python_file": self._handle_create_file,
            "create_file": self._handle_create_file,  # Alias
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
        }
        
        # Register custom tools from registry (Integration Fix #1)
        if tool_registry:
            tool_registry.set_handler(self)
            self.logger.info(f"Registered {len(tool_registry.tools)} custom tools from ToolRegistry")
        self.syntax_validator = SyntaxValidator()
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
            file_path = args.get('file_path', 'unknown')
            console_lines.append(f"✨ [AI Activity] Creating file: {file_path}")
            file_lines.append(f"[{activity['timestamp']}] CREATE: {file_path}")
            
            if self.verbose >= 1:
                content = args.get('content', '')
                if content:
                    console_lines.append(f"   └─ Content length: {len(content)} chars")
            
        else:
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
            # Try to infer tool name from arguments
            inferred_name = self._infer_tool_name_from_args(args)
            
            self.logger.warning(f"=" * 70)
            self.logger.warning(f"TOOL CALL: Empty tool name - inferring from arguments")
            self.logger.warning(f"=" * 70)
            self.logger.warning(f"Arguments: {json.dumps(args, indent=2)}")
            self.logger.warning(f"Inferred tool name: {inferred_name}")
            self.logger.warning(f"=" * 70)
            
            if inferred_name != "unknown":
                # Use inferred name and continue execution
                name = inferred_name
                func["name"] = name  # Update the function object
            else:
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
        
        self.logger.debug(f"Executing tool: {name}")
        
        handler = self._handlers.get(name)
        if not handler:
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
            self.logger.warning(f"⚠️  Coding phase attempted to create .md file: {filepath}")
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
        
        if not is_valid:
            self.logger.error(f"Syntax validation failed for {filepath}")
            self.logger.error(error_msg)
            return {
                "tool": "create_file",
                "success": False,
                "error": f"Syntax error: {error_msg}",
                "filepath": filepath
            }
        
        # Use fixed code if it was modified
        if fixed_code != code:
            self.logger.info(f"Using auto-fixed code for {filepath}")
            code = fixed_code
        
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
                        self.logger.warning(f"  ⚠️ Could not create {init_path}: {e}")
        
        # Create directory and file
        full_path = self.project_dir / filepath
        
        try:
            self.logger.debug(f"Creating directory: {full_path.parent}")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug(f"Writing file: {full_path} ({len(code)} bytes)")
            full_path.write_text(code)
            
            self.files_created.append(filepath)
            self.logger.info(f"  📝 Created: {filepath} ({len(code)} bytes)")
            
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
            return {"tool": "modify_file", "success": False, "error": "Missing filepath"}
        if not original:
            return {"tool": "modify_file", "success": False, "error": "Missing original_code"}
        if new_code is None:  # Allow empty string for deletions
            return {"tool": "modify_file", "success": False, "error": "Missing new_code"}
        
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
            # Try with normalized whitespace (strip leading/trailing, normalize internal)
            original_stripped = original.strip()
            
            # Try to find the code with any indentation
            found = False
            for line_num, line in enumerate(content.split('\n'), 1):
                if line.strip() == original_stripped:
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
                    self.logger.info(f"  ✓ Found code at line {line_num}, stripped {min_indent} spaces, applied {len(indent)} spaces indentation")
                    break
            
            if not found:
                # Try multi-line match with flexible whitespace
                original_lines = [l.strip() for l in original.strip().split('\n') if l.strip()]
                content_lines = content.split('\n')
                
                for i in range(len(content_lines) - len(original_lines) + 1):
                    # Check if this is a match
                    match = True
                    for j, orig_line in enumerate(original_lines):
                        if content_lines[i + j].strip() != orig_line:
                            match = False
                            break
                    
                    if match:
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
                        self.logger.info(f"  ✓ Found multi-line code at line {i+1}, stripped {min_indent} spaces, applied {len(indent)} spaces indentation")
                        break
                
                if not found:
                    self.logger.warning(f"  ⚠️ Original code not found in {filepath}")
                    
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
                    self.logger.info(f"  📄 Failure analysis saved: {report_path.name}")
                    
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
                        "failure_analysis": analysis,
                        "failure_report": str(report_path),
                        "ai_feedback": analysis["ai_feedback"]
                    }
        
        # Validate Python syntax
        if filepath.endswith('.py'):
            valid, error = validate_python_syntax(new_content)
            if not valid:
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
                self.logger.info(f"  📄 Syntax error analysis saved: {report_path.name}")
                
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
            self.logger.warning(f"  ⚠️  Could not save patch: {e}")
        
        # Validate syntax before writing
        is_valid, fixed_content, error_msg = self.syntax_validator.validate_and_fix(new_content, filepath)
        
        if not is_valid:
            self.logger.error(f"Syntax validation failed for modified {filepath}")
            self.logger.error(error_msg)
            return {
                "tool": "modify_file",
                "success": False,
                "error": f"Syntax error after modification: {error_msg}",
                "filepath": filepath
            }
        
        # Use fixed content if it was modified
        if fixed_content != new_content:
            self.logger.info(f"Using auto-fixed code for {filepath}")
            new_content = fixed_content
        
        full_path.write_text(new_content)
        
        # STAGE 1: Immediate Post-Fix Verification
        self.logger.info(f"  🔍 Verifying fix...")
        verification_passed = True
        verification_errors = []
        
        try:
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
                # For wrapping operations (try/except, if/else, etc.)
                # Just verify the new wrapped code was added
                if new_code_normalized not in written_normalized:
                    verification_errors.append("Wrapped code not found in file - wrapping operation may have failed")
                    verification_passed = False
            else:
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
            self.logger.warning(f"  ⚠️  Post-fix verification found issues:")
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
            self.logger.info(f"  📄 Verification analysis saved: {report_path.name}")
            
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
        
        self.logger.info(f"  ✅ Verification passed")
        self.files_modified.append(filepath)
        self.logger.info(f"  ✏️ Modified: {filepath}")
        
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
        filepath = args.get("filepath", "")
        
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
        
        self.logger.warning(f"  ⚠️ Issue [{issue['type']}] {issue['filepath']}: "
                           f"{issue['description'][:60] if issue['description'] else ''}")
        
        return {"tool": "report_issue", "success": True, "issue": issue}
    
    def _handle_approve_code(self, args: Dict) -> Dict:
        """Handle approve_code tool"""
        filepath = args.get("filepath", "")
        if not filepath:
            return {"tool": "approve_code", "success": False, "error": "Missing filepath"}
        
        # Normalize filepath
        filepath = self._normalize_filepath(filepath)
        
        self.approved.append(filepath)
        self.logger.info(f"  ✓ Approved: {filepath}")
        return {"tool": "approve_code", "success": True, "filepath": filepath}
    
    def _handle_mark_task_complete(self, args: Dict) -> Dict:
        """Handle mark_task_complete tool - explicitly marks task as complete without changes"""
        reason = args.get("reason", "File is already complete and correct")
        self.logger.info(f"  ✅ Task marked complete: {reason}")
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
        filepath = args.get("filepath", "")
        
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
        filepath = args.get("filepath")
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
        filepath = args.get("filepath")
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
        filepath = args.get("filepath")
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
        filepath = args.get("filepath")
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
        filepath = args.get("filepath")
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
        filepath = args.get("filepath")
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
        
        self.logger.info("  📊 Project Status Analysis:")
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
            
            self.logger.info(f"📊 Connectivity Analysis:")
            self.logger.info(f"   Connected: {result['connected_vertices']}/{result['total_vertices']} phases")
            self.logger.info(f"   Edges: {result['total_edges']}")
            self.logger.info(f"   Avg Reachability: {result['avg_reachability']:.1f} phases")
            
            if result['isolated_phases']:
                self.logger.warning(f"   Isolated: {', '.join(result['isolated_phases'])}")
            
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
                self.logger.info(f"   Total Points: {result['total_integration_points']}")
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
            
            if result['found']:
                self.logger.info(f"🌊 Variable Flow for '{variable_name}':")
                self.logger.info(f"   Flows through: {result['flows_through']} functions")
                self.logger.info(f"   Criticality: {result['criticality']}")
            
            return {
                "tool": "trace_variable_flow",
                "success": result['found'],
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
            self.logger.info(f"   Direct recursion: {result['total_recursive']} functions")
            self.logger.info(f"   Circular calls: {result['total_circular']} functions")
            
            if result['warning']:
                self.logger.warning("   ⚠️  High number of recursive patterns detected")
            
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
        filepath = args.get('filepath', '')
        
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
                self.logger.info(f"   Quality Score: {result['quality_score']:.1f}/100")
                self.logger.info(f"   Lines: {result['lines']}, Functions: {result['functions']}")
                self.logger.info(f"   Comment Ratio: {result['comment_ratio']:.1f}%")
            
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
            
            self.logger.info(f"🔍 Analyzing code complexity...")
            result = analyzer.analyze(target)
            
            # Generate report
            report = analyzer.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "COMPLEXITY_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Complexity analysis complete")
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
            
            self.logger.info(f"🔍 Detecting dead code...")
            result = detector.analyze(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "DEAD_CODE_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Dead code detection complete")
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
            
            self.logger.info(f"🔍 Finding integration gaps...")
            result = finder.analyze(target)
            
            # Generate report
            report = finder.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "INTEGRATION_GAP_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Integration gap analysis complete")
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
    
    def _handle_generate_call_graph(self, args: Dict) -> Dict:
        """Handle generate_call_graph tool."""
        try:
            from .analysis.call_graph import CallGraphGenerator
            
            generator = CallGraphGenerator(str(self.project_dir), self.logger)
            target = args.get('target')
            
            self.logger.info(f"🔍 Generating call graph...")
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
            
            self.logger.info(f"✅ Call graph generation complete")
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
            
            self.logger.info(f"🔍 Running deep recursive analysis...")
            
            # Run external script
            result = subprocess.run(
                [sys.executable, str(script_path), target],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Deep analysis complete")
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
            
            self.logger.info(f"🔍 Running advanced pattern analysis...")
            
            # Run external script
            result = subprocess.run(
                [sys.executable, str(script_path), target],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Advanced analysis complete")
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
            
            self.logger.info(f"🔍 Running unified analysis...")
            
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
                self.logger.info(f"✅ Unified analysis complete")
                
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
            filepath = args.get('filepath')
            content = args.get('content')
            ensure_newline = args.get('ensure_newline', True)
            
            self.logger.info(f"📝 Appending to file: {filepath}")
            result = file_tools.append_to_file(filepath, content, ensure_newline)
            
            if result['success']:
                self.logger.info(f"✅ Content appended to {filepath}")
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
            filepath = args.get('filepath')
            section_title = args.get('section_title')
            new_content = args.get('new_content')
            create_if_missing = args.get('create_if_missing', True)
            
            self.logger.info(f"📝 Updating section '{section_title}' in {filepath}")
            result = file_tools.update_section(filepath, section_title, new_content, create_if_missing)
            
            if result['success']:
                self.logger.info(f"✅ Section updated in {filepath}")
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
            filepath = args.get('filepath')
            marker = args.get('marker')
            content = args.get('content')
            first_occurrence = args.get('first_occurrence', True)
            
            self.logger.info(f"📝 Inserting content after marker in {filepath}")
            result = file_tools.insert_after(filepath, marker, content, first_occurrence)
            
            if result['success']:
                self.logger.info(f"✅ Content inserted in {filepath}")
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
            filepath = args.get('filepath')
            marker = args.get('marker')
            content = args.get('content')
            first_occurrence = args.get('first_occurrence', True)
            
            self.logger.info(f"📝 Inserting content before marker in {filepath}")
            result = file_tools.insert_before(filepath, marker, content, first_occurrence)
            
            if result['success']:
                self.logger.info(f"✅ Content inserted in {filepath}")
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
            filepath = args.get('filepath')
            start_marker = args.get('start_marker')
            end_marker = args.get('end_marker')
            new_content = args.get('new_content')
            include_markers = args.get('include_markers', False)
            
            self.logger.info(f"📝 Replacing content between markers in {filepath}")
            result = file_tools.replace_between(filepath, start_marker, end_marker, new_content, include_markers)
            
            if result['success']:
                self.logger.info(f"✅ Content replaced in {filepath}")
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
            
            self.logger.info(f"🔍 Detecting bugs in {target}...")
            result = detector.detect(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "BUG_DETECTION_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Bug detection complete")
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
            
            self.logger.info(f"🔍 Detecting anti-patterns in {target}...")
            result = detector.detect(target)
            
            # Generate report
            report = detector.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "ANTIPATTERN_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Anti-pattern detection complete")
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
            
            self.logger.info(f"🔍 Analyzing data flow in {target}...")
            result = analyzer.analyze(target)
            
            # Generate report
            report = analyzer.generate_report(result)
            
            # Save report to file
            report_file = self.project_dir / "DATAFLOW_REPORT.txt"
            report_file.write_text(report)
            
            self.logger.info(f"✅ Data flow analysis complete")
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
