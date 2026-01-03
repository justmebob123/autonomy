#!/usr/bin/env python3
"""
Type Usage Validator

Validates that objects are used according to their types.
Run this manually to check for type usage errors.

Usage:
    python bin/validate_type_usage.py [project_dir]

This is a GENERAL PURPOSE tool that can analyze ANY Python codebase.

Usage:
    python validate_type_usage.py <project_directory>
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.type_usage_validator import TypeUsageValidator


def main():
    """Run type usage validation."""
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
    config_file = None
    
    print(f"🔍 Validating type usage in: {project_dir}")
    if config_file:
        print(f"📋 Using config: {config_file}")
    print("=" * 80)
    print()
    
    validator = TypeUsageValidator(project_dir, config_file)
    result = validator.validate_all()
    
    print("📊 SUMMARY")
    print(f"   Dataclasses found: {result['dataclasses_found']}")
    print(f"   Classes found: {result['classes_found']}")
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
            print(f"   Variable: {error['variable']}")
            print(f"   Actual type: {error['actual_type']}")
            print(f"   Attempted operation: {error['attempted_operation']}")
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