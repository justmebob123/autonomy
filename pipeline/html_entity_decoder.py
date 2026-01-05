"""
HTML Entity Decoder - Version 2 (Context-Aware)

Handles HTML entity decoding for generated code with context awareness.
Only decodes entities in safe contexts to avoid breaking valid Python code.
"""

import html
import re
import ast
from typing import Dict, List, Tuple, Set
from .logging_setup import get_logger


class HTMLEntityDecoder:
    """Decodes HTML entities in generated code with context awareness."""
    
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
        '&#167;': 'Section ',
        '&#146;': "'",
        '&#147;': '"',
        '&#148;': '"',
        '&#174;': '',  # Registered trademark
        '&#168;': '',  # Diaeresis
        '&#153;': '',  # Trademark
        '&#128;': '(euro)',
        '&#163;': '(british pound)',
        '&#150;': '-',
        '&#165;': '(yen)',
        '&#169;': 'copyright ',
        '&ndash;': '\u2013',
        '&mdash;': '\u2014',
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
        
        For Python files: Only decodes in safe contexts (docstrings, comments, syntax errors)
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
        
        # For Python files, use conservative context-aware decoding
        if language == 'python':
            # First fix syntax errors (lines starting with &quot;)
            decoded = self._fix_syntax_errors(code)
            
            # Then try context-aware decoding if file can be parsed
            try:
                decoded = self._decode_python_context_aware(decoded)
            except SyntaxError:
                # If file still has syntax errors, keep the syntax-error fixes
                self.logger.debug(f"Cannot parse {filepath}, using syntax-error fixes only")
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
        """
        Apply manual decoding for common HTML entities.
        
        Uses multiple approaches:
        1. Direct entity replacement from COMMON_ENTITIES
        2. Numeric entity decoding (&#NNNN;)
        3. html.unescape for standard entities
        """
        import re
        
        decoded = code
        
        # Step 1: Replace common entities
        for entity, char in self.COMMON_ENTITIES.items():
            if entity in decoded:
                decoded = decoded.replace(entity, char)
        
        # Step 2: Decode numeric HTML entities (&#NNNN;)
        def replace_numeric_entity(match):
            try:
                dec = int(match.group(1))
                return chr(dec)
            except (ValueError, OverflowError):
                return match.group(0)  # Keep original if conversion fails
        
        decoded = re.sub(r'&#(\d+);', replace_numeric_entity, decoded)
        
        # Step 3: Use html.unescape for any remaining standard entities
        decoded = html.unescape(decoded)
        
        # Step 4: Normalize non-breaking spaces to regular spaces
        decoded = decoded.replace('\xa0', ' ')
        
        return decoded
    
    def _fix_syntax_errors(self, code: str) -> str:
        """
        Fix ONLY patterns that cause syntax errors.
        
        CONSERVATIVE approach - only fixes:
        1. Lines starting with &quot; or \' (line continuation errors)
        2. Lines starting with \&quot; or \&apos; (HTML entity line continuation errors)
        3. Standalone docstring delimiters at line start
        4. HTML entities in comments (safe context)
        
        Does NOT touch:
        - Escape sequences inside string literals
        - HTML entities in string content
        - Raw strings with escapes
        """
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Fix 1: Line starts with \&quot; (ALWAYS a syntax error)
            # Pattern: \&quot;\&quot;\&quot; -> """
            # The pattern is: backslash + &quot; (7 chars total)
            pattern1 = '\\&quot;'
            if stripped.startswith(pattern1):
                # Replace ALL \&quot; on this line
                line = line.replace(pattern1, '"')
            
            # Fix 2: Line starts with \&apos; (ALWAYS a syntax error)
            elif stripped.startswith('\\&apos;'):
                # Replace ALL \&apos; on this line
                line = line.replace('\\&apos;', "'")
            
            # Fix 3: Line starts with &quot; (ALWAYS a syntax error)
            elif stripped.startswith(chr(92) + chr(34)):
                # Check for docstring delimiter: &quot;&quot;&quot;
                if stripped.startswith(chr(92) + chr(34) * 3):
                    # Only replace the first occurrence at line start
                    indent = len(line) - len(line.lstrip())
                    rest = line.lstrip()[len(chr(92) + chr(34) * 3):]
                    line = ' ' * indent + chr(34) * 3 + rest
                # Single &quot; at start
                else:
                    indent = len(line) - len(line.lstrip())
                    rest = line.lstrip()[len(chr(92) + chr(34)):]
                    line = ' ' * indent + chr(34) + rest
            
            # Fix 4: Line starts with \' (ALWAYS a syntax error)
            elif stripped.startswith(chr(92) + chr(39)):
                # Check for docstring delimiter: \'\'\'
                if stripped.startswith(chr(92) + chr(39) * 3):
                    indent = len(line) - len(line.lstrip())
                    rest = line.lstrip()[len(chr(92) + chr(39) * 3):]
                    line = ' ' * indent + chr(39) * 3 + rest
                # Single \' at start
                else:
                    indent = len(line) - len(line.lstrip())
                    rest = line.lstrip()[len(chr(92) + chr(39)):]
                    line = ' ' * indent + chr(39) + rest
            
            # Fix 5: HTML entities in comments (safe to decode)
            if '#' in line:
                try:
                    comment_start = line.index('#')
                    before_comment = line[:comment_start]
                    comment = line[comment_start:]
                    
                    # Decode HTML entities in comment only
                    comment = html.unescape(comment)
                    for entity, char in self.COMMON_ENTITIES.items():
                        if entity in comment:
                            comment = comment.replace(entity, char)
                    
                    line = before_comment + comment
                except ValueError:
                    pass
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
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
            # If we can't parse, return empty list
            self.logger.debug("Could not parse Python AST for docstring detection")
        
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
                
                # Use html.unescape for comprehensive decoding
                decoded_line = html.unescape(line)
                
                # Apply manual decoding for any remaining entities
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