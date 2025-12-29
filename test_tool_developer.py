#!/usr/bin/env python3
"""
Test ToolDeveloper functionality

Tests tool creation, validation, and testing.
"""

import sys
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir.parent))
sys.path.insert(0, str(project_dir))

def test_tool_creation():
    """Test creating a tool from template."""
    print("\n" + "="*80)
    print("TEST 1: Tool Creation from Template")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDeveloper
    
    developer = ToolDeveloper(str(project_dir))
    
    # Create a test tool
    result = developer.create_from_template('test_tool', {
        'description': 'A test tool for demonstration',
        'category': 'testing',
        'author': 'Test Suite',
        'parameters': {
            'input_text': 'str',
            'count': 'int'
        },
        'requires_filesystem': False,
        'timeout_seconds': 10
    })
    
    if result['success']:
        print(f"✓ Tool created successfully")
        print(f"  Filepath: {result['filepath']}")
        print(f"  Tool name: {result['tool_name']}")
    else:
        print(f"✗ Tool creation failed: {result.get('error')}")
    
    return result['success']

def test_tool_validation():
    """Test tool validation."""
    print("\n" + "="*80)
    print("TEST 2: Tool Validation")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDeveloper
    
    developer = ToolDeveloper(str(project_dir))
    
    # Validate existing tools
    tools_to_validate = ['analyze_imports', 'code_complexity', 'find_todos']
    
    for tool_name in tools_to_validate:
        result = developer.validate_tool(tool_name)
        
        if result['success']:
            print(f"✓ {tool_name}: Valid")
            if result.get('warnings'):
                for warning in result['warnings']:
                    print(f"  ⚠ Warning: {warning}")
        else:
            print(f"✗ {tool_name}: Invalid")
            for error in result.get('errors', []):
                print(f"  ✗ Error: {error}")
    
    return True

def test_tool_testing():
    """Test tool execution."""
    print("\n" + "="*80)
    print("TEST 3: Tool Testing")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDeveloper
    
    developer = ToolDeveloper(str(project_dir))
    
    # Test code_complexity tool
    print("\n✓ Testing 'code_complexity' tool...")
    
    # Create a test file
    test_file = project_dir / 'test_complexity.py'
    test_file.write_text("""
def simple_function():
    return 42

def complex_function(x):
    if x > 0:
        if x > 10:
            return x * 2
        else:
            return x + 1
    else:
        return 0
""")
    
    try:
        result = developer.test_tool('code_complexity', {
            'filepath': 'test_complexity.py'
        })
        
        if result['success']:
            print(f"✓ Tool test passed")
            output = result['output']
            if output.get('success'):
                metrics = output['result']['metrics']
                print(f"  Total functions: {metrics['total_functions']}")
                print(f"  Average complexity: {metrics['average_complexity']}")
                print(f"  Max complexity: {metrics['max_complexity']}")
        else:
            print(f"✗ Tool test failed: {result.get('error')}")
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
    
    return True

def test_tool_listing():
    """Test listing all tools."""
    print("\n" + "="*80)
    print("TEST 4: Tool Listing")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDeveloper
    
    developer = ToolDeveloper(str(project_dir))
    
    tools = developer.list_tools()
    
    print(f"✓ Found {len(tools)} custom tools:")
    for tool in tools:
        status = "✓" if tool['valid'] else "✗"
        print(f"  {status} {tool['name']}")
        if tool['errors']:
            for error in tool['errors']:
                print(f"      ✗ {error}")
        if tool['warnings']:
            for warning in tool['warnings']:
                print(f"      ⚠ {warning}")
    
    return True

def test_documentation_generation():
    """Test documentation generation."""
    print("\n" + "="*80)
    print("TEST 5: Documentation Generation")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDeveloper
    
    developer = ToolDeveloper(str(project_dir))
    
    # Generate docs for code_complexity
    result = developer.generate_docs('code_complexity')
    
    if result['success']:
        print(f"✓ Documentation generated")
        print(f"  Filepath: {result['filepath']}")
        print(f"\n  Preview:")
        print("  " + "\n  ".join(result['documentation'].split('\n')[:10]))
        print("  ...")
    else:
        print(f"✗ Documentation generation failed: {result.get('error')}")
    
    return result['success']

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TOOL DEVELOPER TEST SUITE")
    print("="*80)
    
    tests = [
        ("Tool Creation", test_tool_creation),
        ("Tool Validation", test_tool_validation),
        ("Tool Testing", test_tool_testing),
        ("Tool Listing", test_tool_listing),
        ("Documentation Generation", test_documentation_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())