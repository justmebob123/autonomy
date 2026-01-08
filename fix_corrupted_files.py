#!/usr/bin/env python3
"""
Fix corrupted files that have &quot; instead of proper quotes.

This script fixes files that were corrupted by the old JSON encoding bug
that used HTML entity &quot; instead of proper JSON escape &quot;.
"""

import os
import re
from pathlib import Path
import sys

def fix_file(filepath):
    """Fix a single file by replacing &quot; with proper quotes."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has corruption
        if '&quot;' not in content:
            return False
        
        # Count occurrences
        count = content.count('&quot;')
        
        # Fix the corruption
        fixed_content = content.replace('&quot;', '"')
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✓ Fixed: {filepath} ({count} replacements)")
        return True
    except Exception as e:
        print(f"✗ Error fixing {filepath}: {e}")
        return False

def fix_directory(directory, dry_run=False):
    """Fix all Python files in a directory."""
    directory = Path(directory)
    fixed_count = 0
    total_replacements = 0
    
    print(f"Scanning directory: {directory}")
    print(f"Mode: {'DRY RUN' if dry_run else 'FIXING FILES'}")
    print("-" * 70)
    
    for filepath in directory.rglob('*.py'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '&quot;' in content:
                count = content.count('&quot;')
                total_replacements += count
                
                if dry_run:
                    print(f"Would fix: {filepath} ({count} replacements)")
                else:
                    if fix_file(filepath):
                        fixed_count += 1
        except Exception as e:
            print(f"✗ Error reading {filepath}: {e}")
    
    return fixed_count, total_replacements

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_corrupted_files.py <directory> [--dry-run]")
        print("\nOptions:")
        print("  --dry-run    Show what would be fixed without making changes")
        print("\nExample:")
        print("  python3 fix_corrupted_files.py /home/ai/AI/web")
        print("  python3 fix_corrupted_files.py /home/ai/AI/web --dry-run")
        sys.exit(1)
    
    directory = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)
    
    print("=" * 70)
    print("CORRUPTED FILES FIX SCRIPT")
    print("=" * 70)
    print(f"Target directory: {directory}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'FIXING FILES'}")
    print("=" * 70)
    print()
    
    fixed_count, total_replacements = fix_directory(directory, dry_run)
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if dry_run:
        print(f"Files that would be fixed: {fixed_count}")
        print(f"Total replacements: {total_replacements}")
        print()
        print("Run without --dry-run to apply fixes")
    else:
        print(f"✓ Fixed {fixed_count} files")
        print(f"✓ Total replacements: {total_replacements}")
        print()
        print("Next steps:")
        print("1. Verify fixes: python3 -m compileall " + directory)
        print("2. Run autonomy system to continue work")
    print("=" * 70)

if __name__ == '__main__':
    main()