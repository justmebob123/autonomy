#!/usr/bin/env python3
"""
Comprehensive Deep Analysis of Entire Repository

This script will:
1. Run ALL validation tools on the entire repository
2. Analyze every single Python file
3. Check for syntax errors, import issues, logic errors
4. Generate a comprehensive report of ALL issues
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out after 300 seconds',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def main():
    print("=" * 80)
    print("COMPREHENSIVE DEEP ANALYSIS OF ENTIRE REPOSITORY")
    print("=" * 80)
    print()
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    project_root = Path(".")
    results = {}
    
    # Phase 1: Repository Statistics
    print("=" * 80)
    print("PHASE 1: REPOSITORY STATISTICS")
    print("=" * 80)
    print()
    
    # Count files
    py_files = list(project_root.rglob("*.py"))
    print(f"📊 Total Python files: {len(py_files)}")
    
    # Count lines
    total_lines = 0
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
        except:
            pass
    print(f"📊 Total lines of code: {total_lines:,}")
    print()
    
    results['statistics'] = {
        'total_files': len(py_files),
        'total_lines': total_lines
    }
    
    # Phase 2: Run All Validation Tools
    print("=" * 80)
    print("PHASE 2: RUNNING ALL VALIDATION TOOLS")
    print("=" * 80)
    print()
    
    validators = [
        ('bin/validate_all_enhanced.py', 'Enhanced Comprehensive Validation'),
        ('bin/validate_type_usage.py', 'Type Usage Validation'),
        ('bin/validate_method_existence.py', 'Method Existence Validation'),
        ('bin/validate_method_signatures.py', 'Method Signature Validation'),
        ('bin/validate_function_calls.py', 'Function Call Validation'),
        ('bin/validate_enum_attributes.py', 'Enum Attribute Validation'),
        ('bin/validate_dict_structure.py', 'Dictionary Structure Validation'),
        ('bin/validators/keyword_argument_validator.py', 'Keyword Argument Validation'),
    ]
    
    validation_results = {}
    
    for validator_path, description in validators:
        validator_file = project_root / validator_path
        if validator_file.exists():
            cmd = f"python3 {validator_path} ."
            result = run_command(cmd, description)
            validation_results[description] = result
            
            if result['success']:
                print(f"   ✅ {description}: PASSED")
            else:
                print(f"   ❌ {description}: FAILED")
                if result['stderr']:
                    print(f"      Error: {result['stderr'][:200]}")
        else:
            print(f"   ⚠️  {description}: NOT FOUND")
        print()
    
    results['validation'] = validation_results
    
    # Phase 3: Syntax Check All Files
    print("=" * 80)
    print("PHASE 3: SYNTAX CHECKING ALL FILES")
    print("=" * 80)
    print()
    
    syntax_errors = []
    checked = 0
    
    for py_file in py_files:
        if py_file.name.startswith('.'):
            continue
        
        checked += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, str(py_file), 'exec')
        except SyntaxError as e:
            syntax_errors.append({
                'file': str(py_file),
                'line': e.lineno,
                'error': str(e)
            })
        except Exception as e:
            syntax_errors.append({
                'file': str(py_file),
                'line': 0,
                'error': str(e)
            })
    
    print(f"📊 Files checked: {checked}")
    print(f"📊 Syntax errors found: {len(syntax_errors)}")
    
    if syntax_errors:
        print()
        print("❌ SYNTAX ERRORS:")
        for i, error in enumerate(syntax_errors[:10], 1):
            print(f"   {i}. {error['file']}:{error['line']}")
            print(f"      {error['error']}")
        if len(syntax_errors) > 10:
            print(f"   ... and {len(syntax_errors) - 10} more")
    else:
        print("   ✅ No syntax errors found")
    print()
    
    results['syntax_errors'] = syntax_errors
    
    # Phase 4: Import Analysis
    print("=" * 80)
    print("PHASE 4: IMPORT ANALYSIS")
    print("=" * 80)
    print()
    
    cmd = "python3 bin/validate_imports.py ."
    result = run_command(cmd, "Import Validation")
    results['imports'] = result
    
    if result['success']:
        print("   ✅ Import validation passed")
    else:
        print("   ❌ Import validation failed")
        if result['stderr']:
            print(f"      {result['stderr'][:500]}")
    print()
    
    # Phase 5: Deep Analysis Tools
    print("=" * 80)
    print("PHASE 5: DEEP ANALYSIS TOOLS")
    print("=" * 80)
    print()
    
    cmd = "python3 bin/deep_analyze.py ."
    result = run_command(cmd, "Deep Code Analysis")
    results['deep_analysis'] = result
    
    if result['success']:
        print("   ✅ Deep analysis completed")
    else:
        print("   ⚠️  Deep analysis had issues")
    print()
    
    # Phase 6: Generate Summary
    print("=" * 80)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print()
    
    # Count total errors
    total_errors = len(syntax_errors)
    
    # Parse validation results for error counts
    for desc, result in validation_results.items():
        if not result['success']:
            # Try to extract error count from output
            output = result['stdout'] + result['stderr']
            if 'Total errors:' in output:
                try:
                    error_line = [line for line in output.split('\n') if 'Total errors:' in line][0]
                    error_count = int(error_line.split(':')[1].strip())
                    total_errors += error_count
                except:
                    pass
    
    print(f"📊 Total Python files analyzed: {len(py_files)}")
    print(f"📊 Total lines of code: {total_lines:,}")
    print(f"📊 Syntax errors: {len(syntax_errors)}")
    print(f"📊 Validation tools run: {len(validators)}")
    print(f"📊 Estimated total issues: {total_errors}")
    print()
    
    # Save detailed results
    report_file = project_root / "DEEP_ANALYSIS_REPORT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report_file}")
    print()
    
    print("=" * 80)
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return 0 if total_errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())