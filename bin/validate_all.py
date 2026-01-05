#!/usr/bin/env python3
"""
Comprehensive Code Validation - GENERAL PURPOSE TOOL

This tool can analyze ANY Python codebase, not just this project.

Uses ValidatorCoordinator with shared symbol table for improved accuracy
and performance.

Usage:
    python bin/validate_all.py [project_dir]
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.validator_coordinator import ValidatorCoordinator


def main():
    """Run all validators with shared symbol table."""
    # Require explicit project directory
    if len(sys.argv) < 2:
        print("ERROR: Project directory required")
        print()
        print("Usage: {} <project_directory> [--config <file>]".format(sys.argv[0]))
        print()
        print("This is a GENERAL PURPOSE tool that can analyze ANY Python codebase.")
        print()
        print("Examples:")
        print("  {} /path/to/any/project".format(sys.argv[0]))
        print("  {} /home/user/django-app".format(sys.argv[0]))
        print("  {} /var/www/flask-app".format(sys.argv[0]))
        print("  {} . --config custom.yaml".format(sys.argv[0]))
        print()
        sys.exit(1)
    
    project_dir = sys.argv[1]
    config_file = None
    
    # Parse additional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--config' and i + 1 < len(sys.argv):
            config_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    print("=" * 80)
    print("  ENHANCED COMPREHENSIVE CODE VALIDATION")
    print("  (Using Shared Symbol Table)")
    print("=" * 80)
    print()
    print(f"📁 Project: {project_dir}")
    if config_file:
        print(f"📋 Config: {config_file}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create coordinator
    coordinator = ValidatorCoordinator(project_dir, config_file)
    
    # Run all validators
    results = coordinator.validate_all()
    
    # Extract results
    total_errors = results['summary']['total_errors']
    stats = results['summary']['symbol_table_stats']
    duplicate_classes = results['summary']['duplicate_classes']
    
    # Print summary
    print()
    print("=" * 80)
    print("  COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print()
    print("📊 Symbol Table Statistics:")
    print(f"   Classes: {stats['total_classes']}")
    print(f"   Functions: {stats['total_functions']}")
    print(f"   Methods: {stats['total_methods']}")
    print(f"   Enums: {stats['total_enums']}")
    print(f"   Imports: {stats['total_imports']}")
    print(f"   Call graph edges: {stats['total_call_edges']}")
    if stats['duplicate_classes'] > 0:
        print(f"   ⚠️  Duplicate classes: {stats['duplicate_classes']}")
    print()
    
    print("📈 Overall Statistics:")
    print(f"   Total errors across all tools: {total_errors}")
    print()
    
    print("   Breakdown by tool:")
    if results['type_usage']['total_errors'] > 0:
        print(f"      ❌ Type Usage: {results['type_usage']['total_errors']} errors")
    else:
        print(f"      ✅ Type Usage: 0 errors")
    
    if results['method_existence']['total_errors'] > 0:
        print(f"      ❌ Method Existence: {results['method_existence']['total_errors']} errors")
    else:
        print(f"      ✅ Method Existence: 0 errors")
    
    if results['function_calls']['total_errors'] > 0:
        print(f"      ❌ Function Calls: {results['function_calls']['total_errors']} errors")
    else:
        print(f"      ✅ Function Calls: 0 errors")
    
    if results['enum_attributes']['total_errors'] > 0:
        print(f"      ❌ Enum Attributes: {results['enum_attributes']['total_errors']} errors")
    else:
        print(f"      ✅ Enum Attributes: 0 errors")
    
    if results['method_signatures']['total_errors'] > 0:
        print(f"      ❌ Method Signatures: {results['method_signatures']['total_errors']} errors")
    else:
        print(f"      ✅ Method Signatures: 0 errors")
    print()
    
    # Show duplicate classes warning
    if duplicate_classes:
        print("⚠️  DUPLICATE CLASS NAMES DETECTED:")
        print()
        for class_name, locations in list(duplicate_classes.items())[:5]:
            print(f"   {class_name}: {len(locations)} definitions")
            for loc in locations[:3]:
                print(f"      - {loc}")
            if len(locations) > 3:
                print(f"      ... and {len(locations) - 3} more")
        if len(duplicate_classes) > 5:
            print(f"   ... and {len(duplicate_classes) - 5} more")
        print()
        print("   ⚠️  This causes validation errors and production confusion!")
        print()
    
    if total_errors > 0:
        print("❌ DETAILED BREAKDOWN:")
        print()
        
        # Type Usage Errors
        if results['type_usage']['total_errors'] > 0:
            print(f"   Type Usage Errors:")
            for severity, count in results['type_usage']['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
        
        # Method Existence Errors
        if results['method_existence']['total_errors'] > 0:
            print(f"   Method Existence Errors:")
            for severity, count in results['method_existence']['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
        
        # Function Call Errors
        if results['function_calls']['total_errors'] > 0:
            print(f"   Function Call Errors:")
            for error_type, count in results['function_calls']['by_type'].items():
                print(f"      • {error_type}: {count}")
            print()
        
        # Enum Attribute Errors
        if results['enum_attributes']['total_errors'] > 0:
            print(f"   Enum Attribute Errors:")
            for severity, count in results['enum_attributes']['by_severity'].items():
                if count > 0:
                    print(f"      • {severity}: {count}")
            print()
        
        # Method Signature Errors
        if results['method_signatures']['total_errors'] > 0:
            print(f"   Method Signature Errors:")
            for severity, count in results['method_signatures']['by_severity'].items():
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
        if results['type_usage']['total_errors'] > 0:
            print(f"🔴 Type Usage Errors ({results['type_usage']['total_errors']}):")
            print()
            for i, err in enumerate(results['type_usage']['errors'][:20], 1):
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Variable: {err['variable']}")
                print(f"      Type: {err['actual_type']}")
                print(f"      Operation: {err['attempted_operation']}")
                print()
            if results['type_usage']['total_errors'] > 20:
                print(f"   ... and {results['type_usage']['total_errors'] - 20} more")
                print()
        
        # Method Existence Errors
        if results['method_existence']['total_errors'] > 0:
            print(f"🔴 Method Existence Errors ({results['method_existence']['total_errors']}):")
            print()
            for i, err in enumerate(results['method_existence']['errors'][:20], 1):
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Class: {err['class_name']}")
                print(f"      Method: {err['method_name']}")
                print()
            if results['method_existence']['total_errors'] > 20:
                print(f"   ... and {results['method_existence']['total_errors'] - 20} more")
                print()
        
        # Function Call Errors
        if results['function_calls']['total_errors'] > 0:
            print(f"🔴 Function Call Errors ({results['function_calls']['total_errors']}):")
            print()
            for i, err in enumerate(results['function_calls']['errors'][:20], 1):
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Function: {err['function_name']}")
                print(f"      Type: {err['error_type']}")
                print(f"      Message: {err['message']}")
                print()
            if results['function_calls']['total_errors'] > 20:
                print(f"   ... and {results['function_calls']['total_errors'] - 20} more")
                print()
        
        # Enum Attribute Errors
        if results['enum_attributes']['total_errors'] > 0:
            print(f"🔴 Enum Attribute Errors ({results['enum_attributes']['total_errors']}):")
            print()
            for i, err in enumerate(results['enum_attributes']['errors'][:20], 1):
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Enum: {err['enum_name']}")
                print(f"      Invalid attribute: {err['attribute']}")
                print(f"      Message: {err['message']}")
                print()
            if results['enum_attributes']['total_errors'] > 20:
                print(f"   ... and {results['enum_attributes']['total_errors'] - 20} more")
                print()
        
        # Method Signature Errors
        if results['method_signatures']['total_errors'] > 0:
            print(f"🔴 Method Signature Errors ({results['method_signatures']['total_errors']}):")
            print()
            for i, err in enumerate(results['method_signatures']['errors'][:20], 1):
                print(f"   {i}. {err['file']}:{err['line']}")
                print(f"      Class: {err['class_name']}")
                print(f"      Method: {err['method_name']}")
                print(f"      Expected: {err['expected_args']} args")
                print(f"      Provided: {err['provided_args']} args")
                print()
            if results['method_signatures']['total_errors'] > 20:
                print(f"   ... and {results['method_signatures']['total_errors'] - 20} more")
                print()
    
    print("=" * 80)
    
    # Save detailed report
    report_file = Path(project_dir) / "VALIDATION_REPORT_ENHANCED.txt"
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("  ENHANCED COMPREHENSIVE CODE VALIDATION\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Project: {project_dir}\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total errors: {total_errors}\n\n")
        
        f.write("Symbol Table Statistics:\n")
        f.write(f"  Classes: {stats['total_classes']}\n")
        f.write(f"  Functions: {stats['total_functions']}\n")
        f.write(f"  Methods: {stats['total_methods']}\n")
        f.write(f"  Enums: {stats['total_enums']}\n")
        f.write(f"  Call graph edges: {stats['total_call_edges']}\n\n")
        
        # Write all errors
        if results['type_usage']['total_errors'] > 0:
            f.write(f"Type Usage Errors ({results['type_usage']['total_errors']}):\n")
            for err in results['type_usage']['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if results['method_existence']['total_errors'] > 0:
            f.write(f"Method Existence Errors ({results['method_existence']['total_errors']}):\n")
            for err in results['method_existence']['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if results['function_calls']['total_errors'] > 0:
            f.write(f"Function Call Errors ({results['function_calls']['total_errors']}):\n")
            for err in results['function_calls']['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if results['enum_attributes']['total_errors'] > 0:
            f.write(f"Enum Attribute Errors ({results['enum_attributes']['total_errors']}):\n")
            for err in results['enum_attributes']['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
        
        if results['method_signatures']['total_errors'] > 0:
            f.write(f"Method Signature Errors ({results['method_signatures']['total_errors']}):\n")
            for err in results['method_signatures']['errors']:
                f.write(f"  {err['file']}:{err['line']} - {err['message']}\n")
            f.write("\n")
    
    print(f"📄 Detailed report saved to: {report_file}")
    print()
    
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())