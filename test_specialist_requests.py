"""
Test Specialist Request Handler

Verifies that specialist requests are detected and handled correctly.
"""

from pipeline.specialist_request_handler import SpecialistRequestHandler


class MockSpecialist:
    """Mock specialist for testing."""
    
    def __init__(self, name):
        self.name = name
    
    def validate_code(self, **kwargs):
        return {
            'success': True,
            'response': f"{self.name} specialist validated the code"
        }
    
    def reason_about(self, **kwargs):
        return {
            'success': True,
            'response': f"{self.name} specialist provided reasoning"
        }
    
    def analyze_code(self, **kwargs):
        return {
            'success': True,
            'response': f"{self.name} specialist analyzed the code"
        }


def test_detect_coding_request():
    """Test detection of coding specialist requests."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    # Test various coding request phrases
    test_messages = [
        "I need help with the code",
        "Can you validate this code?",
        "Please review this implementation",
        "I need a coding specialist to check this",
    ]
    
    for msg in test_messages:
        request = handler.detect_request(msg)
        assert request is not None, f"Failed to detect request in: {msg}"
        assert request['specialist'] == 'coding', f"Wrong specialist for: {msg}"
        print(f"✅ Detected coding request: {msg[:50]}")


def test_detect_reasoning_request():
    """Test detection of reasoning specialist requests."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    # Test various reasoning request phrases
    test_messages = [
        "I need help thinking through this",
        "Can you help me reason about this?",
        "What would be the best approach?",
        "I need strategic help with this",
    ]
    
    for msg in test_messages:
        request = handler.detect_request(msg)
        assert request is not None, f"Failed to detect request in: {msg}"
        assert request['specialist'] == 'reasoning', f"Wrong specialist for: {msg}"
        print(f"✅ Detected reasoning request: {msg[:50]}")


def test_detect_analysis_request():
    """Test detection of analysis specialist requests."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    # Test various analysis request phrases
    test_messages = [
        "I need help analyzing this",
        "Can you do a quick review?",
        "Please analyze this code",
        "I need an analysis specialist",
    ]
    
    for msg in test_messages:
        request = handler.detect_request(msg)
        assert request is not None, f"Failed to detect request in: {msg}"
        assert request['specialist'] == 'analysis', f"Wrong specialist for: {msg}"
        print(f"✅ Detected analysis request: {msg[:50]}")


def test_no_request():
    """Test that normal messages don't trigger specialist requests."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    # Test messages that should NOT trigger requests
    test_messages = [
        "I will create the file now",
        "The code looks good",
        "Let me implement this feature",
        "I'm going to use the create_file tool",
    ]
    
    for msg in test_messages:
        request = handler.detect_request(msg)
        assert request is None, f"False positive for: {msg}"
        print(f"✅ No false positive: {msg[:50]}")


def test_handle_request():
    """Test handling of specialist requests."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    # Test handling coding request
    request = {
        'specialist': 'coding',
        'context': 'Can you validate this code?',
        'pattern_matched': 'validate.*code'
    }
    
    task_context = {
        'file_path': 'test.py',
        'code': 'def test(): pass'
    }
    
    result = handler.handle_request(request, task_context)
    assert result['success'], "Request handling failed"
    assert 'validated' in result['response'].lower(), "Unexpected response"
    print(f"✅ Request handled: {result['response'][:50]}")


def test_format_response():
    """Test formatting of specialist responses."""
    handler = SpecialistRequestHandler({
        'coding': MockSpecialist('coding'),
        'reasoning': MockSpecialist('reasoning'),
        'analysis': MockSpecialist('analysis')
    })
    
    result = {
        'success': True,
        'response': 'The code looks good'
    }
    
    formatted = handler.format_specialist_response('coding', result)
    assert '[Coding Specialist]' in formatted, "Missing specialist header"
    assert 'The code looks good' in formatted, "Missing response content"
    print(f"✅ Response formatted correctly")


if __name__ == '__main__':
    print("Testing Specialist Request Handler\n")
    
    print("Test 1: Detect coding requests")
    test_detect_coding_request()
    print()
    
    print("Test 2: Detect reasoning requests")
    test_detect_reasoning_request()
    print()
    
    print("Test 3: Detect analysis requests")
    test_detect_analysis_request()
    print()
    
    print("Test 4: No false positives")
    test_no_request()
    print()
    
    print("Test 5: Handle requests")
    test_handle_request()
    print()
    
    print("Test 6: Format responses")
    test_format_response()
    print()
    
    print("✅ All tests passed!")