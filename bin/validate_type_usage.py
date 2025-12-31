#!/usr/bin/env python3
"""
Manual Type Usage Validator

Validates that objects are used according to their types.
Run this manually to check for type usage errors.

Usage:
    python bin/validate_type_usage.py [project_dir]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.type_usage_validator import TypeUsageValidator


def main():
    # Get project directory from args or use current directory
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print(f"🔍 Validating type usage in: {project_dir}")
    print("=" * 80)
    
    # Run validation
    validator = TypeUsageValidator(project_dir)
    result = validator.validate_all()
    
    # Display results
    errors = result.get('errors', [])
    total = result.get('total_errors', 0)
    dataclasses = result.get('dataclasses_found', 0)
    classes = result.get('classes_found', 0)
    by_severity = result.get('by_severity', {})
    
    print(f"\n📊 SUMMARY")
    print(f"   Dataclasses found: {dataclasses}")
    print(f"   Classes found: {classes}")
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
            print(f"   Variable: {err['variable']}")
            print(f"   Actual type: {err['actual_type']}")
            print(f"   Attempted operation: {err['attempted_operation']}")
            print(f"   Severity: {err['severity']}")
            print(f"   Message: {err['message']}")
    else:
        print(f"\n✅ No type usage errors found!")
    
    print("\n" + "=" * 80)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())