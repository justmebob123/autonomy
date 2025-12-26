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


class ToolCallHandler:
    """Handles execution of tool calls from LLM responses"""
    
    def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None, tool_registry=None):
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
        
        # Tool handlers
        self._handlers: Dict[str, Callable] = {
            "create_python_file": self._handle_create_file,
            "create_file": self._handle_create_file,  # Alias
            "modify_python_file": self._handle_modify_file,
            "modify_file": self._handle_modify_file,  # Alias
            "report_issue": self._handle_report_issue,
            "approve_code": self._handle_approve_code,
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
        }
        
        # Register custom tools from registry (Integration Fix #1)
        if tool_registry:
            tool_registry.set_handler(self)
            self.logger.info(f"Registered {len(tool_registry.tools)} custom tools from ToolRegistry")
    
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
    
    def _execute_tool_call(self, call: Dict) -> Dict:
        """Execute a single tool call"""
        func = call.get("function", {})
        name = func.get("name", "unknown")
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
            self.logger.warning(f"Unknown tool: {name}")
            return {
                "tool": name,
                "success": False,
                "error": "unknown_tool",
                "error_type": "unknown_tool",
                "tool_name": name,
                "message": f"Unknown tool: {name}",
                "args": args  # Include for context
            }
        
        try:
            return handler(args)
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
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
        filepath = args.get("filepath", args.get("path", ""))
        code = args.get("code", args.get("content", ""))
        
        if not filepath:
            return {"tool": "create_file", "success": False, "error": "Missing filepath"}
        if not code:
            return {"tool": "create_file", "success": False, "error": "Missing code/content"}
        
        # CRITICAL: Normalize path to prevent absolute path issues
        filepath = self._normalize_filepath(filepath)
        
        if not filepath:
            return {"tool": "create_file", "success": False, "error": "Invalid filepath after normalization"}
        
        # Validate Python syntax
        if filepath.endswith('.py'):
            valid, error = validate_python_syntax(code)
            if not valid:
                self.logger.warning(f"  ⚠️ Syntax error in {filepath}: {error}")
                return {
                    "tool": "create_file", 
                    "success": False,
                    "error": f"Syntax error: {error}", 
                    "filepath": filepath,
                    "error_type": "syntax_error"
                }
        
        # Create directory and file
        full_path = self.project_dir / filepath
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(code)
            self.files_created.append(filepath)
            self.logger.info(f"  📝 Created: {filepath} ({len(code)} bytes)")
            
            return {
                "tool": "create_file", 
                "success": True,
                "filepath": filepath, 
                "size": len(code)
            }
        except PermissionError as e:
            self.logger.error(f"  ✗ Permission denied for {filepath}: {e}")
            return {
                "tool": "create_file", 
                "success": False,
                "error": f"Permission denied: {filepath}", 
                "filepath": filepath
            }
        except Exception as e:
            self.logger.error(f"  ✗ Failed to write {filepath}: {e}")
            return {
                "tool": "create_file", 
                "success": False,
                "error": str(e), 
                "filepath": filepath
            }
    
    def _handle_modify_file(self, args: Dict) -> Dict:
        """Handle modify_python_file / modify_file tool"""
        filepath = args.get("filepath", args.get("path", ""))
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
