#!/usr/bin/env python3
"""
Function Call Validator

Validates function calls have correct arguments.

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
    """Run function call validation."""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = "."
    
    print(f"🔍 Validating function calls in: {project_dir}")
    print("=" * 80)
    print()
    
    validator = FunctionCallValidator(project_dir)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Functions analyzed: {result['functions_analyzed']}")
    print(f"   Total errors: {result['total_errors']}")
    print(f"   By type:")
    for error_type, count in result['by_type'].items():
        print(f"      {error_type}: {count}")
    print()
    
    if result['total_errors'] > 0:
        print("❌ ERRORS FOUND ({})".format(result['total_errors']))
        print("=" * 80)
        print()
        
        for i, error in enumerate(result['errors'], 1):
            print(f"{i}. {error['file']}:{error['line']}")
            print(f"   Function: {error['function_name']}")
            print(f"   Type: {error['error_type']}")
            print(f"   Severity: {error['severity']}")
            print(f"   Message: {error['message']}")
            print()
    else:
        print("✅ NO ERRORS FOUND")
        print()
    
    print("=" * 80)
    
    return 0 if result['total_errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())