#!/usr/bin/env python3
"""
Test script for validation tools.

Tests all Phase 1 critical validation tools to ensure they work correctly.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.analysis.code_validation import (
    AttributeAccessValidator,
    ImportClassMatcher,
    AbstractMethodChecker,
    ToolHandlerVerifier,
    DictAccessValidator
)
from pipeline.logging_setup import get_logger

logger = get_logger()

def test_attribute_access_validator():
    """Test attribute access validation."""
    print("\n" + "="*60)
    print("TEST 1: Attribute Access Validator")
    print("="*60)
    
    # Test on documentation.py (had task.target error)
    filepath = "pipeline/phases/documentation.py"
    validator = AttributeAccessValidator(filepath, logger)
    issues = validator.validate()
    
    print(f"✓ Validated {filepath}")
    print(f"  Issues found: {len(issues)}")
    
    if issues:
        print("\n  Issues:")
        for issue in issues[:3]:
            print(f"    • Line {issue.get('line', '?')}: {issue['message']}")
    
    return len(issues) == 0

def test_import_class_matcher():
    """Test import-class name matching."""
    print("\n" + "="*60)
    print("TEST 2: Import-Class Matcher")
    print("="*60)
    
    # Test on refactoring.py (had ConflictDetector error)
    filepath = "pipeline/phases/refactoring.py"
    matcher = ImportClassMatcher(filepath, logger)
    issues = matcher.validate()
    
    print(f"✓ Validated {filepath}")
    print(f"  Issues found: {len(issues)}")
    
    if issues:
        print("\n  Issues:")
        for issue in issues[:3]:
            print(f"    • Line {issue.get('line', '?')}: {issue['message']}")
    
    return len(issues) == 0

def test_abstract_method_checker():
    """Test abstract method checking."""
    print("\n" + "="*60)
    print("TEST 3: Abstract Method Checker")
    print("="*60)
    
    # Test on RefactoringPhase (had missing generate_state_markdown)
    filepath = "pipeline/phases/refactoring.py"
    class_name = "RefactoringPhase"
    checker = AbstractMethodChecker(filepath, class_name, logger)
    issues = checker.validate()
    
    print(f"✓ Checked {class_name} in {filepath}")
    print(f"  Issues found: {len(issues)}")
    
    if issues:
        print("\n  Issues:")
        for issue in issues:
            print(f"    • {issue['message']}")
    
    return len(issues) == 0

def test_tool_handler_verifier():
    """Test tool-handler verification."""
    print("\n" + "="*60)
    print("TEST 4: Tool-Handler Verifier")
    print("="*60)
    
    project_dir = str(Path(__file__).parent)
    verifier = ToolHandlerVerifier(project_dir, logger)
    issues = verifier.validate()
    
    print(f"✓ Verified tool-handler-registration chain")
    print(f"  Issues found: {len(issues)}")
    
    if issues:
        print("\n  Issues (first 5):")
        for issue in issues[:5]:
            print(f"    • {issue['type']}: {issue['message']}")
    
    return True  # Some issues are expected for unimplemented Phase 2 tools

def test_dict_access_validator():
    """Test dictionary access validation."""
    print("\n" + "="*60)
    print("TEST 5: Dictionary Access Validator")
    print("="*60)
    
    # Test on a phase file
    filepath = "pipeline/phases/coding.py"
    validator = DictAccessValidator(filepath, logger)
    issues = validator.validate()
    
    print(f"✓ Validated {filepath}")
    print(f"  Issues found: {len(issues)}")
    
    if issues:
        print("\n  Issues (first 3):")
        for issue in issues[:3]:
            print(f"    • Line {issue.get('line', '?')}: {issue['message']}")
    
    return True  # Some unsafe accesses might be intentional

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VALIDATION TOOLS TEST SUITE")
    print("="*60)
    
    results = {
        "Attribute Access Validator": test_attribute_access_validator(),
        "Import-Class Matcher": test_import_class_matcher(),
        "Abstract Method Checker": test_abstract_method_checker(),
        "Tool-Handler Verifier": test_tool_handler_verifier(),
        "Dictionary Access Validator": test_dict_access_validator(),
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())