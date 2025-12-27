"""
Test Suite for UnifiedModelTool

Tests the unified model communication layer that merges
Client and ModelTool functionality.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestration.unified_model_tool import (
    UnifiedModelTool,
    create_unified_model_tool
)


class MockClient:
    """Mock Client for testing"""
    
    def __init__(self, model_name: str, host: str):
        self.model_name = model_name
        self.host = host
        self.call_count = 0
    
    def generate(self, messages, tools=None, temperature=0.7, max_tokens=None):
        """Mock generate method"""
        self.call_count += 1
        
        # Simulate response
        return {
            'message': {
                'role': 'assistant',
                'content': 'This is a mock response from the model.',
                'tool_calls': [
                    {
                        'function': {
                            'name': 'test_tool',
                            'arguments': {'param': 'value'}
                        }
                    }
                ] if tools else []
            },
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }


def test_initialization():
    """Test UnifiedModelTool initialization"""
    print("\n" + "="*60)
    print("TEST 1: Initialization")
    print("="*60)
    
    # Test with mock client
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing basic initialization...")
    assert tool.model_name == "qwen2.5:14b"
    assert tool.host == "http://localhost:11434"
    assert tool.context_window == 8192  # 14b model
    print("   ✓ Basic properties set correctly")
    
    print("\n2. Testing client creation...")
    assert tool.client is not None
    assert isinstance(tool.client, MockClient)
    print("   ✓ Client created successfully")
    
    print("\n3. Testing statistics initialization...")
    stats = tool.get_stats()
    assert stats['total_calls'] == 0
    assert stats['successful_calls'] == 0
    assert stats['failed_calls'] == 0
    assert stats['total_tokens'] == 0
    print("   ✓ Statistics initialized correctly")
    
    print("\n✅ TEST 1 PASSED: Initialization")
    return True


def test_context_window_detection():
    """Test context window auto-detection"""
    print("\n" + "="*60)
    print("TEST 2: Context Window Detection")
    print("="*60)
    
    test_cases = [
        ("qwen2.5-coder:32b", 16384),
        ("qwen2.5:32b", 16384),
        ("qwen2.5:14b", 8192),
        ("qwen2.5:7b", 4096),
        ("gemma:7b", 4096),
        ("unknown:model", 8192),  # default
    ]
    
    for model_name, expected_window in test_cases:
        tool = UnifiedModelTool(
            model_name,
            "http://localhost:11434",
            client_class=MockClient
        )
        print(f"\n   {model_name}: {tool.context_window} tokens")
        assert tool.context_window == expected_window
    
    print("\n✅ TEST 2 PASSED: Context Window Detection")
    return True


def test_execute_basic():
    """Test basic execution"""
    print("\n" + "="*60)
    print("TEST 3: Basic Execution")
    print("="*60)
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing basic message execution...")
    messages = [{"role": "user", "content": "Hello"}]
    result = tool.execute(messages)
    
    assert result['success'] == True
    assert 'response' in result
    assert 'tool_calls' in result
    assert 'usage' in result
    print("   ✓ Execution successful")
    print(f"   ✓ Response: {result['response'][:50]}...")
    
    print("\n2. Testing statistics update...")
    stats = tool.get_stats()
    assert stats['total_calls'] == 1
    assert stats['successful_calls'] == 1
    assert stats['failed_calls'] == 0
    assert stats['total_tokens'] == 150
    print(f"   ✓ Statistics updated: {stats['total_calls']} calls, {stats['total_tokens']} tokens")
    
    print("\n✅ TEST 3 PASSED: Basic Execution")
    return True


def test_execute_with_system_prompt():
    """Test execution with system prompt"""
    print("\n" + "="*60)
    print("TEST 4: Execution with System Prompt")
    print("="*60)
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing with system prompt...")
    messages = [{"role": "user", "content": "Hello"}]
    system_prompt = "You are a helpful assistant."
    
    result = tool.execute(messages, system_prompt=system_prompt)
    
    assert result['success'] == True
    print("   ✓ Execution with system prompt successful")
    
    print("\n✅ TEST 4 PASSED: Execution with System Prompt")
    return True


def test_execute_with_tools():
    """Test execution with tools"""
    print("\n" + "="*60)
    print("TEST 5: Execution with Tools")
    print("="*60)
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing with tool definitions...")
    messages = [{"role": "user", "content": "Use a tool"}]
    tools = [
        {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                }
            }
        }
    ]
    
    result = tool.execute(messages, tools=tools)
    
    assert result['success'] == True
    assert len(result['tool_calls']) > 0
    print(f"   ✓ Tool calls parsed: {len(result['tool_calls'])} call(s)")
    
    print("\n2. Testing tool call structure...")
    tool_call = result['tool_calls'][0]
    assert 'name' in tool_call
    assert 'parameters' in tool_call
    print(f"   ✓ Tool call: {tool_call['name']} with params {tool_call['parameters']}")
    
    print("\n✅ TEST 5 PASSED: Execution with Tools")
    return True


def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("TEST 6: Error Handling")
    print("="*60)
    
    class FailingClient:
        """Client that always fails"""
        def __init__(self, model_name, host):
            pass
        
        def generate(self, messages, tools=None, temperature=0.7, max_tokens=None):
            raise Exception("Simulated failure")
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=FailingClient
    )
    
    print("\n1. Testing error handling...")
    messages = [{"role": "user", "content": "Hello"}]
    result = tool.execute(messages)
    
    assert result['success'] == False
    assert 'error' in result
    assert result['response'] == ''
    assert result['tool_calls'] == []
    print("   ✓ Error handled gracefully")
    print(f"   ✓ Error message: {result['error']}")
    
    print("\n2. Testing failure statistics...")
    stats = tool.get_stats()
    assert stats['total_calls'] == 1
    assert stats['successful_calls'] == 0
    assert stats['failed_calls'] == 1
    print(f"   ✓ Failure tracked: {stats['failed_calls']} failure(s)")
    
    print("\n✅ TEST 6 PASSED: Error Handling")
    return True


def test_statistics():
    """Test statistics tracking"""
    print("\n" + "="*60)
    print("TEST 7: Statistics Tracking")
    print("="*60)
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing multiple calls...")
    for i in range(5):
        messages = [{"role": "user", "content": f"Message {i}"}]
        tool.execute(messages)
    
    stats = tool.get_stats()
    print(f"   ✓ Total calls: {stats['total_calls']}")
    print(f"   ✓ Successful calls: {stats['successful_calls']}")
    print(f"   ✓ Total tokens: {stats['total_tokens']}")
    print(f"   ✓ Success rate: {stats['success_rate']:.2%}")
    print(f"   ✓ Avg time: {stats['avg_time']:.3f}s")
    print(f"   ✓ Avg tokens: {stats['avg_tokens']:.1f}")
    
    assert stats['total_calls'] == 5
    assert stats['successful_calls'] == 5
    assert stats['success_rate'] == 1.0
    
    print("\n2. Testing statistics reset...")
    tool.reset_stats()
    stats = tool.get_stats()
    assert stats['total_calls'] == 0
    print("   ✓ Statistics reset successfully")
    
    print("\n✅ TEST 7 PASSED: Statistics Tracking")
    return True


def test_factory_function():
    """Test factory function"""
    print("\n" + "="*60)
    print("TEST 8: Factory Function")
    print("="*60)
    
    print("\n1. Testing create_unified_model_tool...")
    tool = create_unified_model_tool(
        "qwen2.5:14b",
        "http://localhost:11434"
    )
    
    assert isinstance(tool, UnifiedModelTool)
    assert tool.model_name == "qwen2.5:14b"
    print("   ✓ Factory function works correctly")
    
    print("\n✅ TEST 8 PASSED: Factory Function")
    return True


def test_backward_compatibility():
    """Test backward compatibility with existing code"""
    print("\n" + "="*60)
    print("TEST 9: Backward Compatibility")
    print("="*60)
    
    tool = UnifiedModelTool(
        "qwen2.5:14b",
        "http://localhost:11434",
        client_class=MockClient
    )
    
    print("\n1. Testing ModelTool-style interface...")
    # Should work like ModelTool
    result = tool.execute(
        messages=[{"role": "user", "content": "test"}],
        system_prompt="You are helpful"
    )
    assert result['success']
    assert 'response' in result
    assert 'tool_calls' in result
    print("   ✓ ModelTool-style interface works")
    
    print("\n2. Testing Client-style usage...")
    # Should work with Client patterns
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "test"}
    ]
    result = tool.execute(messages)
    assert result['success']
    print("   ✓ Client-style usage works")
    
    print("\n✅ TEST 9 PASSED: Backward Compatibility")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("UNIFIED MODEL TOOL TEST SUITE")
    print("="*60)
    
    tests = [
        ("Initialization", test_initialization),
        ("Context Window Detection", test_context_window_detection),
        ("Basic Execution", test_execute_basic),
        ("Execution with System Prompt", test_execute_with_system_prompt),
        ("Execution with Tools", test_execute_with_tools),
        ("Error Handling", test_error_handling),
        ("Statistics Tracking", test_statistics),
        ("Factory Function", test_factory_function),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:40s} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)