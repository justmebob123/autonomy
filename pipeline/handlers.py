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


class ToolCallHandler:
    """Handles execution of tool calls from LLM responses"""
    
    def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None):
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
            # Monitoring tools
            "get_memory_profile": self._handle_get_memory_profile,
            "get_cpu_profile": self._handle_get_cpu_profile,
            "inspect_process": self._handle_inspect_process,
            "get_system_resources": self._handle_get_system_resources,
            "show_process_tree": self._handle_show_process_tree,
        }
    
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
        if tool_name == 'modify_python_file':
            file_path = args.get('file_path', 'unknown')
            operation = args.get('operation', 'unknown')
            
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
            file_path = args.get('file_path', 'unknown')
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
            return {"tool": name, "success": False, "error": f"Unknown tool: {name}"}
        
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
        
        if original not in content:
            self.logger.warning(f"  ⚠️ Original code not found in {filepath}")
            # Try to find similar code
            similar = self._find_similar_code(content, original)
            error_msg = "Original code not found in file"
            if similar:
                error_msg += f". Did you mean:\n{similar[:200]}"
            return {
                "tool": "modify_file", 
                "success": False,
                "error": error_msg,
                "filepath": filepath
            }
        
        new_content = content.replace(original, new_code, 1)
        
        # Validate Python syntax
        if filepath.endswith('.py'):
            valid, error = validate_python_syntax(new_content)
            if not valid:
                return {
                    "tool": "modify_file", 
                    "success": False,
                    "error": f"Modified code has syntax error: {error}",
                    "filepath": filepath,
                    "error_type": "syntax_error"
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
            
            # 3. Verify the change actually occurred
            if original in written_content:
                verification_errors.append("Original code still present - change may not have applied")
                verification_passed = False
            
            if new_code not in written_content:
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
            self.logger.error(f"  ❌ Post-fix verification FAILED:")
            for err in verification_errors:
                self.logger.error(f"     - {err}")
            
            # Attempt rollback if we have a patch
            if patch_content and 'patch_path' in locals():
                self.logger.warning(f"  🔄 Attempting rollback using patch...")
                try:
                    # Restore original content
                    full_path.write_text(content)
                    self.logger.info(f"  ✅ Rollback successful - file restored to original state")
                    return {
                        "tool": "modify_file",
                        "success": False,
                        "error": "Post-fix verification failed: " + "; ".join(verification_errors),
                        "filepath": filepath,
                        "rolled_back": True
                    }
                except Exception as rollback_error:
                    self.logger.error(f"  ❌ Rollback failed: {rollback_error}")
                    return {
                        "tool": "modify_file",
                        "success": False,
                        "error": "Post-fix verification failed AND rollback failed: " + "; ".join(verification_errors),
                        "filepath": filepath,
                        "rolled_back": False
                    }
            else:
                return {
                    "tool": "modify_file",
                    "success": False,
                    "error": "Post-fix verification failed: " + "; ".join(verification_errors),
                    "filepath": filepath,
                    "rolled_back": False
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
                timeout=10
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
