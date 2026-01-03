#!/usr/bin/env python3
"""
Enum Attribute Validator

Validates that Enum attributes exist before they are accessed.
Detects invalid enum member access like MessageType.INVALID_ATTRIBUTE.

Usage:
    python bin/validate_enum_attributes.py [project_dir]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.enum_attribute_validator import EnumAttributeValidator


def main():
    """Run enum attribute validation."""
    project_dir = "."
    
    # Parse arguments
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    
    print(f"🔍 Validating enum attributes in: {project_dir}")
    print("=" * 80)
    print()
    
    validator = EnumAttributeValidator(project_dir)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Enums found: {result['enums_found']}")
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
            print(f"   Enum: {error['enum_name']}")
            print(f"   Invalid attribute: {error['attribute']}")
            print(f"   Valid attributes: {', '.join(error['valid_attributes'][:10])}")
            if len(error['valid_attributes']) > 10:
                print(f"      ... and {len(error['valid_attributes']) - 10} more")
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