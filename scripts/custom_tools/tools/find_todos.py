#!/usr/bin/env python3
"""
FindTodos - Find TODO comments in code

Scans Python files for TODO, FIXME, HACK, and NOTE comments.
"""

from pathlib import Path
import re
from core.base import BaseTool, ToolResult


class FindTodos(BaseTool):
    """Find TODO, FIXME, HACK, and NOTE comments in Python files."""
    
    # Tool metadata
    name = "find_todos"
    description = "Find TODO, FIXME, HACK, and NOTE comments in Python files"
    version = "1.0.0"
    category = "analysis"
    author = "NinjaTech AI"
    
    # Security settings
    requires_filesystem = True
    requires_network = False
    requires_subprocess = False
    timeout_seconds = 30
    max_file_size_mb = 10
    
    def execute(self, filepath: str = None, directory: str = None) -> ToolResult:
        """
        Execute TODO search.
        
        Args:
            filepath: Path to single Python file (optional)
            directory: Path to directory to scan (optional)
            
        Returns:
            ToolResult with found TODOs
        """
        try:
            todos = []
            
            if filepath:
                # Scan single file
                full_path = self.project_dir / filepath
                if not full_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found: {filepath}"
                    )
                todos.extend(self._scan_file(full_path, filepath))
                
            elif directory:
                # Scan directory
                dir_path = self.project_dir / directory
                if not dir_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"Directory not found: {directory}"
                    )
                
                for py_file in dir_path.rglob('*.py'):
                    rel_path = py_file.relative_to(self.project_dir)
                    todos.extend(self._scan_file(py_file, str(rel_path)))
            else:
                # Scan entire project
                for py_file in self.project_dir.rglob('*.py'):
                    # Skip venv, .git, etc.
                    if any(part.startswith('.') or part == 'venv' for part in py_file.parts):
                        continue
                    rel_path = py_file.relative_to(self.project_dir)
                    todos.extend(self._scan_file(py_file, str(rel_path)))
            
            # Group by type
            by_type = {}
            for todo in todos:
                todo_type = todo['type']
                if todo_type not in by_type:
                    by_type[todo_type] = []
                by_type[todo_type].append(todo)
            
            # Return result
            return ToolResult(
                success=True,
                result={
                    'total_todos': len(todos),
                    'by_type': {k: len(v) for k, v in by_type.items()},
                    'todos': todos
                },
                metadata={
                    'scanned': 'file' if filepath else 'directory' if directory else 'project'
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"TODO search failed: {e}"
            )
    
    def _scan_file(self, filepath: Path, rel_path: str) -> list:
        """Scan a file for TODO comments."""
        todos = []
        
        try:
            content = filepath.read_text()
            lines = content.splitlines()
            
            # Patterns to match
            patterns = {
                'TODO': re.compile(r'#\s*TODO[:\s]+(.+)', re.IGNORECASE),
                'FIXME': re.compile(r'#\s*FIXME[:\s]+(.+)', re.IGNORECASE),
                'HACK': re.compile(r'#\s*HACK[:\s]+(.+)', re.IGNORECASE),
                'NOTE': re.compile(r'#\s*NOTE[:\s]+(.+)', re.IGNORECASE),
            }
            
            for line_num, line in enumerate(lines, 1):
                for todo_type, pattern in patterns.items():
                    match = pattern.search(line)
                    if match:
                        todos.append({
                            'type': todo_type,
                            'filepath': rel_path,
                            'line': line_num,
                            'text': match.group(1).strip(),
                            'full_line': line.strip()
                        })
        
        except Exception:
            pass  # Skip files that can't be read
        
        return todos


# CLI interface for subprocess execution
if __name__ == '__main__':
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-dir', required=True)
    parser.add_argument('--args', required=True)
    args = parser.parse_args()
    
    # Parse arguments
    tool_args = json.loads(args.args)
    
    # Create and run tool
    tool = FindTodos(args.project_dir)
    result = tool.run(**tool_args)
    
    # Output result as JSON
    print(json.dumps(result.to_dict()))
    sys.exit(0 if result.success else 1)