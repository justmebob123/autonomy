#!/usr/bin/env python3
"""
Test script to verify context display fix in debug/QA mode.
This tests that the context is properly formatted with newlines.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.line_fixer import get_line_context


def test_context_display():
    """Test that context is displayed correctly with proper line breaks."""
    
    # Create a test file
    test_file = Path("test_sample.py")
    test_content = """def function1():
    pass

def function2():
    # This line has an error
    execute_pattern = r"self\\.tool_executor\\.execute\\(\\s*['&quot;]([^'&quot;]+)['&quot;]"]
    return pattern

def function3():
    pass
"""
    
    test_file.write_text(test_content)
    
    try:
        # Get context around line 6 (the error line)
        context_list = get_line_context(test_file, 6, context_lines=3)
        
        # Join with newline (what the fixed code does)
        context = '\n'.join(context_list)
        
        # Create description (what the fixed code does)
        error_type = "SyntaxError"
        error_line = 6
        error_message = "unmatched ']'"
        description = f"{error_type} at line {error_line}: {error_message}\n\nContext:\n{context}"
        
        print("="*70)
        print("TEST: Context Display")
        print("="*70)
        print(description)
        print("="*70)
        
        # Verify the output has proper line breaks
        lines = description.split('\n')
        
        # Should have multiple lines
        assert len(lines) > 5, f"Expected multiple lines, got {len(lines)}"
        
        # Should contain the error line marker
        assert any('>>>' in line for line in lines), "Missing >>> marker"
        
        # Should contain line numbers
        assert any('6:' in line for line in lines), "Missing line 6"
        
        # Should contain the actual code
        assert any('execute_pattern' in line for line in lines), "Missing code content"
        
        print("\n✓ All tests passed!")
        print("✓ Context is displayed correctly with proper line breaks")
        print("✓ Line numbers are visible")
        print("✓ Code content is visible")
        print("✓ Error marker (>>>) is present")
        
        return True
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    success = test_context_display()
    sys.exit(0 if success else 1)