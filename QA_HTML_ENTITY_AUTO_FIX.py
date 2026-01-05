#!/usr/bin/env python3
"""
QA Phase HTML Entity Auto-Fix Integration

This script adds automatic HTML entity fixing to the QA phase.
"""

# Method to add to QAPhase class
AUTO_FIX_METHOD = '''
    def _auto_fix_html_entities(self, filepath: str) -> bool:
        """
        Automatically detect and fix HTML entity issues in a file.
        
        This runs BEFORE analysis to prevent syntax errors from blocking QA.
        
        Args:
            filepath: Relative path to file
            
        Returns:
            True if issues were found and fixed, False otherwise
        """
        full_path = self.project_dir / filepath
        if not full_path.exists() or not full_path.is_file():
            return False
        
        try:
            # Read file content
            content = full_path.read_text(encoding='utf-8')
            
            # Quick check for HTML entity patterns
            has_backslash_quote = chr(92) + chr(34) in content  # \&quot;
            has_backslash_apos = chr(92) + chr(39) in content   # \\'
            has_html_entities = '&quot;' in content or '&#34;' in content or '&apos;' in content
            
            if not (has_backslash_quote or has_backslash_apos or has_html_entities):
                return False
            
            self.logger.info(f"🔧 Auto-fixing HTML entities in {filepath}")
            
            # Use the HTMLEntityDecoder directly
            from pipeline.html_entity_decoder import HTMLEntityDecoder
            decoder = HTMLEntityDecoder()
            
            decoded, modified = decoder.decode_html_entities(content, str(filepath))
            
            if modified:
                # Write fixed content
                full_path.write_text(decoded, encoding='utf-8')
                self.logger.info(f"✅ Fixed HTML entities in {filepath}")
                
                # Verify the fix worked
                try:
                    import ast
                    ast.parse(decoded)
                    self.logger.info(f"✅ File now compiles successfully")
                except SyntaxError as e:
                    self.logger.warning(f"⚠️  File still has syntax errors after fix: {e}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to auto-fix HTML entities in {filepath}: {e}")
            return False
'''

# Integration point in execute() method
INTEGRATION_CODE = '''
        # CRITICAL: Auto-fix HTML entities BEFORE reading content
        # This prevents syntax errors from blocking QA analysis
        if filepath and filepath.endswith('.py'):
            if self._auto_fix_html_entities(filepath):
                self.logger.info(f"✅ HTML entities fixed, proceeding with QA")
                # File is now fixed, continue with normal QA
        
        # Read file content (now fixed if it had HTML entities)
        content = self.read_file(filepath)
'''

# Updated system prompt addition
SYSTEM_PROMPT_ADDITION = '''

CRITICAL - HTML Entity Issues:
If you detect syntax errors with patterns like:
- "unexpected character after line continuation character"
- Lines starting with \\&quot; or \\'
- HTML entities like &quot; or &#34;

These are HTML entity encoding issues. They should be AUTOMATICALLY FIXED before you see them.
If you still see them, the auto-fix failed. In that case:
1. Call fix_html_entities tool on the file
2. Wait for confirmation
3. Re-analyze the file
4. Only report_issue if fix_html_entities fails

DO NOT send HTML entity issues to debugging - they should be fixed in QA.
'''

print("=" * 60)
print("QA Phase HTML Entity Auto-Fix Integration")
print("=" * 60)
print()
print("This adds automatic HTML entity fixing to the QA phase.")
print()
print("Changes needed:")
print("1. Add _auto_fix_html_entities() method to QAPhase class")
print("2. Call it before reading file content in execute()")
print("3. Update system prompt to mention auto-fix")
print()
print("=" * 60)
print("Method to add:")
print("=" * 60)
print(AUTO_FIX_METHOD)
print()
print("=" * 60)
print("Integration in execute():")
print("=" * 60)
print(INTEGRATION_CODE)
print()
print("=" * 60)
print("System prompt addition:")
print("=" * 60)
print(SYSTEM_PROMPT_ADDITION)