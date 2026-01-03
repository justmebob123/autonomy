#!/usr/bin/env python3
"""Fix publish_event calls to use correct _publish_message method"""

import os
import re
from pathlib import Path

def fix_file(file_path):
    """Fix publish_event calls in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace self.publish_event with self._publish_message
    new_content = content.replace('self.publish_event(', 'self._publish_message(')
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    phases_dir = Path('pipeline/phases')
    fixed_count = 0
    
    for phase_file in phases_dir.glob('*.py'):
        if phase_file.name.startswith('__'):
            continue
        
        if fix_file(phase_file):
            print(f"✓ Fixed {phase_file.name}")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()