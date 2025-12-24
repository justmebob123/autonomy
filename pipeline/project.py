"""
Project File Management
"""

from pathlib import Path
from typing import List, Optional

from .logging_setup import get_logger
from .utils import validate_python_syntax


class ProjectFiles:
    """Manages project file operations"""
    
    EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir).resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
    
    def read(self, filename: str) -> Optional[str]:
        filepath = self.project_dir / filename
        if not filepath.exists():
            return None
        try:
            return filepath.read_text()
        except Exception as e:
            self.logger.error(f"Error reading {filepath}: {e}")
            return None
    
    def write(self, filename: str, content: str, validate: bool = True) -> bool:
        filepath = self.project_dir / filename
        
        if validate and filename.endswith('.py'):
            valid, error = validate_python_syntax(content)
            if not valid:
                self.logger.warning(f"Syntax error in {filename}: {error}")
                return False
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            filepath.write_text(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing {filepath}: {e}")
            return False
    
    def exists(self, filename: str) -> bool:
        return (self.project_dir / filename).exists()
    
    def list_files(self, extensions: List[str] = None) -> List[Path]:
        if extensions is None:
            extensions = [".py", ".yaml", ".yml", ".json", ".md"]
        
        files = []
        for ext in extensions:
            for f in self.project_dir.rglob(f"*{ext}"):
                if not any(ex in f.parts for ex in self.EXCLUDE_DIRS):
                    files.append(f)
        return sorted(files)
    
    def get_context(self, max_files: int = 5, max_chars: int = 5000) -> str:
        files = self.list_files([".py"])[:max_files]
        parts = []
        total = 0
        
        for f in files:
            content = self.read(str(f.relative_to(self.project_dir)))
            if content and total + len(content) < max_chars:
                rel = f.relative_to(self.project_dir)
                parts.append(f"### {rel} ###\n{content}")
                total += len(content)
        
        return "\n\n".join(parts)
    
    def show_tree(self):
        files = self.list_files()
        self.logger.info("")
        self.logger.info(f"📁 PROJECT: {self.project_dir}")
        self.logger.info("─" * 50)
        
        if not files:
            self.logger.info("   (empty)")
        else:
            for f in files[:20]:
                rel = f.relative_to(self.project_dir)
                self.logger.info(f"   {rel} ({f.stat().st_size} bytes)")
            if len(files) > 20:
                self.logger.info(f"   ... and {len(files) - 20} more")
        
        self.logger.info("─" * 50)
