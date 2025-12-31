#!/usr/bin/env python3
"""
Method Existence Validator

Validates that methods exist on classes, checking parent and base classes.

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
    """Run method existence validation."""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = "."
    
    print(f"🔍 Validating method existence in: {project_dir}")
    print("=" * 80)
    print()
    
    validator = MethodExistenceValidator(project_dir)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Classes analyzed: {result['classes_analyzed']}")
    print(f"   Total errors: {result['total_errors']}")
    
    # Report duplicate classes
    if result.get('duplicate_classes'):
        print(f"   ⚠️  Duplicate class names: {len(result['duplicate_classes'])}")
    
    print(f"   By severity:")
    for severity, count in result['by_severity'].items():
        if count > 0:
            print(f"      {severity}: {count}")
    print()
    
    # Show duplicate classes
    if result.get('duplicate_classes'):
        print("⚠️  DUPLICATE CLASS NAMES DETECTED:")
        print("=" * 80)
        print()
        for class_name, locations in result['duplicate_classes'].items():
            print(f"   Class: {class_name}")
            print(f"   Defined in {len(locations)} files:")
            for loc in locations:
                print(f"      - {loc}")
            print()
        print("   ⚠️  This can cause confusion and validation errors!")
        print("   Recommendation: Rename classes or use namespaces")
        print()
    
    if result['total_errors'] > 0:
        print("❌ ERRORS FOUND ({})".format(result['total_errors']))
        print("=" * 80)
        print()
        
        for i, error in enumerate(result['errors'], 1):
            print(f"{i}. {error['file']}:{error['line']}")
            print(f"   Class: {error['class_name']}")
            print(f"   Method: {error['method_name']}")
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