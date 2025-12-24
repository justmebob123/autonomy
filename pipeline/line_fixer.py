"""
Line-based file fixing - avoids string escape issues entirely.

Instead of matching strings (which has escape sequence problems),
we work directly with line numbers.
"""

from pathlib import Path
from typing import Optional, List
import re


def fix_line_directly(filepath: Path, line_num: int, fix_type: str, error_msg: str) -> bool:
    """
    Fix a specific line based on the error type.
    
    Args:
        filepath: Path to the file
        line_num: Line number (1-indexed)
        fix_type: Type of error (e.g., 'unmatched ]', 'invalid syntax')
        error_msg: Error message from Python
        
    Returns:
        True if fixed, False otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Handle files without final newline
        lines = content.splitlines(keepends=True)
        if content and not content.endswith('\n'):
            # Last line doesn't have newline, add it
            if lines:
                lines[-1] = lines[-1] + '\n'
        
        if line_num < 1 or line_num > len(lines):
            return False
        
        idx = line_num - 1
        original_line = lines[idx]
        fixed_line = apply_fix(original_line, fix_type, error_msg)
        
        if fixed_line and fixed_line != original_line:
            lines[idx] = fixed_line
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error in line_fixer: {e}")
        return False


def apply_fix(line: str, fix_type: str, error_msg: str) -> Optional[str]:
    """
    Apply a fix to a line based on error type.
    
    Returns the fixed line or None if no fix could be applied.
    """
    error_lower = error_msg.lower()
    
    # Fix 1: Unmatched closing bracket ]
    if 'unmatched' in error_lower and ']' in error_lower:
        stripped = line.rstrip()
        
        # Special case: raw string with mixed quotes - needs triple quotes
        # e.g., r"pattern['&quot;]" or r"pattern['"]"]" 
        if 'r"' in stripped and "['" in stripped:
            import re
            
            # First, remove extra ] if present (e.g., ['"]"] -> ['"])
            if stripped.endswith(']"]') or stripped.endswith('"]"'):
                stripped = stripped[:-2] + '"'
            
            # Now convert to triple-quoted raw string
            # Find the closing quote position BEFORE modification
            original_closing_pos = stripped.rfind('"')
            
            # Replace r" with r"""
            fixed = re.sub(r'(r)"', r'\1"""', stripped, count=1)
            
            # The closing position shifted by 2 (we added two quotes)
            new_closing_pos = original_closing_pos + 2
            
            # Replace the closing quote with """
            if new_closing_pos < len(fixed):
                fixed = fixed[:new_closing_pos] + '"""' + fixed[new_closing_pos+1:]
            
            return fixed + '\n'
        
        # Check if line ends with a quote and is missing ]
        if '"' in stripped and not stripped.endswith(']'):
            # Add ] before the newline
            return stripped + ']\n'
    
    # Fix 2: Unmatched closing parenthesis )
    elif 'unmatched' in error_lower and ')' in error_lower:
        stripped = line.rstrip()
        if not stripped.endswith(')'):
            return stripped + ')\n'
    
    # Fix 3: Invalid syntax with XML/HTML tags
    elif 'invalid syntax' in error_lower and '</' in line:
        # Comment out the line
        indent = len(line) - len(line.lstrip())
        return ' ' * indent + '# ' + line.lstrip()
    
    # Fix 4: Markdown code blocks
    elif 'invalid syntax' in error_lower and '```' in line:
        # Remove the line
        return '\n'
    
    # Fix 5: Missing colon (common in function/class definitions)
    elif 'expected' in error_lower and ':' in error_lower:
        stripped = line.rstrip()
        if not stripped.endswith(':'):
            return stripped + ':\n'
    
    return None


def get_line_context(filepath: Path, line_num: int, context_lines: int = 3) -> List[str]:
    """
    Get context around a line for display purposes.
    
    Returns list of strings with line numbers.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context = []
        for i in range(start, end):
            marker = '>>>' if i == line_num - 1 else '   '
            context.append(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
        
        return context
        
    except Exception:
        return []


def replace_line_range(filepath: Path, start_line: int, end_line: int, 
                       new_content: str) -> bool:
    """
    Replace a range of lines with new content.
    
    Args:
        filepath: Path to file
        start_line: Starting line number (1-indexed, inclusive)
        end_line: Ending line number (1-indexed, inclusive)
        new_content: New content (can be multiple lines)
        
    Returns:
        True if successful
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return False
        
        # Split new content into lines
        new_lines = new_content.splitlines(keepends=True)
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        
        # Replace the range
        lines[start_line-1:end_line] = new_lines
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error replacing line range: {e}")
        return False