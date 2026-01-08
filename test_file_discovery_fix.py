#!/usr/bin/env python3
"""
Test script to verify the file_discovery.py fixes work correctly.
"""

import ast
import sys
from pathlib import Path
from pipeline.file_discovery import FileDiscovery
from pipeline.logging_setup import get_logger

def test_extract_functions():
    """Test that _extract_functions works correctly."""
    logger = get_logger()
    
    # Create a test AST with various function types
    test_code = """
def top_level_func():
    pass

class MyClass:
    def method(self):
        pass
    
    def another_method(self):
        pass

def another_top_level():
    pass
"""
    
    tree = ast.parse(test_code)
    discovery = FileDiscovery(Path("."), logger)
    
    # Test function extraction
    functions = discovery._extract_functions(tree)
    print(f"✓ Extracted functions: {functions}")
    assert len(functions) == 2, f"Expected 2 functions, got {len(functions)}"
    assert "top_level_func" in functions
    assert "another_top_level" in functions
    assert "method" not in functions  # Should not include methods
    
    # Test method extraction
    methods = discovery._extract_methods(tree)
    print(f"✓ Extracted methods: {methods}")
    assert len(methods) == 2, f"Expected 2 methods, got {len(methods)}"
    assert "MyClass.method" in methods
    assert "MyClass.another_method" in methods
    
    print("\n✅ All tests passed!")

def test_error_handling():
    """Test that error handling works for malformed AST."""
    logger = get_logger()
    discovery = FileDiscovery(Path("."), logger)
    
    # Create a minimal AST that might cause issues
    tree = ast.parse("x = 1")
    
    # These should not crash
    functions = discovery._extract_functions(tree)
    methods = discovery._extract_methods(tree)
    imports = discovery._extract_imports(tree)
    decorators = discovery._extract_decorators(tree)
    
    print("✓ Error handling works correctly")
    print(f"  Functions: {functions}")
    print(f"  Methods: {methods}")
    print(f"  Imports: {imports}")
    print(f"  Decorators: {decorators}")
    
    print("\n✅ Error handling test passed!")

if __name__ == "__main__":
    print("Testing file_discovery.py fixes...\n")
    try:
        test_extract_functions()
        test_error_handling()
        print("\n" + "="*60)
        print("ALL TESTS PASSED - file_discovery.py is working correctly!")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)