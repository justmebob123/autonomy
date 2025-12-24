"""
Code Context

Provides code diffs, history, and related file context for LLM prompts.
"""

import difflib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from ..logging_setup import get_logger


@dataclass
class CodeDiff:
    """Represents a diff between two versions of code"""
    filepath: str
    old_content: str
    new_content: str
    timestamp: str = ""
    description: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def get_unified_diff(self, context_lines: int = 3) -> str:
        """Get unified diff format"""
        old_lines = self.old_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{self.filepath}",
            tofile=f"b/{self.filepath}",
            n=context_lines
        )
        
        return "".join(diff)
    
    def get_side_by_side(self, width: int = 80) -> str:
        """Get side-by-side diff"""
        old_lines = self.old_content.splitlines()
        new_lines = self.new_content.splitlines()
        
        diff = difflib.HtmlDiff()
        # Use text format instead
        differ = difflib.Differ()
        result = list(differ.compare(old_lines, new_lines))
        
        return "\n".join(result)
    
    def get_changed_lines(self) -> Tuple[List[int], List[int]]:
        """Get line numbers that changed (removed, added)"""
        old_lines = self.old_content.splitlines()
        new_lines = self.new_content.splitlines()
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        removed = []
        added = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                removed.extend(range(i1 + 1, i2 + 1))
            elif tag == 'insert':
                added.extend(range(j1 + 1, j2 + 1))
            elif tag == 'replace':
                removed.extend(range(i1 + 1, i2 + 1))
                added.extend(range(j1 + 1, j2 + 1))
        
        return removed, added
    
    def get_change_summary(self) -> str:
        """Get a summary of changes"""
        old_line_count = len(self.old_content.splitlines())
        new_line_count = len(self.new_content.splitlines())
        removed, added = self.get_changed_lines()
        
        return (f"Changes: {len(removed)} lines removed, {len(added)} lines added "
                f"({old_line_count} -> {new_line_count} total lines)")
    
    def format_for_llm(self, max_diff_lines: int = 50) -> str:
        """Format diff for LLM context"""
        diff = self.get_unified_diff()
        lines = diff.splitlines()
        
        if len(lines) > max_diff_lines:
            lines = lines[:max_diff_lines]
            lines.append(f"... ({len(diff.splitlines()) - max_diff_lines} more lines)")
        
        return "\n".join([
            f"=== DIFF: {self.filepath} ===",
            self.get_change_summary(),
            "",
            "\n".join(lines)
        ])


