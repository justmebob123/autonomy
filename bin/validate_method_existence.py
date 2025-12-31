#!/usr/bin/env python3
"""
Manual Method Existence Validator

Validates that methods called on objects actually exist on their classes.
Run this manually to check for missing method errors.

Usage:
    python bin/validate_method_existence.py [project_dir]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.method_existence_validator import MethodExistenceValidator


def main():
    # Get project directory from args or use current directory
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print(f"🔍 Validating method existence in: {project_dir}")
    print("=" * 80)
    
    # Run validation
    validator = MethodExistenceValidator(project_dir)
    result = validator.validate_all()
    
    # Display results
    errors = result.get('errors', [])
    total = result.get('total_errors', 0)
    classes_analyzed = result.get('classes_analyzed', 0)
    by_severity = result.get('by_severity', {})
    
    print(f"\n📊 SUMMARY")
    print(f"   Classes analyzed: {classes_analyzed}")
    print(f"   Total errors: {total}")
    print(f"   By severity:")
    for severity, count in by_severity.items():
        if count > 0:
            print(f"      {severity}: {count}")
    
    if errors:
        print(f"\n❌ ERRORS FOUND ({len(errors)}):")
        print("=" * 80)
        
        for i, err in enumerate(errors, 1):
            print(f"\n{i}. {err['file']}:{err['line']}")
            print(f"   Class: {err['class_name']}")
            print(f"   Method: {err['method_name']}")
            print(f"   Severity: {err['severity']}")
            print(f"   Message: {err['message']}")
    else:
        print(f"\n✅ No method existence errors found!")
    
    print("\n" + "=" * 80)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())