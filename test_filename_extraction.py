#!/usr/bin/env python3
"""Test the improved filename extraction"""

import sys
sys.path.insert(0, 'autonomy')

from pipeline.text_tool_parser import TextToolParser

parser = TextToolParser()

# Test cases
test_cases = [
    ("Implement user authentication system", "features/user_authentication_system.py"),
    ("Create advanced alerting rules", "monitors/alerting.py"),
    ("Add security monitoring", "monitors/security.py"),
    ("Develop dashboard interface", "ui/dashboard.py"),
    ("Build data export functionality", "features/data_export_functionality.py"),
    ("Implement payment processing", "features/payment_processing.py"),
    ("Create email notification service", "features/email_notification_service.py"),
    ("Add test for user login", "tests/test_user_login.py"),
    ("Implement API rate limiting", "features/api_rate_limiting.py"),
]

print("="*80)
print("FILENAME EXTRACTION TEST")
print("="*80)

passed = 0
failed = 0

for description, expected_pattern in test_cases:
    result = parser._infer_file_path(description)
    
    # Check if result is meaningful (not generic)
    is_generic = 'new_feature' in result or result == 'features/feature.py'
    is_meaningful = not is_generic
    
    # For keyword-based paths, check exact match
    # For extracted names, check it's meaningful
    if 'monitors/' in expected_pattern or 'ui/' in expected_pattern or 'tests/' in expected_pattern:
        success = result == expected_pattern
    else:
        success = is_meaningful and ('features/' in result or 'tests/' in result)
    
    status = "✅ PASS" if success else "❌ FAIL"
    
    print(f"\n{status}")
    print(f"  Input: {description}")
    print(f"  Result: {result}")
    print(f"  Meaningful: {is_meaningful}")
    
    if success:
        passed += 1
    else:
        failed += 1

print("\n" + "="*80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*80)

if failed == 0:
    print("✅ All tests passed! No more generic filenames.")
    sys.exit(0)
else:
    print("❌ Some tests failed.")
    sys.exit(1)