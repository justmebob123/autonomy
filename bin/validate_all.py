#!/usr/bin/env python3
"""
Comprehensive Code Validation

Runs all validators with proper type inference and intelligent filtering.

Usage:
    python bin/validate_all.py [project_dir]

This is a GENERAL PURPOSE tool that can analyze ANY Python codebase.

Usage:
    python validate_all.py <project_directory>
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.type_usage_validator import TypeUsageValidator
from pipeline.analysis.method_existence_validator import MethodExistenceValidator
from pipeline.analysis.function_call_validator import FunctionCallValidator
from pipeline.analysis.enum_attribute_validator import EnumAttributeValidator


def main():
    """Run all validators."""
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
    print("=" * 80)
    print("  COMPREHENSIVE CODE VALIDATION")
    print("=" * 80)
    print()
    print(f"📁 Project: {project_dir}")
    if config_file:
        print(f"📋 Config: {config_file}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_results = {}
    total_errors = 0
    
    # 1. Type Usage Validation
    print("=" * 80)
    print("  1. TYPE USAGE VALIDATION")
    print("=" * 80)
    validator1 = TypeUsageValidator(project_dir, config_file)
    result1 = validator1.validate_all()
    all_results['type_usage'] = result1
    total_errors += result1['total_errors']
    print(f"   ✓ Completed: {result1['total_errors']} errors found")
    print()
    
    # 2. Method Existence Validation
    print("=" * 80)
    print("  2. METHOD EXISTENCE VALIDATION")
    print("=" * 80)
    validator2 = MethodExistenceValidator(project_dir, config_file)
    result2 = validator2.validate_all()
    all_results['method_existence'] = result2
    total_errors += result2['total_errors']
    print(f"   ✓ Completed: {result2['total_errors']} errors found")
    print()
    
    # 3. Function Call Validation
    print("=" * 80)
    print("  3. FUNCTION CALL VALIDATION")
    print("=" * 80)
    validator3 = FunctionCallValidator(project_dir, config_file)
    result3 = validator3.validate_all()
    all_results['function_calls'] = result3
    total_errors += result3['total_errors']
    print(f"   ✓ Completed: {result3['total_errors']} errors found")
    print()
    
    # 4. Enum Attribute Validation
    print("=" * 80)
    print("  4. ENUM ATTRIBUTE VALIDATION")
    print("=" * 80)
    validator4 = EnumAttributeValidator(project_dir)
    result4 = validator4.validate_all()
    all_results['enum_attributes'] = result4
    total_errors += result4['total_errors']
    print(f"   ✓ Completed: {result4['total_errors']} errors found")
    print()
    
    # Summary
    print("=" * 80)
    print("  COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print()
    print("📊 Overall Statistics:")
    print(f"   Total errors across all tools: {total_errors}")
    
    # Report duplicate classes
    if result2.get('duplicate_classes'):
        print(f"   ⚠️  Duplicate class names: {len(result2['duplicate_classes'])}")
    
    print()
    print("   Breakdown by tool:")
    if result1['total_errors'] > 0:
        print(f"      ❌ Type Usage: {result1['total_errors']} errors")
    else:
        print(f"      ✅ Type Usage: 0 errors")
    
    if result2['total_errors'] > 0:
        print(f"      ❌ Method Existence: {result2['total_errors']} errors")
    else:
        print(f"      ✅ Method Existence: 0 errors")
    
    if result3['total_errors'] > 0:
        print(f"      ❌ Function Calls: {result3['total_errors']} errors")
    else:
        print(f"      ✅ Function Calls: 0 errors")
    
    if result4['total_errors'] > 0:
        print(f"      ❌ Enum Attributes: {result4['total_errors']} errors")
    else:
        print(f"      ✅ Enum Attributes: 0 errors")
    print()
    
    # Show duplicate classes warning
    if result2.get('duplicate_classes'):
        print("⚠️  DUPLICATE CLASS NAMES DETECTED:")
        print()
        for class_name, locations in list(result2['duplicate_classes'].items())[:5]:
            print(f"   {class_name}: {len(locations)} definitions")
        if len(result2['duplicate_classes']) > 5:
            print(f"   ... and {len(result2['duplicate_classes']) - 5} more")
        print()
        print("   ⚠️  This causes validation errors and production confusion!")
        print()
    
    if total_errors > 0:
        print("❌ DETAILED BREAKDOWN:")
        print()
        
        # Type Usage Errors
        if result1['total_errors'] > 0:
            print(f"   Type Usage Errors:")
            for severity, count in result1['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
        
        # Method Existence Errors
        if result2['total_errors'] > 0:
            print(f"   Method Existence Errors:")
            for severity, count in result2['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
        
        # Function Call Errors
        if result3['total_errors'] > 0:
            print(f"   Function Call Errors:")
            for error_type, count in result3['by_type'].items():
                print(f"      • {error_type}: {count}")
            print()
        
        # Enum Attribute Errors
        if result4['total_errors'] > 0:
            print(f"   Enum Attribute Errors:")
            for severity, count in result4['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
    
    # Detailed error listings
    if total_errors > 0:
        print("=" * 80)
        print("  DETAILED ERROR LISTINGS")
        print("=" * 80)
        print()
        
        # Type Usage Errors
        if result1['total_errors'] > 0:
            print(f"🔴 Type Usage Errors ({result1['total_errors']}):")
            print()
            for i, err in enumerate(result1['errors'][:20], 1):  # Limit to 20
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Variable: {err['variable']}")
                print(f"      Type: {err['actual_type']}")
                print(f"      Operation: {err['attempted_operation']}")
                print()
            if result1['total_errors'] > 20:
                print(f"   ... and {result1['total_errors'] - 20} more")
                print()
        
        # Method Existence Errors
        if result2['total_errors'] > 0:
            print(f"🔴 Method Existence Errors ({result2['total_errors']}):")
            print()
            for i, err in enumerate(result2['errors'][:20], 1):  # Limit to 20
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Class: {err['class_name']}")
                print(f"      Method: {err['method_name']}")
                print()
            if result2['total_errors'] > 20:
                print(f"   ... and {result2['total_errors'] - 20} more")
                print()
        
        # Function Call Errors
        if result3['total_errors'] > 0:
            print(f"🔴 Function Call Errors ({result3['total_errors']}):")
            print()
            for i, err in enumerate(result3['errors'][:20], 1):  # Limit to 20
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Function: {err['function_name']}")
                print(f"      Type: {err['error_type']}")
                print(f"      Message: {err['message']}")
                print()
            if result3['total_errors'] > 20:
                print(f"   ... and {result3['total_errors'] - 20} more")
                print()
        
        # Enum Attribute Errors
        if result4['total_errors'] > 0:
            print(f"🔴 Enum Attribute Errors ({result4['total_errors']}):")
            print()
            for i, err in enumerate(result4['errors'][:20], 1):  # Limit to 20
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Enum: {err['enum_name']}")
                print(f"      Invalid attribute: {err['attribute']}")
                print(f"      Message: {err['message']}")
                print()
            if result4['total_errors'] > 20:
                print(f"   ... and {result4['total_errors'] - 20} more")
                print()
    
    print("=" * 80)
    
    # Save detailed report
    report_file = Path(project_dir) / "VALIDATION_REPORT.txt"
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("  COMPREHENSIVE CODE VALIDATION\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Project: {project_dir}\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total errors: {total_errors}\n\n")
        
        # Write all errors
        if result1['total_errors'] > 0:
            f.write(f"Type Usage Errors ({result1['total_errors']}):\n")
            for err in result1['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if result2['total_errors'] > 0:
            f.write(f"Method Existence Errors ({result2['total_errors']}):\n")
            for err in result2['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if result3['total_errors'] > 0:
            f.write(f"Function Call Errors ({result3['total_errors']}):\n")
            for err in result3['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if result4['total_errors'] > 0:
            f.write(f"Enum Attribute Errors ({result4['total_errors']}):\n")
            for err in result4['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
    
    print(f"📄 Detailed report saved to: {report_file}")
    print()
    
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())