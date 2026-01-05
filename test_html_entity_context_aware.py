#!/usr/bin/env python3
"""
Test HTML Entity Context-Aware Decoding

Tests that the decoder:
1. Fixes syntax errors (lines starting with &quot;)
2. Preserves valid escape sequences in strings
3. Preserves HTML entities in string content
4. Decodes entities in comments and docstrings
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.html_entity_decoder_v2 import HTMLEntityDecoder

def test_syntax_error_fix():
    """Test that syntax errors are fixed."""
    decoder = HTMLEntityDecoder()
    
    # Test case: Line starts with &quot; (syntax error)
    test = chr(92) + chr(34) * 3 + '\nDocstring\n' + chr(92) + chr(34) * 3
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    expected = '"""\nDocstring\n"""'
    assert decoded == expected, f"Expected {repr(expected)}, got {repr(decoded)}"
    assert modified == True, "Should be modified"
    print("✅ Test 1: Syntax error fix - PASS")

def test_preserve_string_escapes():
    """Test that valid escape sequences in strings are preserved."""
    decoder = HTMLEntityDecoder()
    
    # Test case: Valid escape in string literal
    test = 'text = "He said \&quot;Hello\&quot;"'
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    # Should NOT be modified - this is valid Python
    assert decoded == test, f"Should preserve valid escapes, got {repr(decoded)}"
    assert modified == False, "Should not be modified"
    print("✅ Test 2: Preserve string escapes - PASS")

def test_preserve_html_in_strings():
    """Test that HTML entities in string content are preserved."""
    decoder = HTMLEntityDecoder()
    
    # Test case: HTML entity in string literal
    test = 'html = "<div>&quot;text&quot;</div>"'
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    # Should NOT be modified - HTML entities in strings should be preserved
    assert decoded == test, f"Should preserve HTML in strings, got {repr(decoded)}"
    assert modified == False, "Should not be modified"
    print("✅ Test 3: Preserve HTML in strings - PASS")

def test_decode_in_comments():
    """Test that HTML entities in comments are decoded."""
    decoder = HTMLEntityDecoder()
    
    # Test case: HTML entity in comment
    test = '# This is a &quot;comment&quot;'
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    expected = '# This is a "comment"'
    assert decoded == expected, f"Expected {repr(expected)}, got {repr(decoded)}"
    assert modified == True, "Should be modified"
    print("✅ Test 4: Decode in comments - PASS")

def test_decode_in_docstrings():
    """Test that HTML entities in docstrings are decoded."""
    decoder = HTMLEntityDecoder()
    
    # Test case: HTML entity in docstring
    test = '''def foo():
    """
    This is a &quot;docstring&quot;
    """
    pass'''
    
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    expected = '''def foo():
    """
    This is a "docstring"
    """
    pass'''
    
    assert decoded == expected, f"Expected {repr(expected)}, got {repr(decoded)}"
    assert modified == True, "Should be modified"
    print("✅ Test 5: Decode in docstrings - PASS")

def test_complex_case():
    """Test complex case with multiple contexts."""
    decoder = HTMLEntityDecoder()
    
    # Test case: Mix of contexts
    test = chr(92) + chr(34) * 3 + '''
Module docstring with &quot;quotes&quot;
''' + chr(92) + chr(34) * 3 + '''

def foo():
    # Comment with &quot;quotes&quot;
    text = "String with \&quot;escaped\&quot; quotes"
    html = "<div>&quot;content&quot;</div>"
    return text
'''
    
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    # Check results
    assert '"""' in decoded, "Should have fixed docstring delimiter"
    assert chr(92) + chr(34) * 3 not in decoded, "Should not have backslash-quotes"
    assert 'Comment with "quotes"' in decoded, "Should decode comment"
    assert 'String with \&quot;escaped\&quot; quotes' in decoded, "Should preserve string escapes"
    assert '<div>&quot;content&quot;</div>' in decoded, "Should preserve HTML in strings"
    assert modified == True, "Should be modified"
    print("✅ Test 6: Complex case - PASS")

def test_raw_strings():
    """Test that raw strings are preserved."""
    decoder = HTMLEntityDecoder()
    
    # Test case: Raw string with pattern
    test = 'pattern = r"\&quot;[^\&quot;]*\&quot;"'
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    # Should NOT be modified - raw strings should be preserved
    assert decoded == test, f"Should preserve raw strings, got {repr(decoded)}"
    assert modified == False, "Should not be modified"
    print("✅ Test 7: Preserve raw strings - PASS")

def test_f_strings():
    """Test that f-strings are preserved."""
    decoder = HTMLEntityDecoder()
    
    # Test case: F-string with escapes
    test = 'msg = f"Value: \&quot;{value}\&quot;"'
    decoded, modified = decoder.decode_html_entities(test, "test.py")
    
    # Should NOT be modified - f-string escapes should be preserved
    assert decoded == test, f"Should preserve f-strings, got {repr(decoded)}"
    assert modified == False, "Should not be modified"
    print("✅ Test 8: Preserve f-strings - PASS")

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("HTML Entity Context-Aware Decoding Tests")
    print("=" * 60)
    print()
    
    try:
        test_syntax_error_fix()
        test_preserve_string_escapes()
        test_preserve_html_in_strings()
        test_decode_in_comments()
        test_decode_in_docstrings()
        test_complex_case()
        test_raw_strings()
        test_f_strings()
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())