#!/usr/bin/env python3
"""Remove all excessive debug logging added during debugging session."""

import os
import re
from pathlib import Path

def remove_debug_logging(file_path):
    """Remove debug logging from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patterns to remove (debug logging lines)
    patterns = [
        # Lines with emoji indicators
        r'^\s*logger\.(info|debug|warning|error)\(["\'].*[📊🔍✅⚠️🚨📄🔀🎯✓].*["\'].*\)\s*$',
        # Lines with separator bars
        r'^\s*logger\.(info|debug|warning|error)\(["\']={50,}["\'].*\)\s*$',
        # Multi-line log statements with emojis
        r'^\s*logger\.(info|debug|warning|error)\(\s*$.*?[📊🔍✅⚠️🚨📄🔀🎯✓].*?\)\s*$',
    ]
    
    lines = content.split('\n')
    filtered_lines = []
    skip_next = False
    in_multiline_log = False
    multiline_buffer = []
    
    for i, line in enumerate(lines):
        # Check if this is a debug log line with emojis or separators
        has_emoji = any(emoji in line for emoji in ['📊', '🔍', '✅', '⚠️', '🚨', '📄', '🔀', '🎯', '✓'])
        has_separator = '=' * 50 in line
        is_logger_call = 'logger.' in line and any(level in line for level in ['info', 'debug', 'warning', 'error'])
        
        # Handle multiline logger calls
        if is_logger_call and '(' in line and ')' not in line:
            in_multiline_log = True
            multiline_buffer = [line]
            continue
        
        if in_multiline_log:
            multiline_buffer.append(line)
            if ')' in line:
                # Check if this multiline log has emojis or separators
                full_log = '\n'.join(multiline_buffer)
                has_debug_content = any(emoji in full_log for emoji in ['📊', '🔍', '✅', '⚠️', '🚨', '📄', '🔀', '🎯', '✓']) or '=' * 50 in full_log
                if not has_debug_content:
                    # Keep this log
                    filtered_lines.extend(multiline_buffer)
                in_multiline_log = False
                multiline_buffer = []
            continue
        
        # Skip lines with debug content
        if is_logger_call and (has_emoji or has_separator):
            continue
        
        filtered_lines.append(line)
    
    new_content = '\n'.join(filtered_lines)
    
    # Only write if content changed
    if new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Process all Python files in pipeline directory."""
    pipeline_dir = Path('pipeline')
    modified_count = 0
    
    for py_file in pipeline_dir.rglob('*.py'):
        if remove_debug_logging(py_file):
            print(f"Cleaned: {py_file}")
            modified_count += 1
    
    print(f"\nTotal files modified: {modified_count}")

if __name__ == '__main__':
    main()