"""
Test Result Protocol Implementation

Verifies that the Result protocol and adapters work correctly.
"""

import subprocess
from pipeline.result_protocol import Result, SubprocessResult, DictResult, ensure_result


def test_subprocess_result():
    """Test SubprocessResult adapter"""
    print("Testing SubprocessResult...")
    
    # Successful command
    proc = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    result = SubprocessResult(proc)
    
    assert result.success == True
    assert 'test' in result.data
    assert result.error is None
    assert result.metadata['returncode'] == 0
    print("  ✓ Successful subprocess result works")
    
    # Failed command
    proc = subprocess.run(['ls', '/nonexistent'], capture_output=True, text=True)
    result = SubprocessResult(proc)
    
    assert result.success == False
    assert result.error is not None
    assert result.metadata['returncode'] != 0
    print("  ✓ Failed subprocess result works")


def test_dict_result():
    """Test DictResult adapter"""
    print("\nTesting DictResult...")
    
    # Success dict
    result = DictResult({'success': True, 'data': {'key': 'value'}, 'extra': 'metadata'})
    
    assert result.success == True
    assert result.data == {'key': 'value'}
    assert result.error is None
    assert result.metadata == {'extra': 'metadata'}
    print("  ✓ Success dict result works")
    
    # Failure dict
    result = DictResult({'success': False, 'error': 'Something went wrong'})
    
    assert result.success == False
    assert result.error == 'Something went wrong'
    print("  ✓ Failure dict result works")
    
    # Dict without success key (defaults to True)
    result = DictResult({'data': 'some data'})
    
    assert result.success == True
    assert result.data == {'data': 'some data'}
    print("  ✓ Dict without success key defaults to True")


def test_ensure_result():
    """Test ensure_result function"""
    print("\nTesting ensure_result...")
    
    # Test with subprocess
    proc = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    result = ensure_result(proc)
    assert isinstance(result, SubprocessResult)
    assert result.success == True
    print("  ✓ ensure_result wraps subprocess correctly")
    
    # Test with dict
    result = ensure_result({'success': True, 'data': 'test'})
    assert isinstance(result, DictResult)
    assert result.success == True
    print("  ✓ ensure_result wraps dict correctly")
    
    # Test with object already implementing Result
    dict_result = DictResult({'success': True})
    result = ensure_result(dict_result)
    assert result is dict_result
    print("  ✓ ensure_result returns Result objects as-is")


def test_protocol_compliance():
    """Test that adapters implement Result protocol"""
    print("\nTesting protocol compliance...")
    
    proc = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    subprocess_result = SubprocessResult(proc)
    
    dict_result = DictResult({'success': True, 'data': 'test'})
    
    # Check protocol compliance
    assert isinstance(subprocess_result, Result)
    assert isinstance(dict_result, Result)
    print("  ✓ Adapters implement Result protocol")


if __name__ == '__main__':
    print("=== Result Protocol Tests ===\n")
    
    try:
        test_subprocess_result()
        test_dict_result()
        test_ensure_result()
        test_protocol_compliance()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise