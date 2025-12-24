"""
Tool Call Handlers

Executes tool calls and manages side effects (file creation, etc.)
"""

import json
from typing import Dict, List, Callable
from pathlib import Path

from .logging_setup import get_logger
from .utils import validate_python_syntax


class ToolCallHandler:
    """Handles execution of tool calls from LLM responses"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.logger = get_logger()
        
        # Track results
        self.files_created: List[str] = []
        self.files_modified: List[str] = []
        self.issues: List[Dict] = []
        self.approved: List[str] = []
        self.tasks: List[Dict] = []
        
        # Detailed error info for debugging
        self.errors: List[Dict] = []
        
        # Tool handlers
        self._handlers: Dict[str, Callable] = {
            "create_python_file": self._handle_create_file,
            "create_file": self._handle_create_file,  # Alias
            "modify_python_file": self._handle_modify_file,
            "modify_file": self._handle_modify_file,  # Alias
            "report_issue": self._handle_report_issue,
            "approve_code": self._handle_approve_code,
            "create_task_plan": self._handle_create_plan,
        }
    
    def reset(self):
        """Reset tracking state"""
        self.files_created = []
        self.files_modified = []
        self.issues = []
        self.approved = []
        self.tasks = []
        self.errors = []
    
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
        
        full_path.write_text(new_content)
        self.files_modified.append(filepath)
        self.logger.info(f"  ✏️ Modified: {filepath}")
        
        return {"tool": "modify_file", "success": True, "filepath": filepath}
    
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
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors for debugging"""
        if not self.errors:
            return ""
        
        lines = ["Errors encountered:"]
        for err in self.errors:
            lines.append(f"  - [{err.get('tool')}] {err.get('filepath', '')}: {err.get('error', '')}")
        return "\n".join(lines)
