"""
Code Search - Find all occurrences of broken references across the project.

This module helps detect refactoring-in-progress by finding all uses of
broken attributes, methods, or variables across the entire codebase.
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


def search_for_attribute_usage(
    project_dir: Path,
    attribute_name: str,
    object_type: str = None
) -> Dict[str, List[Dict]]:
    """
    Search for all uses of an attribute across the project.
    
    Args:
        project_dir: Project root directory
        attribute_name: Name of the attribute (e.g., 'start_phase')
        object_type: Optional object type to narrow search
        
    Returns:
        Dict mapping file paths to list of occurrences
        
    Example:
        {
            'job_executor.py': [
                {'line': 3010, 'code': 'self.coordinator.start_phase(...)'},
                {'line': 4527, 'code': 'self.coordinator.start_phase(...)'}
            ],
            'test_runner.py': [
                {'line': 123, 'code': 'coordinator.start_phase(...)'}
            ]
        }
    """
    results = defaultdict(list)
    
    # Build search patterns
    patterns = [
        f'\\.{attribute_name}\\(',  # Method call: .attr(
        f'\\.{attribute_name}\\s',  # Attribute access: .attr 
        f'\\.{attribute_name}$',    # End of line: .attr
    ]
    
    for pattern in patterns:
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-E', pattern, str(project_dir), '--include=*.py'],
                capture_output=True,
                text=True,
                timeout=None  # UNLIMITED
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    # Parse: /path/to/file.py:123:code here
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        line_num = parts[1]
                        code = parts[2].strip()
                        
                        # Make path relative to project_dir
                        try:
                            rel_path = str(Path(file_path).relative_to(project_dir))
                        except ValueError:
                            rel_path = file_path
                        
                        # Avoid duplicates
                        occurrence = {
                            'line': int(line_num),
                            'code': code
                        }
                        
                        if occurrence not in results[rel_path]:
                            results[rel_path].append(occurrence)
        
        except subprocess.TimeoutExpired:
            # Timeout is expected for very large codebases
            continue
        except Exception as e:
            # Log but continue with other patterns
            import logging
            logging.getLogger(__name__).warning(f"Search failed for pattern '{pattern}': {e}")
    
    return dict(results)


def search_for_pattern(
    project_dir: Path,
    pattern: str,
    file_pattern: str = '*.py'
) -> Dict[str, List[Dict]]:
    """
    Search for a general pattern across the project.
    
    Args:
        project_dir: Project root directory
        pattern: Pattern to search for (supports regex)
        file_pattern: File pattern to search in
        
    Returns:
        Dict mapping file paths to list of occurrences
    """
    results = defaultdict(list)
    
    try:
        result = subprocess.run(
            ['grep', '-r', '-n', '-E', pattern, str(project_dir), f'--include={file_pattern}'],
            capture_output=True,
            text=True,
            timeout=None  # UNLIMITED
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    line_num = parts[1]
                    code = parts[2].strip()
                    
                    try:
                        rel_path = str(Path(file_path).relative_to(project_dir))
                    except ValueError:
                        rel_path = file_path
                    
                    results[rel_path].append({
                        'line': int(line_num),
                        'code': code
                    })
    
    except subprocess.TimeoutExpired:
        # Timeout is expected for very large codebases
        pass
    except Exception as e:
        # Log but return partial results
        import logging
        logging.getLogger(__name__).warning(f"Pattern search failed for '{pattern}': {e}")
    
    return dict(results)


def detect_refactoring_context(
    error_group: Dict,
    project_dir: Path
) -> Dict:
    """
    Detect if this error is part of a larger refactoring.
    
    Args:
        error_group: Deduplicated error group
        project_dir: Project root directory
        
    Returns:
        Dict with refactoring context information
    """
    context = {
        'is_refactoring': False,
        'total_occurrences': 0,
        'files_affected': {},
        'files_not_in_error': {}
    }
    
    # Only applicable for AttributeError
    if not error_group.get('missing_attribute'):
        return context
    
    attr_name = error_group['missing_attribute']
    
    # Search for all uses of this attribute
    all_occurrences = search_for_attribute_usage(project_dir, attr_name)
    
    if not all_occurrences:
        return context
    
    # Get files that have errors
    error_files = set(loc['file'] for loc in error_group.get('locations', []))
    
    # Count total occurrences
    total = sum(len(occs) for occs in all_occurrences.values())
    context['total_occurrences'] = total
    context['files_affected'] = all_occurrences
    
    # Find files that use the attribute but DON'T have errors
    # This suggests they might have been updated already
    for file_path, occurrences in all_occurrences.items():
        if file_path not in error_files:
            context['files_not_in_error'][file_path] = occurrences
    
    # Determine if this looks like a refactoring
    if len(all_occurrences) > len(error_files):
        context['is_refactoring'] = True
    
    return context


def format_refactoring_context(context: Dict) -> str:
    """
    Format refactoring context for inclusion in AI prompt.
    
    Args:
        context: Context dict from detect_refactoring_context
        
    Returns:
        Formatted string for prompt
    """
    if not context['is_refactoring']:
        return ""
    
    lines = []
    lines.append("\n## ⚠️ Refactoring Context Detected\n")
    lines.append(f"This attribute is used in **{context['total_occurrences']} locations** ")
    lines.append(f"across **{len(context['files_affected'])} files**.\n")
    
    if context['files_not_in_error']:
        lines.append("\n### Files Using This Attribute (No Errors)\n")
        lines.append("These files might have been updated already:\n")
        for file_path, occurrences in list(context['files_not_in_error'].items())[:5]:
            lines.append(f"\n**{file_path}** ({len(occurrences)} uses):")
            for occ in occurrences[:3]:
                lines.append(f"  - Line {occ['line']}: `{occ['code'][:60]}...`")
            if len(occurrences) > 3:
                lines.append(f"  - ... and {len(occurrences) - 3} more")
        
        if len(context['files_not_in_error']) > 5:
            lines.append(f"\n... and {len(context['files_not_in_error']) - 5} more files")
    
    lines.append("\n### Analysis\n")
    lines.append("This appears to be a **refactoring in progress**. You should:\n")
    lines.append("1. Check if the attribute was renamed (use `search_code` tool)\n")
    lines.append("2. Examine files without errors to see what changed (use `read_file` tool)\n")
    lines.append("3. Decide: Update ALL calls OR create the missing method\n")
    lines.append("4. Apply consistent fix across all affected files\n")
    
    return ''.join(lines)


def get_related_files_summary(context: Dict, max_files: int = 10) -> str:
    """
    Get a summary of related files for the AI to examine.
    
    Args:
        context: Context dict from detect_refactoring_context
        max_files: Maximum number of files to list
        
    Returns:
        Formatted summary string
    """
    if not context['files_affected']:
        return ""
    
    lines = []
    lines.append("\n## Related Files\n")
    lines.append("Files that use this attribute:\n")
    
    for file_path, occurrences in list(context['files_affected'].items())[:max_files]:
        lines.append(f"\n- **{file_path}**: {len(occurrences)} occurrence(s)")
    
    if len(context['files_affected']) > max_files:
        remaining = len(context['files_affected']) - max_files
        lines.append(f"\n- ... and {remaining} more files")
    
    lines.append("\n**Tip**: Use the `read_file` tool to examine these files.\n")
    
    return ''.join(lines)