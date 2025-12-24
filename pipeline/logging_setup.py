"""
Logging Configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI colors to log levels"""
    
    COLORS = {
        'DEBUG':    '\033[0;36m',   # Cyan
        'INFO':     '\033[0;32m',   # Green
        'WARNING':  '\033[0;33m',   # Yellow
        'ERROR':    '\033[0;31m',   # Red
        'CRITICAL': '\033[1;31m',   # Bold Red
        'RESET':    '\033[0m',
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


_logger: Optional[logging.Logger] = None


def setup_logging(log_file: Path, verbose: bool = False) -> logging.Logger:
    """Set up pipeline logging"""
    global _logger
    
    _logger = logging.getLogger("pipeline")
    _logger.setLevel(logging.DEBUG)
    _logger.handlers = []
    
    # Console handler - DEBUG if verbose, INFO otherwise
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(ColorFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    ))
    _logger.addHandler(console)
    
    # File handler - always DEBUG level
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    _logger.addHandler(file_handler)
    
    return _logger


def set_verbose(verbose: bool):
    """Set verbose mode on existing logger"""
    global _logger
    if _logger:
        for handler in _logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.DEBUG if verbose else logging.INFO)


def get_logger() -> logging.Logger:
    """Get the pipeline logger"""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("pipeline")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            console = logging.StreamHandler()
            console.setFormatter(ColorFormatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            ))
            _logger.addHandler(console)
    return _logger
