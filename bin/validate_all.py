#!/usr/bin/env python3
"""
Comprehensive Validation Tool

Runs all validation tools on the project and generates a comprehensive report.

Usage:
    python bin/validate_all.py [project_dir]
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.analysis.function_call_validator import FunctionCallValidator
from pipeline.analysis.method_existence_validator import MethodExistenceValidator
from pipeline.analysis.dict_structure_validator import DictStructureValidator
from pipeline.analysis.type_usage_validator import TypeUsageValidator


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_validation(project_dir):
    """Run all validation tools and collect results."""
    results = {}
    
    # 1. Function Call Validation
    print_section("1. FUNCTION CALL VALIDATION")
    validator1 = FunctionCallValidator(project_dir)
    results['function_calls'] = validator1.validate_all()
    print(f"   ✓ Completed: {results['function_calls']['total_errors']} errors found")
    
    # 2. Method Existence Validation
    print_section("2. METHOD EXISTENCE VALIDATION")
    validator2 = MethodExistenceValidator(project_dir)
    results['method_existence'] = validator2.validate_all()
    print(f"   ✓ Completed: {results['method_existence']['total_errors']} errors found")
    
    # 3. Dictionary Structure Validation
    print_section("3. DICTIONARY STRUCTURE VALIDATION")
    validator3 = DictStructureValidator(project_dir)
    results['dict_structure'] = validator3.validate_all()
    print(f"   ✓ Completed: {results['dict_structure']['total_errors']} errors found")
    
    # 4. Type Usage Validation
    print_section("4. TYPE USAGE VALIDATION")
    validator4 = TypeUsageValidator(project_dir)
    results['type_usage'] = validator4.validate_all()
    print(f"   ✓ Completed: {results['type_usage']['total_errors']} errors found")
    
    return results


def print_summary(results):
    """Print comprehensive summary."""
    print_section("COMPREHENSIVE SUMMARY")
    
    total_errors = sum(r['total_errors'] for r in results.values())
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total errors across all tools: {total_errors}")
    print(f"\n   Breakdown by tool:")
    
    for tool_name, result in results.items():
        errors = result['total_errors']
        status = "✅" if errors == 0 else "❌"
        print(f"      {status} {tool_name.replace('_', ' ').title()}: {errors} errors")
    
    # Detailed breakdown
    if total_errors > 0:
        print(f"\n❌ DETAILED BREAKDOWN:")
        
        # Function calls
        if results['function_calls']['total_errors'] > 0:
            print(f"\n   Function Call Errors:")
            by_type = results['function_calls'].get('by_type', {})
            for error_type, count in by_type.items():
                print(f"      • {error_type}: {count}")
        
        # Method existence
        if results['method_existence']['total_errors'] > 0:
            print(f"\n   Method Existence Errors:")
            print(f"      • Missing methods: {results['method_existence']['total_errors']}")
        
        # Dict structure
        if results['dict_structure']['total_errors'] > 0:
            print(f"\n   Dictionary Structure Errors:")
            by_type = results['dict_structure'].get('by_type', {})
            for error_type, count in by_type.items():
                print(f"      • {error_type}: {count}")
        
        # Type usage
        if results['type_usage']['total_errors'] > 0:
            print(f"\n   Type Usage Errors:")
            print(f"      • Type mismatches: {results['type_usage']['total_errors']}")
    else:
        print(f"\n✅ No errors found! Code quality is excellent!")
    
    return total_errors


def print_detailed_errors(results):
    """Print detailed error listings."""
    total_errors = sum(r['total_errors'] for r in results.values())
    
    if total_errors == 0:
        return
    
    print_section("DETAILED ERROR LISTINGS")
    
    # Function call errors
    if results['function_calls']['total_errors'] > 0:
        print(f"\n🔴 Function Call Errors ({results['function_calls']['total_errors']}):")
        for i, err in enumerate(results['function_calls']['errors'][:20], 1):
            print(f"\n   {i}. {err['file']}:{err['line']}")
            print(f"      Function: {err['function']}")
            print(f"      Type: {err['error_type']}")
            print(f"      Message: {err['message']}")
        
        if len(results['function_calls']['errors']) > 20:
            print(f"\n   ... and {len(results['function_calls']['errors']) - 20} more")
    
    # Method existence errors
    if results['method_existence']['total_errors'] > 0:
        print(f"\n🔴 Method Existence Errors ({results['method_existence']['total_errors']}):")
        for i, err in enumerate(results['method_existence']['errors'][:20], 1):
            print(f"\n   {i}. {err['file']}:{err['line']}")
            print(f"      Class: {err['class_name']}")
            print(f"      Method: {err['method_name']}")
            print(f"      Message: {err['message']}")
        
        if len(results['method_existence']['errors']) > 20:
            print(f"\n   ... and {len(results['method_existence']['errors']) - 20} more")
    
    # Dictionary structure errors
    if results['dict_structure']['total_errors'] > 0:
        print(f"\n🔴 Dictionary Structure Errors ({results['dict_structure']['total_errors']}):")
        for i, err in enumerate(results['dict_structure']['errors'][:20], 1):
            print(f"\n   {i}. {err['file']}:{err['line']}")
            print(f"      Variable: {err['variable']}")
            print(f"      Key: {err['key_path']}")
            print(f"      Message: {err['message']}")
        
        if len(results['dict_structure']['errors']) > 20:
            print(f"\n   ... and {len(results['dict_structure']['errors']) - 20} more")
    
    # Type usage errors
    if results['type_usage']['total_errors'] > 0:
        print(f"\n🔴 Type Usage Errors ({results['type_usage']['total_errors']}):")
        for i, err in enumerate(results['type_usage']['errors'][:20], 1):
            print(f"\n   {i}. {err['file']}:{err['line']}")
            print(f"      Variable: {err['variable']}")
            print(f"      Type: {err['actual_type']}")
            print(f"      Operation: {err['attempted_operation']}")
            print(f"      Message: {err['message']}")
        
        if len(results['type_usage']['errors']) > 20:
            print(f"\n   ... and {len(results['type_usage']['errors']) - 20} more")


def main():
    # Get project directory from args or use current directory
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print("=" * 80)
    print("  COMPREHENSIVE CODE VALIDATION")
    print("=" * 80)
    print(f"\n📁 Project: {project_dir}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all validations
    results = run_validation(project_dir)
    
    # Print summary
    total_errors = print_summary(results)
    
    # Print detailed errors
    print_detailed_errors(results)
    
    # Final message
    print("\n" + "=" * 80)
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if total_errors == 0:
        print("✅ VALIDATION PASSED - No errors found!")
    else:
        print(f"❌ VALIDATION FAILED - {total_errors} errors found")
    
    print("=" * 80 + "\n")
    
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())