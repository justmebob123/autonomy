"""
Comprehensive validation of the entire codebase.
Runs all available validators and provides a complete report.
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
from pipeline.analysis.dict_structure_validator import DictStructureValidator
from bin.validators.keyword_argument_validator import KeywordArgumentValidator

def main():
    """Run comprehensive validation."""
    
    print("="*80)
    print("COMPREHENSIVE CODEBASE VALIDATION")
    print("="*80)
    print()
    
    results = {}
    
    # 1. Dictionary Structure Validator
    print("1. Running Dictionary Structure Validator...")
    dict_validator = DictStructureValidator('.')
    dict_result = dict_validator.validate_all()
    results['dict_structure'] = dict_result
    print(f"   Total: {dict_result['total_errors']} errors")
    print(f"   High severity: {dict_result['by_severity']['high']}")
    print(f"   Low severity: {dict_result['by_severity']['low']}")
    print()
    
    # 2. Keyword Argument Validator
    print("2. Running Keyword Argument Validator...")
    kwarg_validator = KeywordArgumentValidator('.')
    kwarg_result = kwarg_validator.validate_all()
    results['keyword_args'] = kwarg_result
    print(f"   Total: {kwarg_result['total_errors']} errors")
    print()
    
    # 3. Syntax Check (simple)
    print("3. Running Syntax Check...")
    syntax_errors = []
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '.git' in str(py_file):
            continue
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            syntax_errors.append({'file': str(py_file), 'error': str(e)})
    
    results['syntax'] = {'total_errors': len(syntax_errors), 'errors': syntax_errors}
    print(f"   Total: {len(syntax_errors)} errors")
    print()
    
    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print()
    
    total_critical = dict_result['by_severity']['high']
    total_warnings = dict_result['by_severity']['low']
    total_errors = kwarg_result['total_errors'] + len(syntax_errors)
    
    print(f"Critical Issues (High Severity): {total_critical}")
    print(f"Warnings (Low Severity): {total_warnings}")
    print(f"Other Errors: {total_errors}")
    print()
    
    if total_critical == 0 and total_errors == 0:
        print("✅ NO CRITICAL ISSUES OR ERRORS FOUND")
        print(f"⚠️  {total_warnings} low-severity warnings (safe, using .get())")
    else:
        print(f"❌ {total_critical + total_errors} issues need attention")
    
    print()
    
    # Save detailed report
    with open('COMPREHENSIVE_VALIDATION_REPORT.md', 'w') as f:
        f.write("# Comprehensive Validation Report\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Critical Issues:** {total_critical}\n")
        f.write(f"- **Warnings:** {total_warnings}\n")
        f.write(f"- **Other Errors:** {total_errors}\n\n")
        
        if total_critical == 0 and total_errors == 0:
            f.write("✅ **Status:** PASS - No critical issues or errors\n\n")
        else:
            f.write("❌ **Status:** FAIL - Issues need attention\n\n")
        
        f.write("## Dictionary Structure Validation\n\n")
        f.write(f"- Total errors: {dict_result['total_errors']}\n")
        f.write(f"- High severity: {dict_result['by_severity']['high']}\n")
        f.write(f"- Low severity: {dict_result['by_severity']['low']}\n")
        f.write(f"- Structures analyzed: {dict_result['structures_analyzed']}\n\n")
        
        if dict_result['by_severity']['low'] > 0:
            f.write("### Low Severity Warnings\n\n")
            f.write("All warnings use `.get()` with defaults - safe but indicate inconsistent structures.\n")
            f.write("See DICT_WARNINGS_DEEP_ANALYSIS.md for details.\n\n")
        
        f.write("## Keyword Argument Validation\n\n")
        f.write(f"- Total errors: {kwarg_result['total_errors']}\n")
        f.write(f"- Methods checked: {kwarg_result.get('methods_found', 0)}\n\n")
        
        if kwarg_result['total_errors'] > 0:
            f.write("### Errors Found\n\n")
            for error in kwarg_result.get('errors', [])[:10]:
                f.write(f"- {error}\n")
            if len(kwarg_result.get('errors', [])) > 10:
                f.write(f"\n... and {len(kwarg_result['errors']) - 10} more\n")
            f.write("\n")
        
        f.write("## Syntax Validation\n\n")
        f.write(f"- Total errors: {len(syntax_errors)}\n\n")
        
        if syntax_errors:
            f.write("### Errors Found\n\n")
            for error in syntax_errors[:10]:
                f.write(f"- {error['file']}: {error['error']}\n")
            if len(syntax_errors) > 10:
                f.write(f"\n... and {len(syntax_errors) - 10} more\n")
            f.write("\n")
    
    print("✅ Detailed report saved to COMPREHENSIVE_VALIDATION_REPORT.md")
    
    return results

if __name__ == '__main__':
    main()