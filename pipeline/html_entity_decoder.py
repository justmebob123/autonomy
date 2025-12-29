"""
HTML Entity Decoder

Handles HTML entity decoding for generated code across all programming languages.
This is necessary because HTTP transport and LLM responses may introduce HTML entities
that don't belong in source code.

Context-aware decoding: Only decodes entities in safe contexts (docstrings, comments)
to avoid breaking intentional entities in string literals.
"""

import html
import re
import ast
from typing import Dict, List, Tuple, Set
from .logging_setup import get_logger


class HTMLEntityDecoder:
    """Decodes HTML entities in generated code for various programming languages."""
    
    # Common HTML entities that appear in code
    COMMON_ENTITIES = {
        '&quot;': '"',
        '&#34;': '"',
        '&apos;': "'",
        '&#39;': "'",
        '&lt;': '<',
        '&#60;': '<',
        '&gt;': '>',
        '&#62;': '>',
        '&amp;': '&',
        '&#38;': '&',
        '&nbsp;': ' ',
        '&#160;': ' ',
        '&ndash;': '–',
        '&mdash;': '—',
        '&hellip;': '...',
    }
    
    # Language-specific string delimiters
    LANGUAGE_DELIMITERS = {
        'python': {
            'single': ["'", '"'],
            'multi': ['"""', "'''"],
            'raw': ['r"', "r'", 'R"', "R'"],
            'format': ['f"', "f'", 'F"', "F'"],
        },
        'javascript': {
            'single': ["'", '"', '`'],
            'multi': ['`'],
        },
        'typescript': {
            'single': ["'", '"', '`'],
            'multi': ['`'],
        },
        'java': {
            'single': ['"'],
            'multi': ['"""'],
        },
        'c': {
            'single': ['"'],
        },
        'cpp': {
            'single': ['"'],
            'raw': ['R"('],
        },
        'rust': {
            'single': ['"'],
            'raw': ['r"', 'r#"'],
        },
        'go': {
            'single': ['"', '`'],
            'raw': ['`'],
        },
    }
    
    def __init__(self):
        self.logger = get_logger()
    
    def decode_html_entities(self, code: str, filepath: str = "unknown") -> Tuple[str, bool]:
        """
        Decode HTML entities in code with context awareness.
        
        For Python files: Only decodes in docstrings and comments (safe contexts)
        For other languages: Decodes everywhere (legacy behavior)
        
        Args:
            code: Source code potentially containing HTML entities
            filepath: File path for logging and language detection
            
        Returns:
            Tuple of (decoded_code, was_modified)
        """
        if not code:
            return code, False
        
        original_code = code
        language = self._detect_language(filepath)
        
        # For Python files, use context-aware decoding
        if language == 'python':
            decoded = self._decode_python_context_aware(code)
        else:
            # For other languages, use comprehensive decoding (legacy)
            decoded = html.unescape(code)
            decoded = self._manual_decode(decoded)
            if language:
                decoded = self._fix_language_specific(decoded, language)
        
        was_modified = (decoded != original_code)
        
        if was_modified:
            self.logger.info(f"🔧 Decoded HTML entities in {filepath}")
            self._log_changes(original_code, decoded)
        
        return decoded, was_modified
    
    def _detect_language(self, filepath: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
        }
        
        for ext, lang in ext_map.items():
            if filepath.endswith(ext):
                return lang
        
        return None
    
    def _manual_decode(self, code: str) -> str:
        """Apply manual decoding for common HTML entities."""
        decoded = code
        
        for entity, char in self.COMMON_ENTITIES.items():
            if entity in decoded:
                decoded = decoded.replace(entity, char)
        
        return decoded
    
    def _find_python_docstrings(self, source: str) -> List[Tuple[int, int]]:
        """Find all docstring line ranges in Python source code."""
        docstrings = []
        
        try:
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                # Module docstring
                if isinstance(node, ast.Module) and ast.get_docstring(node):
                    if node.body and isinstance(node.body[0], ast.Expr):
                        if isinstance(node.body[0].value, ast.Constant):
                            docstrings.append((node.body[0].lineno, node.body[0].end_lineno))
                
                # Function/Class docstrings
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Constant):
                                docstrings.append((node.body[0].lineno, node.body[0].end_lineno))
        
        except SyntaxError:
            # If we can't parse, be conservative and don't decode anything
            self.logger.debug("Could not parse Python AST, skipping context-aware decoding")
        
        return docstrings
    
    def _find_python_comments(self, source: str) -> Set[int]:
        """Find all comment line numbers in Python source code."""
        comment_lines = set()
        lines = source.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Find # character that's not in a string
            in_string = False
            string_char = None
            escaped = False
            
            for char in line:
                if escaped:
                    escaped = False
                    continue
                
                if char == '\\':
                    escaped = True
                    continue
                
                if char in ('"', "'") and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                elif char == '#' and not in_string:
                    comment_lines.add(line_num)
                    break
        
        return comment_lines
    
    def _decode_python_context_aware(self, source: str) -> str:
        """
        Decode HTML entities in Python code with context awareness.
        Only decodes in docstrings and comments (safe contexts).
        
        Handles backslash-escaped HTML entities (e.g., \\\&amp;quot;) by removing
        the backslash ONLY in safe contexts before decoding.
        """
        lines = source.split('\n')
        
        # Find safe contexts
        docstrings = self._find_python_docstrings(source)
        comment_lines = self._find_python_comments(source)
        
        # Process each line
        for line_num, line in enumerate(lines, 1):
            # Check if this line is in a safe context
            in_docstring = any(start <= line_num <= end for start, end in docstrings)
            in_comment = line_num in comment_lines
            
            if in_docstring or in_comment:
                # Decode HTML entities in this line
                original_line = line
                
                # FIRST: Remove backslashes before HTML entities (only in safe contexts)
                # Example: \&amp;quot; -> &amp;quot; (so html.unescape can recognize it)
                decoded_line = re.sub(r'\\(&amp;[a-zA-Z]+;)', r'\1', line)  # \&amp;quot; -> &amp;quot;
                decoded_line = re.sub(r'\\(&amp;#\d+;)', r'\1', decoded_line)  # \&amp;#34; -> &amp;#34;
                
                # THEN: Use html.unescape for comprehensive decoding
                decoded_line = html.unescape(decoded_line)
                
                # FINALLY: Apply manual decoding for any remaining entities
                for entity, replacement in self.COMMON_ENTITIES.items():
                    if entity in decoded_line:
                        decoded_line = decoded_line.replace(entity, replacement)
                
                if decoded_line != original_line:
                    lines[line_num - 1] = decoded_line
        
        return '\n'.join(lines)
    
    def _fix_language_specific(self, code: str, language: str) -> str:
        """Fix language-specific string delimiter issues."""
        if language not in self.LANGUAGE_DELIMITERS:
            return code
        
        delimiters = self.LANGUAGE_DELIMITERS[language]
        
        # Fix escaped quotes that shouldn't be escaped
        # Example: """ -> """
        if 'multi' in delimiters:
            for delimiter in delimiters['multi']:
                # Fix escaped multi-line delimiters
                # Note: This is intentionally simple - just checking if delimiter appears escaped
                pass  # Most cases handled by html.unescape already
        
        return code
    
    def _log_changes(self, original: str, decoded: str):
        """Log what entities were decoded."""
        changes = []
        
        for entity, char in self.COMMON_ENTITIES.items():
            original_count = original.count(entity)
            decoded_count = decoded.count(entity)
            
            if original_count > decoded_count:
                changes.append(f"  - {entity} → {repr(char)} ({original_count - decoded_count} occurrences)")
        
        if changes:
            self.logger.debug("HTML entities decoded:")
            for change in changes[:5]:  # Limit to first 5 for brevity
                self.logger.debug(change)
            
            if len(changes) > 5:
                self.logger.debug(f"  ... and {len(changes) - 5} more")
    
    def validate_no_entities(self, code: str) -> Tuple[bool, List[str]]:
        """
        Check if code still contains HTML entities.
        
        Args:
            code: Source code to check
            
        Returns:
            Tuple of (is_clean, list_of_found_entities)
        """
        found_entities = []
        
        for entity in self.COMMON_ENTITIES.keys():
            if entity in code:
                found_entities.append(entity)
        
        # Also check for numeric entities
        numeric_pattern = r'&#\d+;'
        numeric_matches = re.findall(numeric_pattern, code)
        found_entities.extend(numeric_matches)
        
        is_clean = len(found_entities) == 0
        
        return is_clean, found_entities