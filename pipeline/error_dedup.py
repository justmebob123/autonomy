"""
Error Deduplication - Group identical errors to avoid redundant fixes.

This module provides functions to deduplicate errors by grouping identical
errors that occur at multiple locations.
"""

from typing import Dict, List, Tuple
from collections import defaultdict


def create_error_key(error: Dict) -> Tuple:
    """
    Create a unique key for an error to enable deduplication.
    
    Args:
        error: Error dict with type, message, file, line, etc.
        
    Returns:
        Tuple that uniquely identifies this error type
    """
    error_type = error.get('type', 'Unknown')
    
    if error_type == 'RuntimeError':
        pass
        # For runtime errors, group by error message and object/attribute
        return (
            error_type,
            error.get('message', '').strip(),
            error.get('object_type'),
            error.get('missing_attribute')
        )
    else:
        pass
        # For syntax errors, group by file + message (line can vary)
        return (
            error_type,
            error.get('file', ''),
            error.get('message', '').strip()
        )


def deduplicate_errors(errors: List[Dict]) -> Dict[Tuple, Dict]:
    """
    Deduplicate errors by grouping identical errors.
    
    Args:
        errors: List of error dicts
        
    Returns:
        Dict mapping error_key to deduplicated error with all locations
        
    Example:
        Input: [
            {'type': 'RuntimeError', 'message': 'AttributeError...', 'file': 'a.py', 'line': 10},
            {'type': 'RuntimeError', 'message': 'AttributeError...', 'file': 'a.py', 'line': 20},
        ]
        
        Output: {
            ('RuntimeError', 'AttributeError...', 'Obj', 'attr'): {
                'type': 'RuntimeError',
                'message': 'AttributeError...',
                'locations': [
                    {'file': 'a.py', 'line': 10, ...},
                    {'file': 'a.py', 'line': 20, ...}
                ],
                ...
            }
        }
    """
    deduplicated = {}
    
    for error in errors:
        error_key = create_error_key(error)
        
        if error_key not in deduplicated:
            pass
            # First occurrence - create entry with all error info
            deduplicated[error_key] = {
                'type': error.get('type', 'Unknown'),
                'message': error.get('message', ''),
                'object_type': error.get('object_type'),
                'missing_attribute': error.get('missing_attribute'),
                'locations': [],
                'context': error.get('context', []),
                'call_chain': error.get('call_chain', []),
                'traceback': error.get('traceback', []),
                'class_definition': error.get('class_definition', {}),
                'similar_methods': error.get('similar_methods', []),
                'related_files': error.get('related_files', {}),
                'original_type': error.get('original_type', '')
            }
        
        # Add this location to the group
        location = {
            'file': error.get('file', ''),
            'line': error.get('line'),
            'function': error.get('function', ''),
            'code': error.get('text', ''),
            'offset': error.get('offset')
        }
        
        # Avoid duplicate locations
        if location not in deduplicated[error_key]['locations']:
            deduplicated[error_key]['locations'].append(location)
    
    return deduplicated


def format_deduplicated_summary(deduplicated: Dict[Tuple, Dict]) -> str:
    """
    Format a summary of deduplicated errors.
    
    Args:
        deduplicated: Dict from deduplicate_errors()
        
    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"Found {len(deduplicated)} unique error(s):")
    lines.append("")
    
    for i, (error_key, error_group) in enumerate(deduplicated.items(), 1):
        num_locations = len(error_group['locations'])
        error_type = error_group['type']
        message = error_group['message'][:80]
        
        lines.append(f"{i}. {error_type}: {message}")
        lines.append(f"   Occurs at {num_locations} location(s)")
        
        # Show first few locations
        for loc in error_group['locations'][:3]:
            lines.append(f"   - {loc['file']}:{loc['line']}")
        
        if num_locations > 3:
            lines.append(f"   ... and {num_locations - 3} more")
        
        lines.append("")
    
    return '\n'.join(lines)


def group_errors_by_file(deduplicated: Dict[Tuple, Dict]) -> Dict[str, List[Dict]]:
    """
    Group deduplicated errors by file for processing.
    
    Args:
        deduplicated: Dict from deduplicate_errors()
        
    Returns:
        Dict mapping file paths to list of error groups affecting that file
    """
    by_file = defaultdict(list)
    
    for error_key, error_group in deduplicated.items():
        pass
        # Get all unique files affected by this error
        files = set(loc['file'] for loc in error_group['locations'] if loc['file'])
        
        for file_path in files:
            pass
            # Filter locations to only this file
            file_locations = [
                loc for loc in error_group['locations']
                if loc['file'] == file_path
            ]
            
            # Create a copy of the error group for this file
            file_error_group = error_group.copy()
            file_error_group['locations'] = file_locations
            
            by_file[file_path].append(file_error_group)
    
    return dict(by_file)


def should_fix_all_at_once(error_group: Dict) -> bool:
    """
    Determine if all occurrences should be fixed in one operation.
    
    Args:
        error_group: Deduplicated error group
        
    Returns:
        True if all occurrences should be fixed together
    """
    # If all locations are in the same file, fix all at once
    files = set(loc['file'] for loc in error_group['locations'] if loc['file'])
    
    if len(files) == 1:
        return True
    
    # If it's an AttributeError with a clear fix (renamed method), fix all at once
    if error_group.get('missing_attribute') and error_group.get('similar_methods'):
        return True
    
    return False