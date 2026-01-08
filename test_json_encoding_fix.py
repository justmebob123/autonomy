#!/usr/bin/env python3
"""
Test script to verify JSON encoding fix for code transmission.
Tests that code with backslashes, quotes, and special characters
is properly encoded and decoded without corruption.
"""

import json
import re


def convert_python_strings_to_json_OLD(text: str) -> str:
    """OLD VERSION - Uses HTML entities (BROKEN)"""
    def replace_triple_quotes(match):
        content = match.group(1)
        content = content.replace('\\', '\\\\')
        content = content.replace('"', r'&quot;')  # ❌ WRONG!
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        return f'"{content}"'
    
    text = re.sub(r'"""([\s\S]*?)"""', replace_triple_quotes, text)
    text = re.sub(r"'''([\s\S]*?)'''", replace_triple_quotes, text)
    return text


def convert_python_strings_to_json_NEW(text: str) -> str:
    """NEW VERSION - Uses proper JSON escaping (FIXED)"""
    def replace_triple_quotes(match):
        content = match.group(1)
        # Use json.dumps to properly escape the content
        # This handles all special characters correctly
        return json.dumps(content)
    
    text = re.sub(r'"""([\s\S]*?)"""', replace_triple_quotes, text)
    text = re.sub(r"'''([\s\S]*?)'''", replace_triple_quotes, text)
    return text


# Test cases with problematic code patterns
test_cases = [
    {
        "name": "Simple string with backslash-n",
        "code": '''"""print("Hello\\nWorld")"""''',
        "expected_in_code": "Hello\\nWorld"
    },
    {
        "name": "Docstring with quotes",
        "code": '''"""This is a "quoted" string"""''',
        "expected_in_code": 'This is a "quoted" string'
    },
    {
        "name": "Code with multiple backslashes",
        "code": '''"""path = "C:\\\\Users\\\\test\\\\file.txt" """''',
        "expected_in_code": "C:\\\\Users\\\\test\\\\file.txt"
    },
    {
        "name": "Mixed special characters",
        "code": '''"""Line 1\\nLine 2\\tTabbed\\r\\nWindows line"""''',
        "expected_in_code": "Line 1\\nLine 2\\tTabbed\\r\\nWindows line"
    },
    {
        "name": "Python code with continuation",
        "code": '''"""result = some_function(\\
    arg1="value1",\\
    arg2="value2"\\
)"""''',
        "expected_in_code": 'result = some_function(\\\n    arg1="value1",\\\n    arg2="value2"\\\n)'
    },
    {
        "name": "Regex pattern with backslashes",
        "code": '''"""pattern = r"\\\\d+\\\\.\\\\d+"  # Match decimal numbers"""''',
        "expected_in_code": 'pattern = r"\\\\d+\\\\.\\\\d+"  # Match decimal numbers'
    }
]


def test_encoding(test_case, converter_func, version_name):
    """Test a single case with the given converter"""
    print(f"\n{'='*70}")
    print(f"Test: {test_case['name']} ({version_name})")
    print(f"{'='*70}")
    
    original = test_case['code']
    print(f"Original: {original}")
    
    # Convert to JSON-compatible format
    converted = converter_func(original)
    print(f"Converted: {converted}")
    
    # Try to parse as JSON
    try:
        # Wrap in a JSON object
        json_str = f'{{"code": {converted}}}'
        parsed = json.loads(json_str)
        decoded_code = parsed['code']
        
        print(f"✓ JSON parsing successful")
        print(f"Decoded: {repr(decoded_code)}")
        
        # Check if the decoded code matches expected
        expected = test_case['expected_in_code']
        if expected in decoded_code:
            print(f"✓ Content verification passed")
            return True
        else:
            print(f"✗ Content verification FAILED")
            print(f"  Expected substring: {repr(expected)}")
            print(f"  Got: {repr(decoded_code)}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    print("="*70)
    print("JSON ENCODING FIX VERIFICATION TEST")
    print("="*70)
    print("\nTesting OLD version (with &quot; HTML entities)...")
    
    old_results = []
    for test_case in test_cases:
        result = test_encoding(test_case, convert_python_strings_to_json_OLD, "OLD")
        old_results.append(result)
    
    print("\n" + "="*70)
    print("Testing NEW version (with proper JSON escaping)...")
    
    new_results = []
    for test_case in test_cases:
        result = test_encoding(test_case, convert_python_strings_to_json_NEW, "NEW")
        new_results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"OLD version: {sum(old_results)}/{len(old_results)} tests passed")
    print(f"NEW version: {sum(new_results)}/{len(new_results)} tests passed")
    
    if sum(new_results) > sum(old_results):
        print("\n✓ FIX VERIFIED: New version handles more cases correctly!")
    elif sum(new_results) == len(new_results):
        print("\n✓ FIX VERIFIED: All tests pass with new version!")
    else:
        print("\n✗ WARNING: Some tests still failing with new version")
    
    return sum(new_results) == len(new_results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)