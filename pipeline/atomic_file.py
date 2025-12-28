"""
Atomic File Operations

Provides utilities for atomic file writes to prevent corruption from crashes.
"""

from pathlib import Path
from typing import Union
import tempfile
import os


def atomic_write(filepath: Union[str, Path], content: str, encoding: str = 'utf-8'):
    """
    Write content to file atomically using temp + rename.
    
    This ensures that the file is either fully written or not modified at all,
    preventing corruption if the process crashes during write.
    
    Args:
        filepath: Path to target file
        content: Content to write
        encoding: Text encoding (default: utf-8)
        
    Raises:
        Exception: If write fails (original file remains unchanged)
    """
    filepath = Path(filepath)
    
    # Create temp file in same directory (ensures same filesystem)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f'.{filepath.name}.',
        suffix='.tmp'
    )
    
    temp_file = Path(temp_path)
    
    try:
        # Write to temp file
        with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk
        
        # Atomic rename (POSIX guarantees atomicity)
        temp_file.replace(filepath)
        
    except Exception:
        # Clean up temp file on failure
        try:
            if temp_file.exists():
                temp_file.unlink()
        except:
            pass
        raise


def atomic_write_json(filepath: Union[str, Path], data: dict, indent: int = 2):
    """
    Write JSON data to file atomically.
    
    Args:
        filepath: Path to target file
        data: Dictionary to serialize as JSON
        indent: JSON indentation (default: 2)
        
    Raises:
        Exception: If write fails (original file remains unchanged)
    """
    import json
    content = json.dumps(data, indent=indent)
    atomic_write(filepath, content)


def atomic_write_yaml(filepath: Union[str, Path], data: dict):
    """
    Write YAML data to file atomically.
    
    Args:
        filepath: Path to target file
        data: Dictionary to serialize as YAML
        
    Raises:
        Exception: If write fails (original file remains unchanged)
    """
    import yaml
    content = yaml.dump(data, default_flow_style=False)
    atomic_write(filepath, content)


def safe_read(filepath: Union[str, Path], default=None, encoding: str = 'utf-8'):
    """
    Safely read file with fallback to default if file doesn't exist or is corrupted.
    
    Args:
        filepath: Path to file
        default: Default value if read fails
        encoding: Text encoding (default: utf-8)
        
    Returns:
        File content or default value
    """
    filepath = Path(filepath)
    
    try:
        return filepath.read_text(encoding=encoding)
    except FileNotFoundError:
        return default
    except Exception as e:
        # Log corruption but return default
        import logging
        logging.getLogger(__name__).error(f"Failed to read {filepath}: {e}")
        return default


def safe_read_json(filepath: Union[str, Path], default=None):
    """
    Safely read JSON file with fallback.
    
    Args:
        filepath: Path to JSON file
        default: Default value if read fails
        
    Returns:
        Parsed JSON or default value
    """
    import json
    content = safe_read(filepath, default=None)
    
    if content is None:
        return default
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        import logging
        logging.getLogger(__name__).error(f"Corrupted JSON in {filepath}: {e}")
        return default