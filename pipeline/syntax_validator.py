"""
Syntax Validator

Pre-validates generated code before writing to files to catch syntax errors early.
"""

import ast
import re
from typing import Dict, Optional, Tuple
from .logging_setup import get_logger
from .html_entity_decoder import HTMLEntityDecoder


class SyntaxValidator:
    """Validates Python code syntax before file operations."""
    
    def __init__(self):
        self.logger = get_logger()
        self.html_decoder = HTMLEntityDecoder()
    
    def validate_python_code(self, code: str, filepath: str = "unknown") -> Tuple[bool, Optional[str]]:
        """
        Validate Python code syntax.
        
        Args:
            code: Python code to validate
            filepath: File path for error reporting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Skip validation for non-Python files
        if not filepath.endswith('.py'):
            return True, None
        
        if not code or not code.strip():
            return False, "Empty code content"
        
        try:
            # Try to parse the code
            ast.parse(code)
            return True, None
            
        except SyntaxError as e:
            error_msg = self._format_syntax_error(e, code, filepath)
            return False, error_msg
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _format_syntax_error(self, error: SyntaxError, code: str, filepath: str) -> str:
        """Format syntax error with context."""
        lines = code.split('\n')
        
        error_line = error.lineno if error.lineno else 0
        error_col = error.offset if error.offset else 0
        
        # Get context lines
        start = max(0, error_line - 3)
        end = min(len(lines), error_line + 2)
        
        context = []
        for i in range(start, end):
            line_num = i + 1
            marker = ">>>" if line_num == error_line else "   "
            context.append(f"{marker} {line_num:4d}: {lines[i]}")
        
        # Add column pointer if available
        if error_col > 0 and error_line > 0:
            pointer = " " * (error_col + 10) + "^"
            context.append(pointer)
        
        error_msg = f"""Syntax error in {filepath}:
Line {error_line}: {error.msg}
{chr(10).join(context)}
"""
        return error_msg
    
    def fix_common_syntax_errors(self, code: str, filepath: str = "unknown") -> str:
        """
        Attempt to fix common syntax errors automatically.
        
        Args:
            code: Python code with potential errors
            filepath: File path for language detection
            
        Returns:
            Fixed code (or original if no fixes applied)
        """
        original_code = code
        
        # Fix 0: CRITICAL - Decode HTML entities (HTTP transport artifact)
        # The decoder is context-aware and handles backslash escaping internally
        code, was_decoded = self.html_decoder.decode_html_entities(code, filepath)
        
        # Verify no entities remain
        is_clean, remaining_entities = self.html_decoder.validate_no_entities(code)
        if not is_clean:
            self.logger.warning(f"⚠️  HTML entities still present after decoding: {remaining_entities[:3]}")
        
        # Fix 1: Remove duplicate imports on same line
        # Example: "time from datetime import datetime" -> "from datetime import datetime"
        # Also fixes: "import from typing" -> "from typing"
        code = re.sub(r'\b\w+\s+(from\s+\w+\s+import\s+)', r'\1', code)
        code = re.sub(r'\bimport\s+(from\s+)', r'\1', code)
        
        # Fix 2: Fix malformed string literals in descriptions
        # Example: 'description": "text' -> 'description": "text"'
        code = re.sub(r'(description["\']:[\s]*["\'])([^"\']*?)(["\'],)', r'\1\2\3', code)
        
        # Fix 3: Remove trailing commas in function calls
        code = re.sub(r',(\s*\))', r'\1', code)
        
        # Fix 4: Fix indentation issues (convert tabs to spaces)
        code = code.replace('\t', '    ')
        
        # Fix 5: Remove multiple consecutive blank lines
        code = re.sub(r'\n\n\n+', '\n\n', code)
        
        # Fix 6: Fix escaped triple quotes (common after HTML entity decoding)
        # Example: &quot;&quot;&quot; -> """
        code = code.replace(r'"""', '"""')
        code = code.replace(r"\'\'\'", "'''")
        
        if code != original_code:
            self.logger.info("Applied automatic syntax fixes")
        
        return code
    
    def validate_and_fix(self, code: str, filepath: str = "unknown") -> Tuple[bool, str, Optional[str]]:
        """
        Validate code and attempt to fix if invalid.
        
        Args:
            code: Python code to validate
            filepath: File path for error reporting
            
        Returns:
            Tuple of (is_valid, fixed_code, error_message)
        """
        # First try validation
        is_valid, error = self.validate_python_code(code, filepath)
        
        if is_valid:
            return True, code, None
        
        # Try to fix common errors
        self.logger.warning(f"Syntax error detected in {filepath}, attempting auto-fix...")
        fixed_code = self.fix_common_syntax_errors(code, filepath)
        
        # Validate fixed code
        is_valid, error = self.validate_python_code(fixed_code, filepath)
        
        if is_valid:
            self.logger.info(f"Successfully fixed syntax errors in {filepath}")
            return True, fixed_code, None
        else:
            return False, code, error