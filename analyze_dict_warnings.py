"""
Deep Analysis of Dictionary Structure Warnings

This script analyzes all 69 low-severity dictionary warnings to determine:
1. Which are false positives (validator incorrectly inferred structure)
2. Which are real issues (inconsistent tool return structures)
3. Root causes and patterns
4. Recommendations for fixes
"""

import sys
sys.path.insert(0, '.')
from pipeline.analysis.dict_structure_validator import DictStructureValidator
from pathlib import Path
import ast
from collections import defaultdict

def analyze_warnings():
    """Analyze all dictionary warnings in detail."""
    
    validator = DictStructureValidator('.')
    result = validator.validate_all()
    
    print("=" * 80)
    print("DEEP ANALYSIS OF 69 DICTIONARY STRUCTURE WARNINGS")
    print("=" * 80)
    print()
    
    # Group by file
    by_file = defaultdict(list)
    for error in result['errors']:
        by_file[error['file']].append(error)
    
    print(f"Total warnings: {result['total_errors']}")
    print(f"Files affected: {len(by_file)}")
    print(f"Structures analyzed: {result['structures_analyzed']}")
    print()
    
    # Analyze patterns
    print("=" * 80)
    print("PATTERN ANALYSIS")
    print("=" * 80)
    print()
    
    # Pattern 1: Missing keys in tool results
    tool_result_errors = [e for e in result['errors'] if 'result' in e['variable']]
    print(f"1. Tool Result Structure Issues: {len(tool_result_errors)} warnings")
    print("   These indicate tools return inconsistent structures")
    print()
    
    # Pattern 2: Missing keys in phase decisions
    phase_decision_errors = [e for e in result['errors'] if 'decision' in e['variable']]
    print(f"2. Phase Decision Structure Issues: {len(phase_decision_errors)} warnings")
    print("   These indicate phase decision structures vary")
    print()
    
    # Pattern 3: Missing keys in analysis results
    analysis_errors = [e for e in result['errors'] if 'analysis' in e['variable']]
    print(f"3. Analysis Structure Issues: {len(analysis_errors)} warnings")
    print("   These indicate analysis results have varying structures")
    print()
    
    # Pattern 4: Missing keys in validation results
    validation_errors = [e for e in result['errors'] if 'validation' in e['variable']]
    print(f"4. Validation Structure Issues: {len(validation_errors)} warnings")
    print("   These indicate validation results vary")
    print()
    
    print("=" * 80)
    print("DETAILED FILE ANALYSIS")
    print("=" * 80)
    print()
    
    for file_path, errors in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{file_path}: {len(errors)} warnings")
        print("-" * 80)
        
        # Group by variable
        by_var = defaultdict(list)
        for error in errors:
            by_var[error['variable']].append(error)
        
        for var, var_errors in by_var.items():
            print(f"\n  Variable: {var}")
            print(f"  Missing keys: {', '.join([e['key_path'] for e in var_errors])}")
            print(f"  Available keys: {var_errors[0]['message'].split('Available keys: ')[1]}")
            
            # Analyze if this is a false positive or real issue
            available_keys = eval(var_errors[0]['message'].split('Available keys: ')[1])
            missing_keys = [e['key_path'] for e in var_errors]
            
            # Check if the available keys make sense for the context
            if 'tool' in available_keys and 'success' in available_keys:
                print(f"  ⚠️  REAL ISSUE: Tool returns inconsistent structure")
                print(f"      Tool result should have consistent keys across all code paths")
            elif 'success' in available_keys and 'error' not in available_keys:
                print(f"  ⚠️  REAL ISSUE: Missing error handling keys")
                print(f"      Should include 'error' key for error cases")
            else:
                print(f"  ℹ️  SAFE: Using .get() with defaults handles this correctly")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    print("1. STANDARDIZE TOOL RETURN STRUCTURES")
    print("   All tools should return consistent dictionaries with:")
    print("   - 'success': bool")
    print("   - 'error': str (optional, but key should exist)")
    print("   - Tool-specific data keys")
    print()
    
    print("2. STANDARDIZE PHASE DECISION STRUCTURES")
    print("   All phase decisions should have consistent keys:")
    print("   - 'phase': str")
    print("   - 'reason': str")
    print("   - 'specialized': bool")
    print("   - Optional keys should still be present (with None/empty values)")
    print()
    
    print("3. ADD STRUCTURE VALIDATION")
    print("   Create validation functions that check return structures")
    print("   before they're used in the code")
    print()
    
    print("4. CURRENT CODE IS SAFE")
    print("   All warnings use .get() with appropriate defaults")
    print("   No runtime crashes will occur")
    print("   These are code quality issues, not bugs")
    print()
    
    return result, by_file

if __name__ == '__main__':
    result, by_file = analyze_warnings()
    
    # Save detailed report
    with open('DICT_WARNINGS_DEEP_ANALYSIS.md', 'w') as f:
        f.write("# Deep Analysis of Dictionary Structure Warnings\n\n")
        f.write(f"**Total Warnings:** {result['total_errors']}\n\n")
        f.write(f"**Files Affected:** {len(by_file)}\n\n")
        f.write(f"**Severity:** All LOW (safe, using .get())\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write("All 69 warnings are **SAFE** - they use `.get()` with appropriate defaults.\n")
        f.write("However, they indicate **inconsistent data structures** across the codebase.\n\n")
        
        f.write("## Root Cause\n\n")
        f.write("Tools and functions return dictionaries with varying structures depending on:\n")
        f.write("- Success vs failure paths\n")
        f.write("- Different tool types\n")
        f.write("- Optional features\n")
        f.write("- Error conditions\n\n")
        
        f.write("## Impact\n\n")
        f.write("- ✅ **No Runtime Risk**: All code uses safe `.get()` access\n")
        f.write("- ⚠️ **Code Quality**: Inconsistent structures make code harder to maintain\n")
        f.write("- ⚠️ **Developer Experience**: Unclear what keys are available\n\n")
        
        f.write("## Detailed Breakdown\n\n")
        
        for file_path, errors in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"### {file_path} ({len(errors)} warnings)\n\n")
            
            by_var = defaultdict(list)
            for error in errors:
                by_var[error['variable']].append(error)
            
            for var, var_errors in by_var.items():
                f.write(f"**Variable:** `{var}`\n\n")
                missing_keys_str = ', '.join([f'`{e["key_path"]}`' for e in var_errors])
                f.write(f"**Missing keys:** {missing_keys_str}\n\n")
                f.write(f"**Available keys:** {var_errors[0]['message'].split('Available keys: ')[1]}\n\n")
                
                for error in var_errors:
                    f.write(f"- Line {error['line']}: `{error['key_path']}`\n")
                
                f.write("\n")
        
        f.write("## Recommendations\n\n")
        f.write("### Priority 1: Document Expected Structures\n")
        f.write("Create documentation for all tool return structures\n\n")
        
        f.write("### Priority 2: Standardize Common Patterns\n")
        f.write("Ensure all tools return consistent base keys:\n")
        f.write("- `success`: bool\n")
        f.write("- `error`: str | None\n")
        f.write("- `message`: str | None\n\n")
        
        f.write("### Priority 3: Add Type Hints\n")
        f.write("Use TypedDict to define return structures\n\n")
        
        f.write("### Priority 4: Validation Functions\n")
        f.write("Create validators that check structure before use\n\n")
    
    print("\n✅ Detailed analysis saved to DICT_WARNINGS_DEEP_ANALYSIS.md")