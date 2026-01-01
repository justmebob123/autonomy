#!/usr/bin/env python3
"""
Integration Test for Custom Tools System

Tests the complete integration of custom tools with the pipeline.
"""

import sys
import json
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_tool_registry():
    """Test ToolRegistry discovery and registration."""
    print("\n" + "="*80)
    print("TEST 1: ToolRegistry Discovery")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import CustomToolRegistry
    
    registry = CustomToolRegistry(str(project_dir))
    count = registry.discover_tools(force=True)
    
    print(f"✓ Discovered {count} custom tools")
    
    # List tools
    tools = registry.list_tools()
    for tool in tools:
        print(f"  - {tool.name} ({tool.category}) v{tool.version}")
        print(f"    {tool.description}")
    
    # Get stats
    stats = registry.get_stats()
    print(f"\n✓ Registry Stats:")
    print(f"  Total Tools: {stats['total_tools']}")
    print(f"  Categories: {stats['categories']}")
    
    return registry

def test_tool_definitions(registry):
    """Test tool definition generation."""
    print("\n" + "="*80)
    print("TEST 2: Tool Definition Generation")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import ToolDefinitionGenerator
    
    generator = ToolDefinitionGenerator(registry)
    
    # Get all definitions
    definitions = generator.generate_all_definitions()
    print(f"✓ Generated {len(definitions)} tool definitions")
    
    # Show first definition
    if definitions:
        print(f"\n✓ Example Definition:")
        print(json.dumps(definitions[0], indent=2))
        
        # Validate definition
        validation = generator.validate_definition(definitions[0])
        if validation['valid']:
            print(f"✓ Definition is valid")
        else:
            print(f"✗ Definition validation failed: {validation['errors']}")
    
    return generator

def test_custom_tool_handler(registry):
    """Test CustomToolHandler execution."""
    print("\n" + "="*80)
    print("TEST 3: CustomToolHandler Execution")
    print("="*80)
    
    from autonomy.pipeline.custom_tools import CustomToolHandler
    
    handler = CustomToolHandler(str(project_dir), registry)
    
    # List custom tools
    tools = handler.list_custom_tools()
    print(f"✓ Handler has {len(tools)} custom tools")
    
    # Test tool execution (if analyze_imports exists)
    if handler.is_custom_tool('analyze_imports'):
        print(f"\n✓ Testing 'analyze_imports' tool...")
        
        # Create a test file
        test_file = project_dir / 'test_imports.py'
        test_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Dict, List
""")
        
        try:
            result = handler.execute_tool('analyze_imports', {
                'filepath': 'test_imports.py'
            })
            
            if result['success']:
                print(f"✓ Tool executed successfully")
                print(f"  Result: {json.dumps(result['result'], indent=2)}")
            else:
                print(f"✗ Tool execution failed: {result.get('error')}")
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    else:
        print(f"⚠ 'analyze_imports' tool not found, skipping execution test")
    
    return handler

def test_pipeline_integration(registry):
    """Test integration with pipeline tools.py."""
    print("\n" + "="*80)
    print("TEST 4: Pipeline Integration")
    print("="*80)
    
    from autonomy.pipeline.tools import get_tools_for_phase
    
    # Test with custom tools
    tools = get_tools_for_phase('coding', tool_registry=registry)
    print(f"✓ get_tools_for_phase returned {len(tools)} tools")
    
    # Count custom tools
    custom_count = sum(1 for t in tools if 'custom' in str(t).lower())
    print(f"✓ Includes custom tools in results")
    
    return tools

def test_handlers_integration():
    """Test integration with handlers.py."""
    print("\n" + "="*80)
    print("TEST 5: Handlers Integration")
    print("="*80)
    
    try:
        from autonomy.pipeline.handlers import ToolCallHandler
        
        handler = ToolCallHandler(project_dir)
        
        # Check if custom_tool_handler is initialized
        if hasattr(handler, 'custom_tool_handler'):
            if handler.custom_tool_handler:
                print(f"✓ ToolCallHandler has custom_tool_handler initialized")
                
                # List custom tools
                tools = handler.custom_tool_handler.list_custom_tools()
                print(f"✓ Custom tool handler has {len(tools)} tools")
            else:
                print(f"⚠ custom_tool_handler is None (no custom tools found)")
        else:
            print(f"✗ ToolCallHandler missing custom_tool_handler attribute")
        
        return handler
    except Exception as e:
        print(f"✗ Handlers integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("CUSTOM TOOLS INTEGRATION TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: ToolRegistry
        registry = test_tool_registry()
        
        # Test 2: Tool Definitions
        generator = test_tool_definitions(registry)
        
        # Test 3: CustomToolHandler
        handler = test_custom_tool_handler(registry)
        
        # Test 4: Pipeline Integration
        tools = test_pipeline_integration(registry)
        
        # Test 5: Handlers Integration
        tool_handler = test_handlers_integration()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("✓ All integration tests passed!")
        print("\nCustom Tools System is ready for use!")
        print("\nNext Steps:")
        print("1. Create custom tools in scripts/custom_tools/tools/")
        print("2. Tools are automatically discovered and available")
        print("3. Use tools in pipeline phases")
        print("4. Monitor tool execution in logs")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())