class CodeContext:
    """
    Manages code context for LLM prompts.
    
    Tracks file history, provides relevant context from related files,
    and manages code diffs for debugging.
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.logger = get_logger()
        
        # History of file versions
        self._history: Dict[str, List[Tuple[str, str]]] = {}  # filepath -> [(timestamp, content)]
        
        # Recent diffs
        self._diffs: List[CodeDiff] = []
        
        # Max versions to keep per file
        self.max_versions = 5
        self.max_diffs = 20
    
    def record_version(self, filepath: str, content: str):
        """Record a version of a file"""
        if filepath not in self._history:
            self._history[filepath] = []
        
        timestamp = datetime.now().isoformat()
        self._history[filepath].append((timestamp, content))
        
        # Trim history
        if len(self._history[filepath]) > self.max_versions:
            self._history[filepath] = self._history[filepath][-self.max_versions:]
    
    def get_previous_version(self, filepath: str, 
                              versions_back: int = 1) -> Optional[str]:
        """Get a previous version of a file"""
        if filepath not in self._history:
            return None
        
        history = self._history[filepath]
        if len(history) < versions_back + 1:
            return None
        
        return history[-(versions_back + 1)][1]
    
    def create_diff(self, filepath: str, old_content: str, 
                    new_content: str, description: str = "") -> CodeDiff:
        """Create and record a diff"""
        diff = CodeDiff(
            filepath=filepath,
            old_content=old_content,
            new_content=new_content,
            description=description
        )
        
        self._diffs.append(diff)
        
        # Trim diffs
        if len(self._diffs) > self.max_diffs:
            self._diffs = self._diffs[-self.max_diffs:]
        
        return diff
    
    def get_recent_diffs(self, filepath: str = None, 
                         count: int = 5) -> List[CodeDiff]:
        """Get recent diffs, optionally filtered by file"""
        diffs = self._diffs
        if filepath:
            diffs = [d for d in diffs if d.filepath == filepath]
        return diffs[-count:]
    
    def read_file(self, filepath: str) -> Optional[str]:
        """Read a file from the project"""
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return None
        try:
            return full_path.read_text()
        except IOError:
            return None
    
    def get_related_files(self, filepath: str, 
                          max_files: int = 3) -> List[Tuple[str, str]]:
        """Get related files based on imports and directory"""
        related = []
        content = self.read_file(filepath)
        
        if not content:
            return related
        
        # Parse imports
        import_files = self._extract_local_imports(content, filepath)
        
        for imp_file in import_files[:max_files]:
            imp_content = self.read_file(imp_file)
            if imp_content:
                related.append((imp_file, imp_content))
        
        # Add sibling files in same directory
        file_dir = Path(filepath).parent
        if file_dir != Path("."):
            for sibling in (self.project_dir / file_dir).glob("*.py"):
                sib_path = str(sibling.relative_to(self.project_dir))
                if sib_path != filepath and len(related) < max_files:
                    sib_content = self.read_file(sib_path)
                    if sib_content and (sib_path, sib_content) not in related:
                        related.append((sib_path, sib_content))
        
        return related[:max_files]
    
    def _extract_local_imports(self, content: str, 
                                current_file: str) -> List[str]:
        """Extract local import paths from code"""
        imports = []
        
        for line in content.splitlines():
            line = line.strip()
            
            # from .module import ...
            if line.startswith("from ."):
                parts = line.split()
                if len(parts) >= 2:
                    module = parts[1].lstrip(".")
                    if " import " in line:
                        module = module.split(" import")[0]
                    # Convert module path to file path
                    module_path = module.replace(".", "/") + ".py"
                    # Make relative to current file's directory
                    current_dir = str(Path(current_file).parent)
                    if current_dir != ".":
                        module_path = f"{current_dir}/{module_path}"
                    imports.append(module_path)
            
            # from module import ... (check if local)
            elif line.startswith("from ") and " import " in line:
                parts = line.split()
                if len(parts) >= 2:
                    module = parts[1]
                    if not module.startswith(".") and "." not in module:
                        module_path = f"{module}.py"
                        if (self.project_dir / module_path).exists():
                            imports.append(module_path)
        
        return imports
    
    def get_context_for_task(self, target_file: str, 
                             task_description: str = "",
                             max_context_chars: int = 4000) -> str:
        """Build comprehensive context for a coding task"""
        lines = []
        total_chars = 0
        
        # Current file content (if exists)
        current_content = self.read_file(target_file)
        if current_content:
            lines.append(f"=== CURRENT FILE: {target_file} ===")
            lines.append(current_content)
            lines.append("")
            total_chars += len(current_content)
        
        # Related files
        related = self.get_related_files(target_file)
        for rel_path, rel_content in related:
            if total_chars + len(rel_content) < max_context_chars:
                lines.append(f"=== RELATED FILE: {rel_path} ===")
                lines.append(rel_content)
                lines.append("")
                total_chars += len(rel_content)
        
        # Recent changes to target file
        recent_diffs = self.get_recent_diffs(target_file, count=2)
        if recent_diffs:
            lines.append("=== RECENT CHANGES ===")
            for diff in recent_diffs:
                lines.append(diff.get_change_summary())
            lines.append("")
        
        return "\n".join(lines)
    
    def get_file_structure(self, directory: str = "") -> str:
        """Get file structure as tree"""
        base = self.project_dir / directory if directory else self.project_dir
        
        lines = []
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(self.project_dir)
            # Skip pycache
            if "__pycache__" in str(rel):
                continue
            depth = len(rel.parts) - 1
            indent = "  " * depth
            lines.append(f"{indent}{rel.name}")
        
        return "\n".join(lines)
    
    def clear_history(self, filepath: str = None):
        """Clear version history"""
        if filepath:
            if filepath in self._history:
                del self._history[filepath]
        else:
            self._history = {}
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return {
            "history": {
                k: [(t, c) for t, c in v]
                for k, v in self._history.items()
            },
            "diffs": [
                {
                    "filepath": d.filepath,
                    "old_content": d.old_content,
                    "new_content": d.new_content,
                    "timestamp": d.timestamp,
                    "description": d.description,
                }
                for d in self._diffs
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict, project_dir: Path) -> "CodeContext":
        """Deserialize from dict"""
        ctx = cls(project_dir)
        
        for filepath, versions in data.get("history", {}).items():
            ctx._history[filepath] = [(t, c) for t, c in versions]
        
        for diff_data in data.get("diffs", []):
            ctx._diffs.append(CodeDiff(**diff_data))
        
        return ctx
