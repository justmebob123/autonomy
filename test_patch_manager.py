#!/usr/bin/env python3
"""
Test suite for patch_manager.py

Tests the patch-based file modification system with various edge cases
including multiple quotes, special characters, and complex strings.
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.patch_manager import PatchManager, apply_line_fix


def test_simple_line_change():
    """Test basic line replacement."""
    print("="*70)
    print("TEST 1: Simple Line Change")
    print("="*70)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("line 1\n")
        f.write("line 2\n")
        f.write("line 3\n")
        temp_file = Path(f.name)
    
    try:
        # Change line 2
        success, msg = apply_line_fix(
            temp_file,
            line_num=2,
            old_line="line 2\n",
            new_line="modified line 2\n"
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify
        content = temp_file.read_text()
        expected = "line 1\nmodified line 2\nline 3\n"
        assert content == expected, f"Content mismatch:\n{content}\nvs\n{expected}"
        print("✓ Content verified")
        
        return success
    finally:
        temp_file.unlink()


def test_multiple_quotes():
    """Test line with multiple single and double quotes."""
    print("\n" + "="*70)
    print("TEST 2: Multiple Quotes")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def func():\n')
        f.write('    pattern = r"test[\'\&quot;]pattern"\n')
        f.write('    return pattern\n')
        temp_file = Path(f.name)
    
    try:
        # Change the pattern line with complex quotes
        old_line = '    pattern = r"test[\'\&quot;]pattern"\n'
        new_line = '    pattern = r"""test[\'\&quot;]pattern"""\n'
        
        print(f"Old line: {repr(old_line)}")
        print(f"New line: {repr(new_line)}")
        
        success, msg = apply_line_fix(
            temp_file,
            line_num=2,
            old_line=old_line,
            new_line=new_line
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify
        lines = temp_file.read_text().splitlines(keepends=True)
        assert lines[1] == new_line, f"Line mismatch: {repr(lines[1])} vs {repr(new_line)}"
        print("✓ Content verified")
        
        return success
    finally:
        temp_file.unlink()


def test_regex_pattern():
    """Test the actual problematic regex pattern from analyze_integration_tools.py"""
    print("\n" + "="*70)
    print("TEST 3: Real-World Regex Pattern")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def analyze():\n')
        f.write('    # Find all tool_executor.execute calls\n')
        f.write('    execute_pattern = r"self\\.tool_executor\\.execute\\(\\s*[\'\&quot;]([^\'\&quot;]+)[\'\&quot;]\&quot;]"\n')
        f.write('    tool_calls = re.findall(execute_pattern, content)\n')
        temp_file = Path(f.name)
    
    try:
        # Fix the pattern (remove extra ])
        old_line = '    execute_pattern = r"self\\.tool_executor\\.execute\\(\\s*[\'\&quot;]([^\'\&quot;]+)[\'\&quot;]\&quot;]"\n'
        new_line = '    execute_pattern = r"""self\\.tool_executor\\.execute\\(\\s*[\'\&quot;]([^\'\&quot;]+)[\'\&quot;]"""\n'
        
        print(f"Old line: {repr(old_line)}")
        print(f"New line: {repr(new_line)}")
        
        success, msg = apply_line_fix(
            temp_file,
            line_num=3,
            old_line=old_line,
            new_line=new_line
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify syntax
        import ast
        content = temp_file.read_text()
        try:
            ast.parse(content)
            print("✓ Python syntax is valid")
        except SyntaxError as e:
            print(f"✗ Syntax error: {e}")
            return False
        
        return success
    finally:
        temp_file.unlink()


def test_special_characters():
    """Test line with various special characters."""
    print("\n" + "="*70)
    print("TEST 4: Special Characters")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('# Comment\n')
        f.write('text = "normal"\n')
        f.write('# Another comment\n')
        temp_file = Path(f.name)
    
    try:
        # Change to line with special chars: tabs, backslashes, quotes
        old_line = 'text = "normal"\n'
        new_line = 'text = "special\\t\\n\\r\\\\\&quot;chars"\n'
        
        print(f"Old line: {repr(old_line)}")
        print(f"New line: {repr(new_line)}")
        
        success, msg = apply_line_fix(
            temp_file,
            line_num=2,
            old_line=old_line,
            new_line=new_line
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify
        lines = temp_file.read_text().splitlines(keepends=True)
        assert lines[1] == new_line, f"Line mismatch: {repr(lines[1])} vs {repr(new_line)}"
        print("✓ Content verified")
        
        return success
    finally:
        temp_file.unlink()


def test_unicode_characters():
    """Test line with unicode characters."""
    print("\n" + "="*70)
    print("TEST 5: Unicode Characters")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write('# English\n')
        f.write('text = "hello"\n')
        f.write('# End\n')
        temp_file = Path(f.name)
    
    try:
        # Change to unicode
        old_line = 'text = "hello"\n'
        new_line = 'text = "你好 مرحبا Здравствуй 🎉"\n'
        
        print(f"Old line: {repr(old_line)}")
        print(f"New line: {repr(new_line)}")
        
        success, msg = apply_line_fix(
            temp_file,
            line_num=2,
            old_line=old_line,
            new_line=new_line
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify
        lines = temp_file.read_text().splitlines(keepends=True)
        assert lines[1] == new_line, f"Line mismatch: {repr(lines[1])} vs {repr(new_line)}"
        print("✓ Content verified")
        
        return success
    finally:
        temp_file.unlink()


def test_patch_tracking():
    """Test that patches are tracked with change numbers."""
    print("\n" + "="*70)
    print("TEST 6: Patch Tracking")
    print("="*70)
    
    manager = PatchManager()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('line 1\n')
        f.write('line 2\n')
        temp_file = Path(f.name)
    
    try:
        # Make a change
        success, msg = manager.apply_line_change(
            temp_file,
            line_num=1,
            old_line='line 1\n',
            new_line='changed line 1\n'
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Check patches were created
        patches = manager.list_patches(limit=1)
        assert len(patches) > 0, "No patches found"
        
        latest_patch = patches[0]
        print(f"✓ Patch created: {latest_patch.name}")
        
        # Get patch info
        info = manager.get_patch_info(latest_patch)
        print(f"  Change number: {info['change_number']}")
        print(f"  Timestamp: {info['timestamp']}")
        print(f"  File: {info['filename']}")
        print(f"  Line: {info['line']}")
        
        return success
    finally:
        temp_file.unlink()


def test_very_long_line():
    """Test line with 10000+ characters."""
    print("\n" + "="*70)
    print("TEST 7: Very Long Line (10K+ chars)")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('# Start\n')
        f.write('x = "short"\n')
        f.write('# End\n')
        temp_file = Path(f.name)
    
    try:
        # Create very long line
        old_line = 'x = "short"\n'
        new_line = 'x = "' + 'a' * 10000 + '"\n'
        
        print(f"Old line length: {len(old_line)}")
        print(f"New line length: {len(new_line)}")
        
        success, msg = apply_line_fix(
            temp_file,
            line_num=2,
            old_line=old_line,
            new_line=new_line
        )
        
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        print(f"Message: {msg}")
        
        # Verify
        lines = temp_file.read_text().splitlines(keepends=True)
        assert len(lines[1]) == len(new_line), f"Length mismatch: {len(lines[1])} vs {len(new_line)}"
        print("✓ Content verified")
        
        return success
    finally:
        temp_file.unlink()


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PATCH MANAGER TEST SUITE")
    print("="*70)
    
    tests = [
        test_simple_line_change,
        test_multiple_quotes,
        test_regex_pattern,
        test_special_characters,
        test_unicode_characters,
        test_patch_tracking,
        test_very_long_line,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())