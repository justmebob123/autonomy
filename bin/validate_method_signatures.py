#!/usr/bin/env python3
"""
Method Signature Validator

Validates that method calls match the actual method signatures.
Detects wrong number of arguments and signature mismatches.

Usage:
    python bin/validate_method_signatures.py [project_dir]

This is a GENERAL PURPOSE tool that can analyze ANY Python codebase.

Usage:
    python validate_method_signatures.py <project_directory>
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.method_signature_validator import MethodSignatureValidator


def main():
    """Run method signature validation."""
    # Require explicit project directory
    if len(sys.argv) < 2:
        print("ERROR: Project directory required")
        print()
        print("Usage: {} <project_directory>".format(sys.argv[0]))
        print()
        print("This tool can analyze ANY Python codebase.")
        print()
        print("Examples:")
        print("  {} /path/to/any/project".format(sys.argv[0]))
        print("  {} /home/user/django-app".format(sys.argv[0]))
        print()
        sys.exit(1)
    
    project_dir = sys.argv[1]
    print(f"🔍 Validating method signatures in: {project_dir}")
    print("=" * 80)
    print()
    
    validator = MethodSignatureValidator(project_dir)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Methods found: {result['methods_found']}")
    print(f"   Total errors: {result['total_errors']}")
    print(f"   By severity:")
    for severity, count in result['by_severity'].items():
        if count > 0:
            print(f"      {severity}: {count}")
    print()
    
    if result['total_errors'] > 0:
        print("❌ ERRORS FOUND ({})".format(result['total_errors']))
        print("=" * 80)
        print()
        
        for i, error in enumerate(result['errors'], 1):
            print(f"{i}. {error['file']}:{error['line']}")
            print(f"   Class: {error['class_name']}")
            print(f"   Method: {error['method_name']}")
            print(f"   Expected args: {error['expected_args']}")
            print(f"   Provided args: {error['provided_args']}")
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