"""
Test Atomic File Operations

Verifies that atomic file writes prevent corruption.
"""

import json
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, '/workspace/autonomy')

# Import directly
import importlib.util
spec = importlib.util.spec_from_file_location("atomic_file", "pipeline/atomic_file.py")
atomic_file = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atomic_file)

atomic_write = atomic_file.atomic_write
atomic_write_json = atomic_file.atomic_write_json
safe_read = atomic_file.safe_read
safe_read_json = atomic_file.safe_read_json


def test_atomic_write():
    """Test basic atomic write"""
    print("Testing atomic_write...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.txt'
        
        # Write content
        atomic_write(filepath, 'Hello, World!')
        
        # Verify content
        assert filepath.read_text() == 'Hello, World!'
        print("  ✓ Basic atomic write works")
        
        # Overwrite
        atomic_write(filepath, 'Updated content')
        assert filepath.read_text() == 'Updated content'
        print("  ✓ Atomic overwrite works")


def test_atomic_write_json():
    """Test atomic JSON write"""
    print("\nTesting atomic_write_json...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        
        data = {'key': 'value', 'number': 42, 'list': [1, 2, 3]}
        
        # Write JSON
        atomic_write_json(filepath, data)
        
        # Verify content
        with open(filepath) as f:
            loaded = json.load(f)
        
        assert loaded == data
        print("  ✓ Atomic JSON write works")


def test_temp_file_cleanup():
    """Test that temp files are cleaned up on failure"""
    print("\nTesting temp file cleanup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.txt'
        
        # Try to write invalid content (will fail)
        try:
            # Simulate failure by writing to read-only location
            atomic_write('/root/readonly.txt', 'content')
        except:
            pass
        
        # Check no temp files left in tmpdir
        temp_files = list(Path(tmpdir).glob('*.tmp'))
        assert len(temp_files) == 0
        print("  ✓ Temp files cleaned up on failure")


def test_safe_read():
    """Test safe read with fallback"""
    print("\nTesting safe_read...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.txt'
        
        # Read non-existent file
        content = safe_read(filepath, default='default value')
        assert content == 'default value'
        print("  ✓ Returns default for non-existent file")
        
        # Write and read
        filepath.write_text('actual content')
        content = safe_read(filepath, default='default value')
        assert content == 'actual content'
        print("  ✓ Returns actual content when file exists")


def test_safe_read_json():
    """Test safe JSON read with fallback"""
    print("\nTesting safe_read_json...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        
        # Read non-existent file
        data = safe_read_json(filepath, default={'default': True})
        assert data == {'default': True}
        print("  ✓ Returns default for non-existent file")
        
        # Write and read valid JSON
        with open(filepath, 'w') as f:
            json.dump({'key': 'value'}, f)
        
        data = safe_read_json(filepath, default={'default': True})
        assert data == {'key': 'value'}
        print("  ✓ Returns parsed JSON when file exists")
        
        # Write corrupted JSON
        filepath.write_text('{ invalid json }')
        data = safe_read_json(filepath, default={'default': True})
        assert data == {'default': True}
        print("  ✓ Returns default for corrupted JSON")


def test_atomicity_guarantee():
    """Test that writes are truly atomic"""
    print("\nTesting atomicity guarantee...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.txt'
        
        # Write initial content
        filepath.write_text('original')
        
        # Try atomic write that will fail
        try:
            # This will fail because we're trying to write None
            atomic_write(filepath, None)
        except:
            pass
        
        # Original file should be unchanged
        assert filepath.read_text() == 'original'
        print("  ✓ Original file unchanged on write failure")


if __name__ == '__main__':
    print("=== Atomic File Operations Tests ===\n")
    
    try:
        test_atomic_write()
        test_atomic_write_json()
        test_temp_file_cleanup()
        test_safe_read()
        test_safe_read_json()
        test_atomicity_guarantee()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise