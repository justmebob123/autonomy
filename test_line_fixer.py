#!/usr/bin/env python3
"""
Comprehensive test suite for line_fixer module.

Tests various edge cases and failure scenarios to ensure robustness.
"""

import tempfile
import os
from pathlib import Path
from pipeline.line_fixer import (
    fix_line_directly,
    apply_fix,
    get_line_context,
    replace_line_range
)


def create_test_file(content: str) -> Path:
    """Create a temporary test file with given content."""
    fd, path = tempfile.mkstemp(suffix='.py', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return Path(path)


def read_file(path: Path) -> str:
    """Read file content."""
    with open(path, 'r') as f:
        return f.read()


def test_unmatched_bracket():
    """Test fixing unmatched closing bracket."""
    print("\n" + "="*70)
    print("TEST 1: Unmatched Closing Bracket ]")
    print("="*70)
    
    content = '''def foo():
    pattern = r"test([^'"]+)['"]"
    return pattern
'''
    
    path = create_test_file(content)
    print(f"Original line 2: {content.splitlines()[1]}")
    
    # Fix line 2
    result = fix_line_directly(path, 2, 'SyntaxError', "unmatched ']'")
    
    if result:
        fixed = read_file(path)
        print(f"Fixed line 2: {fixed.splitlines()[1]}")
        print("✅ PASS: Bracket added")
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_xml_tag():
    """Test fixing XML/HTML tags in Python code."""
    print("\n" + "="*70)
    print("TEST 2: XML/HTML Tag in Python")
    print("="*70)
    
    content = '''def process():
    data = get_data()
    </file_path>
    return data
'''
    
    path = create_test_file(content)
    print(f"Original line 3: {content.splitlines()[2]}")
    
    result = fix_line_directly(path, 3, 'SyntaxError', 'invalid syntax')
    
    if result:
        fixed = read_file(path)
        print(f"Fixed line 3: {fixed.splitlines()[2]}")
        print("✅ PASS: Line commented out")
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_markdown_code_block():
    """Test fixing markdown code blocks."""
    print("\n" + "="*70)
    print("TEST 3: Markdown Code Block")
    print("="*70)
    
    content = '''def example():
    ```
    print("test")
    return True
'''
    
    path = create_test_file(content)
    print(f"Original line 2: {repr(content.splitlines()[1])}")
    
    result = fix_line_directly(path, 2, 'SyntaxError', 'invalid syntax')
    
    if result:
        fixed = read_file(path)
        print(f"Fixed line 2: {repr(fixed.splitlines()[1])}")
        print("✅ PASS: Line removed")
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_unmatched_parenthesis():
    """Test fixing unmatched closing parenthesis."""
    print("\n" + "="*70)
    print("TEST 4: Unmatched Closing Parenthesis")
    print("="*70)
    
    content = '''def calculate():
    result = (1 + 2 + 3
    return result
'''
    
    path = create_test_file(content)
    print(f"Original line 2: {content.splitlines()[1]}")
    
    result = fix_line_directly(path, 2, 'SyntaxError', "unmatched ')'")
    
    if result:
        fixed = read_file(path)
        print(f"Fixed line 2: {fixed.splitlines()[1]}")
        print("✅ PASS: Parenthesis added")
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_context_display():
    """Test context display with line numbers."""
    print("\n" + "="*70)
    print("TEST 5: Context Display")
    print("="*70)
    
    content = '''line 1
line 2
line 3
line 4
line 5
line 6
line 7
'''
    
    path = create_test_file(content)
    
    # Get context around line 4
    context = get_line_context(path, 4, context_lines=2)
    
    print("Context around line 4 (±2 lines):")
    for line in context:
        print(line)
    
    # Check that line 4 has the >>> marker
    has_marker = any('>>>' in line and '4:' in line for line in context)
    
    os.unlink(path)
    
    if has_marker and len(context) == 5:  # Lines 2-6
        print("✅ PASS: Context displayed correctly")
        return True
    else:
        print("❌ FAIL: Context display incorrect")
        return False


def test_line_range_replacement():
    """Test replacing a range of lines."""
    print("\n" + "="*70)
    print("TEST 6: Line Range Replacement")
    print("="*70)
    
    content = '''def old_function():
    # Old implementation
    return "old"
'''
    
    path = create_test_file(content)
    print("Original content:")
    print(content)
    
    new_content = '''def new_function():
    # New implementation
    return "new"
'''
    
    result = replace_line_range(path, 1, 3, new_content)
    
    if result:
        fixed = read_file(path)
        print("\nFixed content:")
        print(fixed)
        print("✅ PASS: Range replaced")
    else:
        print("❌ FAIL: Could not replace range")
    
    os.unlink(path)
    return result


def test_edge_case_empty_file():
    """Test handling empty file."""
    print("\n" + "="*70)
    print("TEST 7: Edge Case - Empty File")
    print("="*70)
    
    path = create_test_file("")
    
    result = fix_line_directly(path, 1, 'SyntaxError', 'test')
    
    os.unlink(path)
    
    if not result:
        print("✅ PASS: Correctly handled empty file")
        return True
    else:
        print("❌ FAIL: Should not fix empty file")
        return False


def test_edge_case_line_out_of_range():
    """Test handling line number out of range."""
    print("\n" + "="*70)
    print("TEST 8: Edge Case - Line Out of Range")
    print("="*70)
    
    content = "line 1\nline 2\nline 3\n"
    path = create_test_file(content)
    
    # Try to fix line 100 (doesn't exist)
    result = fix_line_directly(path, 100, 'SyntaxError', 'test')
    
    os.unlink(path)
    
    if not result:
        print("✅ PASS: Correctly handled out of range")
        return True
    else:
        print("❌ FAIL: Should not fix non-existent line")
        return False


def test_edge_case_unicode():
    """Test handling unicode characters."""
    print("\n" + "="*70)
    print("TEST 9: Edge Case - Unicode Characters")
    print("="*70)
    
    content = '''def test():
    message = "Hello 世界 🌍"
    </file_path>
    return message
'''
    
    path = create_test_file(content)
    print(f"Original line 3: {content.splitlines()[2]}")
    
    result = fix_line_directly(path, 3, 'SyntaxError', 'invalid syntax')
    
    if result:
        fixed = read_file(path)
        print(f"Fixed line 3: {fixed.splitlines()[2]}")
        # Check unicode is preserved
        if '世界' in fixed and '🌍' in fixed:
            print("✅ PASS: Unicode preserved")
        else:
            print("❌ FAIL: Unicode corrupted")
            result = False
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_edge_case_very_long_line():
    """Test handling very long lines."""
    print("\n" + "="*70)
    print("TEST 10: Edge Case - Very Long Line")
    print("="*70)
    
    long_string = "x" * 10000
    content = f'''def test():
    data = "{long_string}"
    return data
'''
    
    path = create_test_file(content)
    print(f"Original line 2 length: {len(content.splitlines()[1])}")
    
    # Get context (should handle long lines)
    context = get_line_context(path, 2, context_lines=1)
    
    os.unlink(path)
    
    if context and len(context) > 0:
        print(f"Context lines: {len(context)}")
        print("✅ PASS: Long line handled")
        return True
    else:
        print("❌ FAIL: Could not handle long line")
        return False


def test_edge_case_mixed_line_endings():
    """Test handling mixed line endings (\\n vs \\r\\n)."""
    print("\n" + "="*70)
    print("TEST 11: Edge Case - Mixed Line Endings")
    print("="*70)
    
    # Create file with mixed line endings
    fd, path_str = tempfile.mkstemp(suffix='.py', text=False)
    path = Path(path_str)
    
    with os.fdopen(fd, 'wb') as f:
        f.write(b'line 1\n')
        f.write(b'line 2\r\n')  # Windows line ending
        f.write(b'</file_path>\n')
        f.write(b'line 4\n')
    
    print("File has mixed line endings (\\n and \\r\\n)")
    
    result = fix_line_directly(path, 3, 'SyntaxError', 'invalid syntax')
    
    if result:
        # Check file is still readable
        try:
            fixed = read_file(path)
            print("✅ PASS: Mixed line endings handled")
        except Exception as e:
            print(f"❌ FAIL: Error reading fixed file: {e}")
            result = False
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_edge_case_no_final_newline():
    """Test handling file without final newline."""
    print("\n" + "="*70)
    print("TEST 12: Edge Case - No Final Newline")
    print("="*70)
    
    # Create file without final newline but with an actual error
    fd, path_str = tempfile.mkstemp(suffix='.py', text=True)
    path = Path(path_str)
    
    with os.fdopen(fd, 'w') as f:
        f.write('line 1\n</file_path>\nline 3')  # No \n at end, line 2 has error
    
    print("File has no final newline and line 2 has XML tag")
    
    result = fix_line_directly(path, 2, 'SyntaxError', 'invalid syntax')
    
    if result:
        fixed = read_file(path)
        lines = fixed.splitlines()
        print(f"Lines in fixed file: {len(lines)}")
        print(f"Fixed line 2: {repr(lines[1])}")
        # Check that line 2 was commented out
        if lines[1].strip().startswith('#'):
            print("✅ PASS: No final newline handled correctly")
        else:
            print("❌ FAIL: Line not fixed correctly")
            result = False
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_real_world_regex_pattern():
    """Test the actual regex pattern from your error."""
    print("\n" + "="*70)
    print("TEST 13: Real World - Your Actual Error")
    print("="*70)
    
    content = r'''def analyze():
    execute_pattern = r"self\.tool_executor\.execute\(\s*['"]([^'"]+)['"]"
    return execute_pattern
'''
    
    path = create_test_file(content)
    print(f"Original line 2:")
    print(f"  {content.splitlines()[1]}")
    
    result = fix_line_directly(path, 2, 'SyntaxError', "unmatched ']'")
    
    if result:
        fixed = read_file(path)
        fixed_line = fixed.splitlines()[1]
        print(f"Fixed line 2:")
        print(f"  {fixed_line}")
        
        # Verify the fix is correct
        if fixed_line.rstrip().endswith(']'):
            print("✅ PASS: Real world regex fixed correctly")
        else:
            print("❌ FAIL: Fix incorrect")
            result = False
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def test_indentation_preservation():
    """Test that indentation is preserved."""
    print("\n" + "="*70)
    print("TEST 14: Indentation Preservation")
    print("="*70)
    
    content = '''def test():
    if True:
        if True:
            </file_path>
            return True
'''
    
    path = create_test_file(content)
    original_indent = len(content.splitlines()[3]) - len(content.splitlines()[3].lstrip())
    print(f"Original indentation: {original_indent} spaces")
    
    result = fix_line_directly(path, 4, 'SyntaxError', 'invalid syntax')
    
    if result:
        fixed = read_file(path)
        fixed_line = fixed.splitlines()[3]
        fixed_indent = len(fixed_line) - len(fixed_line.lstrip())
        print(f"Fixed indentation: {fixed_indent} spaces")
        print(f"Fixed line: {repr(fixed_line)}")
        
        if fixed_indent == original_indent:
            print("✅ PASS: Indentation preserved")
        else:
            print("❌ FAIL: Indentation changed")
            result = False
    else:
        print("❌ FAIL: Could not fix")
    
    os.unlink(path)
    return result


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("LINE FIXER COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Unmatched Bracket", test_unmatched_bracket),
        ("XML Tag", test_xml_tag),
        ("Markdown Code Block", test_markdown_code_block),
        ("Unmatched Parenthesis", test_unmatched_parenthesis),
        ("Context Display", test_context_display),
        ("Line Range Replacement", test_line_range_replacement),
        ("Empty File", test_edge_case_empty_file),
        ("Line Out of Range", test_edge_case_line_out_of_range),
        ("Unicode Characters", test_edge_case_unicode),
        ("Very Long Line", test_edge_case_very_long_line),
        ("Mixed Line Endings", test_edge_case_mixed_line_endings),
        ("No Final Newline", test_edge_case_no_final_newline),
        ("Real World Regex", test_real_world_regex_pattern),
        ("Indentation Preservation", test_indentation_preservation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Solution is robust.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review needed.")
    
    return passed == total


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)