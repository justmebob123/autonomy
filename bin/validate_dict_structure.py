#!/usr/bin/env python3
"""
Manual Dictionary Structure Validator

Validates that dictionary access patterns match actual data structures.
Run this manually to check for dictionary key errors.

Usage:
    python bin/validate_dict_structure.py [project_dir]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.dict_structure_validator import DictStructureValidator


def main():
    # Get project directory from args or use current directory
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print(f"🔍 Validating dictionary structures in: {project_dir}")
    print("=" * 80)
    
    # Run validation
    validator = DictStructureValidator(project_dir)
    result = validator.validate_all()
    
    # Display results
    errors = result.get('errors', [])
    total = result.get('total_errors', 0)
    structures = result.get('structures_analyzed', 0)
    by_severity = result.get('by_severity', {})
    by_type = result.get('by_type', {})
    
    print(f"\n📊 SUMMARY")
    print(f"   Structures analyzed: {structures}")
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
            print(f"   Variable: {err['variable']}")
            print(f"   Key path: {err['key_path']}")
            print(f"   Type: {err['error_type']}")
            print(f"   Severity: {err['severity']}")
            print(f"   Message: {err['message']}")
    else:
        print(f"\n✅ No dictionary structure errors found!")
    
    print("\n" + "=" * 80)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())