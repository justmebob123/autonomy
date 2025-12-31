"""
Filename validation and normalization system.

This module provides comprehensive filename validation to prevent common issues:
- Placeholder text (e.g., <version>, <timestamp>)
- Version iterators (e.g., file (1).py, file_v2.py)
- Special characters and spacing issues
- Inconsistent naming conventions

The validator can operate in three modes:
1. Pre-creation: Block invalid filenames before file creation
2. Consultation: Ask AI to resolve ambiguous cases
3. Detection: Find existing problematic filenames during refactoring
"""

import os
import re
from typing import Tuple, List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class IssueLevel(Enum):
    """Severity levels for filename issues."""
    CRITICAL = "critical"  # Must be fixed before file creation
    WARNING = "warning"    # Should be reviewed but not blocking
    INFO = "info"          # Informational, may be intentional


@dataclass
class FilenameIssue:
    """Represents a detected filename issue."""
    level: IssueLevel
    message: str
    pattern: str
    suggestion: Optional[str] = None


class FilenameValidator:
    """
    Validates and normalizes filenames according to best practices.
    
    This validator detects common filename issues and provides recommendations
    for correction. It can operate in strict mode (blocking) or advisory mode.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the filename validator.
        
        Args:
            strict_mode: If True, CRITICAL issues block file creation
        """
        self.strict_mode = strict_mode
        
        # Patterns for different issue types
        self.patterns = {
            'placeholder': r'<[^>]+>',  # <version>, <timestamp>, etc.
            'version_iterator': r'\(\d+\)',  # (1), (2), etc.
            'parenthetical': r'\([^)]+\)',  # (anything)
            'multiple_underscores': r'_{2,}',  # __, ___, etc.
            'spaces': r'\s+',  # Any whitespace
            'mixed_separators': r'[-_]{2,}',  # -_, _-, etc.
        }
    
    def validate(self, filepath: str, context: Optional[Dict] = None) -> Tuple[bool, List[FilenameIssue]]:
        """
        Validate a filename for common issues.
        
        Args:
            filepath: The file path to validate
            context: Optional context including existing files, project conventions
        
        Returns:
            (is_valid, issues): Tuple of validation result and list of issues
        """
        filename = os.path.basename(filepath)
        issues = []
        
        # CRITICAL: Check for placeholder text
        if re.search(self.patterns['placeholder'], filename):
            issues.append(FilenameIssue(
                level=IssueLevel.CRITICAL,
                message="Placeholder text detected in filename",
                pattern=self.patterns['placeholder'],
                suggestion=self._suggest_placeholder_replacement(filename, context)
            ))
        
        # WARNING: Check for version iterators
        if re.search(self.patterns['version_iterator'], filename):
            issues.append(FilenameIssue(
                level=IssueLevel.WARNING,
                message="Version iterator detected - consider consolidation",
                pattern=self.patterns['version_iterator'],
                suggestion=self._suggest_version_consolidation(filename, context)
            ))
        
        # INFO: Check for parenthetical text (may be intentional)
        elif re.search(self.patterns['parenthetical'], filename):
            issues.append(FilenameIssue(
                level=IssueLevel.INFO,
                message="Parenthetical text detected - verify intentional naming",
                pattern=self.patterns['parenthetical'],
                suggestion=self._suggest_parenthetical_normalization(filename)
            ))
        
        # WARNING: Check for spaces
        if re.search(self.patterns['spaces'], filename):
            issues.append(FilenameIssue(
                level=IssueLevel.WARNING,
                message="Spaces in filename - should use underscores",
                pattern=self.patterns['spaces'],
                suggestion=filename.replace(' ', '_')
            ))
        
        # INFO: Check for multiple consecutive underscores
        if re.search(self.patterns['multiple_underscores'], filename):
            issues.append(FilenameIssue(
                level=IssueLevel.INFO,
                message="Multiple consecutive underscores detected",
                pattern=self.patterns['multiple_underscores'],
                suggestion=re.sub(r'_{2,}', '_', filename)
            ))
        
        # Determine if valid based on strict mode
        has_critical = any(issue.level == IssueLevel.CRITICAL for issue in issues)
        is_valid = not has_critical if self.strict_mode else True
        
        return is_valid, issues
    
    def _suggest_placeholder_replacement(self, filename: str, context: Optional[Dict]) -> str:
        """
        Suggest replacement for placeholder text.
        
        For migration files, suggests version numbers.
        For timestamp files, suggests actual timestamps.
        """
        # Handle None context
        if context is None:
            context = {}
        
        # Check if it's a migration file
        if 'migration' in filename.lower() or 'versions' in str(context.get('directory', '')):
            # Suggest version number based on existing files
            existing_versions = self._get_existing_versions(context)
            next_version = max(existing_versions, default=0) + 1
            return re.sub(r'<version>', f'{next_version:03d}', filename)
        
        # Check if it needs timestamp
        if '<timestamp>' in filename:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return filename.replace('<timestamp>', timestamp)
        
        # Generic placeholder - needs AI consultation
        return f"NEEDS_AI_CONSULTATION: {filename}"
    
    def _suggest_version_consolidation(self, filename: str, context: Optional[Dict]) -> str:
        """
        Suggest consolidation for version iterators.
        
        If multiple versions exist, suggests keeping only the latest.
        """
        base_name = re.sub(r'\s*\(\d+\)', '', filename)
        
        if context and 'existing_files' in context:
            # Check if base file exists
            existing = context['existing_files']
            if base_name in existing:
                return f"CONSOLIDATE: Merge with existing {base_name}"
        
        return base_name
    
    def _suggest_parenthetical_normalization(self, filename: str) -> str:
        """
        Suggest normalization for parenthetical text.
        
        Converts (text) to _text format.
        """
        # Extract parenthetical content
        match = re.search(r'\(([^)]+)\)', filename)
        if match:
            content = match.group(1)
            # Replace parentheses with underscores
            normalized = filename.replace(f'({content})', f'_{content}')
            return normalized
        
        return filename
    
    def _get_existing_versions(self, context: Optional[Dict]) -> List[int]:
        """
        Extract version numbers from existing migration files.
        """
        if not context or 'existing_files' not in context:
            return []
        
        versions = []
        for file in context['existing_files']:
            # Look for numeric prefixes (e.g., 001_, 002_)
            match = re.match(r'^(\d+)_', file)
            if match:
                versions.append(int(match.group(1)))
        
        return versions
    
    def normalize(self, filepath: str, auto_fix: bool = True) -> str:
        """
        Normalize a filename by applying automatic fixes.
        
        Args:
            filepath: The file path to normalize
            auto_fix: If True, apply automatic fixes for non-critical issues
        
        Returns:
            Normalized filepath
        """
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        if auto_fix:
            # Fix spaces
            filename = filename.replace(' ', '_')
            
            # Fix multiple underscores
            filename = re.sub(r'_{2,}', '_', filename)
            
            # Fix mixed separators (prefer underscores)
            filename = re.sub(r'[-_]+', '_', filename)
        
        return os.path.join(directory, filename)
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict]:
        """
        Scan a directory for filename issues.
        
        Args:
            directory: Directory to scan
            recursive: If True, scan subdirectories
        
        Returns:
            List of issues with file paths and recommendations
        """
        issues_found = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    is_valid, issues = self.validate(filepath)
                    
                    if issues:
                        issues_found.append({
                            'filepath': filepath,
                            'is_valid': is_valid,
                            'issues': issues
                        })
        else:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    is_valid, issues = self.validate(filepath)
                    
                    if issues:
                        issues_found.append({
                            'filepath': filepath,
                            'is_valid': is_valid,
                            'issues': issues
                        })
        
        return issues_found
    
    def format_issues_report(self, issues_found: List[Dict]) -> str:
        """
        Format a human-readable report of filename issues.
        
        Args:
            issues_found: List of issues from scan_directory
        
        Returns:
            Formatted report string
        """
        if not issues_found:
            return "✅ No filename issues detected"
        
        report = ["# Filename Issues Report\n"]
        
        # Group by severity
        critical = [i for i in issues_found if any(issue.level == IssueLevel.CRITICAL for issue in i['issues'])]
        warnings = [i for i in issues_found if any(issue.level == IssueLevel.WARNING for issue in i['issues']) and i not in critical]
        info = [i for i in issues_found if i not in critical and i not in warnings]
        
        if critical:
            report.append(f"## 🚨 CRITICAL Issues ({len(critical)})\n")
            for item in critical:
                report.append(f"### {item['filepath']}")
                for issue in item['issues']:
                    if issue.level == IssueLevel.CRITICAL:
                        report.append(f"- **{issue.message}**")
                        if issue.suggestion:
                            report.append(f"  - Suggestion: `{issue.suggestion}`")
                report.append("")
        
        if warnings:
            report.append(f"## ⚠️  WARNING Issues ({len(warnings)})\n")
            for item in warnings:
                report.append(f"### {item['filepath']}")
                for issue in item['issues']:
                    if issue.level == IssueLevel.WARNING:
                        report.append(f"- {issue.message}")
                        if issue.suggestion:
                            report.append(f"  - Suggestion: `{issue.suggestion}`")
                report.append("")
        
        if info:
            report.append(f"## ℹ️  INFO Issues ({len(info)})\n")
            for item in info:
                report.append(f"### {item['filepath']}")
                for issue in item['issues']:
                    if issue.level == IssueLevel.INFO:
                        report.append(f"- {issue.message}")
                        if issue.suggestion:
                            report.append(f"  - Suggestion: `{issue.suggestion}`")
                report.append("")
        
        return "\n".join(report)


def validate_filename(filepath: str, strict: bool = True) -> Tuple[bool, List[FilenameIssue]]:
    """
    Convenience function for quick filename validation.
    
    Args:
        filepath: The file path to validate
        strict: If True, CRITICAL issues block file creation
    
    Returns:
        (is_valid, issues): Tuple of validation result and list of issues
    """
    validator = FilenameValidator(strict_mode=strict)
    return validator.validate(filepath)


if __name__ == '__main__':
    # Example usage
    validator = FilenameValidator(strict_mode=True)
    
    # Test cases
    test_files = [
        'storage/migrations/versions/<version>_projects_table.py',
        'utils (1).py',
        'config_v2.py',
        'chapter_01_(introduction).md',
        'my file.py',
        'file___name.py',
        'normal_file.py',
    ]
    
    print("Filename Validation Test Results:\n")
    for filepath in test_files:
        is_valid, issues = validator.validate(filepath)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{status}: {filepath}")
        for issue in issues:
            print(f"  [{issue.level.value.upper()}] {issue.message}")
            if issue.suggestion:
                print(f"    → Suggestion: {issue.suggestion}")
        print()