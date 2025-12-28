#!/usr/bin/env python3
"""
Deep Code Analyzer - Comprehensive CLI tool for depth-61 analysis.

This is the main entry point for performing comprehensive code analysis
using the Deep Code Analysis Framework.

Usage:
    # Analyze single file
    python deep_analyze.py path/to/file.py
    
    # Analyze directory
    python deep_analyze.py path/to/directory/ --recursive
    
    # Generate markdown report
    python deep_analyze.py path/to/file.py --output report.md
    
    # Generate JSON report
    python deep_analyze.py path/to/file.py --format json --output report.json
    
    # Analyze with specific checks
    python deep_analyze.py path/to/file.py --check bugs --check complexity
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analysis.core.analyzer import DeepCodeAnalyzer, AnalysisResult
from analysis.reporters.markdown import MarkdownReporter
from analysis.reporters.json import JSONReporter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Deep Code Analyzer - Comprehensive depth-61 analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  python deep_analyze.py pipeline/phases/qa.py
  
  # Analyze directory recursively
  python deep_analyze.py pipeline/ --recursive
  
  # Generate markdown report
  python deep_analyze.py pipeline/phases/qa.py --output QA_ANALYSIS.md
  
  # Generate JSON report
  python deep_analyze.py pipeline/phases/qa.py --format json --output qa.json
  
  # Show only critical issues
  python deep_analyze.py pipeline/ --recursive --severity CRITICAL
  
  # Analyze specific aspects
  python deep_analyze.py file.py --check bugs --check complexity --check dataflow
        """
    )
    
    parser.add_argument(
        'path',
        help='Path to Python file or directory to analyze'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively analyze all Python files in directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file for report (default: stdout)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json', 'text'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--severity',
        choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'ALL'],
        default='ALL',
        help='Minimum severity level to report (default: ALL)'
    )
    
    parser.add_argument(
        '--check',
        action='append',
        choices=['bugs', 'complexity', 'dataflow', 'integration', 'patterns', 'runtime', 'all'],
        help='Specific checks to perform (default: all)'
    )
    
    parser.add_argument(
        '--project-root',
        help='Project root directory for cross-file analysis'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics for directory analysis'
    )
    
    args = parser.parse_args()
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        return 1
    
    # Determine project root
    project_root = args.project_root or str(path.parent if path.is_file() else path)
    
    # Analyze
    if path.is_file():
        # Single file analysis
        result = analyze_file(path, project_root, args)
        output_result(result, args)
    
    elif path.is_dir() and args.recursive:
        # Directory analysis
        results = analyze_directory(path, project_root, args)
        
        if args.summary:
            output_summary(results, args)
        else:
            for result in results:
                output_result(result, args)
                print("\n" + "="*80 + "\n")
    
    else:
        print(f"Error: Path is a directory. Use --recursive to analyze all files.", file=sys.stderr)
        return 1
    
    return 0


def analyze_file(filepath: Path, project_root: str, args) -> AnalysisResult:
    """Analyze a single file."""
    if args.verbose:
        print(f"Analyzing {filepath}...", file=sys.stderr)
    
    try:
        analyzer = DeepCodeAnalyzer(str(filepath), project_root)
        result = analyzer.analyze()
        
        if args.verbose:
            print(f"✓ Analysis complete: {result.severity}", file=sys.stderr)
        
        return result
    
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        raise


def analyze_directory(dirpath: Path, project_root: str, args) -> List[AnalysisResult]:
    """Analyze all Python files in directory."""
    results = []
    
    for filepath in dirpath.rglob("*.py"):
        if args.verbose:
            print(f"Analyzing {filepath}...", file=sys.stderr)
        
        try:
            analyzer = DeepCodeAnalyzer(str(filepath), project_root)
            result = analyzer.analyze()
            
            # Filter by severity
            if args.severity != 'ALL':
                severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'GOOD': 4, 'EXCELLENT': 5}
                if severity_order.get(result.severity, 999) > severity_order.get(args.severity, 0):
                    continue
            
            results.append(result)
            
            if args.verbose:
                print(f"✓ {result.severity}", file=sys.stderr)
        
        except Exception as e:
            if args.verbose:
                print(f"✗ Error: {e}", file=sys.stderr)
    
    return results


def output_result(result: AnalysisResult, args):
    """Output analysis result."""
    if args.format == 'markdown':
        report = MarkdownReporter.generate(result, result.filepath)
    elif args.format == 'json':
        report = JSONReporter.generate(result)
    else:  # text
        report = generate_text_report(result)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        if args.verbose:
            print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


def output_summary(results: List[AnalysisResult], args):
    """Output summary statistics."""
    if not results:
        print("No files analyzed.")
        return
    
    analyzer = DeepCodeAnalyzer.__new__(DeepCodeAnalyzer)
    summary = analyzer.get_summary(results)
    
    print("=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal Files: {summary['total_files']}")
    print(f"Total Lines: {summary['total_lines']:,}")
    print(f"Total Functions: {summary['total_functions']}")
    print(f"Total Classes: {summary['total_classes']}")
    print(f"\nTotal Bugs: {summary['total_bugs']}")
    print(f"Critical Bugs: {summary['critical_bugs']}")
    print(f"Total Issues: {summary['total_issues']}")
    print(f"\nAverage Complexity: {summary['average_complexity']:.1f}")
    print(f"Max Complexity: {summary['max_complexity']}")
    
    print("\nSeverity Distribution:")
    for severity, count in summary['severity_distribution'].items():
        print(f"  {severity}: {count}")
    
    print("\n" + "=" * 80)
    
    # Show critical files
    critical_files = [r for r in results if r.severity == 'CRITICAL']
    if critical_files:
        print("\n🔴 CRITICAL FILES:")
        for result in critical_files:
            print(f"  - {result.filepath}")
            for bug in result.bugs:
                if bug['severity'] == 'CRITICAL':
                    print(f"    • Line {bug['line']}: {bug['message']}")


def generate_text_report(result: AnalysisResult) -> str:
    """Generate simple text report."""
    lines = [
        f"File: {result.filepath}",
        f"Severity: {result.severity}",
        f"Lines: {result.lines}",
        f"Functions: {result.functions}",
        f"Complexity: {result.complexity.get('average_complexity', 0):.1f} avg, {result.complexity.get('max_complexity', 0)} max",
        f"Issues: {result.issues_count}",
        "",
    ]
    
    if result.bugs:
        lines.append("BUGS:")
        for bug in result.bugs:
            lines.append(f"  [{bug['severity']}] Line {bug['line']}: {bug['message']}")
        lines.append("")
    
    if result.recommendations:
        lines.append("RECOMMENDATIONS:")
        for rec in result.recommendations:
            lines.append(f"  • {rec}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    sys.exit(main())