"""
File Tracker

Tracks file hashes and timestamps to detect changes.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..logging_setup import get_logger


class FileTracker:
    """Tracks file modifications using SHA256 hashes"""
    
    HASH_FILE = ".pipeline/file_hashes.json"
    EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pipeline"}
    TRACK_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".md", ".txt"}
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.hash_file = self.project_dir / self.HASH_FILE
        self.logger = get_logger()
        
        self._hashes: Dict[str, Dict] = {}
        self._load_hashes()
    
    def _load_hashes(self):
        """Load existing hashes from disk"""
        if self.hash_file.exists():
            try:
                self._hashes = json.loads(self.hash_file.read_text())
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load hashes: {e}")
                self._hashes = {}
    
    def _save_hashes(self):
        """Save hashes to disk"""
        self.hash_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.hash_file.write_text(json.dumps(self._hashes, indent=2))
        except IOError as e:
            self.logger.error(f"Failed to save hashes: {e}")
    
    @staticmethod
    def compute_hash(filepath: Path) -> str:
        """Compute SHA256 hash of a file"""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError:
            return ""
    
    def get_hash(self, filepath: str) -> Optional[str]:
        """Get stored hash for a file"""
        return self._hashes.get(filepath, {}).get("hash")
    
    def update_hash(self, filepath: str, content_hash: str = None) -> str:
        """Update hash for a file"""
        full_path = self.project_dir / filepath
        
        if content_hash is None:
            content_hash = self.compute_hash(full_path)
        
        now = datetime.now().isoformat()
        
        if filepath in self._hashes:
            old_hash = self._hashes[filepath]["hash"]
            if old_hash != content_hash:
                self._hashes[filepath]["previous_hash"] = old_hash
                self._hashes[filepath]["hash"] = content_hash
                self._hashes[filepath]["modified"] = now
        else:
            self._hashes[filepath] = {
                "hash": content_hash,
                "created": now,
                "modified": now,
            }
        
        self._save_hashes()
        return content_hash
    
    def has_changed(self, filepath: str) -> bool:
        """Check if a file has changed since last tracked"""
        full_path = self.project_dir / filepath
        
        if not full_path.exists():
            return filepath in self._hashes  # Deleted = changed
        
        stored = self.get_hash(filepath)
        if stored is None:
            return True  # New file = changed
        
        current = self.compute_hash(full_path)
        return current != stored
    
    def get_changed_files(self, filepaths: List[str] = None) -> List[str]:
        """Get list of files that have changed"""
        if filepaths is None:
            filepaths = list(self._hashes.keys())
        
        return [fp for fp in filepaths if self.has_changed(fp)]
    
    def get_new_files(self) -> List[str]:
        """Get files that exist but aren't tracked"""
        tracked = set(self._hashes.keys())
        existing = set(self._get_project_files())
        return list(existing - tracked)
    
    def get_deleted_files(self) -> List[str]:
        """Get files that are tracked but don't exist"""
        deleted = []
        for filepath in self._hashes:
            if not (self.project_dir / filepath).exists():
                deleted.append(filepath)
        return deleted
    
    def _get_project_files(self) -> List[str]:
        """Get all trackable files in project"""
        files = []
        for ext in self.TRACK_EXTENSIONS:
            for f in self.project_dir.rglob(f"*{ext}"):
                if not any(ex in f.parts for ex in self.EXCLUDE_DIRS):
                    files.append(str(f.relative_to(self.project_dir)))
        return files
    
    def scan_all(self) -> Dict[str, List[str]]:
        """Scan project and categorize all files"""
        result = {
            "new": [],
            "changed": [],
            "deleted": [],
            "unchanged": [],
        }
        
        existing_files = set(self._get_project_files())
        tracked_files = set(self._hashes.keys())
        
        # New files (exist but not tracked)
        result["new"] = list(existing_files - tracked_files)
        
        # Deleted files (tracked but don't exist)
        result["deleted"] = list(tracked_files - existing_files)
        
        # Check existing tracked files for changes
        for filepath in existing_files & tracked_files:
            if self.has_changed(filepath):
                result["changed"].append(filepath)
            else:
                result["unchanged"].append(filepath)
        
        return result
    
    def update_all(self) -> Dict[str, int]:
        """Update hashes for all project files"""
        files = self._get_project_files()
        stats = {"updated": 0, "new": 0, "unchanged": 0}
        
        for filepath in files:
            old_hash = self.get_hash(filepath)
            new_hash = self.update_hash(filepath)
            
            if old_hash is None:
                stats["new"] += 1
            elif old_hash != new_hash:
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1
        
        return stats
    
    def remove_hash(self, filepath: str):
        """Remove hash entry for a file"""
        if filepath in self._hashes:
            del self._hashes[filepath]
            self._save_hashes()
    
    def clear(self):
        """Clear all tracked hashes"""
        self._hashes = {}
        self._save_hashes()
    
    def get_file_info(self, filepath: str) -> Optional[Dict]:
        """Get full tracking info for a file"""
        if filepath not in self._hashes:
            return None
        
        info = self._hashes[filepath].copy()
        full_path = self.project_dir / filepath
        
        if full_path.exists():
            info["exists"] = True
            info["size"] = full_path.stat().st_size
            info["current_hash"] = self.compute_hash(full_path)
            info["changed"] = info["current_hash"] != info["hash"]
        else:
            info["exists"] = False
            info["changed"] = True
        
        return info
