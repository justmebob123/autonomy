#!/usr/bin/env python3
"""
HTML Entity Fixer Tool

A comprehensive tool for detecting and fixing HTML entity issues in Python source files.
This tool can:
- Detect HTML entities in source code
- Fix invalid escape sequences (like \&)
- Apply context-aware decoding
- Handle self-referential issues
- Validate fixes

Usage:
    # Fix a single file
    python bin/fix_html_entities.py path/to/file.py
    
    # Fix all Python files in a directory
    python bin/fix_html_entities.py path/to/directory/ --recursive
    
    # Dry run (show what would be fixed without making changes)
    python bin/fix_html_entities.py path/to/file.py --dry-run
    
    # Fix with backup
    python bin/fix_html_entities.py path/to/file.py --backup
"""

import sys
import os
import argparse
import shutil
from pathlib import Path
from typing import List, Tuple, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.html_entity_decoder import HTMLEntityDecoder


class HTMLEntityFixer:
    """Fixes HTML entity issues in Python source files."""
    
    def __init__(self, dry_run: bool = False, backup: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.backup = backup
        self.verbose = verbose
        self.decoder = HTMLEntityDecoder()
        self.stats = {
            'files_scanned': 0,
            'files_modified': 0,
            'entities_fixed': 0,
            'errors': 0,
        }
    
    def fix_file(self, filepath: Path) -> Tuple[bool, str]:
        """
        Fix HTML entities in a single file.
        
        Returns:
            Tuple of (was_modified, message)
        """
        self.stats['files_scanned'] += 1
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Check for syntax warnings first
            syntax_issues = self._check_syntax_warnings(original_content, str(filepath))
            
            # Decode HTML entities
            decoded_content, was_modified = self.decoder.decode_html_entities(
                original_content, str(filepath)
            )
            
            if not was_modified and not syntax_issues:
                if self.verbose:
                    return False, f"✓ {filepath}: No changes needed"
                return False, ""
            
            # Validate the fix
            validation_ok, validation_msg = self._validate_fix(
                original_content, decoded_content, str(filepath)
            )
            
            if not validation_ok:
                self.stats['errors'] += 1
                return False, f"✗ {filepath}: Validation failed - {validation_msg}"
            
            # Apply fix
            if not self.dry_run:
                # Backup if requested
                if self.backup:
                    backup_path = f"{filepath}.bak"
                    shutil.copy2(filepath, backup_path)
                    if self.verbose:
                        print(f"  Created backup: {backup_path}")
                
                # Write fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)
            
            self.stats['files_modified'] += 1
            
            # Count entities fixed
            entities_fixed = self._count_entities_fixed(original_content, decoded_content)
            self.stats['entities_fixed'] += entities_fixed
            
            action = "Would fix" if self.dry_run else "Fixed"
            return True, f"✓ {filepath}: {action} {entities_fixed} HTML entities"
        
        except Exception as e:
            self.stats['errors'] += 1
            return False, f"✗ {filepath}: Error - {str(e)}"
    
    def fix_directory(self, dirpath: Path, recursive: bool = False) -> List[str]:
        """
        Fix HTML entities in all Python files in a directory.
        
        Returns:
            List of result messages
        """
        results = []
        
        if recursive:
            pattern = '**/*.py'
        else:
            pattern = '*.py'
        
        for filepath in dirpath.glob(pattern):
            if filepath.is_file():
                modified, message = self.fix_file(filepath)
                if message:
                    results.append(message)
        
        return results
    
    def _check_syntax_warnings(self, content: str, filepath: str) -> List[str]:
        """Check for syntax warnings in the content."""
        import warnings
        
        issues = []
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", SyntaxWarning)
            try:
                compile(content, filepath, 'exec')
                for warning in w:
                    if issubclass(warning.category, SyntaxWarning):
                        issues.append(str(warning.message))
            except SyntaxError:
                # Ignore syntax errors, we're only looking for warnings
                pass
        
        return issues
    
    def _validate_fix(self, original: str, fixed: str, filepath: str) -> Tuple[bool, str]:
        """Validate that the fix doesn't break the code."""
        # Check that fixed code has no syntax warnings
        syntax_issues = self._check_syntax_warnings(fixed, filepath)
        if syntax_issues:
            return False, f"Still has syntax warnings: {syntax_issues}"
        
        # Check that we didn't introduce syntax errors
        try:
            compile(fixed, filepath, 'exec')
        except SyntaxError as e:
            return False, f"Introduced syntax error: {e}"
        
        # Check that we didn't remove too much
        if len(fixed) < len(original) * 0.5:
            return False, "Fixed content is suspiciously short"
        
        return True, "OK"
    
    def _count_entities_fixed(self, original: str, fixed: str) -> int:
        """Count how many HTML entities were fixed."""
        count = 0
        
        for entity in self.decoder.COMMON_ENTITIES.keys():
            original_count = original.count(entity)
            fixed_count = fixed.count(entity)
            count += max(0, original_count - fixed_count)
        
        return count
    
    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "=" * 60)
        print("HTML Entity Fixer - Summary")
        print("=" * 60)
        print(f"Files scanned:    {self.stats['files_scanned']}")
        print(f"Files modified:   {self.stats['files_modified']}")
        print(f"Entities fixed:   {self.stats['entities_fixed']}")
        print(f"Errors:           {self.stats['errors']}")
        print("=" * 60)
        
        if self.dry_run:
            print("\n⚠️  DRY RUN - No files were actually modified")
            print("Run without --dry-run to apply changes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fix HTML entity issues in Python source files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix a single file
  python bin/fix_html_entities.py pipeline/html_entity_decoder.py
  
  # Fix all Python files in a directory
  python bin/fix_html_entities.py pipeline/ --recursive
  
  # Dry run (show what would be fixed)
  python bin/fix_html_entities.py pipeline/ --recursive --dry-run
  
  # Fix with backup
  python bin/fix_html_entities.py pipeline/html_entity_decoder.py --backup
        """
    )
    
    parser.add_argument(
        'path',
        help='Path to Python file or directory to fix'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively fix all Python files in directory'
    )
    
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be fixed without making changes'
    )
    
    parser.add_argument(
        '-b', '--backup',
        action='store_true',
        help='Create backup files (.bak) before modifying'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        return 1
    
    # Create fixer
    fixer = HTMLEntityFixer(
        dry_run=args.dry_run,
        backup=args.backup,
        verbose=args.verbose
    )
    
    # Fix
    print("=" * 60)
    print("HTML Entity Fixer")
    print("=" * 60)
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No files will be modified\n")
    
    if path.is_file():
        # Single file
        modified, message = fixer.fix_file(path)
        if message:
            print(message)
    
    elif path.is_dir():
        # Directory
        if not args.recursive:
            print(f"Error: {args.path} is a directory. Use --recursive to fix all files.", file=sys.stderr)
            return 1
        
        results = fixer.fix_directory(path, recursive=True)
        for result in results:
            print(result)
    
    else:
        print(f"Error: Invalid path: {args.path}", file=sys.stderr)
        return 1
    
    # Print summary
    fixer.print_summary()
    
    return 0 if fixer.stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())