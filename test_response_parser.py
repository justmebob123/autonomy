"""
Unit Tests for ResponseParser

Tests the critical parse_response() method to ensure it always returns
a tuple (tool_calls, content) and handles various response formats correctly.
"""

import unittest
from unittest.mock import Mock, MagicMock
from pipeline.client import ResponseParser


class TestResponseParser(unittest.TestCase):
    """Test suite for ResponseParser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ResponseParser()
    
    def test_parse_response_returns_tuple(self):
        """Test that parse_response always returns a tuple"""
        response = {
            "message": {
                "content": "Test content",
                "tool_calls": []
            }
        }
        
        result = self.parser.parse_response(response)
        
        # CRITICAL: Must be a tuple, not a dict
        self.assertIsInstance(result, tuple, "parse_response must return a tuple")
        self.assertEqual(len(result), 2, "Tuple must have exactly 2 elements")
    
    def test_parse_response_with_native_tool_calls(self):
        """Test parsing response with native tool calls"""
        response = {
            "message": {
                "content": "Using tools",
                "tool_calls": [
                    {
                        "function": {
                            "name": "create_file",
                            "arguments": {"path": "test.py", "content": "print('hello')"}
                        }
                    }
                ]
            }
        }
        
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertIsInstance(tool_calls, list)
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["function"]["name"], "create_file")
        self.assertEqual(content, "Using tools")
    
    def test_parse_response_with_no_tool_calls(self):
        """Test parsing response with no tool calls"""
        response = {
            "message": {
                "content": "Just text response",
                "tool_calls": []
            }
        }
        
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertIsInstance(tool_calls, list)
        self.assertEqual(len(tool_calls), 0)
        self.assertEqual(content, "Just text response")
    
    def test_parse_response_empty_response(self):
        """Test parsing empty response"""
        response = {
            "message": {
                "content": "",
                "tool_calls": []
            }
        }
        
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertIsInstance(tool_calls, list)
        self.assertEqual(len(tool_calls), 0)
        self.assertEqual(content, "")
    
    def test_parse_response_missing_message(self):
        """Test parsing response with missing message field"""
        response = {}
        
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertIsInstance(tool_calls, list)
        self.assertEqual(len(tool_calls), 0)
        self.assertEqual(content, "")
    
    def test_parse_response_tuple_unpacking(self):
        """Test that tuple can be unpacked correctly"""
        response = {
            "message": {
                "content": "Test",
                "tool_calls": [{"function": {"name": "test_tool"}}]
            }
        }
        
        # This is how it should be used in the codebase
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertIsInstance(tool_calls, list)
        self.assertIsInstance(content, str)
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(content, "Test")
    
    def test_parse_response_with_tools_parameter(self):
        """Test parsing with tools parameter provided"""
        response = {
            "message": {
                "content": "create_file test.py",
                "tool_calls": []
            }
        }
        
        tools = [
            {
                "name": "create_file",
                "description": "Create a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            }
        ]
        
        tool_calls, content = self.parser.parse_response(response, tools)
        
        # Should return tuple even with tools parameter
        self.assertIsInstance(tool_calls, list)
        self.assertIsInstance(content, str)
    
    def test_parse_response_multiple_tool_calls(self):
        """Test parsing response with multiple tool calls"""
        response = {
            "message": {
                "content": "Multiple operations",
                "tool_calls": [
                    {"function": {"name": "tool1", "arguments": {}}},
                    {"function": {"name": "tool2", "arguments": {}}},
                    {"function": {"name": "tool3", "arguments": {}}}
                ]
            }
        }
        
        tool_calls, content = self.parser.parse_response(response)
        
        self.assertEqual(len(tool_calls), 3)
        self.assertEqual(tool_calls[0]["function"]["name"], "tool1")
        self.assertEqual(tool_calls[1]["function"]["name"], "tool2")
        self.assertEqual(tool_calls[2]["function"]["name"], "tool3")
    
    def test_parse_response_type_safety(self):
        """Test that return types are always correct"""
        test_cases = [
            {"message": {"content": "test", "tool_calls": []}},
            {"message": {"content": "", "tool_calls": []}},
            {"message": {}},
            {},
        ]
        
        for response in test_cases:
            result = self.parser.parse_response(response)
            
            # Must always be a tuple
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            
            # First element must be a list
            self.assertIsInstance(result[0], list)
            
            # Second element must be a string
            self.assertIsInstance(result[1], str)
    
    def test_parse_response_not_dict(self):
        """Test that result is NOT a dict (regression test for the bug)"""
        response = {
            "message": {
                "content": "test",
                "tool_calls": []
            }
        }
        
        result = self.parser.parse_response(response)
        
        # CRITICAL: This was the bug - treating tuple as dict
        self.assertNotIsInstance(result, dict, "Result must NOT be a dict")
        
        # Verify that calling .get() would fail (as it should)
        with self.assertRaises(AttributeError):
            result.get("tool_calls")  # This should fail


class TestResponseParserIntegration(unittest.TestCase):
    """Integration tests for ResponseParser usage patterns"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ResponseParser()
    
    def test_correct_usage_pattern(self):
        """Test the correct way to use parse_response"""
        response = {
            "message": {
                "content": "Creating file",
                "tool_calls": [
                    {"function": {"name": "create_file", "arguments": {}}}
                ]
            }
        }
        
        # CORRECT: Unpack the tuple
        tool_calls, content = self.parser.parse_response(response)
        
        # Use the unpacked values
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(content, "Creating file")
    
    def test_incorrect_usage_pattern_fails(self):
        """Test that incorrect usage pattern fails (as it should)"""
        response = {
            "message": {
                "content": "test",
                "tool_calls": []
            }
        }
        
        # INCORRECT: Treating result as dict
        result = self.parser.parse_response(response)
        
        # This should fail with AttributeError
        with self.assertRaises(AttributeError):
            tool_calls = result.get("tool_calls", [])
    
    def test_usage_in_base_phase(self):
        """Test usage pattern from base.py (after fix)"""
        response = {
            "message": {
                "content": "Response text",
                "tool_calls": [{"function": {"name": "test"}}]
            }
        }
        
        # This is how it's used in base.py after the fix
        tool_calls_parsed, _ = self.parser.parse_response(response)
        
        result = {
            "content": response["message"]["content"],
            "tool_calls": tool_calls_parsed,
            "raw_response": response
        }
        
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["content"], "Response text")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestResponseParser))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseParserIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)