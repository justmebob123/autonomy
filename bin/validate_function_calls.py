#!/usr/bin/env python3
"""
Manual Function Call Validator

Validates that all function and method calls use correct parameters.
Run this manually to check for function call errors.

Usage:
    python bin/validate_function_calls.py [project_dir]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.function_call_validator import FunctionCallValidator


def main():
    # Get project directory from args or use current directory
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print(f"🔍 Validating function calls in: {project_dir}")
    print("=" * 80)
    
    # Run validation
    validator = FunctionCallValidator(project_dir)
    result = validator.validate_all()
    
    # Display results
    errors = result.get('errors', [])
    total = result.get('total_errors', 0)
    by_severity = result.get('by_severity', {})
    by_type = result.get('by_type', {})
    
    print(f"\n📊 SUMMARY")
    print(f"   Total errors: {total}")
    print(f"   By severity:")
    for severity, count in by_severity.items():
        if count > 0:
            print(f"      {severity}: {count}")
    print(f"   By type:")
    for error_type, count in by_type.items():
        print(f"      {error_type}: {count}")
    
    if errors:
        print(f"\n❌ ERRORS FOUND ({len(errors)}):")
        print("=" * 80)
        
        for i, err in enumerate(errors, 1):
            print(f"\n{i}. {err['file']}:{err['line']}")
            print(f"   Function: {err['function']}")
            print(f"   Type: {err['error_type']}")
            print(f"   Severity: {err['severity']}")
            print(f"   Message: {err['message']}")
    else:
        print(f"\n✅ No function call errors found!")
    
    print("\n" + "=" * 80)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())