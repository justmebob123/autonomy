"""
Utility Functions
"""

from typing import Tuple, Optional
import re


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Check if Python code has valid syntax.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        pass
        # Format a helpful error message
        error_msg = f"Line {e.lineno}: {e.msg}"
        if e.text:
            error_msg += f"\n  Code: {e.text.strip()}"
            if e.offset:
                error_msg += f"\n  Position: column {e.offset}"
        return False, error_msg
    except Exception as e:
        return False, str(e)


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_block(text: str, language: str = "python") -> Optional[str]:
    """
    Extract code from a markdown code block.
    
    Args:
        text: Text potentially containing code blocks
        language: Expected language (e.g., 'python')
    
    Returns:
        Extracted code or None if not found
    """
    # Try to find ```python ... ``` blocks
    pattern = rf'```{language}\s*\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try generic ``` ... ``` blocks
    pattern = r'```\s*\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return None


def normalize_filepath(filepath: str) -> str:
    """
    Normalize a file path.
    
    - Removes leading/trailing whitespace
    - Converts backslashes to forward slashes
    - Removes leading ./
    """
    filepath = filepath.strip()
    filepath = filepath.replace('\\', '/')
    if filepath.startswith('./'):
        filepath = filepath[2:]
    return filepath


def indent_code(code: str, spaces: int = 4) -> str:
    """
    Indent all lines of code by the specified number of spaces.
    """
    indent = ' ' * spaces
    lines = code.split('\n')
    return '\n'.join(indent + line if line.strip() else line for line in lines)


def dedent_code(code: str) -> str:
    """
    Remove common leading whitespace from all lines.
    """
    import textwrap
    return textwrap.dedent(code)


def count_lines(code: str) -> int:
    """Count non-empty lines in code"""
    return sum(1 for line in code.split('\n') if line.strip())


def get_function_signatures(code: str) -> list:
    """
    Extract function and class signatures from Python code.
    
    Returns:
        List of signature strings
    """
    signatures = []
    
    # Function definitions
    for match in re.finditer(r'^(def \w+\([^)]*\)(?:\s*->\s*[^:]+)?)', code, re.MULTILINE):
        signatures.append(match.group(1))
    
    # Class definitions
    for match in re.finditer(r'^(class \w+(?:\([^)]*\))?)', code, re.MULTILINE):
        signatures.append(match.group(1))
    
    return signatures
